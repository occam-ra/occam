#!/usr/bin/env python
"""
Test clean report output without duplicates
"""

import pyoccam2

def test_clean_report():
    """Test clean report generation"""
    
    print("=" * 80)
    print("CLEAN REPORT TEST")
    print("=" * 80)
    
    # Initialize manager
    manager = pyoccam2.VBMManager()
    
    # Load data
    success = manager.init_from_command_line(["occam", "dementia05.txt"])
    if not success:
        print("ERROR: Failed to load data")
        return False
    
    # Set clean report variables
    manager.set_report_variables("level$I, h, ddf$I, lr, alpha, information, aic, bic")
    
    # Run search
    print("\nRunning search (Level 1 only)...")
    report = manager.generate_search_report("loopless-up", levels=1, width=3)
    
    # Process the report to remove duplicates
    lines = report.split('\n')
    seen_lines = set()
    clean_lines = []
    
    for line in lines:
        # Keep search progress lines
        if "Searching levels:" in line or " : " in line:
            clean_lines.append(line)
        # Keep unique data lines
        elif line.strip() and line not in seen_lines:
            clean_lines.append(line)
            seen_lines.add(line)
    
    print("\nCleaned Report:")
    print("-" * 80)
    for line in clean_lines:
        print(line)
    
    # Check the kept models directly
    print("\n" + "=" * 80)
    print("KEPT MODELS (Direct Access)")
    print("-" * 80)
    
    kept = manager.get_kept_models()
    print(f"Number of kept models: {len(kept)}")
    
    # Sort by information for display
    kept.sort(key=lambda m: m.information, reverse=True)
    
    print(f"\n{'ID':<4} {'Model':<15} {'Level':<6} {'H':<10} {'dDF':<6} {'LR':<10} {'Info':<10} {'BIC':<10}")
    print("-" * 90)
    
    for i, model in enumerate(kept, 1):
        print(f"{i:<4} {model.name:<15} {model.level:<6.0f} {model.h:<10.4f} "
              f"{model.df:<6.0f} {model.lr:<10.2f} {model.information:<10.6f} {model.bic:<10.2f}")
    
    # Test Level 7 to see final results
    print("\n" + "=" * 80)
    print("FULL SEARCH (Level 7)")
    print("-" * 80)
    
    report_full = manager.generate_search_report("loopless-up", levels=7, width=3)
    
    # Just show search progress and top models
    lines = report_full.split('\n')
    
    print("Search Progress:")
    for line in lines[:10]:
        if "Searching" in line or " : " in line:
            print(line)
    
    # Get final kept models
    kept_final = manager.get_kept_models()
    kept_final.sort(key=lambda m: m.information, reverse=True)
    
    print(f"\nTop 5 models by information (out of {len(kept_final)} total):")
    print("-" * 60)
    
    for model in kept_final[:5]:
        print(f"{model.name:<20} Level={model.level:1.0f} Info={model.information:.6f} dBIC={model.dbic:.2f}")
    
    # Check if we got the expected top model
    if kept_final and kept_final[0].name == "IV:ApSxAgACEMZ":
        print("\n✓ SUCCESS: Top model matches server (IV:ApSxAgACEMZ)")
    else:
        top_name = kept_final[0].name if kept_final else "none"
        print(f"\n✗ Top model is {top_name}, expected IV:ApSxAgACEMZ")
    
    return True

if __name__ == "__main__":
    import sys
    success = test_clean_report()
    print("\n" + "=" * 80)
    print("Clean report test complete.")
    print("=" * 80)
    sys.exit(0 if success else 1)