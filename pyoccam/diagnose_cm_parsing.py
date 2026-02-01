#!/usr/bin/env python3
"""
Diagnostic script to understand confusion matrix parsing issues
Helps identify where the parser is getting wrong values from
"""

import pyoccam
import re

def diagnose_cm_extraction():
    """Diagnose confusion matrix extraction to find why wrong values are returned"""
    
    print("=" * 80)
    print("CONFUSION MATRIX PARSING DIAGNOSTIC")
    print("=" * 80)
    print()
    
    # Initialize
    manager = pyoccam.VBMManager()
    if not manager.init_from_command_line(["occam", "dementia05.txt"]):
        print("❌ Failed to load data")
        return 1
    
    print("✓ Data loaded (424 samples)")
    print()
    
    # Test with a simple model
    model_name = "IV:ApZ"
    target_state = "0"
    
    print(f"Testing model: {model_name}")
    print(f"Target state: {target_state}")
    print()
    
    # Generate fit report and save it
    print("=" * 80)
    print("STEP 1: Generate fit report")
    print("=" * 80)
    
    fit_report = manager.generate_fit_report(model_name, target_state)
    
    # Save to file for inspection
    with open("diagnostic_fit_report.txt", "w") as f:
        f.write(fit_report)
    print(f"✓ Saved fit report to: diagnostic_fit_report.txt ({len(fit_report)} chars)")
    print()
    
    # Analyze the report structure
    print("=" * 80)
    print("STEP 2: Analyze report structure")
    print("=" * 80)
    print()
    
    # Find all confusion matrix sections
    model_cm_pos = fit_report.find("Confusion Matrix for the Model")
    relation_cm_pos = fit_report.find("Confusion Matrix for the Relation")
    
    print(f"Model CM header at position: {model_cm_pos}")
    print(f"Relation CM header at position: {relation_cm_pos}")
    print()
    
    # Extract the model-level CM section
    if model_cm_pos != -1:
        # Find the end of model section (before relation or end of file)
        if relation_cm_pos != -1 and relation_cm_pos > model_cm_pos:
            model_section = fit_report[model_cm_pos:relation_cm_pos]
        else:
            model_section = fit_report[model_cm_pos:model_cm_pos+2000]
        
        print("MODEL-LEVEL CONFUSION MATRIX SECTION:")
        print("-" * 80)
        print(model_section[:1500])  # First 1500 chars
        print()
        
        # Find all TN values in this section
        tn_pattern = r'TN=,(\d+\.?\d*)'
        fp_pattern = r'FP=,(\d+\.?\d*)'
        fn_pattern = r'FN=,(\d+\.?\d*)'
        tp_pattern = r'TP=,(\d+\.?\d*)'
        
        tn_matches = re.findall(tn_pattern, model_section)
        fp_matches = re.findall(fp_pattern, model_section)
        fn_matches = re.findall(fn_pattern, model_section)
        tp_matches = re.findall(tp_pattern, model_section)
        
        print("VALUES FOUND IN MODEL SECTION:")
        print(f"  TN values: {tn_matches}")
        print(f"  FP values: {fp_matches}")
        print(f"  FN values: {fn_matches}")
        print(f"  TP values: {tp_matches}")
        print()
        
        if len(tn_matches) > 1:
            print("⚠ WARNING: Multiple TN values found! Parser may be confused.")
            print("  Expected: 1 training CM (and possibly 1 test CM)")
            print(f"  Found: {len(tn_matches)} TN values")
            print()
    else:
        print("❌ No model-level CM found in report!")
        print()
    
    # Now call the actual get_confusion_matrix and see what it returns
    print("=" * 80)
    print("STEP 3: Call get_confusion_matrix() and compare")
    print("=" * 80)
    print()
    
    cm = manager.get_confusion_matrix(model_name, target_state)
    
    print("Returned confusion matrix:")
    for key in ['TN', 'FP', 'FN', 'TP', 'accuracy']:
        if key in cm:
            print(f"  {key}: {cm[key]}")
        else:
            # Try lowercase
            key_lower = key.lower()
            if key_lower in cm:
                print(f"  {key_lower}: {cm[key_lower]} (lowercase key!)")
    print()
    
    # Compare expected vs actual
    print("=" * 80)
    print("EXPECTED VALUES (from console output):")
    print("=" * 80)
    print("  TN: 179.000")
    print("  FP:  42.000")
    print("  FN:  98.000")
    print("  TP: 105.000")
    print()
    
    print("=" * 80)
    print("ACTUAL VALUES EXTRACTED:")
    print("=" * 80)
    tn_actual = cm.get('TN', cm.get('tn', 'NOT FOUND'))
    fp_actual = cm.get('FP', cm.get('fp', 'NOT FOUND'))
    fn_actual = cm.get('FN', cm.get('fn', 'NOT FOUND'))
    tp_actual = cm.get('TP', cm.get('tp', 'NOT FOUND'))
    
    print(f"  TN: {tn_actual}")
    print(f"  FP: {fp_actual}")
    print(f"  FN: {fn_actual}")
    print(f"  TP: {tp_actual}")
    print()
    
    # Diagnosis
    print("=" * 80)
    print("DIAGNOSIS:")
    print("=" * 80)
    
    issues = []
    
    if str(tn_actual) != "179.0" and str(tn_actual) != "179":
        issues.append(f"TN mismatch: expected 179, got {tn_actual}")
    
    if str(fp_actual) != "42.0" and str(fp_actual) != "42":
        issues.append(f"FP mismatch: expected 42, got {fp_actual}")
    
    if 'TN' not in cm and 'tn' not in cm:
        issues.append("Missing TN key entirely")
    elif 'tn' in cm and 'TN' not in cm:
        issues.append("Using lowercase keys instead of uppercase")
    
    if issues:
        print("❌ Issues found:")
        for issue in issues:
            print(f"  • {issue}")
        print()
        print("RECOMMENDED FIXES:")
        print("  1. Check extractConfusionMatrixFromReport() is parsing MODEL section, not RELATION")
        print("  2. Ensure parser looks for first TN after 'Model' header, not later ones")
        print("  3. Use uppercase keys in result dictionary: result['TN'] not result['tn']")
    else:
        print("✅ All values match expected!")
    
    print("=" * 80)
    
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(diagnose_cm_extraction())
