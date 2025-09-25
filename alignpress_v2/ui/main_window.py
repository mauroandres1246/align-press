"""AlignPress v2 main window built with CustomTkinter.

This module defines the root window that wires UI widgets to the
application controller. It deliberately stays thin; state changes are
pushed in from the controller and user events are forwarded back via the
controller façade.
"""
from __future__ import annotations

from typing import Callable, Optional

try:
    import customtkinter as ctk
except ModuleNotFoundError:  # pragma: no cover - optional dependency during scaffolding
    ctk = None  # type: ignore


class MainWindow:
    """Create and manage the AlignPress v2 top-level window."""

    def __init__(self, controller: "AppController") -> None:
        if ctk is None:
            raise RuntimeError(
                "customtkinter is required to run the AlignPress v2 UI."
            )
        self._controller = controller
        self._root = ctk.CTk()
        self._root.title("AlignPress v2")
        self._body = ctk.CTkFrame(self._root)
        self._body.pack(fill="both", expand=True)

    def start(self) -> None:
        """Start the Tkinter event loop."""

        self._controller.on_ui_ready()
        self._root.mainloop()

    def bind_on_close(self, callback: Optional[Callable[[], None]]) -> None:
        """Allow the controller to perform cleanup when the window closes."""

        if callback is None:
            return
        self._root.protocol("WM_DELETE_WINDOW", callback)


from alignpress_v2.controller.app_controller import AppController  # noqa: E402
