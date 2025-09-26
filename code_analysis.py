#!/usr/bin/env python3
"""
Code Analysis Script for Configuration Designer
Identifies potential issues, bugs, and improvements
"""

import ast
import os
import re

def analyze_config_designer():
    """Analyze the main config_designer.py file"""
    print("🔍 Analyzing config_designer.py...")

    file_path = "alignpress_v2/tools/config_designer.py"

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    issues = []
    suggestions = []

    # Check for potential issues

    # 1. Check for unused variables/imports
    if "self.selected_logo:" in content:
        issues.append("⚠️  Found reference to removed self.selected_logo variable")

    # 2. Check for missing error handling
    error_prone_functions = [
        "_load_preset", "_save_preset", "_on_canvas_drag",
        "_move_logo_to_canvas_position", "_display_image"
    ]

    for func in error_prone_functions:
        func_pattern = rf"def {func}\(.*?\):(.*?)(?=def|\Z)"
        func_match = re.search(func_pattern, content, re.DOTALL)
        if func_match:
            func_content = func_match.group(1)
            if "try:" not in func_content:
                suggestions.append(f"💡 Consider adding error handling to {func}")

    # 3. Check for hardcoded values
    hardcoded_patterns = [
        (r"width=\d+", "Hardcoded width values"),
        (r"size\s*=\s*\d+", "Hardcoded size values"),
        (r"tolerance_mm=\d+\.\d+", "Hardcoded tolerance values"),
    ]

    for pattern, desc in hardcoded_patterns:
        matches = re.findall(pattern, content)
        if matches:
            suggestions.append(f"💡 {desc} found: {len(matches)} instances")

    # 4. Check for potential memory leaks
    if "self.photo_image =" in content and "del self.photo_image" not in content:
        suggestions.append("💡 Consider cleanup of self.photo_image to prevent memory leaks")

    # 5. Check for missing validations
    validation_checks = [
        ("self.current_image is None", "Image validation"),
        ("self.mm_per_pixel", "Calibration validation"),
        ("self.selected_logo_index is not None", "Logo index validation")
    ]

    for check, desc in validation_checks:
        if check in content:
            print(f"✅ {desc} present")
        else:
            issues.append(f"⚠️  Missing {desc}")

    # 6. Check function complexity (approximate)
    function_pattern = r"def (\w+)\(.*?\):(.*?)(?=def|\Z)"
    functions = re.findall(function_pattern, content, re.DOTALL)

    complex_functions = []
    for func_name, func_body in functions:
        lines = len([line for line in func_body.split('\n') if line.strip()])
        if lines > 50:
            complex_functions.append((func_name, lines))

    if complex_functions:
        suggestions.append("💡 Consider breaking down large functions:")
        for func_name, lines in complex_functions:
            suggestions.append(f"   - {func_name}: {lines} lines")

    print(f"📊 Analysis results:")
    print(f"   Functions analyzed: {len(functions)}")
    print(f"   Issues found: {len(issues)}")
    print(f"   Suggestions: {len(suggestions)}")

    if issues:
        print("\n❌ Issues found:")
        for issue in issues:
            print(f"   {issue}")

    if suggestions:
        print("\n💡 Suggestions:")
        for suggestion in suggestions:
            print(f"   {suggestion}")

    return len(issues) == 0

def check_function_signatures():
    """Check for consistent function signatures"""
    print("\n🔍 Checking function signatures...")

    file_path = "alignpress_v2/tools/config_designer.py"

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Find all event handler functions
    event_handlers = re.findall(r"def (_on_\w+)\((.*?)\):", content)

    issues = []

    for func_name, params in event_handlers:
        if "event" in params and "event=None" not in params:
            # Event handlers should have event=None as default
            issues.append(f"⚠️  {func_name} should have event=None default parameter")

    print(f"Event handlers found: {len(event_handlers)}")

    if issues:
        print("❌ Function signature issues:")
        for issue in issues:
            print(f"   {issue}")
        return False
    else:
        print("✅ All function signatures look good")
        return True

def check_ui_consistency():
    """Check UI element consistency"""
    print("\n🔍 Checking UI consistency...")

    file_path = "alignpress_v2/tools/config_designer.py"

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Check for consistent button styles
    button_patterns = [
        r'ttk\.Button\([^)]*text="([^"]*)"',
        r'ttk\.Button\([^)]*text=\'([^\']*)\''
    ]

    buttons = []
    for pattern in button_patterns:
        buttons.extend(re.findall(pattern, content))

    # Check for emoji consistency
    emoji_buttons = [btn for btn in buttons if any(char for char in btn if ord(char) > 127)]
    non_emoji_buttons = [btn for btn in buttons if not any(char for char in btn if ord(char) > 127)]

    suggestions = []

    if emoji_buttons and non_emoji_buttons:
        suggestions.append("💡 Consider consistent emoji usage in buttons")
        suggestions.append(f"   Emoji buttons: {len(emoji_buttons)}")
        suggestions.append(f"   Non-emoji buttons: {len(non_emoji_buttons)}")

    # Check for consistent color usage
    color_usage = re.findall(r'foreground="(\w+)"', content)
    color_counts = {}
    for color in color_usage:
        color_counts[color] = color_counts.get(color, 0) + 1

    print(f"Color usage:")
    for color, count in color_counts.items():
        print(f"   {color}: {count} times")

    if suggestions:
        for suggestion in suggestions:
            print(f"{suggestion}")
    else:
        print("✅ UI consistency looks good")

    return len(suggestions) == 0

def check_variable_naming():
    """Check variable naming consistency"""
    print("\n🔍 Checking variable naming...")

    file_path = "alignpress_v2/tools/config_designer.py"

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Check for consistent variable naming patterns
    variable_patterns = [
        (r"self\.(\w+)_var", "UI variables"),
        (r"self\.(\w+)_frame", "Frame variables"),
        (r"self\.(\w+)_label", "Label variables"),
        (r"self\.(\w+)_button", "Button variables")
    ]

    inconsistencies = []

    for pattern, desc in variable_patterns:
        matches = re.findall(pattern, content)
        # Check naming consistency (should be snake_case)
        for match in matches:
            if re.search(r'[A-Z]', match):
                inconsistencies.append(f"⚠️  {desc}: {match} should use snake_case")

    if inconsistencies:
        print("❌ Variable naming issues:")
        for issue in inconsistencies:
            print(f"   {issue}")
        return False
    else:
        print("✅ Variable naming is consistent")
        return True

def main():
    """Run all code analysis checks"""
    print("=" * 60)
    print("🔍 CONFIGURATION DESIGNER CODE ANALYSIS")
    print("=" * 60)

    checks = [
        ("Main Code Analysis", analyze_config_designer),
        ("Function Signatures", check_function_signatures),
        ("UI Consistency", check_ui_consistency),
        ("Variable Naming", check_variable_naming)
    ]

    results = {}

    for check_name, check_func in checks:
        print(f"\n{'=' * 20} {check_name} {'=' * 20}")
        try:
            results[check_name] = check_func()
        except Exception as e:
            print(f"❌ {check_name} failed: {e}")
            results[check_name] = False

    # Summary
    print(f"\n{'=' * 60}")
    print("📊 CODE ANALYSIS SUMMARY")
    print("=" * 60)

    passed = sum(1 for result in results.values() if result)
    total = len(results)

    for check_name, result in results.items():
        status = "✅ PASS" if result else "⚠️  ISSUES"
        print(f"{check_name:<25} {status}")

    print(f"\nOverall: {passed}/{total} checks passed")

    if passed == total:
        print("🎉 Code analysis passed! No critical issues found.")
    else:
        print("⚠️  Some issues found. Consider reviewing the suggestions above.")

    return passed >= total * 0.8  # 80% pass rate is acceptable

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)