#!/usr/bin/env python3
"""
Test confusion matrix with the three best models from the server version:
- Best by BIC: IV:ApZ:EdZ:CZ
- Best by AIC: IV:ApSxZ:EdZ:AgZ:CZ:KZ  
- Best by Information: IV:ApZ:EdZ:AgZ:CZ:KZ

This will help diagnose why we're getting all zeros.
"""
import pyoccam

print("="*80)
print("CONFUSION MATRIX TEST - SERVER BEST MODELS")
print("="*80)
print()

# Initialize
print("1. Initializing PyOccam...")
manager = pyoccam.VBMManager()
if not manager.init_from_command_line(["occam", "dementia05.txt"]):
    print("❌ Failed to load data")
    exit(1)
print("✓ Data loaded: dementia05.txt (424 samples)")
print()

# Test models from server output
test_models = [
    ("IV:ApZ:EdZ:CZ", "Best by BIC (dBIC=49.59)"),
    ("IV:ApSxZ:EdZ:AgZ:CZ:KZ", "Best by AIC (dAIC=30.90)"),
    ("IV:ApZ:EdZ:AgZ:CZ:KZ", "Best by Information (dBIC=54.17)")
]

target_state = "0"  # Z=0 is the "negative" class

for model_name, description in test_models:
    print("=" * 80)
    print(f"Testing: {model_name}")
    print(f"Description: {description}")
    print("=" * 80)
    print()
    
    try:
        print(f"Calling get_confusion_matrix('{model_name}', '{target_state}')...")
        print()
        
        # This will trigger the debug output from computeConfusionMatrix
        cm = manager.get_confusion_matrix(model_name, target_state)
        
        print()
        print("RESULTS RECEIVED FROM PYTHON:")
        print("-" * 80)
        
        if "error" in cm:
            print(f"❌ ERROR: {cm['error']}")
        else:
            tn = cm.get('TN', 0)
            fp = cm.get('FP', 0)
            fn = cm.get('FN', 0)
            tp = cm.get('TP', 0)
            total = tn + fp + fn + tp
            
            print(f"Confusion Matrix:")
            print(f"              Predicted")
            print(f"              Z=0     Z≠0")
            print(f"Actual Z=0    {tn:>3.0f}     {fp:>3.0f}")
            print(f"       Z≠0    {fn:>3.0f}     {tp:>3.0f}")
            print()
            print(f"Total samples: {total:.0f} (expected 424)")
            print()
            
            if total > 0:
                acc = cm.get('accuracy', 0)
                sens = cm.get('sensitivity', 0)
                spec = cm.get('specificity', 0)
                
                print(f"Metrics:")
                print(f"  Accuracy:    {acc:.3f}")
                print(f"  Sensitivity: {sens:.3f}")
                print(f"  Specificity: {spec:.3f}")
                
                if total > 400:
                    print()
                    print("✓ Got real confusion matrix values!")
                else:
                    print()
                    print("⚠ Total seems low - possible issue")
            else:
                print("❌ All values are ZERO - this is the bug!")
        
        print()
        
    except Exception as e:
        print(f"❌ EXCEPTION: {e}")
        import traceback
        traceback.print_exc()
        print()

print("=" * 80)
print("TEST COMPLETE")
print("=" * 80)
print()
print("What to look for in the debug output:")
print("  1. Does it find predictive relations?")
print("  2. What is the iv_statespace calculation?")
print("  3. How many keys_found in fit table?")
print("  4. How many input_counter in input table?")
print("  5. Are the raw TN/FP/FN/TP values correct before returning?")
print()
