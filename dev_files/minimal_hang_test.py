#!/usr/bin/env python3
"""
Minimal test to isolate the hang
Tests only the specific operations that might hang
"""

import pyoccam
import sys
import time
import threading

def run_with_timer(description, func):
    """Run a function and time it"""
    print(f"\n{description}...", end=" ")
    sys.stdout.flush()
    
    start = time.time()
    result = None
    error = None
    
    try:
        result = func()
        elapsed = time.time() - start
        print(f"✓ ({elapsed:.2f}s)")
        return result
    except Exception as e:
        elapsed = time.time() - start
        print(f"✗ ({elapsed:.2f}s) - {e}")
        return None

print("="*70)
print("MINIMAL HANG TEST")
print("="*70)

# Initialize
print("\nInitializing...")
manager = pyoccam.VBMManager()
manager.init_from_command_line(["occam", "dementia05.txt"])
print("✓ Initialized")

# Run minimal search
run_with_timer("Running minimal search (1 level, width 3)", 
               lambda: manager.generate_search_report("loopless-up", 1, 3))

# Get best model
best = run_with_timer("Getting best model",
                      lambda: manager.get_best_model_by_information())
print(f"  Best model: {best}")

# Test 1: Simplest model (just IV)
print("\n" + "="*70)
print("TEST 1: Simplest possible model (IV)")
print("="*70)

cm = run_with_timer("  get_confusion_matrix('IV', '0')",
                    lambda: manager.get_confusion_matrix("IV", "0"))
if cm:
    print(f"  Result: TN={cm['tn']:.0f}, FP={cm['fp']:.0f}, Acc={cm['accuracy']:.3f}")

# Test 2: Simple 2-variable model
print("\n" + "="*70)
print("TEST 2: Simple 2-variable model")
print("="*70)

two_var_model = "IV:ApZ"  # Simplest 2-variable model
cm = run_with_timer(f"  get_confusion_matrix('{two_var_model}', '0')",
                    lambda: manager.get_confusion_matrix(two_var_model, "0"))
if cm:
    print(f"  Result: TN={cm['tn']:.0f}, FP={cm['fp']:.0f}, Acc={cm['accuracy']:.3f}")

# Test 3: Best model from search
if best:
    print("\n" + "="*70)
    print(f"TEST 3: Best model from search ({best})")
    print("="*70)
    
    cm = run_with_timer(f"  get_confusion_matrix('{best}', '0')",
                        lambda: manager.get_confusion_matrix(best, "0"))
    if cm:
        print(f"  Result: TN={cm['tn']:.0f}, FP={cm['fp']:.0f}, Acc={cm['accuracy']:.3f}")

# Test 4: Generate fit report (this might be where it hangs)
print("\n" + "="*70)
print("TEST 4: Generate fit report (NO target state)")
print("="*70)

report = run_with_timer(f"  generate_fit_report('{best}', '')",
                        lambda: manager.generate_fit_report(best, ""))
if report:
    print(f"  Report length: {len(report)} chars")

# Test 5: Generate fit report WITH target state
print("\n" + "="*70)
print("TEST 5: Generate fit report (WITH target state)")
print("="*70)

report = run_with_timer(f"  generate_fit_report('{best}', '0')",
                        lambda: manager.generate_fit_report(best, "0"))
if report:
    print(f"  Report length: {len(report)} chars")
    if "Confusion Matrix" in report:
        print("  ✓ Contains Confusion Matrix section")
        # Count how many times it appears
        count = report.count("Confusion Matrix")
        print(f"  ℹ  'Confusion Matrix' appears {count} time(s)")
        
        # Check for component relations
        if "Component" in report or "Relation" in report:
            print("  ⚠️  Report contains Component Relations")

print("\n" + "="*70)
print("ALL TESTS COMPLETE")
print("="*70)
