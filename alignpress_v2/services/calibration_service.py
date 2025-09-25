"""Calibration service wrapper."""
from __future__ import annotations

from alignpress_v2.domain.models import CalibrationResult


class CalibrationService:
    """Provide a thin abstraction over the calibration workflow."""

    def calibrate(self, frame) -> CalibrationResult:
        # Placeholder implementation to be replaced with the real calibration
        # pipeline. Returning a neutral calibration ensures the state manager
        # can be exercised during early integration tests.
        return CalibrationResult.identity()
