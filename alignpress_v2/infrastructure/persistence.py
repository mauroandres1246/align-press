"""Data persistence helpers for AlignPress."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict


class JobCardRepository:
    """Store and retrieve job card data from disk."""

    def __init__(self, path: Path) -> None:
        self._path = path

    def load(self) -> Dict[str, Any]:
        if not self._path.exists():
            return {}
        with self._path.open("r", encoding="utf-8") as handle:
            return json.load(handle)

    def save(self, data: Dict[str, Any]) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with self._path.open("w", encoding="utf-8") as handle:
            json.dump(data, handle, indent=2, ensure_ascii=False)
