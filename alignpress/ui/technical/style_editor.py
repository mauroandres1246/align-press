from __future__ import annotations

import json
import shutil
import time
from pathlib import Path
from typing import Dict, Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QDoubleSpinBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPlainTextEdit,
    QPushButton,
    QSpinBox,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from alignpress.domain.style import LogoDefinition, StyleDefinition


class StyleEditorWidget(QWidget):
    messageEmitted = Signal(str)
    errorEmitted = Signal(str)
    dataChanged = Signal()

    def __init__(self, directory: Path, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._dir = directory
        self._current_path: Optional[Path] = None
        self._current_logo: Optional[LogoDefinition] = None
        self._style: Optional[StyleDefinition] = None
        self._building = False

        self._build_ui()
        self.refresh()

    # region UI construction
    def _build_ui(self) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        self._list = QListWidget()
        self._list.setSelectionMode(QListWidget.SingleSelection)
        layout.addWidget(self._list, stretch=1)

        right = QVBoxLayout()
        right.setSpacing(10)

        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignRight)
        form.setFormAlignment(Qt.AlignTop)

        self._style_name = QLabel("—")
        form.addRow("Nombre", self._style_name)

        self._style_version = QLabel("—")
        form.addRow("Versión", self._style_version)

        right.addLayout(form)

        buttons = QHBoxLayout()
        self._btn_new = QPushButton("Nuevo")
        self._btn_dup = QPushButton("Duplicar")
        self._btn_delete = QPushButton("Eliminar")
        buttons.addWidget(self._btn_new)
        buttons.addWidget(self._btn_dup)
        buttons.addWidget(self._btn_delete)
        right.addLayout(buttons)

        buttons2 = QHBoxLayout()
        self._btn_import = QPushButton("Importar")
        self._btn_export = QPushButton("Exportar")
        self._btn_save = QPushButton("Guardar")
        buttons2.addWidget(self._btn_import)
        buttons2.addWidget(self._btn_export)
        buttons2.addStretch(1)
        buttons2.addWidget(self._btn_save)
        right.addLayout(buttons2)

        self._logo_list = QListWidget()
        self._logo_list.setSelectionMode(QListWidget.SingleSelection)
        right.addWidget(QLabel("Logos"))
        right.addWidget(self._logo_list, stretch=1)

        logo_buttons = QHBoxLayout()
        self._btn_logo_add = QPushButton("Agregar logo")
        self._btn_logo_dup = QPushButton("Duplicar")
        self._btn_logo_remove = QPushButton("Eliminar")
        logo_buttons.addWidget(self._btn_logo_add)
        logo_buttons.addWidget(self._btn_logo_dup)
        logo_buttons.addWidget(self._btn_logo_remove)
        right.addLayout(logo_buttons)

        self._logo_tabs = QTabWidget()
        right.addWidget(self._logo_tabs, stretch=2)

        main_tab = QWidget()
        main_form = QFormLayout(main_tab)

        self._logo_id_edit = QLabel("—")
        main_form.addRow("ID", self._logo_id_edit)

        self._logo_display_edit = QLabel("—")
        main_form.addRow("Nombre", self._logo_display_edit)

        self._detector_combo = QComboBox()
        self._detector_combo.addItems(["contour", "aruco"])
        main_form.addRow("Detector", self._detector_combo)

        self._aruco_spin = QSpinBox()
        self._aruco_spin.setRange(-1, 1000)
        main_form.addRow("ArUco ID", self._aruco_spin)

        self._instructions_edit = QPlainTextEdit()
        self._instructions_edit.setPlaceholderText("Instrucciones opcionales para el operador")
        self._instructions_edit.setMaximumHeight(80)
        main_form.addRow("Instrucciones", self._instructions_edit)

        self._logo_tabs.addTab(main_tab, "General")

        geom_tab = QWidget()
        geom_form = QFormLayout(geom_tab)

        self._center_x_spin = QDoubleSpinBox()
        self._center_x_spin.setRange(-2000.0, 2000.0)
        self._center_x_spin.setDecimals(2)
        self._center_y_spin = QDoubleSpinBox()
        self._center_y_spin.setRange(-2000.0, 2000.0)
        self._center_y_spin.setDecimals(2)
        center_layout = QHBoxLayout()
        center_layout.addWidget(self._center_x_spin)
        center_layout.addWidget(self._center_y_spin)
        geom_form.addRow("Centro (mm)", center_layout)

        self._size_w_spin = QDoubleSpinBox()
        self._size_w_spin.setRange(1.0, 2000.0)
        self._size_w_spin.setDecimals(2)
        self._size_h_spin = QDoubleSpinBox()
        self._size_h_spin.setRange(1.0, 2000.0)
        self._size_h_spin.setDecimals(2)
        size_layout = QHBoxLayout()
        size_layout.addWidget(self._size_w_spin)
        size_layout.addWidget(self._size_h_spin)
        geom_form.addRow("Tamaño logo (mm)", size_layout)

        self._roi_w_spin = QDoubleSpinBox()
        self._roi_w_spin.setRange(10.0, 4000.0)
        self._roi_w_spin.setDecimals(2)
        self._roi_h_spin = QDoubleSpinBox()
        self._roi_h_spin.setRange(10.0, 4000.0)
        self._roi_h_spin.setDecimals(2)
        roi_layout = QHBoxLayout()
        roi_layout.addWidget(self._roi_w_spin)
        roi_layout.addWidget(self._roi_h_spin)
        geom_form.addRow("ROI (mm)", roi_layout)

        self._angle_spin = QDoubleSpinBox()
        self._angle_spin.setRange(-180.0, 180.0)
        self._angle_spin.setDecimals(2)
        geom_form.addRow("Ángulo (°)", self._angle_spin)

        self._tol_mm_spin = QDoubleSpinBox()
        self._tol_mm_spin.setRange(0.1, 100.0)
        self._tol_mm_spin.setDecimals(2)
        self._tol_deg_spin = QDoubleSpinBox()
        self._tol_deg_spin.setRange(0.1, 45.0)
        self._tol_deg_spin.setDecimals(2)
        tol_layout = QHBoxLayout()
        tol_layout.addWidget(self._tol_mm_spin)
        tol_layout.addWidget(self._tol_deg_spin)
        geom_form.addRow("Tolerancias", tol_layout)

        self._logo_tabs.addTab(geom_tab, "Geometría")

        params_tab = QWidget()
        params_layout = QVBoxLayout(params_tab)
        self._params_edit = QPlainTextEdit()
        self._params_edit.setPlaceholderText("JSON de parámetros del detector")
        params_layout.addWidget(self._params_edit)
        self._logo_tabs.addTab(params_tab, "Parámetros")

        layout.addLayout(right, stretch=3)

        # Connections
        self._list.currentItemChanged.connect(self._on_style_selected)
        self._btn_new.clicked.connect(self._create_new_style)
        self._btn_dup.clicked.connect(self._duplicate_style)
        self._btn_delete.clicked.connect(self._delete_style)
        self._btn_import.clicked.connect(self._import_style)
        self._btn_export.clicked.connect(self._export_style)
        self._btn_save.clicked.connect(self._save_style)

        self._logo_list.currentItemChanged.connect(self._on_logo_selected)
        self._btn_logo_add.clicked.connect(self._add_logo)
        self._btn_logo_dup.clicked.connect(self._duplicate_logo)
        self._btn_logo_remove.clicked.connect(self._remove_logo)
    # endregion

    # region Styles management
    def refresh(self) -> None:
        self._building = True
        self._list.clear()
        for path in sorted(self._dir.glob("*.json")):
            try:
                style = StyleDefinition.from_json(path)
                item = QListWidgetItem(f"{style.name} v{style.version}")
            except Exception:
                item = QListWidgetItem(path.name)
            item.setData(Qt.UserRole, path)
            self._list.addItem(item)
        self._building = False
        if self._list.count() > 0:
            self._list.setCurrentRow(0)
        else:
            self._clear_style()

    def _clear_style(self) -> None:
        self._current_path = None
        self._style = None
        self._style_name.setText("—")
        self._style_version.setText("—")
        self._logo_list.clear()
        self._clear_logo_form()

    def _load_style(self, path: Path) -> None:
        try:
            style = StyleDefinition.from_json(path)
        except Exception as exc:
            self.errorEmitted.emit(str(exc))
            return
        self._style = style
        self._current_path = path
        self._style_name.setText(style.name)
        self._style_version.setText(style.version)
        self._populate_logo_list()

    def _populate_logo_list(self) -> None:
        self._logo_list.clear()
        if not self._style:
            return
        for logo in self._style.logos:
            item = QListWidgetItem(f"{logo.display_name} ({logo.logo_id})")
            item.setData(Qt.UserRole, logo.logo_id)
            self._logo_list.addItem(item)
        if self._logo_list.count() > 0:
            self._logo_list.setCurrentRow(0)
        else:
            self._clear_logo_form()

    def _on_style_selected(self, item: QListWidgetItem, _: QListWidgetItem) -> None:
        if self._building:
            return
        if item is None:
            self._clear_style()
            return
        path = item.data(Qt.UserRole)
        if not isinstance(path, Path):
            return
        self._load_style(path)

    def _create_new_style(self) -> None:
        timestamp = int(time.time())
        path = self._dir / f"style_{timestamp}.json"
        style = StyleDefinition(name=f"Estilo {timestamp}", version="1.0")
        style.to_json(path)
        self.refresh()
        self.messageEmitted.emit("Estilo creado")

    def _duplicate_style(self) -> None:
        if not self._current_path:
            return
        timestamp = int(time.time())
        target = self._dir / f"{self._current_path.stem}_copy_{timestamp}.json"
        shutil.copy(self._current_path, target)
        self.refresh()
        self.messageEmitted.emit("Estilo duplicado")

    def _delete_style(self) -> None:
        if not self._current_path:
            return
        self._current_path.unlink(missing_ok=True)
        self.refresh()
        self.messageEmitted.emit("Estilo eliminado")

    def _import_style(self) -> None:
        from PySide6.QtWidgets import QFileDialog

        path, _ = QFileDialog.getOpenFileName(self, "Importar estilo", str(self._dir), "JSON (*.json)")
        if not path:
            return
        shutil.copy(Path(path), self._dir / Path(path).name)
        self.refresh()
        self.messageEmitted.emit("Estilo importado")

    def _export_style(self) -> None:
        if not self._current_path:
            return
        from PySide6.QtWidgets import QFileDialog

        path, _ = QFileDialog.getSaveFileName(self, "Exportar estilo", str(self._current_path.name), "JSON (*.json)")
        if not path:
            return
        shutil.copy(self._current_path, Path(path))
        self.messageEmitted.emit("Estilo exportado")

    def _save_style(self) -> None:
        if not self._style:
            return
        self._update_logo_from_form()  # ensure current logo saved
        if not self._current_path:
            timestamp = int(time.time())
            self._current_path = self._dir / f"style_{timestamp}.json"
        try:
            self._style.to_json(self._current_path)
            self.messageEmitted.emit("Estilo guardado")
            self.dataChanged.emit()
            self.refresh()
        except Exception as exc:
            self.errorEmitted.emit(str(exc))
    # endregion

    # region Logos
    def _clear_logo_form(self) -> None:
        self._current_logo = None
        self._logo_id_edit.setText("—")
        self._logo_display_edit.setText("—")
        self._detector_combo.setCurrentIndex(0)
        self._aruco_spin.setValue(-1)
        self._instructions_edit.setPlainText("")
        self._center_x_spin.setValue(0.0)
        self._center_y_spin.setValue(0.0)
        self._size_w_spin.setValue(100.0)
        self._size_h_spin.setValue(60.0)
        self._roi_w_spin.setValue(200.0)
        self._roi_h_spin.setValue(200.0)
        self._angle_spin.setValue(0.0)
        self._tol_mm_spin.setValue(3.0)
        self._tol_deg_spin.setValue(2.0)
        self._params_edit.setPlainText(json.dumps({"threshold": "otsu"}, indent=2))

    def _load_logo_to_form(self, logo: LogoDefinition) -> None:
        self._current_logo = logo
        self._logo_id_edit.setText(logo.logo_id)
        self._logo_display_edit.setText(logo.display_name)
        idx = self._detector_combo.findText(logo.detector)
        self._detector_combo.setCurrentIndex(idx if idx >= 0 else 0)
        self._aruco_spin.setValue(logo.aruco_id if logo.aruco_id is not None else -1)
        self._instructions_edit.setPlainText(logo.instructions or "")
        self._center_x_spin.setValue(logo.target_center_mm[0])
        self._center_y_spin.setValue(logo.target_center_mm[1])
        self._size_w_spin.setValue(logo.target_size_mm[0])
        self._size_h_spin.setValue(logo.target_size_mm[1])
        self._roi_w_spin.setValue(logo.roi_size_mm[0])
        self._roi_h_spin.setValue(logo.roi_size_mm[1])
        self._angle_spin.setValue(logo.target_angle_deg)
        self._tol_mm_spin.setValue(logo.tolerance_mm)
        self._tol_deg_spin.setValue(logo.tolerance_deg)
        self._params_edit.setPlainText(json.dumps(logo.params, indent=2))

    def _update_logo_from_form(self) -> None:
        if not self._current_logo or not self._style:
            return
        try:
            params = json.loads(self._params_edit.toPlainText() or "{}")
        except json.JSONDecodeError as exc:
            self.errorEmitted.emit(f"Parámetros inválidos: {exc}")
            return

        logo = self._current_logo
        logo.detector = self._detector_combo.currentText()
        logo.params = params
        logo.target_center_mm = (self._center_x_spin.value(), self._center_y_spin.value())
        logo.target_size_mm = (self._size_w_spin.value(), self._size_h_spin.value())
        logo.roi_size_mm = (self._roi_w_spin.value(), self._roi_h_spin.value())
        logo.target_angle_deg = self._angle_spin.value()
        logo.tolerance_mm = self._tol_mm_spin.value()
        logo.tolerance_deg = self._tol_deg_spin.value()
        logo.instructions = self._instructions_edit.toPlainText() or None
        aruco_id = self._aruco_spin.value()
        logo.aruco_id = None if aruco_id < 0 else aruco_id

    def _on_logo_selected(self, item: QListWidgetItem, _: QListWidgetItem) -> None:
        if self._style is None or item is None:
            self._clear_logo_form()
            return
        logo_id = item.data(Qt.UserRole)
        logo = next((lg for lg in self._style.logos if lg.logo_id == logo_id), None)
        if logo:
            # Save previous selection first
            self._update_logo_from_form()
            self._load_logo_to_form(logo)

    def _add_logo(self) -> None:
        if not self._style:
            return
        timestamp = int(time.time())
        logo = LogoDefinition(
            logo_id=f"logo_{timestamp}",
            display_name=f"Logo {timestamp}",
            detector="contour",
            params={"threshold": "otsu"},
            target_center_mm=(100.0, 100.0),
            target_size_mm=(120.0, 80.0),
            roi_size_mm=(240.0, 200.0),
            target_angle_deg=0.0,
            tolerance_mm=3.0,
            tolerance_deg=2.0,
        )
        self._style.logos.append(logo)
        self._populate_logo_list()
        self.messageEmitted.emit("Logo agregado")

    def _duplicate_logo(self) -> None:
        if not self._style or not self._current_logo:
            return
        timestamp = int(time.time())
        clone = LogoDefinition.from_dict(self._current_logo.to_dict())
        clone.logo_id = f"{clone.logo_id}_copy_{timestamp}"
        self._style.logos.append(clone)
        self._populate_logo_list()
        self.messageEmitted.emit("Logo duplicado")

    def _remove_logo(self) -> None:
        if not self._style or not self._current_logo:
            return
        self._style.logos = [lg for lg in self._style.logos if lg.logo_id != self._current_logo.logo_id]
        self._populate_logo_list()
        self.messageEmitted.emit("Logo eliminado")
    # endregion
