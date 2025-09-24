from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Tuple

import json

ISO_FORMAT = "%Y-%m-%dT%H:%M:%S%z"


def _parse_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        if value.endswith("Z"):
            value = value[:-1] + "+0000"
        if value[-3] == ":":  # handle isoformat with colon in offset
            value = value[:-3] + value[-2:]
        return datetime.strptime(value, ISO_FORMAT)
    except Exception:
        try:
            return datetime.fromisoformat(value)
        except Exception:
            return None


def _format_datetime(value: datetime | None) -> str | None:
    if value is None:
        return None
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.strftime(ISO_FORMAT)


@dataclass
class CalibrationProfile:
    mm_per_px: float
    pattern_size: Tuple[int, int]
    square_size_mm: float
    last_verified: datetime | None = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "mm_per_px": float(self.mm_per_px),
            "pattern_size": list(self.pattern_size),
            "square_size_mm": float(self.square_size_mm),
            "last_verified": _format_datetime(self.last_verified),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CalibrationProfile":
        return cls(
            mm_per_px=float(data["mm_per_px"]),
            pattern_size=tuple(data.get("pattern_size", (7, 5))),
            square_size_mm=float(data.get("square_size_mm", 25.0)),
            last_verified=_parse_datetime(data.get("last_verified")),
        )


@dataclass
class PlatenProfile:
    name: str
    size_mm: Tuple[float, float]
    calibration: CalibrationProfile
    notes: str | None = None
    schema_version: int = 1

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "name": self.name,
            "size_mm": list(self.size_mm),
            "calibration": self.calibration.to_dict(),
            "notes": self.notes,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PlatenProfile":
        return cls(
            name=data["name"],
            size_mm=tuple(float(v) for v in data.get("size_mm", (400.0, 500.0))),
            calibration=CalibrationProfile.from_dict(data["calibration"]),
            notes=data.get("notes"),
            schema_version=int(data.get("schema_version", 1)),
        )

    def to_json(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.to_dict(), indent=2), encoding="utf-8")

    @classmethod
    def from_json(cls, path: Path) -> "PlatenProfile":
        data = json.loads(path.read_text(encoding="utf-8"))
        return cls.from_dict(data)

    def calibration_age_days(self, reference: datetime | None = None) -> float | None:
        if not self.calibration.last_verified:
            return None
        ref = reference or datetime.now(timezone.utc)
        delta = ref - self.calibration.last_verified
        return delta.total_seconds() / 86400.0

    def calibration_state(self, remind_after_days: int = 7, expire_after_days: int = 30) -> str:
        age = self.calibration_age_days()
        if age is None:
            return "recalibrate"
        if age >= expire_after_days:
            return "recalibrate"
        if age >= remind_after_days:
            return "verify"
        return "calibrated"
