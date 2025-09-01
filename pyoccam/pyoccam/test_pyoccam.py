#!/usr/bin/env python3
"""
Test script to verify PyOCCAM fixes for:
1. Best model display at bottom of search report
2. Best model getter methods
3. Confusion matrix extraction
"""

import pyoccam
import sys

def test_pyoccam():
    print("=" * 60)
    print("TESTING PYOCCAM FIXES")
    print("=" * 60)
    
    # 1. Initialize
    manager = pyoccam.VBMManager()
    
    # Replace with your data file
    DATA_FILE = "dementia05.txt"
    
    if not manager.init_from_command_line(["occam", DATA_FILE]):
        print(f"Error: Could not load {DATA_FILE}")
        return False
    
    print(f"✓ Data loaded: {DATA_FILE}")
    print(f"  Sample size: {manager.get_sample_size()}")
    print()
    
    # 2. Configure
    manager.set_report_separator(pyoccam.SPACESEP)
    manager.set_report_variables("ID$I, Model, Level$I, h, ddf, dLR, Alpha, Inf, %dH(DV), dAIC, dBIC")
    manager.set_ref_model("bottom")
    
    # 3. Run search
    print("Running search...")
    search_report = manager.generate_search_report(
        search_type="loopless-up",
        levels=3,
        width=3,
        include_test_data=False
    )
    
    # 4. CHECK: Does search report contain best model summary at bottom?
    print("\nChecking search report for best model summary...")
    if "BEST MODELS SUMMARY" in search_report:
        print("✓ Best models summary found in report!")
        
        # Extract the summary section
        summary_start = search_report.find("BEST MODELS SUMMARY")
        if summary_start > 0:
            print("\nSummary section:")
            print("-" * 40)
            print(search_report[summary_start:])
    else:
        print("✗ Best models summary NOT found in report")
        print("  This is the issue that needs fixing!")
    
    # 5. Test getter methods
    print("\nTesting best model getter methods...")
    best_bic = manager.get_best_model_by_bic()
    best_aic = manager.get_best_model_by_aic()
    best_info = manager.get_best_model_by_information()
    
    print(f"  get_best_model_by_bic(): {best_bic if best_bic else 'EMPTY'}")
    print(f"  get_best_model_by_aic(): {best_aic if best_aic else 'EMPTY'}")
    print(f"  get_best_model_by_information(): {best_info if best_info else 'EMPTY'}")
    
    if best_bic or best_aic or best_info:
        print("✓ Getter methods returning models!")
    else:
        print("✗ Getter methods returning empty")
    
    # 6. Save search report to verify content
    with open("test_search_report.txt", 'w') as f:
        f.write(search_report)
    print("\n✓ Full search report saved to test_search_report.txt")
    
    # 7. Test confusion matrix if we have a best model
    if best_bic:
        print(f"\nTesting confusion matrix for model: {best_bic}")
        cm = manager.get_confusion_matrix(best_bic, "0")
        
        print("Confusion Matrix values:")
        print(f"  True Positives:  {cm['tp']}")
        print(f"  True Negatives:  {cm['tn']}")
        print(f"  False Positives: {cm['fp']}")
        print(f"  False Negatives: {cm['fn']}")
        print(f"  Accuracy:        {cm['accuracy']:.3f}")
        print(f"  Sensitivity:     {cm['sensitivity']:.3f}")
        print(f"  Specificity:     {cm['specificity']:.3f}")
    
    print("\n" + "=" * 60)
    print("TEST COMPLETE")
    print("=" * 60)
    
    # Summary of issues
    print("\nSUMMARY:")
    issues_found = []
    
    if "BEST MODELS SUMMARY" not in search_report:
        issues_found.append("Best model summary missing from search report")
    
    if not (best_bic or best_aic or best_info):
        issues_found.append("Best model getters returning empty")
    
    if issues_found:
        print("Issues that need fixing:")
        for issue in issues_found:
            print(f"  - {issue}")
    else:
        print("✓ All tests passed! The fixes are working correctly.")
    
    return len(issues_found) == 0

if __name__ == "__main__":
    success = test_pyoccam()
    sys.exit(0 if success else 1)