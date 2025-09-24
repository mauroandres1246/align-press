from __future__ import annotations

import json
import shutil
import time
from pathlib import Path
from typing import Dict, Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QInputDialog,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
    QLabel,
    QComboBox,
    QLineEdit,
)

from alignpress.core.presets import Preset, load_preset, save_preset
from alignpress.ui.app_context import AppContext
from alignpress.ui.controllers.simulator import SimulatorController
from alignpress.ui.i18n import I18nManager
from alignpress.ui.technical.calibration_panel import CalibrationPanel
from alignpress.ui.technical.hardware_mock import HardwareMockWidget
from alignpress.ui.technical.preset_editor import PresetEditorWidget


class TechnicalPage(QWidget):
    messageEmitted = Signal(str)
    errorEmitted = Signal(str)
    presetSaved = Signal(Preset, Path)

    def __init__(self, context: AppContext, controller: SimulatorController, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._context = context
        self._controller = controller
        self._i18n: I18nManager = context.i18n
        self._preset_dir = context.config.preset_path.parent
        self._preset_dir.mkdir(parents=True, exist_ok=True)
        self._current_preset_path: Optional[Path] = None
        self._original_preset: Optional[Preset] = None
        self._dirty = False

        self._build_ui()
        self.retranslate_ui()
        self._connect_signals()
        self.refresh_preset_list()
        self._update_sample_background()

    def _build_ui(self) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)

        # Preset list and actions
        presets_container = QVBoxLayout()
        presets_group = QGroupBox(self._i18n("technical.preset.editor"))
        presets_group_layout = QVBoxLayout(presets_group)

        self._preset_list = QListWidget()
        presets_group_layout.addWidget(self._preset_list)

        btns_layout = QHBoxLayout()
        self._btn_new = QPushButton()
        self._btn_duplicate = QPushButton()
        self._btn_rename = QPushButton()
        self._btn_delete = QPushButton()
        btns_layout.addWidget(self._btn_new)
        btns_layout.addWidget(self._btn_duplicate)
        btns_layout.addWidget(self._btn_rename)
        btns_layout.addWidget(self._btn_delete)
        presets_group_layout.addLayout(btns_layout)

        btns_layout2 = QHBoxLayout()
        self._btn_import = QPushButton()
        self._btn_export = QPushButton()
        self._btn_save = QPushButton()
        btns_layout2.addWidget(self._btn_import)
        btns_layout2.addWidget(self._btn_export)
        btns_layout2.addWidget(self._btn_save)
        presets_group_layout.addLayout(btns_layout2)

        presets_container.addWidget(presets_group)

        config_group = QGroupBox(self._i18n("technical.camera.layout"))
        config_layout = QFormLayout(config_group)
        self._camera_layout_combo = QComboBox()
        self._camera_layout_combo.addItem("", "single")
        self._camera_layout_combo.addItem("", "dual")
        config_layout.addRow(self._camera_layout_combo)

        self._pin_edit = QLineEdit()
        self._pin_edit.setEchoMode(QLineEdit.Password)
        self._pin_button = QPushButton()
        config_layout.addRow(self._i18n("technical.config.pin"), self._pin_edit)
        config_layout.addRow(self._pin_button)

        rules_label = QLabel()
        rules_label.setWordWrap(True)
        rules_label.setStyleSheet("color: #888888;")
        rules_label.setObjectName("rulesLabel")
        config_layout.addRow(rules_label)

        presets_container.addWidget(config_group)
        presets_container.addStretch(1)

        layout.addLayout(presets_container, stretch=1)

        # Preset editor center
        self._editor = PresetEditorWidget(self._i18n, self)
        layout.addWidget(self._editor, stretch=2)

        # Right panel with calibration and hardware
        right_panel = QVBoxLayout()
        self._calibration_panel = CalibrationPanel(self._i18n, self)
        right_panel.addWidget(self._calibration_panel, stretch=1)
        self._hardware_mock = HardwareMockWidget(self._i18n, self)
        right_panel.addWidget(self._hardware_mock, stretch=1)
        layout.addLayout(right_panel, stretch=1)

        self._rules_label = rules_label

    def retranslate_ui(self) -> None:
        self._btn_new.setText(self._i18n("technical.preset.new"))
        self._btn_duplicate.setText(self._i18n("technical.preset.duplicate"))
        self._btn_rename.setText(self._i18n("technical.preset.rename"))
        self._btn_delete.setText(self._i18n("technical.preset.delete"))
        self._btn_import.setText(self._i18n("technical.preset.import"))
        self._btn_export.setText(self._i18n("technical.preset.export"))
        self._btn_save.setText(self._i18n("technical.preset.save"))
        self._pin_button.setText(self._i18n("technical.config.pin_update"))
        self._hardware_mock.retranslate_ui()
        self._calibration_panel.retranslate_ui()
        self._editor.retranslate_ui()
        self._camera_layout_combo.setItemText(0, self._i18n("technical.camera.single"))
        self._camera_layout_combo.setItemText(1, self._i18n("technical.camera.dual"))
        self._rules_label.setText(
            f"{self._i18n('technical.rules.title')}:\n"
            f"INIT → {self._i18n('status.init')}\n"
            f"IDLE → {self._i18n('status.idle')}\n"
            f"RUN_SIM → {self._i18n('status.running')}\n"
            f"ERROR → {self._i18n('status.error')}"
        )
        self._apply_config_values()

    def _connect_signals(self) -> None:
        self._preset_list.currentItemChanged.connect(self._on_preset_selected)
        self._btn_new.clicked.connect(self._create_new_preset)
        self._btn_duplicate.clicked.connect(self._duplicate_preset)
        self._btn_rename.clicked.connect(self._rename_preset)
        self._btn_delete.clicked.connect(self._delete_preset)
        self._btn_import.clicked.connect(self._import_preset)
        self._btn_export.clicked.connect(self._export_preset)
        self._btn_save.clicked.connect(self._save_current_preset)
        self._camera_layout_combo.currentIndexChanged.connect(self._on_camera_layout_changed)
        self._pin_button.clicked.connect(self._update_pin)

        self._editor.presetChanged.connect(self._on_editor_changed)
        self._calibration_panel.calibrationComputed.connect(lambda cal: self.messageEmitted.emit(f"mm/px={cal.mm_per_px:.5f}"))
        self._calibration_panel.errorRaised.connect(self.errorEmitted)
        self._calibration_panel.messageRaised.connect(self.messageEmitted)
        self._calibration_panel.calibrationSaved.connect(self._imported_calibration_to_config)
        self._hardware_mock.eventRaised.connect(self.messageEmitted)

        self._controller.datasetLoaded.connect(lambda _: self._update_sample_background())

    # region Preset management
    def refresh_preset_list(self) -> None:
        self._preset_list.clear()
        presets = sorted(self._preset_dir.glob("*.json"))
        self._preset_items: Dict[str, Path] = {}
        for path in presets:
            item = QListWidgetItem(path.name)
            self._preset_list.addItem(item)
            self._preset_items[item.text()] = path
        # ensure current preset is selected
        current = self._context.config.preset_path.name
        items = self._preset_list.findItems(current, Qt.MatchExactly)
        if items:
            self._preset_list.setCurrentItem(items[0])
        elif self._preset_list.count() > 0:
            self._preset_list.setCurrentRow(0)

    def _load_preset(self, path: Path) -> None:
        try:
            preset = load_preset(path)
        except Exception as exc:
            self.errorEmitted.emit(str(exc))
            return
        self._current_preset_path = path
        self._original_preset = preset
        self._editor.set_preset(preset)
        self._dirty = False
        self._update_dirty_state()

    def _on_preset_selected(self, current: QListWidgetItem | None, prev: QListWidgetItem | None) -> None:
        if current is None:
            return
        path = self._preset_items.get(current.text())
        if not path:
            return
        if self._dirty and self._current_preset_path and self._current_preset_path != path:
            choice = QMessageBox.question(
                self,
                "Preset",
                self._i18n("technical.preset.save") + "?",
                QMessageBox.Yes | QMessageBox.No,
            )
            if choice == QMessageBox.Yes:
                self._save_current_preset()
        self._load_preset(path)

    def _save_current_preset(self) -> None:
        if not self._current_preset_path:
            return
        try:
            preset = self._editor.current_preset()
            save_preset(preset, self._current_preset_path)
            self._context.config.preset_path = self._current_preset_path
            self._context.save_config()
            self._dirty = False
            self._update_dirty_state()
            self.messageEmitted.emit(self._i18n("technical.preset.save"))
            self.presetSaved.emit(preset, self._current_preset_path)
        except Exception as exc:
            self.errorEmitted.emit(str(exc))

    def _create_new_preset(self) -> None:
        base = self._editor.current_preset() if self._current_preset_path else load_preset(self._context.config.preset_path)
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        new_name = f"preset_{timestamp}"
        new_preset = Preset(
            name=new_name,
            roi=base.roi,
            target_center_px=base.target_center_px,
            target_angle_deg=base.target_angle_deg,
            target_size_px=base.target_size_px,
            tolerance_mm=base.tolerance_mm,
            tolerance_deg=base.tolerance_deg,
            detection_mode=base.detection_mode,
            params=base.params,
            schema_version=base.schema_version,
        )
        path = self._preset_dir / f"{new_name}.json"
        save_preset(new_preset, path)
        self.refresh_preset_list()
        self._context.config.preset_path = path
        self._context.save_config()
        items = self._preset_list.findItems(path.name, Qt.MatchExactly)
        if items:
            self._preset_list.setCurrentItem(items[0])

    def _duplicate_preset(self) -> None:
        if not self._current_preset_path:
            return
        preset = self._editor.current_preset()
        timestamp = time.strftime("%H%M%S")
        new_name = f"{preset.name}_copy_{timestamp}"
        preset.name = new_name
        target = self._preset_dir / f"{new_name}.json"
        save_preset(preset, target)
        self.refresh_preset_list()
        items = self._preset_list.findItems(target.name, Qt.MatchExactly)
        if items:
            self._preset_list.setCurrentItem(items[0])
        self._context.config.preset_path = target
        self._context.save_config()

    def _rename_preset(self) -> None:
        if not self._current_preset_path:
            return
        new_name, ok = QInputDialog.getText(
            self,
            self._i18n("technical.preset.rename"),
            self._i18n("technical.preset.rename"),
            text=self._current_preset_path.stem,
        )
        if not ok or not new_name:
            return
        target = self._preset_dir / f"{new_name}.json"
        if target.exists():
            self.errorEmitted.emit(self._i18n("messages.file.exists"))
            return
        preset = self._editor.current_preset()
        preset.name = new_name
        save_preset(preset, target)
        if self._current_preset_path.exists():
            self._current_preset_path.unlink()
        self._current_preset_path = target
        self._context.config.preset_path = target
        self._context.save_config()
        self.refresh_preset_list()
        items = self._preset_list.findItems(target.name, Qt.MatchExactly)
        if items:
            self._preset_list.setCurrentItem(items[0])

    def _delete_preset(self) -> None:
        if not self._current_preset_path:
            return
        confirm = QMessageBox.question(
            self,
            self._i18n("technical.preset.delete"),
            self._i18n("technical.preset.delete_confirm"),
        )
        if confirm != QMessageBox.Yes:
            return
        self._current_preset_path.unlink(missing_ok=True)
        self._current_preset_path = None
        self.refresh_preset_list()
        if self._preset_list.count() > 0:
            self._preset_list.setCurrentRow(0)
            current_item = self._preset_list.currentItem()
            if current_item:
                path = self._preset_items.get(current_item.text())
                if path:
                    self._context.config.preset_path = path
                    self._context.save_config()
        else:
            default_preset = Preset(
                name="preset_default",
                roi=(0, 0, 200, 200),
                target_center_px=(100.0, 100.0),
                target_angle_deg=0.0,
                target_size_px=(100, 60),
                tolerance_mm=2.0,
                tolerance_deg=2.0,
                detection_mode="contour",
                params={},
            )
            self._original_preset = default_preset
            self._editor.set_preset(default_preset)
            self._dirty = False
            self._update_dirty_state()

    def _import_preset(self) -> None:
        path_str, _ = QFileDialog.getOpenFileName(
            self,
            self._i18n("technical.preset.import"),
            str(self._preset_dir),
            "JSON (*.json)"
        )
        if not path_str:
            return
        source = Path(path_str)
        target = self._preset_dir / source.name
        shutil.copy(source, target)
        self.refresh_preset_list()
        items = self._preset_list.findItems(target.name, Qt.MatchExactly)
        if items:
            self._preset_list.setCurrentItem(items[0])
        self._context.config.preset_path = target
        self._context.save_config()

    def _export_preset(self) -> None:
        if not self._current_preset_path:
            return
        path_str, _ = QFileDialog.getSaveFileName(
            self,
            self._i18n("technical.preset.export"),
            str(self._current_preset_path.name),
            "JSON (*.json)"
        )
        if not path_str:
            return
        target = Path(path_str)
        preset = self._editor.current_preset()
        save_preset(preset, target)
        self.messageEmitted.emit(self._i18n("messages.export.completed"))

    def _on_editor_changed(self, preset: Preset) -> None:
        self._dirty = True
        self._update_dirty_state()

    def _update_dirty_state(self) -> None:
        if self._dirty:
            self._btn_save.setStyleSheet("background-color: #ffca28; color: #212121;")
        else:
            self._btn_save.setStyleSheet("")

    # endregion

    def _apply_config_values(self) -> None:
        layout = self._context.config.ui.camera_layout
        current_index = 0
        for idx in range(self._camera_layout_combo.count()):
            if self._camera_layout_combo.itemData(idx) == layout:
                current_index = idx
                break
        self._camera_layout_combo.setCurrentIndex(current_index)
        self._pin_edit.setText(self._context.config.ui.technical_pin)

    def _on_camera_layout_changed(self, index: int) -> None:
        layout_name = self._camera_layout_combo.itemData(index)
        if not layout_name:
            return
        self._context.config.ui.camera_layout = layout_name
        self._context.save_config()

    def _update_pin(self) -> None:
        pin = self._pin_edit.text().strip()
        if not pin:
            self.errorEmitted.emit("PIN inválido")
            return
        self._context.config.ui.technical_pin = pin
        self._context.save_config()
        self.messageEmitted.emit(self._i18n("technical.config.pin_update"))

    def _update_sample_background(self) -> None:
        frame = self._controller.sample_frame()
        if frame is not None:
            self._editor.set_background(frame)

    def update_sample_background(self) -> None:
        self._update_sample_background()

    def _imported_calibration_to_config(self, calibration_path: Path) -> None:
        self._context.config.calibration_path = calibration_path
        self._context.save_config()
        self.messageEmitted.emit(self._i18n("technical.calibration.save"))
