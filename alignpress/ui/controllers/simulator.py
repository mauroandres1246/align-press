from __future__ import annotations

import csv
import json
import time
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np
from PySide6.QtCore import QObject, QTimer, Signal

from alignpress.core.alignment import FrameAnalysis, LogoAligner
from alignpress.core.calibration import load_calibration
from alignpress.core.presets import load_preset, Preset
from alignpress.io.config import AppConfig
from alignpress.io.logger import ResultLogger
from alignpress.ui.dataset_loader import DatasetFrame, DatasetLoader
from alignpress.ui.rendering import render_operator_overlay
from alignpress.ui.utils import cv_to_qimage


class SimulatorController(QObject):
    datasetLoaded = Signal(int)
    frameProcessed = Signal(int, str, object, object)
    playbackStateChanged = Signal(bool)
    statusMessage = Signal(str)
    errorOccurred = Signal(str)

    def __init__(self, config: AppConfig, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._config = config
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._advance_frame)
        self._frames: List[DatasetFrame] = []
        self._history: Dict[int, FrameAnalysis] = {}
        self._current_index = 0
        self._playing = False
        self._loop = config.dataset.loop
        self._speed = 1.0
        self._aligner: Optional[LogoAligner] = None
        self._preset: Optional[Preset] = None
        self._last_overlay = None
        self._status_labels: Dict[str, str] = {}
        self._sample_frame: Optional[np.ndarray] = None
        self._log_dir_base = self._config.logging.output_dir
        self._log_dir_base.mkdir(parents=True, exist_ok=True)
        self._session_logger: Optional[ResultLogger] = None
        self._session_id: str = ""

    # region Session management
    def load_session(self) -> None:
        try:
            preset = load_preset(self._config.preset_path)
            calibration = load_calibration(self._config.calibration_path)
            self._aligner = LogoAligner(preset=preset, calibration=calibration)
            self._preset = preset
        except Exception as exc:  # pragma: no cover - depends on filesystem
            self.errorOccurred.emit(str(exc))
            return

        try:
            loader = DatasetLoader(self._config.dataset.path, fps=self._config.dataset.fps, loop=self._config.dataset.loop)
            self._frames = loader.load()
        except Exception as exc:  # pragma: no cover - depends on filesystem
            self.errorOccurred.emit(str(exc))
            return

        if not self._frames:
            self.errorOccurred.emit("Dataset vacío")
            return

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

    def _emit_current_frame(self) -> None:
        if not self._aligner or not self._frames:
            return
        frame_data = self._frames[self._current_index]
        frame = frame_data.frame.copy()
        timestamp = frame_data.timestamp
        frame_id = frame_data.frame_id
        analysis = self._aligner.process_frame(frame, timestamp, frame_id)
        self._history[self._current_index] = analysis
        overlay = (
            render_operator_overlay(frame, self._preset, analysis, self._status_labels)
            if self._preset
            else frame
        )
        self._last_overlay = overlay
        qimage = cv_to_qimage(overlay)
        self.frameProcessed.emit(self._current_index, frame_id, qimage, analysis)
        if self._session_logger:
            record = analysis.to_record()
            record.update(
                {
                    "session_id": self._session_id,
                    "preset_name": self._preset.name if self._preset else "",
                    "dataset_path": str(self._config.dataset.path),
                }
            )
            self._session_logger.log(record)

    # region Snapshot & export helpers
    def current_overlay(self) -> Optional[np.ndarray]:
        return None if self._last_overlay is None else self._last_overlay.copy()

    def history(self) -> Dict[int, FrameAnalysis]:
        return dict(self._history)

    def frame_count(self) -> int:
        return len(self._frames)

    def current_index(self) -> int:
        return self._current_index

    def current_analysis(self) -> Optional[FrameAnalysis]:
        return self._history.get(self._current_index)

    def is_playing(self) -> bool:
        return self._playing

    def preset(self) -> Optional[Preset]:
        return self._preset

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
        records = []
        for index in sorted(self._history.keys()):
            analysis = self._history[index]
            record = analysis.to_record()
            record.update(
                {
                    "session_id": self._session_id,
                    "preset_name": self._preset.name if self._preset else "",
                    "dataset_path": str(self._config.dataset.path),
                }
            )
            records.append(record)
        if fmt == "json":
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("w", encoding="utf-8") as fh:
                json.dump(records, fh, indent=2)
            return
        if not records:
            path.write_text("")
            return
        fieldnames = list(records[0].keys())
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(records)
    # endregion
