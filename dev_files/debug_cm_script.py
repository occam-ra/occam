#!/usr/bin/env python3
"""
Diagnostic script to figure out what's wrong with get_confusion_matrix()
"""
import pyoccam

print("="*70)
print("CONFUSION MATRIX DEBUG SCRIPT")
print("="*70)

# Initialize
manager = pyoccam.VBMManager()
if not manager.init_from_command_line(["occam", "dementia05.txt"]):
    print("❌ Failed to load data")
    exit(1)

print("✓ Data loaded")
print()

# Test with IV:ApZ
model_name = "IV:ApZ"
target_state = "0"

print(f"Testing model: {model_name}")
print(f"Target state: {target_state}")
print()

# Call get_confusion_matrix and see what we get back
print("Calling get_confusion_matrix()...")
cm = manager.get_confusion_matrix(model_name, target_state)

print()
print("="*70)
print("RESULT:")
print("="*70)

# Print all keys and values
for key in sorted(cm.keys()):
    print(f"  {key}: {cm[key]}")

print()

# Check specifically for error
if "error" in cm:
    print(f"❌ ERROR FOUND: {cm['error']}")
    print()
    print("This means the C++ code returned an error.")
    print("Most likely reasons:")
    print("  1. Model has no predictive relations")
    print("  2. computeConfusionMatrix() returned is_valid=false")
    print("  3. Target state '0' not found in the DV")
else:
    if cm['TP'] == 0 and cm['TN'] == 0 and cm['FP'] == 0 and cm['FN'] == 0:
        print("⚠️  No error, but all values are ZERO")
        print()
        print("This means:")
        print("  - The method ran without error")
        print("  - But computeConfusionMatrix() returned zeros")
        print("  - Likely the C++ computation has a bug")
    else:
        print("✓ SUCCESS! Got real values:")
        print(f"  TN={cm['TN']}, FP={cm['FP']}")
        print(f"  FN={cm['FN']}, TP={cm['TP']}")
        print(f"  Accuracy={cm['accuracy']:.3f}")
