from dataclasses import dataclass
from typing import Optional, Tuple
import numpy as np

@dataclass
class Pose2D:
    center: Tuple[float, float]  # (x, y) in px
    angle_deg: float             # rotation angle of detected logo (deg)
    size: Tuple[float, float]    # width,height in px (optional, as detected)

@dataclass
class AlignmentMetrics:
    dx_mm: float
    dy_mm: float
    dtheta_deg: float

@dataclass
class AlignmentEvaluation:
    status: str  # ok | out_of_tolerance | not_found
    within_tolerance: bool
    metrics: Optional[AlignmentMetrics] = None

def diff_pose(det_px:Pose2D, target_px:Pose2D, mm_per_px:float):
    dx_px = det_px.center[0] - target_px.center[0]
    dy_px = det_px.center[1] - target_px.center[1]
    dtheta = det_px.angle_deg - target_px.angle_deg
    # normaliza -180..180
    dtheta = (dtheta + 180) % 360 - 180
    dx_mm = dx_px * mm_per_px
    dy_mm = dy_px * mm_per_px
    return dx_mm, dy_mm, dtheta

def compute_alignment_metrics(det_pose: Pose2D, target_pose: Pose2D, mm_per_px: float) -> AlignmentMetrics:
    dx_mm, dy_mm, dtheta = diff_pose(det_pose, target_pose, mm_per_px)
    return AlignmentMetrics(dx_mm=dx_mm, dy_mm=dy_mm, dtheta_deg=dtheta)

def evaluate_alignment(det_pose: Optional[Pose2D], target_pose: Pose2D, mm_per_px: float, tolerance_mm: float, tolerance_deg: float) -> AlignmentEvaluation:
    if det_pose is None:
        return AlignmentEvaluation(status="not_found", within_tolerance=False, metrics=None)
    metrics = compute_alignment_metrics(det_pose, target_pose, mm_per_px)
    within = (
        abs(metrics.dx_mm) <= tolerance_mm
        and abs(metrics.dy_mm) <= tolerance_mm
        and abs(metrics.dtheta_deg) <= tolerance_deg
    )
    status = "ok" if within else "out_of_tolerance"
    return AlignmentEvaluation(status=status, within_tolerance=within, metrics=metrics)
