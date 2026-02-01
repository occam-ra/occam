#!/usr/bin/env python3
"""
Debug the CSV parsing to see what's actually in the parts
"""

import _pyoccam as pyoccam

# Initialize and get a model
manager = pyoccam.VBMManager()
manager.init_from_command_line(["occam", "dementia05.txt"])
manager.generate_search_report("loopless-up", 3, 3, False)
best_model = manager.get_best_model_by_bic()

# Generate fit report
fit_report = manager.generate_fit_report(best_model, "0")

# Find and parse the confusion matrix lines manually
lines = fit_report.split('\n')
for i, line in enumerate(lines):
    if "TN=" in line and "FP=" in line:
        print(f"\nFound TN/FP line at {i}:")
        print(f"Raw line: [{line}]")
        
        # Split by comma
        parts = line.split(',')
        print(f"\nNumber of parts: {len(parts)}")
        for j, part in enumerate(parts):
            print(f"  Part {j:2d}: [{part}]")
        
        # Look for TN= and the value
        for j in range(len(parts)):
            if "TN=" in parts[j]:
                print(f"\nFound 'TN=' in part {j}: [{parts[j]}]")
                if j + 1 < len(parts):
                    print(f"Next part (should be value): [{parts[j+1]}]")
                    try:
                        value = float(parts[j+1])
                        print(f"✓ Successfully parsed as: {value}")
                    except:
                        print(f"✗ Failed to parse as float")
                        
    if "FN=" in line and "TP=" in line:
        print(f"\nFound FN/TP line at {i}:")
        print(f"Raw line: [{line}]")
        
        parts = line.split(',')
        print(f"\nNumber of parts: {len(parts)}")
        for j, part in enumerate(parts):
            print(f"  Part {j:2d}: [{part}]")
