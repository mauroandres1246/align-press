from __future__ import annotations

from pathlib import Path
from typing import Callable

from PySide6.QtCore import QEvent, Qt, Slot
from PySide6.QtGui import QAction, QCloseEvent, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QFileDialog,
    QInputDialog,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QStackedWidget,
    QWidget,
)

from alignpress.ui.app_context import AppContext
from alignpress.ui.controllers.simulator import SimulatorController
from alignpress.ui.i18n import I18nManager
from alignpress.ui.state import GlobalState, StateStore
from alignpress.ui.views.operator_page import OperatorPage
from alignpress.ui.views.technical_page import TechnicalPage


class MainWindow(QMainWindow):
    def __init__(self, context: AppContext, update_theme: Callable[[str], None], parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._context = context
        self._i18n: I18nManager = context.i18n
        self._state_store: StateStore = context.state_store
        self._update_theme = update_theme
        self._controller = SimulatorController(context.config, parent=self)
        self._technical_unlocked = False

        self._stack = QStackedWidget(self)
        self._operator_page = OperatorPage(context, self._controller, parent=self)
        self._technical_page = TechnicalPage(context, self._controller, parent=self)
        self._stack.addWidget(self._operator_page)
        self._stack.addWidget(self._technical_page)
        self.setCentralWidget(self._stack)
        self._stack.setCurrentWidget(self._operator_page)

        self._create_actions()
        self._create_menus()
        self._retranslate_ui()

        self._operator_page.messageEmitted.connect(self._show_status_message)
        self._operator_page.errorEmitted.connect(self._show_error_message)
        self._technical_page.messageEmitted.connect(self._show_status_message)
        self._technical_page.errorEmitted.connect(self._show_error_message)
        self._technical_page.presetSaved.connect(lambda *_: self._controller.load_session())
        self._controller.errorOccurred.connect(self._show_error_message)
        self._controller.statusMessage.connect(self._show_status_message)
        self._controller.playbackStateChanged.connect(self._handle_playback_state)
        self._controller.datasetLoaded.connect(self._on_session_loaded)

        self._shortcut_playpause = QShortcut(QKeySequence(Qt.Key_Space), self)
        self._shortcut_playpause.activated.connect(self._controller.toggle_play)
        self._shortcut_snapshot = QShortcut(QKeySequence("S"), self)
        self._shortcut_snapshot.activated.connect(self._operator_page.capture_snapshot)
        self._shortcut_fullscreen = QShortcut(QKeySequence(Qt.Key_F11), self)
        self._shortcut_fullscreen.activated.connect(self._on_toggle_fullscreen)

        self._state_store.subscribe(self._on_state_changed)
        self._apply_window_prefs()
        self._operator_page.initialize()
        self._activate_operator_mode()
        if not self._context.config.ui.onboarding_completed:
            self._show_onboarding()

    # region UI setup
    def _create_actions(self) -> None:
        self.act_open_dataset = QAction(self)
        self.act_open_dataset.triggered.connect(self._on_open_dataset)

        self.act_open_preset = QAction(self)
        self.act_open_preset.triggered.connect(self._on_open_preset)

        self.act_open_calibration = QAction(self)
        self.act_open_calibration.triggered.connect(self._on_open_calibration)

        self.act_save_preset = QAction(self)
        self.act_save_preset.triggered.connect(self._on_save_preset)

        self.act_export_results = QAction(self)
        self.act_export_results.triggered.connect(self._on_export_results)

        self.act_toggle_fullscreen = QAction(self)
        self.act_toggle_fullscreen.setCheckable(True)
        self.act_toggle_fullscreen.triggered.connect(self._on_toggle_fullscreen)

        self.act_theme_light = QAction(self)
        self.act_theme_light.setCheckable(True)
        self.act_theme_light.triggered.connect(lambda: self._change_theme("light"))

        self.act_theme_dark = QAction(self)
        self.act_theme_dark.setCheckable(True)
        self.act_theme_dark.triggered.connect(lambda: self._change_theme("dark"))

        self.act_about = QAction(self)
        self.act_about.triggered.connect(self._show_about)

        self.act_show_operator = QAction(self)
        self.act_show_operator.setCheckable(True)
        self.act_show_operator.triggered.connect(self._activate_operator_mode)

        self.act_show_technical = QAction(self)
        self.act_show_technical.setCheckable(True)
        self.act_show_technical.triggered.connect(self._activate_technical_mode)

    def _create_menus(self) -> None:
        menu_bar = self.menuBar()
        self.menu_file = menu_bar.addMenu("")
        self.menu_file.addAction(self.act_open_dataset)
        self.menu_file.addAction(self.act_open_preset)
        self.menu_file.addAction(self.act_open_calibration)
        self.menu_file.addSeparator()
        self.menu_file.addAction(self.act_save_preset)
        self.menu_file.addAction(self.act_export_results)

        self.menu_view = menu_bar.addMenu("")
        self.menu_view.addAction(self.act_toggle_fullscreen)
        self.menu_view.addSeparator()
        self.menu_view.addAction(self.act_theme_light)
        self.menu_view.addAction(self.act_theme_dark)
        self.menu_view.addSeparator()
        self.menu_view.addAction(self.act_show_operator)
        self.menu_view.addAction(self.act_show_technical)

        self.menu_help = menu_bar.addMenu("")
        self.menu_help.addAction(self.act_about)
    # endregion

    def _apply_window_prefs(self) -> None:
        opts = self._context.config.ui
        if opts.operator_fullscreen or opts.kiosk_mode:
            self.showFullScreen()
            self.act_toggle_fullscreen.setChecked(True)
        else:
            self.resize(1280, 720)

    def _change_theme(self, theme: str) -> None:
        self._update_theme(theme)
        self._sync_theme_actions()

    def _sync_theme_actions(self) -> None:
        theme = self._context.config.ui.theme
        self.act_theme_light.setChecked(theme == "light")
        self.act_theme_dark.setChecked(theme == "dark")

    def _retranslate_ui(self) -> None:
        tr = self._i18n
        self.setWindowTitle(f"{tr('app.title')} — {tr('app.subtitle')}")
        self.menu_file.setTitle(tr("menu.file"))
        self.menu_view.setTitle(tr("menu.view"))
        self.menu_help.setTitle(tr("menu.help"))

        self.act_open_dataset.setText(tr("menu.file.open_dataset"))
        self.act_open_preset.setText(tr("menu.file.open_preset"))
        self.act_open_calibration.setText(tr("menu.file.open_calibration"))
        self.act_save_preset.setText(tr("menu.file.save_preset"))
        self.act_export_results.setText(tr("menu.file.export_results"))
        self.act_toggle_fullscreen.setText(tr("menu.view.fullscreen"))
        self.act_theme_light.setText(tr("menu.view.theme_light"))
        self.act_theme_dark.setText(tr("menu.view.theme_dark"))
        self.act_about.setText(tr("menu.help.about"))
        self.act_show_operator.setText(tr("operator.panel.title"))
        self.act_show_technical.setText(tr("technical.panel.title"))

        self._operator_page.retranslate_ui()
        self._technical_page.retranslate_ui()
        self._sync_theme_actions()
        if self._stack.currentWidget() is self._operator_page:
            self.act_show_operator.setChecked(True)
            self.act_show_technical.setChecked(False)
        else:
            self.act_show_operator.setChecked(False)
            self.act_show_technical.setChecked(True)

    # region Event handlers (placeholders for now)
    @Slot()
    def _on_open_dataset(self) -> None:  # pragma: no cover - UI placeholder
        path = QFileDialog.getExistingDirectory(
            self,
            self._i18n("messages.choose_folder"),
            str(self._context.config.dataset.path)
        )
        if not path:
            path, _ = QFileDialog.getOpenFileName(
                self,
                self._i18n("messages.choose_file"),
                str(self._context.config.dataset.path),
                "Imágenes/Videos (*.png *.jpg *.jpeg *.bmp *.tif *.tiff *.mp4 *.avi *.mov *.mkv)"
            )
        if path:
            self._context.config.dataset.path = Path(path)
            self._context.save_config()
            self._controller.load_session()

    @Slot()
    def _on_open_preset(self) -> None:  # pragma: no cover - UI placeholder
        path, _ = QFileDialog.getOpenFileName(self, self._i18n("messages.choose_file"), str(self._context.config.preset_path), "JSON (*.json)")
        if path:
            self._context.config.preset_path = Path(path)
            self._context.save_config()
            self._controller.load_session()

    @Slot()
    def _on_open_calibration(self) -> None:  # pragma: no cover - UI placeholder
        path, _ = QFileDialog.getOpenFileName(self, self._i18n("messages.choose_file"), str(self._context.config.calibration_path), "JSON (*.json)")
        if path:
            self._context.config.calibration_path = Path(path)
            self._context.save_config()
            self._controller.load_session()

    @Slot()
    def _on_save_preset(self) -> None:  # pragma: no cover - UI placeholder
        QMessageBox.information(self, "AlignPress", "Guardar preset estará disponible en breve.")

    @Slot()
    def _on_export_results(self) -> None:  # pragma: no cover - UI placeholder
        history = self._controller.history()
        if not history:
            QMessageBox.information(self, self._i18n("menu.file.export_results"), self._i18n("messages.simulation.completed"))
            return
        path_str, selected_filter = QFileDialog.getSaveFileName(
            self,
            self._i18n("menu.file.export_results"),
            "results.csv",
            "CSV (*.csv);;JSON (*.json)"
        )
        if not path_str:
            return
        path = Path(path_str)
        fmt = "json" if selected_filter.startswith("JSON") or path.suffix.lower() == ".json" else "csv"
        try:
            self._controller.export_history(path, fmt=fmt)
            self._show_status_message(self._i18n("messages.export.completed"))
        except Exception as exc:
            self._show_error_message(str(exc))

    @Slot()
    def _on_toggle_fullscreen(self) -> None:
        if self.isFullScreen():
            self.showNormal()
            self._context.config.ui.operator_fullscreen = False
        else:
            self.showFullScreen()
            self._context.config.ui.operator_fullscreen = True
        self._context.save_config()

    def _show_about(self) -> None:
        QMessageBox.information(
            self,
            "AlignPress Pro",
            "AlignPress Pro\nSprint 2 UI prototipo."
        )
    # endregion

    def changeEvent(self, event) -> None:  # pragma: no cover - UI detail
        if event.type() == QEvent.LanguageChange:
            self._retranslate_ui()
        super().changeEvent(event)

    def closeEvent(self, event: QCloseEvent) -> None:  # pragma: no cover - UI detail
        if self.isFullScreen():
            self._context.config.ui.operator_fullscreen = True
            self._context.save_config()
        self._operator_page.stop()
        self._controller.shutdown()
        super().closeEvent(event)

    def _on_state_changed(self, state: GlobalState) -> None:
        if state == GlobalState.ERROR:
            self.statusBar().showMessage(self._i18n("status.error"), 5000)
        elif state == GlobalState.RUN_SIM:
            self.statusBar().showMessage(self._i18n("status.running"))
        elif state == GlobalState.IDLE:
            self.statusBar().showMessage(self._i18n("status.idle"))
        else:
            self.statusBar().showMessage(self._i18n("status.init"))

    def _show_status_message(self, message: str) -> None:
        if not message:
            return
        self.statusBar().showMessage(message, 4000)

    def _show_error_message(self, message: str) -> None:
        if not message:
            return
        self._state_store.set_state(GlobalState.ERROR)
        QMessageBox.warning(self, self._i18n("status.error"), message)

    def _handle_playback_state(self, playing: bool) -> None:
        self._state_store.set_state(GlobalState.RUN_SIM if playing else GlobalState.IDLE)

    def _on_session_loaded(self, count: int) -> None:
        self._state_store.set_state(GlobalState.IDLE)
        self._show_status_message(f"{self._i18n('messages.dataset.loaded')} ({count})")
        self._technical_page.update_sample_background()

    def _activate_operator_mode(self) -> None:
        self._stack.setCurrentWidget(self._operator_page)
        self.act_show_operator.setChecked(True)
        self.act_show_technical.setChecked(False)

    def _activate_technical_mode(self) -> None:
        if not self._technical_unlocked and not self._prompt_technical_pin():
            self.act_show_operator.setChecked(True)
            self.act_show_technical.setChecked(False)
            return
        self._stack.setCurrentWidget(self._technical_page)
        self.act_show_operator.setChecked(False)
        self.act_show_technical.setChecked(True)

    def _prompt_technical_pin(self) -> bool:
        pin, ok = QInputDialog.getText(
            self,
            self._i18n("technical.config.pin"),
            self._i18n("technical.pin.prompt"),
            QLineEdit.Password,
        )
        if not ok:
            return False
        if pin == self._context.config.ui.technical_pin:
            self._technical_unlocked = True
            return True
        QMessageBox.warning(self, self._i18n("technical.panel.title"), self._i18n("technical.pin.error"))
        return False

    def _show_onboarding(self) -> None:
        steps = "\n".join(
            [
                self._i18n("messages.onboarding.subtitle"),
                "",
                f"1. {self._i18n('app.onboarding.step1')}",
                f"2. {self._i18n('app.onboarding.step2')}",
                f"3. {self._i18n('app.onboarding.step3')}",
            ]
        )
        QMessageBox.information(self, self._i18n("messages.onboarding.title"), steps)
        self._context.config.ui.onboarding_completed = True
        self._context.save_config()
