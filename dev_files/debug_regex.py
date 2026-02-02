#!/usr/bin/env python3
"""
Debug the regex pattern to see what's not matching
"""

import _pyoccam as pyoccam
import re

print("="*60)
print("DEBUGGING REGEX PATTERN MATCHING")
print("="*60)

# Initialize and load data
manager = pyoccam.VBMManager()
manager.init_from_command_line(["occam", "dementia05.txt"])

# Quick search
manager.generate_search_report("loopless-up", 3, 3, False)
best_model = manager.get_best_model_by_bic()

# Generate fit report to examine
print(f"\nGenerating fit report for: {best_model}")
fit_report = manager.generate_fit_report(best_model, "0")

# Find confusion matrix section
cm_start = fit_report.find("Confusion Matrix")
if cm_start >= 0:
    # Extract relevant section
    cm_section = fit_report[cm_start:cm_start+1000]
    
    print("\nConfusion Matrix Section:")
    print("-"*40)
    lines = cm_section.split('\n')[:15]  # First 15 lines
    for i, line in enumerate(lines):
        print(f"Line {i:2}: [{line}]")  # Show with brackets to see spaces
    
    print("\n" + "-"*40)
    print("Testing different regex patterns:")
    print("-"*40)
    
    # Test different patterns
    patterns = [
        (r"TN=([0-9]+(?:\.[0-9]+)?)", "TN without comma"),
        (r"TN=,([0-9]+(?:\.[0-9]+)?)", "TN with comma after ="),
        (r"TN=\s*,\s*([0-9]+(?:\.[0-9]+)?)", "TN with spaces"),
        (r",TN=,([0-9]+(?:\.[0-9]+)?)", "TN with leading comma"),
        (r"TN=\s*,?\s*([0-9]+(?:\.[0-9]+)?)", "TN flexible"),
    ]
    
    for pattern, desc in patterns:
        match = re.search(pattern, cm_section)
        if match:
            print(f"✓ {desc:25} matched: {match.group(1)}")
        else:
            print(f"✗ {desc:25} no match")
    
    # Look for the actual pattern in the text
    print("\n" + "-"*40)
    print("Looking for 'TN=' in the section:")
    print("-"*40)
    
    tn_pos = cm_section.find("TN=")
    if tn_pos >= 0:
        # Show 20 chars before and after
        start = max(0, tn_pos - 20)
        end = min(len(cm_section), tn_pos + 30)
        context = cm_section[start:end]
        print(f"Found at position {tn_pos}:")
        print(f"Context: [{context}]")
        print(f"         {' ' * (tn_pos - start)}^")
        
        # Show as hex to see exact characters
        print("\nAs hex values:")
        for i, char in enumerate(context):
            if i == tn_pos - start:
                print(f"[{ord(char):02x}]", end="")
            else:
                print(f" {ord(char):02x} ", end="")
        print()
    else:
        print("'TN=' not found in section")

# Also save the full report for inspection
with open("debug_fit_report.txt", "w", encoding='utf-8') as f:
    f.write(fit_report)
print(f"\nFull report saved to: debug_fit_report.txt")

print("\n" + "="*60)
