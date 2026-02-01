#!/usr/bin/env python3
"""
Comprehensive test of confusion matrix with test data
Verifies both training and test CM extraction
"""
import pyoccam

def print_cm_table(cm, data_type="Training"):
    """Pretty print confusion matrix"""
    print(f"\n    📊 {data_type} Confusion Matrix:")
    print(f"    ┌──────────────────────────────┐")
    print(f"    │         Predicted            │")
    print(f"    │     Negative    Positive     │")
    print(f"    ├──────────────────────────────┤")
    print(f"    │ Actual Negative │ TN={cm['TN']:3.0f}  FP={cm['FP']:3.0f} │")
    print(f"    │        Positive │ FN={cm['FN']:3.0f}  TP={cm['TP']:3.0f} │")
    print(f"    └──────────────────────────────┘")
    print(f"\n    📈 {data_type} Metrics:")
    print(f"      Accuracy:    {cm['accuracy']:.3f}")
    print(f"      Sensitivity: {cm['sensitivity']:.3f} (Recall/TPR)")
    print(f"      Specificity: {cm['specificity']:.3f} (TNR)")
    print(f"      Precision:   {cm['precision']:.3f} (PPV)")
    print(f"      F1 Score:    {cm['f1_score']:.3f}")

def test_dataset(data_file, models_to_test, target_state="0"):
    """Test confusion matrix extraction for a dataset"""
    print(f"\n{'='*70}")
    print(f"TESTING: {data_file}")
    print(f"{'='*70}")
    
    # Initialize
    manager = pyoccam.VBMManager()
    if not manager.init_from_command_line(["occam", data_file]):
        print(f"❌ Failed to load {data_file}")
        return False
    
    # Check for test data
    has_test = manager.has_test_data()
    print(f"\n✓ Data loaded: {data_file}")
    print(f"  Test data present: {'YES' if has_test else 'NO'}")
    print(f"  Sample size: {manager.get_sample_size()}")
    
    if has_test:
        print(f"  ⭐ This dataset has train/test split!")
    
    # Test each model
    for model_name in models_to_test:
        print(f"\n{'-'*70}")
        print(f"Model: {model_name}")
        print(f"{'-'*70}")
        
        try:
            cm = manager.get_confusion_matrix(model_name, target_state)
            
            # Check if we got valid data
            if "error" in cm:
                print(f"  ⚠️  Error: {cm['error']}")
                continue
            
            # Check training CM
            total_train = cm['TN'] + cm['FP'] + cm['FN'] + cm['TP']
            if total_train == 0:
                print(f"  ❌ FAILED: Training CM all zeros")
                continue
            
            print(f"  ✓ Training CM extracted successfully")
            print_cm_table(cm, "Training")
            
            # Check for test CM
            if cm.get('has_test_data', False):
                print(f"\n  ⭐ TEST DATA CONFUSION MATRIX AVAILABLE!")
                
                # Extract test CM values
                test_cm = {
                    'TN': cm.get('test_TN', 0),
                    'FP': cm.get('test_FP', 0),
                    'FN': cm.get('test_FN', 0),
                    'TP': cm.get('test_TP', 0),
                }
                
                # Calculate test metrics
                total_test = test_cm['TN'] + test_cm['FP'] + test_cm['FN'] + test_cm['TP']
                
                if total_test > 0:
                    test_cm['accuracy'] = (test_cm['TP'] + test_cm['TN']) / total_test
                    test_cm['sensitivity'] = test_cm['TP'] / (test_cm['TP'] + test_cm['FN']) if (test_cm['TP'] + test_cm['FN']) > 0 else 0
                    test_cm['specificity'] = test_cm['TN'] / (test_cm['TN'] + test_cm['FP']) if (test_cm['TN'] + test_cm['FP']) > 0 else 0
                    test_cm['precision'] = test_cm['TP'] / (test_cm['TP'] + test_cm['FP']) if (test_cm['TP'] + test_cm['FP']) > 0 else 0
                    test_cm['f1_score'] = 2 * (test_cm['precision'] * test_cm['sensitivity']) / (test_cm['precision'] + test_cm['sensitivity']) if (test_cm['precision'] + test_cm['sensitivity']) > 0 else 0
                    
                    print_cm_table(test_cm, "Test")
                    
                    # Compare train vs test
                    print(f"\n  📊 Train vs Test Comparison:")
                    print(f"    Train Accuracy: {cm['accuracy']:.3f}")
                    print(f"    Test Accuracy:  {test_cm['accuracy']:.3f}")
                    diff = test_cm['accuracy'] - cm['accuracy']
                    if abs(diff) < 0.05:
                        print(f"    Difference: {diff:+.3f} (GOOD - similar performance)")
                    elif diff > 0:
                        print(f"    Difference: {diff:+.3f} (WARNING - test better than train!)")
                    else:
                        print(f"    Difference: {diff:+.3f} (overfit warning)")
                else:
                    print(f"  ❌ Test CM flag set but all zeros!")
            else:
                if has_test:
                    print(f"  ⚠️  Dataset has test data but CM doesn't indicate test results")
                else:
                    print(f"  ℹ️  No test data (training only)")
            
        except Exception as e:
            print(f"  ❌ EXCEPTION: {e}")
            import traceback
            traceback.print_exc()
    
    return True

def main():
    print("="*70)
    print("CONFUSION MATRIX TEST DATA VERIFICATION")
    print("="*70)
    
    # Test 1: Dataset WITHOUT test data (dementia05)
    print("\n\n### TEST 1: Dataset without test/train split ###")
    test_dataset(
        "dementia05.txt",
        ["IV:ApZ", "IV:EdZ", "IV:ApZ:EdZ"],
        target_state="0"
    )
    
    # Test 2: Dataset WITH test data (SY_sample if available)
    print("\n\n### TEST 2: Dataset with test/train split ###")
    # Note: This assumes SY data is available with train/test split
    # The actual file might be named differently in your setup
    test_dataset(
        "SY_sample_pts_to_occam3_shuffle_split42_hdr.txt",
        ["IV:SxY", "IV:EdY", "IV:SxEdY"],  # Adjust model names as needed
        target_state="0"
    )
    
    print("\n\n" + "="*70)
    print("VERIFICATION SUMMARY")
    print("="*70)
    print("""
Key Questions Answered:
1. ✓ Does CM extraction work for training data?
2. ? Does has_test_data flag appear in results?
3. ? Are test CM values (test_TN, test_TP, etc.) populated?
4. ? Do test metrics calculate correctly?
5. ? Is there reasonable train/test comparison?

Next Steps:
- If test CM shows all zeros, the C++ computeConfusionMatrix() 
  needs test data support added
- If test CM values look good, we're done!
- Compare against server output CSV files to validate correctness
""")

if __name__ == "__main__":
    main()
