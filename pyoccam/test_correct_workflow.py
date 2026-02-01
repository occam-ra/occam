#!/usr/bin/env python3
"""
Test the CORRECT workflow:
1. generate_fit_report() computes and stores CM
2. get_confusion_matrix() just reads what was stored
"""
import pyoccam
import sys

# Redirect stderr to stdout for PyCharm
sys.stderr = sys.stdout

print("="*80)
print("CORRECT CONFUSION MATRIX WORKFLOW TEST")
print("="*80)
print()

manager = pyoccam.VBMManager()
if not manager.init_from_command_line(["occam", "dementia05.txt"]):
    print("Failed to load data")
    sys.exit(1)

print("Data loaded: dementia05.txt")
print()

# Test with the model from server output
model_name = "IV:ApZ:EdZ:CZ"
target_state = "0"

print(f"Model: {model_name}")
print(f"Target state: {target_state}")
print()
print("="*80)
print("STEP 1: Generate fit report (this computes and stores CM)")
print("="*80)
print()

# This should compute the CM and store it in ManagerBase
fit_report = manager.generate_fit_report(model_name, target_state)

# Check if we see confusion matrix in the output
if "Confusion Matrix" in fit_report:
    print("✓ Fit report contains confusion matrix section")
    # Extract the relevant lines
    lines = fit_report.split('\n')
    for i, line in enumerate(lines):
        if '[CM DEBUG]' in line:
            print(f"  {line}")
        elif 'Confusion Matrix' in line:
            # Print this line and next few
            for j in range(i, min(i+15, len(lines))):
                if lines[j].strip():
                    print(f"  {lines[j]}")
            break
else:
    print("⚠ No confusion matrix found in fit report")

print()
print("="*80)
print("STEP 2: Get confusion matrix (just reads from ManagerBase)")
print("="*80)
print()

# This should just read what was already stored
cm = manager.get_confusion_matrix()

print("Result:")
if "error" in cm:
    print(f"  ✗ Error: {cm['error']}")
elif not cm.get('has_values', False):
    print(f"  ✗ has_values = False")
    print(f"     CM was not populated during fit report")
else:
    tn, fp, fn, tp = cm['TN'], cm['FP'], cm['FN'], cm['TP']
    total = tn + fp + fn + tp
    
    print(f"  TN = {tn:.0f}")
    print(f"  FP = {fp:.0f}")
    print(f"  FN = {fn:.0f}")
    print(f"  TP = {tp:.0f}")
    print(f"  Total = {total:.0f}")
    print(f"  Accuracy = {cm['accuracy']:.3f}")
    
    # Check against server output
    if tn == 352 and fp == 90 and fn == 168 and tp == 238:
        print()
        print("  ✓✓✓ PERFECT MATCH WITH SERVER OUTPUT! ✓✓✓")
    elif total > 400:
        print(f"  ⚠ Values don't match server, but total looks reasonable")
    else:
        print(f"  ✗ Something is wrong with the values")

print()
print("="*80)
