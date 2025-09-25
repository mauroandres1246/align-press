"""Configuration management for AlignPress v2."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from alignpress_v2.domain.models import Config


class ConfigManager:
    """Load and persist configuration from a single JSON source."""

    def __init__(self, path: Path) -> None:
        self._path = path

    def load(self) -> Config:
        if not self._path.exists():
            return Config()
        with self._path.open("r", encoding="utf-8") as handle:
            raw = json.load(handle)
        return Config.from_dict(raw)

    def save(self, config: Config) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with self._path.open("w", encoding="utf-8") as handle:
            json.dump(config.to_dict(), handle, indent=2, ensure_ascii=False)

    def migrate(self, raw: Any) -> Config:
        """Translate legacy configuration dictionaries into the new schema."""

        return Config.from_dict(raw)
