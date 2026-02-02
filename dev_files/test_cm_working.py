#!/usr/bin/env python3
"""
Test confusion matrix with models that are known to work
"""
import pyoccam

print("="*70)
print("CONFUSION MATRIX TEST - CORRECT MODELS")
print("="*70)

# Initialize
manager = pyoccam.VBMManager()
if not manager.init_from_command_line(["occam", "dementia05.txt"]):
    print("❌ Failed to load data")
    exit(1)

print("✓ Data loaded: dementia05.txt")
print()

# Models to test - these have predictive components
test_models = [
    "IV:ApZ",        # Ap predicts Z
    "IV:SxZ",        # Sx predicts Z
    "IV:EdZ",        # Ed predicts Z
    "IV:ApSxZ",      # ApSx predicts Z
    "IV:ApZ:EdZ",
]

for model_name in test_models:
    print(f"\nTesting: {model_name}")
    print("-" * 70)
    
    cm = manager.get_confusion_matrix(model_name, "0")
    
    if "error" in cm:
        print(f"  ❌ ERROR: {cm['error']}")
    elif cm['TP'] == 0 and cm['TN'] == 0:
        print(f"  ⚠️  All zeros (unexpected)")
    else:
        print(f"  ✓ SUCCESS!")
        print(f"    TN={cm['TN']:.0f}  FP={cm['FP']:.0f}")
        print(f"    FN={cm['FN']:.0f}  TP={cm['TP']:.0f}")
        print(f"    Accuracy: {cm['accuracy']:.3f}")
        print(f"    Sensitivity: {cm['sensitivity']:.3f}")
        print(f"    Specificity: {cm['specificity']:.3f}")

print()
print("="*70)
print("KEY INSIGHT:")
print("="*70)
print()
print("IV:ApZ means: Ap and Z are INDEPENDENT (no prediction)")
print("IV:Ap:Z means: Ap → Z (Ap PREDICTS Z)")
print()
print("Confusion matrices only work with predictive models!")
