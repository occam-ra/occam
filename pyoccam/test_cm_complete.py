#!/usr/bin/env python3
"""
Complete confusion matrix test - verifies the struct approach
"""
import pyoccam
import sys

print("=" * 80)
print("CONFUSION MATRIX STRUCT IMPLEMENTATION TEST")
print("=" * 80)
print()

# Initialize
manager = pyoccam.VBMManager()
if not manager.init_from_command_line(["occam", "dementia05.txt"]):
    print("✗ Failed to load data")
    sys.exit(1)

print("✓ Data loaded: dementia05.txt (424 samples)")
print()

# Test models
test_cases = [
    ("IV:ApZ:EdZ:CZ", "0", 352, 90, 168, 238),  # From server output
    ("IV:ApZ", "0", None, None, None, None),  # Any predictive model
    ("IV:EdZ", "0", None, None, None, None),  # Any predictive model
]

print("TEST 1: Basic CM retrieval")
print("-" * 80)
for model_name, target, exp_tn, exp_fp, exp_fn, exp_tp in test_cases:
    cm = manager.get_confusion_matrix(model_name, target)

    if "error" in cm:
        print(f"  ✗ {model_name}: ERROR - {cm['error']}")
    elif not cm.get('has_values', False):
        print(f"  ✗ {model_name}: has_values=False")
    else:
        tn, fp, fn, tp = cm['TN'], cm['FP'], cm['FN'], cm['TP']
        total = tn + fp + fn + tp

        if exp_tn is not None:
            # Check against expected values
            if (tn == exp_tn and fp == exp_fp and fn == exp_fn and tp == exp_tp):
                print(f"  ✓ {model_name}: PERFECT MATCH!")
            else:
                print(f"  ⚠ {model_name}: Got TN={tn:.0f} FP={fp:.0f} FN={fn:.0f} TP={tp:.0f}")
                print(f"                  Expected TN={exp_tn} FP={exp_fp} FN={fn} TP={exp_tp}")
        else:
            # Just check values are reasonable
            if total >= 400 and total <= 424:
                print(f"  ✓ {model_name}: Reasonable values (total={total:.0f})")
            else:
                print(f"  ⚠ {model_name}: Strange total={total:.0f}")

print()
print("TEST 2: State bug regression (fit-then-CM)")
print("-" * 80)
model_name = "IV:ApZ"
print(f"  Step 1: Generate fit report for {model_name}...")
fit_report = manager.generate_fit_report(model_name, "0")
print(f"  Step 2: Get confusion matrix...")
cm = manager.get_confusion_matrix(model_name, "0")

if "error" in cm:
    print(f"  ✗ FAILED: {cm['error']}")
elif not cm.get('has_values', False):
    print(f"  ✗ FAILED: has_values=False (the state bug!)")
elif cm['TN'] == 0 and cm['FP'] == 0:
    print(f"  ✗ FAILED: All zeros (the state bug!)")
else:
    print(f"  ✓ PASSED: Got real values after fit report!")
    print(f"    TN={cm['TN']:.0f} FP={cm['FP']:.0f} FN={cm['FN']:.0f} TP={cm['TP']:.0f}")

print()
print("=" * 80)
print("SUMMARY")
print("=" * 80)
print("If all tests passed, the struct implementation is working!")
print("If Test 2 failed, the state bug still exists.")
print("=" * 80)