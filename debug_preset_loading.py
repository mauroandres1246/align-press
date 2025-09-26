#!/usr/bin/env python3
"""
Debug script to test Configuration Designer preset loading
"""

import os
import sys
import json
from pathlib import Path

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_config_designer_loading():
    """Test Configuration Designer preset loading logic directly"""
    print("🔍 Testing Configuration Designer preset loading...")

    try:
        # Import the Configuration Designer
        from alignpress_v2.tools.config_designer import ConfigurationDesigner

        # Create instance but don't initialize GUI
        designer = ConfigurationDesigner.__new__(ConfigurationDesigner)

        # Initialize basic state without GUI
        designer.current_config = None
        designer.current_style = None
        designer.mm_per_pixel = 1.0

        # Test loading a preset file
        preset_path = "configs/Comunicaciones Corinta/Talla S/Delantera.json"

        if not os.path.exists(preset_path):
            print(f"❌ Preset file not found: {preset_path}")
            return False

        print(f"📁 Loading preset: {preset_path}")

        # Read the preset manually (like the _load_preset method does)
        with open(preset_path, 'r', encoding='utf-8') as f:
            config_data = json.load(f)

        print(f"📊 Preset data:")
        print(f"   Design: {config_data.get('design')}")
        print(f"   Size: {config_data.get('size')}")
        print(f"   Part: {config_data.get('part')}")
        print(f"   Logos: {len(config_data.get('logos', []))}")

        # Simulate the loading process
        from alignpress_v2.config.models import Style, Logo, Point, Rectangle

        # Initialize style like in _load_preset
        designer.current_style = Style(
            id=f"{config_data.get('design')}_{config_data.get('size')}_{config_data.get('part')}",
            name=f"{config_data.get('design')} {config_data.get('size')} {config_data.get('part')}",
            logos=[]
        )

        # Load logos
        designer.current_style.logos.clear()
        for logo_data in config_data.get('logos', []):
            logo = Logo(
                id=logo_data['id'],
                name=logo_data['name'],
                position_mm=Point(logo_data['position_mm']['x'], logo_data['position_mm']['y']),
                tolerance_mm=logo_data.get('tolerance_mm', 3.0),
                detector_type=logo_data.get('detector_type', logo_data.get('detector', 'template_matching')),
                roi=Rectangle(
                    logo_data['roi']['x'],
                    logo_data['roi']['y'],
                    logo_data['roi']['width'],
                    logo_data['roi']['height']
                )
            )
            designer.current_style.logos.append(logo)

        print(f"✅ Loaded {len(designer.current_style.logos)} logos into current_style")

        # Check what logos are actually loaded
        for i, logo in enumerate(designer.current_style.logos):
            print(f"   Logo {i+1}: {logo.id} - {logo.name}")

        # Check if there's any default config interference
        if hasattr(designer, 'current_config') and designer.current_config:
            print("⚠️  current_config exists - checking for default logos...")
            if hasattr(designer.current_config, 'library') and designer.current_config.library.styles:
                for style in designer.current_config.library.styles:
                    print(f"   Config style: {style.id} with {len(style.logos)} logos")
                    for logo in style.logos:
                        print(f"     - {logo.id}: {logo.name}")
        else:
            print("✅ No current_config interference")

        return len(designer.current_style.logos) > 0

    except Exception as e:
        print(f"❌ Error testing Configuration Designer: {e}")
        import traceback
        traceback.print_exc()
        return False

def check_for_default_config_calls():
    """Check where create_default_config might be called inappropriately"""
    print("\n🔍 Checking for inappropriate default config calls...")

    config_designer_path = "alignpress_v2/tools/config_designer.py"

    with open(config_designer_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Find all create_default_config calls
    import re
    calls = []
    lines = content.split('\n')

    for i, line in enumerate(lines):
        if 'create_default_config()' in line:
            calls.append((i+1, line.strip()))

    print(f"📊 Found {len(calls)} create_default_config() calls:")
    for line_num, line_content in calls:
        print(f"   Line {line_num}: {line_content}")

    # Check if any are called during preset loading
    preset_load_start = None
    for i, line in enumerate(lines):
        if 'def _load_preset(self):' in line:
            preset_load_start = i
            break

    if preset_load_start:
        # Look for create_default_config in the next 100 lines
        preset_load_section = lines[preset_load_start:preset_load_start+100]
        for i, line in enumerate(preset_load_section):
            if 'create_default_config()' in line:
                print(f"⚠️  create_default_config() found in _load_preset at line {preset_load_start + i + 1}")
                print(f"     {line.strip()}")
                return True

    print("✅ No create_default_config() calls found in _load_preset method")
    return False

def main():
    """Run all debug tests"""
    print("=" * 60)
    print("🐛 DEBUG: CONFIGURATION DESIGNER PRESET LOADING")
    print("=" * 60)

    tests = [
        ("Configuration Designer Loading", test_config_designer_loading),
        ("Default Config Interference", check_for_default_config_calls)
    ]

    results = []
    for test_name, test_func in tests:
        print(f"\n{'=' * 20} {test_name} {'=' * 20}")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} failed: {e}")
            results.append((test_name, False))

    # Summary
    print(f"\n{'=' * 60}")
    print("📊 DEBUG SUMMARY")
    print("=" * 60)

    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:<30} {status}")

    return all(result for _, result in results)

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)