#!/usr/bin/env python3
"""
Debug script to see exact confusion matrix output from OCCAM
This will show us the raw format so we can fix the parsing
"""

import pyoccam
import sys
import time

def main():
    print("="*80)
    print("CONFUSION MATRIX DEBUG - RAW OUTPUT INSPECTION")
    print("="*80)
    
    # Initialize and load data
    print("\n1. Loading dementia05 data...")
    manager = pyoccam.VBMManager()
    manager.init_from_command_line(["occam", "dementia05.txt"])
    print("✓ Data loaded")
    
    # Quick search to get a model
    print("\n2. Running quick search to get models...")
    search_report = manager.generate_search_report("loopless-up", 3, 3, False)
    print("✓ Search complete")
    
    # Get best model
    best_model = manager.get_best_model_by_bic()
    if not best_model:
        print("⚠️ No best model found, using default: IV:ApSxZ:EdZ:AgZ:CZ:KZ")
        best_model = "IV:ApSxZ:EdZ:AgZ:CZ:KZ"
    else:
        print(f"✓ Best model: {best_model}")
    
    print("\n3. Generating fit report for inspection...")
    print("="*80)
    
    # Generate fit report with target state "0"
    fit_report = manager.generate_fit_report(best_model, "0")
    
    # Save to file
    with open("debug_fit_report.txt", "w") as f:
        f.write(fit_report)
    print("✓ Full report saved to: debug_fit_report.txt")
    
    print("\n4. SHOWING CONFUSION MATRIX SECTION OF REPORT:")
    print("="*80)
    
    # Find and display the confusion matrix section
    lines = fit_report.split('\n')
    cm_start = -1
    cm_end = -1
    
    # Find confusion matrix section
    for i, line in enumerate(lines):
        if "Confusion Matrix" in line or "CONFUSION MATRIX" in line:
            cm_start = i
            print(f"Found confusion matrix at line {i}")
            # Look for the end (usually about 20-30 lines)
            for j in range(i, min(i+50, len(lines))):
                if lines[j].strip() == "" and j > i+10:  # Empty line after some content
                    cm_end = j
                    break
            if cm_end == -1:
                cm_end = min(i+40, len(lines))
            break
    
    if cm_start >= 0:
        print("\n--- START OF CONFUSION MATRIX SECTION ---")
        for i in range(max(0, cm_start-2), min(cm_end+2, len(lines))):
            print(f"Line {i:3d}: {lines[i]}")
        print("--- END OF CONFUSION MATRIX SECTION ---\n")
    else:
        print("⚠️ No confusion matrix found in report!")
        print("\nFirst 50 lines of report:")
        print("-"*40)
        for i in range(min(50, len(lines))):
            print(f"Line {i:3d}: {lines[i]}")
        print("-"*40)
    
    # Also try to call get_confusion_matrix and see what happens
    print("\n5. Testing get_confusion_matrix() method:")
    print("="*80)
    
    try:
        print(f"Calling: manager.get_confusion_matrix('{best_model}', '0')")
        cm = manager.get_confusion_matrix(best_model, "0")
        print("✓ Method returned successfully")
        print("\nReturned dictionary:")
        for key, value in cm.items():
            print(f"  {key}: {value}")
    except Exception as e:
        print(f"✗ Method failed with error: {e}")
        import traceback
        traceback.print_exc()
    
    # Search for specific patterns
    print("\n6. Searching for confusion matrix patterns in report:")
    print("="*80)
    
    patterns = [
        "TN=",
        "FP=", 
        "FN=",
        "TP=",
        "True Negative",
        "False Positive",
        "Actual",
        "Predicted",
        "Rule",
        "%correct",
        "Accuracy",
        "Sensitivity",
        "Specificity"
    ]
    
    for pattern in patterns:
        found = False
        for i, line in enumerate(lines):
            if pattern in line:
                if not found:
                    print(f"\n'{pattern}' found at:")
                    found = True
                print(f"  Line {i}: {line.strip()}")
        if not found:
            print(f"\n'{pattern}' - NOT FOUND")
    
    print("\n" + "="*80)
    print("DEBUG COMPLETE - Check output above to see actual format")
    print("="*80)
    
    return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
