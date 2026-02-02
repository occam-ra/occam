#!/usr/bin/env python3
"""
Test to diagnose the checkTarget issue - redirects stderr to stdout for PyCharm
"""
import pyoccam
import sys

# CRITICAL: Redirect stderr to stdout so we can see debug output in PyCharm
sys.stderr = sys.stdout

print("="*80)
print("CONFUSION MATRIX DEBUG TEST")
print("="*80)
print()

# Initialize
manager = pyoccam.VBMManager()
if not manager.init_from_command_line(["occam", "dementia05.txt"]):
    print("Failed to load data")
    sys.exit(1)

print("Data loaded. Now testing with different target states...")
print()
print("NOTE: You should see [CM DEBUG] messages below for each test")
print("="*80)
print()

# Test multiple potential target states
test_states = ["0", "1", "case", "control", "Case", "Control", "Y", "N"]

for target in test_states:
    print(f"\n{'='*80}")
    print(f"TESTING target_state='{target}'")
    print(f"{'='*80}")
    sys.stdout.flush()
    
    cm = manager.get_confusion_matrix("IV:ApZ", target)
    
    print(f"\nPython received:")
    print(f"  has_values: {cm.get('has_values', 'N/A')}")
    print(f"  TN={cm.get('TN', 0):.0f}, FP={cm.get('FP', 0):.0f}, FN={cm.get('FN', 0):.0f}, TP={cm.get('TP', 0):.0f}")
    
    total = cm.get('TN', 0) + cm.get('FP', 0) + cm.get('FN', 0) + cm.get('TP', 0)
    
    if "error" not in cm and cm.get('has_values', False) and total > 0:
        print(f"\n*** SUCCESS! Target '{target}' works! ***")
        print(f"    Total = {total:.0f}")
        print(f"\nFOUND IT! Use target_state='{target}'")
        break
    elif total > 0:
        print(f"  ⚠ Got non-zero values but has_values={cm.get('has_values', 'N/A')}")
    else:
        print(f"  ✗ Failed (all zeros)")

print("\n" + "="*80)
print("Test complete.")
print("="*80)
print()
print("WHAT TO LOOK FOR:")
print("  - Each test should show '[CM DEBUG] classTarget=...' messages")
print("  - Look for '[CM DEBUG] dv_label[0]=...' to see actual DV states")
print("  - Look for '[CM DEBUG] MATCH found' to see which target works")
print("="*80)
