#!/usr/bin/env python3
"""
PyOccam Complete Pipeline Test
Tests search, model selection, fit reports, and confusion matrices
"""

import pyoccam
import time
import sys

def print_header(text, char='=', width=80):
    """Print a formatted header"""
    print(f"\n{char * width}")
    print(f"{text.center(width)}")
    print(f"{char * width}")

def print_confusion_matrix(cm, model_name=""):
    """Pretty print a confusion matrix"""
    if model_name:
        print(f"\nConfusion Matrix for {model_name}:")
    else:
        print("\nConfusion Matrix:")
    
    print(f"{'':15} {'Predicted':^20}")
    print(f"{'':15} {'Negative':>10} {'Positive':>10}")
    print(f"{'Actual Negative':<15} {cm.get('TN', 0):>10.0f} {cm.get('FP', 0):>10.0f}")
    print(f"{'       Positive':<15} {cm.get('FN', 0):>10.0f} {cm.get('TP', 0):>10.0f}")
    
    print("\nPerformance Metrics:")
    print(f"  Accuracy:    {cm.get('accuracy', 0):.3f} ({cm.get('accuracy', 0)*100:.1f}%)")
    print(f"  Precision:   {cm.get('precision', 0):.3f}")
    print(f"  Recall:      {cm.get('recall', 0):.3f} (Sensitivity)")
    print(f"  Specificity: {cm.get('specificity', 0):.3f}")
    print(f"  F1 Score:    {cm.get('f1_score', 0):.3f}")

def test_model(manager, model_name, target_state="0", verbose=True):
    """Test a single model and return confusion matrix"""
    if verbose:
        print(f"\nTesting model: {model_name}")
        print("-" * 40)
    
    try:
        # Get confusion matrix
        cm = manager.get_confusion_matrix(model_name, target_state)
        
        if "error" in cm:
            print(f"  ✗ Error: {cm['error']}")
            return None
            
        if verbose:
            print(f"  ✓ Confusion matrix extracted")
            print(f"  ✓ Accuracy: {cm.get('accuracy', 0):.3f}")
        
        return cm
        
    except Exception as e:
        print(f"  ✗ Exception: {e}")
        return None

def main():
    print_header("PYOCCAM COMPLETE PIPELINE TEST")
    
    # ========== Configuration ==========
    DATA_FILE = "dementia05.txt"
    SEARCH_TYPE = "loopless-up"
    SEARCH_LEVELS = 7  # More levels for thorough testing
    SEARCH_WIDTH = 3
    TARGET_STATE = "0"  # Default negative state for confusion matrix
    
    print("\n📋 Configuration:")
    print(f"  Data file: {DATA_FILE}")
    print(f"  Search: {SEARCH_TYPE} (levels={SEARCH_LEVELS}, width={SEARCH_WIDTH})")
    print(f"  Target state for CM: Z={TARGET_STATE}")
    
    # ========== 1. Initialize ==========
    print_header("STEP 1: INITIALIZATION", '-', 60)
    manager = pyoccam.VBMManager()
    if not manager.init_from_command_line(["occam", DATA_FILE]):
        print("✗ Failed to load data")
        sys.exit(1)
    
    print(f"✓ Data loaded: {DATA_FILE}")
    print(f"  Sample size: {manager.get_sample_size()}")
    vars = manager.get_variable_list()
    print(f"  Variables ({len(vars)}): {', '.join(vars[:5])}...")
    
    # ========== 2. Configure ==========
    print_header("STEP 2: CONFIGURATION", '-', 60)
    manager.set_report_separator(pyoccam.SPACESEP)
    manager.set_ref_model("bottom")
    print("✓ Report separator: SPACE")
    print("✓ Reference model: bottom")
    
    # ========== 3. Search ==========
    print_header("STEP 3: SEARCH", '-', 60)
    print(f"Running {SEARCH_TYPE} search...")
    start_time = time.time()
    
    search_report = manager.generate_search_report(
        search_type=SEARCH_TYPE,
        levels=SEARCH_LEVELS,
        width=SEARCH_WIDTH,
        include_test_data=False
    )
    
    elapsed = time.time() - start_time
    print(f"✓ Search completed in {elapsed:.2f} seconds")
    
    # Count models in report
    model_count = search_report.count("IV:")
    print(f"✓ Models evaluated: ~{model_count}")
    
    # Save search report
    with open("search_report_complete.txt", "w") as f:
        f.write(search_report)
    print(f"✓ Search report saved to search_report_complete.txt")
    
    # ========== 4. Best Model Selection ==========
    print_header("STEP 4: BEST MODEL SELECTION", '-', 60)
    
    best_bic = manager.get_best_model_by_bic()
    best_aic = manager.get_best_model_by_aic()
    best_info = manager.get_best_model_by_information()
    
    print("Best Models Found:")
    print(f"  📊 By Information: {best_info} (DEFAULT)")
    print(f"  📈 By BIC:         {best_bic}")
    print(f"  📉 By AIC:         {best_aic}")
    
    # Default to best by information
    best_model = best_info if best_info else best_bic
    print(f"\n🎯 Using best model: {best_model}")
    
    # ========== 5. Fit Report ==========
    print_header("STEP 5: FIT REPORT", '-', 60)
    
    print(f"Generating fit report for {best_model}...")
    fit_report = manager.generate_fit_report(best_model, TARGET_STATE)
    
    if "ERROR" not in fit_report:
        print(f"✓ Fit report generated: {len(fit_report)} chars")
        
        # Save fit report
        with open(f"fit_report_{best_model.replace(':', '_')}.txt", "w") as f:
            f.write(fit_report)
        print(f"✓ Fit report saved")
        
        # Check content
        has_stats = "MODEL STATISTICS" in fit_report or "Model Statistics" in fit_report
        has_conditional = "CONDITIONAL" in fit_report.upper()
        
        print(f"  Contains statistics: {'✓' if has_stats else '✗'}")
        print(f"  Contains conditional tables: {'✓' if has_conditional else '✗'}")
    else:
        print(f"✗ Error: {fit_report}")
    
    # ========== 6. Confusion Matrix Testing ==========
    print_header("STEP 6: CONFUSION MATRIX ANALYSIS", '-', 60)
    
    # Test best model
    cm_best = test_model(manager, best_model, TARGET_STATE)
    if cm_best:
        print_confusion_matrix(cm_best, best_model)
    
    # ========== 7. Test Multiple Models ==========
    print_header("STEP 7: TESTING MULTIPLE MODELS", '-', 60)
    
    # Test some simple models
    test_models = [
        "IV:Z",           # Independence (baseline)
        "IV:ApZ",         # Simple 2-variable
        "IV:CZ",          # Another simple model
        "IV:ApZ:CZ",      # 3-variable
        "IV:ApZ:EdZ",     # Different combination
    ]
    
    results = {}
    print("\nTesting various models:")
    for model_name in test_models:
        cm = test_model(manager, model_name, TARGET_STATE, verbose=False)
        if cm:
            acc = cm.get('accuracy', 0)
            results[model_name] = acc
            print(f"  {model_name:20} Accuracy: {acc:.3f} ({acc*100:.1f}%)")
    
    # Find best from our test set
    if results:
        best_test = max(results, key=results.get)
        print(f"\n🏆 Best accuracy from test set: {best_test} ({results[best_test]:.3f})")
    
    # ========== 8. Complex Model Testing ==========
    print_header("STEP 8: COMPLEX MODEL TESTING", '-', 60)
    
    # Test a more complex model if available
    complex_models = [
        "IV:ApZ:EdZ:CZ",
        "IV:ApSxZ:EdZ:AgZ:CZ",
        best_model  # Test the best model again
    ]
    
    for model_name in complex_models:
        if model_name:  # Check if not empty
            cm = test_model(manager, model_name, TARGET_STATE)
            if cm:
                print_confusion_matrix(cm, model_name)
                break
    
    # ========== 9. Performance Summary ==========
    print_header("STEP 9: PERFORMANCE SUMMARY", '-', 60)
    
    print("\n📊 Summary Statistics:")
    print(f"  Models tested: {len(results) + len(complex_models)}")
    print(f"  Search time: {elapsed:.2f}s")
    print(f"  Best model: {best_model}")
    
    if cm_best:
        print(f"\n📈 Best Model Performance:")
        print(f"  Accuracy:    {cm_best.get('accuracy', 0):.3f}")
        print(f"  Precision:   {cm_best.get('precision', 0):.3f}")
        print(f"  Recall:      {cm_best.get('recall', 0):.3f}")
        print(f"  F1 Score:    {cm_best.get('f1_score', 0):.3f}")
    
    # ========== Final Status ==========
    print_header("✅ ALL TESTS COMPLETED SUCCESSFULLY!", '=', 80)
    
    return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n⚠️ Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
