#!/usr/bin/env python
"""
Diagnose the model naming issue - why search returns wrong model names
"""

import pyoccam2

def diagnose_naming():
    """Compare manual model creation vs search results"""
    
    print("=" * 70)
    print("MODEL NAMING DIAGNOSIS")
    print("=" * 70)
    
    # Initialize manager
    manager = pyoccam2.VBMManager()
    success = manager.init_from_command_line(["occam", "dementia05.txt"])
    
    if not success:
        print("ERROR: Failed to load data")
        return
    
    # Get variables for reference
    variables = manager.get_variable_list()
    
    print("\n1. Variable Reference:")
    print("-" * 50)
    var_abbrevs = {
        0: ("APOE", "Ap"),
        1: ("Gender", "Sx"),
        2: ("Education", "Ed"),
        3: ("AgeLastExam", "Ag"),
        13: ("rs11193130", "K"),
        16: ("rs3764650", "N"),
        17: ("rs3865444", "P"),
        18: ("CaseControl", "Z")
    }
    
    for idx, (name, abbrev) in var_abbrevs.items():
        if idx < len(variables):
            print(f"  [{idx:2d}] {variables[idx]:<15} → {abbrev}")
    
    # Manually create and check statistics for what SHOULD be top models
    print("\n2. Manual Model Creation (What We Expect):")
    print("-" * 50)
    
    expected_models = [
        ("IV:ApZ", "APOE + CaseControl"),
        ("IV:EdZ", "Education + CaseControl"),
        ("IV:AgZ", "AgeLastExam + CaseControl"),
        ("IV:CZ", "rs7561528 + CaseControl"),
        ("IV:KZ", "rs11193130 + CaseControl"),
        ("IV:PZ", "rs3865444 + CaseControl"),
        ("IV:NZ", "rs3764650 + CaseControl"),
    ]
    
    manual_stats = {}
    for model_name, description in expected_models:
        model = manager.make_model(model_name, True)
        manual_stats[model_name] = {
            'h': model.h,
            'info': model.information,
            'aic': model.aic,
            'bic': model.bic,
            'description': description
        }
        print(f"  {model_name:<10} ({description:<30}) → Info={model.information:.4f}")
    
    # Run search and get results
    print("\n3. Search Results (What We Actually Get):")
    print("-" * 50)
    
    search_report = manager.generate_search_report("loopless-up", levels=1, width=18)
    kept = manager.get_kept_models()
    
    # Get Level 1 models
    level1_models = [m for m in kept if m.level == 1]
    level1_models.sort(key=lambda m: m.dbic, reverse=True)
    
    for model in level1_models[:7]:
        print(f"  {model.name:<10} → Info={model.information:.4f}, dBIC={model.dbic:.3f}, H={model.h:.4f}")
    
    # HYPOTHESIS: The model named "IV:PZ" in search has the statistics of "IV:ApZ"
    print("\n4. Hypothesis Test:")
    print("-" * 50)
    print("Theory: Search model 'IV:PZ' is actually APOE model with wrong name")
    print()
    
    # Compare statistics
    search_pz = next((m for m in level1_models if m.name == "IV:PZ"), None)
    manual_apz = manual_stats.get("IV:ApZ", {})
    manual_pz = manual_stats.get("IV:PZ", {})
    
    if search_pz:
        print(f"Search 'IV:PZ' statistics:")
        print(f"  H     = {search_pz.h:.4f}")
        print(f"  Info  = {search_pz.information:.4f}")
        print()
        print(f"Manual 'IV:ApZ' (APOE) statistics:")
        print(f"  H     = {manual_apz.get('h', 0):.4f}")
        print(f"  Info  = {manual_apz.get('info', 0):.4f}")
        print()
        print(f"Manual 'IV:PZ' (rs3865444) statistics:")
        print(f"  H     = {manual_pz.get('h', 0):.4f}")
        print(f"  Info  = {manual_pz.get('info', 0):.4f}")
        print()
        
        # Check which one matches
        h_diff_apoe = abs(search_pz.h - manual_apz.get('h', 0))
        h_diff_p = abs(search_pz.h - manual_pz.get('h', 0))
        
        if h_diff_apoe < 0.001:
            print("✓ CONFIRMED: Search 'IV:PZ' has APOE statistics!")
            print("  The model is correct but the name is wrong.")
        elif h_diff_p < 0.001:
            print("✗ Search 'IV:PZ' actually has rs3865444 statistics")
            print("  The statistics are wrong.")
        else:
            print("? Neither matches - something else is wrong")
    
    # Check all top models
    print("\n5. Full Diagnosis - Matching Search Models to Expected:")
    print("-" * 50)
    print(f"{'Search Name':<12} {'H':<8} {'Best Match':<12} {'Match H':<8} {'Status'}")
    print("-" * 50)
    
    for model in level1_models[:5]:
        best_match = None
        best_diff = 999
        
        for manual_name, stats in manual_stats.items():
            h_diff = abs(model.h - stats['h'])
            if h_diff < best_diff:
                best_diff = h_diff
                best_match = (manual_name, stats)
        
        if best_match and best_diff < 0.001:
            match_name, match_stats = best_match
            status = "✓ Match" if best_diff < 0.0001 else "~ Close"
            print(f"{model.name:<12} {model.h:<8.4f} {match_name:<12} {match_stats['h']:<8.4f} {status}")
        else:
            print(f"{model.name:<12} {model.h:<8.4f} {'???':<12} {'---':<8} ✗ No match")
    
    print("\n6. Conclusion:")
    print("-" * 50)
    
    if search_pz and h_diff_apoe < 0.001:
        print("The search IS finding the correct models (APOE, Education, etc.)")
        print("but Model::getPrintName() is returning the wrong variable abbreviations.")
        print("\nThe bug is in how model names are constructed, not in the search logic.")
        print("\nLikely issue: Model::getPrintName() is using the wrong variable")
        print("abbreviation lookup - possibly using variable index instead of the")
        print("actual variable's abbreviation.")
    else:
        print("Unable to determine the exact issue.")

if __name__ == "__main__":
    diagnose_naming()