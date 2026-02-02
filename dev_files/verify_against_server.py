#!/usr/bin/env python3
"""
Compare pyoccam confusion matrix results against server output
Uses the CSV files from server runs as gold standard
"""
import pyoccam
import csv

# Expected values from server output files
# From: SY_sample_pts_to_occam3_shuffle_split42_hdr_server_fit.csv
# and dementia05 server outputs
SERVER_EXPECTED = {
    "dementia05": {
        "IV:ApZ": {
            "train": {"TN": 179, "FP": 42, "FN": 98, "TP": 105},
            "test": None  # No test data in dementia05
        },
        "IV:EdZ": {
            "train": {"TN": 221, "FP": 0, "FN": 203, "TP": 0},  # Degenerate predictor
            "test": None
        },
    },
    "SY_sample": {
        # Add expected values from SY server output here
        # Once we run the server version and get the CSV
    }
}

def compare_cm(actual, expected, tolerance=1.0):
    """
    Compare confusion matrix values with tolerance
    tolerance=1.0 allows ±1 difference (for rounding)
    """
    if expected is None:
        return True, "No expected values to compare"
    
    differences = {}
    all_match = True
    
    for key in ['TN', 'FP', 'FN', 'TP']:
        actual_val = actual.get(key, 0)
        expected_val = expected.get(key, 0)
        diff = abs(actual_val - expected_val)
        differences[key] = diff
        
        if diff > tolerance:
            all_match = False
    
    return all_match, differences

def load_server_csv(filename):
    """
    Load confusion matrix from server CSV output
    Returns dict with model -> CM mapping
    """
    # TODO: Parse server CSV files to extract CM values
    # This depends on the actual format of the CSV files
    pass

def test_model_against_server(manager, model_name, target_state, expected, dataset_name):
    """Test a single model and compare to expected values"""
    print(f"\n  Testing: {model_name}")
    print(f"  " + "-"*60)
    
    # Get CM from pyoccam
    cm = manager.get_confusion_matrix(model_name, target_state)
    
    if "error" in cm:
        print(f"    ❌ Error: {cm['error']}")
        return False
    
    # Check training CM
    actual_train = {
        'TN': cm['TN'],
        'FP': cm['FP'],
        'FN': cm['FN'],
        'TP': cm['TP']
    }
    
    print(f"    📊 Training CM:")
    print(f"      Actual:   TN={actual_train['TN']:.0f} FP={actual_train['FP']:.0f} FN={actual_train['FN']:.0f} TP={actual_train['TP']:.0f}")
    
    # Compare to expected
    if expected and expected.get("train"):
        exp_train = expected["train"]
        print(f"      Expected: TN={exp_train['TN']} FP={exp_train['FP']} FN={exp_train['FN']} TP={exp_train['TP']}")
        
        matches, diffs = compare_cm(actual_train, exp_train, tolerance=1.0)
        
        if matches:
            print(f"      ✅ MATCH! (within tolerance)")
        else:
            print(f"      ❌ MISMATCH!")
            print(f"         Differences: {diffs}")
            return False
    else:
        print(f"      ℹ️  No expected values for comparison")
    
    # Check test CM if present
    if cm.get('has_test_data', False):
        actual_test = {
            'TN': cm.get('test_TN', 0),
            'FP': cm.get('test_FP', 0),
            'FN': cm.get('test_FN', 0),
            'TP': cm.get('test_TP', 0)
        }
        
        print(f"    📊 Test CM:")
        print(f"      Actual:   TN={actual_test['TN']:.0f} FP={actual_test['FP']:.0f} FN={actual_test['FN']:.0f} TP={actual_test['TP']:.0f}")
        
        if expected and expected.get("test"):
            exp_test = expected["test"]
            print(f"      Expected: TN={exp_test['TN']} FP={exp_test['FP']} FN={exp_test['FN']} TP={exp_test['TP']}")
            
            matches, diffs = compare_cm(actual_test, exp_test, tolerance=1.0)
            
            if matches:
                print(f"      ✅ MATCH! (within tolerance)")
            else:
                print(f"      ❌ MISMATCH!")
                print(f"         Differences: {diffs}")
                return False
        else:
            print(f"      ℹ️  No expected test values for comparison")
    
    return True

def main():
    print("="*70)
    print("CONFUSION MATRIX VERIFICATION AGAINST SERVER OUTPUT")
    print("="*70)
    
    results = {
        "passed": 0,
        "failed": 0,
        "no_expected": 0
    }
    
    # Test dementia05
    print(f"\n{'='*70}")
    print(f"Dataset: dementia05.txt")
    print(f"{'='*70}")
    
    manager = pyoccam.VBMManager()
    if not manager.init_from_command_line(["occam", "dementia05.txt"]):
        print("❌ Failed to load dementia05.txt")
        return
    
    print(f"✓ Data loaded")
    print(f"  Sample size: {manager.get_sample_size()}")
    print(f"  Has test data: {manager.has_test_data()}")
    
    for model_name, expected in SERVER_EXPECTED["dementia05"].items():
        success = test_model_against_server(
            manager, model_name, "0", expected, "dementia05"
        )
        if success:
            results["passed"] += 1
        else:
            results["failed"] += 1
    
    # Summary
    print(f"\n{'='*70}")
    print(f"SUMMARY")
    print(f"{'='*70}")
    print(f"  ✅ Passed: {results['passed']}")
    print(f"  ❌ Failed: {results['failed']}")
    print(f"  ℹ️  No expected values: {results['no_expected']}")
    
    if results['failed'] == 0:
        print(f"\n🎉 ALL TESTS PASSED!")
        print(f"\nConfusion matrix extraction is working correctly!")
        print(f"Values match server output within tolerance.")
    else:
        print(f"\n⚠️  Some tests failed - review differences above")
    
    print(f"\n{'='*70}")
    print(f"NEXT STEPS:")
    print(f"{'='*70}")
    print("""
1. Run server version with SY_sample data to get expected test CM values
2. Add those expected values to SERVER_EXPECTED dict
3. Verify test CM extraction works correctly
4. Document any differences and explain why (if reasonable)

If training CM matches server output, the core algorithm is correct!
""")

if __name__ == "__main__":
    main()
