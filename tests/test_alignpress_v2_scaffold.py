"""Smoke tests for the AlignPress v2 scaffolding."""
from alignpress_v2.controller.app_controller import AppController
from alignpress_v2.controller.state_manager import StateManager
from alignpress_v2.services.calibration_service import CalibrationService
from alignpress_v2.services.composition_service import CompositionService
from alignpress_v2.services.detection_service import DetectionService


def test_controller_updates_state():
    controller = AppController(
        state_manager=StateManager(),
        detection_service=DetectionService(),
        calibration_service=CalibrationService(),
        composition_service=CompositionService(),
    )

    controller.handle_command("start_detection")
    assert controller.state.current_mode == "DETECTING"

    controller.handle_command("calibrate")
    assert controller.state.current_mode == "CALIBRATING"


def test_unknown_command_raises():
    controller = AppController(
        state_manager=StateManager(),
        detection_service=DetectionService(),
        calibration_service=CalibrationService(),
        composition_service=CompositionService(),
    )

    try:
        controller.handle_command("invalid")
    except ValueError as exc:
        assert "Unknown command" in str(exc)
    else:  # pragma: no cover - defensive
        raise AssertionError("ValueError was not raised")
