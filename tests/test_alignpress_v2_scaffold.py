"""Smoke tests for the AlignPress v2 scaffolding."""
from __future__ import annotations

import json
import textwrap

from alignpress_v2.config.config_manager import ConfigManager
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


def test_config_manager_migrates_yaml(tmp_path):
    legacy_yaml = textwrap.dedent(
        """
        schema_version: 3
        language: en
        ui:
          theme: light
        selection:
          platen_path: ../platens/default_platen.json
          style_path: ../styles/example_style.json
          variant_path: ../variants/example_variant.json
        """
    ).strip()

    config_path = tmp_path / "app.yaml"
    config_path.write_text(legacy_yaml, encoding="utf-8")

    manager = ConfigManager(config_path)
    config = manager.load()

    assert config.language == "en"
    assert config.theme == "light"
    assert config.active_platen_id == "default_platen"
    assert config.active_style_id == "example_style"
    assert config.active_variant_id == "example_variant"


def test_config_manager_respects_json_output(tmp_path):
    config_path = tmp_path / "config.json"
    manager = ConfigManager(config_path)

    base_config = manager.load()
    updated = base_config.__class__(
        version="1",
        language="es",
        units="mm",
        theme="dark",
        active_platen_id="default",
        active_style_id="style",
        active_variant_id="variant",
    )

    manager.save(updated)

    raw = json.loads(config_path.read_text(encoding="utf-8"))
    assert raw["active_style_id"] == "style"
    assert config_path.suffix == ".json"
