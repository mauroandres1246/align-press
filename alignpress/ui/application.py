from __future__ import annotations

from typing import Sequence

from PySide6.QtWidgets import QApplication

from alignpress.ui.app_context import AppContext
from alignpress.ui.theme import apply_theme


def create_qapplication(argv: Sequence[str], context: AppContext) -> QApplication:
    app = QApplication(list(argv))
    app.setApplicationName("AlignPress Pro")
    app.setOrganizationName("AlignPress")
    apply_theme(app, context.config.ui.theme)
    return app


def update_theme(app: QApplication, context: AppContext, theme_name: str) -> None:
    theme_applied = apply_theme(app, theme_name)
    context.config.ui.theme = theme_applied
    context.save_config()
