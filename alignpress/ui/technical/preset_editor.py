from __future__ import annotations

from dataclasses import replace
from typing import Dict, Optional

import cv2
import numpy as np
from PySide6.QtCore import QObject, QPointF, QRectF, Qt, Signal
from PySide6.QtGui import QBrush, QColor, QPen, QPixmap
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QFormLayout,
    QGraphicsEllipseItem,
    QGraphicsItem,
    QGraphicsRectItem,
    QGraphicsScene,
    QGraphicsView,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from alignpress.core.presets import Preset
from alignpress.ui.i18n import I18nManager
from alignpress.ui.utils import cv_to_qimage


def _available_aruco_dictionaries() -> list[str]:
    if hasattr(cv2, "aruco"):
        return [name for name in dir(cv2.aruco) if name.startswith("DICT_")]
    return ["DICT_5X5_50", "DICT_4X4_50", "DICT_APRILTAG_36h11"]


class DraggableRectItem(QObject, QGraphicsRectItem):
    moved = Signal(float, float)

    def __init__(self, rect: QRectF) -> None:
        QObject.__init__(self)
        QGraphicsRectItem.__init__(self, rect)
        self.setFlags(
            QGraphicsItem.ItemIsMovable
            | QGraphicsItem.ItemIsSelectable
            | QGraphicsItem.ItemSendsGeometryChanges
        )
        self.setPen(QPen(QColor("#00e676"), 2, Qt.DashLine))

    def itemChange(self, change: QGraphicsItem.GraphicsItemChange, value):
        if change == QGraphicsItem.ItemPositionHasChanged:
            self.moved.emit(value.x(), value.y())
        return super().itemChange(change, value)


class DraggableCenterItem(QObject, QGraphicsEllipseItem):
    moved = Signal(float, float)

    def __init__(self, radius: float = 8.0) -> None:
        QObject.__init__(self)
        QGraphicsEllipseItem.__init__(self, -radius, -radius, radius * 2, radius * 2)
        self.setBrush(QBrush(QColor("#ffc400")))
        self.setPen(QPen(QColor("#ffab00"), 1.5))
        self.setFlags(
            QGraphicsItem.ItemIsMovable
            | QGraphicsItem.ItemIsSelectable
            | QGraphicsItem.ItemSendsGeometryChanges
        )

    def itemChange(self, change: QGraphicsItem.GraphicsItemChange, value):
        if change == QGraphicsItem.ItemPositionHasChanged:
            self.moved.emit(value.x(), value.y())
        return super().itemChange(change, value)


class PresetGraphicsView(QGraphicsView):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setRenderHints(self.renderHints() | Qt.Antialiasing | Qt.SmoothPixmapTransform)
        self.setScene(QGraphicsScene(self))
        self._background = self.scene().addPixmap(QPixmap())
        self._roi_item = DraggableRectItem(QRectF(0, 0, 100, 100))
        self.scene().addItem(self._roi_item)
        self._target_rect = QGraphicsRectItem(-50, -30, 100, 60)
        self._target_rect.setPen(QPen(QColor("#ff5252"), 2))
        self.scene().addItem(self._target_rect)
        self._target_center = DraggableCenterItem()
        self.scene().addItem(self._target_center)

    @property
    def roi_item(self) -> DraggableRectItem:
        return self._roi_item

    @property
    def target_center_item(self) -> DraggableCenterItem:
        return self._target_center

    @property
    def target_rect_item(self) -> QGraphicsRectItem:
        return self._target_rect

    def set_background(self, image: Optional[np.ndarray]) -> None:
        if image is None:
            self._background.setPixmap(QPixmap())
            return
        qimg = cv_to_qimage(image)
        pixmap = QPixmap.fromImage(qimg)
        self._background.setPixmap(pixmap)
        self.scene().setSceneRect(QRectF(0, 0, pixmap.width(), pixmap.height()))


class PresetEditorWidget(QWidget):
    presetChanged = Signal(Preset)

    def __init__(
        self,
        i18n: I18nManager,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._i18n = i18n
        self._updating = False
        self._preset: Optional[Preset] = None
        self._params: Dict[str, Dict[str, object]] = {}

        self._build_ui()
        self.retranslate_ui()

    def _build_ui(self) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)

        self._view = PresetGraphicsView(self)
        self._view.setMinimumSize(640, 480)
        layout.addWidget(self._view, stretch=2)

        side = QVBoxLayout()
        form = QFormLayout()

        self._roi_x = QSpinBox()
        self._roi_y = QSpinBox()
        self._roi_w = QSpinBox()
        self._roi_h = QSpinBox()
        for widget in (self._roi_x, self._roi_y, self._roi_w, self._roi_h):
            widget.setRange(0, 5000)
            widget.valueChanged.connect(self._on_roi_spin_changed)
        form.addRow("ROI X", self._roi_x)
        form.addRow("ROI Y", self._roi_y)
        form.addRow("ROI W", self._roi_w)
        form.addRow("ROI H", self._roi_h)

        self._center_x = QDoubleSpinBox()
        self._center_y = QDoubleSpinBox()
        for widget in (self._center_x, self._center_y):
            widget.setRange(0.0, 5000.0)
            widget.setDecimals(2)
            widget.valueChanged.connect(self._on_center_spin_changed)
        form.addRow("Centro X", self._center_x)
        form.addRow("Centro Y", self._center_y)

        self._size_w = QDoubleSpinBox()
        self._size_h = QDoubleSpinBox()
        for widget in (self._size_w, self._size_h):
            widget.setRange(1.0, 2000.0)
            widget.setDecimals(2)
            widget.valueChanged.connect(self._on_size_spin_changed)
        form.addRow("Logo W", self._size_w)
        form.addRow("Logo H", self._size_h)

        self._angle = QDoubleSpinBox()
        self._angle.setRange(-180.0, 180.0)
        self._angle.setDecimals(2)
        self._angle.valueChanged.connect(self._on_angle_changed)
        form.addRow("Ángulo", self._angle)

        self._tol_mm = QDoubleSpinBox()
        self._tol_mm.setRange(0.1, 100.0)
        self._tol_mm.setDecimals(2)
        self._tol_mm.valueChanged.connect(self._on_tol_changed)
        form.addRow("Tol mm", self._tol_mm)

        self._tol_deg = QDoubleSpinBox()
        self._tol_deg.setRange(0.1, 90.0)
        self._tol_deg.setDecimals(2)
        self._tol_deg.valueChanged.connect(self._on_tol_changed)
        form.addRow("Tol °", self._tol_deg)

        self._detection_mode = QComboBox()
        self._detection_mode.addItems(["contour", "aruco"])
        self._detection_mode.currentTextChanged.connect(self._emit_change)
        form.addRow("Detector", self._detection_mode)

        side.addLayout(form)

        self._view.roi_item.moved.connect(self._on_roi_item_moved)
        self._view.target_center_item.moved.connect(self._on_center_item_moved)

        detector_box = QGroupBox("Detector")
        det_layout = QFormLayout(detector_box)

        self._threshold_mode = QComboBox()
        self._threshold_mode.addItems(["otsu", "fixed"])
        self._threshold_value = QSpinBox()
        self._threshold_value.setRange(0, 255)
        self._invert_checkbox = QCheckBox()
        self._morph_k = QSpinBox()
        self._morph_k.setRange(0, 15)
        self._min_area = QSpinBox()
        self._min_area.setRange(0, 500000)
        det_layout.addRow("Umbral", self._threshold_mode)
        det_layout.addRow("Valor", self._threshold_value)
        det_layout.addRow("Invertir", self._invert_checkbox)
        det_layout.addRow("Morf k", self._morph_k)
        det_layout.addRow("Área mínima", self._min_area)

        aruco_box = QGroupBox("ArUco")
        aruco_layout = QFormLayout(aruco_box)
        self._aruco_dict = QComboBox()
        self._aruco_dict.setEditable(True)
        for name in _available_aruco_dictionaries():
            self._aruco_dict.addItem(name)
        self._aruco_marker_mm = QDoubleSpinBox()
        self._aruco_marker_mm.setRange(1.0, 500.0)
        self._aruco_marker_mm.setDecimals(2)
        aruco_layout.addRow("Diccionario", self._aruco_dict)
        aruco_layout.addRow("Marker mm", self._aruco_marker_mm)

        side.addWidget(detector_box)
        side.addWidget(aruco_box)

        layout.addLayout(side, stretch=1)

        self._threshold_mode.currentTextChanged.connect(self._on_threshold_mode_changed)
        self._threshold_value.valueChanged.connect(self._on_params_changed)
        self._invert_checkbox.toggled.connect(self._on_params_changed)
        self._morph_k.valueChanged.connect(self._on_params_changed)
        self._min_area.valueChanged.connect(self._on_params_changed)
        self._aruco_dict.currentTextChanged.connect(self._on_params_changed)
        self._aruco_marker_mm.valueChanged.connect(self._on_params_changed)

    def retranslate_ui(self) -> None:
        # Translations handled in TechnicalPage; placeholder texts remain generic
        pass

    # region Public API
    def set_background(self, image: Optional[np.ndarray]) -> None:
        self._view.set_background(image)

    def set_preset(self, preset: Preset) -> None:
        self._preset = preset
        self._params = {
            "contour": dict(preset.params.get("contour", {})),
            "aruco": dict(preset.params.get("aruco", {})),
        }
        self._update_from_preset()

    def current_preset(self) -> Preset:
        if not self._preset:
            raise RuntimeError("No preset loaded")
        preset = replace(self._preset)
        preset.roi = (self._roi_x.value(), self._roi_y.value(), self._roi_w.value(), self._roi_h.value())
        preset.target_center_px = (self._center_x.value(), self._center_y.value())
        preset.target_size_px = (self._size_w.value(), self._size_h.value())
        preset.target_angle_deg = self._angle.value()
        preset.tolerance_mm = self._tol_mm.value()
        preset.tolerance_deg = self._tol_deg.value()
        preset.detection_mode = self._detection_mode.currentText()
        preset.params = {
            "contour": {
                "threshold": self._threshold_mode.currentText() or "otsu",
                "thr_value": self._threshold_value.value(),
                "invert": self._invert_checkbox.isChecked(),
                "morph_k": self._morph_k.value(),
                "min_area": self._min_area.value(),
            },
            "aruco": {
                "dictionary": self._aruco_dict.currentText() or "DICT_5X5_50",
                "marker_length_mm": self._aruco_marker_mm.value(),
            },
        }
        return preset
    # endregion

    def _update_from_preset(self) -> None:
        if not self._preset:
            return
        self._updating = True
        roi = self._preset.roi
        self._roi_x.setValue(int(roi[0]))
        self._roi_y.setValue(int(roi[1]))
        self._roi_w.setValue(int(roi[2]))
        self._roi_h.setValue(int(roi[3]))
        self._center_x.setValue(float(self._preset.target_center_px[0]))
        self._center_y.setValue(float(self._preset.target_center_px[1]))
        self._size_w.setValue(float(self._preset.target_size_px[0]))
        self._size_h.setValue(float(self._preset.target_size_px[1]))
        self._angle.setValue(float(self._preset.target_angle_deg))
        self._tol_mm.setValue(float(self._preset.tolerance_mm))
        self._tol_deg.setValue(float(self._preset.tolerance_deg))
        index = self._detection_mode.findText(self._preset.detection_mode)
        if index != -1:
            self._detection_mode.setCurrentIndex(index)
        else:
            self._detection_mode.setCurrentIndex(0)
        self._apply_graphics()

        contour = self._params.get("contour", {})
        mode = str(contour.get("threshold", "otsu"))
        idx = self._threshold_mode.findText(mode)
        if idx != -1:
            self._threshold_mode.setCurrentIndex(idx)
        else:
            self._threshold_mode.setCurrentIndex(0)
        self._threshold_value.setEnabled(self._threshold_mode.currentText() == "fixed")
        self._threshold_value.setValue(int(contour.get("thr_value", 120)))
        self._invert_checkbox.setChecked(bool(contour.get("invert", False)))
        self._morph_k.setValue(int(contour.get("morph_k", 3)))
        self._min_area.setValue(int(contour.get("min_area", 800)))

        aruco = self._params.get("aruco", {})
        dict_name = str(aruco.get("dictionary", "DICT_5X5_50"))
        idx_dict = self._aruco_dict.findText(dict_name)
        if idx_dict != -1:
            self._aruco_dict.setCurrentIndex(idx_dict)
        else:
            self._aruco_dict.setEditText(dict_name)
        self._aruco_marker_mm.setValue(float(aruco.get("marker_length_mm", 50.0)))
        self._updating = False

    def _apply_graphics(self) -> None:
        if not self._preset:
            return
        x, y, w, h = self._preset.roi
        self._view.roi_item.setRect(0, 0, w, h)
        self._view.roi_item.setPos(x, y)
        cx, cy = self._preset.target_center_px
        self._view.target_center_item.setPos(QPointF(cx, cy))
        width, height = self._preset.target_size_px
        rect_item = self._view.target_rect_item
        rect_item.setRect(-width / 2.0, -height / 2.0, width, height)
        rect_item.setPos(QPointF(cx, cy))
        rect_item.setRotation(self._preset.target_angle_deg)

    # region Event callbacks
    def _on_roi_spin_changed(self) -> None:
        if self._updating:
            return
        x, y, w, h = self._roi_x.value(), self._roi_y.value(), self._roi_w.value(), self._roi_h.value()
        self._preset = replace(self._preset, roi=(x, y, w, h)) if self._preset else None
        self._view.roi_item.setRect(0, 0, w, h)
        self._view.roi_item.setPos(x, y)
        self._emit_change()

    def _on_center_spin_changed(self) -> None:
        if self._updating:
            return
        cx, cy = self._center_x.value(), self._center_y.value()
        self._preset = replace(self._preset, target_center_px=(cx, cy)) if self._preset else None
        self._view.target_center_item.setPos(QPointF(cx, cy))
        self._view.target_rect_item.setPos(QPointF(cx, cy))
        self._emit_change()

    def _on_size_spin_changed(self) -> None:
        if self._updating:
            return
        width, height = self._size_w.value(), self._size_h.value()
        if self._preset:
            self._preset = replace(self._preset, target_size_px=(width, height))
        self._view.target_rect_item.setRect(-width / 2.0, -height / 2.0, width, height)
        self._emit_change()

    def _on_angle_changed(self, value: float) -> None:
        if self._updating:
            return
        if self._preset:
            self._preset = replace(self._preset, target_angle_deg=value)
        self._view.target_rect_item.setRotation(value)
        self._emit_change()

    def _on_tol_changed(self) -> None:
        if self._updating:
            return
        if self._preset:
            self._preset = replace(
                self._preset,
                tolerance_mm=self._tol_mm.value(),
                tolerance_deg=self._tol_deg.value(),
            )
        self._emit_change()

    def _on_roi_item_moved(self, x: float, y: float) -> None:
        if self._updating:
            return
        self._updating = True
        self._roi_x.setValue(int(round(x)))
        self._roi_y.setValue(int(round(y)))
        self._updating = False
        if self._preset:
            roi = (self._roi_x.value(), self._roi_y.value(), self._roi_w.value(), self._roi_h.value())
            self._preset = replace(self._preset, roi=roi)
        self._emit_change()

    def _on_center_item_moved(self, x: float, y: float) -> None:
        if self._updating:
            return
        self._updating = True
        self._center_x.setValue(round(x, 2))
        self._center_y.setValue(round(y, 2))
        self._updating = False
        if self._preset:
            self._preset = replace(self._preset, target_center_px=(x, y))
            self._view.target_rect_item.setPos(QPointF(x, y))
        self._emit_change()

    def _on_params_changed(self) -> None:
        if self._updating:
            return
        self._emit_change()

    def _on_threshold_mode_changed(self, mode: str) -> None:
        self._threshold_value.setEnabled(mode == "fixed")
        self._on_params_changed()

    def _emit_change(self) -> None:
        if self._updating or not self._preset:
            return
        self.presetChanged.emit(self.current_preset())
