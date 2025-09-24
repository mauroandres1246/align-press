"""Theme helpers for AlignPress UI."""

from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import QApplication


@dataclass
class Theme:
    name: str
    palette: QPalette
    stylesheet: str = ""


def _build_light_palette() -> QPalette:
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor(245, 245, 245))
    palette.setColor(QPalette.WindowText, QColor(33, 33, 33))
    palette.setColor(QPalette.Base, QColor(255, 255, 255))
    palette.setColor(QPalette.AlternateBase, QColor(240, 240, 240))
    palette.setColor(QPalette.ToolTipBase, QColor(255, 255, 220))
    palette.setColor(QPalette.ToolTipText, QColor(33, 33, 33))
    palette.setColor(QPalette.Text, QColor(33, 33, 33))
    palette.setColor(QPalette.Button, QColor(245, 245, 245))
    palette.setColor(QPalette.ButtonText, QColor(33, 33, 33))
    palette.setColor(QPalette.Highlight, QColor(57, 134, 250))
    palette.setColor(QPalette.HighlightedText, QColor(255, 255, 255))
    return palette


def _build_dark_palette() -> QPalette:
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor(40, 44, 52))
    palette.setColor(QPalette.WindowText, QColor(220, 220, 220))
    palette.setColor(QPalette.Base, QColor(30, 34, 40))
    palette.setColor(QPalette.AlternateBase, QColor(45, 49, 58))
    palette.setColor(QPalette.ToolTipBase, QColor(65, 70, 80))
    palette.setColor(QPalette.ToolTipText, QColor(220, 220, 220))
    palette.setColor(QPalette.Text, QColor(220, 220, 220))
    palette.setColor(QPalette.Button, QColor(45, 49, 58))
    palette.setColor(QPalette.ButtonText, QColor(220, 220, 220))
    palette.setColor(QPalette.BrightText, QColor(255, 0, 0))
    palette.setColor(QPalette.Link, QColor(90, 170, 250))
    palette.setColor(QPalette.Highlight, QColor(90, 170, 250))
    palette.setColor(QPalette.HighlightedText, QColor(20, 24, 30))
    return palette


_THEMES = {
    "light": Theme(name="light", palette=_build_light_palette()),
    "dark": Theme(
        name="dark",
        palette=_build_dark_palette(),
        stylesheet="QToolTip { color: #ffffff; background-color: #444444; border: 1px solid #76797C; }",
    ),
}


def available_themes() -> list[str]:
    return list(_THEMES.keys())


def apply_theme(app: QApplication, theme_name: str) -> str:
    theme = _THEMES.get(theme_name, _THEMES["light"])
    app.setPalette(theme.palette)
    app.setStyleSheet(theme.stylesheet)
    return theme.name
