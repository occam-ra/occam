#!/usr/bin/env python3
"""
Debug exactly where get_confusion_matrix is hanging
"""

import pyoccam
import time

print("Testing get_confusion_matrix with timing...\n")

# Initialize
manager = pyoccam.VBMManager()
manager.init_from_command_line(["occam", "dementia05.txt"])

# Run full-up search
print("Running full-up search...")
manager.generate_search_report("full-up", 7, 3)
best = manager.get_best_model_by_information()
print(f"Best model: {best}\n")

# Test generate_fit_report timing
print("Testing generate_fit_report (should be fast)...")
start = time.time()
fit_report = manager.generate_fit_report(best, "0")
elapsed = time.time() - start
print(f"✓ Generated in {elapsed:.3f}s, length={len(fit_report)} chars\n")

# Save it
with open("debug_fit_report.txt", "w") as f:
    f.write(fit_report)
print("✓ Saved to debug_fit_report.txt\n")

# Now test get_confusion_matrix with timeout
print("Testing get_confusion_matrix (this is where it might hang)...")
print("Press Ctrl+C if it hangs for more than 5 seconds...\n")

start = time.time()
try:
    cm = manager.get_confusion_matrix(best, "0")
    elapsed = time.time() - start
    print(f"✓ Completed in {elapsed:.3f}s")
    print(f"  Result: TN={cm['tn']}, FP={cm['fp']}, FN={cm['fn']}, TP={cm['tp']}")
except KeyboardInterrupt:
    elapsed = time.time() - start
    print(f"\n✗ HUNG after {elapsed:.1f}s - manually interrupted")
    print("\nThis confirms the hang is in the C++ parsing code.")
    print("Check the extractConfusionMatrixFromReport function.")
except Exception as e:
    elapsed = time.time() - start
    print(f"✗ Error after {elapsed:.3f}s: {e}")
