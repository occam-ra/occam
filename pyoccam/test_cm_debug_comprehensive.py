#!/usr/bin/env python3
"""
Comprehensive CM Debug Test
This test will show EXACTLY where the CM computation is failing
"""
import sys
import pyoccam

print("="*80)
print("COMPREHENSIVE CONFUSION MATRIX DEBUG TEST")
print("="*80)
print()

# Initialize
print("Initializing PyOccam...")
manager = pyoccam.VBMManager()
if not manager.init_from_command_line(["occam", "dementia05.txt"]):
    print("ERROR: Failed to load data")
    sys.exit(1)
print("✓ Data loaded: dementia05.txt")
print()

# Test with the best BIC model from server output
model_name = "IV:ApZ:EdZ:CZ"
target_state = "0"

print("="*80)
print("Testing model:", model_name)
print("Target state:", target_state)
print("="*80)
print()
print("CRITICAL: Watch for these debug messages from C++:")
print("  1. 'ENTERED printConditional_DV' - function was called")
print("  2. 'CHECKING TARGET' - verifying target state")
print("  3. 'CM COMPUTATION' - computing the confusion matrix")  
print("  4. 'ATTEMPTING CM STORAGE' - trying to store in manager")
print()
print("If you don't see ALL FOUR sections, that's where the bug is!")
print()
print("="*80)
print("C++ DEBUG OUTPUT SHOULD APPEAR BELOW:")
print("="*80)
sys.stdout.flush()

# This should trigger comprehensive debug output
try:
    cm = manager.get_confusion_matrix(model_name, target_state)
except Exception as e:
    print(f"\n✗ EXCEPTION: {e}\n")
    sys.exit(1)

sys.stdout.flush()

print("="*80)
print("C++ DEBUG OUTPUT ENDED ABOVE")
print("="*80)
print()

# Show what we got back
print("PYTHON RECEIVED:")
print("="*80)
for key in ['TN', 'FP', 'FN', 'TP', 'has_values', 'error']:
    value = cm.get(key, 'NOT_PRESENT')
    print(f"{key:15s} = {value}")
print()

# Diagnose
if 'error' in cm:
    print("✗ ERROR:", cm['error'])
    print()
    print("This means:")
    print("  - printConditional_DV completed")
    print("  - But has_values was still FALSE")
    print("  - So the storage code never ran OR ran but didn't set has_values")
elif all(cm.get(k, 0) == 0 for k in ['TN', 'FP', 'FN', 'TP']):
    print("✗ All values are zero")
else:
    total = cm.get('TN', 0) + cm.get('FP', 0) + cm.get('FN', 0) + cm.get('TP', 0)
    print(f"✓ SUCCESS! Total = {total}")

print()
print("="*80)
print("DIAGNOSIS GUIDE:")
print("="*80)
print()
print("If you saw 'ENTERED printConditional_DV' multiple times:")
print("  → Function is being called for main model + component relations")
print("  → The FIRST call should store CM (rel==NULL)")
print()
print("If checkTarget was FALSE:")
print("  → This is the bug! The target state didn't match any DV labels")
print("  → Check the 'CHECKING TARGET' section for the mismatch")
print()
print("If checkTarget was TRUE but 'PASSED lock check' wasn't shown:")
print("  → The has_values lock is preventing storage")
print("  → This means clearMainModelConfusionMatrix() didn't work")
print()
print("If you saw 'PASSED lock check' but still got error:")
print("  → setMainModelConfusionMatrix() might not be working")
print("="*80)
