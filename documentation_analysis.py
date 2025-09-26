#!/usr/bin/env python3
"""
Documentation Analysis Script
Verifies accuracy and completeness of documentation
"""

import os
import re
import json
from pathlib import Path

def analyze_readme():
    """Analyze README.md for accuracy and completeness"""
    print("📖 Analyzing README.md...")

    with open("README.md", 'r', encoding='utf-8') as f:
        readme_content = f.read()

    issues = []
    suggestions = []

    # Check version mentions
    version_pattern = r"v?(\d+\.\d+\.\d+)"
    versions_found = re.findall(version_pattern, readme_content)
    latest_version = "2.4.0"

    if latest_version not in versions_found:
        issues.append(f"❌ Latest version {latest_version} not prominently mentioned")
    else:
        print(f"✅ Latest version {latest_version} found in README")

    # Check feature mentions
    key_features = [
        "Smart Preset Management",
        "Interactive Preset Loading",
        "Visual Logo Editing",
        "Dual Position Control",
        "drag-to-move",
        "click-to-edit"
    ]

    missing_features = []
    for feature in key_features:
        if feature.lower() not in readme_content.lower():
            missing_features.append(feature)

    if missing_features:
        suggestions.append(f"💡 Consider adding recently implemented features: {missing_features}")
    else:
        print("✅ All key features mentioned in README")

    # Check workflow documentation
    workflow_keywords = [
        "Configuration Designer",
        "Cargar Preset",
        "Guardar Preset",
        "arrastrar",
        "editar logos"
    ]

    documented_workflows = []
    for keyword in workflow_keywords:
        if keyword.lower() in readme_content.lower():
            documented_workflows.append(keyword)

    print(f"✅ Workflow documentation: {len(documented_workflows)}/{len(workflow_keywords)} keywords found")

    # Check file structure accuracy
    if "configs/" in readme_content and "Diseño/Talla/Parte.json" in readme_content:
        print("✅ File structure documentation accurate")
    else:
        issues.append("❌ File structure documentation may be outdated")

    return len(issues) == 0, issues, suggestions

def analyze_changelog():
    """Analyze CHANGELOG.md for completeness"""
    print("\n📝 Analyzing CHANGELOG.md...")

    with open("CHANGELOG.md", 'r', encoding='utf-8') as f:
        changelog_content = f.read()

    issues = []
    suggestions = []

    # Check if latest features are documented
    latest_features = [
        "drag-to-move logo functionality",
        "Interactive preset loading",
        "Smart dropdown population",
        "Visual logo editing",
        "Click logo to edit"
    ]

    # Check v2.4.0 section
    v240_section = re.search(r"\[2\.4\.0\](.*?)\[2\.3\.0\]", changelog_content, re.DOTALL)
    if v240_section:
        v240_content = v240_section.group(1)
        print("✅ v2.4.0 section found")

        # Check for specific improvements we implemented
        recent_improvements = [
            "Interactive preset loading",
            "Visual logo editing",
            "drag-to-move",
            "click-to-edit"
        ]

        missing_in_changelog = []
        for improvement in recent_improvements:
            if improvement.lower() not in v240_content.lower():
                missing_in_changelog.append(improvement)

        if missing_in_changelog:
            suggestions.append(f"💡 Consider adding to v2.4.0: {missing_in_changelog}")
        else:
            print("✅ Recent improvements documented in v2.4.0")
    else:
        issues.append("❌ v2.4.0 section not found or malformed")

    # Check date format
    date_pattern = r"\[2\.4\.0\] - (\d{4}-\d{2}-\d{2})"
    date_match = re.search(date_pattern, changelog_content)
    if date_match:
        print(f"✅ v2.4.0 date found: {date_match.group(1)}")
    else:
        suggestions.append("💡 Consider adding proper date format for v2.4.0")

    return len(issues) == 0, issues, suggestions

def check_code_documentation():
    """Check if code has adequate documentation"""
    print("\n🔍 Checking code documentation...")

    config_designer_path = "alignpress_v2/tools/config_designer.py"

    if not os.path.exists(config_designer_path):
        return False, ["❌ config_designer.py not found"], []

    with open(config_designer_path, 'r', encoding='utf-8') as f:
        code_content = f.read()

    issues = []
    suggestions = []

    # Check for docstrings
    docstring_pattern = r'""".*?"""'
    docstrings = re.findall(docstring_pattern, code_content, re.DOTALL)

    # Count functions
    function_pattern = r'def (\w+)\('
    functions = re.findall(function_pattern, code_content)

    print(f"📊 Code statistics:")
    print(f"   Functions: {len(functions)}")
    print(f"   Docstrings: {len(docstrings)}")

    # Check critical functions have docstrings
    critical_functions = [
        "_load_preset",
        "_save_preset",
        "_on_logo_selected",
        "_on_canvas_drag",
        "_move_logo_to_canvas_position"
    ]

    missing_docs = []
    for func in critical_functions:
        func_pattern = rf"def {func}\(.*?\):\s*\"\"\".*?\"\"\""
        if not re.search(func_pattern, code_content, re.DOTALL):
            missing_docs.append(func)

    if missing_docs:
        suggestions.append(f"💡 Consider adding docstrings to: {missing_docs}")
    else:
        print("✅ Critical functions have docstrings")

    # Check for comments in complex functions
    complex_functions = ["_load_preset", "_save_preset"]
    for func in complex_functions:
        func_start = code_content.find(f"def {func}(")
        if func_start != -1:
            # Get next 50 lines after function start
            func_lines = code_content[func_start:].split('\n')[:50]
            comment_count = sum(1 for line in func_lines if line.strip().startswith('#'))
            if comment_count < 3:
                suggestions.append(f"💡 {func} could use more inline comments")

    return len(issues) == 0, issues, suggestions

def verify_examples_accuracy():
    """Verify that examples match current implementation"""
    print("\n📋 Verifying examples accuracy...")

    issues = []
    suggestions = []

    # Check if example files exist
    example_files = [
        "example_camisola_workflow.py",
        "dev_tools_launcher.py"
    ]

    for example_file in example_files:
        if os.path.exists(example_file):
            print(f"✅ {example_file} exists")

            # Basic check for outdated patterns
            with open(example_file, 'r', encoding='utf-8') as f:
                content = f.read()

            # Check for deprecated patterns
            deprecated_patterns = [
                "self.selected_logo:",
                "variants=",
                "Style.*variants"
            ]

            for pattern in deprecated_patterns:
                if re.search(pattern, content):
                    suggestions.append(f"💡 {example_file} may contain deprecated pattern: {pattern}")

        else:
            issues.append(f"❌ {example_file} not found")

    # Check config examples
    configs_dir = "configs"
    if os.path.exists(configs_dir):
        print("✅ configs/ directory exists")

        # Look for example configs
        example_configs = []
        for root, dirs, files in os.walk(configs_dir):
            for file in files:
                if file.endswith('.json'):
                    example_configs.append(os.path.join(root, file))

        print(f"📊 Found {len(example_configs)} config examples")

        # Verify structure of one example
        if example_configs:
            sample_config = example_configs[0]
            try:
                with open(sample_config, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)

                required_fields = ["design", "size", "part", "calibration_factor", "logos"]
                missing_fields = [field for field in required_fields if field not in config_data]

                if missing_fields:
                    suggestions.append(f"💡 Example config missing fields: {missing_fields}")
                else:
                    print("✅ Example config structure is current")

            except Exception as e:
                issues.append(f"❌ Error reading example config: {e}")
    else:
        issues.append("❌ configs/ directory not found")

    return len(issues) == 0, issues, suggestions

def check_documentation_consistency():
    """Check consistency between different documentation files"""
    print("\n🔄 Checking documentation consistency...")

    issues = []
    suggestions = []

    # Read both files
    with open("README.md", 'r', encoding='utf-8') as f:
        readme_content = f.read()

    with open("CHANGELOG.md", 'r', encoding='utf-8') as f:
        changelog_content = f.read()

    # Check version consistency
    readme_versions = set(re.findall(r"v?(\d+\.\d+\.\d+)", readme_content))
    changelog_versions = set(re.findall(r"\[(\d+\.\d+\.\d+)\]", changelog_content))

    latest_readme = max(readme_versions) if readme_versions else "0.0.0"
    latest_changelog = max(changelog_versions) if changelog_versions else "0.0.0"

    if latest_readme != latest_changelog:
        issues.append(f"❌ Version mismatch: README {latest_readme} vs CHANGELOG {latest_changelog}")
    else:
        print(f"✅ Version consistency: {latest_readme}")

    # Check feature consistency
    readme_features = re.findall(r"✅.*", readme_content)
    changelog_features = re.findall(r"✅.*", changelog_content)

    print(f"📊 Features mentioned:")
    print(f"   README: {len(readme_features)}")
    print(f"   CHANGELOG: {len(changelog_features)}")

    return len(issues) == 0, issues, suggestions

def update_documentation_if_needed():
    """Update documentation based on recent changes"""
    print("\n📝 Checking if documentation needs updates...")

    # Check if we need to add the latest improvements to README
    updates_needed = []

    with open("README.md", 'r', encoding='utf-8') as f:
        readme_content = f.read()

    # Recent features that should be prominently mentioned
    recent_features = {
        "Interactive Preset Loading": "File browser-based preset loading with automatic UI population",
        "Visual Logo Editing": "Click-to-edit and drag-to-move logo functionality",
        "Smart Dropdown Population": "Dropdowns auto-populate based on existing presets",
        "Dual Position Control": "Both visual (drag) and numeric (fields) position editing"
    }

    missing_features = []
    for feature, description in recent_features.items():
        if feature.lower() not in readme_content.lower():
            missing_features.append((feature, description))

    if missing_features:
        print("💡 Consider adding these recent features to README:")
        for feature, desc in missing_features:
            print(f"   • {feature}: {desc}")
        return False, ["Documentation could be enhanced with recent features"]
    else:
        print("✅ README appears up-to-date with recent features")
        return True, []

def generate_documentation_report():
    """Generate comprehensive documentation analysis report"""

    print("=" * 80)
    print("📚 ALIGNPRESS V2 - DOCUMENTATION ANALYSIS")
    print("=" * 80)

    all_results = []

    # Run all checks
    checks = [
        ("README.md Analysis", analyze_readme),
        ("CHANGELOG.md Analysis", analyze_changelog),
        ("Code Documentation", check_code_documentation),
        ("Examples Verification", verify_examples_accuracy),
        ("Documentation Consistency", check_documentation_consistency),
        ("Update Assessment", update_documentation_if_needed)
    ]

    for check_name, check_func in checks:
        print(f"\n{'=' * 20} {check_name} {'=' * 20}")
        try:
            success, issues, suggestions = check_func()
            all_results.append((check_name, success, issues, suggestions))
        except Exception as e:
            print(f"❌ {check_name} failed: {e}")
            all_results.append((check_name, False, [f"Check failed: {e}"], []))

    # Summary
    print(f"\n{'=' * 80}")
    print("📊 DOCUMENTATION ANALYSIS SUMMARY")
    print("=" * 80)

    passed = sum(1 for _, success, _, _ in all_results if success)
    total = len(all_results)

    for check_name, success, issues, suggestions in all_results:
        status = "✅ GOOD" if success else "⚠️  NEEDS ATTENTION"
        print(f"{check_name:<30} {status}")

        if issues:
            for issue in issues:
                print(f"   {issue}")

        if suggestions:
            for suggestion in suggestions:
                print(f"   {suggestion}")

    print(f"\nOverall: {passed}/{total} checks passed")

    if passed >= total * 0.8:
        print("🎉 Documentation is in good shape!")
        if passed < total:
            print("💡 Consider addressing the suggestions above for even better docs.")
    else:
        print("⚠️  Documentation needs attention. Please review the issues above.")

    return passed >= total * 0.8

def main():
    """Run documentation analysis"""
    return generate_documentation_report()

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)