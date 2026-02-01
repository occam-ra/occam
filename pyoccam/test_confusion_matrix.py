#!/usr/bin/env python3
"""
Simple test script for pyoccam get_confusion_matrix() method
Tests with dementia05.txt to verify confusion matrix extraction is working
"""

import pyoccam
import sys

def test_confusion_matrix():
    """Test the get_confusion_matrix method"""
    
    print("="*80)
    print("PYOCCAM CONFUSION MATRIX TEST")
    print("="*80)
    
    print("\n📋 Test Configuration:")
    print("  Data file: dementia05.txt")
    print("  Search: loopless-up (levels=3, width=3)")
    print("  Target state for CM: Z=0")
    
    try:
        # 1. Initialize
        print("\n" + "="*50)
        print("1. INITIALIZING MANAGER")
        print("="*50)
        manager = pyoccam.VBMManager()
        print("✓ VBMManager created")
        
        # 2. Load data
        print("\n" + "="*50)
        print("2. LOADING DATA")
        print("="*50)
        if not manager.init_from_command_line(["occam", "dementia05.txt"]):
            print("✗ Failed to load data")
            return False
        print("✓ Data loaded: dementia05.txt")
        print(f"  Sample size: {manager.get_sample_size()}")
        print(f"  Variables: {', '.join(manager.get_variable_list())}")
        
        # 3. Configure
        print("\n" + "="*50)
        print("3. CONFIGURING")
        print("="*50)
        manager.set_report_separator(pyoccam.SPACESEP)
        manager.set_ref_model("bottom")
        print("✓ Configuration set")
        
        # 4. Run search
        print("\n" + "="*50)
        print("4. RUNNING SEARCH")
        print("="*50)
        print("Searching (loopless-up, levels=3, width=3)...")
        search_report = manager.generate_search_report("loopless-up", 3, 3)
        print("✓ Search completed")
        
        # Save search report for debugging
        with open("test_search_report.txt", "w") as f:
            f.write(search_report)
        print("  Search report saved to: test_search_report.txt")
        
        # 5. Get best models
        print("\n" + "="*50)
        print("5. FINDING BEST MODELS")
        print("="*50)
        best_bic = manager.get_best_model_by_bic()
        best_aic = manager.get_best_model_by_aic()
        best_info = manager.get_best_model_by_information()
        
        print(f"✓ Best model by BIC: {best_bic}")
        print(f"✓ Best model by AIC: {best_aic}")
        print(f"✓ Best model by Information: {best_info}")
        
        # 6. Test confusion matrix extraction
        print("\n" + "="*50)
        print("6. TESTING CONFUSION MATRIX")
        print("="*50)
        
        test_model = best_bic if best_bic else "IV:ApZ"
        target_state = "0"
        
        print(f"\nGetting confusion matrix for: {test_model}")
        print(f"Target (negative) state: Z={target_state}")
        
        # Generate fit report first to see what we're parsing
        print("\nGenerating fit report...")
        fit_report = manager.generate_fit_report(test_model, target_state)
        
        # Save fit report for inspection
        with open("test_fit_report.txt", "w") as f:
            f.write(fit_report)
        print("  Fit report saved to: test_fit_report.txt")
        
        # Look for confusion matrix in the report
        if "Confusion Matrix" in fit_report:
            print("✓ Confusion matrix found in fit report")
            
            # Extract the confusion matrix section for display
            cm_start = fit_report.find("Confusion Matrix")
            cm_section = fit_report[cm_start:cm_start+800] if cm_start >= 0 else ""
            print("\nConfusion matrix section from report:")
            print("-"*50)
            for line in cm_section.split('\n')[:15]:
                if line.strip():
                    print(f"  {line}")
            print("-"*50)
        else:
            print("✗ No confusion matrix in fit report!")
        
        # Now test get_confusion_matrix method
        print("\nCalling get_confusion_matrix()...")
        cm = manager.get_confusion_matrix(test_model, target_state)
        
        # Check if we got values
        got_values = False
        if 'tn' in cm and (cm['tn'] > 0 or cm['fp'] > 0 or cm['fn'] > 0 or cm['tp'] > 0):
            got_values = True
            print("\n✓ Confusion matrix extracted successfully!")
            print(f"\n  Raw values:")
            print(f"    TN = {cm['tn']:.0f}")
            print(f"    FP = {cm['fp']:.0f}")
            print(f"    FN = {cm['fn']:.0f}")
            print(f"    TP = {cm['tp']:.0f}")
            print(f"\n  Calculated metrics:")
            print(f"    Accuracy:    {cm['accuracy']:.3f}")
            print(f"    Sensitivity: {cm['sensitivity']:.3f}")
            print(f"    Specificity: {cm['specificity']:.3f}")
            print(f"    Precision:   {cm['precision']:.3f}")
            print(f"    F1 Score:    {cm['f1_score']:.3f}")
        else:
            print("\n✗ No confusion matrix data returned!")
            print(f"  Debug: cm = {cm}")
            
            # Check for debug info
            if 'warning' in cm:
                print(f"  Warning: {cm['warning']}")
            if 'debug_info' in cm:
                print(f"  Debug info: {cm['debug_info']}")
        
        # 7. Test multiple models
        print("\n" + "="*50)
        print("7. TESTING MULTIPLE MODELS")
        print("="*50)
        
        test_models = ["IV:CZ:KZ", "IV:ApZ", "IV:EdZ:AgZ"]
        for model in test_models:
            print(f"\n🔍 Testing model: {model}")
            try:
                # Try to create the model
                fit_report = manager.generate_fit_report(model, target_state)
                if len(fit_report) > 100:
                    cm = manager.get_confusion_matrix(model, target_state)
                    if cm.get('accuracy', 0) > 0:
                        print(f"  ✓ Accuracy: {cm['accuracy']:.3f}")
                    else:
                        print(f"  ✗ No accuracy returned")
                else:
                    print(f"  ✗ Could not generate fit report")
            except Exception as e:
                print(f"  ✗ Error: {e}")
        
        # Final summary
        print("\n" + "="*80)
        if got_values:
            print("✅ SUCCESS: Confusion matrix extraction is working!")
        else:
            print("❌ FAILURE: Confusion matrix extraction failed")
            print("\nPossible issues:")
            print("  1. The extractConfusionMatrixFromReport() function may need adjustment")
            print("  2. The report separator might be affecting the format")
            print("  3. The target state encoding might be different")
        print("="*80)
        
        return got_values
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

def compare_with_expected():
    """Compare extracted values with expected values from server PDFs"""
    print("\n" + "="*50)
    print("COMPARING WITH EXPECTED VALUES")
    print("="*50)
    
    # Expected values from server PDFs (dementia05 dataset)
    expected = {
        "IV:ApZ": {"tn": 179, "fp": 42, "fn": 98, "tp": 105, "accuracy": 0.670},
        "IV:ApSxZ:EdZ:AgZ:CZ:KZ": {"tn": 170, "fp": 51, "fn": 69, "tp": 134, "accuracy": 0.717}
    }
    
    manager = pyoccam.VBMManager()
    if not manager.init_from_command_line(["occam", "dementia05.txt"]):
        print("Failed to load data")
        return
    
    manager.set_report_separator(pyoccam.SPACESEP)
    manager.set_ref_model("bottom")
    
    all_match = True
    for model_name, expected_values in expected.items():
        print(f"\nTesting model: {model_name}")
        print(f"  Expected: TN={expected_values['tn']}, FP={expected_values['fp']}, "
              f"FN={expected_values['fn']}, TP={expected_values['tp']}, "
              f"Acc={expected_values['accuracy']:.3f}")
        
        try:
            # Generate fit report
            fit_report = manager.generate_fit_report(model_name, "0")
            
            # Get confusion matrix
            cm = manager.get_confusion_matrix(model_name, "0")
            
            # Compare values
            match = True
            if abs(cm.get('tn', 0) - expected_values['tn']) > 1:
                print(f"  ✗ TN mismatch: got {cm.get('tn', 0)}, expected {expected_values['tn']}")
                match = False
            if abs(cm.get('fp', 0) - expected_values['fp']) > 1:
                print(f"  ✗ FP mismatch: got {cm.get('fp', 0)}, expected {expected_values['fp']}")
                match = False
            if abs(cm.get('fn', 0) - expected_values['fn']) > 1:
                print(f"  ✗ FN mismatch: got {cm.get('fn', 0)}, expected {expected_values['fn']}")
                match = False
            if abs(cm.get('tp', 0) - expected_values['tp']) > 1:
                print(f"  ✗ TP mismatch: got {cm.get('tp', 0)}, expected {expected_values['tp']}")
                match = False
            if abs(cm.get('accuracy', 0) - expected_values['accuracy']) > 0.01:
                print(f"  ✗ Accuracy mismatch: got {cm.get('accuracy', 0):.3f}, expected {expected_values['accuracy']:.3f}")
                match = False
            
            if match:
                print(f"  ✓ All values match!")
            else:
                all_match = False
                
        except Exception as e:
            print(f"  ✗ Error: {e}")
            all_match = False
    
    if all_match:
        print("\n✅ ALL EXPECTED VALUES MATCH!")
    else:
        print("\n⚠️ Some values don't match expected.")
        print("\nThe confusion matrix extraction may have issues.")
        print("\nPossible causes:")
        print("1. The server PDF may show different models than tested")
        print("2. The target state encoding may be different")
        print("3. The confusion matrix orientation may be swapped")
        print("\nRecommendations:")
        print("1. Check exact model names in server PDF")
        print("2. Verify target state (0 vs 1 vs other)")
        print("3. Check if TN/TP positions are swapped")

if __name__ == "__main__":
    # Run main test
    success = test_confusion_matrix()
    
    # If successful, compare with expected values
    if success:
        compare_with_expected()
    
    sys.exit(0 if success else 1)