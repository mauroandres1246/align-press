from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

import json

from alignpress.core.alignment import FrameAnalysis


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class JobLogoRecord:
    logo_id: str
    display_name: str
    status: str
    dx_mm: float | None = None
    dy_mm: float | None = None
    dtheta_deg: float | None = None
    detection_method: str | None = None
    frame_id: str | None = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "logo_id": self.logo_id,
            "display_name": self.display_name,
            "status": self.status,
            "dx_mm": self.dx_mm,
            "dy_mm": self.dy_mm,
            "dtheta_deg": self.dtheta_deg,
            "detection_method": self.detection_method,
            "frame_id": self.frame_id,
        }

    @classmethod
    def from_analysis(cls, logo_id: str, display: str, analysis: FrameAnalysis) -> "JobLogoRecord":
        metrics = analysis.evaluation.metrics
        return cls(
            logo_id=logo_id,
            display_name=display,
            status=analysis.evaluation.status,
            dx_mm=metrics.dx_mm if metrics else None,
            dy_mm=metrics.dy_mm if metrics else None,
            dtheta_deg=metrics.dtheta_deg if metrics else None,
            detection_method=analysis.detection.method,
            frame_id=analysis.frame_id,
        )


@dataclass
class JobCard:
    job_id: str
    timestamp: str
    platen_name: str
    style_name: str
    style_version: str
    variant_name: str
    dataset: str
    logos: List[JobLogoRecord] = field(default_factory=list)
    snapshot_path: str | None = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "job_id": self.job_id,
            "timestamp": self.timestamp,
            "platen_name": self.platen_name,
            "style_name": self.style_name,
            "style_version": self.style_version,
            "variant_name": self.variant_name,
            "dataset": self.dataset,
            "logos": [logo.to_dict() for logo in self.logos],
            "snapshot_path": self.snapshot_path,
        }

    def save(self, directory: Path) -> Path:
        directory.mkdir(parents=True, exist_ok=True)
        path = directory / f"{self.job_id}.json"
        path.write_text(json.dumps(self.to_dict(), indent=2), encoding="utf-8")
        return path

    @classmethod
    def create(
        cls,
        platen_name: str,
        style_name: str,
        style_version: str,
        variant_name: str,
        dataset: str,
        logos: List[JobLogoRecord],
        snapshot_path: str | None = None,
    ) -> "JobCard":
        job_id = datetime.now(timezone.utc).strftime("job_%Y%m%d_%H%M%S")
        return cls(
            job_id=job_id,
            timestamp=_now_iso(),
            platen_name=platen_name,
            style_name=style_name,
            style_version=style_version,
            variant_name=variant_name,
            dataset=dataset,
            logos=logos,
            snapshot_path=snapshot_path,
        )
