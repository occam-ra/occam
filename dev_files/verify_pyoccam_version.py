#!/usr/bin/env python3
"""
Verify which version of pyoccam is loaded and if debug output works
"""
import sys
import pyoccam

print("Python executable:", sys.executable)
print("PyOccam version:", pyoccam.__version__)
print("PyOccam file location:", pyoccam.__file__)
print()

# Check if get_confusion_matrix method exists and what it looks like
if hasattr(pyoccam.VBMManager, 'get_confusion_matrix'):
    print("✓ get_confusion_matrix method exists")
    method = getattr(pyoccam.VBMManager, 'get_confusion_matrix')
    print(f"  Method: {method}")
else:
    print("✗ get_confusion_matrix method NOT FOUND")
    sys.exit(1)

print()
print("=" * 70)
print("TESTING DEBUG OUTPUT")
print("=" * 70)
print()

# Try to call it and see if we get ANY debug output
manager = pyoccam.VBMManager()
if not manager.init_from_command_line(["occam", "dementia05.txt"]):
    print("✗ Failed to load data")
    sys.exit(1)

print("Data loaded. Now calling get_confusion_matrix...")
print()
print("WATCH FOR C++ DEBUG OUTPUT BELOW:")
print("-" * 70)

# Force flush before C++ code runs
sys.stdout.flush()
sys.stderr.flush()

cm = manager.get_confusion_matrix("IV:Ap:Z", "0")

# Force flush after
sys.stdout.flush()
sys.stderr.flush()

print("-" * 70)
print()
print("If you saw lines like:")
print("  '=== GET_CONFUSION_MATRIX CALLED ==='")
print("  '=== PYTHON WRAPPER: About to call printConditional_DV ==='")
print("  '=== STORED in Manager ==='")
print("Then the NEW compiled version is loaded.")
print()
print("If you saw NOTHING, then the OLD version is still loaded!")
print()
print(f"Result: TN={cm.get('TN', 'missing')}")
