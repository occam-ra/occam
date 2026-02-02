#!/usr/bin/env python3
"""
Diagnose where the hang is occurring
"""

import pyoccam
import sys

print("Step 1: Initialize manager...")
sys.stdout.flush()
manager = pyoccam.VBMManager()
manager.init_from_command_line(["occam", "dementia05.txt"])
print("✓ Manager initialized")
sys.stdout.flush()

print("\nStep 2: Run search...")
sys.stdout.flush()
manager.generate_search_report("full-up", 3, 3)
print("✓ Search completed")
sys.stdout.flush()

print("\nStep 3: Get best model...")
sys.stdout.flush()
best = manager.get_best_model_by_information()
print(f"✓ Best model: {best}")
sys.stdout.flush()

print("\nStep 4: Generate fit report WITHOUT target state...")
sys.stdout.flush()
try:
    fit_report = manager.generate_fit_report(best, "")  # Empty string = no target
    print(f"✓ Fit report generated ({len(fit_report)} chars)")
    # Save it
    with open("test_fit_report_no_target.txt", "w") as f:
        f.write(fit_report)
    print("✓ Saved to test_fit_report_no_target.txt")
except Exception as e:
    print(f"✗ Error: {e}")
sys.stdout.flush()

print("\nStep 5: Generate fit report WITH target state '0'...")
sys.stdout.flush()
print("This is where it might hang...")
sys.stdout.flush()

try:
    fit_report = manager.generate_fit_report(best, "0")
    print(f"✓ Fit report generated ({len(fit_report)} chars)")
    # Save it
    with open("test_fit_report_with_target.txt", "w") as f:
        f.write(fit_report)
    print("✓ Saved to test_fit_report_with_target.txt")
except Exception as e:
    print(f"✗ Error: {e}")
sys.stdout.flush()

print("\nStep 6: Call get_confusion_matrix()...")
sys.stdout.flush()
print("This is where your script hangs...")
sys.stdout.flush()

try:
    cm = manager.get_confusion_matrix(best, "0")
    print(f"✓ Confusion matrix returned: {cm}")
except Exception as e:
    print(f"✗ Error: {e}")
sys.stdout.flush()

print("\n✓ All steps completed!")
