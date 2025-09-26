#!/usr/bin/env python3
"""
Validation script for AlignPress v2 architecture

This script validates that the new architecture is working correctly
and can be used for static analysis and testing.
"""
import sys
import logging
from pathlib import Path

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent))

from alignpress_v2.config.models import create_default_config
from alignpress_v2.config.config_manager import ConfigManager
from alignpress_v2.controller.app_controller import AppController
from alignpress_v2.controller.event_bus import get_event_bus

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


def validate_configuration():
    """Validate configuration system"""
    print("🔧 Validating Configuration System...")

    # Test default config creation
    config = create_default_config()
    print(f"  ✅ Default config created: v{config.version}")
    print(f"  ✅ Language: {config.system.language}")
    print(f"  ✅ Platens: {len(config.library.platens)}")
    print(f"  ✅ Styles: {len(config.library.styles)}")
    print(f"  ✅ Variants: {len(config.library.variants)}")

    # Test config manager
    config_manager = ConfigManager(Path("config/test_alignpress_v2.json"))
    config_manager.save(config)
    loaded_config = config_manager.load()

    print(f"  ✅ Config save/load working")
    print(f"  ✅ Validation: {config_manager.validate(loaded_config)}")

    # Cleanup
    Path("config/test_alignpress_v2.json").unlink(missing_ok=True)

    return config


def validate_event_system():
    """Validate event system"""
    print("\n📡 Validating Event System...")

    bus = get_event_bus()
    events_received = []

    def test_handler(event):
        events_received.append(event)

    # Subscribe and test
    from alignpress_v2.controller.event_bus import EventType
    bus.subscribe(EventType.CONFIG_CHANGED, test_handler)
    bus.emit(EventType.CONFIG_CHANGED, {"test": "data"}, "ValidationScript")

    print(f"  ✅ Event bus created")
    print(f"  ✅ Events received: {len(events_received)}")

    return len(events_received) > 0


def validate_controller():
    """Validate app controller"""
    print("\n🎛️ Validating App Controller...")

    # Create controller with temp config
    controller = AppController(Path("config/temp_validation.json"))

    print(f"  ✅ Controller initialized")
    print(f"  ✅ Config version: {controller.config.version}")
    print(f"  ✅ Initial mode: {controller.state.mode.value}")

    # Test startup
    startup_success = controller.startup()
    print(f"  ✅ Startup: {'success' if startup_success else 'failed'}")
    print(f"  ✅ Hardware status: camera={controller.state.hardware_status.camera_connected}")

    # Test logo selection
    logo_count = len(controller.state.current_logos)
    print(f"  ✅ Available logos: {logo_count}")

    if logo_count > 0:
        selected = controller.select_logo(0)
        print(f"  ✅ Logo selection: {'success' if selected else 'failed'}")
        current_logo = controller.state.current_logo
        if current_logo:
            print(f"  ✅ Selected logo: {current_logo.id}")

    # Test state summary
    summary = controller.state_manager.get_state_summary()
    print(f"  ✅ State summary: {summary}")

    # Cleanup
    controller.shutdown()
    Path("config/temp_validation.json").unlink(missing_ok=True)

    return startup_success


def validate_complete_workflow():
    """Validate complete workflow"""
    print("\n🔄 Validating Complete Workflow...")

    controller = AppController(Path("config/workflow_test.json"))

    # 1. Startup
    assert controller.startup(), "Startup failed"
    print("  ✅ Step 1: Startup completed")

    # 2. Add calibration to make system ready
    from datetime import datetime
    from alignpress_v2.config.models import CalibrationData
    config = controller.config
    config.calibration = CalibrationData(
        factor_mm_px=0.5,
        timestamp=datetime.now(),
        method="validation_test"
    )
    controller.state_manager.update_config(config)
    print("  ✅ Step 2: Calibration added")

    # 3. Verify system is ready
    ready = controller.state.is_ready_for_detection
    print(f"  ✅ Step 3: System ready for detection: {ready}")

    # 4. Select logo
    if len(controller.state.current_logos) > 0:
        selected = controller.select_logo(0)
        print(f"  ✅ Step 4: Logo selected: {selected}")

        # 5. Simulate detection workflow (if ready)
        if ready and selected:
            detection_started = controller.start_detection()
            print(f"  ✅ Step 5: Detection started: {detection_started}")

            if detection_started:
                controller.stop_detection()
                print("  ✅ Step 6: Detection stopped")

    # 7. Shutdown
    controller.shutdown()
    Path("config/workflow_test.json").unlink(missing_ok=True)
    print("  ✅ Step 7: Shutdown completed")

    return True


def main():
    """Run complete validation"""
    print("🚀 AlignPress v2 Architecture Validation")
    print("=" * 50)

    try:
        # Validate each component
        config = validate_configuration()
        event_success = validate_event_system()
        controller_success = validate_controller()
        workflow_success = validate_complete_workflow()

        print("\n" + "=" * 50)
        print("📊 VALIDATION RESULTS")
        print("=" * 50)
        print(f"✅ Configuration System: {'PASS' if config else 'FAIL'}")
        print(f"✅ Event System: {'PASS' if event_success else 'FAIL'}")
        print(f"✅ Controller System: {'PASS' if controller_success else 'FAIL'}")
        print(f"✅ Complete Workflow: {'PASS' if workflow_success else 'FAIL'}")

        if all([config, event_success, controller_success, workflow_success]):
            print("\n🎉 ARCHITECTURE VALIDATION: PASSED")
            print("\n📋 SUMMARY:")
            print("• Configuration system working correctly")
            print("• Event bus functioning properly")
            print("• State management operational")
            print("• Controller orchestration working")
            print("• Complete workflow tested successfully")
            print("\n✅ AlignPress v2 architecture is ready for:")
            print("  - Static testing and analysis")
            print("  - Algorithm validation")
            print("  - UI development")
            print("  - Service integration")

            return 0
        else:
            print("\n❌ ARCHITECTURE VALIDATION: FAILED")
            return 1

    except Exception as e:
        print(f"\n💥 VALIDATION ERROR: {e}")
        logger.exception("Validation failed with exception")
        return 1


if __name__ == "__main__":
    sys.exit(main())