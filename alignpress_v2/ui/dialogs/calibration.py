"""Calibration dialog to guide operators through recalibration."""
from __future__ import annotations

from typing import Callable

try:
    import customtkinter as ctk
except ModuleNotFoundError:  # pragma: no cover - optional dependency during scaffolding
    ctk = None  # type: ignore


class CalibrationDialog:
    """Simple modal dialog that triggers the calibration workflow."""

    def __init__(self, parent, on_start: Callable[[], None]) -> None:
        if ctk is None:
            raise RuntimeError("customtkinter is required to use the AlignPress dialogs")
        self._dialog = ctk.CTkToplevel(parent)
        self._dialog.title("Calibración")
        label = ctk.CTkLabel(
            self._dialog,
            text=(
                "Coloque el patrón de calibración en la plataforma y "
                "presione comenzar para iniciar el proceso."
            ),
            wraplength=320,
        )
        label.pack(padx=16, pady=16)
        start_button = ctk.CTkButton(self._dialog, text="Comenzar", command=on_start)
        start_button.pack(pady=(0, 12))
        close_button = ctk.CTkButton(
            self._dialog, text="Cerrar", command=self._dialog.destroy
        )
        close_button.pack(pady=(0, 12))

    def show(self) -> None:
        """Display the dialog and wait for user input."""

        self._dialog.grab_set()
        self._dialog.wait_window()
