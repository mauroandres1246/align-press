"""Control panel displaying key metrics and controls for AlignPress."""
from __future__ import annotations

from typing import Callable, Dict

try:
    import customtkinter as ctk
except ModuleNotFoundError:  # pragma: no cover - optional dependency during scaffolding
    ctk = None  # type: ignore


class ControlPanel:
    """Provide quick access controls and status indicators for the operator."""

    def __init__(self, parent: "ctk.CTkFrame", on_command: Callable[[str], None]) -> None:
        if ctk is None:
            raise RuntimeError("customtkinter is required to use the AlignPress control panel")
        self._frame = ctk.CTkFrame(parent)
        self._frame.pack(side="right", fill="y")
        self._labels: Dict[str, "ctk.CTkLabel"] = {}
        self._on_command = on_command

    def set_metric(self, key: str, value: str) -> None:
        """Update or create a metric label."""

        label = self._labels.get(key)
        if label is None:
            label = ctk.CTkLabel(self._frame, text=f"{key}: {value}")
            label.pack(anchor="w", padx=8, pady=4)
            self._labels[key] = label
        else:
            label.configure(text=f"{key}: {value}")

    def add_button(self, text: str, command_key: str) -> None:
        """Register a new button that dispatches the given command key."""

        button = ctk.CTkButton(
            self._frame,
            text=text,
            command=lambda: self._on_command(command_key),
        )
        button.pack(fill="x", padx=8, pady=4)
