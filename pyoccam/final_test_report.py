#!/usr/bin/env python
"""
Final test of report format matching server output
"""

import pyoccam2

def final_report_test():
    """Final verification of report format"""
    
    print("=" * 80)
    print("FINAL REPORT FORMAT TEST")
    print("=" * 80)
    
    # Initialize manager
    manager = pyoccam2.VBMManager()
    
    # Load data
    success = manager.init_from_command_line(["occam", "dementia05.txt"])
    if not success:
        print("ERROR: Failed to load data")
        return False
    
    # Test Level 1 first to see column values
    print("\n1. Testing Level 1 only (for clarity):")
    print("-" * 80)
    
    report = manager.generate_search_report("loopless-up", levels=1, width=3)
    print(report)
    
    # Now full search
    print("\n2. Full 7-level search:")
    print("-" * 80)
    
    report_full = manager.generate_search_report("loopless-up", levels=7, width=3)
    
    # Just show the first part and last part
    lines = report_full.split('\n')
    
    # Show search progress
    print("Search progress:")
    for line in lines[:10]:
        if line.strip():
            print(line)
    
    # Show first few data rows
    print("\nFirst few model rows:")
    model_lines = [l for l in lines if "IV:" in l]
    for line in model_lines[:5]:
        print(line)
    
    # Check specific values for top model
    print("\n3. Checking top model values:")
    print("-" * 80)
    
    kept = manager.get_kept_models()
    if kept:
        # Sort by information to get top model
        kept.sort(key=lambda m: m.information, reverse=True)
        top = kept[0]
        
        print(f"Top model: {top.name}")
        print(f"  Level: {top.level}")
        print(f"  H: {top.h:.4f}")
        print(f"  dDF: {top.df:.0f}")
        print(f"  dLR: {top.lr:.4f}")  # This should show the LR value
        print(f"  Alpha: {top.alpha:.4f}")
        print(f"  Information: {top.information:.8f}")
        print(f"  %dH(DV): {top.information * 100:.4f}")  # As percentage
        print(f"  dAIC: {top.daic:.4f}")
        print(f"  dBIC: {top.dbic:.4f}")
    
    # Compare with server expected values
    print("\n4. Server expected values for top model (IV:ApSxAgACEMZ):")
    print("-" * 80)
    print("  Level: 7")
    print("  H: 9.0080")
    print("  dDF: 971")
    print("  dLR: 422.3768")
    print("  Alpha: 1.0000")
    print("  Inf: 0.71952168")
    print("  %dH(DV): 71.9522")
    print("  dAIC: -1519.6232")
    print("  dBIC: -5451.9144")
    
    return True

if __name__ == "__main__":
    import sys
    success = final_report_test()
    print("\n" + "=" * 80)
    print("Test complete. Check if values match server output.")
    print("=" * 80)
    sys.exit(0 if success else 1)