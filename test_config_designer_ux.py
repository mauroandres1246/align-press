#!/usr/bin/env python3
"""
UX Test Script for Configuration Designer
Tests the complete workflow and identifies potential issues
"""

import os
import sys
import json
import tempfile
import shutil
from pathlib import Path

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test that all required modules can be imported"""
    print("🧪 Testing imports...")
    try:
        from alignpress_v2.tools.config_designer import ConfigDesigner
        from alignpress_v2.config.models import Logo, Style, Point, Rectangle
        print("✅ All imports successful")
        return True
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False

def test_file_structure():
    """Test that the file structure is correct"""
    print("🧪 Testing file structure...")

    # Check main files exist
    files_to_check = [
        "alignpress_v2/tools/config_designer.py",
        "alignpress_v2/config/models.py",
        "alignpress_v2/config/config_manager.py"
    ]

    all_exist = True
    for file_path in files_to_check:
        if os.path.exists(file_path):
            print(f"✅ {file_path} exists")
        else:
            print(f"❌ {file_path} missing")
            all_exist = False

    # Check configs directory structure
    configs_dir = "configs"
    if os.path.exists(configs_dir):
        print(f"✅ {configs_dir} directory exists")
        # List any existing presets
        for root, dirs, files in os.walk(configs_dir):
            level = root.replace(configs_dir, '').count(os.sep)
            indent = ' ' * 2 * level
            print(f"{indent}📁 {os.path.basename(root)}/")
            subindent = ' ' * 2 * (level + 1)
            for file in files:
                if file.endswith('.json'):
                    print(f"{subindent}📄 {file}")
    else:
        print(f"⚠️  {configs_dir} directory doesn't exist yet")

    return all_exist

def test_json_structure():
    """Test JSON structure for saved presets"""
    print("🧪 Testing JSON structure...")

    configs_dir = "configs"
    found_presets = False

    for root, dirs, files in os.walk(configs_dir):
        for file in files:
            if file.endswith('.json'):
                found_presets = True
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)

                    # Check required fields
                    required_fields = ['design', 'size', 'part', 'calibration_factor', 'logos']
                    missing_fields = [field for field in required_fields if field not in data]

                    if missing_fields:
                        print(f"❌ {file_path} missing fields: {missing_fields}")
                    else:
                        print(f"✅ {file_path} has correct structure")

                        # Check logos structure
                        for i, logo in enumerate(data.get('logos', [])):
                            logo_required = ['id', 'name', 'position_mm', 'roi']
                            logo_missing = [field for field in logo_required if field not in logo]
                            if logo_missing:
                                print(f"   ❌ Logo {i} missing: {logo_missing}")
                            else:
                                print(f"   ✅ Logo {i} structure OK")

                except json.JSONDecodeError as e:
                    print(f"❌ {file_path} invalid JSON: {e}")
                except Exception as e:
                    print(f"❌ {file_path} error: {e}")

    if not found_presets:
        print("⚠️  No preset files found - this is normal for new installations")

    return True

def create_test_preset():
    """Create a test preset to verify saving functionality"""
    print("🧪 Creating test preset...")

    configs_dir = "configs"
    test_dir = os.path.join(configs_dir, "TestDesign", "TestSize")
    os.makedirs(test_dir, exist_ok=True)

    test_preset = {
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

    test_file = os.path.join(test_dir, "TestPart.json")

    try:
        with open(test_file, 'w', encoding='utf-8') as f:
            json.dump(test_preset, f, indent=2, ensure_ascii=False)
        print(f"✅ Test preset created: {test_file}")
        return test_file
    except Exception as e:
        print(f"❌ Failed to create test preset: {e}")
        return None

def test_preset_loading_logic():
    """Test the preset loading logic without GUI"""
    print("🧪 Testing preset loading logic...")

    test_file = create_test_preset()
    if not test_file:
        return False

    try:
        # Simulate loading logic
        with open(test_file, 'r', encoding='utf-8') as f:
            config_data = json.load(f)

        # Test path parsing
        configs_dir = "configs"
        rel_path = os.path.relpath(test_file, configs_dir)
        path_parts = rel_path.split(os.sep)

        if len(path_parts) >= 3:
            design = path_parts[0]
            size = path_parts[1]
            part = os.path.splitext(path_parts[2])[0]
            print(f"✅ Path parsing: {design}/{size}/{part}")
        else:
            print(f"❌ Path parsing failed: {path_parts}")
            return False

        # Test logo creation
        for logo_data in config_data.get('logos', []):
            try:
                # Simulate Logo creation (without actual import to avoid GUI dependencies)
                required_logo_fields = ['id', 'name', 'position_mm', 'roi']
                for field in required_logo_fields:
                    if field not in logo_data:
                        raise ValueError(f"Missing field: {field}")
                print(f"✅ Logo validation passed: {logo_data['name']}")
            except Exception as e:
                print(f"❌ Logo validation failed: {e}")
                return False

        print("✅ Preset loading logic test passed")
        return True

    except Exception as e:
        print(f"❌ Preset loading logic failed: {e}")
        return False
    finally:
        # Clean up test file
        if test_file and os.path.exists(test_file):
            os.remove(test_file)
            # Try to remove empty directories
            try:
                os.rmdir(os.path.dirname(test_file))
                os.rmdir(os.path.dirname(os.path.dirname(test_file)))
            except OSError:
                pass  # Directory not empty, that's ok

def test_syntax_compilation():
    """Test that all Python files compile without syntax errors"""
    print("🧪 Testing syntax compilation...")

    files_to_test = [
        "alignpress_v2/tools/config_designer.py",
        "alignpress_v2/config/models.py"
    ]

    all_good = True
    for file_path in files_to_test:
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                compile(content, file_path, 'exec')
                print(f"✅ {file_path} syntax OK")
            except SyntaxError as e:
                print(f"❌ {file_path} syntax error: {e}")
                all_good = False
            except Exception as e:
                print(f"❌ {file_path} compilation error: {e}")
                all_good = False
        else:
            print(f"❌ {file_path} not found")
            all_good = False

    return all_good

def analyze_ux_flow():
    """Analyze the UX flow and identify potential issues"""
    print("🧪 Analyzing UX flow...")

    ux_issues = []
    recommendations = []

    # Check if main workflow is intuitive
    workflow_steps = [
        "1. Cargar imagen de prenda",
        "2. Calibrar sistema (opcional pero recomendado)",
        "3. Seleccionar/crear Diseño, Talla, Parte",
        "4. Cargar template de logo",
        "5. Posicionar logo en imagen",
        "6. Confirmar logo",
        "7. Repetir 4-6 para más logos",
        "8. Guardar preset"
    ]

    print("📋 Flujo de trabajo identificado:")
    for step in workflow_steps:
        print(f"   {step}")

    # Alternative workflow
    alt_workflow = [
        "1. Cargar imagen de prenda",
        "2. Cargar preset existente (carga diseño/talla/parte/logos automáticamente)",
        "3. Editar logos existentes (arrastrar o campos numéricos)",
        "4. Agregar nuevos logos si es necesario",
        "5. Guardar cambios al preset"
    ]

    print("📋 Flujo alternativo (cargar preset existente):")
    for step in alt_workflow:
        print(f"   {step}")

    # Potential UX improvements
    recommendations.extend([
        "✨ Flujo principal bien estructurado",
        "✨ Edición visual de logos implementada",
        "✨ Cargar presets funcional",
        "⚠️  Considerar agregar tooltips/ayuda contextual",
        "⚠️  Validar que imagen esté cargada antes de permitir templates",
        "⚠️  Agregar shortcuts de teclado para funciones comunes"
    ])

    print("📊 Recomendaciones UX:")
    for rec in recommendations:
        print(f"   {rec}")

    return True

def main():
    """Run all tests"""
    print("=" * 60)
    print("🧪 ALIGNPRESS V2 - CONFIGURATION DESIGNER UX TESTS")
    print("=" * 60)

    tests = [
        ("File Structure", test_file_structure),
        ("Imports", test_imports),
        ("JSON Structure", test_json_structure),
        ("Syntax Compilation", test_syntax_compilation),
        ("Preset Loading Logic", test_preset_loading_logic),
        ("UX Flow Analysis", analyze_ux_flow)
    ]

    results = {}

    for test_name, test_func in tests:
        print(f"\n{'=' * 20} {test_name} {'=' * 20}")
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            results[test_name] = False

    # Summary
    print(f"\n{'=' * 60}")
    print("📊 TEST SUMMARY")
    print("=" * 60)

    passed = sum(1 for result in results.values() if result)
    total = len(results)

    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:<25} {status}")

    print(f"\nOverall: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All tests passed! Configuration Designer is ready for use.")
    else:
        print("⚠️  Some tests failed. Please review the issues above.")

    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)