#!/usr/bin/env python3
"""
Test script for the new confusion matrix extraction functionality
This demonstrates direct access to the confusion matrix values from C++
"""

import pyoccam
import json

def print_confusion_matrix(cm_dict, label=""):
    """Pretty print a confusion matrix dictionary"""
    if label:
        print(f"\n{'='*60}")
        print(f"{label}")
        print('='*60)
    
    if "error" in cm_dict:
        print(f"Error: {cm_dict['error']}")
        return
        
    # Handle both old format (flat) and new format (train/test)
    if "train" in cm_dict:
        # New format with train/test separation
        print("\nTraining Data Confusion Matrix:")
        print_cm_values(cm_dict["train"])
        
        if cm_dict.get("has_test_data") and "test" in cm_dict:
            print("\nTest Data Confusion Matrix:")
            print_cm_values(cm_dict["test"])
    else:
        # Old format - flat structure
        print_cm_values(cm_dict)

def print_cm_values(cm):
    """Print confusion matrix values and metrics"""
    print(f"""
    Confusion Matrix:
                  Predicted
                  Negative  Positive
    Actual Negative   {cm.get('tn', 0):.0f}      {cm.get('fp', 0):.0f}
           Positive   {cm.get('fn', 0):.0f}      {cm.get('tp', 0):.0f}
    
    Performance Metrics:
    - Accuracy:    {cm.get('accuracy', 0):.4f}
    - Sensitivity: {cm.get('sensitivity', 0):.4f} (True Positive Rate)
    - Specificity: {cm.get('specificity', 0):.4f} (True Negative Rate)
    - Precision:   {cm.get('precision', 0):.4f} (Positive Predictive Value)
    - NPV:         {cm.get('npv', 0):.4f} (Negative Predictive Value)
    - F1 Score:    {cm.get('f1_score', 0):.4f}
    """)

def main():
    print("OCCAM Confusion Matrix Direct Extraction Test")
    print("=" * 60)
    
    # Initialize manager
    manager = pyoccam.VBMManager()
    
    # Load data file
    data_file = "dementia05.txt"
    if not manager.init_from_command_line(["occam", data_file]):
        print(f"Error: Could not load {data_file}")
        return
    
    print(f"✓ Data loaded: {data_file}")
    
    # Configure
    manager.set_report_separator(pyoccam.SPACESEP)
    manager.set_ref_model("bottom")
    
    # Run a search to get some models
    print("\nRunning search...")
    search_report = manager.generate_search_report("loopless-up", 3, 3)
    
    # Get best model
    best_model = manager.get_best_model_by_bic()
    if not best_model:
        print("No best model found, using default")
        best_model = "IV:JKPZ"
    
    print(f"\nBest model by BIC: {best_model}")
    
    # Test 1: Get confusion matrix with new direct extraction
    print_confusion_matrix(
        manager.get_confusion_matrix(best_model, "0"),
        "TEST 1: Direct Confusion Matrix Extraction (target='0')"
    )
    
    # Test 2: Try with different target state
    print_confusion_matrix(
        manager.get_confusion_matrix(best_model, "1"),
        "TEST 2: Direct Confusion Matrix Extraction (target='1')"
    )
    
    # Test 3: Get raw contingency table
    print("\n" + "="*60)
    print("TEST 3: Raw Contingency Table Access")
    print("="*60)
    
    contingency = manager.get_contingency_table(best_model)
    if "error" not in contingency:
        print(f"\nContingency Table Shape: {len(contingency['table'])} x {len(contingency['table'][0]) if contingency['table'] else 0}")
        print(f"Total Count: {contingency.get('total', 0):.0f}")
        print(f"Row Totals: {contingency.get('row_totals', [])[:5]}...")  # Show first 5
        
        # Show a sample of the table
        if contingency['table']:
            print("\nFirst few rows of contingency table:")
            for i, row in enumerate(contingency['table'][:5]):
                print(f"  Row {i}: {row}")
    
    # Test 4: Compare with fit report parsing (old method)
    print("\n" + "="*60)
    print("TEST 4: Comparison with Text Parsing Method")
    print("="*60)
    
    fit_report = manager.generate_fit_report(best_model, "0")
    
    # Check if confusion matrix appears in the fit report
    if "CONFUSION MATRIX" in fit_report:
        print("✓ Confusion matrix found in fit report text")
        
        # Extract a few lines around the confusion matrix
        lines = fit_report.split('\n')
        for i, line in enumerate(lines):
            if "CONFUSION MATRIX" in line:
                print("\nFrom fit report text:")
                for j in range(max(0, i), min(len(lines), i+15)):
                    print(lines[j])
                break
    else:
        print("✗ No confusion matrix in fit report text")
    
    # Test 5: Multiple models comparison
    print("\n" + "="*60)
    print("TEST 5: Multiple Models Comparison")
    print("="*60)
    
    test_models = [
        "IV:JKPZ",
        "IV:ApSxZ:EdZ:AgZ",
        "IV:ApSxZ:EdZ:AgZ:CZ:KZ"
    ]
    
    for model_name in test_models:
        try:
            cm = manager.get_confusion_matrix(model_name, "0")
            if "train" in cm:
                acc = cm["train"].get("accuracy", 0)
                print(f"{model_name:30} - Accuracy: {acc:.4f}")
            elif "accuracy" in cm:
                print(f"{model_name:30} - Accuracy: {cm['accuracy']:.4f}")
            else:
                print(f"{model_name:30} - Error getting confusion matrix")
        except Exception as e:
            print(f"{model_name:30} - Exception: {e}")
    
    print("\n" + "="*60)
    print("Test complete!")
    print("="*60)
    
    # Summary of what we've exposed
    print("\n📊 SUMMARY - New Exposed Functionality:")
    print("1. Direct confusion matrix values (tp, tn, fp, fn)")
    print("2. Calculated metrics (accuracy, sensitivity, specificity, etc.)")
    print("3. Separate train/test confusion matrices when test data available")
    print("4. Raw contingency table access")
    print("5. No need to parse text output anymore!")

if __name__ == "__main__":
    main()