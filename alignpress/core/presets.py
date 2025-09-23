from dataclasses import dataclass
from typing import Tuple, Optional, Dict, Any
import json, pathlib

@dataclass
class Preset:
    name: str
    roi: Tuple[int,int,int,int]  # x,y,w,h in px
    target_center_px: Tuple[float,float]
    target_angle_deg: float
    target_size_px: Tuple[int,int]
    tolerance_mm: float
    tolerance_deg: float
    detection_mode: str  # "contour" or "aruco"
    params: Dict[str,Any]

def load_preset(path: pathlib.Path) -> Preset:
    data = json.loads(path.read_text())
    return Preset(
        name = data["name"],
        roi = tuple(data["roi"]),
        target_center_px = tuple(data["target_center_px"]),
        target_angle_deg = float(data["target_angle_deg"]),
        target_size_px = tuple(data["target_size_px"]),
        tolerance_mm = float(data["tolerance_mm"]),
        tolerance_deg = float(data["tolerance_deg"]),
        detection_mode = data.get("detection_mode", "contour"),
        params = data.get("params", {}),
    )
