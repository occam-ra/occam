#!/usr/bin/env python
"""
Check if statistics are being calculated correctly
"""

import pyoccam2
import math

def check_statistics():
    """Verify statistics calculation for models"""
    
    print("=" * 70)
    print("STATISTICS CALCULATION CHECK")
    print("=" * 70)
    
    # Initialize manager
    manager = pyoccam2.VBMManager()
    success = manager.init_from_command_line(["occam", "dementia05.txt"])
    
    if not success:
        print("ERROR: Failed to load data")
        return
    
    sample_size = manager.get_sample_size()
    print(f"\nSample size: {sample_size}")
    
    # Create reference model
    print("\n1. Reference Model (IV:Z):")
    print("-" * 50)
    ref = manager.make_model("IV:Z", True)
    print(f"  H = {ref.h:.4f}")
    print(f"  df = {ref.df:.0f}")
    print(f"  lr = {ref.lr:.4f}")
    print(f"  aic = {ref.aic:.4f}")
    print(f"  bic = {ref.bic:.4f}")
    print(f"  alpha = {ref.alpha:.4f}")
    print(f"  information = {ref.information:.4f}")
    
    # Create test models and check statistics
    print("\n2. Test Models with Manual BIC Calculation:")
    print("-" * 50)
    
    test_models = [
        "IV:ApZ",   # APOE - should be best
        "IV:EdZ",   # Education - should be good
        "IV:AgZ",   # Age - should be okay
        "IV:PZ",    # rs3865444 - should be poor
        "IV:NZ",    # rs3764650 - should be poor
    ]
    
    print(f"{'Model':<10} {'H':<8} {'df':<6} {'LR':<8} {'AIC':<10} {'BIC':<10} {'Info':<8} {'dBIC':<8}")
    print("-" * 90)
    
    for model_name in test_models:
        model = manager.make_model(model_name, True)
        
        # Calculate what dBIC should be
        expected_dbic = ref.bic - model.bic
        
        print(f"{model_name:<10} {model.h:<8.4f} {model.df:<6.0f} {model.lr:<8.2f} "
              f"{model.aic:<10.2f} {model.bic:<10.2f} {model.information:<8.4f} {expected_dbic:<8.2f}")
    
    # Now run search and see what it reports
    print("\n3. Search Results (Level 1):")
    print("-" * 50)
    
    search_report = manager.generate_search_report("loopless-up", levels=1, width=18)
    kept = manager.get_kept_models()
    
    level1 = [m for m in kept if m.level == 1]
    level1.sort(key=lambda m: m.dbic, reverse=True)
    
    print(f"{'Model':<10} {'H':<8} {'df':<6} {'LR':<8} {'AIC':<10} {'BIC':<10} {'Info':<8} {'dBIC':<8} {'dAIC':<8}")
    print("-" * 100)
    
    for model in level1[:5]:
        print(f"{model.name:<10} {model.h:<8.4f} {model.df:<6.0f} {model.lr:<8.2f} "
              f"{model.aic:<10.2f} {model.bic:<10.2f} {model.information:<8.4f} "
              f"{model.dbic:<8.2f} {model.daic:<8.2f}")
    
    # Check the calculation
    print("\n4. Diagnosis:")
    print("-" * 50)
    
    # Get the IV:PZ model from search
    search_pz = next((m for m in level1 if m.name == "IV:PZ"), None)
    manual_pz = manager.make_model("IV:PZ", True)
    
    if search_pz:
        print(f"Manual IV:PZ:")
        print(f"  BIC = {manual_pz.bic:.4f}")
        print(f"  Expected dBIC = {ref.bic - manual_pz.bic:.4f}")
        print()
        print(f"Search IV:PZ:")
        print(f"  BIC = {search_pz.bic:.4f}")
        print(f"  Reported dBIC = {search_pz.dbic:.4f}")
        print()
        
        # Check the math
        if abs(manual_pz.bic - search_pz.bic) < 0.01:
            print("✓ BIC values match between manual and search")
        else:
            print("✗ BIC values DON'T match!")
            
        calc_dbic = ref.bic - search_pz.bic
        if abs(calc_dbic - search_pz.dbic) < 0.01:
            print("✓ dBIC calculation is correct (ref.bic - model.bic)")
        else:
            print("✗ dBIC calculation is WRONG!")
            print(f"  Should be: {ref.bic:.4f} - {search_pz.bic:.4f} = {calc_dbic:.4f}")
            print(f"  But got: {search_pz.dbic:.4f}")
    
    # Check why wrong models are being selected
    print("\n5. Model Selection Analysis:")
    print("-" * 50)
    
    # Manually calculate statistics for all single-variable models
    print("All single-variable models:")
    print(f"{'Var':<10} {'Model':<10} {'Info':<8} {'BIC':<10} {'dBIC':<8} {'Rank'}")
    print("-" * 60)
    
    variables = manager.get_variable_list()
    all_singles = []
    
    for i, var_name in enumerate(variables[:-1]):  # Skip CaseControl
        # Need to figure out the abbreviation
        # This is a hack based on position
        if i == 0: abbrev = "Ap"
        elif i == 1: abbrev = "Sx"
        elif i == 2: abbrev = "Ed"
        elif i == 3: abbrev = "Ag"
        elif i < 16: abbrev = chr(ord('A') + i - 4)  # A through L
        elif i == 16: abbrev = "N"
        elif i == 17: abbrev = "P"
        else: continue
        
        model_name = f"IV:{abbrev}Z"
        try:
            model = manager.make_model(model_name, True)
            dbic = ref.bic - model.bic
            all_singles.append((var_name, model_name, model.information, model.bic, dbic))
        except:
            pass
    
    # Sort by dBIC (what search should use)
    all_singles.sort(key=lambda x: x[4], reverse=True)
    
    for rank, (var_name, model_name, info, bic, dbic) in enumerate(all_singles[:10], 1):
        print(f"{var_name:<10} {model_name:<10} {info:<8.4f} {bic:<10.2f} {dbic:<8.2f} #{rank}")
    
    print("\nConclusion:")
    print("-" * 50)
    
    # Check if IV:ApZ should be best
    apz_rank = next((i for i, (_, name, _, _, _) in enumerate(all_singles, 1) if name == "IV:ApZ"), None)
    pz_rank = next((i for i, (_, name, _, _, _) in enumerate(all_singles, 1) if name == "IV:PZ"), None)
    
    if apz_rank and pz_rank:
        if apz_rank < pz_rank:
            print(f"✓ IV:ApZ (APOE) should rank #{apz_rank}, IV:PZ ranks #{pz_rank}")
            print("  So the search is selecting the WRONG models!")
        else:
            print(f"✗ IV:PZ actually ranks better (#{pz_rank}) than IV:ApZ (#{apz_rank})")
            print("  The BIC calculation might be wrong.")

if __name__ == "__main__":
    check_statistics()