"""Configuration dialog allowing operators to adjust runtime settings."""
from __future__ import annotations

from typing import Callable, Dict

try:
    import customtkinter as ctk
except ModuleNotFoundError:  # pragma: no cover - optional dependency during scaffolding
    ctk = None  # type: ignore


class ConfigDialog:
    """Present a lightweight form backed by the central configuration."""

    def __init__(self, parent, config: Dict[str, str], on_save: Callable[[Dict[str, str]], None]) -> None:
        if ctk is None:
            raise RuntimeError("customtkinter is required to use the AlignPress dialogs")
        self._dialog = ctk.CTkToplevel(parent)
        self._dialog.title("Configuración")
        self._entries: Dict[str, "ctk.CTkEntry"] = {}
        for key, value in config.items():
            frame = ctk.CTkFrame(self._dialog)
            frame.pack(fill="x", padx=12, pady=4)
            label = ctk.CTkLabel(frame, text=key)
            label.pack(side="left")
            entry = ctk.CTkEntry(frame)
            entry.insert(0, value)
            entry.pack(side="right", fill="x", expand=True)
            self._entries[key] = entry
        save_button = ctk.CTkButton(
            self._dialog,
            text="Guardar",
            command=lambda: on_save(self._collect_values()),
        )
        save_button.pack(pady=12)

    def _collect_values(self) -> Dict[str, str]:
        return {key: entry.get() for key, entry in self._entries.items()}

    def show(self) -> None:
        """Display the dialog modally."""

        self._dialog.grab_set()
        self._dialog.wait_window()
