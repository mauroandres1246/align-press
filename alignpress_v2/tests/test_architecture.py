"""
Basic Architecture Tests for AlignPress v2

These tests validate that the new architecture works and can be used for static evaluation
"""
import pytest
from pathlib import Path
import tempfile
import json

from alignpress_v2.config.models import create_default_config, AlignPressConfig
from alignpress_v2.config.config_manager import ConfigManager
from alignpress_v2.controller.app_controller import AppController
from alignpress_v2.controller.state_manager import StateManager, AppMode
from alignpress_v2.controller.event_bus import get_event_bus, EventType


class TestConfigurationSchema:
    """Test the unified configuration system"""

    def test_default_config_creation(self):
        """Test creating default configuration"""
        config = create_default_config()

        assert config.version == "2.0.0"
        assert config.system.language == "es"
        assert config.library.platens
        assert config.library.styles
        assert config.library.variants
        assert config.session.active_platen_id == "default_platen"

    def test_config_serialization(self):
        """Test config can be serialized to/from JSON"""
        config = create_default_config()

        # Create temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            config_path = Path(f.name)

        try:
            # Test save/load cycle
            manager = ConfigManager(config_path)
            manager.save(config)

            loaded_config = manager.load()

            assert loaded_config.version == config.version
            assert loaded_config.system.language == config.system.language
            assert loaded_config.session.active_platen_id == config.session.active_platen_id
            assert len(loaded_config.library.platens) == len(config.library.platens)
            assert len(loaded_config.library.styles) == len(config.library.styles)

        finally:
            config_path.unlink(missing_ok=True)

    def test_config_validation(self):
        """Test configuration validation"""
        config = create_default_config()
        manager = ConfigManager()

        # Valid config should pass
        assert manager.validate(config)

        # Invalid reference should fail
        config.session.active_style_id = "nonexistent_style"
        assert not manager.validate(config)

    def test_config_ready_for_detection(self):
        """Test detection readiness check"""
        config = create_default_config()

        # Without calibration, not ready
        assert not config.is_ready_for_detection

        # Add calibration
        from datetime import datetime
        from alignpress_v2.config.models import CalibrationData
        config.calibration = CalibrationData(
            factor_mm_px=0.5,
            timestamp=datetime.now(),
            method="test"
        )

        # Should be ready now
        assert config.is_ready_for_detection


class TestEventSystem:
    """Test the event bus system"""

    def test_event_bus_creation(self):
        """Test event bus singleton creation"""
        bus1 = get_event_bus()
        bus2 = get_event_bus()

        # Should be the same instance
        assert bus1 is bus2

    def test_event_subscription_and_publishing(self):
        """Test basic event flow"""
        bus = get_event_bus()
        events_received = []

        def handler(event):
            events_received.append(event)

        # Subscribe to events
        bus.subscribe(EventType.CONFIG_CHANGED, handler)

        # Emit event
        bus.emit(EventType.CONFIG_CHANGED, {"test": "data"}, "TestSource")

        # Verify received
        assert len(events_received) == 1
        assert events_received[0].type == EventType.CONFIG_CHANGED
        assert events_received[0].data["test"] == "data"
        assert events_received[0].source == "TestSource"


class TestStateManager:
    """Test the state management system"""

    def test_state_manager_initialization(self):
        """Test state manager starts with correct defaults"""
        config = create_default_config()
        state_mgr = StateManager(config)

        assert state_mgr.state.mode == AppMode.IDLE
        assert state_mgr.state.current_logo_index == 0
        assert len(state_mgr.state.detection_results) == 0
        assert state_mgr.state.config == config

    def test_logo_selection(self):
        """Test logo selection functionality"""
        config = create_default_config()
        state_mgr = StateManager(config)

        # Should have logos from default style
        assert len(state_mgr.state.current_logos) > 0

        # Test valid selection
        assert state_mgr.select_logo(0)
        assert state_mgr.state.current_logo_index == 0

        # Test invalid selection
        assert not state_mgr.select_logo(999)
        assert state_mgr.state.current_logo_index == 0  # Should remain unchanged

    def test_mode_changes(self):
        """Test application mode changes"""
        config = create_default_config()
        state_mgr = StateManager(config)

        # Should start in IDLE
        assert state_mgr.state.mode == AppMode.IDLE

        # Change mode
        state_mgr.set_mode(AppMode.DETECTING)
        assert state_mgr.state.mode == AppMode.DETECTING

        # Change back
        state_mgr.set_mode(AppMode.IDLE)
        assert state_mgr.state.mode == AppMode.IDLE


class TestAppController:
    """Test the main application controller"""

    def test_app_controller_initialization(self):
        """Test app controller initializes properly"""
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
            config_path = Path(f.name)

        try:
            controller = AppController(config_path)

            assert controller.config is not None
            assert controller.state is not None
            assert controller.config.version == "2.0.0"

        finally:
            config_path.unlink(missing_ok=True)

    def test_startup_sequence(self):
        """Test complete startup sequence"""
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
            config_path = Path(f.name)

        try:
            controller = AppController(config_path)

            # Startup should succeed
            assert controller.startup()

            # Hardware should be "connected" (mocked)
            assert controller.state.hardware_status.camera_connected

            # Should be in IDLE mode
            assert controller.state.mode == AppMode.IDLE

        finally:
            config_path.unlink(missing_ok=True)

    def test_configuration_updates(self):
        """Test configuration update workflow"""
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
            config_path = Path(f.name)

        try:
            controller = AppController(config_path)
            controller.startup()

            # Should have default selections
            assert controller.config.session.active_platen_id == "default_platen"
            assert controller.config.session.active_style_id == "basic_tshirt"

            # Update style should work
            assert controller.update_style("basic_tshirt")

            # Invalid style should fail
            assert not controller.update_style("nonexistent_style")

        finally:
            config_path.unlink(missing_ok=True)

    def test_detection_workflow(self):
        """Test basic detection workflow"""
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
            config_path = Path(f.name)

        try:
            controller = AppController(config_path)
            controller.startup()

            # Add calibration to make system ready
            from datetime import datetime
            from alignpress_v2.config.models import CalibrationData
            config = controller.config
            config.calibration = CalibrationData(
                factor_mm_px=0.5,
                timestamp=datetime.now(),
                method="test"
            )
            controller.state_manager.update_config(config)

            # Should be ready now
            assert controller.state.is_ready_for_detection

            # Start detection should work
            assert controller.start_detection()
            assert controller.state.mode == AppMode.DETECTING

            # Stop detection
            controller.stop_detection()
            assert controller.state.mode == AppMode.IDLE

        finally:
            config_path.unlink(missing_ok=True)


class TestArchitectureIntegration:
    """Test that all components work together"""

    def test_complete_workflow(self):
        """Test a complete workflow from startup to detection"""
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
            config_path = Path(f.name)

        try:
            # 1. Initialize controller
            controller = AppController(config_path)

            # 2. Startup
            assert controller.startup()

            # 3. Verify initial state
            assert controller.state.mode == AppMode.IDLE
            assert len(controller.state.current_logos) > 0

            # 4. Add calibration
            from datetime import datetime
            from alignpress_v2.config.models import CalibrationData
            config = controller.config
            config.calibration = CalibrationData(
                factor_mm_px=0.5,
                timestamp=datetime.now(),
                method="test"
            )
            controller.state_manager.update_config(config)

            # 5. Select a logo
            assert controller.select_logo(0)
            assert controller.state.current_logo is not None

            # 6. Start detection
            assert controller.start_detection()
            assert controller.state.mode == AppMode.DETECTING

            # 7. Stop detection
            controller.stop_detection()
            assert controller.state.mode == AppMode.IDLE

            # 8. Shutdown
            controller.shutdown()

            # Config should have been saved
            assert config_path.exists()

        finally:
            config_path.unlink(missing_ok=True)

    def test_state_summary(self):
        """Test state summary generation"""
        config = create_default_config()
        state_mgr = StateManager(config)

        summary = state_mgr.get_state_summary()
        assert "Mode:" in summary
        assert "Logo:" in summary
        assert "Ready:" in summary


if __name__ == "__main__":
    # Run basic validation
    print("Running AlignPress v2 architecture validation...")

    # Test config creation
    config = create_default_config()
    print(f"✅ Configuration created: {config.version}")

    # Test state manager
    state_mgr = StateManager(config)
    print(f"✅ State manager created: {state_mgr.state.mode}")

    # Test controller
    controller = AppController()
    success = controller.startup()
    print(f"✅ Controller startup: {'success' if success else 'failed'}")

    print("\n🎉 AlignPress v2 architecture validation complete!")
    print(f"📊 Status: {controller.state_manager.get_state_summary()}")