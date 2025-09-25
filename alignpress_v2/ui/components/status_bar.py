"""Status bar showing live system feedback."""
from __future__ import annotations

from typing import Dict

try:
    import customtkinter as ctk
except ModuleNotFoundError:  # pragma: no cover - optional dependency during scaffolding
    ctk = None  # type: ignore


class StatusBar:
    """Render key-value pairs describing the current system status."""

    def __init__(self, parent: "ctk.CTkFrame") -> None:
        if ctk is None:
            raise RuntimeError("customtkinter is required to use the AlignPress status bar")
        self._frame = ctk.CTkFrame(parent)
        self._frame.pack(side="bottom", fill="x")
        self._labels: Dict[str, "ctk.CTkLabel"] = {}

    def set_status(self, key: str, value: str) -> None:
        """Update a status item."""

        label = self._labels.get(key)
        if label is None:
            label = ctk.CTkLabel(self._frame, text=f"{key}: {value}")
            label.pack(side="left", padx=4, pady=2)
            self._labels[key] = label
        else:
            label.configure(text=f"{key}: {value}")
