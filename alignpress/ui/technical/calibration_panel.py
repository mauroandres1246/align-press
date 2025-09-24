from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from typing import Optional

import cv2
import numpy as np
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QComboBox,
    QDoubleSpinBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from alignpress.core.calibration import (
    Calibration,
    aruco_mm_per_px,
    chessboard_mm_per_px,
    save_calibration,
)
from alignpress.ui.i18n import I18nManager
from alignpress.ui.utils import cv_to_qimage


class CalibrationPanel(QWidget):
    calibrationComputed = Signal(Calibration)
    errorRaised = Signal(str)
    messageRaised = Signal(str)
    calibrationSaved = Signal(Path)

    def __init__(self, i18n: I18nManager, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._i18n = i18n
        self._image_path: Optional[Path] = None
        self._current_calibration: Optional[Calibration] = None
        self._build_ui()
        self.retranslate_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        form_group = QGroupBox()
        form = QFormLayout(form_group)

        self._mode_combo = QComboBox()
        self._mode_combo.addItems(["chessboard", "aruco"])
        form.addRow(self._i18n("technical.calibration.title"), self._mode_combo)

        self._pattern_w = QSpinBox()
        self._pattern_h = QSpinBox()
        for widget in (self._pattern_w, self._pattern_h):
            widget.setRange(2, 20)
        self._pattern_w.setValue(7)
        self._pattern_h.setValue(5)
        pattern_layout = QHBoxLayout()
        pattern_layout.addWidget(self._pattern_w)
        pattern_layout.addWidget(QLabel("x"))
        pattern_layout.addWidget(self._pattern_h)
        form.addRow("Pattern", pattern_layout)

        self._square_mm = QDoubleSpinBox()
        self._square_mm.setRange(1.0, 100.0)
        self._square_mm.setDecimals(2)
        self._square_mm.setValue(25.0)
        form.addRow("Square mm", self._square_mm)

        self._aruco_dict = QComboBox()
        self._aruco_dict.setEditable(True)
        if hasattr(cv2, "aruco"):
            for name in dir(cv2.aruco):
                if name.startswith("DICT_"):
                    self._aruco_dict.addItem(name)
        if self._aruco_dict.count() == 0:
            self._aruco_dict.addItems(["DICT_5X5_50", "DICT_APRILTAG_36h11"])
        self._aruco_marker_mm = QDoubleSpinBox()
        self._aruco_marker_mm.setRange(1.0, 500.0)
        self._aruco_marker_mm.setDecimals(2)
        self._aruco_marker_mm.setValue(50.0)
        form.addRow("Diccionario", self._aruco_dict)
        form.addRow("Marker mm", self._aruco_marker_mm)

        layout.addWidget(form_group)

        buttons_layout = QHBoxLayout()
        self._btn_load = QPushButton()
        self._btn_compute = QPushButton()
        self._btn_save = QPushButton()
        buttons_layout.addWidget(self._btn_load)
        buttons_layout.addWidget(self._btn_compute)
        buttons_layout.addWidget(self._btn_save)
        layout.addLayout(buttons_layout)

        self._preview_label = QLabel()
        self._preview_label.setMinimumHeight(240)
        self._preview_label.setAlignment(Qt.AlignCenter)
        self._preview_label.setStyleSheet("background-color: #1e1e1e; border: 1px solid #2e2e2e;")
        layout.addWidget(self._preview_label)

        self._mm_per_px_label = QLabel("mm/px: —")
        layout.addWidget(self._mm_per_px_label)

        self._last_preview_pixmap: Optional[QPixmap] = None

        self._btn_load.clicked.connect(self._on_load_image)
        self._btn_compute.clicked.connect(self._on_compute)
        self._btn_save.clicked.connect(self._on_save)
        self._mode_combo.currentTextChanged.connect(self._on_mode_changed)
        self._on_mode_changed(self._mode_combo.currentText())

    def retranslate_ui(self) -> None:
        self._btn_load.setText(self._i18n("technical.calibration.load_image"))
        self._btn_compute.setText(self._i18n("technical.calibration.run"))
        self._btn_save.setText(self._i18n("technical.calibration.save"))

    def set_image(self, image_path: Path) -> None:
        self._image_path = image_path
        self._preview_label.setText(str(image_path))

    def set_existing_calibration(self, calibration: Calibration) -> None:
        self._current_calibration = calibration
        self._mm_per_px_label.setText(f"mm/px: {calibration.mm_per_px:.5f}")

    def _on_load_image(self) -> None:
        path_str, _ = QFileDialog.getOpenFileName(
            self,
            self._i18n("messages.choose_file"),
            str(self._image_path or ""),
            "Imágenes (*.png *.jpg *.jpeg *.bmp *.tif *.tiff)"
        )
        if not path_str:
            return
        self._image_path = Path(path_str)
        self._preview_label.setText(str(self._image_path))

    def _on_compute(self) -> None:
        if not self._image_path or not self._image_path.exists():
            self.errorRaised.emit(self._i18n("messages.calibration.missing"))
            return
        image = cv2.imread(str(self._image_path))
        if image is None:
            self.errorRaised.emit(self._i18n("messages.calibration.missing"))
            return

        mode = self._mode_combo.currentText()
        calibration: Optional[Calibration] = None
        preview = image.copy()

        if mode == "chessboard":
            pattern = (self._pattern_w.value(), self._pattern_h.value())
            square_mm = self._square_mm.value()
            calibration = chessboard_mm_per_px(image, pattern_size=pattern, square_size_mm=square_mm)
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            ret, corners = cv2.findChessboardCorners(gray, pattern, None)
            if ret and corners is not None:
                cv2.drawChessboardCorners(preview, pattern, corners, True)
        else:
            dictionary_name = self._aruco_dict.currentText()
            marker_mm = self._aruco_marker_mm.value()
            calibration = aruco_mm_per_px(image, marker_length_mm=marker_mm, dictionary_name=dictionary_name)
            if hasattr(cv2, "aruco"):
                aruco = cv2.aruco
                dict_map = {name: getattr(aruco, name) for name in dir(aruco) if name.startswith("DICT_")}
                if dictionary_name in dict_map:
                    dictionary = aruco.getPredefinedDictionary(dict_map[dictionary_name])
                    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
                    corners, ids, _ = aruco.detectMarkers(gray, dictionary)
                    if ids is not None and len(corners) > 0:
                        aruco.drawDetectedMarkers(preview, corners, ids)

        if calibration is None:
            self.errorRaised.emit(self._i18n("messages.error.generic"))
            return

        self._current_calibration = replace(calibration)
        self._mm_per_px_label.setText(f"mm/px: {calibration.mm_per_px:.5f}")
        qimg = cv_to_qimage(preview)
        pixmap = QPixmap.fromImage(qimg)
        self._last_preview_pixmap = pixmap
        self._update_preview_pixmap()
        self.calibrationComputed.emit(calibration)
        self.messageRaised.emit(self._i18n("technical.calibration.title"))

    def _on_save(self) -> None:
        if not self._current_calibration:
            self.errorRaised.emit(self._i18n("messages.error.generic"))
            return
        path_str, _ = QFileDialog.getSaveFileName(
            self,
            self._i18n("technical.calibration.save"),
            str(self._image_path or "calibration.json"),
            "JSON (*.json)"
        )
        if not path_str:
            return
        path = Path(path_str)
        save_calibration(self._current_calibration, path)
        self.messageRaised.emit(self._i18n("messages.export.completed"))
        self.calibrationSaved.emit(path)

    def _on_mode_changed(self, mode: str) -> None:
        is_chessboard = mode == "chessboard"
        self._pattern_w.setEnabled(is_chessboard)
        self._pattern_h.setEnabled(is_chessboard)
        self._square_mm.setEnabled(is_chessboard)
        self._aruco_dict.setEnabled(not is_chessboard)
        self._aruco_marker_mm.setEnabled(not is_chessboard)

    def resizeEvent(self, event) -> None:  # pragma: no cover - UI detail
        super().resizeEvent(event)
        self._update_preview_pixmap()

    def _update_preview_pixmap(self) -> None:
        if self._last_preview_pixmap is None:
            return
        scaled = self._last_preview_pixmap.scaled(
            self._preview_label.size(),
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation,
        )
        self._preview_label.setPixmap(scaled)
