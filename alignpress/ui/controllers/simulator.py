from __future__ import annotations

import csv
import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np
from PySide6.QtCore import QObject, QTimer, Signal

from alignpress.core.alignment import FrameAnalysis, LogoAligner
from alignpress.core.calibration import Calibration, load_calibration
from alignpress.core.presets import Preset, load_preset
from alignpress.domain.composition import LogoTaskDefinition
from alignpress.domain.job import JobCard, JobLogoRecord
from alignpress.domain.platen import PlatenProfile
from alignpress.domain.style import StyleDefinition
from alignpress.domain.variant import SizeVariant
from alignpress.io.config import AppConfig
from alignpress.io.logger import ResultLogger
from alignpress.ui.dataset_loader import DatasetFrame, DatasetLoader
from alignpress.ui.rendering import render_operator_overlay
from alignpress.ui.utils import cv_to_qimage


@dataclass
class LogoTask:
    definition: LogoTaskDefinition
    aligner: LogoAligner
    status: str = "pending"
    last_analysis: FrameAnalysis | None = None


@dataclass
class JobContext:
    platen: PlatenProfile | None = None
    style: StyleDefinition | None = None
    variant: SizeVariant | None = None
    calibration: Calibration | None = None

    def platen_name(self) -> str:
        return self.platen.name if self.platen else ""

    def style_name(self) -> str:
        return self.style.name if self.style else ""

    def style_version(self) -> str:
        return self.style.version if self.style else ""

    def variant_name(self) -> str:
        return self.variant.name if self.variant else "Base"


class SimulatorController(QObject):
    datasetLoaded = Signal(int)
    frameProcessed = Signal(int, str, object, object)
    playbackStateChanged = Signal(bool)
    statusMessage = Signal(str)
    errorOccurred = Signal(str)
    logoChanged = Signal(str, str)
    logoStatusUpdated = Signal(str, str)
    jobCompleted = Signal(str)

    def __init__(self, config: AppConfig, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._config = config
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._advance_frame)
        self._frames: List[DatasetFrame] = []
        self._history: List[Dict[str, object]] = []
        self._current_index = 0
        self._playing = False
        self._loop = config.dataset.loop
        self._speed = 1.0
        self._status_labels: Dict[str, str] = {}
        self._sample_frame: Optional[np.ndarray] = None
        self._log_dir_base = self._config.logging.output_dir
        self._log_dir_base.mkdir(parents=True, exist_ok=True)
        self._session_logger: Optional[ResultLogger] = None
        self._session_id: str = ""

        self._logo_tasks: List[LogoTask] = []
        self._current_logo_index: int = 0
        self._job_context: JobContext = JobContext()
        self._job_completed: bool = False
        self._auto_advance: bool = True

        # Legacy fallback for single preset mode
        self._legacy_aligner: Optional[LogoAligner] = None
        self._legacy_preset: Optional[Preset] = None

    # region Public configuration
    def configure_job(
        self,
        platen: PlatenProfile,
        style: StyleDefinition,
        variant: SizeVariant | None,
        calibration: Calibration,
        logos: List[LogoTaskDefinition],
    ) -> None:
        self._job_context = JobContext(platen=platen, style=style, variant=variant, calibration=calibration)
        self._logo_tasks = [LogoTask(definition=definition, aligner=LogoAligner(definition.preset, calibration)) for definition in logos]
        self._current_logo_index = 0
        self._job_completed = False
        self._legacy_aligner = None
        self._legacy_preset = None
        if self._logo_tasks:
            self.logoChanged.emit(self._logo_tasks[0].definition.logo_id, self._logo_tasks[0].definition.display_name)
    # endregion

    # region Session management
    def load_session(self) -> None:
        try:
            loader = DatasetLoader(self._config.dataset.path, fps=self._config.dataset.fps, loop=self._config.dataset.loop)
            self._frames = loader.load()
        except Exception as exc:  # pragma: no cover - depends on filesystem
            self.errorOccurred.emit(str(exc))
            return

        if not self._frames:
            self.errorOccurred.emit("Dataset vacío")
            return

        # Legacy fallback if no job configured
        if not self._logo_tasks:
            try:
                preset = load_preset(self._config.preset_path)
                calibration = load_calibration(self._config.calibration_path)
                self._legacy_aligner = LogoAligner(preset=preset, calibration=calibration)
                self._legacy_preset = preset
            except Exception as exc:  # pragma: no cover - depends on filesystem
                self.errorOccurred.emit(str(exc))
                return
        else:
            self._legacy_aligner = None
            self._legacy_preset = None

        self._history.clear()
        self._current_index = 0
        self._sample_frame = self._frames[0].frame.copy()
        if self._session_logger:
            self._session_logger.close()
        self._session_id = time.strftime("session_%Y%m%d_%H%M%S")
        session_dir = self._log_dir_base / self._session_id
        self._session_logger = ResultLogger(session_dir, self._config.logging.formats)
        self._session_logger.open()
        self.statusMessage.emit(str(session_dir))
        self.datasetLoaded.emit(len(self._frames))
        self._emit_current_frame()
    # endregion

    # region Playback controls
    def play(self) -> None:
        if not self._frames:
            return
        if self._playing:
            return
        interval_ms = 33
        if self._config.dataset.fps > 0:
            interval_ms = int(1000 / (self._config.dataset.fps * self._speed))
            interval_ms = max(interval_ms, 10)
        self._timer.start(interval_ms)
        self._playing = True
        self.playbackStateChanged.emit(True)

    def pause(self) -> None:
        if not self._playing:
            return
        self._timer.stop()
        self._playing = False
        self.playbackStateChanged.emit(False)

    def toggle_play(self) -> None:
        if self._playing:
            self.pause()
        else:
            self.play()

    def next_frame(self) -> None:
        if not self._frames:
            return
        self._current_index = (self._current_index + 1) % len(self._frames)
        if self._current_index == 0 and not self._loop and self._playing:
            self.pause()
            self.statusMessage.emit("Fin de dataset")
        self._emit_current_frame()

    def previous_frame(self) -> None:
        if not self._frames:
            return
        self._current_index = (self._current_index - 1) % len(self._frames)
        self._emit_current_frame()

    def set_speed(self, speed: float) -> None:
        self._speed = max(speed, 0.1)
        if self._playing:
            self.pause()
            self.play()

    def seek(self, index: int) -> None:
        if not self._frames:
            return
        if index < 0 or index >= len(self._frames):
            return
        self._current_index = index
        self._emit_current_frame()

    def _advance_frame(self) -> None:
        if not self._frames:
            self.pause()
            return
        if self._current_index + 1 >= len(self._frames):
            if self._loop:
                self._current_index = 0
            else:
                self.pause()
                self.statusMessage.emit("Fin de dataset")
                return
        else:
            self._current_index += 1
        self._emit_current_frame()
    # endregion

    # region Logo workflow
    def current_logo_task(self) -> LogoTask | None:
        if not self._logo_tasks:
            return None
        if self._current_logo_index < 0 or self._current_logo_index >= len(self._logo_tasks):
            return None
        return self._logo_tasks[self._current_logo_index]

    def next_logo(self, auto: bool = False) -> None:
        if not self._logo_tasks:
            return
        if self._current_logo_index + 1 >= len(self._logo_tasks):
            if auto:
                self._check_job_completion()
            return
        self._current_logo_index += 1
        task = self.current_logo_task()
        if task:
            self.logoChanged.emit(task.definition.logo_id, task.definition.display_name)
        if auto:
            self._emit_current_frame()

    def previous_logo(self) -> None:
        if not self._logo_tasks:
            return
        if self._current_logo_index == 0:
            return
        self._current_logo_index -= 1
        task = self.current_logo_task()
        if task:
            self.logoChanged.emit(task.definition.logo_id, task.definition.display_name)
        self._emit_current_frame()

    def select_logo(self, logo_id: str) -> None:
        if not self._logo_tasks:
            return
        for idx, task in enumerate(self._logo_tasks):
            if task.definition.logo_id == logo_id:
                self._current_logo_index = idx
                self.logoChanged.emit(task.definition.logo_id, task.definition.display_name)
                self._emit_current_frame()
                break

    def logo_tasks_summary(self) -> List[Dict[str, str]]:
        summary = []
        for task in self._logo_tasks:
            summary.append(
                {
                    "logo_id": task.definition.logo_id,
                    "display_name": task.definition.display_name,
                    "status": task.status,
                }
            )
        return summary
    # endregion

    def _emit_current_frame(self) -> None:
        aligner: LogoAligner | None = None
        preset: Optional[Preset] = None
        logo_task = self.current_logo_task()
        if logo_task:
            aligner = logo_task.aligner
            preset = logo_task.definition.preset
        elif self._legacy_aligner:
            aligner = self._legacy_aligner
            preset = self._legacy_preset

        if not aligner or not self._frames:
            return

        frame_data = self._frames[self._current_index]
        frame = frame_data.frame.copy()
        timestamp = frame_data.timestamp
        frame_id = frame_data.frame_id
        analysis = aligner.process_frame(frame, timestamp, frame_id)

        if logo_task:
            logo_task.last_analysis = analysis
            if analysis.evaluation.status != logo_task.status:
                logo_task.status = analysis.evaluation.status
                self.logoStatusUpdated.emit(logo_task.definition.logo_id, logo_task.status)
            record_logo_id = logo_task.definition.logo_id
            display_name = logo_task.definition.display_name
        else:
            record_logo_id = preset.name if preset else "legacy"
            display_name = record_logo_id

        overlay = render_operator_overlay(frame, preset, analysis, self._status_labels) if preset else frame
        if self._sample_frame is None:
            self._sample_frame = frame.copy()
        self._history.append(
            {
                "frame_index": self._current_index,
                "frame_id": frame_id,
                "logo_id": record_logo_id,
                "display_name": display_name,
                "analysis": analysis,
            }
        )
        self._last_overlay = overlay
        qimage = cv_to_qimage(overlay)
        self.frameProcessed.emit(self._current_index, frame_id, qimage, analysis)

        if self._session_logger:
            record = analysis.to_record()
            record.update(
                {
                    "session_id": self._session_id,
                    "preset_name": preset.name if preset else "",
                    "logo_id": record_logo_id,
                    "dataset_path": str(self._config.dataset.path),
                }
            )
            self._session_logger.log(record)

        if logo_task and analysis.evaluation.status == "ok" and self._auto_advance:
            self.next_logo(auto=True)
        else:
            self._check_job_completion()

    # region Snapshot & export helpers
    def current_overlay(self) -> Optional[np.ndarray]:
        return None if self._last_overlay is None else self._last_overlay.copy()

    def history(self) -> List[Dict[str, object]]:
        return list(self._history)

    def frame_count(self) -> int:
        return len(self._frames)

    def current_index(self) -> int:
        return self._current_index

    def current_analysis(self) -> Optional[FrameAnalysis]:
        if not self._history:
            return None
        return self._history[-1]["analysis"]

    def is_playing(self) -> bool:
        return self._playing

    def set_status_labels(self, labels: Dict[str, str]) -> None:
        self._status_labels = dict(labels)

    def sample_frame(self) -> Optional[np.ndarray]:
        if self._sample_frame is not None:
            return self._sample_frame.copy()
        if self._frames:
            return self._frames[0].frame.copy()
        return None

    def shutdown(self) -> None:
        if self._session_logger:
            self._session_logger.close()
            self._session_logger = None

    def export_history(self, path: Path, fmt: str = "csv") -> None:
        records: List[Dict[str, object]] = []
        for entry in self._history:
            analysis: FrameAnalysis = entry["analysis"]
            record = analysis.to_record()
            record.update(
                {
                    "session_id": self._session_id,
                    "preset_name": entry.get("display_name", ""),
                    "logo_id": entry.get("logo_id", ""),
                    "dataset_path": str(self._config.dataset.path),
                }
            )
            records.append(record)
        path.parent.mkdir(parents=True, exist_ok=True)
        if fmt == "json":
            with path.open("w", encoding="utf-8") as fh:
                json.dump(records, fh, indent=2)
            return
        if not records:
            path.write_text("", encoding="utf-8")
            return
        fieldnames = list(records[0].keys())
        with path.open("w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(records)
    # endregion

    # region Job cards
    def _check_job_completion(self) -> None:
        if not self._logo_tasks or self._job_completed:
            return
        if any(task.status != "ok" for task in self._logo_tasks):
            return
        if any(task.last_analysis is None for task in self._logo_tasks):
            return
        self._job_completed = True
        card = self._build_job_card()
        if not card:
            return
        directory = self._config.assets.job_cards_dir if self._config.assets else (self._log_dir_base / "job_cards")
        path = card.save(directory)
        self.jobCompleted.emit(str(path))
        self.statusMessage.emit(f"Job guardado en {path}")

    def _build_job_card(self) -> JobCard | None:
        if not self._job_context or not self._logo_tasks:
            return None
        dataset_path = str(self._config.dataset.path)
        records: List[JobLogoRecord] = []
        for task in self._logo_tasks:
            if not task.last_analysis:
                continue
            records.append(
                JobLogoRecord.from_analysis(task.definition.logo_id, task.definition.display_name, task.last_analysis)
            )
        if not records:
            return None
        card = JobCard.create(
            platen_name=self._job_context.platen_name(),
            style_name=self._job_context.style_name(),
            style_version=self._job_context.style_version(),
            variant_name=self._job_context.variant_name(),
            dataset=dataset_path,
            logos=records,
        )
        return card
    # endregion
