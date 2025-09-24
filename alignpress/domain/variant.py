from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Tuple

import json


@dataclass
class LogoOverride:
    logo_id: str
    offset_mm: Tuple[float, float] = (0.0, 0.0)
    scale: float = 1.0
    angle_offset_deg: float = 0.0
    tolerance_mm: float | None = None
    tolerance_deg: float | None = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "logo_id": self.logo_id,
            "offset_mm": list(self.offset_mm),
            "scale": float(self.scale),
            "angle_offset_deg": float(self.angle_offset_deg),
            "tolerance_mm": self.tolerance_mm,
            "tolerance_deg": self.tolerance_deg,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "LogoOverride":
        return cls(
            logo_id=data["logo_id"],
            offset_mm=tuple(float(v) for v in data.get("offset_mm", (0.0, 0.0))),
            scale=float(data.get("scale", 1.0)),
            angle_offset_deg=float(data.get("angle_offset_deg", 0.0)),
            tolerance_mm=data.get("tolerance_mm"),
            tolerance_deg=data.get("tolerance_deg"),
        )


@dataclass
class SizeVariant:
    name: str
    style_name: str
    description: str | None = None
    scale: float = 1.0
    logos: List[LogoOverride] = field(default_factory=list)
    schema_version: int = 1

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "name": self.name,
            "style_name": self.style_name,
            "description": self.description,
            "scale": float(self.scale),
            "logos": [item.to_dict() for item in self.logos],
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SizeVariant":
        logos = [LogoOverride.from_dict(item) for item in data.get("logos", [])]
        return cls(
            name=data["name"],
            style_name=data.get("style_name", ""),
            description=data.get("description"),
            scale=float(data.get("scale", 1.0)),
            logos=logos,
            schema_version=int(data.get("schema_version", 1)),
        )

    def to_json(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.to_dict(), indent=2), encoding="utf-8")

    @classmethod
    def from_json(cls, path: Path) -> "SizeVariant":
        data = json.loads(path.read_text(encoding="utf-8"))
        return cls.from_dict(data)
