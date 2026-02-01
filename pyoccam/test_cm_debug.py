#!/usr/bin/env python3
"""
Debug script to test confusion matrix extraction
Shows exactly what the C++ function is returning and what we expect
"""

import pyoccam
import re

print("=" * 80)
print("CONFUSION MATRIX DEBUG TEST")
print("=" * 80)

# Initialize manager
manager = pyoccam.VBMManager()
manager.init_from_command_line(["occam", "dementia05.txt"])

# Run search
print("\nRunning search...")
manager.generate_search_report("loopless-up", 3, 3)

# Get best model
best_model = manager.get_best_model_by_bic()
print(f"Best model: {best_model}")

# Generate fit report to see what it contains
print("\n" + "=" * 80)
print("GENERATING FIT REPORT")
print("=" * 80)
fit_report = manager.generate_fit_report(best_model, "0")

# Save the report
with open("debug_fit_report.txt", "w") as f:
    f.write(fit_report)
print("Fit report saved to: debug_fit_report.txt")

# Look for the confusion matrix section
print("\n" + "=" * 80)
print("SEARCHING FOR CONFUSION MATRIX IN REPORT")
print("=" * 80)

lines = fit_report.split('\n')
found_cm = False
for i, line in enumerate(lines):
    if 'Confusion Matrix' in line:
        print(f"\nFound at line {i}: {line}")
        # Print next 15 lines
        print("\nNext 15 lines:")
        for j in range(i, min(i+15, len(lines))):
            print(f"  {j}: {lines[j]}")
        found_cm = True
        break

if not found_cm:
    print("\n❌ NO CONFUSION MATRIX FOUND IN REPORT!")
    print("\nFirst 50 lines of report:")
    for i in range(min(50, len(lines))):
        print(f"  {i}: {lines[i]}")

# Now test the get_confusion_matrix function
print("\n" + "=" * 80)
print("TESTING get_confusion_matrix() FUNCTION")
print("=" * 80)

cm = manager.get_confusion_matrix(best_model, "0")

print("\nReturned dictionary:")
for key, value in cm.items():
    print(f"  {key}: {value}")

# Try to manually parse from the report
print("\n" + "=" * 80)
print("MANUAL PARSING ATTEMPT")
print("=" * 80)

# Look for patterns like: ,Z=0,|,TN=,179.000,FP=,42.000,AN=,221.000
tn = fp = fn = tp = 0

for line in lines:
    # Look for the Z=0 row (negatives)
    if ',Z=0,|,TN=' in line or ',Z=0,|,TN=' in line.replace(' ', ''):
        print(f"\nFound TN/FP line: {line}")
        # Parse: ,Z=0,|,TN=,179.000,FP=,42.000,AN=,221.000
        parts = line.split(',')
        print(f"  Parts: {parts}")
        for i, part in enumerate(parts):
            if part == 'TN=' and i+1 < len(parts):
                try:
                    tn = float(parts[i+1])
                    print(f"  Extracted TN = {tn}")
                except:
                    pass
            elif part == 'FP=' and i+1 < len(parts):
                try:
                    fp = float(parts[i+1])
                    print(f"  Extracted FP = {fp}")
                except:
                    pass
    
    # Look for the Z≠0 or Z=not0 row (positives)
    if (',Z≠0,|,FN=' in line or ',Z=not0,|,FN=' in line or 
        ',Z=not0,|,FN=' in line.replace(' ', '')):
        print(f"\nFound FN/TP line: {line}")
        parts = line.split(',')
        print(f"  Parts: {parts}")
        for i, part in enumerate(parts):
            if part == 'FN=' and i+1 < len(parts):
                try:
                    fn = float(parts[i+1])
                    print(f"  Extracted FN = {fn}")
                except:
                    pass
            elif part == 'TP=' and i+1 < len(parts):
                try:
                    tp = float(parts[i+1])
                    print(f"  Extracted TP = {tp}")
                except:
                    pass

print("\n" + "=" * 80)
print("RESULTS COMPARISON")
print("=" * 80)

print("\nManual parsing extracted:")
print(f"  TN = {tn}")
print(f"  FP = {fp}")
print(f"  FN = {fn}")
print(f"  TP = {tp}")

if tn > 0 or tp > 0:
    total = tn + fp + fn + tp
    accuracy = (tn + tp) / total if total > 0 else 0
    print(f"  Accuracy = {accuracy:.3f}")
    print("\n✅ Manual parsing SUCCESS!")
else:
    print("\n❌ Manual parsing FAILED!")

print("\nC++ get_confusion_matrix() returned:")
print(f"  TN = {cm.get('tn', cm.get('TN', 0))}")
print(f"  FP = {cm.get('fp', cm.get('FP', 0))}")
print(f"  FN = {cm.get('fn', cm.get('FN', 0))}")
print(f"  TP = {cm.get('tp', cm.get('TP', 0))}")
print(f"  Accuracy = {cm.get('accuracy', 0)}")

if cm.get('accuracy', cm.get('TN', 0)) > 0:
    print("\n✅ C++ function is working!")
else:
    print("\n❌ C++ function is NOT extracting values!")
    print("\nThe C++ extractConfusionMatrixFromReport() function needs to be fixed")
    print("to parse the CSV format correctly.")

print("\n" + "=" * 80)
