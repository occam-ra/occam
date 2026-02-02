#!/usr/bin/env python3
"""
Minimal test - Creates models WITHOUT fit tables to isolate the hanging issue
"""

import pyoccam
import time

print("=" * 70)
print("MINIMAL TEST - Model Creation WITHOUT Fit Tables")
print("=" * 70)

# Initialize
print("\n1. Initializing...")
manager = pyoccam.VBMManager()
success = manager.init_from_command_line(["occam", "dementia05.txt"])
print("   ✓ Data loaded")

# Run search
print("\n2. Running search...")
manager.generate_search_report("loopless-up", 3, 3)
best = manager.get_best_model_by_bic()
print(f"   ✓ Best model: {best}")

# Test creating models WITHOUT fit tables (second parameter = False)
print("\n3. Testing model creation WITHOUT fit tables...")
test_models = ["IV:ApZ", "IV:SxZ", "IV:EdZ", "IV:ApZ:CZ"]

for model_name in test_models:
    print(f"\n   Model: {model_name}")
    start = time.time()
    
    # Clean up first
    print(f"      → deleteTablesFromCache()...", end='', flush=True)
    manager.deleteTablesFromCache()
    print(" OK")
    
    # Create model WITHOUT fit table (should be fast)
    print(f"      → makeModel('{model_name}', False)...", end='', flush=True)
    model = manager.make_model(model_name, False)
    elapsed = time.time() - start
    
    if model and model.name:
        print(f" OK ({elapsed:.3f}s)")
        print(f"         Model created: {model.name}")
    else:
        print(f" FAILED")

print("\n" + "=" * 70)
print("If this test works but the confusion matrix test hangs,")
print("the issue is in:")
print("  1. makeFitTable (when creating fit tables)")
print("  2. IPF convergence (iterative proportional fitting)")
print("  3. printConditional_DV (printing confusion matrix)")
print("=" * 70)