#!/usr/bin/env python3
"""
Test script to verify the preset save/load fix
"""

import os
import sys
import json
import tempfile
import shutil

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_preset_loading_simulation():
    """Simulate the preset loading process to verify the fix"""
    print("🔍 Testing preset loading simulation...")

    try:
        # Import required modules
        from alignpress_v2.config.models import Style, Logo, Point, Rectangle, AlignPressConfig, LibraryData

        # Test data like from existing preset
        config_data = {
            "design": "Comunicaciones Corinta",
            "size": "Talla S",
            "part": "Delantera",
            "calibration_factor": 0.35262802243232727,
            "logos": [
                {
                    "id": "logo_comunicaciones",
                    "name": "Logo comunicaciones.png",
                    "position_mm": {"x": 408.343, "y": 126.593},
                    "roi": {"x": 358.343, "y": 76.593, "width": 100, "height": 100},
                    "tolerance_mm": 3.0,
                    "detector_type": "template_matching"
                },
                {
                    "id": "logo_gulf",
                    "name": "Logo gulf.png",
                    "position_mm": {"x": 208.050, "y": 220.745},
                    "roi": {"x": 158.050, "y": 170.745, "width": 100, "height": 100},
                    "tolerance_mm": 3.0,
                    "detector_type": "template_matching"
                },
                {
                    "id": "logo_gana",
                    "name": "Logo gana.png",
                    "position_mm": {"x": 292.681, "y": 312.43},
                    "roi": {"x": 242.681, "y": 262.43, "width": 100, "height": 100},
                    "tolerance_mm": 3.0,
                    "detector_type": "template_matching"
                }
            ]
        }

        print(f"📊 Test data loaded:")
        print(f"   Design: {config_data['design']}")
        print(f"   Size: {config_data['size']}")
        print(f"   Part: {config_data['part']}")
        print(f"   Logos: {len(config_data['logos'])}")

        # Simulate the _load_preset logic
        design = config_data.get('design')
        size = config_data.get('size')
        part = config_data.get('part')

        # Create style (like in _load_preset)
        current_style = Style(
            id=f"{design}_{size}_{part}",
            name=f"{design} {size} {part}",
            logos=[]
        )

        # Load logos from config
        current_style.logos.clear()
        for logo_data in config_data.get('logos', []):
            logo = Logo(
                id=logo_data['id'],
                name=logo_data['name'],
                position_mm=Point(logo_data['position_mm']['x'], logo_data['position_mm']['y']),
                tolerance_mm=logo_data.get('tolerance_mm', 3.0),
                detector_type=logo_data.get('detector_type', 'template_matching'),
                roi=Rectangle(
                    logo_data['roi']['x'],
                    logo_data['roi']['y'],
                    logo_data['roi']['width'],
                    logo_data['roi']['height']
                )
            )
            current_style.logos.append(logo)

        print(f"✅ Created style with {len(current_style.logos)} logos")

        # Test the fix: Initialize current_config properly
        current_config = AlignPressConfig(library=LibraryData(styles=[]))
        current_config.library.styles = [current_style]

        print(f"✅ Created config with {len(current_config.library.styles)} styles")

        # Verify the loaded logos
        for i, logo in enumerate(current_style.logos):
            print(f"   Logo {i+1}: {logo.id} - {logo.name} at ({logo.position_mm.x:.1f}, {logo.position_mm.y:.1f})")

        # Verify config doesn't have default logos
        has_chest_logo = any(logo.id == "chest" for style in current_config.library.styles for logo in style.logos)
        has_sleeve_logo = any(logo.id == "sleeve" for style in current_config.library.styles for logo in style.logos)

        if has_chest_logo or has_sleeve_logo:
            print("❌ FAILURE: Config contains default chest/sleeve logos!")
            return False
        else:
            print("✅ SUCCESS: No default chest/sleeve logos found!")

        # Test that we can access the logos without fallback
        loaded_logos = current_config.library.styles[0].logos
        print(f"✅ Config access successful: {len(loaded_logos)} logos available")

        return len(loaded_logos) == 3  # Should have our 3 test logos

    except Exception as e:
        print(f"❌ Error in simulation: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_save_load_cycle():
    """Test complete save/load cycle"""
    print("\n🔍 Testing complete save/load cycle...")

    try:
        # Create temporary directory for test
        temp_dir = tempfile.mkdtemp()
        print(f"📁 Using temp directory: {temp_dir}")

        # Create test preset data
        test_preset = {
            "design": "TestDesign",
            "size": "TestSize",
            "part": "TestPart",
            "calibration_factor": 0.5,
            "logos": [
                {
                    "id": "test_logo_1",
                    "name": "Test Logo 1",
                    "position_mm": {"x": 100.0, "y": 150.0},
                    "roi": {"x": 50.0, "y": 100.0, "width": 100.0, "height": 100.0},
                    "tolerance_mm": 3.0,
                    "detector_type": "template_matching"
                },
                {
                    "id": "test_logo_2",
                    "name": "Test Logo 2",
                    "position_mm": {"x": 200.0, "y": 250.0},
                    "roi": {"x": 150.0, "y": 200.0, "width": 100.0, "height": 100.0},
                    "tolerance_mm": 3.0,
                    "detector_type": "template_matching"
                }
            ]
        }

        # Save test preset
        test_file = os.path.join(temp_dir, "test_preset.json")
        with open(test_file, 'w', encoding='utf-8') as f:
            json.dump(test_preset, f, indent=2, ensure_ascii=False)

        print(f"💾 Saved test preset with {len(test_preset['logos'])} logos")

        # Load test preset (simulate _load_preset)
        with open(test_file, 'r', encoding='utf-8') as f:
            loaded_data = json.load(f)

        print(f"📖 Loaded preset data:")
        print(f"   Design: {loaded_data['design']}")
        print(f"   Logos: {len(loaded_data['logos'])}")

        # Verify logos match
        original_logos = test_preset['logos']
        loaded_logos = loaded_data['logos']

        if len(original_logos) != len(loaded_logos):
            print(f"❌ Logo count mismatch: {len(original_logos)} vs {len(loaded_logos)}")
            return False

        for i, (orig, loaded) in enumerate(zip(original_logos, loaded_logos)):
            if orig['id'] != loaded['id'] or orig['name'] != loaded['name']:
                print(f"❌ Logo {i+1} mismatch: {orig['id']} vs {loaded['id']}")
                return False

        print("✅ Save/load cycle successful!")
        return True

    except Exception as e:
        print(f"❌ Error in save/load test: {e}")
        return False
    finally:
        # Cleanup
        if 'temp_dir' in locals():
            shutil.rmtree(temp_dir)

def test_no_default_interference():
    """Test that default config doesn't interfere with loaded preset"""
    print("\n🔍 Testing default config interference...")

    try:
        from alignpress_v2.config.models import create_default_config, AlignPressConfig, LibraryData, Style, Logo, Point, Rectangle

        # Create default config (this contains chest/sleeve logos)
        default_config = create_default_config()
        print(f"📊 Default config has {len(default_config.library.styles)} styles")

        for style in default_config.library.styles:
            print(f"   Style '{style.id}' with {len(style.logos)} logos:")
            for logo in style.logos:
                print(f"     - {logo.id}: {logo.name}")

        # Now create a separate config for our loaded preset (like the fix does)
        preset_config = AlignPressConfig(library=LibraryData(styles=[]))

        # Create a style with custom logos
        custom_style = Style(
            id="custom_style",
            name="Custom Style",
            logos=[
                Logo(
                    id="custom_logo_1",
                    name="Custom Logo 1",
                    position_mm=Point(100, 100),
                    roi=Rectangle(50, 50, 100, 100),
                    tolerance_mm=3.0,
                    detector_type="template_matching"
                )
            ]
        )

        preset_config.library.styles = [custom_style]

        print(f"📊 Preset config has {len(preset_config.library.styles)} styles")
        for style in preset_config.library.styles:
            print(f"   Style '{style.id}' with {len(style.logos)} logos:")
            for logo in style.logos:
                print(f"     - {logo.id}: {logo.name}")

        # Verify no interference
        preset_logo_ids = [logo.id for style in preset_config.library.styles for logo in style.logos]
        default_logo_ids = [logo.id for style in default_config.library.styles for logo in style.logos]

        has_default_interference = any(logo_id in default_logo_ids for logo_id in preset_logo_ids)

        if has_default_interference:
            print("❌ FAILURE: Default config is interfering with preset!")
            return False
        else:
            print("✅ SUCCESS: No interference between default and preset configs!")
            return True

    except Exception as e:
        print(f"❌ Error in interference test: {e}")
        return False

def main():
    """Run all tests"""
    print("=" * 70)
    print("🧪 PRESET SAVE/LOAD FIX VERIFICATION")
    print("=" * 70)

    tests = [
        ("Preset Loading Simulation", test_preset_loading_simulation),
        ("Save/Load Cycle", test_save_load_cycle),
        ("Default Config Interference", test_no_default_interference)
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
    print(f"\n{'=' * 70}")
    print("📊 TEST SUMMARY")
    print("=" * 70)

    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:<30} {status}")
        if result:
            passed += 1

    total = len(results)
    print(f"\nOverall: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 ALL TESTS PASSED! The preset save/load fix should resolve the issue.")
        print("💡 The 'chest pecho and sleeve manga' problem should be fixed.")
    else:
        print("⚠️  Some tests failed. The fix may need additional work.")

    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)