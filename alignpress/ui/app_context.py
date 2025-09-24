from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from alignpress.io.config import AppConfig, save_app_config
from alignpress.ui.i18n import I18nManager
from alignpress.ui.state import StateStore


@dataclass
class AppContext:
    config_path: Path
    config: AppConfig
    i18n: I18nManager
    state_store: StateStore

    def save_config(self) -> None:
        save_app_config(self.config, self.config_path)
