#!/usr/bin/env python3
"""
SAFE version - Tests fixes with simpler models to avoid hanging
"""

import pyoccam
import time

print("=" * 70)
print("PYOCCAM FIXES TEST (SAFE VERSION)")
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

# ========== TEST 2: SAFE Model Switching ==========
print("=" * 70)
print("TEST 2: Model Switching (SAFE - using only 2-variable models)")
print("=" * 70)

# Use ONLY simple 2-variable models to avoid IPF convergence issues
test_models = [
    "IV:ApZ",   # 2 variables - APOE + CaseControl
    "IV:SxZ",   # 2 variables - Gender + CaseControl  
    "IV:EdZ",   # 2 variables - Education + CaseControl
]

print(f"Testing switching between {len(test_models)} SIMPLE models...")
print("(Using only 2-variable models to avoid hanging)")
start = time.time()
timeout = 30  # seconds

success_count = 0
try:
    for i, model in enumerate(test_models):
        elapsed = time.time() - start
        if elapsed > timeout:
            print(f"\n⚠️  Timeout after {elapsed:.1f}s on model {i+1}/{len(test_models)}")
            print(f"   Successfully tested {success_count}/{len(test_models)} models")
            break
        
        # Test WITHOUT confusion matrix first (faster)
        print(f"\n  Model {i+1}/{len(test_models)}: {model}")
        print(f"    → Testing fit report without CM...", end='', flush=True)
        
        try:
            report = manager.generate_fit_report(model, "")
            print(f" OK ({len(report)} chars)")
        except Exception as e:
            print(f" ERROR: {e}")
            continue
        
        # Now test WITH confusion matrix
        print(f"    → Testing with confusion matrix...", end='', flush=True)
        try:
            cm = manager.get_confusion_matrix(model, "0")
            if 'accuracy' in cm and cm['accuracy'] > 0:
                print(f" OK (acc={cm['accuracy']:.3f})")
                success_count += 1
            else:
                print(f" No valid CM")
        except Exception as e:
            print(f" ERROR: {e}")
            continue
    
    elapsed = time.time() - start
    if success_count == len(test_models):
        print(f"\n✅ TEST 2 PASSED: All {success_count} models tested successfully ({elapsed:.2f}s)")
        print("   Model switching works correctly with simple models")
    elif success_count > 0:
        print(f"\n⚠️  TEST 2 PARTIAL: {success_count}/{len(test_models)} models worked ({elapsed:.2f}s)")
    else:
        print(f"\n❌ TEST 2 FAILED: No models could be tested")
    
except KeyboardInterrupt:
    print(f"\n\n⚠️  Interrupted by user")
    print(f"   Successfully tested {success_count}/{len(test_models)} models")
except Exception as e:
    print(f"\n❌ TEST 2 FAILED: Exception: {e}")

print()

# ========== SUMMARY ==========
print("=" * 70)
print("SUMMARY")
print("=" * 70)
print("TEST 1: Confusion Matrix Keys")
print("TEST 2: Model Switching (using simple 2-variable models)")
print()
print("If TEST 2 still hangs:")
print("  - The issue is in generate_fit_report or get_confusion_matrix")
print("  - Run test_hang_diagnostic.py to find exact hang location")
print("  - Check if makeFitTable or IPF is causing convergence issues")
print("=" * 70)