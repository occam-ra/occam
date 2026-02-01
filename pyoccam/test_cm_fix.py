#!/usr/bin/env python3
"""
Quick test to verify the confusion matrix regex fix is working
"""

import _pyoccam

print("="*60)
print("TESTING CONFUSION MATRIX FIX (v0.1.3)")
print("="*60)

# Initialize and load data
print("\n1. Loading data...")
manager = pyoccam.VBMManager()
manager.init_from_command_line(["occam", "dementia05.txt"])
print("✓ Data loaded")

# Quick search
print("\n2. Running quick search...")
manager.generate_search_report("loopless-up", 3, 3, False)
print("✓ Search complete")

# Get best model
best_model = manager.get_best_model_by_bic()
print(f"\n3. Best model: {best_model}")

# Test confusion matrix
print("\n4. Testing confusion matrix extraction...")
print("-"*40)

try:
    cm = manager.get_confusion_matrix(best_model, "0")
    
    # Check if we got actual values (not all zeros)
    has_values = any([cm['TN'] > 0, cm['FP'] > 0, cm['FN'] > 0, cm['TP'] > 0])
    
    if has_values:
        print("✅ SUCCESS! Confusion matrix extracted:")
        print(f"   TN = {cm['TN']:.0f}")
        print(f"   FP = {cm['FP']:.0f}")
        print(f"   FN = {cm['FN']:.0f}")
        print(f"   TP = {cm['TP']:.0f}")
        print(f"   Accuracy = {cm['accuracy']:.3f} ({cm['accuracy']*100:.1f}%)")
        print(f"   F1 Score = {cm['f1_score']:.3f}")
        print("\n🎉 The regex fix worked! PyOccam 0.1.3 is ready!")
    else:
        print("❌ FAILED: All values are zero")
        print("   The regex pattern may still need adjustment")
        print(f"   Debug: {cm}")
        
except Exception as e:
    print(f"❌ ERROR: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*60)
