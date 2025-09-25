"""Domain models shared across AlignPress v2 layers."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple


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

    def to_dict(self) -> Dict[str, str]:
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
    def from_dict(cls, raw: Dict[str, str]) -> "Config":
        data = {**cls().to_dict(), **raw}
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
