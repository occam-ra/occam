#!/usr/bin/env python3
"""
Direct debugging of confusion matrix generation
Tests the C++ Report class methods directly
"""

import pyoccam
import sys

print("=" * 80)
print("DIRECT CONFUSION MATRIX DEBUGGING")
print("=" * 80)

# Initialize
manager = pyoccam.VBMManager()
success = manager.init_from_command_line(["occam", "dementia05.txt"])
if not success:
    print("ERROR: Failed to initialize")
    sys.exit(1)

print("✓ Data loaded successfully\n")

# Test parameters
model_name = "IV:ApZ"
target_state = "0"

print(f"Testing model: {model_name}")
print(f"Target state: {target_state}")
print()

# Step 1: Generate fit report WITH target state
print("=" * 80)
print("STEP 1: Generate fit report with target_state")
print("=" * 80)
fit_report = manager.generate_fit_report(model_name, target_state)

# Check if confusion matrix appears
if "Confusion Matrix" in fit_report:
    print("✓ Confusion matrix text found in fit report!")
    
    # Find and display the relevant section
    cm_start = fit_report.find("Confusion Matrix")
    cm_section = fit_report[cm_start:cm_start+1000] if cm_start >= 0 else ""
    print("\nConfusion matrix section:")
    print("-" * 40)
    print(cm_section)
    print("-" * 40)
else:
    print("✗ No confusion matrix found in fit report")
    print("\nSearching for conditional DV section...")
    
    if "Conditional DV" in fit_report:
        print("✓ Found Conditional DV section")
        cdv_start = fit_report.find("Conditional DV")
        cdv_section = fit_report[cdv_start:cdv_start+500] if cdv_start >= 0 else ""
        print("\nConditional DV section:")
        print("-" * 40)
        print(cdv_section)
        print("-" * 40)
    else:
        print("✗ No Conditional DV section found either")
    
    print("\nFull fit report length:", len(fit_report))
    print("\nFirst 500 chars of report:")
    print("-" * 40)
    print(fit_report[:500])
    print("-" * 40)

# Step 2: Test get_confusion_matrix directly
print("\n" + "=" * 80)
print("STEP 2: Test get_confusion_matrix()")
print("=" * 80)

cm = manager.get_confusion_matrix(model_name, target_state)
print("\nReturned values:")
for key, value in cm.items():
    if key != 'error':
        print(f"  {key}: {value}")

# Check if we got actual values
if cm.get('accuracy', 0) > 0:
    print("\n✓ Got actual confusion matrix values!")
else:
    print("\n✗ No values extracted")
    if 'error' in cm:
        print(f"  Error: {cm['error']}")

# Step 3: Alternative approach - generate without target first, then with
print("\n" + "=" * 80)
print("STEP 3: Compare with/without target_state")
print("=" * 80)

# Without target
report_no_target = manager.generate_fit_report(model_name, "")
print(f"Report without target_state: {len(report_no_target)} chars")

# With target
report_with_target = manager.generate_fit_report(model_name, target_state)
print(f"Report with target_state: {len(report_with_target)} chars")

# What's different?
if len(report_with_target) > len(report_no_target):
    extra = len(report_with_target) - len(report_no_target)
    print(f"\n✓ Target state adds {extra} chars to report")
    
    # Find what was added
    if "CONDITIONAL PROBABILITY" in report_with_target:
        print("✓ Found CONDITIONAL PROBABILITY section")
    if "Confusion Matrix" in report_with_target:
        print("✓ Found Confusion Matrix in extended report")
else:
    print("\n✗ Target state doesn't add content to report")

# Step 4: Test different models
print("\n" + "=" * 80)
print("STEP 4: Test with a more complex model")
print("=" * 80)

complex_model = "IV:ApZ:EdZ:CZ"
print(f"Testing model: {complex_model}")

fit_complex = manager.generate_fit_report(complex_model, target_state)
cm_complex = manager.get_confusion_matrix(complex_model, target_state)

if "Confusion Matrix" in fit_complex:
    print("✓ Confusion matrix found for complex model")
else:
    print("✗ No confusion matrix for complex model either")

print(f"\nComplex model accuracy: {cm_complex.get('accuracy', 0):.3f}")

# Step 5: Save all reports for inspection
print("\n" + "=" * 80)
print("STEP 5: Saving reports for inspection")
print("=" * 80)

with open("report_no_target.txt", "w") as f:
    f.write(report_no_target)
print("Saved: report_no_target.txt")

with open("report_with_target.txt", "w") as f:
    f.write(report_with_target)
print("Saved: report_with_target.txt")

with open("report_complex.txt", "w") as f:
    f.write(fit_complex)
print("Saved: report_complex.txt")

# Step 6: Expected values check
print("\n" + "=" * 80)
print("STEP 6: Expected Values (from server)")
print("=" * 80)

print("For model IV:ApZ with target '0':")
print("  Expected TN: 179")
print("  Expected FP: 42")
print("  Expected FN: 98")
print("  Expected TP: 105")
print("  Expected Accuracy: 0.670")

if cm.get('tn', 0) == 179:
    print("\n✓ TN matches expected!")
else:
    print(f"\n✗ TN mismatch: got {cm.get('tn', 0)}, expected 179")

print("\n" + "=" * 80)
print("DIAGNOSTIC COMPLETE")
print("=" * 80)
print("\nCheck the saved report files to see what's being generated.")
print("The confusion matrix should appear after 'CONDITIONAL PROBABILITY TABLES'")
print("\nIf no confusion matrix is found, the issue is likely:")
print("  1. The Report object is not initialized")
print("  2. The printConditional_DV signature is incorrect")
print("  3. The target_state parameter is not being passed correctly")
