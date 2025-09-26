"""
Camera Viewport Component for AlignPress v2

Displays camera feed with overlay visualization of detection results
"""
from __future__ import annotations

import logging
import tkinter as tk
from typing import Optional, Tuple, List
import numpy as np

try:
    import customtkinter as ctk
    from PIL import Image, ImageTk, ImageDraw
    CTK_AVAILABLE = True
    PIL_AVAILABLE = True
except ImportError:
    import tkinter as ctk
    CTK_AVAILABLE = False
    PIL_AVAILABLE = False

from ...config.models import Logo, Point, Rectangle
from ...controller.state_manager import DetectionResult

logger = logging.getLogger(__name__)


class CameraViewport:
    """Camera viewport with overlay visualization"""

    def __init__(self, parent, width: int = 640, height: int = 480):
        self.parent = parent
        self.width = width
        self.height = height

        # Current frame and overlays
        self.current_frame: Optional[np.ndarray] = None
        self.detection_results: List[DetectionResult] = []
        self.target_logos: List[Logo] = []

        # Create the viewport frame
        self._setup_viewport()

        logger.info(f"CameraViewport initialized ({width}x{height})")

    def _setup_viewport(self):
        """Setup the viewport UI components"""
        if CTK_AVAILABLE:
            self.frame = ctk.CTkFrame(self.parent)
            self.canvas = ctk.CTkCanvas(
                self.frame,
                width=self.width,
                height=self.height,
                bg="black"
            )
        else:
            self.frame = tk.Frame(self.parent, bg="black")
            self.canvas = tk.Canvas(
                self.frame,
                width=self.width,
                height=self.height,
                bg="black"
            )

        # Pack canvas
        self.canvas.pack(fill="both", expand=True, padx=10, pady=10)

        # Add placeholder text
        self.canvas.create_text(
            self.width // 2,
            self.height // 2,
            text="Camera Feed\n(No signal)",
            fill="white",
            font=("Arial", 16),
            tags="placeholder"
        )

    def update_frame(self, frame: Optional[np.ndarray]):
        """Update the displayed frame"""
        self.current_frame = frame

        if frame is not None and PIL_AVAILABLE:
            try:
                # Convert frame to PIL Image
                if len(frame.shape) == 3:
                    # Color frame
                    image = Image.fromarray(frame)
                else:
                    # Grayscale frame
                    image = Image.fromarray(frame).convert("RGB")

                # Resize to fit viewport while maintaining aspect ratio
                image = self._resize_image(image)

                # Draw overlays
                image = self._draw_overlays(image)

                # Convert to PhotoImage and display
                photo = ImageTk.PhotoImage(image)

                # Clear canvas and show image
                self.canvas.delete("all")
                self.canvas.create_image(
                    self.width // 2,
                    self.height // 2,
                    image=photo,
                    tags="frame"
                )

                # Keep reference to prevent garbage collection
                self.canvas.image = photo

            except Exception as e:
                logger.error(f"Error updating frame: {e}")
                self._show_error_message("Frame update error")
        else:
            # Show placeholder when no frame available
            self._show_placeholder()

    def _resize_image(self, image: Image.Image) -> Image.Image:
        """Resize image to fit viewport while maintaining aspect ratio"""
        img_width, img_height = image.size

        # Calculate scaling factor
        scale_x = self.width / img_width
        scale_y = self.height / img_height
        scale = min(scale_x, scale_y)

        # Calculate new size
        new_width = int(img_width * scale)
        new_height = int(img_height * scale)

        return image.resize((new_width, new_height), Image.Resampling.LANCZOS)

    def _draw_overlays(self, image: Image.Image) -> Image.Image:
        """Draw detection overlays on the image"""
        draw = ImageDraw.Draw(image)

        # Draw target logo positions
        for logo in self.target_logos:
            self._draw_target_logo(draw, logo, image.size)

        # Draw detection results
        for result in self.detection_results:
            self._draw_detection_result(draw, result, image.size)

        return image

    def _draw_target_logo(self, draw: ImageDraw.Draw, logo: Logo, image_size: Tuple[int, int]):
        """Draw target logo position overlay"""
        # Convert mm coordinates to pixel coordinates
        # This would need calibration data in a real implementation
        x_px = int(logo.position_mm.x * 2)  # Mock conversion
        y_px = int(logo.position_mm.y * 2)  # Mock conversion

        # Ensure coordinates are within image bounds
        x_px = max(0, min(x_px, image_size[0] - 1))
        y_px = max(0, min(y_px, image_size[1] - 1))

        # Draw target crosshair
        size = 20
        draw.line(
            [(x_px - size, y_px), (x_px + size, y_px)],
            fill="blue",
            width=2
        )
        draw.line(
            [(x_px, y_px - size), (x_px, y_px + size)],
            fill="blue",
            width=2
        )

        # Draw target circle
        tolerance_px = int(logo.tolerance_mm * 2)  # Mock conversion
        draw.ellipse(
            [
                x_px - tolerance_px,
                y_px - tolerance_px,
                x_px + tolerance_px,
                y_px + tolerance_px
            ],
            outline="blue",
            width=1
        )

        # Draw logo name
        draw.text(
            (x_px + 25, y_px - 10),
            logo.name,
            fill="blue"
        )

    def _draw_detection_result(self, draw: ImageDraw.Draw, result: DetectionResult, image_size: Tuple[int, int]):
        """Draw detection result overlay"""
        x_px, y_px = result.position

        # Ensure coordinates are within image bounds
        x_px = max(0, min(int(x_px), image_size[0] - 1))
        y_px = max(0, min(int(y_px), image_size[1] - 1))

        # Choose color based on success
        color = "green" if result.success else "red"

        # Draw detection marker
        size = 15
        draw.rectangle(
            [x_px - size, y_px - size, x_px + size, y_px + size],
            outline=color,
            width=3
        )

        # Draw confidence text
        confidence_text = f"{result.confidence:.2f}"
        draw.text(
            (x_px + 20, y_px + 20),
            confidence_text,
            fill=color
        )

    def _show_placeholder(self):
        """Show placeholder when no frame is available"""
        self.canvas.delete("all")
        self.canvas.create_text(
            self.width // 2,
            self.height // 2,
            text="Camera Feed\n(No signal)",
            fill="white",
            font=("Arial", 16),
            tags="placeholder"
        )

    def _show_error_message(self, message: str):
        """Show error message on viewport"""
        self.canvas.delete("all")
        self.canvas.create_text(
            self.width // 2,
            self.height // 2,
            text=f"Error\n{message}",
            fill="red",
            font=("Arial", 14),
            tags="error"
        )

    def set_target_logos(self, logos: List[Logo]):
        """Set the target logos to display as overlays"""
        self.target_logos = logos
        logger.debug(f"Updated target logos: {len(logos)} logos")

    def set_detection_results(self, results: List[DetectionResult]):
        """Set detection results to display as overlays"""
        self.detection_results = results
        logger.debug(f"Updated detection results: {len(results)} results")

    def clear_overlays(self):
        """Clear all overlays"""
        self.target_logos = []
        self.detection_results = []

    def get_frame(self) -> tk.Frame:
        """Get the viewport frame widget"""
        return self.frame


def create_camera_viewport(parent, width: int = 640, height: int = 480) -> CameraViewport:
    """Create a camera viewport component"""
    return CameraViewport(parent, width, height)