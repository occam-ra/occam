"""
PyOccam v0.9.4 Test Suite
=========================
Tests the new test_split feature and related functionality.

Run from: D:\projects\occam
Command:  python test_v094.py
"""

import sys
import os
import tempfile
import csv

# Force local version
sys.path.insert(0, r"D:\projects\occam")

print("=" * 70)
print("PyOccam v0.9.4 Test Suite")
print("=" * 70)

# Track results
tests_passed = 0
tests_failed = 0

def test(name, condition, details=""):
    global tests_passed, tests_failed
    if condition:
        print(f"✓ PASS: {name}")
        tests_passed += 1
    else:
        print(f"✗ FAIL: {name}")
        if details:
            print(f"        {details}")
        tests_failed += 1

# ===========================================================================
# TEST 1: Import and version check
# ===========================================================================
print("\n--- Test 1: Import and Version ---")

try:
    import pyoccam
    test("Import pyoccam", True)
    test("Version is 0.9.4", pyoccam.__version__ == "0.9.4", 
         f"Got {pyoccam.__version__}")
    print(f"    Loaded from: {pyoccam.__file__}")
except Exception as e:
    test("Import pyoccam", False, str(e))

# ===========================================================================
# TEST 2: Create test CSV data
# ===========================================================================
print("\n--- Test 2: Create Test CSV ---")

# Create a simple test CSV
test_csv = os.path.join(tempfile.gettempdir(), "pyoccam_test_v094.csv")
test_data = [
    ["var_a", "var_b", "var_c", "target"],
    ["0", "0", "low", "0"],
    ["0", "1", "low", "0"],
    ["1", "0", "high", "1"],
    ["1", "1", "high", "1"],
    ["0", "0", "med", "0"],
    ["0", "1", "med", "0"],
    ["1", "0", "low", "1"],
    ["1", "1", "low", "1"],
    ["0", "0", "high", "0"],
    ["0", "1", "high", "1"],
] * 10  # 100 rows total

try:
    with open(test_csv, 'w', newline='') as f:
        writer = csv.writer(f)
        for row in test_data:
            writer.writerow(row)
    test("Create test CSV", os.path.exists(test_csv))
    print(f"    Created: {test_csv}")
    print(f"    Rows: {len(test_data) - 1}")
except Exception as e:
    test("Create test CSV", False, str(e))

# ===========================================================================
# TEST 3: CSV conversion WITHOUT test split (baseline)
# ===========================================================================
print("\n--- Test 3: CSV Conversion (no split) ---")

try:
    output_file, data = pyoccam.make_occam_input_from_csv(
        test_csv,
        verbose=False
    )
    test("Conversion succeeds", data is not None)
    test("has_test_data is False", data.has_test_data == False,
         f"Got {data.has_test_data}")
    
    # Check file doesn't have :test section
    with open(output_file, 'r') as f:
        content = f.read()
    test("No :test section in file", ":test" not in content)
    
    os.remove(output_file)
except Exception as e:
    test("Conversion (no split)", False, str(e))

# ===========================================================================
# TEST 4: CSV conversion WITH test split
# ===========================================================================
print("\n--- Test 4: CSV Conversion (with 20% split) ---")

try:
    output_file, data = pyoccam.make_occam_input_from_csv(
        test_csv,
        test_split=0.2,
        random_state=42,
        verbose=False
    )
    test("Conversion with split succeeds", data is not None)
    test("has_test_data is True", data.has_test_data == True,
         f"Got {data.has_test_data}")
    
    # Check file HAS :test section
    with open(output_file, 'r') as f:
        content = f.read()
    test(":test section in file", ":test" in content)
    
    # Count lines in each section
    lines = content.split('\n')
    data_idx = None
    test_idx = None
    for i, line in enumerate(lines):
        if line.strip() == ':data':
            data_idx = i
        elif line.strip() == ':test':
            test_idx = i
    
    if data_idx and test_idx:
        train_lines = test_idx - data_idx - 1
        test_lines = len([l for l in lines[test_idx+1:] if l.strip()])
        print(f"    Train rows in file: {train_lines}")
        print(f"    Test rows in file: {test_lines}")
        test("Train/test ratio ~80/20", 
             0.15 < test_lines / (train_lines + test_lines) < 0.25,
             f"Got {test_lines/(train_lines+test_lines):.1%}")
    
    # Keep for next tests
    test_output_file = output_file
    test_data_obj = data
    
except Exception as e:
    test("Conversion with split", False, str(e))
    test_output_file = None
    test_data_obj = None

# ===========================================================================
# TEST 5: Reproducibility (same random_state = same split)
# ===========================================================================
print("\n--- Test 5: Reproducibility ---")

try:
    output1, data1 = pyoccam.make_occam_input_from_csv(
        test_csv, test_split=0.2, random_state=42, verbose=False)
    output2, data2 = pyoccam.make_occam_input_from_csv(
        test_csv, test_split=0.2, random_state=42, verbose=False)
    output3, data3 = pyoccam.make_occam_input_from_csv(
        test_csv, test_split=0.2, random_state=99, verbose=False)  # Different seed
    
    with open(output1, 'r') as f:
        content1 = f.read()
    with open(output2, 'r') as f:
        content2 = f.read()
    with open(output3, 'r') as f:
        content3 = f.read()
    
    test("Same seed = same output", content1 == content2)
    test("Different seed = different output", content1 != content3)
    
    os.remove(output1)
    os.remove(output2)
    os.remove(output3)
except Exception as e:
    test("Reproducibility", False, str(e))

# ===========================================================================
# TEST 6: Search and confusion matrix with test data
# ===========================================================================
print("\n--- Test 6: Search and Confusion Matrix ---")

if test_data_obj:
    try:
        manager = test_data_obj.manager
        report = manager.generate_search_report("loopless-up", 3, 3)
        test("Search completes", len(report) > 0)
        
        best = manager.get_best_model_by_bic()
        test("Get best model", best is not None and len(best) > 0,
             f"Got: {best}")
        print(f"    Best model: {best}")
        
        cm = manager.get_confusion_matrix(best, target_state="0")
        test("Confusion matrix has values", cm.get('has_values', False))
        
        # Check for train metrics
        test("Has train_accuracy", 'train_accuracy' in cm,
             f"Keys: {list(cm.keys())}")
        
        # Check for test metrics (this is the key new feature!)
        test("Has test_accuracy", 'test_accuracy' in cm,
             f"Keys: {list(cm.keys())}")
        
        if 'train_accuracy' in cm:
            print(f"    Train accuracy: {cm['train_accuracy']:.1%}")
        if 'test_accuracy' in cm:
            print(f"    Test accuracy:  {cm['test_accuracy']:.1%}")
            
    except Exception as e:
        test("Search and CM", False, str(e))
        import traceback
        traceback.print_exc()

# ===========================================================================
# TEST 7: Built-in datasets still work
# ===========================================================================
print("\n--- Test 7: Built-in Datasets ---")

try:
    dementia = pyoccam.load_dementia()
    test("load_dementia() works", dementia is not None)
    test("Dementia has expected samples", dementia.n_samples > 400)
except Exception as e:
    test("load_dementia()", False, str(e))

try:
    landslides = pyoccam.load_landslides()
    test("load_landslides() works", landslides is not None)
except Exception as e:
    test("load_landslides()", False, str(e))

# ===========================================================================
# TEST 8: CLI argument parsing (dry run)
# ===========================================================================
print("\n--- Test 8: CLI Module ---")

try:
    from pyoccam import __main__
    test("__main__.py imports", True)
    
    # Check the argument parser has new options
    import argparse
    # We can't easily test the full CLI without subprocess, but we can check imports
    test("CLI module has main()", hasattr(__main__, 'main'))
    test("CLI module has run_csv2occam()", hasattr(__main__, 'run_csv2occam'))
except Exception as e:
    test("CLI module", False, str(e))

# ===========================================================================
# TEST 9: Advanced demo exists and is valid Python
# ===========================================================================
print("\n--- Test 9: Advanced Demo ---")

demo_path = r"D:\projects\occam\pyoccam\pyoccam_demo_advanced.py"
try:
    test("Advanced demo exists", os.path.exists(demo_path))
    
    # Try to compile it (syntax check)
    with open(demo_path, 'r') as f:
        code = f.read()
    compile(code, demo_path, 'exec')
    test("Advanced demo syntax valid", True)
except SyntaxError as e:
    test("Advanced demo syntax", False, str(e))
except Exception as e:
    test("Advanced demo", False, str(e))

# ===========================================================================
# Cleanup
# ===========================================================================
print("\n--- Cleanup ---")
try:
    if os.path.exists(test_csv):
        os.remove(test_csv)
    if test_output_file and os.path.exists(test_output_file):
        os.remove(test_output_file)
    print("    Temp files removed")
except:
    pass

# ===========================================================================
# Summary
# ===========================================================================
print("\n" + "=" * 70)
print(f"RESULTS: {tests_passed} passed, {tests_failed} failed")
print("=" * 70)

if tests_failed == 0:
    print("\n🎉 All tests passed! Ready to build and push.")
    print("\nNext steps:")
    print("  1. .\\build_all_pythons2.bat")
    print("  2. git add -A")
    print('  3. git commit -m "v0.9.4: Add test_split to CSV converter, advanced demo"')
    print("  4. git push origin pyoccam-port")
else:
    print(f"\n⚠️  {tests_failed} test(s) failed. Please fix before pushing.")
    sys.exit(1)
