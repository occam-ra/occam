#!/usr/bin/env python
"""
Debug why confusion matrix is not showing
"""

import pyoccam2

print("DEBUG: Confusion Matrix Test")
print("=" * 80)

# Initialize and load data
manager = pyoccam2.VBMManager()
manager.init_from_command_line(["occam", "dementia05.txt"])

# Configure
manager.set_report_separator(pyoccam2.SPACESEP)
manager.set_ref_model("bottom")

# Enable debug mode to see what's happening
manager.set_debug_mode(True)

print("\nTest 1: Setting fit_classifier_target globally")
print("-" * 40)
manager.set_fit_classifier_target("0")
fit_report1 = manager.generate_fit_report("IV:ApZ")

# Check output
if "Confusion Matrix" in fit_report1:
    print("✓ SUCCESS: Confusion matrix found!")
else:
    print("✗ FAIL: No confusion matrix")
    # Look for the Note message
    for line in fit_report1.split('\n'):
        if "Note:" in line and "default" in line:
            print(f"Found message: {line}")
            break

print("\nTest 2: Passing target_state directly")
print("-" * 40)
# Clear the global setting
manager.set_fit_classifier_target("")
fit_report2 = manager.generate_fit_report("IV:ApZ", "0")

# Check output
if "Confusion Matrix" in fit_report2:
    print("✓ SUCCESS: Confusion matrix found!")
else:
    print("✗ FAIL: No confusion matrix")
    # Look for the Note message
    for line in fit_report2.split('\n'):
        if "Note:" in line and "default" in line:
            print(f"Found message: {line}")
            break

print("\nTest 3: Both global and parameter")
print("-" * 40)
manager.set_fit_classifier_target("0")
fit_report3 = manager.generate_fit_report("IV:ApZ", "0")

# Check output
if "Confusion Matrix" in fit_report3:
    print("✓ SUCCESS: Confusion matrix found!")
else:
    print("✗ FAIL: No confusion matrix")
    # Look for the Note message
    for line in fit_report3.split('\n'):
        if "Note:" in line and "default" in line:
            print(f"Found message: {line}")
            break