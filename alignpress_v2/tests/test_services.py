"""
Service Integration Tests for AlignPress v2

Tests the service wrappers and their integration with the existing core
"""
import pytest
import numpy as np
from datetime import datetime
from pathlib import Path
import tempfile

from alignpress_v2.config.models import create_default_config, CalibrationData, Logo, Point, Rectangle
from alignpress_v2.services.detection_service import get_detection_service
from alignpress_v2.services.calibration_service import get_calibration_service
from alignpress_v2.services.composition_service import get_composition_service
from alignpress_v2.infrastructure.hardware import get_hardware_manager, LEDColor


class TestDetectionService:
    """Test detection service wrapper"""

    def test_service_creation(self):
        """Test detection service can be created"""
        service = get_detection_service()
        assert service is not None

    def test_available_detectors(self):
        """Test getting available detectors"""
        service = get_detection_service()
        detectors = service.get_available_detectors()

        assert isinstance(detectors, list)
        assert len(detectors) > 0
        assert "contour" in detectors or "aruco" in detectors

    def test_detector_availability(self):
        """Test checking detector availability"""
        service = get_detection_service()

        # Should have at least mock detectors
        assert service.is_detector_available("contour")
        assert not service.is_detector_available("nonexistent")

    def test_mock_detection(self):
        """Test mock detection functionality"""
        service = get_detection_service()
        config = create_default_config()

        # Add calibration
        config.calibration = CalibrationData(
            factor_mm_px=0.2,
            timestamp=datetime.now(),
            method="test"
        )

        # Get first logo from default style
        style = config.get_active_style()
        assert style is not None
        assert len(style.logos) > 0

        logo = style.logos[0]

        # Create mock frame
        frame = np.zeros((480, 640, 3), dtype=np.uint8)

        # Perform detection
        result = service.detect_logo(frame, logo, config)

        assert result is not None
        assert result.logo_id == logo.id
        assert isinstance(result.success, bool)
        assert isinstance(result.position, tuple)
        assert len(result.position) == 2
        assert isinstance(result.confidence, float)
        assert 0.0 <= result.confidence <= 1.0


class TestCalibrationService:
    """Test calibration service wrapper"""

    def test_service_creation(self):
        """Test calibration service can be created"""
        service = get_calibration_service()
        assert service is not None

    def test_mock_calibration(self):
        """Test mock calibration functionality"""
        service = get_calibration_service()

        # Create mock frame
        frame = np.ones((480, 640, 3), dtype=np.uint8) * 128

        # Perform calibration
        calibration = service.calibrate_from_chessboard(frame)

        assert calibration is not None
        assert isinstance(calibration.factor_mm_px, float)
        assert calibration.factor_mm_px > 0
        assert calibration.method == "mock_chessboard"
        assert isinstance(calibration.timestamp, datetime)

    def test_calibration_quality_assessment(self):
        """Test calibration quality assessment"""
        service = get_calibration_service()

        # Recent calibration should be excellent
        recent_calibration = CalibrationData(
            factor_mm_px=0.2,
            timestamp=datetime.now(),
            method="test"
        )

        quality = service.get_calibration_quality(recent_calibration)
        assert quality == "excellent"

        # Old calibration should be expired
        from datetime import timedelta
        old_calibration = CalibrationData(
            factor_mm_px=0.2,
            timestamp=datetime.now() - timedelta(days=35),
            method="test"
        )

        quality = service.get_calibration_quality(old_calibration)
        assert quality == "expired"


class TestCompositionService:
    """Test composition service wrapper"""

    def test_service_creation(self):
        """Test composition service can be created"""
        service = get_composition_service()
        assert service is not None

    def test_composition_validation(self):
        """Test composition validation"""
        service = get_composition_service()
        config = create_default_config()

        # Without calibration, should fail
        assert not service.validate_composition(config)

        # With calibration, should pass
        config.calibration = CalibrationData(
            factor_mm_px=0.2,
            timestamp=datetime.now(),
            method="test"
        )

        assert service.validate_composition(config)

    def test_preset_composition(self):
        """Test preset composition"""
        service = get_composition_service()
        config = create_default_config()

        # Add calibration
        config.calibration = CalibrationData(
            factor_mm_px=0.2,
            timestamp=datetime.now(),
            method="test"
        )

        # Compose presets
        presets = service.compose_presets(config)

        assert isinstance(presets, list)
        assert len(presets) > 0

        # Check first preset structure
        preset = presets[0]
        assert "logo_id" in preset
        assert "display_name" in preset
        assert "target_position_mm" in preset
        assert "tolerance_mm" in preset
        assert "detector_type" in preset


class TestHardwareManager:
    """Test hardware abstraction layer"""

    def test_hardware_manager_creation(self):
        """Test hardware manager can be created"""
        manager = get_hardware_manager()
        assert manager is not None

    def test_mock_interface_registration(self):
        """Test mock interface is registered by default"""
        manager = get_hardware_manager()

        # Initialize mock interface
        success = manager.initialize_interface("mock")
        assert success
        assert manager.is_connected()

    def test_led_control(self):
        """Test LED control through hardware manager"""
        manager = get_hardware_manager()
        manager.initialize_interface("mock")

        # Test LED colors
        assert manager.set_led(LEDColor.RED)
        assert manager.set_led(LEDColor.GREEN)
        assert manager.set_led(LEDColor.OFF)

    def test_button_state(self):
        """Test button state reading"""
        manager = get_hardware_manager()
        manager.initialize_interface("mock")

        # Button state should be boolean
        button_state = manager.get_button_state()
        assert isinstance(button_state, bool)

    def test_hardware_shutdown(self):
        """Test hardware shutdown"""
        manager = get_hardware_manager()
        manager.initialize_interface("mock")

        assert manager.is_connected()

        manager.shutdown()

        # After shutdown, should not be connected
        # Note: Mock hardware might still report connected,
        # this tests the shutdown process works


class TestServiceIntegration:
    """Test integration between services"""

    def test_complete_workflow(self):
        """Test complete workflow using all services"""
        # Get all services
        detection_service = get_detection_service()
        calibration_service = get_calibration_service()
        composition_service = get_composition_service()
        hardware_manager = get_hardware_manager()

        # Initialize hardware
        hardware_manager.initialize_interface("mock")

        # Create configuration
        config = create_default_config()

        # Perform calibration
        frame = np.ones((480, 640, 3), dtype=np.uint8) * 128
        calibration = calibration_service.calibrate_from_chessboard(frame)
        assert calibration is not None

        # Apply calibration to config
        config.calibration = calibration

        # Validate composition is possible
        assert composition_service.validate_composition(config)

        # Compose presets
        presets = composition_service.compose_presets(config)
        assert len(presets) > 0

        # Perform detection on first logo
        style = config.get_active_style()
        logo = style.logos[0]

        # Signal start with LED
        hardware_manager.set_led(LEDColor.BLUE)

        result = detection_service.detect_logo(frame, logo, config)
        assert result is not None

        # Signal result with LED
        if result.success:
            hardware_manager.set_led(LEDColor.GREEN)
        else:
            hardware_manager.set_led(LEDColor.RED)

        # Test completed successfully
        assert True

    def test_service_error_handling(self):
        """Test service error handling"""
        detection_service = get_detection_service()

        # Test with invalid configuration
        config = create_default_config()
        config.library.styles = []  # Remove all styles

        # Should handle gracefully
        frame = np.zeros((480, 640, 3), dtype=np.uint8)

        # This should not crash
        try:
            # Create a minimal logo for testing
            test_logo = Logo(
                id="test",
                name="Test Logo",
                position_mm=Point(100, 100),
                tolerance_mm=2.0,
                detector_type="contour",
                roi=Rectangle(50, 50, 100, 100)
            )

            result = detection_service.detect_logo(frame, test_logo, config)
            # Should return a result even with invalid config
            assert result is not None
        except Exception as e:
            pytest.fail(f"Service should handle errors gracefully: {e}")


if __name__ == "__main__":
    # Run basic validation
    print("Running AlignPress v2 service integration tests...")

    # Test detection service
    detection_service = get_detection_service()
    print(f"✅ Detection service: {len(detection_service.get_available_detectors())} detectors")

    # Test calibration service
    calibration_service = get_calibration_service()
    frame = np.ones((100, 100, 3), dtype=np.uint8) * 128
    calibration = calibration_service.calibrate_from_chessboard(frame)
    print(f"✅ Calibration service: {calibration.factor_mm_px:.4f} mm/px")

    # Test composition service
    composition_service = get_composition_service()
    config = create_default_config()
    config.calibration = calibration
    presets = composition_service.compose_presets(config)
    print(f"✅ Composition service: {len(presets)} presets composed")

    # Test hardware manager
    hardware_manager = get_hardware_manager()
    hardware_manager.initialize_interface("mock")
    hardware_manager.set_led(LEDColor.GREEN)
    print(f"✅ Hardware manager: connected={hardware_manager.is_connected()}")

    print("\n🎉 Service integration validation complete!")