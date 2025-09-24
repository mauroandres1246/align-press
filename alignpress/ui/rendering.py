from __future__ import annotations

import cv2
import numpy as np

from alignpress.core.alignment import FrameAnalysis
from alignpress.core.geometry import Pose2D
from alignpress.core.presets import Preset
from alignpress.gui.overlay import draw_arrows, draw_detected_rect, draw_ghost_rect, put_hud

_STATUS_COLOR = {
    "ok": (0, 200, 0),
    "out_of_tolerance": (0, 0, 255),
    "not_found": (0, 165, 255),
}


def render_operator_overlay(
    frame: np.ndarray,
    preset: Preset,
    analysis: FrameAnalysis,
    status_labels: dict[str, str] | None = None,
) -> np.ndarray:
    display = frame.copy()
    roi = preset.roi
    x, y, w, h = roi
    cv2.rectangle(display, (x, y), (x + w, y + h), (120, 120, 120), 2)

    target_pose = Pose2D(
        center=preset.target_center_px,
        angle_deg=preset.target_angle_deg,
        size=preset.target_size_px,
    )
    draw_ghost_rect(display, target_pose.center, target_pose.size, target_pose.angle_deg, color=(0, 200, 0), thickness=1)

    if analysis.detection.pose is not None and analysis.evaluation.metrics is not None:
        det_pose = analysis.detection.pose
        draw_detected_rect(display, det_pose.center, det_pose.size, det_pose.angle_deg, color=(0, 0, 255), thickness=2)
        draw_arrows(display, target_pose.center, det_pose.center, color=(255, 255, 255))
        metrics = analysis.evaluation.metrics
        txt = f"dx={metrics.dx_mm:+.2f} mm  dy={metrics.dy_mm:+.2f} mm  dθ={metrics.dtheta_deg:+.2f}°"
        put_hud(display, txt, org=(20, 40), color=(255, 255, 255))
    else:
        put_hud(display, "No detectado", org=(20, 40), color=(0, 0, 255))

    status = analysis.evaluation.status
    color = _STATUS_COLOR.get(status, (255, 255, 255))
    if status_labels and status in status_labels:
        text = status_labels[status]
    else:
        text = status.upper()
    put_hud(display, text, org=(20, 80), color=color)
    return display
