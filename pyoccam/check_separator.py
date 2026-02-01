#!/usr/bin/env python3
"""
Check what separator format is actually being used in the fit reports
"""

import pyoccam

print("Checking separator format...\n")

# Initialize
manager = pyoccam.VBMManager()
manager.init_from_command_line(["occam", "dementia05.txt"])

# Run quick search
manager.generate_search_report("loopless-up", 3, 3)
best = manager.get_best_model_by_information()
print(f"Best model: {best}\n")

# Generate fit report
print("Generating fit report...")
fit_report = manager.generate_fit_report(best, "0")
print(f"Report length: {len(fit_report)} chars\n")

# Find the confusion matrix section
cm_pos = fit_report.find("Confusion Matrix")
if cm_pos == -1:
    print("ERROR: No Confusion Matrix found!")
else:
    print("Found Confusion Matrix section\n")
    
    # Extract a chunk around the CM
    chunk = fit_report[cm_pos:cm_pos+1000]
    
    # Look for the TN line
    tn_line_start = chunk.find("TN=")
    if tn_line_start != -1:
        # Get the full line
        line_end = chunk.find('\n', tn_line_start)
        if line_end == -1:
            line_end = len(chunk)
        tn_line = chunk[tn_line_start:line_end]
        
        print("="*80)
        print("TN LINE FOUND:")
        print("="*80)
        print(repr(tn_line))
        print()
        
        # Check what separator is used
        if ',TN=' in tn_line:
            print("✓ Uses COMMA separator: ',TN='")
        elif '\tTN=' in tn_line:
            print("✓ Uses TAB separator: '\\tTN='")
        elif ' TN=' in tn_line:
            print("✓ Uses SPACE separator: ' TN='")
        else:
            print("? Unknown separator")
        
        print()
        
        # Show the actual bytes
        print("First 200 characters as repr():")
        print(repr(tn_line[:200]))
        print()
        
        # Count separators
        comma_count = tn_line.count(',')
        tab_count = tn_line.count('\t')
        space_count = tn_line.count(' ')
        
        print(f"Separator counts in this line:")
        print(f"  Commas: {comma_count}")
        print(f"  Tabs: {tab_count}")
        print(f"  Spaces: {space_count}")
        
    else:
        print("ERROR: No TN= found in CM section!")
        print("\nShowing first 500 chars of CM section:")
        print(chunk[:500])

# Save full report for inspection
with open("test_fit_report_full.txt", "w") as f:
    f.write(fit_report)
print("\n✓ Full report saved to test_fit_report_full.txt")
