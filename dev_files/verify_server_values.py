#!/usr/bin/env python
"""
Verify our calculations match the server output
Based on server_search_output_dementia05_loopless.PDF and full-up.PDF
"""

import pyoccam2

def verify_server_match():
    """Check if our values match the server output"""
    
    print("=" * 80)
    print("VERIFYING AGAINST SERVER OUTPUT")
    print("=" * 80)
    
    # Initialize manager
    manager = pyoccam2.VBMManager()
    manager.set_debug_mode(False)
    
    # Initialize with the same data file
    success = manager.init_from_command_line(["occam", "dementia05.txt"])
    if not success:
        print("ERROR: Failed to load data")
        return
    
    # According to the server output screenshots:
    # Best Model by dBIC at Level 1:
    # - IV:ApZ (APOE) should have high positive dBIC
    # - IV:EdZ (Education) should be second
    # - SNP variables should have low or negative dBIC
    
    print("\nExpected from server (loopless-up, Level 1):")
    print("-" * 50)
    print("Top models should be:")
    print("1. IV:ApZ (APOE)")
    print("2. IV:EdZ (Education)")  
    print("3. IV:AgZ (Age)")
    print()
    
    # Run search
    print("Running search...")
    report = manager.generate_search_report("loopless-up", levels=1, width=18)
    
    # Get results
    kept = manager.get_kept_models()
    level1 = [m for m in kept if m.level == 1]
    
    # Sort by dBIC (should match search's internal sort)
    level1.sort(key=lambda m: m.dbic, reverse=True)  # Higher is better
    
    print("\nActual results from pyoccam2:")
    print("-" * 50)
    print(f"{'Rank':<6} {'Model':<12} {'dBIC':<10} {'dAIC':<10} {'Info':<8}")
    print("-" * 50)
    
    for i, model in enumerate(level1[:5], 1):
        print(f"{i:<6} {model.name:<12} {model.dbic:>9.2f} {model.daic:>9.2f} {model.information:>7.4f}")
    
    # Check best model methods
    print("\n" + "=" * 80)
    print("BEST MODEL METHODS CHECK")
    print("-" * 50)
    
    best_bic = manager.get_best_model_by_bic()
    best_aic = manager.get_best_model_by_aic()
    best_info = manager.get_best_model_by_information()
    
    print(f"get_best_model_by_bic(): {best_bic}")
    print(f"get_best_model_by_aic(): {best_aic}")
    print(f"get_best_model_by_information(): {best_info}")
    
    # Verification
    print("\n" + "=" * 80)
    print("VERIFICATION RESULTS")
    print("-" * 50)
    
    success = True
    
    if level1 and level1[0].name == "IV:ApZ":
        print("✓ IV:ApZ (APOE) is correctly ranked #1")
    else:
        print(f"✗ Wrong #1: {level1[0].name if level1 else 'none'}")
        success = False
    
    if best_bic == "IV:ApZ":
        print("✓ get_best_model_by_bic() returns IV:ApZ")
    else:
        print(f"✗ get_best_model_by_bic() returns {best_bic}")
        success = False
    
    # Check if top 3 match expected
    if len(level1) >= 3:
        top3 = [m.name for m in level1[:3]]
        expected = ["IV:ApZ", "IV:EdZ", "IV:AgZ"]
        
        if top3 == expected:
            print(f"✓ Top 3 models match expected: {', '.join(top3)}")
        else:
            print(f"✗ Top 3 don't match.")
            print(f"  Expected: {', '.join(expected)}")
            print(f"  Got:      {', '.join(top3)}")
            success = False
    
    return success

if __name__ == "__main__":
    import sys
    if verify_server_match():
        print("\n✓✓✓ SUCCESS: Matches server output!")
        sys.exit(0)
    else:
        print("\n✗✗✗ FAILURE: Does not match server output")
        sys.exit(1)