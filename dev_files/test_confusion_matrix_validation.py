#!/usr/bin/env python3
"""
Confusion Matrix Validation Test
Compares PyOccam results against server PDF gold standard
"""

import pyoccam
import sys

def print_header(text, width=80):
    print("\n" + "=" * width)
    print(text.center(width))
    print("=" * width)

def compare_confusion_matrix(cm, expected, model_name, tolerance=1.0):
    """Compare extracted CM with expected values from server"""
    print(f"\n{'='*60}")
    print(f"Model: {model_name}")
    print(f"{'='*60}")
    
    # Print both side by side
    print("\n{:<30} {:<15} {:<15}".format("Metric", "PyOccam", "Server PDF"))
    print("-" * 60)
    
    passed = True
    
    # Check raw values
    for key in ['TN', 'FP', 'FN', 'TP']:
        pyoccam_val = cm.get(key, -999)
        server_val = expected.get(key, -999)
        match = abs(pyoccam_val - server_val) < tolerance
        
        status = "✓" if match else "✗"
        print(f"{key:<30} {pyoccam_val:>15.1f} {server_val:>15.1f} {status}")
        
        if not match:
            passed = False
            print(f"  ⚠️ MISMATCH: Difference = {pyoccam_val - server_val:.1f}")
    
    # Check calculated metrics
    print("\nDerived Metrics:")
    print("-" * 60)
    
    metrics = {
        'accuracy': '(TP+TN)/Total',
        'sensitivity': 'TP/(TP+FN)',
        'specificity': 'TN/(TN+FP)',
        'precision': 'TP/(TP+FP)',
        'f1_score': '2*P*R/(P+R)'
    }
    
    for metric, formula in metrics.items():
        if metric in cm and metric in expected:
            pyoccam_val = cm[metric]
            server_val = expected[metric]
            match = abs(pyoccam_val - server_val) < 0.01  # 1% tolerance for ratios
            
            status = "✓" if match else "✗"
            print(f"{metric:<30} {pyoccam_val:>15.3f} {server_val:>15.3f} {status}")
            
            if not match:
                passed = False
                print(f"  ⚠️ MISMATCH: Difference = {pyoccam_val - server_val:.3f}")
    
    # Print the actual confusion matrix layout
    print("\nConfusion Matrix Layout:")
    print("-" * 40)
    print(f"              Predicted")
    print(f"              Z=0     Z≠0")
    print(f"Actual Z=0    {cm.get('TN', 0):>3.0f}     {cm.get('FP', 0):>3.0f}")
    print(f"       Z≠0    {cm.get('FN', 0):>3.0f}     {cm.get('TP', 0):>3.0f}")
    
    return passed

def main():
    print_header("CONFUSION MATRIX VALIDATION TEST")
    print("Comparing PyOccam against dementia05_server_fit_output.pdf")
    
    # Initialize
    manager = pyoccam.VBMManager()
    if not manager.init_from_command_line(["occam", "dementia05.txt"]):
        print("✗ Failed to load dementia05.txt")
        sys.exit(1)
    print("✓ Data loaded: dementia05.txt")
    
    # ==================================================================
    # TEST CASES FROM SERVER PDF
    # These exact values come from dementia05_server_fit_output.pdf
    # ==================================================================
    
    test_cases = [
        {
            # Main model from PDF
            'model': 'IV:ApSxZ:EdZ:AgZ:CZ:KZ',
            'expected': {
                # From server PDF - main model confusion matrix
                'TN': 170,   # True Negatives
                'FP': 51,    # False Positives
                'FN': 69,    # False Negatives
                'TP': 134,   # True Positives
                'accuracy': 0.717,      # %correct
                'sensitivity': 0.660,   # TP/AP = 134/203
                'specificity': 0.769,   # TN/AN = 170/221
                'precision': 0.724,     # TP/RP = 134/185
                'npv': 0.711,          # TN/RN = 170/239
                'f1_score': 0.691      # From PDF
            }
        },
        {
            # Component relation ApSxZ
            'model': 'IV:ApSxZ',
            'expected': {
                # From server PDF - ApSxZ component
                'TN': 179,   
                'FP': 42,    
                'FN': 98,    
                'TP': 105,   
                'accuracy': 0.670,      
                'sensitivity': 0.517,   # 105/203
                'specificity': 0.810,   # 179/221
                'precision': 0.714,     # 105/147
                'npv': 0.646,          # 179/277
                'f1_score': 0.600      
            }
        },
        {
            # Component relation EdZ
            'model': 'IV:EdZ',
            'expected': {
                # From server PDF - EdZ component
                'TN': 216,   
                'FP': 5,     
                'FN': 180,   
                'TP': 23,    
                'accuracy': 0.564,      
                'sensitivity': 0.113,   # 23/203
                'specificity': 0.977,   # 216/221
                'precision': 0.821,     # 23/28
                'npv': 0.545,          # 216/396
                'f1_score': 0.199      
            }
        },
        {
            # Component relation AgZ
            'model': 'IV:AgZ',
            'expected': {
                # From server PDF - AgZ component
                'TN': 191,   
                'FP': 30,    
                'FN': 157,   
                'TP': 46,    
                'accuracy': 0.559,      
                'sensitivity': 0.227,   # 46/203
                'specificity': 0.864,   # 191/221
                'precision': 0.605,     # 46/76
                'npv': 0.549,          # 191/348
                'f1_score': 0.330      
            }
        },
        {
            # Component relation CZ
            'model': 'IV:CZ',
            'expected': {
                # From server PDF - CZ component
                'TN': 111,   
                'FP': 110,   
                'FN': 68,    
                'TP': 135,   
                'accuracy': 0.580,      
                'sensitivity': 0.665,   # 135/203
                'specificity': 0.502,   # 111/221
                'precision': 0.551,     # 135/245
                'npv': 0.620,          # 111/179
                'f1_score': 0.603      
            }
        },
        {
            # Component relation KZ
            'model': 'IV:KZ',
            'expected': {
                # From server PDF - KZ component
                'TN': 69,    
                'FP': 152,   
                'FN': 32,    
                'TP': 171,   
                'accuracy': 0.566,      
                'sensitivity': 0.842,   # 171/203
                'specificity': 0.312,   # 69/221
                'precision': 0.529,     # 171/323
                'npv': 0.683,          # 69/101
                'f1_score': 0.650      # Calculated from precision and sensitivity
            }
        }
    ]
    
    # Run tests
    all_passed = True
    passed_count = 0
    failed_count = 0
    
    print("\n" + "=" * 80)
    print("RUNNING VALIDATION TESTS")
    print("=" * 80)
    
    for test_case in test_cases:
        model_name = test_case['model']
        expected = test_case['expected']
        
        print(f"\nTesting model: {model_name}")
        print("-" * 40)
        
        try:
            # Get confusion matrix from PyOccam
            cm = manager.get_confusion_matrix(model_name, "0")
            
            if "error" in cm:
                print(f"✗ Error: {cm['error']}")
                failed_count += 1
                all_passed = False
                continue
            
            if "warning" in cm:
                print(f"⚠️ Warning: {cm['warning']}")
            
            # Compare with expected
            passed = compare_confusion_matrix(cm, expected, model_name)
            
            if passed:
                print(f"\n✓ {model_name} PASSED")
                passed_count += 1
            else:
                print(f"\n✗ {model_name} FAILED")
                failed_count += 1
                all_passed = False
                
        except Exception as e:
            print(f"✗ Exception: {e}")
            failed_count += 1
            all_passed = False
    
    # ==================================================================
    # ADDITIONAL TESTS
    # ==================================================================
    
    print("\n" + "=" * 80)
    print("ADDITIONAL VALIDATION TESTS")
    print("=" * 80)
    
    # Test 1: Independence model (should have worst performance)
    print("\n1. Testing Independence Model (IV:Z):")
    cm_independence = manager.get_confusion_matrix("IV:Z", "0")
    print(f"   Accuracy: {cm_independence.get('accuracy', 0):.3f}")
    print("   Note: Independence model should have lower accuracy")
    
    # Test 2: Check that more complex models generally improve
    print("\n2. Testing Model Complexity vs Performance:")
    complexity_test = [
        "IV:Z",           # Independence
        "IV:ApZ",         # Single predictor
        "IV:ApZ:EdZ",     # Two predictors
        "IV:ApZ:EdZ:CZ"   # Three predictors
    ]
    
    for model in complexity_test:
        cm = manager.get_confusion_matrix(model, "0")
        acc = cm.get('accuracy', 0)
        print(f"   {model:<20} Accuracy: {acc:.3f}")
    
    # Test 3: Verify sum constraints
    print("\n3. Verifying Confusion Matrix Constraints:")
    cm = manager.get_confusion_matrix("IV:ApZ", "0")
    
    total = cm.get('TN', 0) + cm.get('FP', 0) + cm.get('FN', 0) + cm.get('TP', 0)
    print(f"   Total samples: {total:.0f} (should be 424)")
    
    actual_negative = cm.get('TN', 0) + cm.get('FP', 0)
    actual_positive = cm.get('FN', 0) + cm.get('TP', 0)
    print(f"   Actual negative (AN): {actual_negative:.0f} (should be 221)")
    print(f"   Actual positive (AP): {actual_positive:.0f} (should be 203)")
    
    predicted_negative = cm.get('TN', 0) + cm.get('FN', 0)
    predicted_positive = cm.get('FP', 0) + cm.get('TP', 0)
    print(f"   Predicted negative (RN): {predicted_negative:.0f}")
    print(f"   Predicted positive (RP): {predicted_positive:.0f}")
    
    # ==================================================================
    # FINAL SUMMARY
    # ==================================================================
    
    print("\n" + "=" * 80)
    print("VALIDATION SUMMARY")
    print("=" * 80)
    
    print(f"\nTests Passed: {passed_count}")
    print(f"Tests Failed: {failed_count}")
    
    if all_passed:
        print("\n✅ ALL VALIDATION TESTS PASSED!")
        print("The confusion matrix extraction is working correctly.")
    else:
        print("\n⚠️ SOME TESTS FAILED!")
        print("The confusion matrix extraction may have issues.")
        print("\nPossible causes:")
        print("1. The server PDF may show different models than tested")
        print("2. The target state encoding may be different")
        print("3. The confusion matrix orientation may be swapped")
        print("\nRecommendations:")
        print("1. Check exact model names in server PDF")
        print("2. Verify target state (0 vs 1 vs other)")
        print("3. Check if TN/TP positions are swapped")
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())
