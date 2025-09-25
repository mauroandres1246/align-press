"""Domain models shared across AlignPress v2 layers."""
from __future__ import annotations

from dataclasses import dataclass, field
from dataclasses import fields as dataclass_fields
from typing import Any, Dict, List, Mapping, Optional, Tuple


@dataclass(frozen=True)
class Config:
    """Application configuration loaded from the single source JSON file."""

    version: str = "0"
    language: str = "es"
    units: str = "mm"
    theme: str = "dark"
    active_platen_id: Optional[str] = None
    active_style_id: Optional[str] = None
    active_variant_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "version": self.version,
            "language": self.language,
            "units": self.units,
            "theme": self.theme,
            "active_platen_id": self.active_platen_id,
            "active_style_id": self.active_style_id,
            "active_variant_id": self.active_variant_id,
        }

    @classmethod
    def from_dict(cls, raw: Mapping[str, Any]) -> "Config":
        defaults = cls().to_dict()
        allowed = {field.name for field in dataclass_fields(cls)}
        filtered = {key: raw[key] for key in raw if key in allowed and raw[key] is not None}
        data = {**defaults, **filtered}
        return cls(**data)


@dataclass(frozen=True)
class DetectionResult:
    """Output produced by the detection pipeline."""

    logos: List[Dict[str, float]] = field(default_factory=list)

    @classmethod
    def empty(cls) -> "DetectionResult":
        return cls()


@dataclass(frozen=True)
class CalibrationResult:
    """Result of a calibration run."""

    mm_per_px: float = 1.0
    timestamp: Optional[str] = None

    @classmethod
    def identity(cls) -> "CalibrationResult":
        return cls(mm_per_px=1.0)


@dataclass(frozen=True)
class CompositionPreset:
    """Preset used to render alignment guides for a variant."""

    platen: str
    style: str
    variant: str
    offsets: Dict[str, Tuple[float, float]]
