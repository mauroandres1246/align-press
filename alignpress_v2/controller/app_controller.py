"""Application controller orchestrating AlignPress v2."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, List

from alignpress_v2.controller.event_bus import EventBus
from alignpress_v2.controller.state_manager import AppState, StateManager
from alignpress_v2.services.calibration_service import CalibrationService
from alignpress_v2.services.composition_service import CompositionService
from alignpress_v2.services.detection_service import DetectionService


@dataclass
class AppController:
    """Coordinate UI events, services, and global application state."""

    state_manager: StateManager
    detection_service: DetectionService
    calibration_service: CalibrationService
    composition_service: CompositionService
    event_bus: EventBus = field(default_factory=EventBus)
    _ui_ready_callbacks: List[Callable[[], None]] = field(default_factory=list)

    def on_ui_ready(self) -> None:
        """Notify listeners that the UI finished booting."""

        for callback in self._ui_ready_callbacks:
            callback()

    def subscribe_ui_ready(self, callback: Callable[[], None]) -> None:
        """Register a callback that runs when the UI is ready."""

        self._ui_ready_callbacks.append(callback)

    def handle_command(self, command: str) -> None:
        """Dispatch a command originating from the UI layer."""

        if command == "start_detection":
            self._start_detection()
        elif command == "stop_detection":
            self._stop_detection()
        elif command == "calibrate":
            self._begin_calibration()
        else:
            raise ValueError(f"Unknown command: {command}")

    def _start_detection(self) -> None:
        state = self.state_manager.state
        result = self.detection_service.detect(
            frame=None,  # Placeholder until the vision pipeline is integrated.
            config=state.configuration,
        )
        self.state_manager.update_detection(result)
        self.event_bus.publish("detection.completed", result)

    def _stop_detection(self) -> None:
        self.event_bus.publish("detection.stopped", None)

    def _begin_calibration(self) -> None:
        result = self.calibration_service.calibrate(frame=None)
        self.state_manager.update_calibration(result)
        self.event_bus.publish("calibration.completed", result)

    @property
    def state(self) -> AppState:
        """Expose the current application state."""

        return self.state_manager.state
