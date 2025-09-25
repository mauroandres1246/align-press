"""State manager for AlignPress v2."""
from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Optional

from alignpress_v2.domain.models import CalibrationResult, Config, DetectionResult


@dataclass(frozen=True)
class AppState:
    """Immutable snapshot of AlignPress application state."""

    current_mode: str = "IDLE"
    current_logo: Optional[str] = None
    detection_results: Optional[DetectionResult] = None
    calibration: Optional[CalibrationResult] = None
    configuration: Config = field(default_factory=Config)


class StateManager:
    """Create and update the global application state."""

    def __init__(self, initial_state: Optional[AppState] = None) -> None:
        self._state = initial_state or AppState()

    @property
    def state(self) -> AppState:
        return self._state

    def update_detection(self, result: DetectionResult) -> None:
        self._state = replace(self._state, detection_results=result, current_mode="DETECTING")

    def update_calibration(self, result: CalibrationResult) -> None:
        self._state = replace(self._state, calibration=result, current_mode="CALIBRATING")

    def update_configuration(self, config: Config) -> None:
        self._state = replace(self._state, configuration=config)
