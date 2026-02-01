#!/usr/bin/env python3
"""
Diagnostic test to understand why confusion matrix is returning garbage values
"""
import sys
import pyoccam

print("="*80)
print("CONFUSION MATRIX DIAGNOSTIC TEST")
print("="*80)
print()

# Redirect stderr to see C++ debug output
import io
import os

# Initialize
manager = pyoccam.VBMManager()
if not manager.init_from_command_line(["occam", "dementia05.txt"]):
    print("❌ Failed to load data")
    sys.exit(1)

print("✓ Data loaded successfully")
print()

# Test with a simple predictive model
model_name = "IV:ApZ:EdZ:CZ"  # Server's best BIC model
target_state = "0"

print(f"Testing model: {model_name}")
print(f"Target state: '{target_state}'")
print()
print("=" * 80)
print("CALLING get_confusion_matrix()...")
print("=" * 80)
print()
print("Note: C++ debug output from ReportPrintConditionalDV.cpp should appear here")
print("      showing classTarget, DV labels, and checkTarget status")
print()

# THIS SHOULD TRIGGER DEBUG OUTPUT FROM C++
cm = manager.get_confusion_matrix(model_name, target_state)

print()
print("=" * 80)
print("PYTHON RECEIVED:")
print("=" * 80)
print(f"TN = {cm.get('TN', 'NOT FOUND')}")
print(f"FP = {cm.get('FP', 'NOT FOUND')}")
print(f"FN = {cm.get('FN', 'NOT FOUND')}")
print(f"TP = {cm.get('TP', 'NOT FOUND')}")
print()

# Check for uninitialized values
tn = cm.get('TN', 0)
if abs(tn) > 1000:  # Garbage value
    print("❌ ERROR: TN contains garbage value (uninitialized memory)")
    print("   This means the confusion matrix was never stored in the manager")
    print()
    print("Possible causes:")
    print("  1. checkTarget is false (target_state doesn't match any DV label)")
    print("  2. rel parameter is not NULL (should be NULL for main model)")
    print("  3. model parameter is NULL")
    print()
    print("SOLUTION: Check the C++ debug output above for:")
    print("  - What is classTarget?")
    print("  - What are the DV labels?")
    print("  - Is checkTarget set to TRUE?")
elif tn == 0 and cm.get('FP', 0) == 0:
    print("❌ ERROR: All values are zero")
    print("   The confusion matrix was initialized but never populated")
else:
    print("✓ Got valid confusion matrix values!")
    total = tn + cm.get('FP', 0) + cm.get('FN', 0) + cm.get('TP', 0)
    print(f"   Total = {total} (expected 424)")

print()
print("=" * 80)
