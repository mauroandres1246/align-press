#!/usr/bin/env python3
"""
UI Integration Test for AlignPress v2

Tests the complete UI integration with the controller layer
"""
import sys
import os
import logging

# Add alignpress_v2 to Python path
sys.path.insert(0, os.path.abspath('.'))

def test_ui_creation():
    """Test creating UI components without running main loop"""
    print("Testing UI component creation...")

    try:
        from alignpress_v2.ui.app import AlignPressApp

        # Create application
        app = AlignPressApp()

        # Test initialization
        success = app.initialize()

        if success:
            print("✅ UI initialization successful")

            # Test that components were created
            if hasattr(app.main_window, 'viewport'):
                print("✅ Viewport component created")
            else:
                print("❌ Viewport component missing")

            if hasattr(app.main_window, 'control_panel'):
                print("✅ Control panel component created")
            else:
                print("❌ Control panel component missing")

            # Test controller integration
            if app.controller:
                print("✅ Controller integrated")

                # Test configuration loading
                if app.controller.config:
                    print("✅ Configuration loaded")
                else:
                    print("❌ Configuration not loaded")

                # Test state manager
                if app.controller.state:
                    print("✅ State manager available")
                else:
                    print("❌ State manager not available")
            else:
                print("❌ Controller not integrated")

            print("✅ UI integration test passed")
            return True

        else:
            print("❌ UI initialization failed")
            return False

    except Exception as e:
        print(f"❌ UI integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_component_interaction():
    """Test component interaction without GUI"""
    print("\nTesting component interaction...")

    try:
        from alignpress_v2.ui.components import create_camera_viewport, create_control_panel
        from alignpress_v2.config.models import create_default_config, Logo, Point, Rectangle
        from alignpress_v2.controller.state_manager import DetectionResult
        import tkinter as tk

        # Create a test root window (but don't show it)
        root = tk.Tk()
        root.withdraw()  # Hide the window

        # Create components
        viewport = create_camera_viewport(root)
        control_panel = create_control_panel(root)

        print("✅ Components created successfully")

        # Test viewport functionality
        config = create_default_config()
        style = config.get_active_style()
        if style and len(style.logos) > 0:
            viewport.set_target_logos(style.logos)
            print("✅ Viewport target logos set")

        # Test detection result display
        import time
        test_result = DetectionResult(
            logo_id="test_logo",
            success=True,
            position=(100, 150),
            angle=45.0,
            confidence=0.85,
            error_mm=2.5,
            error_deg=1.2,
            timestamp=time.time()
        )
        viewport.set_detection_results([test_result])
        print("✅ Viewport detection results set")

        # Test control panel updates
        control_panel.update_from_config(config)
        print("✅ Control panel config update")

        status_updates = {
            "mode": "READY",
            "detection": "Active",
            "calibration": "Available"
        }
        control_panel.update_status(status_updates)
        print("✅ Control panel status update")

        metrics = {
            "total_detections": "5",
            "successful": "4",
            "failed": "1",
            "success_rate": "80%"
        }
        control_panel.update_metrics(metrics)
        print("✅ Control panel metrics update")

        # Clean up
        root.destroy()

        print("✅ Component interaction test passed")
        return True

    except Exception as e:
        print(f"❌ Component interaction test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all UI integration tests"""
    print("=" * 50)
    print("AlignPress v2 UI Integration Tests")
    print("=" * 50)

    # Setup logging
    logging.basicConfig(level=logging.WARNING)  # Reduce log noise

    tests = [
        test_ui_creation,
        test_component_interaction
    ]

    results = []
    for test in tests:
        results.append(test())

    print("\n" + "=" * 50)
    if all(results):
        print("🎉 All UI integration tests PASSED")
        return 0
    else:
        print("💥 Some UI integration tests FAILED")
        return 1

if __name__ == "__main__":
    sys.exit(main())