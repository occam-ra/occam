#!/usr/bin/env python3
"""
Test just the complex model hang
"""
import pyoccam
import sys
import time

sys.stderr = sys.stdout

print("="*80)
print("TESTING COMPLEX MODEL HANG")
print("="*80)

manager = pyoccam.VBMManager()
manager.init_from_command_line(["occam", "dementia05.txt"])

model_name = "IV:ApZ:EdZ:CZ"
target = "0"

print(f"\nModel: {model_name} (4 components)")
print(f"Target: {target}")
print()
print("Starting fit report generation...")
print("If this hangs, press Ctrl+C after 30 seconds")
print()

start = time.time()

fit_report = manager.generate_fit_report(model_name, target)

elapsed = time.time() - start

print(f"\n✓ COMPLETED in {elapsed:.2f} seconds!")
print(f"Report length: {len(fit_report)} chars")

# Check for component relations
if "Component" in fit_report or "Relation" in fit_report:
    print("✓ Report contains component/relation sections")

# Get CM
cm = manager.get_confusion_matrix()
if cm.get('has_values'):
    print(f"\n✓ Confusion Matrix:")
    print(f"  TN={cm['TN']:.0f}, FP={cm['FP']:.0f}, FN={cm['FN']:.0f}, TP={cm['TP']:.0f}")
    print(f"  Accuracy: {cm['accuracy']:.3f}")
    
    # Check vs server
    if cm['TN'] == 352 and cm['FP'] == 90:
        print("\n✓✓✓ MATCHES SERVER OUTPUT!")
    else:
        print(f"\n⚠ Values don't match server (expected TN=352, FP=90)")
else:
    print("\n✗ No confusion matrix values")

print("\n" + "="*80)
print("TEST COMPLETE")
print("="*80)
