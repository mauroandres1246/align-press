from __future__ import annotations

import json
import shutil
import time
from pathlib import Path
from typing import Dict, List, Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QDoubleSpinBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from alignpress.domain.style import StyleDefinition
from alignpress.domain.variant import LogoOverride, SizeVariant


class VariantEditorWidget(QWidget):
    messageEmitted = Signal(str)
    errorEmitted = Signal(str)
    dataChanged = Signal()

    def __init__(self, directory: Path, styles_dir: Path, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._dir = directory
        self._styles_dir = styles_dir
        self._variant: Optional[SizeVariant] = None
        self._current_path: Optional[Path] = None
        self._current_override: Optional[LogoOverride] = None
        self._building = False

        self._build_ui()
        self.refresh()

    # region UI
    def _build_ui(self) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        self._list = QListWidget()
        self._list.setSelectionMode(QListWidget.SingleSelection)
        layout.addWidget(self._list, stretch=1)

        right = QVBoxLayout()
        right.setSpacing(8)

        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignRight)

        self._variant_name = QLabel("—")
        form.addRow("Nombre", self._variant_name)

        self._style_combo = QComboBox()
        self._style_combo.setEditable(False)
        form.addRow("Estilo base", self._style_combo)

        self._scale_spin = QDoubleSpinBox()
        self._scale_spin.setRange(0.5, 2.0)
        self._scale_spin.setDecimals(3)
        self._scale_spin.setValue(1.0)
        form.addRow("Escala", self._scale_spin)

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

        right.addWidget(QLabel("Overrides"))
        self._override_list = QListWidget()
        self._override_list.setSelectionMode(QListWidget.SingleSelection)
        right.addWidget(self._override_list, stretch=1)

        override_buttons = QHBoxLayout()
        self._btn_override_add = QPushButton("Agregar")
        self._btn_override_remove = QPushButton("Eliminar")
        override_buttons.addWidget(self._btn_override_add)
        override_buttons.addWidget(self._btn_override_remove)
        right.addLayout(override_buttons)

        override_form = QFormLayout()
        override_form.setLabelAlignment(Qt.AlignRight)

        self._logo_combo = QComboBox()
        self._logo_combo.setEditable(True)
        override_form.addRow("Logo", self._logo_combo)

        self._offset_x_spin = QDoubleSpinBox()
        self._offset_x_spin.setRange(-200.0, 200.0)
        self._offset_x_spin.setDecimals(2)
        self._offset_y_spin = QDoubleSpinBox()
        self._offset_y_spin.setRange(-200.0, 200.0)
        self._offset_y_spin.setDecimals(2)
        offset_layout = QHBoxLayout()
        offset_layout.addWidget(self._offset_x_spin)
        offset_layout.addWidget(self._offset_y_spin)
        override_form.addRow("Offset (mm)", offset_layout)

        self._override_scale_spin = QDoubleSpinBox()
        self._override_scale_spin.setRange(0.5, 2.0)
        self._override_scale_spin.setDecimals(3)
        self._override_scale_spin.setValue(1.0)
        override_form.addRow("Escala", self._override_scale_spin)

        self._angle_offset_spin = QDoubleSpinBox()
        self._angle_offset_spin.setRange(-45.0, 45.0)
        self._angle_offset_spin.setDecimals(2)
        override_form.addRow("Ángulo extra", self._angle_offset_spin)

        self._tol_mm_override_spin = QDoubleSpinBox()
        self._tol_mm_override_spin.setRange(0.0, 100.0)
        self._tol_mm_override_spin.setDecimals(2)
        self._tol_deg_override_spin = QDoubleSpinBox()
        self._tol_deg_override_spin.setRange(0.0, 45.0)
        self._tol_deg_override_spin.setDecimals(2)
        tol_override_layout = QHBoxLayout()
        tol_override_layout.addWidget(self._tol_mm_override_spin)
        tol_override_layout.addWidget(self._tol_deg_override_spin)
        override_form.addRow("Tol. override", tol_override_layout)

        right.addLayout(override_form)
        layout.addLayout(right, stretch=3)

        # Signals
        self._list.currentItemChanged.connect(self._on_variant_selected)
        self._btn_new.clicked.connect(self._create_new_variant)
        self._btn_dup.clicked.connect(self._duplicate_variant)
        self._btn_delete.clicked.connect(self._delete_variant)
        self._btn_import.clicked.connect(self._import_variant)
        self._btn_export.clicked.connect(self._export_variant)
        self._btn_save.clicked.connect(self._save_variant)

        self._override_list.currentItemChanged.connect(self._on_override_selected)
        self._btn_override_add.clicked.connect(self._add_override)
        self._btn_override_remove.clicked.connect(self._remove_override)
        self._style_combo.currentIndexChanged.connect(lambda _: self._populate_logo_combo())
    # endregion

    # region Variant list
    def refresh(self) -> None:
        self._populate_style_combo()
        self._building = True
        self._list.clear()
        for path in sorted(self._dir.glob("*.json")):
            try:
                variant = SizeVariant.from_json(path)
                item = QListWidgetItem(f"{variant.name} ({variant.style_name})")
            except Exception:
                item = QListWidgetItem(path.name)
            item.setData(Qt.UserRole, path)
            self._list.addItem(item)
        self._building = False
        if self._list.count() > 0:
            self._list.setCurrentRow(0)
        else:
            self._clear_variant()

    def _populate_style_combo(self) -> None:
        self._style_combo.blockSignals(True)
        self._style_combo.clear()
        for path in sorted(self._styles_dir.glob("*.json")):
            try:
                style = StyleDefinition.from_json(path)
                label = f"{style.name} ({path.name})"
                self._style_combo.addItem(label, style.name)
            except Exception:
                continue
        self._style_combo.blockSignals(False)

    def _clear_variant(self) -> None:
        self._variant = None
        self._current_path = None
        self._variant_name.setText("—")
        if self._style_combo.count() > 0:
            self._style_combo.setCurrentIndex(0)
        self._scale_spin.setValue(1.0)
        self._override_list.clear()
        self._clear_override_form()

    def _load_variant(self, path: Path) -> None:
        try:
            variant = SizeVariant.from_json(path)
        except Exception as exc:
            self.errorEmitted.emit(str(exc))
            return
        self._variant = variant
        self._current_path = path
        self._variant_name.setText(variant.name)
        index = self._style_combo.findData(variant.style_name)
        if index >= 0:
            self._style_combo.setCurrentIndex(index)
        self._scale_spin.setValue(variant.scale)
        self._populate_override_list()

    def _on_variant_selected(self, item: QListWidgetItem, _: QListWidgetItem) -> None:
        if self._building:
            return
        if item is None:
            self._clear_variant()
            return
        path = item.data(Qt.UserRole)
        if not isinstance(path, Path):
            return
        self._load_variant(path)

    def _create_new_variant(self) -> None:
        timestamp = int(time.time())
        path = self._dir / f"variant_{timestamp}.json"
        style_name = self._style_combo.currentData() if self._style_combo.count() > 0 else ""
        variant = SizeVariant(name=f"Talla {timestamp}", style_name=style_name or "style")
        variant.to_json(path)
        self.refresh()
        self.messageEmitted.emit("Talla creada")

    def _duplicate_variant(self) -> None:
        if not self._current_path:
            return
        timestamp = int(time.time())
        target = self._dir / f"{self._current_path.stem}_copy_{timestamp}.json"
        shutil.copy(self._current_path, target)
        self.refresh()
        self.messageEmitted.emit("Talla duplicada")

    def _delete_variant(self) -> None:
        if not self._current_path:
            return
        self._current_path.unlink(missing_ok=True)
        self.refresh()
        self.messageEmitted.emit("Talla eliminada")

    def _import_variant(self) -> None:
        from PySide6.QtWidgets import QFileDialog

        path, _ = QFileDialog.getOpenFileName(self, "Importar talla", str(self._dir), "JSON (*.json)")
        if not path:
            return
        shutil.copy(Path(path), self._dir / Path(path).name)
        self.refresh()
        self.messageEmitted.emit("Talla importada")

    def _export_variant(self) -> None:
        if not self._current_path:
            return
        from PySide6.QtWidgets import QFileDialog

        path, _ = QFileDialog.getSaveFileName(self, "Exportar talla", str(self._current_path.name), "JSON (*.json)")
        if not path:
            return
        shutil.copy(self._current_path, Path(path))
        self.messageEmitted.emit("Talla exportada")

    def _save_variant(self) -> None:
        if not self._variant:
            return
        self._update_override_from_form()
        self._variant.style_name = self._style_combo.currentData() or self._variant.style_name
        self._variant.scale = self._scale_spin.value()
        if not self._current_path:
            timestamp = int(time.time())
            self._current_path = self._dir / f"variant_{timestamp}.json"
        try:
            self._variant.to_json(self._current_path)
            self.dataChanged.emit()
            self.messageEmitted.emit("Talla guardada")
            self.refresh()
        except Exception as exc:
            self.errorEmitted.emit(str(exc))
    # endregion

    # region Overrides
    def _clear_override_form(self) -> None:
        self._current_override = None
        self._logo_combo.clearEditText()
        self._offset_x_spin.setValue(0.0)
        self._offset_y_spin.setValue(0.0)
        self._override_scale_spin.setValue(1.0)
        self._angle_offset_spin.setValue(0.0)
        self._tol_mm_override_spin.setValue(0.0)
        self._tol_deg_override_spin.setValue(0.0)

    def _populate_logo_combo(self) -> None:
        self._logo_combo.blockSignals(True)
        current = self._logo_combo.currentText()
        self._logo_combo.clear()
        style_name = self._style_combo.currentData()
        logos: List[str] = []
        if style_name:
            for path in self._styles_dir.glob("*.json"):
                try:
                    style = StyleDefinition.from_json(path)
                except Exception:
                    continue
                if style.name == style_name:
                    logos = [logo.logo_id for logo in style.logos]
                    break
        for logo_id in logos:
            self._logo_combo.addItem(logo_id)
        if current:
            index = self._logo_combo.findText(current)
            if index >= 0:
                self._logo_combo.setCurrentIndex(index)
            else:
                self._logo_combo.setEditText(current)
        self._logo_combo.blockSignals(False)

    def _populate_override_list(self) -> None:
        self._override_list.clear()
        if not self._variant:
            return
        for override in self._variant.logos:
            item = QListWidgetItem(override.logo_id)
            item.setData(Qt.UserRole, override.logo_id)
            self._override_list.addItem(item)
        if self._override_list.count() > 0:
            self._override_list.setCurrentRow(0)
        else:
            self._clear_override_form()

    def _on_override_selected(self, item: QListWidgetItem, _: QListWidgetItem) -> None:
        if self._variant is None or item is None:
            self._clear_override_form()
            return
        logo_id = item.data(Qt.UserRole)
        override = next((ov for ov in self._variant.logos if ov.logo_id == logo_id), None)
        if override:
            self._update_override_from_form()
            self._load_override_to_form(override)

    def _load_override_to_form(self, override: LogoOverride) -> None:
        self._current_override = override
        self._logo_combo.setEditText(override.logo_id)
        self._offset_x_spin.setValue(override.offset_mm[0])
        self._offset_y_spin.setValue(override.offset_mm[1])
        self._override_scale_spin.setValue(override.scale)
        self._angle_offset_spin.setValue(override.angle_offset_deg)
        self._tol_mm_override_spin.setValue(override.tolerance_mm or 0.0)
        self._tol_deg_override_spin.setValue(override.tolerance_deg or 0.0)

    def _update_override_from_form(self) -> None:
        if not self._variant or not self._current_override:
            return
        logo_id = self._logo_combo.currentText() or self._current_override.logo_id
        self._current_override.logo_id = logo_id
        self._current_override.offset_mm = (self._offset_x_spin.value(), self._offset_y_spin.value())
        self._current_override.scale = self._override_scale_spin.value()
        self._current_override.angle_offset_deg = self._angle_offset_spin.value()
        tol_mm = self._tol_mm_override_spin.value()
        tol_deg = self._tol_deg_override_spin.value()
        self._current_override.tolerance_mm = tol_mm if tol_mm > 0 else None
        self._current_override.tolerance_deg = tol_deg if tol_deg > 0 else None
        # update list text
        current_row = self._override_list.currentRow()
        if current_row >= 0:
            self._override_list.item(current_row).setText(self._current_override.logo_id)

    def _add_override(self) -> None:
        if not self._variant:
            return
        new_override = LogoOverride(logo_id="logo", offset_mm=(0.0, 0.0))
        self._variant.logos.append(new_override)
        self._populate_override_list()
        self.messageEmitted.emit("Override agregado")

    def _remove_override(self) -> None:
        if not self._variant or not self._current_override:
            return
        self._variant.logos = [ov for ov in self._variant.logos if ov.logo_id != self._current_override.logo_id]
        self._populate_override_list()
        self.messageEmitted.emit("Override eliminado")
    # endregion
