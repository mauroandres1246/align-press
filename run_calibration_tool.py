#!/usr/bin/env python3
"""
Direct launcher for AlignPress v2 Visual Calibration Tool

Quick access to calibration functionality
"""
import sys
import os

# Add alignpress_v2 to Python path
sys.path.insert(0, os.path.abspath('.'))

if __name__ == "__main__":
    try:
        from alignpress_v2.tools.calibration_tool import CalibrationTool

        print("🚀 Launching AlignPress v2 Visual Calibration Tool...")
        app = CalibrationTool()
        app.run()

    except ImportError as e:
        print("❌ Error: Required dependencies not available")
        print("   Please install: pip install opencv-python pillow")
        print(f"   Details: {e}")
    except Exception as e:
        print(f"❌ Error launching calibration tool: {e}")
        sys.exit(1)