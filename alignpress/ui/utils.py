from __future__ import annotations

import cv2
import numpy as np
from PySide6.QtGui import QImage


def cv_to_qimage(frame: np.ndarray) -> QImage:
    if frame.ndim == 2:
        height, width = frame.shape
        qimg = QImage(frame.data, width, height, width, QImage.Format_Grayscale8)
        return qimg.copy()
    if frame.shape[2] == 3:
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        height, width, channels = rgb.shape
        bytes_per_line = channels * width
        qimg = QImage(rgb.data, width, height, bytes_per_line, QImage.Format_RGB888)
        return qimg.copy()
    raise ValueError("Unsupported frame format for QImage conversion")


def format_metric(value: float | None, unit: str, decimals: int = 2) -> str:
    if value is None:
        return "—"
    return f"{value:+.{decimals}f} {unit}"
