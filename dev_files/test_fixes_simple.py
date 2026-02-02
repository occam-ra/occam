#!/usr/bin/env python3
"""
Simple test to verify the two fixes:
1. Confusion matrix returns UPPERCASE keys
2. Model switching doesn't hang
"""

import pyoccam
import time

print("=" * 70)
print("TESTING PYOCCAM FIXES")
print("=" * 70)

# Initialize
manager = pyoccam.VBMManager()
success = manager.init_from_command_line(["occam", "dementia05.txt"])

if not success:
    print("❌ Failed to load data")
    exit(1)

print("✅ Data loaded\n")

# Run a quick search
print("Running quick search...")
manager.generate_search_report("loopless-up", 3, 3)
best = manager.get_best_model_by_bic()
print(f"✅ Best model: {best}\n")

# ========== TEST 1: Check Confusion Matrix Keys ==========
print("=" * 70)
print("TEST 1: Confusion Matrix Key Case")
print("=" * 70)

cm = manager.get_confusion_matrix(best, "0")
keys = list(cm.keys())
print(f"Keys returned: {keys}")

# Check if uppercase keys are present
has_uppercase = all(key in keys for key in ['TP', 'TN', 'FP', 'FN'])
has_lowercase = all(key in keys for key in ['tp', 'tn', 'fp', 'fn'])

if has_uppercase:
    print("✅ TEST 1 PASSED: Returns UPPERCASE keys")
    print(f"   TP={cm['TP']:.0f}, TN={cm['TN']:.0f}, FP={cm['FP']:.0f}, FN={cm['FN']:.0f}")
    print(f"   Accuracy: {cm['accuracy']:.3f}")
elif has_lowercase:
    print("❌ TEST 1 FAILED: Still returning lowercase keys")
    print("   Please apply the fixed get_confusion_matrix code")
else:
    print("❌ TEST 1 FAILED: Unexpected key format")

print()

# ========== TEST 2: Rapid Model Switching ==========
print("=" * 70)
print("TEST 2: Model Switching (Heap Corruption Test)")
print("=" * 70)

# List of models to test switching between
test_models = ["IV:ApZ", "IV:ApZ:CZ", "IV:ApZ:EdZ", "IV:CZ"]

print(f"Testing rapid switching between {len(test_models)} models...")
start = time.time()
timeout = 10  # seconds

try:
    for i, model in enumerate(test_models):
        elapsed = time.time() - start
        if elapsed > timeout:
            print(f"❌ TEST 2 FAILED: Timeout after {elapsed:.1f}s")
            print("   Still hanging on model switching")
            break
        
        # Try to get confusion matrix (this triggers model creation)
        cm = manager.get_confusion_matrix(model, "0")
        
        # Check if we got valid results
        if 'accuracy' in cm and cm['accuracy'] > 0:
            print(f"  ✓ Model {i+1}/{len(test_models)}: {model} (acc={cm['accuracy']:.3f})")
        else:
            print(f"  - Model {i+1}/{len(test_models)}: {model} (no valid CM)")
    
    elapsed = time.time() - start
    if elapsed <= timeout:
        print(f"\n✅ TEST 2 PASSED: No hanging ({elapsed:.2f}s)")
        print("   Model switching works correctly")
    
except Exception as e:
    print(f"❌ TEST 2 FAILED: Exception: {e}")

print()

# ========== SUMMARY ==========
print("=" * 70)
print("SUMMARY")
print("=" * 70)
print("If both tests passed, the fixes are working correctly!")
print("If TEST 1 failed: Apply the fixed get_confusion_matrix code")
print("If TEST 2 failed: Apply the fixed generate_fit_report code")
print("=" * 70)