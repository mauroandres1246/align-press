from __future__ import annotations

import json
import math
import time
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

import cv2
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QSizePolicy,
    QSpacerItem,
    QStackedWidget,
    QHeaderView,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from alignpress.core.alignment import FrameAnalysis
from alignpress.domain.platen import PlatenProfile
from alignpress.domain.style import StyleDefinition
from alignpress.domain.variant import SizeVariant
from alignpress.domain.service import build_logo_tasks, list_json_files, load_platen, load_style, load_variant
from alignpress.io.config import AppConfig, SelectionConfig
from alignpress.ui.app_context import AppContext
from alignpress.ui.controllers.simulator import SimulatorController
from alignpress.ui.i18n import I18nManager
from alignpress.ui.utils import format_metric


@dataclass
class ActiveAssets:
    platen: PlatenProfile | None = None
    style: StyleDefinition | None = None
    variant: SizeVariant | None = None


class OperatorPage(QWidget):
    selectionApplied = Signal()
    messageEmitted = Signal(str)
    errorEmitted = Signal(str)

    def __init__(self, context: AppContext, controller: SimulatorController, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._context = context
        self._controller = controller
        self._config: AppConfig = context.config
        self._i18n: I18nManager = context.i18n
        self._assets = ActiveAssets()
        self._logo_tasks: List[dict] = []
        self._current_logo_id: str | None = None
        self._current_preset_tolerance_mm: float = 3.0
        self._current_preset_tolerance_deg: float = 2.0

        self._build_ui()
        self._connect_signals()
        self.retranslate_ui()

    # region UI setup
    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # Header
        header = QHBoxLayout()
        header.setSpacing(24)

        self._platen_label = QLabel("—")
        self._style_label = QLabel("—")
        self._variant_label = QLabel("—")
        self._version_label = QLabel("—")
        for lbl in (self._platen_label, self._style_label, self._variant_label, self._version_label):
            lbl.setStyleSheet("font-size: 18px; font-weight: 600;")
        header.addWidget(self._platen_label)
        header.addWidget(self._style_label)
        header.addWidget(self._variant_label)
        header.addWidget(self._version_label)

        header.addStretch(1)

        self._calibration_chip = QLabel("Calibración")
        self._calibration_chip.setAlignment(Qt.AlignCenter)
        self._calibration_chip.setFixedWidth(140)
        self._calibration_chip.setStyleSheet("border-radius: 12px; padding: 6px 12px; font-weight: 600;")
        header.addWidget(self._calibration_chip)

        self._dataset_label = QLabel("Dataset: —")
        self._dataset_label.setStyleSheet("color: #888888;")
        header.addWidget(self._dataset_label)

        layout.addLayout(header)

        # Stack: wizard vs operation view
        self._stack = QStackedWidget(self)
        layout.addWidget(self._stack, stretch=1)

        self._stack.addWidget(self._build_wizard())
        self._stack.addWidget(self._build_operation_view())

    def _build_wizard(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(32, 32, 32, 32)
        layout.setSpacing(16)

        self._wizard_stack = QStackedWidget(widget)
        layout.addWidget(self._wizard_stack, stretch=1)

        self._wizard_platen_list = QListWidget()
        self._wizard_style_list = QListWidget()
        self._wizard_variant_list = QListWidget()
        for lst in (self._wizard_platen_list, self._wizard_style_list, self._wizard_variant_list):
            lst.setSelectionMode(QListWidget.SingleSelection)

        self._wizard_style_list.currentItemChanged.connect(lambda *_: self._filter_variants_for_style())

        platen_page = QWidget()
        platen_layout = QVBoxLayout(platen_page)
        self._wizard_platen_title = QLabel()
        platen_layout.addWidget(self._wizard_platen_title)
        platen_layout.addWidget(self._wizard_platen_list)

        style_page = QWidget()
        style_layout = QVBoxLayout(style_page)
        self._wizard_style_title = QLabel()
        style_layout.addWidget(self._wizard_style_title)
        style_layout.addWidget(self._wizard_style_list)

        variant_page = QWidget()
        variant_layout = QVBoxLayout(variant_page)
        self._wizard_variant_title = QLabel()
        variant_layout.addWidget(self._wizard_variant_title)
        variant_layout.addWidget(self._wizard_variant_list)

        summary_page = QWidget()
        summary_layout = QVBoxLayout(summary_page)
        self._wizard_summary = QLabel("—")
        self._wizard_summary.setWordWrap(True)
        summary_layout.addWidget(self._wizard_summary)

        self._wizard_stack.addWidget(platen_page)
        self._wizard_stack.addWidget(style_page)
        self._wizard_stack.addWidget(variant_page)
        self._wizard_stack.addWidget(summary_page)

        buttons = QHBoxLayout()
        buttons.addStretch(1)
        self._wizard_back = QPushButton()
        self._wizard_next = QPushButton()
        self._wizard_start = QPushButton()
        self._wizard_start.setVisible(False)
        buttons.addWidget(self._wizard_back)
        buttons.addWidget(self._wizard_next)
        buttons.addWidget(self._wizard_start)
        layout.addLayout(buttons)

        self._wizard_back.clicked.connect(lambda: self._move_wizard(-1))
        self._wizard_next.clicked.connect(lambda: self._move_wizard(1))
        self._wizard_start.clicked.connect(self._apply_wizard_selection)

        return widget

    def _build_operation_view(self) -> QWidget:
        widget = QWidget()
        outer = QVBoxLayout(widget)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(12)

        body = QHBoxLayout()
        body.setSpacing(24)

        # Image panel
        image_column = QVBoxLayout()
        self._image_label = QLabel()
        self._image_label.setMinimumSize(960, 540)
        self._image_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self._image_label.setStyleSheet("background-color: #1c1c1c; border: 2px solid #2f2f2f;")
        self._image_label.setAlignment(Qt.AlignCenter)
        image_column.addWidget(self._image_label, stretch=1)

        controls = QHBoxLayout()
        self._btn_prev_frame = QPushButton()
        self._btn_play_pause = QPushButton()
        self._btn_next_frame = QPushButton()
        for btn in (self._btn_prev_frame, self._btn_play_pause, self._btn_next_frame):
            btn.setFixedHeight(52)
            btn.setMinimumWidth(100)
        self._speed_combo = QComboBox()
        self._speed_combo.addItems(["0.25x", "0.5x", "1x", "1.5x", "2x"])
        self._speed_combo.setCurrentIndex(2)
        self._speed_combo.setFixedHeight(52)
        controls.addWidget(self._btn_prev_frame)
        controls.addWidget(self._btn_play_pause)
        controls.addWidget(self._btn_next_frame)
        controls.addWidget(self._speed_combo)
        image_column.addLayout(controls)

        self._frame_label = QLabel("—")
        self._frame_label.setAlignment(Qt.AlignCenter)
        self._frame_label.setStyleSheet("color: #888888;")
        image_column.addWidget(self._frame_label)

        body.addLayout(image_column, stretch=3)

        # Side panel
        side = QVBoxLayout()
        side.setSpacing(12)
        self._status_label = QLabel("—")
        self._status_label.setAlignment(Qt.AlignCenter)
        self._status_label.setFixedHeight(120)
        self._status_label.setStyleSheet("border-radius: 12px; font-size: 36px; font-weight: 700;")
        side.addWidget(self._status_label)

        self._metrics_labels = {
            "dx": QLabel(),
            "dy": QLabel(),
            "theta": QLabel(),
        }
        for lbl in self._metrics_labels.values():
            lbl.setStyleSheet("font-size: 18px; font-weight: 600;")
            side.addWidget(lbl)

        self._instructions_label = QLabel("—")
        self._instructions_label.setWordWrap(True)
        self._instructions_label.setStyleSheet("font-size: 16px; color: #f5f5f5; background-color: #263238; border-radius: 8px; padding: 8px;")
        side.addWidget(self._instructions_label)

        self._status_header_label = QLabel()
        side.addWidget(self._status_header_label)
        self._logo_checklist = QListWidget()
        self._logo_checklist.setSelectionMode(QListWidget.SingleSelection)
        side.addWidget(self._logo_checklist, stretch=1)

        button_box = QHBoxLayout()
        self._btn_prev_logo = QPushButton()
        self._btn_next_logo = QPushButton()
        self._btn_snapshot = QPushButton()
        for btn in (self._btn_prev_logo, self._btn_next_logo, self._btn_snapshot):
            btn.setFixedHeight(44)
        button_box.addWidget(self._btn_prev_logo)
        button_box.addWidget(self._btn_next_logo)
        button_box.addWidget(self._btn_snapshot)
        side.addLayout(button_box)

        self._btn_change_selection = QPushButton()
        self._btn_change_selection.setFixedHeight(44)
        side.addWidget(self._btn_change_selection)

        self._btn_stop = QPushButton()
        self._btn_stop.setFixedHeight(44)
        side.addWidget(self._btn_stop)

        body.addLayout(side, stretch=2)
        outer.addLayout(body, stretch=1)

        # History table
        self._history_table = QTableWidget(0, 6)
        self._history_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self._history_table.setSelectionMode(QTableWidget.SingleSelection)
        header = self._history_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        outer.addWidget(self._history_table, stretch=1)
        return widget

    def _connect_signals(self) -> None:
        self._btn_prev_frame.clicked.connect(self._controller.previous_frame)
        self._btn_next_frame.clicked.connect(self._controller.next_frame)
        self._btn_play_pause.clicked.connect(self._controller.toggle_play)
        self._btn_prev_logo.clicked.connect(lambda: self._controller.previous_logo())
        self._btn_next_logo.clicked.connect(lambda: self._controller.next_logo(auto=False))
        self._btn_snapshot.clicked.connect(self._on_snapshot)
        self._btn_stop.clicked.connect(self._controller.pause)
        self._btn_change_selection.clicked.connect(self.start_selection_wizard)
        self._speed_combo.currentIndexChanged.connect(self._on_speed_changed)
        self._logo_checklist.itemClicked.connect(self._on_logo_selected_from_list)

        self._controller.frameProcessed.connect(self._on_frame_processed)
        self._controller.playbackStateChanged.connect(self._on_play_state_changed)
        self._controller.statusMessage.connect(self.messageEmitted)
        self._controller.errorOccurred.connect(self.errorEmitted)
        self._controller.logoChanged.connect(self._on_logo_changed)
        self._controller.logoStatusUpdated.connect(self._on_logo_status_updated)
        self._controller.jobCompleted.connect(self._on_job_completed)
    # endregion

    def retranslate_ui(self) -> None:
        tr = self._i18n
        self._wizard_platen_title.setText(tr("app.onboarding.step1"))
        self._wizard_style_title.setText(tr("app.onboarding.step2"))
        self._wizard_variant_title.setText(tr("app.onboarding.step3"))
        self._wizard_back.setText(f"← {tr('operator.wizard.back')}")
        self._wizard_next.setText(f"{tr('operator.wizard.next')} →")
        self._wizard_start.setText(tr("operator.wizard.start"))

        self._btn_play_pause.setText(tr("operator.controls.play"))
        self._btn_prev_frame.setText("⏮")
        self._btn_next_frame.setText("⏭")
        self._btn_prev_frame.setToolTip(tr("simulator.prev"))
        self._btn_next_frame.setToolTip(tr("simulator.next"))
        self._speed_combo.setToolTip(tr("simulator.speed"))

        self._btn_prev_logo.setText(f"← {tr('simulator.prev')}")
        self._btn_next_logo.setText(f"{tr('simulator.next')} →")
        self._btn_snapshot.setText(tr("operator.controls.snapshot"))
        self._btn_change_selection.setText(tr("operator.controls.change_preset"))
        self._btn_stop.setText(tr("operator.controls.stop"))

        self._status_header_label.setText(tr("operator.status.header"))
        if not self._instructions_label.text() or self._instructions_label.text() == "—":
            self._instructions_label.setText(tr("operator.instructions.empty"))

        self._history_table.setHorizontalHeaderLabels([
            tr("operator.table.header.frame"),
            tr("operator.table.header.status"),
            tr("operator.table.header.dx"),
            tr("operator.table.header.dy"),
            tr("operator.table.header.theta"),
            tr("operator.table.header.timestamp"),
        ])

        dataset_name = getattr(self._context.config.dataset.path, "name", "—")
        self._dataset_label.setText(f"{tr('operator.dataset')}: {dataset_name}")

        self._update_header()
        self._update_checklist()

    # region Wizard
    def start_selection_wizard(self) -> None:
        self._populate_wizard_lists()
        self._select_wizard_defaults()
        self._filter_variants_for_style()
        self._wizard_stack.setCurrentIndex(0)
        self._wizard_start.setVisible(False)
        self._stack.setCurrentIndex(0)

    def _populate_wizard_lists(self) -> None:
        self._wizard_platen_list.clear()
        self._wizard_style_list.clear()
        self._wizard_variant_list.clear()

        assets = self._config.assets
        if assets is None:
            self.errorEmitted.emit("Configuración de assets no encontrada")
            return

        platens = list_json_files(assets.platens_dir)
        for path in platens:
            profile = load_platen(path)
            item = QListWidgetItem(f"{profile.name} ({path.name})")
            item.setData(Qt.UserRole, path)
            self._wizard_platen_list.addItem(item)

        styles = list_json_files(assets.styles_dir)
        for path in styles:
            style = load_style(path)
            item = QListWidgetItem(f"{style.name} v{style.version}")
            item.setData(Qt.UserRole, path)
            self._wizard_style_list.addItem(item)

        variants = list_json_files(assets.variants_dir)
        for path in variants:
            variant = load_variant(path)
            item = QListWidgetItem(f"{variant.name} ({variant.style_name})")
            item.setData(Qt.UserRole, path)
             # store style name for filtering
            item.setData(Qt.UserRole + 1, variant.style_name)
            self._wizard_variant_list.addItem(item)

    def _select_wizard_defaults(self) -> None:
        selection = self._context.config.selection
        if not selection:
            return
        if selection.platen_path:
            for i in range(self._wizard_platen_list.count()):
                item = self._wizard_platen_list.item(i)
                path = item.data(Qt.UserRole)
                if path == selection.platen_path:
                    self._wizard_platen_list.setCurrentRow(i)
                    break
        if selection.style_path:
            for i in range(self._wizard_style_list.count()):
                item = self._wizard_style_list.item(i)
                path = item.data(Qt.UserRole)
                if path == selection.style_path:
                    self._wizard_style_list.setCurrentRow(i)
                    break
        if selection.variant_path:
            for i in range(self._wizard_variant_list.count()):
                item = self._wizard_variant_list.item(i)
                path = item.data(Qt.UserRole)
                if path == selection.variant_path:
                    self._wizard_variant_list.setCurrentRow(i)
                    break

    def _filter_variants_for_style(self) -> None:
        current_style_item = self._wizard_style_list.currentItem()
        if current_style_item is None:
            for i in range(self._wizard_variant_list.count()):
                self._wizard_variant_list.item(i).setHidden(False)
            return
        style_path = current_style_item.data(Qt.UserRole)
        style_name = None
        if isinstance(style_path, Path) and style_path.exists():
            try:
                style = load_style(style_path)
                style_name = style.name
            except Exception:
                style_name = None
        for i in range(self._wizard_variant_list.count()):
            item = self._wizard_variant_list.item(i)
            variant_style = item.data(Qt.UserRole + 1)
            hide = False
            if style_name and variant_style and variant_style != style_name:
                hide = True
            item.setHidden(hide)

    def _move_wizard(self, delta: int) -> None:
        index = self._wizard_stack.currentIndex() + delta
        index = max(0, min(self._wizard_stack.count() - 1, index))
        self._wizard_stack.setCurrentIndex(index)
        self._wizard_back.setEnabled(index > 0)
        if index == self._wizard_stack.count() - 1:
            self._wizard_next.setVisible(False)
            self._wizard_start.setVisible(True)
            self._update_wizard_summary()
        else:
            self._wizard_next.setVisible(True)
            self._wizard_start.setVisible(False)

    def _update_wizard_summary(self) -> None:
        platen_item = self._wizard_platen_list.currentItem()
        style_item = self._wizard_style_list.currentItem()
        variant_item = self._wizard_variant_list.currentItem()
        texts = [
            f"Plancha: {platen_item.text() if platen_item else '—'}",
            f"Estilo: {style_item.text() if style_item else '—'}",
            f"Talla: {variant_item.text() if variant_item else '—'}",
        ]
        self._wizard_summary.setText("\n".join(texts))

    def _apply_wizard_selection(self) -> None:
        platen_item = self._wizard_platen_list.currentItem()
        style_item = self._wizard_style_list.currentItem()
        if not platen_item or not style_item:
            self.errorEmitted.emit("Selecciona plancha y estilo")
            return
        variant_item = self._wizard_variant_list.currentItem()
        platen_path = platen_item.data(Qt.UserRole)
        style_path = style_item.data(Qt.UserRole)
        variant_path = variant_item.data(Qt.UserRole) if variant_item else None

        selection = self._context.config.selection
        if selection is None:
            selection = SelectionConfig(platen_path=platen_path, style_path=style_path, variant_path=variant_path)
            self._context.config.selection = selection
        else:
            selection.platen_path = platen_path
            selection.style_path = style_path
            selection.variant_path = variant_path
        self._context.save_config()
        self.selectionApplied.emit()
        self.messageEmitted.emit("Selección aplicada. Recalculando presets...")
        self._stack.setCurrentIndex(1)
    # endregion

    # region Operation view helpers
    def initialize_assets(
        self,
        platen: PlatenProfile | None,
        style: StyleDefinition | None,
        variant: SizeVariant | None,
        dataset_path: Path,
    ) -> None:
        self._assets = ActiveAssets(platen=platen, style=style, variant=variant)
        dataset_name = dataset_path.name if hasattr(dataset_path, "name") else str(dataset_path)
        self._dataset_label.setText(f"{self._i18n('operator.dataset')}: {dataset_name}")
        self._controller.set_status_labels(
            {
                "ok": self._i18n("operator.status.ok"),
                "out_of_tolerance": self._i18n("operator.status.adjust"),
                "not_found": self._i18n("operator.status.not_found"),
            }
        )
        self._history_table.setRowCount(0)
        self._instructions_label.setText("—")
        self._update_header()
        self._update_checklist()
        self._stack.setCurrentIndex(1 if platen and style else 0)

    def _update_header(self) -> None:
        if self._assets.platen:
            self._platen_label.setText(f"Plancha: {self._assets.platen.name}")
            state = self._assets.platen.calibration_state(
                remind_after_days=self._config.calibration_reminder_days,
                expire_after_days=self._config.calibration_expire_days,
            )
            if state == "calibrated":
                self._calibration_chip.setText("🟢 Calibrado")
                self._calibration_chip.setStyleSheet("background-color: #2e7d32; color: #ffffff; border-radius: 12px; padding: 6px;")
            elif state == "verify":
                self._calibration_chip.setText("🟠 Verificar")
                self._calibration_chip.setStyleSheet("background-color: #f9a825; color: #212121; border-radius: 12px; padding: 6px;")
            else:
                self._calibration_chip.setText("🔴 Recalibrar")
                self._calibration_chip.setStyleSheet("background-color: #c62828; color: #ffffff; border-radius: 12px; padding: 6px;")
        else:
            self._platen_label.setText("Plancha: —")
            self._calibration_chip.setText("Calibración")
            self._calibration_chip.setStyleSheet("background-color: #616161; color: #ffffff; border-radius: 12px; padding: 6px;")

        if self._assets.style:
            self._style_label.setText(f"Estilo: {self._assets.style.name}")
            self._version_label.setText(f"Versión: {self._assets.style.version}")
        else:
            self._style_label.setText("Estilo: —")
            self._version_label.setText("Versión: —")

        if self._assets.variant:
            self._variant_label.setText(f"Talla: {self._assets.variant.name}")
        else:
            self._variant_label.setText("Talla: Base")

    def _update_checklist(self) -> None:
        summary = self._controller.logo_tasks_summary()
        self._logo_tasks = summary
        self._logo_checklist.clear()
        for item in summary:
            text = f"{item['display_name']} — {item['status']}"
            list_item = QListWidgetItem(text)
            list_item.setData(Qt.UserRole, item["logo_id"])
            self._logo_checklist.addItem(list_item)
        if summary:
            self._logo_checklist.setCurrentRow(0)

    def _highlight_logo(self, logo_id: str) -> None:
        for row in range(self._logo_checklist.count()):
            item = self._logo_checklist.item(row)
            if item.data(Qt.UserRole) == logo_id:
                self._logo_checklist.setCurrentRow(row)
                break

    # endregion

    # region Controller callbacks
    def _on_speed_changed(self) -> None:
        speed_map = {0: 0.25, 1: 0.5, 2: 1.0, 3: 1.5, 4: 2.0}
        value = speed_map.get(self._speed_combo.currentIndex(), 1.0)
        self._controller.set_speed(value)

    def _on_play_state_changed(self, playing: bool) -> None:
        self._btn_play_pause.setText(self._i18n("operator.controls.pause" if playing else "operator.controls.play"))

    def _on_frame_processed(self, index: int, frame_id: str, image, analysis: FrameAnalysis) -> None:
        pixmap = QPixmap.fromImage(image) if not isinstance(image, QPixmap) else image
        scaled = pixmap.scaled(self._image_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self._image_label.setPixmap(scaled)
        self._frame_label.setText(f"Frame {index + 1}: {frame_id}")
        metrics = analysis.evaluation.metrics
        self._metrics_labels["dx"].setText(f"dx: {format_metric(metrics.dx_mm if metrics else None, 'mm')}")
        self._metrics_labels["dy"].setText(f"dy: {format_metric(metrics.dy_mm if metrics else None, 'mm')}")
        self._metrics_labels["theta"].setText(f"θ: {format_metric(metrics.dtheta_deg if metrics else None, '°')}")
        instruction = self._build_instruction(metrics)
        self._instructions_label.setText(instruction)
        self._append_history_row(analysis)

    def _on_logo_changed(self, logo_id: str, display_name: str) -> None:
        self._current_logo_id = logo_id
        self._status_label.setText(display_name)
        self._highlight_logo(logo_id)
        summary = next((item for item in self._logo_tasks if item["logo_id"] == logo_id), None)
        if summary:
            self._status_label.setText(f"{display_name}\n{summary['status']}")

    def _on_logo_status_updated(self, logo_id: str, status: str) -> None:
        for row in range(self._logo_checklist.count()):
            item = self._logo_checklist.item(row)
            if item.data(Qt.UserRole) == logo_id:
                base = item.text().split(" — ")[0]
                item.setText(f"{base} — {status}")
                break
        if self._current_logo_id == logo_id:
            self._status_label.setText(f"{self._status_label.text().splitlines()[0]}\n{status}")

    def _on_job_completed(self, path: str) -> None:
        self.messageEmitted.emit(f"Checklist completo. Job card: {path}")

    def _on_logo_selected_from_list(self, item: QListWidgetItem) -> None:
        logo_id = item.data(Qt.UserRole)
        if logo_id:
            self._controller.select_logo(logo_id)

    # endregion

    # region History & instructions
    def _append_history_row(self, analysis: FrameAnalysis) -> None:
        row = self._history_table.rowCount()
        self._history_table.insertRow(row)
        metrics = analysis.evaluation.metrics
        logo_name = self._status_label.text().split("\n")[0]
        self._history_table.setItem(row, 0, QTableWidgetItem(logo_name))
        self._history_table.setItem(row, 1, QTableWidgetItem(analysis.evaluation.status))
        self._history_table.setItem(row, 2, QTableWidgetItem(format_metric(metrics.dx_mm if metrics else None, "mm")))
        self._history_table.setItem(row, 3, QTableWidgetItem(format_metric(metrics.dy_mm if metrics else None, "mm")))
        self._history_table.setItem(row, 4, QTableWidgetItem(format_metric(metrics.dtheta_deg if metrics else None, "°")))
        self._history_table.setItem(row, 5, QTableWidgetItem(f"{analysis.timestamp:.2f}"))

    def _build_instruction(self, metrics) -> str:
        if metrics is None:
            return self._i18n("operator.status.not_found")
        instructions = []
        dx = metrics.dx_mm
        dy = metrics.dy_mm
        dtheta = metrics.dtheta_deg
        if abs(dx) > 0.2:
            arrow = "→" if dx > 0 else "←"
            instructions.append(f"Mover {abs(dx):.1f} mm {arrow}")
        if abs(dy) > 0.2:
            arrow = "↓" if dy > 0 else "↑"
            instructions.append(f"Mover {abs(dy):.1f} mm {arrow}")
        if abs(dtheta) > 0.1:
            arrow = "↻" if dtheta > 0 else "↺"
            instructions.append(f"Rotar {abs(dtheta):.1f}° {arrow}")
        if not instructions:
            instructions.append(self._i18n("operator.status.ok"))
        return "\n".join(instructions)
    # endregion

    def _on_snapshot(self) -> None:
        overlay = self._controller.current_overlay()
        if overlay is None:
            self.messageEmitted.emit(self._i18n("messages.snapshot.unavailable"))
            return
        default_dir = (self._config.logging.output_dir / "snapshots").resolve()
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

    def capture_snapshot(self) -> None:
        self._on_snapshot()
