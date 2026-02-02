#!/usr/bin/env python3
"""
Diagnostic script to find exactly where model switching hangs
"""

import pyoccam
import sys
import time

print("=" * 70)
print("HANG DIAGNOSTIC - Model Switching")
print("=" * 70)

# Initialize
print("\n1. Initializing manager...")
sys.stdout.flush()
manager = pyoccam.VBMManager()
success = manager.init_from_command_line(["occam", "dementia05.txt"])
print("   ✓ Manager initialized")
sys.stdout.flush()

# Run search
print("\n2. Running search...")
sys.stdout.flush()
manager.generate_search_report("loopless-up", 3, 3)
print("   ✓ Search complete")
sys.stdout.flush()

# Test models in order of complexity (simplest to most complex)
test_models = [
    ("IV", 0),           # Independence - guarded, should skip
    ("IV:ApZ", 2),       # 2 variables
    ("IV:ApZ:CZ", 3),    # 3 variables
    ("IV:ApZ:EdZ", 3),   # 3 variables
]

print("\n3. Testing model switching...")
sys.stdout.flush()

for model_name, var_count in test_models:
    print(f"\n   Testing: {model_name} ({var_count} vars)")
    sys.stdout.flush()
    
    # Test step by step
    try:
        # Step A: Try to get fit report WITHOUT confusion matrix first
        print(f"      A. generate_fit_report('{model_name}', '') - NO target...")
        sys.stdout.flush()
        start = time.time()
        
        report = manager.generate_fit_report(model_name, "")
        
        elapsed = time.time() - start
        print(f"         ✓ Success ({elapsed:.2f}s, {len(report)} chars)")
        sys.stdout.flush()
        
    except Exception as e:
        print(f"         ✗ Exception: {e}")
        sys.stdout.flush()
        break
    
    # Skip confusion matrix for IV model
    if model_name == "IV":
        print(f"      B. Skipping confusion matrix (IV model)")
        sys.stdout.flush()
        continue
    
    try:
        # Step B: Now try WITH confusion matrix
        print(f"      B. generate_fit_report('{model_name}', '0') - WITH target...")
        sys.stdout.flush()
        start = time.time()
        
        report = manager.generate_fit_report(model_name, "0")
        
        elapsed = time.time() - start
        print(f"         ✓ Success ({elapsed:.2f}s, {len(report)} chars)")
        sys.stdout.flush()
        
    except Exception as e:
        print(f"         ✗ Exception: {e}")
        sys.stdout.flush()
        break
    
    try:
        # Step C: Try get_confusion_matrix (calls generate_fit_report internally)
        print(f"      C. get_confusion_matrix('{model_name}', '0')...")
        sys.stdout.flush()
        start = time.time()
        
        cm = manager.get_confusion_matrix(model_name, "0")
        
        elapsed = time.time() - start
        if 'accuracy' in cm:
            print(f"         ✓ Success ({elapsed:.2f}s, acc={cm.get('accuracy', 0):.3f})")
        else:
            print(f"         ✓ Returned ({elapsed:.2f}s) but no accuracy")
        sys.stdout.flush()
        
    except Exception as e:
        print(f"         ✗ Exception: {e}")
        sys.stdout.flush()
        break

print("\n" + "=" * 70)
print("DIAGNOSTIC COMPLETE")
print("If it hung, note which model and which step (A, B, or C)")
print("=" * 70)