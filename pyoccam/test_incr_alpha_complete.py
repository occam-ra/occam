#!/usr/bin/env python3
"""
Test script for verifying incremental alpha fixes in pyoccam2
This should correctly identify IV:ApZ:EdZ:AgZ:CZ:KZ as the best model by information with incremental alpha
"""

import pyoccam2
import sys

def main():
    print("=" * 70)
    print("TESTING INCREMENTAL ALPHA FIX")
    print("=" * 70)
    
    # Initialize manager
    manager = pyoccam2.VBMManager()
    
    # Load data
    if not manager.init_from_command_line(["occam", "dementia05.txt"]):
        print("ERROR: Could not load data file")
        return False
    
    print("✓ Data loaded successfully")
    print(f"  Sample size: {manager.get_sample_size()}")
    print(f"  Variables: {', '.join(manager.get_variable_list())}")
    print()
    
    # Configure
    manager.set_ref_model("bottom")
    manager.set_debug_mode(True)  # Enable debugging
    manager.set_report_separator(pyoccam2.SPACESEP)
    
    # Set report variables to include incremental alpha columns
    manager.set_report_variables("ID$I, Model, Level$I, h, ddf, dLR, Alpha, Inf, %dH(DV), dAIC, dBIC, Inc.Alpha, Prog., %C(Data)")
    
    print("=" * 70)
    print("PERFORMING SEARCH")
    print("=" * 70)
    
    # Do search
    report = manager.generate_search_report("full-up", 7, 3, False)
    
    # Save report for inspection
    with open("search_report_with_incr_alpha.txt", "w") as f:
        f.write(report)
    print("\n✓ Search report saved to search_report_with_incr_alpha.txt")
    
    # Check for incremental alpha section in report
    print("\n" + "=" * 70)
    print("CHECKING REPORT CONTENT")
    print("=" * 70)
    
    if "Best Model(s) by Information with all Inc. Alpha" in report:
        print("✓ Incremental alpha section FOUND in report")
        
        # Extract and display the section
        lines = report.split('\n')
        found = False
        for i, line in enumerate(lines):
            if "Best Model(s) by Information with all Inc. Alpha" in line:
                found = True
                print("\nExtracted section:")
                print("-" * 40)
                print(line)
                # Print next few lines to see the actual model
                for j in range(1, 4):
                    if i+j < len(lines) and lines[i+j].strip():
                        print(lines[i+j])
                print("-" * 40)
                break
    else:
        print("✗ Incremental alpha section NOT FOUND in report")
    
    # Check best models using methods
    print("\n" + "=" * 70)
    print("BEST MODEL SELECTIONS")
    print("=" * 70)
    
    best_bic = manager.get_best_model_by_bic()
    best_aic = manager.get_best_model_by_aic()
    best_info = manager.get_best_model_by_information()
    best_info_alpha = manager.get_best_model_by_info_alpha()
    
    print(f"By BIC:              {best_bic}")
    print(f"By AIC:              {best_aic}")
    print(f"By Information:      {best_info}")
    print(f"By Info+Alpha:       {best_info_alpha}")
    
    # Expected from server PDF (model #19)
    expected_info_alpha = "IV:ApZ:EdZ:AgZ:CZ:KZ"
    
    print("\n" + "=" * 70)
    print("VALIDATION")
    print("=" * 70)
    
    print(f"Expected Info+Alpha: {expected_info_alpha}")
    print(f"Actual Info+Alpha:   {best_info_alpha}")
    
    success = (best_info_alpha == expected_info_alpha)
    
    if success:
        print("\n✓✓✓ SUCCESS! Incremental alpha selection is CORRECT! ✓✓✓")
    else:
        print("\n✗✗✗ FAILED! Incremental alpha selection is INCORRECT! ✗✗✗")
        
        # Additional debugging
        print("\n" + "=" * 70)
        print("DEBUGGING INFO")
        print("=" * 70)
        
        # Debug the incremental alpha status
        manager.debug_incr_alpha()
        
        # Check specific model attributes
        if best_info_alpha:
            print(f"\nActual best model attributes:")
            attrs = manager.debug_model_attributes(best_info_alpha)
            for key, value in attrs.items():
                print(f"  {key}: {value}")
        
        print(f"\nExpected model attributes:")
        attrs = manager.debug_model_attributes(expected_info_alpha)
        for key, value in attrs.items():
            print(f"  {key}: {value}")
    
    # Count models with asterisks (reachable models)
    print("\n" + "=" * 70)
    print("ASTERISK CHECK")
    print("=" * 70)
    
    asterisk_count = 0
    for line in report.split('\n'):
        if line.strip() and line[0:4].strip() and '*' in line[0:5]:
            asterisk_count += 1
            if asterisk_count <= 5:  # Show first 5
                # Extract model name
                parts = line.split()
                if len(parts) > 1:
                    model_name = parts[1] if parts[0].endswith('*') else parts[0]
                    print(f"  Reachable model: {model_name}")
    
    print(f"\nTotal models with asterisk (*): {asterisk_count}")
    
    # Final summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    
    all_tests = {
        "Data loading": True,
        "Search execution": True,
        "Report generation": True,
        "Inc.Alpha section present": "Best Model(s) by Information with all Inc. Alpha" in report,
        "Best BIC found": bool(best_bic),
        "Best AIC found": bool(best_aic),
        "Best Info found": bool(best_info),
        "Best Info+Alpha found": bool(best_info_alpha),
        "Info+Alpha selection correct": success,
        "Asterisks present": asterisk_count > 0
    }
    
    passed = sum(1 for v in all_tests.values() if v)
    total = len(all_tests)
    
    for test, result in all_tests.items():
        status = "✓" if result else "✗"
        print(f"  {status} {test}")
    
    print(f"\nTests passed: {passed}/{total}")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
