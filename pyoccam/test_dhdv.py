#!/usr/bin/env python
"""
Test that %dH(DV) column shows proper values
"""

import pyoccam2

def test_dhdv():
    """Test that %dH(DV) column has values"""
    
    print("=" * 80)
    print("TEST: %dH(DV) COLUMN VALUES")
    print("=" * 80)
    
    # Initialize manager
    manager = pyoccam2.VBMManager()
    
    # Enable debug mode to see the values being set
    manager.set_debug_mode(True)
    
    # Load data
    success = manager.init_from_command_line(["occam", "dementia05.txt"])
    if not success:
        print("ERROR: Failed to load dementia05.txt")
        return False
    
    print("\nData loaded successfully")
    
    # Run a simple 1-level search
    print("\nRunning 1-level search with debug output...")
    print("-" * 80)
    
    report = manager.generate_search_report("loopless-up", levels=1, width=3)
    
    # Print the report
    print("\n" + "=" * 80)
    print("SEARCH REPORT:")
    print("=" * 80)
    print(report)
    
    # Check if %dH(DV) values are present
    print("\n" + "=" * 80)
    print("VERIFICATION:")
    print("=" * 80)
    
    # Parse the report to check for %dH(DV) values
    lines = report.split('\n')
    has_values = False
    for line in lines:
        if 'IV:ApZ' in line:
            print(f"IV:ApZ line: {line}")
            # Check if there's a value around 8.7 (which is what we expect for IV:ApZ)
            if '8.7' in line or '8.71' in line:
                has_values = True
                print("✓ Found expected %dH(DV) value for IV:ApZ (~8.7%)")
            else:
                print("✗ Missing %dH(DV) value for IV:ApZ")
    
    # Get individual model statistics
    print("\nDirect model check:")
    model = manager.get_model_statistics("IV:ApZ")
    print(f"  IV:ApZ information: {model.information:.6f}")
    print(f"  Expected %dH(DV): {model.information * 100:.2f}%")
    
    if has_values:
        print("\n✓ SUCCESS: %dH(DV) column has proper values")
        return True
    else:
        print("\n✗ FAILURE: %dH(DV) column is missing values")
        return False

if __name__ == "__main__":
    import sys
    success = test_dhdv()
    print("\n" + "=" * 80)
    if success:
        print("Test passed - %dH(DV) values are showing correctly")
    else:
        print("Test failed - %dH(DV) values are missing")
        print("Check that the %dH(DV) attribute is being set in computeModelStatistics()")
    print("=" * 80)
    sys.exit(0 if success else 1)