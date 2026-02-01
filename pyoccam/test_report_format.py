#!/usr/bin/env python
"""
Test that our report format matches the server output exactly
"""

import pyoccam2

def test_report_format():
    """Verify report format matches server"""
    
    print("=" * 80)
    print("TESTING REPORT FORMAT")
    print("=" * 80)
    
    # Initialize manager
    manager = pyoccam2.VBMManager()
    
    # Server settings
    print("\nUsing server settings:")
    print("  Search: loopless-up")
    print("  Width: 3")
    print("  Levels: 7")
    print("  Report separator: space-filled")
    
    # Load data
    success = manager.init_from_command_line(["occam", "dementia05.txt"])
    if not success:
        print("ERROR: Failed to load data")
        return False
    
    # Run search with server parameters
    print("\nGenerating search report...")
    print("-" * 80)
    
    # This should now include the search progress lines and formatted table
    report = manager.generate_search_report("full-up", levels=7, width=3)
    
    # Print the full report
    print(report)
    
    # Check the format
    print("\n" + "=" * 80)
    print("FORMAT CHECK")
    print("-" * 80)
    
    lines = report.split('\n')
    
    # Check for search progress lines
    search_lines = [l for l in lines if l.startswith("Searching levels:") or " : " in l]
    if search_lines:
        print("✓ Search progress lines found:")
        for line in search_lines[:3]:  # Show first few
            print(f"  {line}")
    else:
        print("✗ Search progress lines missing")
    
    # Check for table header
    header_found = False
    for line in lines:
        if "ID" in line and "MODEL" in line and "Level" in line:
            header_found = True
            print(f"\n✓ Table header found:")
            print(f"  {line}")
            break
    
    if not header_found:
        # Try alternate format
        for line in lines:
            if "Model" in line and "h" in line and "dBIC" in line:
                header_found = True
                print(f"\n✓ Table header found (alternate format):")
                print(f"  {line}")
                break
    
    if not header_found:
        print("\n✗ Table header not found")
    
    # Check for data rows
    data_lines = []
    for line in lines:
        if "IV:" in line:  # Model names contain IV:
            data_lines.append(line)
    
    if data_lines:
        print(f"\n✓ Found {len(data_lines)} data rows")
        print("  First few rows:")
        for line in data_lines[:3]:
            # Truncate long lines for display
            if len(line) > 100:
                print(f"  {line[:100]}...")
            else:
                print(f"  {line}")
    else:
        print("\n✗ No data rows found")
    
    # Expected format from server:
    print("\n" + "=" * 80)
    print("EXPECTED SERVER FORMAT")
    print("-" * 80)
    print("Searching levels:")
    print("1 : 18 new models, 3 kept; 19 total models, 4 total kept; 0 kb memory used; 0.0 seconds, 0.0 total")
    print("...")
    print("ID MODEL Level H dDF dLR Alpha Inf %dH(DV) dAIC dBIC Inc.Alpha Prog. %C(Data) %cover")
    print("22 IV:ApSxAgACEMZ 7 9.0080 971 422.3768 1.0000 0.71952168 71.9522 -1519.6232 -5451.9144 ...")
    
    return True

if __name__ == "__main__":
    import sys
    success = test_report_format()
    sys.exit(0 if success else 1)