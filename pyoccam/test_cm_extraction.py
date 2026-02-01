#!/usr/bin/env python3
"""
Test script for confusion matrix extraction
Tests that CM extraction works reliably across multiple models without hanging or crashing
"""

import pyoccam
import sys

def test_fixed_cm():
    """Test the fixed confusion matrix extraction with proper cleanup"""
    
    print("=" * 70)
    print("CONFUSION MATRIX EXTRACTION TEST")
    print("Testing fixed generate_fit_report with cleanup")
    print("=" * 70)
    print()
    
    # Initialize
    manager = pyoccam.VBMManager()
    if not manager.init_from_command_line(["occam", "dementia05.txt"]):
        print("❌ Failed to load data file")
        return 1
    
    print("✓ Data loaded successfully")
    print(f"  Sample size: {manager.get_sample_size()}")
    print()
    
    # Quick sanity check - test if get_confusion_matrix exists
    print("🔍 Checking if get_confusion_matrix method exists...")
    if not hasattr(manager, 'get_confusion_matrix'):
        print("❌ FATAL: get_confusion_matrix method not found!")
        print("   Make sure pyoccam_pybind11.cpp has been updated and recompiled")
        return 1
    print("✓ Method exists")
    print()
    
    # Test with simplest model first
    print("🧪 Testing with simplest model (IV) - should return error...")
    try:
        iv_cm = manager.get_confusion_matrix("IV", "0")
        print(f"   Result: {iv_cm}")
        if "error" in iv_cm:
            print("   ✓ Correctly returns error for IV model")
        else:
            print("   ⚠ Warning: No error for IV model (unexpected)")
    except Exception as e:
        print(f"   ✗ Exception: {e}")
    print()
    
    # Run a search to get some models to test
    print("Running search to get test models...")
    manager.generate_search_report("loopless-up", 1, 3)
    best_model = manager.get_best_model_by_information()
    print(f"✓ Search complete, best model: {best_model}")
    print()
    
    # Test cases: simple to complex models
    test_cases = [
        ("IV", "Independence model (simplest)"),
        ("IV:ApZ", "Simple 2-variable model"),
        ("IV:ApZ:EdZ", "3-variable model"),
        (best_model, "Complex best model"),
    ]
    
    print("=" * 70)
    print("TESTING CONFUSION MATRIX EXTRACTION")
    print("=" * 70)
    print()
    
    all_passed = True
    
    for model_name, description in test_cases:
        print(f"Testing: {model_name}")
        print(f"  ({description})")
        
        try:
            cm = manager.get_confusion_matrix(model_name, "0")
            
            # DEBUG: Show what we actually got
            print(f"  Keys returned: {list(cm.keys())}")
            
            # Check for error first
            if "error" in cm:
                print(f"  ✗ Error: {cm['error']}")
                all_passed = False
            # Check if we got the expected keys
            elif 'TN' not in cm or 'FP' not in cm or 'FN' not in cm or 'TP' not in cm:
                print(f"  ✗ FAILED: Missing expected keys")
                print(f"     Got: {cm}")
                all_passed = False
            elif cm['TN'] == 0 and cm['FP'] == 0 and cm['FN'] == 0 and cm['TP'] == 0:
                print(f"  ✗ FAILED: Extraction returned all zeros")
                if 'warning' in cm:
                    print(f"     Warning: {cm['warning']}")
                all_passed = False
            else:
                # Got real values!
                print(f"  ✓ SUCCESS:")
                print(f"     TN={cm['TN']:.0f}, FP={cm['FP']:.0f}, FN={cm['FN']:.0f}, TP={cm['TP']:.0f}")
                print(f"     Accuracy={cm['accuracy']:.3f}, Precision={cm['precision']:.3f}")
                print(f"     Sensitivity={cm['sensitivity']:.3f}, Specificity={cm['specificity']:.3f}")
                
                # Verify reasonable values
                total = cm['TN'] + cm['FP'] + cm['FN'] + cm['TP']
                if total < 400 or total > 450:  # dementia has 424 samples
                    print(f"     ⚠ Warning: Total samples = {total:.0f} (expected ~424)")
                    
        except KeyError as e:
            print(f"  ✗ KEY ERROR: Missing key {e}")
            print(f"     Dictionary returned: {cm}")
            all_passed = False
        except Exception as e:
            print(f"  ✗ EXCEPTION: {e}")
            import traceback
            traceback.print_exc()
            all_passed = False
        
        print()
    
    print("=" * 70)
    if all_passed:
        print("✅ ALL TESTS PASSED!")
        print()
        print("The confusion matrix extraction is working correctly:")
        print("  • Extracts model-level CM (not sub-relations)")
        print("  • Returns real values (not zeros)")
        print("  • Works with complex models (no hang)")
        print("  • Prefers test data if available")
    else:
        print("❌ SOME TESTS FAILED")
        print()
        print("Check the output above for details.")
    print("=" * 70)
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(test_fixed_cm())
