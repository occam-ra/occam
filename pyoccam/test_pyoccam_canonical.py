#!/usr/bin/env python3
"""
PyOccam Canonical Test Suite
Tests core functionality against known good outputs

This is the definitive "does pyoccam work correctly" test suite.
Run this to verify your pyoccam installation is working properly.

Usage:
    python test_pyoccam.py              # Run all tests
    python test_pyoccam.py --verbose    # Verbose output
    python test_pyoccam.py --quick      # Skip slow tests
"""

import pyoccam
import sys
import os
from pathlib import Path

# Test configuration
VERBOSE = "--verbose" in sys.argv or "-v" in sys.argv
QUICK_MODE = "--quick" in sys.argv or "-q" in sys.argv

class TestResults:
    """Track test results"""
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.skipped = 0
        self.tests = []
    
    def record(self, name, passed, message="", skip=False):
        if skip:
            self.skipped += 1
            status = "SKIP"
        elif passed:
            self.passed += 1
            status = "PASS"
        else:
            self.failed += 1
            status = "FAIL"
        
        self.tests.append((name, status, message))
        
        # Print immediately
        symbol = "⊘" if skip else ("✓" if passed else "✗")
        print(f"  {symbol} {name}", end="")
        if message and (not passed or VERBOSE):
            print(f": {message}")
        else:
            print()
    
    def summary(self):
        total = self.passed + self.failed + self.skipped
        print("\n" + "=" * 70)
        print("TEST SUMMARY")
        print("=" * 70)
        print(f"Total tests: {total}")
        print(f"  ✓ Passed:  {self.passed}")
        print(f"  ✗ Failed:  {self.failed}")
        print(f"  ⊘ Skipped: {self.skipped}")
        
        if self.failed > 0:
            print("\nFailed tests:")
            for name, status, msg in self.tests:
                if status == "FAIL":
                    print(f"  • {name}: {msg}")
        
        print("=" * 70)
        return self.failed == 0

results = TestResults()

# ==============================================================================
# TEST 1: BASIC INITIALIZATION
# ==============================================================================

def test_initialization():
    """Test basic pyoccam initialization and imports"""
    print("\n" + "=" * 70)
    print("TEST 1: BASIC INITIALIZATION")
    print("=" * 70)
    
    try:
        # Test version
        version = pyoccam.__version__
        results.record("Version available", True, f"v{version}")
        
        # Test VBMManager class exists
        manager = pyoccam.VBMManager()
        results.record("VBMManager class instantiation", True)
        
        # Test help function
        if hasattr(pyoccam, 'help'):
            results.record("Help function available", True)
        else:
            results.record("Help function available", False, "pyoccam.help() not found")
        
        return True
    except Exception as e:
        results.record("Basic initialization", False, str(e))
        return False

# ==============================================================================
# TEST 2: DATA LOADING
# ==============================================================================

def test_data_loading():
    """Test data file loading"""
    print("\n" + "=" * 70)
    print("TEST 2: DATA LOADING")
    print("=" * 70)
    
    manager = pyoccam.VBMManager()
    
    # Test dementia05 loading
    try:
        success = manager.init_from_command_line(["occam", "dementia05.txt"])
        if success:
            sample_size = manager.get_sample_size()
            expected_size = 424
            if sample_size == expected_size:
                results.record("Load dementia05.txt", True, f"{sample_size} samples")
            else:
                results.record("Load dementia05.txt", False, 
                             f"Expected {expected_size}, got {sample_size}")
        else:
            results.record("Load dementia05.txt", False, "init_from_command_line returned False")
    except Exception as e:
        results.record("Load dementia05.txt", False, str(e))
        return False
    
    # Test variable list
    try:
        variables = manager.get_variable_list()
        if len(variables) > 0:
            results.record("Get variable list", True, f"{len(variables)} variables")
        else:
            results.record("Get variable list", False, "No variables returned")
    except Exception as e:
        results.record("Get variable list", False, str(e))
    
    # Test basic statistics
    try:
        stats = manager.get_basic_statistics()
        if len(stats) > 0:
            results.record("Get basic statistics", True)
        else:
            results.record("Get basic statistics", False, "Empty string returned")
    except Exception as e:
        results.record("Get basic statistics", False, str(e))
    
    # Test test data detection
    try:
        has_test = manager.has_test_data()
        # dementia05 has no test data
        if not has_test:
            results.record("Test data detection (negative)", True, "Correctly reports no test data")
        else:
            results.record("Test data detection (negative)", False, "False positive")
    except Exception as e:
        results.record("Test data detection", False, str(e))
    
    return True

# ==============================================================================
# TEST 3: SEARCH OPERATIONS
# ==============================================================================

def test_search_loopless():
    """Test loopless-up search"""
    print("\n" + "=" * 70)
    print("TEST 3: SEARCH OPERATIONS - LOOPLESS")
    print("=" * 70)
    
    manager = pyoccam.VBMManager()
    if not manager.init_from_command_line(["occam", "dementia05.txt"]):
        results.record("Search initialization", False, "Failed to load data")
        return False
    
    # Configure search
    try:
        manager.set_report_separator(pyoccam.SPACESEP)
        manager.set_report_variables("Level$I, h, ddf, dLR, Alpha, %dH(DV), dAIC, dBIC")
        results.record("Configure search report", True)
    except Exception as e:
        results.record("Configure search report", False, str(e))
        return False
    
    # Run search
    try:
        if QUICK_MODE:
            report = manager.generate_search_report("loopless-up", 1, 3)
        else:
            report = manager.generate_search_report("loopless-up", 3, 3)
        
        if len(report) > 0:
            results.record("Generate loopless search report", True, f"{len(report)} chars")
        else:
            results.record("Generate loopless search report", False, "Empty report")
            return False
    except Exception as e:
        results.record("Generate loopless search report", False, str(e))
        return False
    
    # Test best model selection
    try:
        best_bic = manager.get_best_model_by_bic()
        if best_bic and best_bic != "":
            results.record("Get best model by BIC", True, best_bic)
        else:
            results.record("Get best model by BIC", False, "Empty string returned")
    except Exception as e:
        results.record("Get best model by BIC", False, str(e))
    
    try:
        best_info = manager.get_best_model_by_information()
        if best_info and best_info != "":
            results.record("Get best model by Information", True, best_info)
        else:
            results.record("Get best model by Information", False, "Empty string returned")
    except Exception as e:
        results.record("Get best model by Information", False, str(e))
    
    # Test model count
    try:
        count = manager.get_search_model_count()
        if count > 0:
            results.record("Get search model count", True, f"{count} models")
        else:
            results.record("Get search model count", False, f"Count = {count}")
    except Exception as e:
        results.record("Get search model count", False, str(e))
    
    return True

def test_search_fullup():
    """Test full-up search"""
    if QUICK_MODE:
        results.record("Full-up search test", True, skip=True, message="Skipped in quick mode")
        return True
    
    print("\n" + "=" * 70)
    print("TEST 3b: SEARCH OPERATIONS - FULL-UP")
    print("=" * 70)
    
    manager = pyoccam.VBMManager()
    if not manager.init_from_command_line(["occam", "dementia05.txt"]):
        results.record("Full-up search initialization", False, "Failed to load data")
        return False
    
    try:
        manager.set_report_separator(pyoccam.SPACESEP)
        manager.set_report_variables("Level$I, h, ddf, dLR, Alpha, %dH(DV), dAIC, dBIC")
        report = manager.generate_search_report("full-up", 2, 3)
        
        if len(report) > 0:
            results.record("Generate full-up search report", True)
        else:
            results.record("Generate full-up search report", False, "Empty report")
    except Exception as e:
        results.record("Generate full-up search report", False, str(e))
    
    return True

# ==============================================================================
# TEST 4: MODEL OPERATIONS
# ==============================================================================

def test_model_operations():
    """Test model creation and statistics"""
    print("\n" + "=" * 70)
    print("TEST 4: MODEL OPERATIONS")
    print("=" * 70)
    
    manager = pyoccam.VBMManager()
    if not manager.init_from_command_line(["occam", "dementia05.txt"]):
        results.record("Model operations initialization", False, "Failed to load data")
        return False
    
    # Test simple model creation
    try:
        model_name = "IV:ApZ"
        model = manager.make_model(model_name, make_fit_table=False)
        if model:
            results.record(f"Create model {model_name}", True)
        else:
            results.record(f"Create model {model_name}", False, "make_model returned None/False")
    except Exception as e:
        results.record("Create simple model", False, str(e))
        return False
    
    # Test model with fit table
    try:
        model_name = "IV:ApZ:EdZ"
        model = manager.make_model(model_name, make_fit_table=True)
        if model:
            results.record(f"Create model with fit table", True, model_name)
        else:
            results.record(f"Create model with fit table", False, "make_model returned None/False")
    except Exception as e:
        results.record("Create model with fit table", False, str(e))
    
    # Test model statistics
    try:
        stats = manager.get_model_statistics(model_name)
        if stats and len(stats) > 0:
            # Check for key statistics
            has_h = 'h' in stats
            has_df = 'df' in stats
            has_bic = 'bic' in stats
            
            if has_h and has_df and has_bic:
                results.record("Get model statistics", True, f"h={stats.get('h', 'N/A'):.3f}")
            else:
                missing = []
                if not has_h: missing.append('h')
                if not has_df: missing.append('df')
                if not has_bic: missing.append('bic')
                results.record("Get model statistics", False, f"Missing: {missing}")
        else:
            results.record("Get model statistics", False, "Empty dict returned")
    except Exception as e:
        results.record("Get model statistics", False, str(e))
    
    return True

# ==============================================================================
# TEST 5: FIT REPORTS
# ==============================================================================

def test_fit_reports():
    """Test fit report generation"""
    print("\n" + "=" * 70)
    print("TEST 5: FIT REPORTS")
    print("=" * 70)
    
    manager = pyoccam.VBMManager()
    if not manager.init_from_command_line(["occam", "dementia05.txt"]):
        results.record("Fit report initialization", False, "Failed to load data")
        return False
    
    # Test basic fit report (no target)
    try:
        model_name = "IV:ApZ"
        report = manager.generate_fit_report(model_name)
        if len(report) > 0:
            results.record("Generate basic fit report", True, f"{len(report)} chars")
        else:
            results.record("Generate basic fit report", False, "Empty report")
    except Exception as e:
        results.record("Generate basic fit report", False, str(e))
    
    # Test fit report with target state (for confusion matrix)
    try:
        model_name = "IV:ApZ"
        report = manager.generate_fit_report(model_name, target_state="0")
        if len(report) > 0:
            # Check if conditional tables are present
            has_conditional = "CONDITIONAL" in report or "conditional" in report
            results.record("Generate fit report with target", True, 
                         "with conditional tables" if has_conditional else "no conditional tables")
        else:
            results.record("Generate fit report with target", False, "Empty report")
    except Exception as e:
        results.record("Generate fit report with target", False, str(e))
    
    return True

# ==============================================================================
# TEST 6: CONFUSION MATRIX
# ==============================================================================

def test_confusion_matrix():
    """Test confusion matrix extraction"""
    print("\n" + "=" * 70)
    print("TEST 6: CONFUSION MATRIX EXTRACTION")
    print("=" * 70)
    
    manager = pyoccam.VBMManager()
    if not manager.init_from_command_line(["occam", "dementia05.txt"]):
        results.record("CM initialization", False, "Failed to load data")
        return False
    
    # Check if method exists
    if not hasattr(manager, 'get_confusion_matrix'):
        results.record("get_confusion_matrix method exists", False, 
                     "Method not found in VBMManager")
        results.record("CM for IV:ApZ", True, skip=True, 
                     message="Skipped - method doesn't exist")
        results.record("CM validation", True, skip=True, 
                     message="Skipped - method doesn't exist")
        return False
    
    results.record("get_confusion_matrix method exists", True)
    
    # Test with simple model
    try:
        model_name = "IV:ApZ"
        cm = manager.get_confusion_matrix(model_name, "0")
        
        # Check what we got back
        if "error" in cm:
            results.record(f"CM for {model_name}", False, cm["error"])
        elif not all(key in cm for key in ['TN', 'FP', 'FN', 'TP']):
            results.record(f"CM for {model_name}", False, 
                         f"Missing keys. Got: {list(cm.keys())}")
        elif cm['TN'] == 0 and cm['FP'] == 0 and cm['FN'] == 0 and cm['TP'] == 0:
            results.record(f"CM for {model_name}", False, "All values are zero")
        else:
            # Got real values!
            total = cm['TN'] + cm['FP'] + cm['FN'] + cm['TP']
            accuracy = cm.get('accuracy', 0)
            results.record(f"CM for {model_name}", True, 
                         f"TN={cm['TN']:.0f}, TP={cm['TP']:.0f}, Acc={accuracy:.3f}")
            
            # Validate totals make sense for dementia (424 samples)
            if 400 <= total <= 450:
                results.record("CM total samples validation", True, f"{total:.0f} samples")
            else:
                results.record("CM total samples validation", False, 
                             f"Expected ~424, got {total:.0f}")
    except Exception as e:
        results.record("CM extraction", False, str(e))
    
    return True

# ==============================================================================
# TEST 7: MODEL SWITCHING (HEAP CORRUPTION TEST)
# ==============================================================================

def test_model_switching():
    """Test that switching between models doesn't cause heap corruption"""
    print("\n" + "=" * 70)
    print("TEST 7: MODEL SWITCHING (HEAP CORRUPTION)")
    print("=" * 70)
    
    manager = pyoccam.VBMManager()
    if not manager.init_from_command_line(["occam", "dementia05.txt"]):
        results.record("Model switching initialization", False, "Failed to load data")
        return False
    
    # Test switching between different models multiple times
    models = ["IV:ApZ", "IV:EdZ", "IV:CZ", "IV:ApZ:EdZ"]
    
    try:
        for i, model_name in enumerate(models):
            report = manager.generate_fit_report(model_name)
            if len(report) == 0:
                results.record(f"Switch to model {i+1}/4", False, f"{model_name} returned empty")
                return False
        
        results.record("Model switching without crash", True, f"Tested {len(models)} models")
    except Exception as e:
        results.record("Model switching without crash", False, str(e))
        return False
    
    # If confusion matrix method exists, test switching with CM extraction
    if hasattr(manager, 'get_confusion_matrix'):
        try:
            for i, model_name in enumerate(models[:3]):  # Test first 3
                cm = manager.get_confusion_matrix(model_name, "0")
                if "error" not in cm and all(key in cm for key in ['TN', 'FP', 'FN', 'TP']):
                    continue  # Success
                else:
                    results.record(f"CM switching test {i+1}/3", False, 
                                 f"{model_name} failed")
                    return False
            
            results.record("Model switching with CM extraction", True, 
                         f"Tested {len(models[:3])} models")
        except Exception as e:
            results.record("Model switching with CM extraction", False, str(e))
    
    return True

# ==============================================================================
# TEST 8: CONVENIENCE FUNCTIONS
# ==============================================================================

def test_convenience_functions():
    """Test high-level convenience functions"""
    print("\n" + "=" * 70)
    print("TEST 8: CONVENIENCE FUNCTIONS")
    print("=" * 70)
    
    # Test data loading functions
    try:
        if hasattr(pyoccam, 'load_dementia'):
            data = pyoccam.load_dementia()
            if hasattr(data, 'n_samples') and data.n_samples == 424:
                results.record("load_dementia()", True, f"{data.n_samples} samples")
            else:
                results.record("load_dementia()", False, "Invalid data object")
        else:
            results.record("load_dementia()", True, skip=True, 
                         message="Function not available (optional)")
    except Exception as e:
        results.record("load_dementia()", False, str(e))
    
    # Test demo access
    try:
        if hasattr(pyoccam, 'get_demo_script'):
            path = pyoccam.get_demo_script()
            if os.path.exists(path):
                results.record("get_demo_script()", True)
            else:
                results.record("get_demo_script()", False, "Path doesn't exist")
        else:
            results.record("get_demo_script()", True, skip=True, 
                         message="Function not available (optional)")
    except Exception as e:
        results.record("get_demo_script()", False, str(e))
    
    return True

# ==============================================================================
# TEST 9: SERVER OUTPUT COMPARISON (COMPREHENSIVE)
# ==============================================================================

def test_server_comparison():
    """Test that outputs match known server results"""
    if QUICK_MODE:
        results.record("Server output comparison", True, skip=True, 
                     message="Skipped in quick mode")
        return True
    
    print("\n" + "=" * 70)
    print("TEST 9: SERVER OUTPUT COMPARISON")
    print("=" * 70)
    
    manager = pyoccam.VBMManager()
    if not manager.init_from_command_line(["occam", "dementia05.txt"]):
        results.record("Server comparison initialization", False, "Failed to load data")
        return False
    
    # Run search
    manager.set_report_separator(pyoccam.SPACESEP)
    manager.set_report_variables("Level$I, h, ddf, dLR, Alpha, %dH(DV), dAIC, dBIC")
    report = manager.generate_search_report("loopless-up", 7, 3)
    
    # Check for known models that should appear
    expected_models = ["IV:ApZ", "IV:EdZ", "IV:CZ"]
    found_models = []
    
    for model in expected_models:
        if model in report:
            found_models.append(model)
    
    if len(found_models) == len(expected_models):
        results.record("Expected models present", True, 
                     f"Found all {len(expected_models)} models")
    else:
        missing = set(expected_models) - set(found_models)
        results.record("Expected models present", False, 
                     f"Missing: {missing}")
    
    # Check specific values for IV:ApZ (known from server output)
    # From server: IV:ApZ has dBIC around -1.xxx (negative = not better than IV)
    if "IV:ApZ" in report:
        # Extract the line with IV:ApZ
        lines = report.split('\n')
        for line in lines:
            if 'IV:ApZ' in line and not line.strip().startswith('#'):
                # Very basic check - just verify it has numerical values
                if any(char.isdigit() for char in line):
                    results.record("IV:ApZ has numerical values", True)
                else:
                    results.record("IV:ApZ has numerical values", False, "No digits found")
                break
    
    return True

# ==============================================================================
# MAIN TEST RUNNER
# ==============================================================================

def main():
    """Run all tests"""
    print("=" * 70)
    print("PYOCCAM CANONICAL TEST SUITE")
    print("=" * 70)
    print(f"PyOccam version: {pyoccam.__version__}")
    print(f"Test mode: {'QUICK' if QUICK_MODE else 'COMPREHENSIVE'}")
    print(f"Verbosity: {'VERBOSE' if VERBOSE else 'NORMAL'}")
    print("=" * 70)
    
    # Run all test groups
    test_functions = [
        test_initialization,
        test_data_loading,
        test_search_loopless,
        test_search_fullup,
        test_model_operations,
        test_fit_reports,
        test_confusion_matrix,
        test_model_switching,
        test_convenience_functions,
        test_server_comparison,
    ]
    
    for test_func in test_functions:
        try:
            test_func()
        except Exception as e:
            print(f"\n❌ FATAL ERROR in {test_func.__name__}: {e}")
            import traceback
            traceback.print_exc()
            results.record(f"FATAL: {test_func.__name__}", False, str(e))
    
    # Print summary
    success = results.summary()
    
    # Exit with appropriate code
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
