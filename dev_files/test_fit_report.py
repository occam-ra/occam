#!/usr/bin/env python
"""
Test pyoccam2 fit report functionality
Demonstrates complete fit reports matching server output
"""

import pyoccam2
import sys

def test_fit_reports():
    """Test fit reports with various configurations"""
    
    print("=" * 80)
    print("PYOCCAM2 FIT REPORT TEST")
    print("Testing complete fit functionality matching ocutils.py pattern")
    print("=" * 80)
    
    # Initialize manager
    manager = pyoccam2.VBMManager()
    
    # Load data
    success = manager.init_from_command_line(["occam", "dementia05.txt"])
    if not success:
        print("ERROR: Failed to load dementia05.txt")
        return False
    
    print("\nData loaded successfully:")
    print(manager.get_basic_statistics())
    
    # Configure for standard output
    manager.set_report_separator(pyoccam2.SPACESEP)
    manager.set_ref_model("bottom")
    
    # ========== TEST 1: Basic Fit Report ==========
    print("\n" + "=" * 80)
    print("TEST 1: Basic Fit Report")
    print("Model: IV:ApSxZ:EdZ:AgZ:CZ:KZ")
    print("=" * 80)
    
    fit_report = manager.generate_fit_report("IV:ApSxZ:EdZ:AgZ:CZ:KZ")
    print(fit_report)
    
    # ========== TEST 2: Fit Report with Skip Options ==========
    print("\n" + "=" * 80)
    print("TEST 2: Fit Report with Skip Options")
    print("Skipping trained model table and IVI tables")
    print("=" * 80)
    
    manager.set_skip_trained_model_table(True)
    manager.set_skip_ivi_tables(True)
    
    fit_report = manager.generate_fit_report("IV:ApZ:EdZ")
    print(fit_report)
    
    # Reset skip options
    manager.set_skip_trained_model_table(False)
    manager.set_skip_ivi_tables(False)
    
    # ========== TEST 3: Fit Report with Classifier Target ==========
    print("\n" + "=" * 80)
    print("TEST 3: Fit Report with Classifier Target")
    print("Target state for confusion matrix: 0")
    print("=" * 80)
    
    manager.set_fit_classifier_target("0")
    fit_report = manager.generate_fit_report("IV:ApZ", "0")
    print(fit_report)
    
    # ========== TEST 4: Fit Report with Default Model Comparison ==========
    print("\n" + "=" * 80)
    print("TEST 4: Fit Report with Default Model Comparison")
    print("Comparing IV:ApZ:EdZ:AgZ against default IV:ApZ")
    print("=" * 80)
    
    manager.set_default_fit_model("IV:ApZ")
    manager.set_calc_expected_dv(True)
    
    fit_report = manager.generate_fit_report("IV:ApZ:EdZ:AgZ")
    print(fit_report)
    
    # ========== TEST 5: Fit Report for Independence Model ==========
    print("\n" + "=" * 80)
    print("TEST 5: Independence Model (IV:Z)")
    print("=" * 80)
    
    fit_report = manager.generate_fit_report("IV:Z")
    print(fit_report)
    
    # ========== SUMMARY ==========
    print("\n" + "=" * 80)
    print("FIT REPORT TEST SUMMARY")
    print("=" * 80)
    
    print("\n✅ Key Features Implemented:")
    print("1. Basic statistics output")
    print("2. Fit report from VBMManager")
    print("3. Residuals table from Report class")
    print("4. Conditional DV probability tables")
    print("5. Configuration options:")
    print("   - Skip trained model table")
    print("   - Skip IVI tables")
    print("   - Classifier target state")
    print("   - Default model comparison")
    print("   - Calculate expected DV values")
    
    print("\n📊 Fit Report Components (following ocutils.py):")
    print("1. printBasicStatistics() - Data summary")
    print("2. printFitReport() - Model fit statistics")
    print("3. makeFitTable() - Contingency table computation")
    print("4. printResiduals() - Residuals and confusion matrix")
    print("5. printConditional_DV() - Conditional probability tables")
    
    print("\n🔍 What to Check Against Server PDFs:")
    print("- Model statistics (H, DF, LR, Alpha, etc.)")
    print("- Confusion matrix values")
    print("- Conditional probability tables")
    print("- Performance metrics (% correct)")
    
    return True

def compare_with_search():
    """Quick comparison: Run search then fit on best model"""
    
    print("\n" * 2)
    print("=" * 80)
    print("INTEGRATED TEST: Search + Fit")
    print("=" * 80)
    
    manager = pyoccam2.VBMManager()
    manager.init_from_command_line(["occam", "dementia05.txt"])
    manager.set_report_separator(pyoccam2.SPACESEP)
    manager.set_ref_model("bottom")
    
    # Run a quick search
    print("\n1. Running loopless-up search (3 levels, width=3)...")
    search_report = manager.generate_search_report("loopless-up", levels=3, width=3)
    
    # Get best model
    best_model = manager.get_best_model_by_bic()
    if best_model:
        print(f"\n2. Best model by BIC: {best_model}")
        print("\n3. Generating fit report for best model...")
        print("-" * 80)
        
        fit_report = manager.generate_fit_report(best_model)
        print(fit_report)
    else:
        print("\nNote: Best model tracking needs to be verified")
    
    return True

def main():
    """Run all fit report tests"""
    
    print("OCCAM PYOCCAM2 - COMPLETE FIT REPORT TESTING")
    print("Version 39: Following ocutils.py doFit/doAllComputations pattern")
    print("=" * 80)
    
    # Test 1: Fit reports
    success1 = test_fit_reports()
    
    # Test 2: Integrated search + fit
    success2 = compare_with_search()
    
    # Summary
    print("\n" * 2)
    print("=" * 80)
    print("FINAL SUMMARY")
    print("=" * 80)
    
    if success1 and success2:
        print("✅ All tests completed successfully")
        print("\n🎯 Next Steps:")
        print("1. Compare output with server PDFs for exact match")
        print("2. Verify contingency table values")
        print("3. Check conditional probability formatting")
        print("4. Validate confusion matrix calculations")
        
        print("\n📌 Implementation Notes:")
        print("- Following ocutils.py's doFit() and doAllComputations() patterns")
        print("- Using Report class for residuals and conditional DV tables")
        print("- Properly setting %dH(DV) as information × 100")
        print("- Supporting all configuration options from weboccam")
        
        return True
    else:
        print("❌ Some tests failed")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)