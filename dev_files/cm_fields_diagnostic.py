#!/usr/bin/env python3
"""
Simple diagnostic: What fields does get_confusion_matrix actually return?
"""
import pyoccam
import json

print("="*70)
print("CONFUSION MATRIX FIELDS DIAGNOSTIC")
print("="*70)

# Test with dementia05 (no test data)
print("\n### Dataset WITHOUT test data (dementia05) ###\n")
manager1 = pyoccam.VBMManager()
if manager1.init_from_command_line(["occam", "dementia05.txt"]):
    print(f"Has test data: {manager1.has_test_data()}")
    
    cm = manager1.get_confusion_matrix("IV:ApZ", "0")
    
    print(f"\nReturned fields:")
    for key in sorted(cm.keys()):
        value = cm[key]
        if isinstance(value, float):
            print(f"  {key:20s} = {value:.6f}")
        else:
            print(f"  {key:20s} = {value}")
    
    print(f"\nChecking test-related fields:")
    print(f"  has_test_data    : {cm.get('has_test_data', 'NOT PRESENT')}")
    print(f"  test_TN          : {cm.get('test_TN', 'NOT PRESENT')}")
    print(f"  test_FP          : {cm.get('test_FP', 'NOT PRESENT')}")
    print(f"  test_FN          : {cm.get('test_FN', 'NOT PRESENT')}")
    print(f"  test_TP          : {cm.get('test_TP', 'NOT PRESENT')}")

# Try with a dataset that might have test data
print("\n\n### Attempting dataset WITH test data ###\n")
print("(If SY_sample file exists)")

try:
    manager2 = pyoccam.VBMManager()
    # Try various possible filenames
    test_files = [
        "SY_sample_pts_to_occam3_shuffle_split42_hdr.txt",
        "SY_sample.txt",
        "test_data.txt"
    ]
    
    loaded = False
    for test_file in test_files:
        try:
            if manager2.init_from_command_line(["occam", test_file]):
                print(f"✓ Loaded: {test_file}")
                print(f"  Has test data: {manager2.has_test_data()}")
                loaded = True
                
                # Try to get CM
                # Note: Need to know what models exist in this dataset
                # Common pattern would be IV:X:Y where Y is DV
                print(f"\n  Attempting to get CM for a model...")
                print(f"  (This might fail if we don't know the correct model name)")
                
                break
        except:
            continue
    
    if not loaded:
        print("  ℹ️  No test data file found - that's okay!")
        print("     To test with test data:")
        print("     1. Run OCCAM server with a train/test split")
        print("     2. Save the data file")
        print("     3. Update this script with the filename and model names")

except Exception as e:
    print(f"  ℹ️  {e}")

print("\n" + "="*70)
print("DIAGNOSTIC COMPLETE")
print("="*70)
print("""
Key Questions:
1. Are test_* fields present in the dictionary? (even if 0)
2. Is has_test_data field present?
3. What is the value of has_test_data?

Expected Behavior:
- If dataset has no test data:
  has_test_data = False
  test_TN/FP/FN/TP = 0 (or not present)

- If dataset has test data:
  has_test_data = True
  test_TN/FP/FN/TP = actual values from test set

Current Status:
- Check the output above to see what fields are actually returned
- If test_* fields are missing, they need to be added to the pybind11 wrapper
- If test_* fields are present but always 0, the C++ code needs to compute them
""")
