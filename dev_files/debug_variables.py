#!/usr/bin/env python
"""
Debug script to check how OCCAM is loading variable abbreviations
"""

import pyoccam2

def check_variables():
    """Check variable loading and abbreviations"""
    
    print("=" * 70)
    print("OCCAM VARIABLE ABBREVIATION CHECK")
    print("=" * 70)
    
    # Initialize manager
    manager = pyoccam2.VBMManager()
    
    # Enable debug mode to see variable info
    manager.set_debug_mode(True)
    
    # Load data - this should show debug output
    print("\n1. Loading dementia05.txt...")
    print("-" * 50)
    success = manager.init_from_command_line(["occam", "dementia05.txt"])
    
    if not success:
        print("ERROR: Failed to load data")
        return
    
    # Get variable list
    variables = manager.get_variable_list()
    
    print("\n2. Variables Loaded:")
    print("-" * 50)
    print(f"Total variables: {len(variables)}")
    
    # Expected abbreviations from the data file
    expected = {
        "APOE": "Ap",
        "Gender": "Sx", 
        "Education": "Ed",
        "AgeLastExam": "Ag",
        "rs1801133": "A",
        "rs3818361": "B",
        "rs7561528": "C",
        "rs744373": "D",
        "rs6943822": "E",
        "rs4298437": "F",
        "rs7012010": "G",
        "rs11136000": "H",
        "rs10786998": "J",
        "rs11193130": "K",
        "rs610932": "L",
        "rs3851179": "M",
        "rs3764650": "N",
        "rs3865444": "P",
        "CaseControl": "Z"
    }
    
    print("\n3. Variable Name Mapping:")
    print("-" * 50)
    print(f"{'Variable Name':<15} {'Expected':<10} {'Status'}")
    print("-" * 50)
    
    for i, var_name in enumerate(variables):
        if var_name in expected:
            exp_abbrev = expected[var_name]
            print(f"{var_name:<15} {exp_abbrev:<10} ✓")
        else:
            print(f"{var_name:<15} {'???':<10} ✗ UNEXPECTED")
    
    # Test creating models with proper abbreviations
    print("\n4. Testing Model Creation:")
    print("-" * 50)
    
    test_models = [
        "IV:Z",           # Independence model
        "IV:ApZ",         # APOE with outcome
        "IV:EdZ",         # Education with outcome
        "IV:AgZ",         # Age with outcome
        "IV:SxZ",         # Gender with outcome
        "IV:ApSxZ",       # APOE and Gender
        "IV:PZ",          # rs3865444 (what we're seeing)
        "IV:NZ",          # rs3764650 (what we're seeing)
    ]
    
    for model_name in test_models:
        try:
            model = manager.make_model(model_name, True)
            if model.name != "ERROR":
                print(f"  {model_name:<15} → H={model.h:.4f}, Info={model.information:.4f}")
            else:
                print(f"  {model_name:<15} → ERROR: Could not create model")
        except Exception as e:
            print(f"  {model_name:<15} → EXCEPTION: {e}")
    
    # Run a quick 1-level search to see what comes out
    print("\n5. Running 1-level search:")
    print("-" * 50)
    
    manager.set_debug_mode(False)  # Turn off debug for search
    search_report = manager.generate_search_report("loopless-up", levels=1, width=18)
    
    # Get kept models
    kept = manager.get_kept_models()
    
    print(f"Models at Level 1: {len(kept) - 1} (excluding reference)")
    print("\nTop 5 by dBIC:")
    
    # Sort by dBIC
    level1_models = [m for m in kept if m.level == 1]
    level1_models.sort(key=lambda m: m.dbic, reverse=True)
    
    for i, model in enumerate(level1_models[:5], 1):
        print(f"  {i}. {model.name:<10} dBIC={model.dbic:8.3f}, dAIC={model.daic:8.3f}")
    
    print("\nExpected top models (from server):")
    print("  1. IV:ApZ     (APOE)")
    print("  2. IV:EdZ     (Education)")  
    print("  3. IV:AgZ     (AgeLastExam)")

if __name__ == "__main__":
    check_variables()