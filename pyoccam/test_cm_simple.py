#!/usr/bin/env python3
"""
Simple confusion matrix test - ASCII only for Windows compatibility
"""
import sys
import pyoccam

print("="*80)
print("CONFUSION MATRIX TEST - ASCII VERSION")
print("="*80)
print()

# Initialize
print("1. Initializing PyOccam...")
manager = pyoccam.VBMManager()
if not manager.init_from_command_line(["occam", "dementia05.txt"]):
    print("ERROR: Failed to load data")
    sys.exit(1)
print("OK: Data loaded: dementia05.txt (424 samples)")
print()

# Test with server's best BIC model
model_name = "IV:ApZ:EdZ:CZ"
target_state = "0"

print("="*80)
print("Testing model:", model_name)
print("Target state:", target_state)
print("="*80)
print()

print("NOTE: C++ debug output should appear below this line")
print("      Look for 'DEBUG ReportPrintConditionalDV' messages")
print("-"*80)

# Flush to ensure message appears before C++ output
sys.stdout.flush()

# This should trigger debug output
cm = manager.get_confusion_matrix(model_name, target_state)

# Flush again before showing results
sys.stdout.flush()

print("-"*80)
print()
print("RESULTS RECEIVED IN PYTHON:")
print("="*80)
print("TN =", cm.get('TN', 'NOT FOUND'))
print("FP =", cm.get('FP', 'NOT FOUND'))
print("FN =", cm.get('FN', 'NOT FOUND'))
print("TP =", cm.get('TP', 'NOT FOUND'))
print()

# Diagnose the values
tn = cm.get('TN', 0)
fp = cm.get('FP', 0)
fn = cm.get('FN', 0)
tp = cm.get('TP', 0)

print("DIAGNOSIS:")
print("-"*80)

# Check for uninitialized memory (huge garbage values)
if abs(tn) > 1000 or abs(fp) > 1000:
    print("ERROR: Got garbage values (uninitialized memory)")
    print("       This means the confusion matrix was NEVER stored")
    print()
    print("WHAT TO LOOK FOR IN DEBUG OUTPUT ABOVE:")
    print("  1. Was checkTarget set to TRUE?")
    print("  2. Did you see 'STORED in Manager' message?")
    print("  3. What were the actual DV labels?")
    
elif tn == 0 and fp == 0 and fn == 0 and tp == 0:
    print("ERROR: All values are zero")
    print("       CM was initialized but never populated")
    
else:
    total = tn + fp + fn + tp
    print("OK: Got valid confusion matrix!")
    print(f"    Total = {total} (expected 424)")
    if total > 400:
        print("    Values look correct!")
    else:
        print("    WARNING: Total seems low")

print()
print("="*80)
print("If you don't see 'DEBUG ReportPrintConditionalDV' above,")
print("the debug output is not being shown. Make sure to use:")
print("    python test_cm_simple.py 2>&1")
print("to redirect stderr to stdout")
print("="*80)
