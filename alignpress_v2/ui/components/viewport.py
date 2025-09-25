"""Viewport widget that renders the camera feed with alignment overlays."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

try:
    import customtkinter as ctk
except ModuleNotFoundError:  # pragma: no cover - optional dependency during scaffolding
    ctk = None  # type: ignore


@dataclass
class Overlay:
    """Overlay metadata describing what should be drawn on the viewport."""

    label: str
    x: int
    y: int
    width: int
    height: int
    color: str = "#00FF00"


class Viewport:
    """Wrap a Canvas-like widget that can render camera frames and overlays."""

    def __init__(self, parent: "ctk.CTkFrame") -> None:
        if ctk is None:
            raise RuntimeError("customtkinter is required to use the AlignPress viewport")
        self._canvas = ctk.CTkCanvas(parent)
        self._canvas.pack(fill="both", expand=True)

    def update_frame(self, image) -> None:
        """Display the latest camera frame."""
        # Implementation to be completed during integration with the vision pipeline.
        del image

    def draw_overlays(self, overlays: Iterable[Overlay]) -> None:
        """Render overlays on top of the current frame."""

        self._canvas.delete("overlay")
        for overlay in overlays:
            self._canvas.create_rectangle(
                overlay.x,
                overlay.y,
                overlay.x + overlay.width,
                overlay.y + overlay.height,
                outline=overlay.color,
                tags="overlay",
            )
            self._canvas.create_text(
                overlay.x,
                overlay.y - 10,
                text=overlay.label,
                fill=overlay.color,
                tags="overlay",
            )

    def clear(self) -> None:
        """Remove all overlays and reset the canvas."""

        self._canvas.delete("all")
