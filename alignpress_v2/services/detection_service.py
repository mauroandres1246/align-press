"""Wrapper around the existing detection pipeline."""
from __future__ import annotations

from alignpress_v2.domain.models import Config, DetectionResult


class DetectionService:
    """Call into the legacy detection pipeline with a simplified API."""

    def detect(self, frame, config: Config) -> DetectionResult:
        # Placeholder implementation; integration with the existing core will
        # happen in a later phase. For now we return an empty result so that
        # scaffolding can progress without hardware dependencies.
        return DetectionResult.empty()
