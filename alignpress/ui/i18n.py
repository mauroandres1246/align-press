"""Simple JSON based internationalization helper."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict


@dataclass
class Locale:
    language: str
    strings: Dict[str, str]


class I18nManager:
    def __init__(self, resources_dir: Path) -> None:
        self._resources_dir = resources_dir
        self._locales: Dict[str, Locale] = {}
        self._current_language = "es"
        self._load_locale("es")

    @property
    def language(self) -> str:
        return self._current_language

    def available_languages(self) -> Dict[str, str]:
        langs = {}
        for path in self._resources_dir.glob("strings_*.json"):
            lang_code = path.stem.split("_")[-1]
            langs[lang_code] = lang_code
        return langs

    def _load_locale(self, language: str) -> None:
        if language in self._locales:
            return
        filename = f"strings_{language}.json"
        path = self._resources_dir / filename
        if not path.exists():
            raise FileNotFoundError(f"No translation file for language '{language}' at {path}")
        data = json.loads(path.read_text(encoding="utf-8"))
        self._locales[language] = Locale(language=language, strings=data)

    def set_language(self, language: str) -> None:
        self._load_locale(language)
        self._current_language = language

    def translate(self, key: str, default: str | None = None) -> str:
        locale = self._locales.get(self._current_language)
        if locale and key in locale.strings:
            return locale.strings[key]
        fallback = self._locales.get("es")
        if fallback and key in fallback.strings:
            return fallback.strings[key]
        return default if default is not None else key

    def __call__(self, key: str, default: str | None = None) -> str:
        return self.translate(key, default)
