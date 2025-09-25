"""Configuration management for AlignPress v2."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping, MutableMapping

import yaml

from alignpress_v2.domain.models import Config


class ConfigManager:
    """Load and persist configuration regardless of legacy format."""

    def __init__(self, path: Path) -> None:
        self._path = path

    def load(self) -> Config:
        if not self._path.exists():
            return Config()
        raw = self._read_raw(self._path)
        if not isinstance(raw, Mapping):
            raise ValueError("Configuration file must contain a mapping")
        flat_keys = set(raw.keys())
        allowed_keys = set(Config().to_dict().keys())
        if flat_keys.issubset(allowed_keys):
            return Config.from_dict(raw)
        return self.migrate(raw)

    def save(self, config: Config) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        serialized = config.to_dict()
        suffix = self._path.suffix.lower()
        if suffix in {".yaml", ".yml"}:
            with self._path.open("w", encoding="utf-8") as handle:
                yaml.safe_dump(serialized, handle, allow_unicode=True, sort_keys=False)
        else:
            with self._path.open("w", encoding="utf-8") as handle:
                json.dump(serialized, handle, indent=2, ensure_ascii=False)

    def migrate(self, raw: Mapping[str, Any]) -> Config:
        """Translate legacy configuration dictionaries into the new schema."""

        defaults = Config().to_dict()

        def _get(mapping: Mapping[str, Any], *keys: str) -> Any:
            value: Any = mapping
            for key in keys:
                if not isinstance(value, Mapping):
                    return None
                value = value.get(key)
            return value

        def _id_from_path(path_value: Any) -> Any:
            if not path_value:
                return None
            try:
                return Path(path_value).stem
            except TypeError:
                return None

        migrated: MutableMapping[str, Any] = dict(defaults)
        migrated["version"] = str(raw.get("version") or raw.get("schema_version") or defaults["version"])
        migrated["language"] = (
            raw.get("language")
            or _get(raw, "system", "language")
            or defaults["language"]
        )
        migrated["units"] = (
            raw.get("units")
            or _get(raw, "system", "units")
            or defaults["units"]
        )
        migrated["theme"] = (
            raw.get("theme")
            or _get(raw, "ui", "theme")
            or defaults["theme"]
        )

        selection = raw.get("selection")
        if isinstance(selection, Mapping):
            migrated["active_platen_id"] = selection.get("platen_id") or _id_from_path(selection.get("platen_path"))
            migrated["active_style_id"] = selection.get("style_id") or _id_from_path(selection.get("style_path"))
            migrated["active_variant_id"] = selection.get("variant_id") or _id_from_path(selection.get("variant_path"))

        return Config.from_dict(dict(migrated))

    def _read_raw(self, path: Path) -> Any:
        suffix = path.suffix.lower()
        with path.open("r", encoding="utf-8") as handle:
            if suffix in {".yaml", ".yml"}:
                return yaml.safe_load(handle) or {}
            return json.load(handle)
