
#!/usr/bin/env python
"""
Diagnostic to find exactly where the hang occurs
"""

import pyoccam
import sys
import time

def test_hang_location():
    print("=" * 70)
    print("HANG LOCATION DIAGNOSTIC")
    print("=" * 70)
    print()
    
    manager = pyoccam.VBMManager()
    if not manager.init_from_command_line(["occam", "dementia05.txt"]):
        print("ERROR: Failed to load data")
        return 1
    
    print("✓ Data loaded")
    print()
    
    # Test creating models WITHOUT fit tables
    print("=" * 70)
    print("TEST 1: Create models WITHOUT fit tables (makeFitTable=False)")
    print("=" * 70)
    
    test_models = ["IV:ApZ", "IV:ApZ:EdZ", "IV:ApZ:EdZ:CZ"]
    
    for model_name in test_models:
        print(f"\nCreating {model_name} without fit table...")
        start = time.time()
        
        # This should be fast - just creates the model structure
        py_model = manager.make_model(model_name, make_fit_table=False)
        
        elapsed = time.time() - start
        print(f"  ✓ Created in {elapsed:.3f}s - name: {py_model.name}")
    
    print()
    print("=" * 70)
    print("TEST 2: Create models WITH fit tables (makeFitTable=True)")
    print("=" * 70)
    print("This is where the hang might occur due to IPF not converging!")
    print()
    
    for model_name in test_models:
        print(f"\nCreating {model_name} WITH fit table...")
        start = time.time()
        
        try:
            # This is the slow/hanging part - IPF for complex models
            py_model = manager.make_model(model_name, make_fit_table=True)
            
            elapsed = time.time() - start
            
            if elapsed > 5:
                print(f"  ⚠ SLOW: Took {elapsed:.3f}s (might hang on more complex models)")
            else:
                print(f"  ✓ Created in {elapsed:.3f}s")
                
        except Exception as e:
            print(f"  ✗ EXCEPTION: {e}")
            return 1
    
    print()
    print("=" * 70)
    print("If you got here without hanging, the issue is in print/report generation")
    print("If it hung on TEST 2, the issue is in IPF/fit table creation")
    print("=" * 70)
    
    return 0

if __name__ == "__main__":
    print("\n⚠ WARNING: This test might hang! Be ready to Ctrl+C")
    print("If it hangs, note which test and model it hung on.")
    print()
    input("Press Enter to continue...")
    print()
    
    sys.exit(test_hang_location())
