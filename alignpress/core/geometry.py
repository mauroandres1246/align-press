from dataclasses import dataclass
from typing import Tuple
import numpy as np

@dataclass
class Pose2D:
    center: Tuple[float, float]  # (x, y) in px
    angle_deg: float             # rotation angle of detected logo (deg)
    size: Tuple[float, float]    # width,height in px (optional, as detected)

def diff_pose(det_px:Pose2D, target_px:Pose2D, mm_per_px:float):
    dx_px = det_px.center[0] - target_px.center[0]
    dy_px = det_px.center[1] - target_px.center[1]
    dtheta = det_px.angle_deg - target_px.angle_deg
    # normaliza -180..180
    dtheta = (dtheta + 180) % 360 - 180
    dx_mm = dx_px * mm_per_px
    dy_mm = dy_px * mm_per_px
    return dx_mm, dy_mm, dtheta
