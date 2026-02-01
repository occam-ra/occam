#!/usr/bin/env python3
"""
Test script for the new confusion matrix API
Demonstrates the clean, direct API approach instead of text parsing
"""

import pyoccam

def main():
    print("=" * 70)
    print("TESTING NEW CONFUSION MATRIX API")
    print("=" * 70)
    
    # Initialize manager
    manager = pyoccam.VBMManager()
    success = manager.init_from_command_line(["occam", "dementia05.txt"])
    
    if not success:
        print("❌ Failed to load data")
        return
    
    print("✓ Data loaded: dementia05.txt")
    print()
    
    # Test with a simple model
    model_name = "IV:ApZ"
    target_state = "0"  # Z=0 is the "negative" class
    
    print(f"Testing model: {model_name}")
    print(f"Target (negative) state: Z={target_state}")
    print()
    
    # Get confusion matrix using the NEW API
    cm = manager.get_confusion_matrix(model_name, target_state)
    
    # Check if valid
    if not cm.get('is_valid', False):
        print("❌ Confusion matrix computation failed")
        if 'error' in cm:
            print(f"   Error: {cm['error']}")
        return
    
    # Print results
    print("=" * 70)
    print("CONFUSION MATRIX (TRAINING DATA)")
    print("=" * 70)
    print()
    print("             Predicted Negative  Predicted Positive")
    print(f"Actual 0:    TN = {cm['TN']:7.0f}       FP = {cm['FP']:7.0f}")
    print(f"Actual 1:    FN = {cm['FN']:7.0f}       TP = {cm['TP']:7.0f}")
    print()
    print(f"Total samples: {cm['TN'] + cm['FP'] + cm['FN'] + cm['TP']:.0f}")
    print()
    
    print("=" * 70)
    print("PERFORMANCE METRICS")
    print("=" * 70)
    print(f"  Accuracy:    {cm['accuracy']:.3f}")
    print(f"  Precision:   {cm['precision']:.3f}")
    print(f"  Recall:      {cm['recall']:.3f}")
    print(f"  Specificity: {cm['specificity']:.3f}")
    print(f"  NPV:         {cm['npv']:.3f}")
    print(f"  F1 Score:    {cm['f1_score']:.3f}")
    print()
    
    # Compare with server output
    print("=" * 70)
    print("EXPECTED VALUES (from server output)")
    print("=" * 70)
    print("TN=179.000, FP=42.000, FN=98.000, TP=105.000")
    print("Accuracy: 0.670, Sensitivity: 0.517, Specificity: 0.810")
    print("Precision: 0.714, NPV: 0.646, F1: 0.600")
    print()
    
    # Verify results
    expected = {
        'TN': 179.0,
        'FP': 42.0,
        'FN': 98.0,
        'TP': 105.0,
        'accuracy': 0.670,
        'sensitivity': 0.517,
        'specificity': 0.810,
        'precision': 0.714,
        'npv': 0.646,
        'f1_score': 0.600
    }
    
    print("=" * 70)
    print("VERIFICATION")
    print("=" * 70)
    
    all_match = True
    for key, expected_val in expected.items():
        actual_val = cm.get(key, 0.0)
        diff = abs(actual_val - expected_val)
        match = diff < 0.001  # Allow small floating point differences
        
        symbol = "✓" if match else "❌"
        print(f"{symbol} {key:12s}: Expected {expected_val:8.3f}, Got {actual_val:8.3f}, Diff {diff:8.5f}")
        
        if not match:
            all_match = False
    
    print()
    if all_match:
        print("✓✓✓ ALL VALUES MATCH SERVER OUTPUT! ✓✓✓")
    else:
        print("❌ Some values don't match - needs debugging")
    
    print()
    print("=" * 70)
    print("API USAGE NOTES")
    print("=" * 70)
    print("✓ No text parsing required")
    print("✓ Direct access to confusion matrix data")
    print("✓ All metrics calculated automatically")
    print("✓ Works on Windows without stdout issues")
    print("✓ Clean, type-safe Python dictionary")

if __name__ == "__main__":
    main()
