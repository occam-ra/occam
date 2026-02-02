#!/usr/bin/env python
"""
Test the simplest report output with Version 38 - includes fixed BIC calculation
"""

import pyoccam2

def test_simple_report():
    """Test report generation with corrected BIC calculations"""
    
    print("=" * 80)
    print("SIMPLE REPORT TEST - Version 38 with Fixed BIC")
    print("=" * 80)
    
    # Initialize manager
    manager = pyoccam2.VBMManager()
    
    # Load data
    success = manager.init_from_command_line(["occam", "dementia05.txt"])
    if not success:
        print("ERROR: Failed to load data")
        return False
    
    # Test with space separator (default)
    print("\n1. Testing LOOPLESS-UP search (1 level, width=3):")
    print("-" * 80)
    
    manager.set_report_separator(3)  # Space
    report = manager.generate_search_report("loopless-up", levels=1, width=3)
    
    # Print the report
    print(report)
    
    # Show which models were selected
    print("\n" + "-" * 80)
    print("Best models selected:")
    print(f"  By BIC: {manager.get_best_model_by_bic()}")
    print(f"  By AIC: {manager.get_best_model_by_aic()}")
    print(f"  By Info: {manager.get_best_model_by_information()}")
    best_alpha = manager.get_best_model_by_info_alpha()
    if best_alpha:
        print(f"  By Info (inc.alpha < 0.05): {best_alpha}")
    
    # Test multi-level search
    print("\n2. Testing LOOPLESS-UP search (2 levels, width=3):")
    print("-" * 80)
    
    report = manager.generate_search_report("loopless-up", levels=2, width=3)
    
    # Show search progress and first few lines
    lines = report.split('\n')
    for i, line in enumerate(lines[:15]):  # Show first 15 lines
        print(line)
    if len(lines) > 15:
        print("... (output truncated)")
    
    print(f"\nBest after 2 levels: {manager.get_best_model_by_bic()}")
    
    # Test FULL-UP search
    print("\n3. Testing FULL-UP search (1 level, width=3):")
    print("-" * 80)
    
    report = manager.generate_search_report("full-up", levels=1, width=3)
    
    # Count how many models were generated
    for line in report.split('\n'):
        if "new models" in line:
            print(f"Search progress: {line}")
    
    print(f"\nBest model (full-up): {manager.get_best_model_by_bic()}")
    
    return True

if __name__ == "__main__":
    import sys
    success = test_simple_report()
    print("\n" + "=" * 80)
    print("Simple report test complete (Version 38).")
    print("Key improvements:")
    print("  - Fixed BIC calculation: correctly using OCCAM's computations")
    print("  - Report class properly integrated with fresh instance per search")
    print("  - Added incremental alpha computation and filtering")
    print("  - Added %dH(DV) and Inc.Alpha columns to match server output")
    print("  - IV:ApZ should now be selected as best model")
    print("=" * 80)
    sys.exit(0 if success else 1)