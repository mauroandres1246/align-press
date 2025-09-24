from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Tuple

import json


@dataclass
class LogoDefinition:
    logo_id: str
    display_name: str
    detector: str
    params: Dict[str, Any]
    target_center_mm: Tuple[float, float]
    target_size_mm: Tuple[float, float]
    roi_size_mm: Tuple[float, float]
    target_angle_deg: float
    tolerance_mm: float
    tolerance_deg: float
    instructions: str | None = None
    aruco_id: int | None = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "logo_id": self.logo_id,
            "display_name": self.display_name,
            "detector": self.detector,
            "params": self.params,
            "target_center_mm": list(self.target_center_mm),
            "target_size_mm": list(self.target_size_mm),
            "roi_size_mm": list(self.roi_size_mm),
            "target_angle_deg": float(self.target_angle_deg),
            "tolerance_mm": float(self.tolerance_mm),
            "tolerance_deg": float(self.tolerance_deg),
            "instructions": self.instructions,
            "aruco_id": self.aruco_id,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "LogoDefinition":
        return cls(
            logo_id=data["logo_id"],
            display_name=data.get("display_name", data["logo_id"].replace("_", " ").title()),
            detector=data.get("detector", "contour"),
            params=data.get("params", {}),
            target_center_mm=tuple(float(v) for v in data.get("target_center_mm", (0.0, 0.0))),
            target_size_mm=tuple(float(v) for v in data.get("target_size_mm", (100.0, 60.0))),
            roi_size_mm=tuple(float(v) for v in data.get("roi_size_mm", (200.0, 200.0))),
            target_angle_deg=float(data.get("target_angle_deg", 0.0)),
            tolerance_mm=float(data.get("tolerance_mm", 3.0)),
            tolerance_deg=float(data.get("tolerance_deg", 2.0)),
            instructions=data.get("instructions"),
            aruco_id=data.get("aruco_id"),
        )


@dataclass
class StyleDefinition:
    name: str
    version: str
    logos: List[LogoDefinition] = field(default_factory=list)
    notes: str | None = None
    schema_version: int = 1

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "name": self.name,
            "version": self.version,
            "logos": [logo.to_dict() for logo in self.logos],
            "notes": self.notes,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "StyleDefinition":
        logos = [LogoDefinition.from_dict(item) for item in data.get("logos", [])]
        return cls(
            name=data["name"],
            version=data.get("version", "1.0"),
            logos=logos,
            notes=data.get("notes"),
            schema_version=int(data.get("schema_version", 1)),
        )

    def to_json(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.to_dict(), indent=2), encoding="utf-8")

    @classmethod
    def from_json(cls, path: Path) -> "StyleDefinition":
        data = json.loads(path.read_text(encoding="utf-8"))
        return cls.from_dict(data)
