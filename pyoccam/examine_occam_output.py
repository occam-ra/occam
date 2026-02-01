#!/usr/bin/env python3
"""
Examine OCCAM output to understand format and content
"""

import pyoccam2 as pyoccam
import re

print("="*70)
print("OCCAM OUTPUT EXAMINATION")
print("="*70)

# Initialize
manager = pyoccam.VBMManager()
manager.init_from_command_line(["occam", "dementia05.txt"])
manager.set_report_separator(pyoccam.SPACESEP)
manager.set_ref_model("bottom")
manager.set_fit_classifier_target("0")

# Get best model
print("\n1. RUNNING SEARCH TO GET BEST MODEL...")
search_report = manager.generate_search_report("full-up", 3, 3, False)
best_bic = manager.get_best_model_by_bic()
print(f"Best BIC model: {best_bic}")

# Generate fit report
print("\n2. GENERATING FIT REPORT...")
fit_report = manager.generate_fit_report(best_bic, "0")

# Examine the structure
print("\n3. FIT REPORT STRUCTURE:")
print("-" * 50)

# Split into sections
sections = fit_report.split("\n\n")
print(f"Number of sections: {len(sections)}")

# Look for key components
components = {
    "Basic Statistics": "H(data)",
    "Model Info": "Model",
    "Residuals": "Residuals",
    "IVI": "obs.*p\\(DV\\|IV\\)",  # regex for conditional probability
    "Conditional DV": "Conditional DV",
    "Confusion Matrix": "Confusion Matrix",
    "Accuracy Stats": "Accuracy"
}

print("\nComponents found:")
for name, pattern in components.items():
    if re.search(pattern, fit_report, re.IGNORECASE):
        print(f"  ✓ {name}")
        # Find the line
        for line in fit_report.split('\n'):
            if re.search(pattern, line, re.IGNORECASE):
                print(f"    Sample: {line[:60]}...")
                break
    else:
        print(f"  ✗ {name}")

# Look at confusion matrix specifically
print("\n4. CONFUSION MATRIX DETAILS:")
print("-" * 50)

if "Confusion Matrix" in fit_report:
    # Extract confusion matrix section
    lines = fit_report.split('\n')
    in_cm = False
    cm_lines = []
    
    for i, line in enumerate(lines):
        if "Confusion Matrix" in line:
            in_cm = True
            print(f"Found at line {i}: {line}")
        elif in_cm:
            cm_lines.append(line)
            if len(cm_lines) > 15:  # Get enough context
                break
    
    print("\nConfusion matrix section:")
    for line in cm_lines[:10]:
        print(f"  {line}")
else:
    print("No confusion matrix found")

# Look at the conditional probability table format
print("\n5. CONDITIONAL PROBABILITY TABLE FORMAT:")
print("-" * 50)

# Find a conditional table
for line in fit_report.split('\n'):
    if "freq" in line and "obs" in line:
        idx = fit_report.index(line)
        # Get surrounding lines
        context = fit_report[max(0, idx-100):idx+500]
        print("Sample of conditional probability table:")
        print(context)
        break

# Check column alignment issues
print("\n6. CHECKING COLUMN ALIGNMENT:")
print("-" * 50)

# Look for lines with multiple columns
data_lines = []
for line in fit_report.split('\n'):
    parts = line.split()
    if len(parts) > 5 and parts[0].replace('.', '').isdigit():
        data_lines.append(line)
        if len(data_lines) <= 3:
            print(f"Data line: {line}")

# Save different format versions
print("\n7. SAVING DIFFERENT FORMATS:")
print("-" * 50)

# Space format (already have it)
with open("fit_space.txt", "w") as f:
    f.write(fit_report)
print("✓ Saved space-separated: fit_space.txt")

# Tab format
manager.set_report_separator(pyoccam.TABSEP)
fit_tab = manager.generate_fit_report(best_bic, "0")
with open("fit_tab.txt", "w") as f:
    f.write(fit_tab)
print("✓ Saved tab-separated: fit_tab.txt")

# Comma format
manager.set_report_separator(pyoccam.COMMASEP)
fit_comma = manager.generate_fit_report(best_bic, "0")
with open("fit_comma.txt", "w") as f:
    f.write(fit_comma)
print("✓ Saved comma-separated: fit_comma.txt")

# HTML format
manager.set_report_separator(pyoccam.HTMLFORMAT)
fit_html = manager.generate_fit_report(best_bic, "0")
with open("fit_html.html", "w") as f:
    f.write(fit_html)
print("✓ Saved HTML: fit_html.html")

print("\n" + "="*70)
print("EXAMINATION COMPLETE")
print("="*70)
print("\nCheck the output files:")
print("  - fit_space.txt  (space-separated)")
print("  - fit_tab.txt    (tab-separated)")
print("  - fit_comma.txt  (comma-separated)") 
print("  - fit_html.html  (HTML formatted)")
print("\nThe HTML version should display perfectly in Jupyter notebooks!")
