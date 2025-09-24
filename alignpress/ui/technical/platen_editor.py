from __future__ import annotations

import shutil
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QDialog,
    QDoubleSpinBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from alignpress.domain.platen import CalibrationProfile, PlatenProfile
from alignpress.ui.i18n import I18nManager
from alignpress.ui.technical.calibration_panel import CalibrationPanel


class PlatenEditorWidget(QWidget):
    messageEmitted = Signal(str)
    errorEmitted = Signal(str)
    dataChanged = Signal()

    def __init__(self, directory: Path, i18n: I18nManager, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._dir = directory
        self._i18n = i18n
        self._current_path: Optional[Path] = None
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
        right.setSpacing(8)

        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignRight)
        form.setFormAlignment(Qt.AlignTop)

        self._name_label = QLabel("–")
        form.addRow("Archivo", self._name_label)

        self._display_name = QLabel("–")
        form.addRow("Nombre", self._display_name)

        self._width_spin = QDoubleSpinBox()
        self._width_spin.setRange(10.0, 2000.0)
        self._width_spin.setDecimals(1)
        self._width_spin.setSuffix(" mm")
        form.addRow("Ancho", self._width_spin)

        self._height_spin = QDoubleSpinBox()
        self._height_spin.setRange(10.0, 2000.0)
        self._height_spin.setDecimals(1)
        self._height_spin.setSuffix(" mm")
        form.addRow("Alto", self._height_spin)

        self._mm_per_px_spin = QDoubleSpinBox()
        self._mm_per_px_spin.setRange(0.001, 10.0)
        self._mm_per_px_spin.setDecimals(5)
        form.addRow("mm/px", self._mm_per_px_spin)

        pattern_layout = QHBoxLayout()
        self._pattern_w_spin = QSpinBox()
        self._pattern_w_spin.setRange(2, 20)
        self._pattern_h_spin = QSpinBox()
        self._pattern_h_spin.setRange(2, 20)
        pattern_layout.addWidget(self._pattern_w_spin)
        pattern_layout.addWidget(QLabel("x"))
        pattern_layout.addWidget(self._pattern_h_spin)
        form.addRow("Pattern", pattern_layout)

        self._square_mm_spin = QDoubleSpinBox()
        self._square_mm_spin.setRange(1.0, 100.0)
        self._square_mm_spin.setDecimals(2)
        self._square_mm_spin.setValue(25.0)
        form.addRow("Cuadro mm", self._square_mm_spin)

        self._last_verified_label = QLabel("—")
        form.addRow("Última verificación", self._last_verified_label)

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
        self._btn_calibrate = QPushButton("Calibrar…")
        buttons2.addWidget(self._btn_import)
        buttons2.addWidget(self._btn_export)
        buttons2.addWidget(self._btn_calibrate)
        right.addLayout(buttons2)

        buttons3 = QHBoxLayout()
        self._btn_set_today = QPushButton("Marcar hoy")
        self._btn_save = QPushButton("Guardar")
        buttons3.addWidget(self._btn_set_today)
        buttons3.addStretch(1)
        buttons3.addWidget(self._btn_save)
        right.addLayout(buttons3)

        layout.addLayout(right, stretch=2)

        # Connections
        self._list.currentItemChanged.connect(self._on_item_selected)
        self._btn_new.clicked.connect(self._create_new)
        self._btn_dup.clicked.connect(self._duplicate)
        self._btn_delete.clicked.connect(self._delete)
        self._btn_import.clicked.connect(self._import)
        self._btn_export.clicked.connect(self._export)
        self._btn_calibrate.clicked.connect(self._open_calibration)
        self._btn_save.clicked.connect(self._save)
        self._btn_set_today.clicked.connect(self._mark_today)
    # endregion

    # region Data helpers
    def refresh(self) -> None:
        self._building = True
        self._list.clear()
        paths = sorted(self._dir.glob("*.json"))
        for path in paths:
            try:
                profile = PlatenProfile.from_json(path)
                item = QListWidgetItem(f"{profile.name} ({path.name})")
            except Exception:
                item = QListWidgetItem(f"{path.name}")
            item.setData(Qt.UserRole, path)
            self._list.addItem(item)
        self._building = False
        if self._list.count() > 0:
            self._list.setCurrentRow(0)
        else:
            self._clear_form()

    def _clear_form(self) -> None:
        self._current_path = None
        self._name_label.setText("—")
        self._display_name.setText("—")
        self._width_spin.setValue(400.0)
        self._height_spin.setValue(500.0)
        self._mm_per_px_spin.setValue(0.12)
        self._pattern_w_spin.setValue(7)
        self._pattern_h_spin.setValue(5)
        self._square_mm_spin.setValue(25.0)
        self._last_verified_label.setText("—")

    def _apply_profile(self, path: Path, profile: PlatenProfile) -> None:
        self._current_path = path
        self._name_label.setText(path.name)
        self._display_name.setText(profile.name)
        self._width_spin.setValue(profile.size_mm[0])
        self._height_spin.setValue(profile.size_mm[1])
        self._mm_per_px_spin.setValue(profile.calibration.mm_per_px)
        self._pattern_w_spin.setValue(profile.calibration.pattern_size[0])
        self._pattern_h_spin.setValue(profile.calibration.pattern_size[1])
        self._square_mm_spin.setValue(profile.calibration.square_size_mm)
        if profile.calibration.last_verified:
            self._last_verified_label.setText(profile.calibration.last_verified.isoformat())
        else:
            self._last_verified_label.setText("—")

    def _capture_profile(self) -> PlatenProfile:
        calibration = CalibrationProfile(
            mm_per_px=self._mm_per_px_spin.value(),
            pattern_size=(self._pattern_w_spin.value(), self._pattern_h_spin.value()),
            square_size_mm=self._square_mm_spin.value(),
            last_verified=self._parse_last_verified(),
        )
        name = self._display_name.text() if self._display_name.text() != "—" else "Plancha"
        profile = PlatenProfile(
            name=name,
            size_mm=(self._width_spin.value(), self._height_spin.value()),
            calibration=calibration,
        )
        return profile

    def _parse_last_verified(self) -> datetime | None:
        text = self._last_verified_label.text()
        if text in ("—", "", None):
            return None
        try:
            return datetime.fromisoformat(text)
        except Exception:
            return None
    # endregion

    # region Actions
    def _on_item_selected(self, current: QListWidgetItem, _: QListWidgetItem) -> None:
        if self._building:
            return
        if current is None:
            self._clear_form()
            return
        path = current.data(Qt.UserRole)
        if not isinstance(path, Path):
            return
        try:
            profile = PlatenProfile.from_json(path)
        except Exception as exc:
            self.errorEmitted.emit(str(exc))
            return
        self._apply_profile(path, profile)

    def _create_new(self) -> None:
        timestamp = int(time.time())
        path = self._dir / f"platen_{timestamp}.json"
        profile = PlatenProfile(
            name=f"Plancha {timestamp}",
            size_mm=(400.0, 500.0),
            calibration=CalibrationProfile(mm_per_px=0.12, pattern_size=(7, 5), square_size_mm=25.0),
        )
        profile.to_json(path)
        self.refresh()
        self.messageEmitted.emit("Plancha creada")

    def _duplicate(self) -> None:
        if not self._current_path:
            return
        timestamp = int(time.time())
        target = self._dir / f"{self._current_path.stem}_copy_{timestamp}.json"
        shutil.copy(self._current_path, target)
        self.refresh()
        self.messageEmitted.emit("Plancha duplicada")

    def _delete(self) -> None:
        if not self._current_path:
            return
        self._current_path.unlink(missing_ok=True)
        self.refresh()
        self.messageEmitted.emit("Plancha eliminada")

    def _import(self) -> None:
        from PySide6.QtWidgets import QFileDialog

        path, _ = QFileDialog.getOpenFileName(self, "Importar plancha", str(self._dir), "JSON (*.json)")
        if not path:
            return
        source = Path(path)
        target = self._dir / source.name
        shutil.copy(source, target)
        self.refresh()
        self.messageEmitted.emit("Plancha importada")

    def _export(self) -> None:
        if not self._current_path:
            return
        from PySide6.QtWidgets import QFileDialog

        path, _ = QFileDialog.getSaveFileName(self, "Exportar plancha", str(self._current_path.name), "JSON (*.json)")
        if not path:
            return
        shutil.copy(self._current_path, Path(path))
        self.messageEmitted.emit("Plancha exportada")

    def _open_calibration(self) -> None:
        dialog = QDialog(self)
        dialog.setWindowTitle("Calibración")
        layout = QVBoxLayout(dialog)
        panel = CalibrationPanel(self._i18n, dialog)
        layout.addWidget(panel)

        def _on_computed(cal):
            self._mm_per_px_spin.setValue(cal.mm_per_px)
            if "pattern_size" in cal.meta:
                pattern = cal.meta["pattern_size"]
                if isinstance(pattern, (list, tuple)) and len(pattern) == 2:
                    self._pattern_w_spin.setValue(int(pattern[0]))
                    self._pattern_h_spin.setValue(int(pattern[1]))
            if "square_size_mm" in cal.meta:
                self._square_mm_spin.setValue(float(cal.meta["square_size_mm"]))

        panel.calibrationComputed.connect(_on_computed)
        dialog.exec()

    def _mark_today(self) -> None:
        now = datetime.now(timezone.utc).isoformat()
        self._last_verified_label.setText(now)

    def _save(self) -> None:
        profile = self._capture_profile()
        if not self._current_path:
            timestamp = int(time.time())
            self._current_path = self._dir / f"platen_{timestamp}.json"
        profile.to_json(self._current_path)
        self.refresh()
        self.messageEmitted.emit("Plancha guardada")
        self.dataChanged.emit()
    # endregion
