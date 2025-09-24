from __future__ import annotations

from pathlib import Path
from typing import Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QTabWidget, QVBoxLayout, QWidget

from alignpress.io.config import AppConfig
from alignpress.ui.app_context import AppContext
from alignpress.ui.controllers.simulator import SimulatorController
from alignpress.ui.i18n import I18nManager
from alignpress.ui.technical.platen_editor import PlatenEditorWidget
from alignpress.ui.technical.hardware_mock import HardwareMockWidget
from alignpress.ui.technical.style_editor import StyleEditorWidget
from alignpress.ui.technical.variant_editor import VariantEditorWidget


class TechnicalPage(QWidget):
    messageEmitted = Signal(str)
    errorEmitted = Signal(str)
    dataChanged = Signal()

    def __init__(self, context: AppContext, controller: SimulatorController, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._context = context
        self._controller = controller
        self._config: AppConfig = context.config
        self._i18n: I18nManager = context.i18n

        self._tab = QTabWidget(self)
        layout = QVBoxLayout(self)
        layout.addWidget(self._tab)

        assets = self._config.assets
        platens_dir = assets.platens_dir if assets else Path("platens")
        styles_dir = assets.styles_dir if assets else Path("styles")
        variants_dir = assets.variants_dir if assets else Path("variants")

        self._platen_editor = PlatenEditorWidget(platens_dir, self._i18n, self)
        self._style_editor = StyleEditorWidget(styles_dir, self)
        self._variant_editor = VariantEditorWidget(variants_dir, styles_dir, self)

        self._hardware_mock = HardwareMockWidget(self._i18n, self)

        self._tab.addTab(self._platen_editor, "Planchas")
        self._tab.addTab(self._style_editor, "Estilos")
        self._tab.addTab(self._variant_editor, "Tallas")
        self._tab.addTab(self._hardware_mock, "Hardware")

        # Wire signals
        self._platen_editor.messageEmitted.connect(self.messageEmitted)
        self._platen_editor.errorEmitted.connect(self.errorEmitted)
        self._platen_editor.dataChanged.connect(self._emit_data_changed)

        self._style_editor.messageEmitted.connect(self.messageEmitted)
        self._style_editor.errorEmitted.connect(self.errorEmitted)
        self._style_editor.dataChanged.connect(self._on_style_changed)

        self._variant_editor.messageEmitted.connect(self.messageEmitted)
        self._variant_editor.errorEmitted.connect(self.errorEmitted)
        self._variant_editor.dataChanged.connect(self._emit_data_changed)

        self._hardware_mock.eventRaised.connect(self.messageEmitted)

        self.retranslate_ui()

    def _emit_data_changed(self) -> None:
        self.dataChanged.emit()

    def _on_style_changed(self) -> None:
        self._variant_editor.refresh()
        self._emit_data_changed()

    def update_sample_background(self) -> None:
        # placeholder: no direct preview in new UI
        pass

    def retranslate_ui(self) -> None:
        tr = self._i18n
        self._tab.setTabText(0, tr("technical.tab.platens"))
        self._tab.setTabText(1, tr("technical.tab.styles"))
        self._tab.setTabText(2, tr("technical.tab.variants"))
        self._tab.setTabText(3, tr("technical.tab.hardware"))
        self._hardware_mock.retranslate_ui()
