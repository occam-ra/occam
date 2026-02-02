#!/usr/bin/env python3
"""
Step-by-step test to see exactly where it hangs
"""
import pyoccam
import sys

# Redirect stderr to stdout
sys.stderr = sys.stdout

print("="*80)
print("STEP-BY-STEP HANG DIAGNOSTIC")
print("="*80)

print("\n[1/5] Importing pyoccam... ", end='', flush=True)
print("OK")

print("[2/5] Creating manager... ", end='', flush=True)
manager = pyoccam.VBMManager()
print("OK")

print("[3/5] Loading data... ", end='', flush=True)
if not manager.init_from_command_line(["occam", "dementia05.txt"]):
    print("FAILED")
    exit(1)
print("OK")

print("[4/5] Calling generate_fit_report()... ", end='', flush=True)
sys.stdout.flush()

# This is where it might hang
model_name = "IV:ApZ"
target = "0"

try:
    fit_report = manager.generate_fit_report(model_name, target)
    print("OK")
    print(f"    Report length: {len(fit_report)} characters")
    
    # Check for confusion matrix in output
    if "Confusion Matrix" in fit_report:
        print("    ✓ Report contains 'Confusion Matrix'")
    else:
        print("    ✗ Report does NOT contain 'Confusion Matrix'")
        
    if "[CM DEBUG]" in fit_report:
        print("    ✓ Report contains '[CM DEBUG]' messages")
        # Extract and show them
        for line in fit_report.split('\n'):
            if '[CM DEBUG]' in line:
                print(f"      {line.strip()}")
    else:
        print("    ✗ Report does NOT contain '[CM DEBUG]' messages")
        
except Exception as e:
    print(f"ERROR: {e}")
    exit(1)

print("[5/5] Calling get_confusion_matrix()... ", end='', flush=True)
try:
    cm = manager.get_confusion_matrix()
    print("OK")
    
    if "error" in cm:
        print(f"    ✗ Error: {cm['error']}")
    elif cm.get('has_values', False):
        print(f"    ✓ Success!")
        print(f"      TN={cm['TN']:.0f}, FP={cm['FP']:.0f}, FN={cm['FN']:.0f}, TP={cm['TP']:.0f}")
    else:
        print(f"    ✗ has_values=False")
        
except Exception as e:
    print(f"ERROR: {e}")
    exit(1)

print("\n" + "="*80)
print("TEST COMPLETE")
print("="*80)
