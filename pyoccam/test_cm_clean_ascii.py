#!/usr/bin/env python3
"""
Clean ASCII-only CM Debug Test - No Unicode
"""
import sys
import pyoccam

print("="*80)
print("CONFUSION MATRIX DEBUG TEST - ASCII ONLY")
print("="*80)
print()

# Initialize
print("Initializing PyOccam...")
manager = pyoccam.VBMManager()
if not manager.init_from_command_line(["occam", "dementia05.txt"]):
    print("ERROR: Failed to load data")
    sys.exit(1)
print("[OK] Data loaded: dementia05.txt")
print()

# Test with the best BIC model from server output
model_name = "IV:ApZ:EdZ:CZ"
target_state = "0"

print("="*80)
print("Testing model:", model_name)
print("Target state:", target_state)
print("="*80)
print()
print("WATCH FOR THESE C++ DEBUG MESSAGES:")
print("  1. 'ENTERED printConditional_DV' - function was called")
print("  2. 'CHECKING TARGET' - verifying target state")
print("  3. 'CM COMPUTATION' - computing the confusion matrix")  
print("  4. 'ATTEMPTING CM STORAGE' - trying to store in manager")
print()
print("If messages stop after #1, there's an early return!")
print()
print("="*80)
print("C++ DEBUG OUTPUT BELOW:")
print("="*80)
sys.stdout.flush()

# This should trigger comprehensive debug output
try:
    cm = manager.get_confusion_matrix(model_name, target_state)
except Exception as e:
    print("\n[ERROR] EXCEPTION:", str(e))
    import traceback
    traceback.print_exc()
    sys.exit(1)

sys.stdout.flush()

print("="*80)
print("C++ DEBUG OUTPUT ENDED")
print("="*80)
print()

# Show what we got back
print("PYTHON RECEIVED:")
print("-"*80)
for key in ['TN', 'FP', 'FN', 'TP', 'has_values', 'error']:
    value = cm.get(key, 'NOT_PRESENT')
    print("  {:15s} = {}".format(key, value))
print()

# Diagnose
if 'error' in cm:
    print("[X] ERROR:", cm['error'])
    print()
    print("DIAGNOSIS:")
    print("  - printConditional_DV was called")
    print("  - But has_values stayed FALSE")
    print("  - Check which debug section appeared last")
    print()
    print("If only 'ENTERED' appeared:")
    print("  -> Function returned early (likely isDirected() check)")
    print()
    print("If 'CHECKING TARGET' showed checkTarget=FALSE:")
    print("  -> Target state didn't match DV labels")
    print()
    print("If 'CM COMPUTATION' was skipped:")
    print("  -> checkTarget was FALSE, so no CM computed")
    print()
    print("If 'ATTEMPTING CM STORAGE' showed guard failure:")
    print("  -> One of the conditions (rel==NULL, model!=NULL, etc) failed")
    
elif all(cm.get(k, 0) == 0 for k in ['TN', 'FP', 'FN', 'TP']):
    print("[X] All values are zero - CM was not computed")
else:
    total = cm.get('TN', 0) + cm.get('FP', 0) + cm.get('FN', 0) + cm.get('TP', 0)
    print("[OK] SUCCESS! Total = {}".format(total))
    print("Expected: 424")

print()
print("="*80)
