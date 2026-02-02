#!/usr/bin/env python3
"""
Simple test script for OCCAM functionality
Run this to verify everything works before using notebooks
"""

import pyoccam2 as pyoccam
import sys
import time

print("="*60)
print("OCCAM SIMPLE TEST SCRIPT")
print("="*60)

# Configuration
DATA_FILE = "dementia05.txt"
SEARCH_LEVELS = 3
SEARCH_WIDTH = 3
TARGET_STATE = "0"

# Test 1: Initialize
print("\n1. INITIALIZING...")
manager = pyoccam.VBMManager()
success = manager.init_from_command_line(["occam", DATA_FILE])
if not success:
    print("ERROR: Could not load data file")
    sys.exit(1)
print(f"✓ Data loaded: {DATA_FILE}")
print(f"  Sample size: {manager.get_sample_size()}")
vars = manager.get_variable_list()
print(f"  Variables: {len(vars)} total")
print(f"  DV: {vars[-1]}")

# Test 2: Configuration
print("\n2. CONFIGURING...")
manager.set_report_separator(pyoccam.SPACESEP)
manager.set_ref_model("bottom")
manager.set_fit_classifier_target(TARGET_STATE)
print("✓ Configuration complete")

# Test 3: Search
print("\n3. SEARCHING...")
print(f"  Type: loopless-up")
print(f"  Levels: {SEARCH_LEVELS}")
print(f"  Width: {SEARCH_WIDTH}")
print("  Running search...")

start = time.time()
search_report = manager.generate_search_report(
    search_type="loopless-up",
    levels=SEARCH_LEVELS,
    width=SEARCH_WIDTH,
    include_test_data=False
)
elapsed = time.time() - start

print(f"✓ Search completed in {elapsed:.2f}s")
print(f"  Report length: {len(search_report)} characters")

# Test 4: Get best models
print("\n4. BEST MODELS...")
best_bic = manager.get_best_model_by_bic()
best_aic = manager.get_best_model_by_aic()
best_info = manager.get_best_model_by_information()

print(f"  BIC: {best_bic}")
print(f"  AIC: {best_aic}")
print(f"  Info: {best_info}")

# Test 5: Try fit report
print("\n5. FIT REPORT TEST...")
if best_bic:
    print(f"  Model to fit: {best_bic}")
    print(f"  Target state: {TARGET_STATE}")
    
    # Try the simplest approach first
    print("  Attempt 1: Fit with target state directly...")
    try:
        fit_report = manager.generate_fit_report(best_bic, TARGET_STATE)
        if fit_report:
            print(f"  ✓ SUCCESS! Report generated ({len(fit_report)} chars)")
            
            # Check contents
            if "Confusion Matrix" in fit_report:
                print("  ✓ Contains confusion matrix")
            if "Conditional" in fit_report:
                print("  ✓ Contains conditional tables")
            if "Residuals" in fit_report:
                print("  ✓ Contains residuals")
                
            # Save it
            with open("test_fit_output.txt", "w") as f:
                f.write(fit_report)
            print("  ✓ Saved to test_fit_output.txt")
        else:
            print("  ✗ Report is empty/None")
    except Exception as e:
        print(f"  ✗ ERROR: {e}")
        
    # If that failed, try without confusion matrix
    if not fit_report:
        print("\n  Attempt 2: Fit without confusion matrix...")
        try:
            fit_report = manager.generate_fit_report(best_bic, "")
            if fit_report:
                print(f"  ✓ SUCCESS! Report generated ({len(fit_report)} chars)")
            else:
                print("  ✗ Report is empty/None")
        except Exception as e:
            print(f"  ✗ ERROR: {e}")
else:
    print("  No best model found to test")

# Test 6: Try simplest possible model
print("\n6. SIMPLE MODEL TEST...")
print("  Testing model: IV:Z")
try:
    print("  Without confusion matrix...")
    simple_report = manager.generate_fit_report("IV:Z", "")
    if simple_report:
        print(f"  ✓ Works! ({len(simple_report)} chars)")
    else:
        print("  ✗ Empty report")
except Exception as e:
    print(f"  ✗ Error: {e}")

try:
    print("  With confusion matrix...")
    simple_report = manager.generate_fit_report("IV:Z", TARGET_STATE)
    if simple_report:
        print(f"  ✓ Works! ({len(simple_report)} chars)")
    else:
        print("  ✗ Empty report")
except Exception as e:
    print(f"  ✗ Error: {e}")

print("\n" + "="*60)
print("TEST COMPLETE")
print("="*60)
print("\nSummary:")
print(f"  ✓ Data loading works")
print(f"  ✓ Search works") 
print(f"  ✓ Best model selection works")
if fit_report:
    print(f"  ✓ Fit reports work")
else:
    print(f"  ✗ Fit reports have issues")
print("\nCheck test_fit_output.txt for the fit report (if generated)")
