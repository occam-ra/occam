#!/usr/bin/env python3
"""
Focused test for pyoccam get_confusion_matrix() with dementia05 data
Tests the new implementation to ensure we're getting real values
"""

import pyoccam
import sys
import time

def main():
    print("="*80)
    print("PYOCCAM CONFUSION MATRIX TEST - DEMENTIA DATA")
    print("="*80)
    
    try:
        # Initialize manager
        print("\n1. Initializing PyOccam...")
        manager = pyoccam.VBMManager()
        
        # Load dementia data
        print("2. Loading dementia05.txt...")
        if not manager.init_from_command_line(["occam", "dementia05.txt"]):
            print("ERROR: Failed to load dementia05.txt")
            print("Make sure dementia05.txt is in the current directory")
            return 1
        
        sample_size = manager.get_sample_size()
        variables = manager.get_variable_list()
        print(f"   ✓ Data loaded: {sample_size} samples, {len(variables)} variables")
        print(f"   Variables: {', '.join(variables[:5])}...")
        
        # Configure manager
        print("\n3. Configuring manager...")
        manager.set_report_separator(pyoccam.SPACESEP)  # This actually produces CSV format
        manager.set_ref_model("bottom")
        print("   ✓ Configuration complete")
        
        # Run a simple search
        print("\n4. Running search (loopless-up, 3 levels)...")
        start_time = time.time()
        search_report = manager.generate_search_report("loopless-up", 3, 3)
        search_time = time.time() - start_time
        print(f"   ✓ Search completed in {search_time:.2f} seconds")
        
        # Get best models
        print("\n5. Finding best models...")
        best_bic = manager.get_best_model_by_bic()
        best_aic = manager.get_best_model_by_aic()
        best_info = manager.get_best_model_by_information()
        
        print(f"   Best by BIC:         {best_bic}")
        print(f"   Best by AIC:         {best_aic}")
        print(f"   Best by Information: {best_info}")
        
        # Test confusion matrix for each model
        print("\n6. Testing get_confusion_matrix() method...")
        print("-"*60)
        
        # Define models to test (use best models found, plus some known models)
        test_models = []
        if best_bic:
            test_models.append(("Best BIC", best_bic))
        if best_aic and best_aic != best_bic:
            test_models.append(("Best AIC", best_aic))
        
        # Add some known models from the dementia dataset
        test_models.extend([
            ("Simple IV:ApZ", "IV:ApZ"),
            ("Two component", "IV:CZ:KZ"),
            ("Three component", "IV:ApZ:EdZ:CZ")
        ])
        
        successful_extractions = 0
        
        for description, model_name in test_models:
            print(f"\n   Testing: {description} ({model_name})")
            print("   " + "-"*40)
            
            try:
                # First, generate the fit report to see what we're dealing with
                print("   Generating fit report...")
                fit_report = manager.generate_fit_report(model_name, "0")
                
                # Check if confusion matrix is in the report
                if "Confusion Matrix" in fit_report:
                    print("   ✓ Confusion matrix found in fit report")
                    
                    # Find and display the confusion matrix section
                    cm_start = fit_report.find("Confusion Matrix")
                    if cm_start >= 0:
                        # Get a few lines of the confusion matrix
                        cm_lines = fit_report[cm_start:].split('\n')[:10]
                        print("\n   Actual confusion matrix in report:")
                        for line in cm_lines:
                            if line.strip() and ('TN=' in line or 'FN=' in line or 
                                               'TP=' in line or 'FP=' in line or 
                                               'Confusion' in line or 'Actual' in line):
                                print(f"     {line}")
                else:
                    print("   ⚠ No confusion matrix in fit report")
                
                # Now call get_confusion_matrix
                print("\n   Calling get_confusion_matrix()...")
                cm = manager.get_confusion_matrix(model_name, "0")
                
                # Check what we got
                if isinstance(cm, dict):
                    # Check if we have actual values
                    has_values = False
                    tn = cm.get('tn', 0)
                    fp = cm.get('fp', 0)
                    fn = cm.get('fn', 0)
                    tp = cm.get('tp', 0)
                    
                    if tn > 0 or fp > 0 or fn > 0 or tp > 0:
                        has_values = True
                        successful_extractions += 1
                        
                        print(f"\n   ✅ CONFUSION MATRIX EXTRACTED:")
                        print(f"      TN (True Negatives):  {tn:6.0f}")
                        print(f"      FP (False Positives): {fp:6.0f}")
                        print(f"      FN (False Negatives): {fn:6.0f}")
                        print(f"      TP (True Positives):  {tp:6.0f}")
                        print(f"      " + "-"*30)
                        print(f"      Total samples: {tn+fp+fn+tp:.0f}")
                        
                        # Metrics
                        accuracy = cm.get('accuracy', 0)
                        sensitivity = cm.get('sensitivity', 0)
                        specificity = cm.get('specificity', 0)
                        precision = cm.get('precision', 0)
                        f1_score = cm.get('f1_score', 0)
                        
                        print(f"\n   📊 CALCULATED METRICS:")
                        print(f"      Accuracy:    {accuracy:.3f} ({accuracy*100:.1f}%)")
                        print(f"      Sensitivity: {sensitivity:.3f} (Recall/TPR)")
                        print(f"      Specificity: {specificity:.3f} (TNR)")
                        print(f"      Precision:   {precision:.3f} (PPV)")
                        print(f"      F1 Score:    {f1_score:.3f}")
                    else:
                        print("\n   ❌ NO VALUES EXTRACTED")
                        print(f"      Returned dictionary: {cm}")
                        
                        # Debug info
                        if 'warning' in cm:
                            print(f"      Warning: {cm['warning']}")
                        if 'debug_info' in cm:
                            print(f"      Debug: {cm['debug_info']}")
                        if 'report_length' in cm:
                            print(f"      Report length: {cm['report_length']}")
                else:
                    print(f"\n   ❌ Unexpected return type: {type(cm)}")
                    print(f"      Value: {cm}")
                    
            except Exception as e:
                print(f"\n   ❌ ERROR: {e}")
                import traceback
                traceback.print_exc()
        
        # Final summary
        print("\n" + "="*80)
        print("SUMMARY")
        print("="*80)
        
        if successful_extractions > 0:
            print(f"✅ SUCCESS: Extracted confusion matrices for {successful_extractions}/{len(test_models)} models")
            
            # Show example values for verification
            print("\nExample from IV:ApZ (if available):")
            try:
                cm = manager.get_confusion_matrix("IV:ApZ", "0")
                if cm.get('tn', 0) > 0:
                    print(f"  TN={cm['tn']:.0f}, FP={cm['fp']:.0f}")
                    print(f"  FN={cm['fn']:.0f}, TP={cm['tp']:.0f}")
                    print(f"  Accuracy: {cm['accuracy']:.3f}")
                    
                    # Compare with expected values from server PDF
                    print("\nExpected values from server PDF (IV:ApZ):")
                    print("  TN=179, FP=42")
                    print("  FN=98, TP=105")
                    print("  Accuracy: 0.670")
                    
                    # Check if they match
                    if abs(cm['tn'] - 179) < 2 and abs(cm['tp'] - 105) < 2:
                        print("\n  ✅ Values match server output!")
                    else:
                        print("\n  ⚠ Values don't match server output")
                        print("  This could be due to different data preprocessing or model parameters")
            except:
                pass
                
        else:
            print("❌ FAILED: Could not extract confusion matrices")
            print("\nTroubleshooting steps:")
            print("1. Check that the fit report contains 'Confusion Matrix'")
            print("2. Verify the format is CSV (commas) as expected")
            print("3. Check pyoccam_pybind11.cpp extractConfusionMatrixFromReport()")
            print("4. Ensure the model can be created and fitted properly")
            
            # Save debug files
            print("\nSaving debug files...")
            try:
                # Save search report
                with open("debug_search_report.txt", "w") as f:
                    f.write(search_report)
                print("  Saved: debug_search_report.txt")
                
                # Save a fit report
                if best_bic:
                    fit_report = manager.generate_fit_report(best_bic, "0")
                    with open("debug_fit_report.txt", "w") as f:
                        f.write(fit_report)
                    print("  Saved: debug_fit_report.txt")
                    print("\nCheck these files to see the actual format of the confusion matrix")
            except:
                pass
        
        print("="*80)
        return 0 if successful_extractions > 0 else 1
        
    except Exception as e:
        print(f"\n❌ FATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())