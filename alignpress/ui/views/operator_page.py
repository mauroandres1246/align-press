from __future__ import annotations

import time
from pathlib import Path
from typing import Optional

import cv2
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QSpacerItem,
    QVBoxLayout,
    QWidget,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
)

from alignpress.core.alignment import FrameAnalysis
from alignpress.core.presets import Preset
from alignpress.ui.app_context import AppContext
from alignpress.ui.controllers.simulator import SimulatorController
from alignpress.ui.i18n import I18nManager
from alignpress.ui.utils import format_metric


_STATUS_STYLE = {
    "ok": ("🟢", "#1b5e20", "#ffffff"),
    "out_of_tolerance": ("🟠", "#ef6c00", "#212121"),
    "not_found": ("🔴", "#b71c1c", "#ffffff"),
}


class OperatorPage(QWidget):
    messageEmitted = Signal(str)
    errorEmitted = Signal(str)

    def __init__(self, context: AppContext, controller: SimulatorController, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._context = context
        self._controller = controller
        self._i18n: I18nManager = context.i18n
        self._frame_count = 0
        self._current_pixmap: Optional[QPixmap] = None
        self._preset: Optional[Preset] = None

        self._build_ui()
        self._connect_signals()
        self.retranslate_ui()

    def _build_ui(self) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(16, 16, 16, 16)
        outer.setSpacing(12)

        self._tabs = QTabWidget(self)
        outer.addWidget(self._tabs)

        camera_a_widget = QWidget()
        root = QHBoxLayout(camera_a_widget)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(24)

        # Image panel
        image_layout = QVBoxLayout()
        self._image_label = QLabel()
        self._image_label.setMinimumSize(960, 540)
        self._image_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self._image_label.setStyleSheet("background-color: #1c1c1c; border: 2px solid #2f2f2f;")
        self._image_label.setAlignment(Qt.AlignCenter)
        image_layout.addWidget(self._image_label, stretch=1)

        controls_layout = QHBoxLayout()
        self._btn_prev = QPushButton("⏮")
        self._btn_prev.setFixedHeight(52)
        self._btn_prev.setMinimumWidth(72)

        self._btn_play_pause = QPushButton()
        self._btn_play_pause.setFixedHeight(52)
        self._btn_play_pause.setMinimumWidth(140)

        self._btn_next = QPushButton("⏭")
        self._btn_next.setFixedHeight(52)
        self._btn_next.setMinimumWidth(72)

        self._speed_combo = QComboBox()
        self._speed_combo.addItem("0.25x", 0.25)
        self._speed_combo.addItem("0.5x", 0.5)
        self._speed_combo.addItem("1x", 1.0)
        self._speed_combo.addItem("1.5x", 1.5)
        self._speed_combo.addItem("2x", 2.0)
        self._speed_combo.setCurrentIndex(2)
        self._speed_combo.setFixedHeight(52)
        self._speed_combo.setMinimumWidth(100)

        controls_layout.addWidget(self._btn_prev)
        controls_layout.addWidget(self._btn_play_pause, stretch=1)
        controls_layout.addWidget(self._btn_next)
        controls_layout.addWidget(self._speed_combo)
        image_layout.addLayout(controls_layout)

        self._frame_label = QLabel("—")
        self._frame_label.setAlignment(Qt.AlignCenter)
        self._frame_label.setStyleSheet("font-size: 14px; color: #888888;")
        image_layout.addWidget(self._frame_label)

        root.addLayout(image_layout, stretch=3)

        # Side panel
        side_layout = QVBoxLayout()
        side_layout.setSpacing(16)

        self._status_label = QLabel()
        self._status_label.setAlignment(Qt.AlignCenter)
        self._status_label.setFixedHeight(120)
        self._status_label.setStyleSheet("border-radius: 12px; font-size: 36px; font-weight: 700;")
        side_layout.addWidget(self._status_label)

        self._metrics_labels = {
            "dx": QLabel(),
            "dy": QLabel(),
            "theta": QLabel(),
        }
        for lbl in self._metrics_labels.values():
            lbl.setStyleSheet("font-size: 20px; font-weight: 600;")
            lbl.setAlignment(Qt.AlignLeft)
            side_layout.addWidget(lbl)

        side_layout.addSpacerItem(QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Expanding))

        self._btn_snapshot = QPushButton()
        self._btn_snapshot.setFixedHeight(50)
        self._btn_snapshot.setStyleSheet("font-size: 18px;")

        self._btn_change_preset = QPushButton()
        self._btn_change_preset.setFixedHeight(50)
        self._btn_change_preset.setStyleSheet("font-size: 18px;")

        self._btn_stop = QPushButton()
        self._btn_stop.setFixedHeight(50)
        self._btn_stop.setStyleSheet("font-size: 18px;")

        side_layout.addWidget(self._btn_snapshot)
        side_layout.addWidget(self._btn_change_preset)
        side_layout.addWidget(self._btn_stop)

        root.addLayout(side_layout, stretch=1)

        self._tabs.addTab(camera_a_widget, "")

        camera_b_widget = QWidget()
        camera_b_layout = QVBoxLayout(camera_b_widget)
        camera_b_layout.setContentsMargins(48, 48, 48, 48)
        camera_b_layout.setAlignment(Qt.AlignCenter)
        self._camera_b_label = QLabel("Camera B placeholder")
        self._camera_b_label.setAlignment(Qt.AlignCenter)
        self._camera_b_label.setStyleSheet("color: #888888; font-size: 20px;")
        camera_b_layout.addWidget(self._camera_b_label)

        self._tabs.addTab(camera_b_widget, "")

        self._history_table = QTableWidget(0, 6)
        self._history_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self._history_table.setSelectionBehavior(QTableWidget.SelectRows)
        self._history_table.setSelectionMode(QTableWidget.SingleSelection)
        header = self._history_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        outer.addWidget(self._history_table)

    def _connect_signals(self) -> None:
        self._btn_play_pause.clicked.connect(self._controller.toggle_play)
        self._btn_prev.clicked.connect(self._controller.previous_frame)
        self._btn_next.clicked.connect(self._controller.next_frame)
        self._btn_snapshot.clicked.connect(self._on_snapshot)
        self._btn_change_preset.clicked.connect(self._on_change_preset)
        self._btn_stop.clicked.connect(self._controller.pause)
        self._speed_combo.currentIndexChanged.connect(self._on_speed_changed)

        self._controller.frameProcessed.connect(self._on_frame_processed)
        self._controller.playbackStateChanged.connect(self._on_play_state_changed)
        self._controller.datasetLoaded.connect(self._on_dataset_loaded)
        self._controller.statusMessage.connect(self.messageEmitted)
        self._controller.errorOccurred.connect(self.errorEmitted)

    # region UI logic
    def retranslate_ui(self) -> None:
        tr = self._i18n
        self._btn_play_pause.setText(tr("operator.controls.play"))
        self._btn_snapshot.setText(tr("operator.controls.snapshot"))
        self._btn_change_preset.setText(tr("operator.controls.change_preset"))
        self._btn_stop.setText(tr("operator.controls.stop"))
        self._frame_label.setText("—")
        self._update_metrics(None)
        self._update_status("init", None)
        self._controller.set_status_labels(
            {
                "ok": tr("operator.status.ok"),
                "out_of_tolerance": tr("operator.status.adjust"),
                "not_found": tr("operator.status.not_found"),
            }
        )
        self._tabs.setTabText(0, tr("operator.camera.a"))
        self._tabs.setTabText(1, tr("operator.camera.b"))
        self._camera_b_label.setText(tr("technical.camera.dual"))
        self._history_table.setHorizontalHeaderLabels([
            tr("operator.table.header.frame"),
            tr("operator.table.header.status"),
            tr("operator.table.header.dx"),
            tr("operator.table.header.dy"),
            tr("operator.table.header.theta"),
            tr("operator.table.header.timestamp"),
        ])

    def _on_speed_changed(self) -> None:
        speed = self._speed_combo.currentData()
        if isinstance(speed, float):
            self._controller.set_speed(speed)

    def _on_play_state_changed(self, playing: bool) -> None:
        tr = self._i18n
        self._btn_play_pause.setText(tr("operator.controls.pause" if playing else "operator.controls.play"))

    def _on_dataset_loaded(self, count: int) -> None:
        self._frame_count = count
        self._preset = self._controller.preset()
        if self._preset:
            self._update_metrics(None)
        self._history_table.setRowCount(0)

    def _on_frame_processed(self, index: int, frame_id: str, image, analysis: FrameAnalysis) -> None:
        if isinstance(image, QPixmap):
            pixmap = image
        else:
            pixmap = QPixmap.fromImage(image)
        self._current_pixmap = pixmap
        self._update_pixmap()
        self._frame_label.setText(f"{index + 1}/{self._frame_count} — {frame_id}")
        self._update_metrics(analysis)
        self._update_status(analysis.evaluation.status, analysis)
        self._append_history_row(index, frame_id, analysis)

    def _update_pixmap(self) -> None:
        if not self._current_pixmap:
            return
        label_size = self._image_label.size()
        scaled = self._current_pixmap.scaled(label_size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self._image_label.setPixmap(scaled)

    def resizeEvent(self, event) -> None:  # pragma: no cover - UI detail
        super().resizeEvent(event)
        self._update_pixmap()

    def _update_metrics(self, analysis: Optional[FrameAnalysis]) -> None:
        preset = self._preset
        metrics = analysis.evaluation.metrics if analysis else None
        dx_text = format_metric(metrics.dx_mm if metrics else None, "mm")
        dy_text = format_metric(metrics.dy_mm if metrics else None, "mm")
        theta_text = format_metric(metrics.dtheta_deg if metrics else None, "°")
        tol_mm = f"±{preset.tolerance_mm:.2f} mm" if preset else ""
        tol_deg = f"±{preset.tolerance_deg:.2f}°" if preset else ""
        dx_line = f"dx: {dx_text}"
        dy_line = f"dy: {dy_text}"
        theta_line = f"θ: {theta_text}"
        if tol_mm:
            dx_line += f"  ({tol_mm})"
            dy_line += f"  ({tol_mm})"
        if tol_deg:
            theta_line += f"  ({tol_deg})"
        self._metrics_labels["dx"].setText(dx_line)
        self._metrics_labels["dy"].setText(dy_line)
        self._metrics_labels["theta"].setText(theta_line)

    def _update_status(self, status: str, analysis: Optional[FrameAnalysis]) -> None:
        emoji, bg, fg = _STATUS_STYLE.get(status, ("⚪", "#424242", "#f5f5f5"))
        if status == "ok":
            key = "operator.status.ok"
        elif status == "out_of_tolerance":
            key = "operator.status.adjust"
        elif status == "not_found":
            key = "operator.status.not_found"
        else:
            key = "status.init"
        text = f"{emoji}\n{self._i18n(key)}"
        self._status_label.setText(text)
        self._status_label.setStyleSheet(
            f"border-radius: 12px; font-size: 42px; font-weight: 700; padding: 8px; background-color: {bg}; color: {fg};"
        )
    # endregion

    def _append_history_row(self, index: int, frame_id: str, analysis: FrameAnalysis) -> None:
        row = self._history_table.rowCount()
        self._history_table.insertRow(row)
        self._history_table.setItem(row, 0, QTableWidgetItem(f"{index + 1}: {frame_id}"))
        status_key = {
            "ok": "operator.status.ok",
            "out_of_tolerance": "operator.status.adjust",
            "not_found": "operator.status.not_found",
        }.get(analysis.evaluation.status, "status.error")
        status_item = QTableWidgetItem(self._i18n(status_key))
        self._history_table.setItem(row, 1, status_item)
        metrics = analysis.evaluation.metrics
        self._history_table.setItem(row, 2, QTableWidgetItem(format_metric(metrics.dx_mm if metrics else None, "mm")))
        self._history_table.setItem(row, 3, QTableWidgetItem(format_metric(metrics.dy_mm if metrics else None, "mm")))
        self._history_table.setItem(row, 4, QTableWidgetItem(format_metric(metrics.dtheta_deg if metrics else None, "°")))
        self._history_table.setItem(row, 5, QTableWidgetItem(f"{analysis.timestamp:.2f}"))

    def _on_snapshot(self) -> None:
        overlay = self._controller.current_overlay()
        if overlay is None:
            self.messageEmitted.emit(self._i18n("messages.snapshot.unavailable"))
            return
        default_dir = self._context.config.logging.output_dir / "snapshots"
        default_dir.mkdir(parents=True, exist_ok=True)
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        default_path = default_dir / f"snapshot_{timestamp}.png"
        path, _ = QFileDialog.getSaveFileName(
            self,
            self._i18n("messages.snapshot.saved"),
            str(default_path),
            "PNG (*.png)"
        )
        if not path:
            return
        success = cv2.imwrite(path, overlay)
        if success:
            self.messageEmitted.emit(self._i18n("messages.snapshot.saved"))
        else:
            self.errorEmitted.emit(self._i18n("messages.error.generic"))

    def _on_change_preset(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            self._i18n("menu.file.open_preset"),
            str(self._context.config.preset_path),
            "JSON (*.json)"
        )
        if not path:
            return
        self._context.config.preset_path = Path(path)
        self._context.save_config()
        self._controller.load_session()

    def initialize(self) -> None:
        self._controller.load_session()

    def stop(self) -> None:
        self._controller.pause()

    def capture_snapshot(self) -> None:
        self._on_snapshot()
