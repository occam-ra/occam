# debug_cm_windows.py
import pyoccam
import sys

print("CONFUSION MATRIX DEBUG (Windows)")
print("=" * 60)

# Initialize
manager = pyoccam.VBMManager()
if not manager.init_from_command_line(["occam", "dementia05.txt"]):
    print("Failed to load data")
    sys.exit(1)

# Get variable list
var_list = manager.get_variable_list()
print(f"Variables: {var_list}")
print(f"DV (last variable): {var_list[-1]}")

# Test the exact models from your search output
test_models = [
    ("IV:ApZ:EdZ:CZ", "0"),  # Best model from server
    ("IV:ApZ", "0"),  # Simple single predictor
    ("IV:EdZ", "0"),  # Another single predictor
]

print("\nTesting models from server output:")
print("-" * 60)

for model, target in test_models:
    print(f"\nModel: '{model}', Target: '{target}'")

    # Try to create the model first
    result = manager.make_model(model, True)
    if result.get('success'):
        print(f"  ✓ Model created: {result.get('name')}")
    else:
        print(f"  ✗ Model failed: {result.get('error')}")
        continue

    # Now try confusion matrix (this is where it hangs)
    print("  Attempting get_confusion_matrix...")
    try:
        cm = manager.get_confusion_matrix(model, target)
        if cm.get('has_values'):
            print(f"  ✓ CM computed: TN={cm['TN']:.0f}, FP={cm['FP']:.0f}")
        else:
            print(f"  ✗ CM error: {cm.get('error', 'Unknown')}")
    except Exception as e:
        print(f"  ✗ Exception: {e}")

print("\n" + "=" * 60)