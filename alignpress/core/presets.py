from dataclasses import dataclass
from typing import Tuple, Dict, Any
import json
from pathlib import Path

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
    schema_version: int = 1

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "name": self.name,
            "roi": list(self.roi),
            "target_center_px": list(self.target_center_px),
            "target_angle_deg": float(self.target_angle_deg),
            "target_size_px": list(self.target_size_px),
            "tolerance_mm": float(self.tolerance_mm),
            "tolerance_deg": float(self.tolerance_deg),
            "detection_mode": self.detection_mode,
            "params": self.params,
        }

    def detector_params(self, detector_name: str) -> Dict[str, Any]:
        candidate = self.params.get(detector_name) if isinstance(self.params, dict) else None
        if isinstance(candidate, dict):
            return candidate
        return self.params if isinstance(self.params, dict) else {}

def load_preset(path: Path) -> Preset:
    data = json.loads(path.read_text())
    schema_version = int(data.get("schema_version", 1))
    def _int_tuple(values):
        return (int(round(values[0])), int(round(values[1])))
    return Preset(
        name = data["name"],
        roi = tuple(int(round(v)) for v in data["roi"]),
        target_center_px = tuple(float(v) for v in data["target_center_px"]),
        target_angle_deg = float(data["target_angle_deg"]),
        target_size_px = _int_tuple(data["target_size_px"]),
        tolerance_mm = float(data["tolerance_mm"]),
        tolerance_deg = float(data["tolerance_deg"]),
        detection_mode = data.get("detection_mode", "contour"),
        params = data.get("params", {}),
        schema_version=schema_version,
    )

def save_preset(preset: Preset, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(preset.to_dict(), indent=2))
