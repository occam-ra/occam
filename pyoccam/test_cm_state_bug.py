#!/usr/bin/env python3
"""
Test to verify state/caching bug hypothesis:
Does get_confusion_matrix() fail after generate_fit_report()?
"""
import pyoccam

print("="*70)
print("CONFUSION MATRIX STATE BUG TEST")
print("="*70)

# Initialize
manager = pyoccam.VBMManager()
if not manager.init_from_command_line(["occam", "dementia05.txt"]):
    print("❌ Failed to load data")
    exit(1)

print("✓ Data loaded: dementia05.txt\n")

model_name = "IV:ApZ"

# ==============================================================================
# TEST 1: Call get_confusion_matrix() FIRST (before any fit report)
# ==============================================================================
print("TEST 1: get_confusion_matrix() called FIRST")
print("-" * 70)
cm1 = manager.get_confusion_matrix(model_name, "0")
print(f"  Result: TN={cm1['TN']:.0f}, FP={cm1['FP']:.0f}, FN={cm1['FN']:.0f}, TP={cm1['TP']:.0f}")
if cm1['TN'] > 0 or cm1['TP'] > 0:
    print("  ✓ Got real values!\n")
else:
    print("  ❌ All zeros!\n")

# ==============================================================================
# TEST 2: Call get_confusion_matrix() TWICE in a row
# ==============================================================================
print("TEST 2: get_confusion_matrix() called TWICE in a row")
print("-" * 70)
cm2 = manager.get_confusion_matrix(model_name, "0")
print(f"  Result: TN={cm2['TN']:.0f}, FP={cm2['FP']:.0f}, FN={cm2['FN']:.0f}, TP={cm2['TP']:.0f}")
if cm2['TN'] > 0 or cm2['TP'] > 0:
    print("  ✓ Still works!\n")
else:
    print("  ❌ Second call returned zeros!\n")

# ==============================================================================
# TEST 3: Call generate_fit_report() THEN get_confusion_matrix()
# ==============================================================================
print("TEST 3: generate_fit_report() THEN get_confusion_matrix()")
print("-" * 70)
print("  Generating fit report...")
fit_report = manager.generate_fit_report(model_name, "0")
print(f"  Fit report length: {len(fit_report)} chars")

print("  Now calling get_confusion_matrix()...")
cm3 = manager.get_confusion_matrix(model_name, "0")
print(f"  Result: TN={cm3['TN']:.0f}, FP={cm3['FP']:.0f}, FN={cm3['FN']:.0f}, TP={cm3['TP']:.0f}")
if cm3['TN'] > 0 or cm3['TP'] > 0:
    print("  ✓ Still works after fit report!\n")
else:
    print("  ❌ FAILED after fit report - THIS IS THE BUG!\n")

# ==============================================================================
# TEST 4: Try calling get_confusion_matrix() again
# ==============================================================================
print("TEST 4: get_confusion_matrix() called AFTER the fit report")
print("-" * 70)
cm4 = manager.get_confusion_matrix(model_name, "0")
print(f"  Result: TN={cm4['TN']:.0f}, FP={cm4['FP']:.0f}, FN={cm4['FN']:.0f}, TP={cm4['TP']:.0f}")
if cm4['TN'] > 0 or cm4['TP'] > 0:
    print("  ✓ Recovered!\n")
else:
    print("  ❌ Still broken!\n")

# ==============================================================================
# SUMMARY
# ==============================================================================
print("="*70)
print("SUMMARY")
print("="*70)
print(f"Test 1 (CM first):           {'PASS' if (cm1['TN'] > 0 or cm1['TP'] > 0) else 'FAIL'}")
print(f"Test 2 (CM twice):           {'PASS' if (cm2['TN'] > 0 or cm2['TP'] > 0) else 'FAIL'}")
print(f"Test 3 (CM after fit):       {'PASS' if (cm3['TN'] > 0 or cm3['TP'] > 0) else 'FAIL'}")
print(f"Test 4 (CM again):           {'PASS' if (cm4['TN'] > 0 or cm4['TP'] > 0) else 'FAIL'}")
print()

if (cm1['TN'] > 0 or cm1['TP'] > 0) and (cm3['TN'] == 0 and cm3['TP'] == 0):
    print("🎯 BUG CONFIRMED: generate_fit_report() breaks get_confusion_matrix()")
    print("   Root cause: Likely deleteTablesFromCache() in generate_fit_report()")
elif (cm1['TN'] == 0 and cm1['TP'] == 0):
    print("🤔 get_confusion_matrix() doesn't work at all - different issue")
else:
    print("✅ No state bug detected - both methods work independently")
