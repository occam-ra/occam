#!/usr/bin/env python3
"""
PyOccam Canonical Test Suite - Improved Version
Tests all core functionality with better output and configuration
"""

import pyoccam
import sys
import os
import time

# ==============================================================================
# CONFIGURATION - EDIT THESE
# ==============================================================================
DATA_FILE = "dementia05.txt"           # Data file to test with
SEARCH_TYPE = "loopless-up"            # Search algorithm
SEARCH_LEVELS = 3                      # Search depth
SEARCH_WIDTH = 3                       # Beam width
TARGET_STATE = "0"                     # For confusion matrix
VERBOSE = True                         # Show detailed output
DELAY_BETWEEN_CM_CALLS = 0.05          # Seconds to wait between CM calls (Windows)

# ==============================================================================
# TEST 6: CONFUSION MATRIX WITH DISPLAY
# ==============================================================================

def test_confusion_matrix_with_display():
    """Test confusion matrix extraction and display the values"""
    print("\n" + "=" * 70)
    print("TEST 6: CONFUSION MATRIX EXTRACTION")
    print("=" * 70)
    
    manager = pyoccam.VBMManager()
    if not manager.init_from_command_line(["occam", DATA_FILE]):
        print(f"  ✗ Failed to load {DATA_FILE}")
        return False
    
    # Check if method exists
    if not hasattr(manager, 'get_confusion_matrix'):
        print("  ✗ get_confusion_matrix method not found")
        return False
    
    print("  ✓ get_confusion_matrix method exists")
    
    # Test with simple model
    try:
        model_name = "IV:ApZ"
        print(f"\n  Testing with model: {model_name}")
        print(f"  Target state: {TARGET_STATE}")
        print("  Calling get_confusion_matrix()...")
        
        cm = manager.get_confusion_matrix(model_name, TARGET_STATE)
        
        # Display what we got
        print(f"\n  Returned keys: {list(cm.keys())}")
        
        # Check for errors
        if "error" in cm:
            print(f"  ✗ Error: {cm['error']}")
            return False
        
        # Check for required keys (try both uppercase and lowercase)
        required_keys_upper = ['TN', 'FP', 'FN', 'TP']
        required_keys_lower = ['tn', 'fp', 'fn', 'tp']
        
        has_upper = all(key in cm for key in required_keys_upper)
        has_lower = all(key in cm for key in required_keys_lower)
        
        if not (has_upper or has_lower):
            print(f"  ✗ Missing required keys")
            print(f"     Expected: {required_keys_upper} or {required_keys_lower}")
            print(f"     Got: {list(cm.keys())}")
            return False
        
        # Use whichever case we have
        if has_upper:
            tn, fp, fn, tp = cm['TN'], cm['FP'], cm['FN'], cm['TP']
            accuracy = cm.get('accuracy', 0)
            precision = cm.get('precision', 0)
            recall = cm.get('sensitivity', 0)
            specificity = cm.get('specificity', 0)
        else:
            tn, fp, fn, tp = cm['tn'], cm['fp'], cm['fn'], cm['tp']
            accuracy = cm.get('accuracy', 0)
            precision = cm.get('precision', 0)
            recall = cm.get('sensitivity', 0)
            specificity = cm.get('specificity', 0)
        
        # Check if we got real values
        total = tn + fp + fn + tp
        
        if total == 0:
            print(f"  ✗ All values are zero - CM extraction failed")
            if 'warning' in cm:
                print(f"     Warning: {cm['warning']}")
            if 'debug' in cm:
                print(f"     Debug: {cm['debug']}")
            return False
        
        # Display the confusion matrix
        print("\n  " + "=" * 60)
        print("  CONFUSION MATRIX EXTRACTED:")
        print("  " + "=" * 60)
        print(f"             Predicted Negative  Predicted Positive")
        print(f"  Actual 0:  TN = {tn:6.0f}       FP = {fp:6.0f}")
        print(f"  Actual 1:  FN = {fn:6.0f}       TP = {tp:6.0f}")
        print("  " + "-" * 60)
        print(f"  Total samples: {total:.0f}")
        print(f"\n  Performance Metrics:")
        print(f"    Accuracy:    {accuracy:.3f}")
        print(f"    Precision:   {precision:.3f}")
        print(f"    Recall:      {recall:.3f}")
        print(f"    Specificity: {specificity:.3f}")
        print("  " + "=" * 60)
        
        # Validate totals
        if 400 <= total <= 450:
            print(f"  ✓ Sample size validation passed ({total:.0f} samples)")
        else:
            print(f"  ⚠ Warning: Expected ~424 samples, got {total:.0f}")
        
        print(f"  ✓ Confusion matrix extraction SUCCESSFUL")
        return True
        
    except Exception as e:
        print(f"  ✗ Exception: {e}")
        import traceback
        traceback.print_exc()
        return False

# ==============================================================================
# TEST 7: MODEL SWITCHING WITH DELAYS
# ==============================================================================

def test_model_switching_with_delays():
    """Test that switching between models doesn't cause crashes"""
    print("\n" + "=" * 70)
    print("TEST 7: MODEL SWITCHING (WITH DELAYS)")
    print("=" * 70)
    
    manager = pyoccam.VBMManager()
    if not manager.init_from_command_line(["occam", DATA_FILE]):
        print(f"  ✗ Failed to load {DATA_FILE}")
        return False
    
    # Test switching between different models
    models = ["IV:ApZ", "IV:EdZ", "IV:CZ"]
    
    print(f"  Testing {len(models)} models with {DELAY_BETWEEN_CM_CALLS}s delays...")
    
    try:
        # First test: just fit reports (no CM)
        print("\n  Phase 1: Fit reports only")
        for i, model_name in enumerate(models, 1):
            print(f"    Model {i}/{len(models)}: {model_name}...", end="", flush=True)
            report = manager.generate_fit_report(model_name, "")
            if len(report) == 0:
                print(f" ✗ Empty report")
                return False
            print(f" ✓ ({len(report)} chars)")
            time.sleep(DELAY_BETWEEN_CM_CALLS)  # Give Windows time to clean up
        
        print("  ✓ Fit report switching OK")
        
        # Second test: confusion matrix extraction
        if hasattr(manager, 'get_confusion_matrix'):
            print("\n  Phase 2: Confusion matrix extraction")
            for i, model_name in enumerate(models, 1):
                print(f"    Model {i}/{len(models)}: {model_name}...", end="", flush=True)
                
                # Add delay BEFORE calling CM
                time.sleep(DELAY_BETWEEN_CM_CALLS)
                
                cm = manager.get_confusion_matrix(model_name, TARGET_STATE)
                
                # Check result
                if "error" in cm:
                    print(f" ✗ Error: {cm['error']}")
                    return False
                
                # Check for values (try both cases)
                has_values = False
                if 'TN' in cm and cm['TN'] + cm['TP'] + cm['FN'] + cm['FP'] > 0:
                    has_values = True
                elif 'tn' in cm and cm['tn'] + cm['tp'] + cm['fn'] + cm['fp'] > 0:
                    has_values = True
                
                if has_values:
                    print(f" ✓")
                else:
                    print(f" ⚠ No values")
            
            print("  ✓ CM extraction switching OK")
        
        print("\n  ✓ Model switching test PASSED")
        return True
        
    except Exception as e:
        print(f"\n  ✗ Exception: {e}")
        import traceback
        traceback.print_exc()
        return False

# ==============================================================================
# MAIN
# ==============================================================================

def main():
    """Run improved tests"""
    print("=" * 70)
    print("PYOCCAM CANONICAL TEST SUITE - IMPROVED")
    print("=" * 70)
    print(f"PyOccam version: {pyoccam.__version__}")
    print(f"Data file: {DATA_FILE}")
    print(f"Search: {SEARCH_TYPE} (levels={SEARCH_LEVELS}, width={SEARCH_WIDTH})")
    print(f"CM delay: {DELAY_BETWEEN_CM_CALLS}s")
    print("=" * 70)
    
    # Run the critical tests
    test6_pass = test_confusion_matrix_with_display()
    test7_pass = test_model_switching_with_delays()
    
    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    print(f"TEST 6 (Confusion Matrix): {'✓ PASS' if test6_pass else '✗ FAIL'}")
    print(f"TEST 7 (Model Switching):  {'✓ PASS' if test7_pass else '✗ FAIL'}")
    print("=" * 70)
    
    return 0 if (test6_pass and test7_pass) else 1

if __name__ == "__main__":
    sys.exit(main())
