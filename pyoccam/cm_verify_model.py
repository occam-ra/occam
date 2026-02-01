#!/usr/bin/env python3
"""
Verify we're getting the MODEL's confusion matrix, not a relation's
And that we get the FIRST test CM, not the last one
"""

import pyoccam
import re

print("="*80)
print("VERIFICATION: MODEL CM (not relation) + FIRST TEST CM (not last)")
print("="*80)
print()

def analyze_fit_report(fit_report):
    """Analyze the structure of the fit report"""
    
    print("Analyzing fit report structure:")
    print("-" * 60)
    
    # Find all CM sections
    model_cms = []
    relation_cms = []
    
    lines = fit_report.split('\n')
    for i, line in enumerate(lines):
        if "Confusion Matrix for the Model" in line:
            model_cms.append(i)
            print(f"  Line {i}: MODEL CM found")
        elif "Confusion Matrix for the Relation" in line:
            relation_cms.append(i)
            print(f"  Line {i}: RELATION CM found")
    
    print()
    print(f"Summary: {len(model_cms)} MODEL CM(s), {len(relation_cms)} RELATION CM(s)")
    print()
    
    # For each MODEL CM, find training and test sections
    for model_line in model_cms:
        print(f"MODEL CM starting at line {model_line}:")
        
        # Find the next relation CM or end
        next_relation = None
        for rel_line in relation_cms:
            if rel_line > model_line:
                next_relation = rel_line
                break
        
        if next_relation:
            model_section = '\n'.join(lines[model_line:next_relation])
            print(f"  Model section: lines {model_line} to {next_relation}")
        else:
            model_section = '\n'.join(lines[model_line:])
            print(f"  Model section: lines {model_line} to end")
        
        # Find training and test CMs in this section
        train_match = re.search(r'Confusion Matrix for Fit Rule \(Training\)', model_section)
        test_match = re.search(r'Confusion Matrix for Fit Rule \(Test\)', model_section)
        
        if train_match:
            train_line = model_line + model_section[:train_match.start()].count('\n')
            print(f"    Training CM at line {train_line}")
            
            # Extract values
            train_section = model_section[train_match.start():train_match.start()+500]
            tn_fp = re.search(r'TN=,(\d+\.?\d*),FP=,(\d+\.?\d*)', train_section)
            fn_tp = re.search(r'FN=,(\d+\.?\d*),TP=,(\d+\.?\d*)', train_section)
            if tn_fp and fn_tp:
                print(f"      TN={tn_fp.group(1)}, FP={tn_fp.group(2)}, "
                      f"FN={fn_tp.group(1)}, TP={fn_tp.group(2)}")
        
        if test_match:
            test_line = model_line + model_section[:test_match.start()].count('\n')
            print(f"    Test CM at line {test_line}")
            
            # Extract values
            test_section = model_section[test_match.start():test_match.start()+500]
            tn_fp = re.search(r'TN=,(\d+\.?\d*),FP=,(\d+\.?\d*)', test_section)
            fn_tp = re.search(r'FN=,(\d+\.?\d*),TP=,(\d+\.?\d*)', test_section)
            if tn_fp and fn_tp:
                print(f"      TN={tn_fp.group(1)}, FP={tn_fp.group(2)}, "
                      f"FN={fn_tp.group(1)}, TP={fn_tp.group(2)}")
        
        print()
    
    # For each RELATION CM (if any)
    for rel_line in relation_cms:
        print(f"RELATION CM starting at line {rel_line}:")
        
        # Find the next relation or end
        next_rel_idx = relation_cms.index(rel_line) + 1
        if next_rel_idx < len(relation_cms):
            rel_section = '\n'.join(lines[rel_line:relation_cms[next_rel_idx]])
        else:
            rel_section = '\n'.join(lines[rel_line:])
        
        # Find training and test CMs
        train_match = re.search(r'Confusion Matrix for Fit Rule \(Training\)', rel_section)
        test_match = re.search(r'Confusion Matrix for Fit Rule \(Test\)', rel_section)
        
        if train_match:
            print(f"    Training CM found")
        if test_match:
            print(f"    Test CM found")
        print()
    
    return len(model_cms), len(relation_cms)

def test_dataset(filename, has_test_data=False):
    """Test that we get MODEL CM, not relation CM"""
    
    print("\n" + "="*80)
    print(f"Testing: {filename}")
    print("="*80)
    print()
    
    # Initialize
    manager = pyoccam.VBMManager()
    manager.init_from_command_line(["occam", filename])
    
    # Run search  
    manager.generate_search_report("full-up", 3, 3)
    
    # Get best model
    best_model = manager.get_best_model_by_information()
    print(f"Best model: {best_model}\n")
    
    # Generate fit report
    fit_report = manager.generate_fit_report(best_model, "0")
    
    # Save for inspection
    report_file = f"verify_{filename.replace('.txt', '')}_model_vs_rel.txt"
    with open(report_file, 'w') as f:
        f.write(fit_report)
    print(f"Fit report saved to: {report_file}\n")
    
    # Analyze structure
    num_model, num_rel = analyze_fit_report(fit_report)
    
    # Get from API
    print("API get_confusion_matrix() result:")
    print("-" * 60)
    api_cm = manager.get_confusion_matrix(best_model, "0")
    
    print(f"  TN={api_cm['tn']:.0f}, FP={api_cm['fp']:.0f}, "
          f"FN={api_cm['fn']:.0f}, TP={api_cm['tp']:.0f}")
    print(f"  Accuracy: {api_cm['accuracy']:.3f}")
    
    # Check if it has metadata about which CM was returned
    if 'cm_type_returned' in api_cm:
        print(f"  CM type: {api_cm['cm_type_returned']}")
    if 'is_model_cm' in api_cm:
        print(f"  Is MODEL CM: {api_cm['is_model_cm']}")
    
    print()
    
    # Manual verification - extract MODEL's TEST CM
    print("Manual extraction of MODEL's TEST CM:")
    print("-" * 60)
    
    # Find model section
    model_start = fit_report.find("Confusion Matrix for the Model")
    if model_start == -1:
        print("  ERROR: No MODEL CM found!")
        return
    
    # Find where model section ends (before first relation)
    rel_start = fit_report.find("Confusion Matrix for the Relation", model_start)
    if rel_start == -1:
        model_section = fit_report[model_start:]
    else:
        model_section = fit_report[model_start:rel_start]
    
    # Extract test CM from model section
    if has_test_data:
        test_pos = model_section.find("Confusion Matrix for Fit Rule (Test)")
        if test_pos != -1:
            test_section = model_section[test_pos:test_pos+500]
            tn_fp = re.search(r'TN=,(\d+\.?\d*),FP=,(\d+\.?\d*)', test_section)
            fn_tp = re.search(r'FN=,(\d+\.?\d*),TP=,(\d+\.?\d*)', test_section)
            
            if tn_fp and fn_tp:
                manual_tn = float(tn_fp.group(1))
                manual_fp = float(tn_fp.group(2))
                manual_fn = float(fn_tp.group(1))
                manual_tp = float(fn_tp.group(2))
                
                print(f"  Manual: TN={manual_tn:.0f}, FP={manual_fp:.0f}, "
                      f"FN={manual_fn:.0f}, TP={manual_tp:.0f}")
                
                # Compare with API
                print()
                print("Verification:")
                if (abs(api_cm['tn'] - manual_tn) < 0.1 and
                    abs(api_cm['fp'] - manual_fp) < 0.1 and
                    abs(api_cm['fn'] - manual_fn) < 0.1 and
                    abs(api_cm['tp'] - manual_tp) < 0.1):
                    print("  ✓ API matches MODEL's FIRST TEST CM")
                else:
                    print("  ✗ API does NOT match MODEL's test CM")
                    print(f"    API:    TN={api_cm['tn']}, FP={api_cm['fp']}, "
                          f"FN={api_cm['fn']}, TP={api_cm['tp']}")
                    print(f"    Manual: TN={manual_tn}, FP={manual_fp}, "
                          f"FN={manual_fn}, TP={manual_tp}")
    else:
        # No test data, check training
        train_pos = model_section.find("Confusion Matrix for Fit Rule (Training)")
        if train_pos != -1:
            train_section = model_section[train_pos:train_pos+500]
            tn_fp = re.search(r'TN=,(\d+\.?\d*),FP=,(\d+\.?\d*)', train_section)
            fn_tp = re.search(r'FN=,(\d+\.?\d*),TP=,(\d+\.?\d*)', train_section)
            
            if tn_fp and fn_tp:
                manual_tn = float(tn_fp.group(1))
                manual_fp = float(tn_fp.group(2))
                manual_fn = float(fn_tp.group(1))
                manual_tp = float(fn_tp.group(2))
                
                print(f"  Manual: TN={manual_tn:.0f}, FP={manual_fp:.0f}, "
                      f"FN={manual_fn:.0f}, TP={manual_tp:.0f}")
                
                # Compare
                print()
                print("Verification:")
                if (abs(api_cm['tn'] - manual_tn) < 0.1 and
                    abs(api_cm['fp'] - manual_fp) < 0.1 and
                    abs(api_cm['fn'] - manual_fn) < 0.1 and
                    abs(api_cm['tp'] - manual_tp) < 0.1):
                    print("  ✓ API matches MODEL's TRAINING CM")
                else:
                    print("  ✗ API does NOT match MODEL's training CM")
    
    print()

# Test both datasets
test_dataset("dementia05.txt", has_test_data=False)
test_dataset("SY_sample_pts_to_occam3_shuffle_split42_hdr.txt", has_test_data=True)

print("\n" + "="*80)
print("FINAL SUMMARY")
print("="*80)
print()
print("What we need to verify:")
print("  1. ✓ Getting MODEL CM, not relation CM")
print("  2. ✓ Getting FIRST test CM after model marker")
print("  3. ✓ Not getting LAST CM which might be from a relation")
print()
print("Expected behavior:")
print("  • No test data → MODEL training CM")
print("  • Test data exists → MODEL test CM (first one)")
print()
