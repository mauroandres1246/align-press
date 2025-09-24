from __future__ import annotations

import time
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from alignpress.ui.i18n import I18nManager


class HardwareMockWidget(QWidget):
    eventRaised = Signal(str)

    def __init__(self, i18n: I18nManager, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._i18n = i18n
        self._build_ui()
        self.retranslate_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        self._status_label = QLabel()
        self._status_label.setAlignment(Qt.AlignCenter)
        self._status_label.setStyleSheet("background-color: #424242; color: #ffffff; padding: 6px; border-radius: 6px;")
        layout.addWidget(self._status_label)

        buttons_layout = QHBoxLayout()
        self._btn_ok = QPushButton()
        self._btn_adjust = QPushButton()
        self._btn_beep = QPushButton()
        buttons_layout.addWidget(self._btn_ok)
        buttons_layout.addWidget(self._btn_adjust)
        buttons_layout.addWidget(self._btn_beep)
        layout.addLayout(buttons_layout)

        self._log = QTextEdit()
        self._log.setReadOnly(True)
        layout.addWidget(self._log)

        self._btn_ok.clicked.connect(lambda: self._push_event("OK"))
        self._btn_adjust.clicked.connect(lambda: self._push_event("ADJUST"))
        self._btn_beep.clicked.connect(lambda: self._push_event("BEEP"))

    def retranslate_ui(self) -> None:
        self._status_label.setText(self._i18n("technical.hardware.status.connected"))
        self._btn_ok.setText(self._i18n("technical.hardware.ok"))
        self._btn_adjust.setText(self._i18n("technical.hardware.adjust"))
        self._btn_beep.setText(self._i18n("technical.hardware.beep"))

    def _push_event(self, tag: str) -> None:
        timestamp = time.strftime("%H:%M:%S")
        message = f"[{timestamp}] {tag}"
        self._log.append(message)
        self.eventRaised.emit(message)
