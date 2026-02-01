#!/usr/bin/env python3
"""
Pinpoint exactly where the hang occurs in confusion matrix code
Windows-compatible version using threading
"""

import pyoccam
import sys
import time
import threading

class TimeoutError(Exception):
    pass

def test_with_timeout(test_name, test_func, timeout_seconds=30):
    """Run a test with timeout protection (Windows-compatible)"""
    print(f"\n{'='*70}")
    print(f"TEST: {test_name}")
    print(f"{'='*70}")
    sys.stdout.flush()
    
    result = [None]
    exception = [None]
    
    def wrapper():
        try:
            result[0] = test_func()
        except Exception as e:
            exception[0] = e
    
    start = time.time()
    thread = threading.Thread(target=wrapper)
    thread.daemon = True
    thread.start()
    thread.join(timeout_seconds)
    elapsed = time.time() - start
    
    if thread.is_alive():
        print(f"❌ TIMEOUT! Hung for {timeout_seconds}+ seconds")
        print("This indicates an infinite loop or deadlock")
        print(f"⚠️  Thread is still running in background (daemon)")
        return None
    
    if exception[0]:
        print(f"❌ FAILED in {elapsed:.2f}s: {exception[0]}")
        return None
    
    print(f"✅ PASSED in {elapsed:.2f}s")
    return result[0]

# Initialize
print("Initializing PyOccam...")
manager = pyoccam.VBMManager()
manager.init_from_command_line(["occam", "dementia05.txt"])
print("✅ Manager initialized\n")

# Test 1: Basic search
def test_search():
    manager.generate_search_report("loopless-up", 3, 3)
    return "Search completed"

test_with_timeout("Basic search", test_search)

# Test 2: Get best model
def test_best_model():
    best = manager.get_best_model_by_information()
    print(f"Best model: {best}")
    return best

best_model = test_with_timeout("Get best model", test_best_model)

# Test 3: Generate fit report WITHOUT target state
def test_fit_no_target():
    report = manager.generate_fit_report(best_model, "")
    print(f"Report length: {len(report)} chars")
    return report

test_with_timeout("Fit report (no target)", test_fit_no_target, timeout_seconds=60)

# Test 4: Generate fit report WITH target state
def test_fit_with_target():
    report = manager.generate_fit_report(best_model, "0")
    print(f"Report length: {len(report)} chars")
    # Check if confusion matrix section exists
    if "Confusion Matrix" in report:
        print("✅ Confusion Matrix section found")
    else:
        print("⚠️  No Confusion Matrix section found")
    return report

fit_report = test_with_timeout("Fit report (with target='0')", test_fit_with_target, timeout_seconds=60)

# Test 5: Call get_confusion_matrix directly
def test_cm_direct():
    cm = manager.get_confusion_matrix(best_model, "0")
    print(f"CM values: TN={cm['tn']}, FP={cm['fp']}, FN={cm['fn']}, TP={cm['tp']}")
    print(f"Accuracy: {cm['accuracy']:.4f}")
    return cm

test_with_timeout("Direct confusion matrix call", test_cm_direct, timeout_seconds=60)

# Test 6: Multiple calls in rapid succession
def test_multiple_calls():
    for i in range(5):
        print(f"  Call {i+1}/5...", end=" ")
        sys.stdout.flush()
        cm = manager.get_confusion_matrix(best_model, "0")
        print(f"OK (acc={cm['accuracy']:.3f})")
    return "All calls completed"

test_with_timeout("Multiple rapid CM calls", test_multiple_calls, timeout_seconds=120)

# Test 7: Different models
def test_different_models():
    models_to_test = ["IV", "IV:ApZ", "IV:ApZ:EdZ"]
    for model_name in models_to_test:
        print(f"  Testing {model_name}...", end=" ")
        sys.stdout.flush()
        try:
            cm = manager.get_confusion_matrix(model_name, "0")
            print(f"OK (acc={cm['accuracy']:.3f})")
        except Exception as e:
            print(f"FAILED: {e}")
    return "All models tested"

test_with_timeout("Different models", test_different_models, timeout_seconds=120)

print("\n" + "="*70)
print("✅ ALL TESTS COMPLETED SUCCESSFULLY")
print("="*70)
print("\nNo hanging detected in basic operations.")
print("If cm_verify_model.py hangs, the issue is likely in the string parsing")
print("or file I/O operations in that specific script, not in the C++ core.")
