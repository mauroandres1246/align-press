#!/usr/bin/env python3
"""
Test script to verify preset save/load functionality
"""

import os
import sys
import json
import tempfile
import shutil

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_json_structure():
    """Test the JSON structure we're saving vs loading"""
    print("🔍 Testing JSON structure...")

    # Check existing preset
    existing_preset = "configs/Comunicaciones Corinta/Talla S/Delantera.json"

    if os.path.exists(existing_preset):
        with open(existing_preset, 'r', encoding='utf-8') as f:
            data = json.load(f)

        print(f"📄 Existing preset structure:")
        print(f"   Design: {data.get('design')}")
        print(f"   Size: {data.get('size')}")
        print(f"   Part: {data.get('part')}")
        print(f"   Logos count: {len(data.get('logos', []))}")
        print(f"   Calibration: {data.get('calibration_factor')}")

        # Check logos structure
        for i, logo in enumerate(data.get('logos', [])):
            print(f"   Logo {i+1}: {logo.get('name')} at ({logo.get('position_mm', {}).get('x')}, {logo.get('position_mm', {}).get('y')})")

        return True
    else:
        print(f"❌ {existing_preset} not found")
        return False

def test_save_structure():
    """Test what structure we should be saving"""
    print("\n🔍 Testing save structure...")

    # Create test data that matches what config_designer should save
    test_data = {
        "design": "TestDesign",
        "size": "TestSize",
        "part": "TestPart",
        "calibration_factor": 0.5,
        "logos": [
            {
                "id": "logo_1",
                "name": "Test Logo",
                "position_mm": {"x": 100.0, "y": 150.0},
                "roi": {"x": 90.0, "y": 140.0, "width": 20.0, "height": 20.0},
                "tolerance_mm": 5.0,
                "detector_type": "template_matching"
            }
        ]
    }

    # Create temporary file
    temp_dir = tempfile.mkdtemp()
    test_file = os.path.join(temp_dir, "test_preset.json")

    try:
        with open(test_file, 'w', encoding='utf-8') as f:
            json.dump(test_data, f, indent=2, ensure_ascii=False)

        print(f"✅ Test preset saved to: {test_file}")

        # Read it back
        with open(test_file, 'r', encoding='utf-8') as f:
            loaded_data = json.load(f)

        print(f"✅ Test preset loaded successfully")
        print(f"   Design: {loaded_data.get('design')}")
        print(f"   Logos: {len(loaded_data.get('logos', []))}")

        return True

    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False
    finally:
        shutil.rmtree(temp_dir)

def check_ui_translation_issues():
    """Check for potential UI translation issues"""
    print("\n🔍 Checking for UI translation issues...")

    config_designer_path = "alignpress_v2/tools/config_designer.py"

    if not os.path.exists(config_designer_path):
        print(f"❌ {config_designer_path} not found")
        return False

    with open(config_designer_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Look for suspicious translations or hardcoded values
    suspicious_patterns = [
        "chest",
        "pecho",
        "sleeve",
        "manga",
        "delantera",
        "trasera"
    ]

    found_patterns = []
    for pattern in suspicious_patterns:
        if pattern.lower() in content.lower():
            found_patterns.append(pattern)

    if found_patterns:
        print(f"🔍 Found UI text patterns: {found_patterns}")

        # Check if these are in the right context
        lines = content.split('\n')
        for i, line in enumerate(lines):
            for pattern in found_patterns:
                if pattern.lower() in line.lower():
                    print(f"   Line {i+1}: {line.strip()}")
    else:
        print("✅ No suspicious translation patterns found")

    return True

def analyze_logo_list_update():
    """Check how _update_logo_list works"""
    print("\n🔍 Analyzing logo list update logic...")

    config_designer_path = "alignpress_v2/tools/config_designer.py"

    with open(config_designer_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Find _update_logo_list function
    import re
    func_pattern = r"def _update_logo_list\(.*?\):(.*?)(?=def|\Z)"
    func_match = re.search(func_pattern, content, re.DOTALL)

    if func_match:
        func_content = func_match.group(1)
        print("✅ Found _update_logo_list function")

        # Check if it clears and repopulates properly
        if "delete(0, tk.END)" in func_content or "clear" in func_content:
            print("✅ Function clears existing items")
        else:
            print("⚠️  Function may not clear existing items properly")

        if "self.current_style" in func_content and "logos" in func_content:
            print("✅ Function references current_style.logos")
        else:
            print("❌ Function may not reference logos correctly")

        if "insert" in func_content:
            print("✅ Function inserts new items")
        else:
            print("❌ Function may not insert items")

    else:
        print("❌ _update_logo_list function not found")

    return func_match is not None

def main():
    """Run all tests"""
    print("=" * 60)
    print("🧪 PRESET SAVE/LOAD ISSUE INVESTIGATION")
    print("=" * 60)

    tests = [
        ("JSON Structure Check", test_json_structure),
        ("Save Structure Test", test_save_structure),
        ("UI Translation Check", check_ui_translation_issues),
        ("Logo List Analysis", analyze_logo_list_update)
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
    print("📊 INVESTIGATION SUMMARY")
    print("=" * 60)

    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:<25} {status}")

    passed = sum(1 for _, result in results if result)
    total = len(results)
    print(f"\nOverall: {passed}/{total} checks passed")

    return passed >= total * 0.75

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)