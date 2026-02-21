"""
PyOccam Demo: CSV Conversion & Lookup Tables
=============================================
Shows how to:
  1. Convert a standard CSV file to OCCAM format
  2. Use auto-generated lookup tables to decode integer encodings
  3. Run a quick analysis on the converted data
  4. Use train/test split for validation

The sample CSV is automatically found in the package directory.
"""

import pyoccam
import os

print("=" * 60)
print("PyOccam CSV Conversion & Lookup Tables Demo")
print("=" * 60)

# Helper: find a file in CWD first, then fall back to package directory
def find_sample(filename):
    if os.path.exists(filename):
        return filename
    pkg_path = os.path.join(os.path.dirname(pyoccam.__file__), filename)
    if os.path.exists(pkg_path):
        return pkg_path
    raise FileNotFoundError(
        f"{filename} not found. Run: pyoccam.get_demo_script('csv', copy_to_current=True)")

SAMPLE_CSV = find_sample("sample_mydata.csv")

# ──────────────────────────────────────────────────────────
# PART 1: Basic CSV conversion
# ──────────────────────────────────────────────────────────
print("\n── Part 1: Convert CSV to OCCAM format ──\n")

# The sample CSV has:
#   site_id      - unique IDs (will be auto-excluded, cardinality > 20)
#   elevation_m  - continuous values (will be auto-excluded, cardinality > 20)
#   slope_class  - 4 text categories: flat, gentle, moderate, steep
#   soil_type    - 6 soil orders: Andisols, Inceptisols, etc.
#   vegetation   - 8 NLCD-style land cover categories
#   geology      - 4 rock type categories
#   drainage     - 6 drainage class categories
#   risk         - binary DV (0 = no risk, 1 = risk)

output_file, data = pyoccam.make_occam_input_from_csv(SAMPLE_CSV)

print(f"\nResult: {data}")
print(f"Output file: {output_file}")

# ──────────────────────────────────────────────────────────
# PART 2: Explore the lookup tables
# ──────────────────────────────────────────────────────────
print("\n── Part 2: Using Lookup Tables ──\n")

# The converter automatically saved a _lookups.csv file
# AND attached the lookups to the data object
print(f"Variables with lookups: {list(data.lookups.keys())}")

# Decode soil types
print("\nSoil type encoding:")
for code, name in sorted(data.lookups['soil_type'].items()):
    print(f"  {code} = {name}")

# Decode vegetation
print("\nVegetation encoding:")
for code, name in sorted(data.lookups['vegetation'].items()):
    print(f"  {code} = {name}")

# The lookup file is a standard CSV you can open in Excel
lookups_file = output_file.replace('.txt', '_lookups.csv')
print(f"\nLookup CSV saved to: {lookups_file}")

# You can also reload lookups from the CSV at any time
reloaded = pyoccam.load_lookups(lookups_file)
print(f"Reloaded {len(reloaded)} variable lookups from CSV")

# ──────────────────────────────────────────────────────────
# PART 3: Search and Fit on converted data
# ──────────────────────────────────────────────────────────
print("\n── Part 3: Search and Fit on Converted Data ──\n")

manager = data.manager

# Run search
report = manager.generate_search_report("full-up", 7, 3)
print(report)

# Pick best model by AIC (good balance for small datasets)
best = manager.get_best_model_by_aic()
print(f"Best model (AIC): {best}")

# Fit the best model
print(f"\nFitting model: {best}")
fit_report = manager.generate_fit_report(best)
print(fit_report)

# ──────────────────────────────────────────────────────────
# PART 4: Train/test split with confusion matrix
# ──────────────────────────────────────────────────────────
print("\n── Part 4: Train/Test Split with Validation ──\n")

output_file2, data2 = pyoccam.make_occam_input_from_csv(
    SAMPLE_CSV,
    output_filename="sample_mydata_split.txt",
    test_split=0.2,
    random_state=42,
    exclude_columns=["site_id"]   # explicit exclude (elevation_m still auto-excluded)
)

print(f"\nHas test data: {data2.has_test_data}")
print(f"Result: {data2}")

# Search
manager2 = data2.manager
report2 = manager2.generate_search_report("full-up", 7, 3)
best2 = manager2.get_best_model_by_aic()
print(f"Best model (AIC): {best2}")

# Fit the best model
print(f"\nFitting model: {best2}")
fit_report2 = manager2.generate_fit_report(best2)
print(fit_report2)

# Extract confusion matrix (target_state="0" = no risk)
cm = None  # Will be passed to FitReportAnalyzer in Part 6
try:
    cm = manager2.get_confusion_matrix(best2, target_state="0")
    print("\nConfusion Matrix Results:")
    print(f"  Train accuracy: {cm['train_accuracy']:.1%}")
    print(f"  Train:  TP={cm['train_tp']:4.0f}  FP={cm['train_fp']:4.0f}")
    print(f"          FN={cm['train_fn']:4.0f}  TN={cm['train_tn']:4.0f}")
    if data2.has_test_data and 'test_accuracy' in cm:
        print(f"\n  Test accuracy:  {cm['test_accuracy']:.1%}")
        print(f"  Test:   TP={cm['test_tp']:4.0f}  FP={cm['test_fp']:4.0f}")
        print(f"          FN={cm['test_fn']:4.0f}  TN={cm['test_tn']:4.0f}")
except Exception as e:
    print(f"\n  (Confusion matrix not available for this model: {e})")
    print("  This can happen with very small datasets or simple models.")

# ──────────────────────────────────────────────────────────
# PART 5: Bundled dataset lookups (landslides)
# ──────────────────────────────────────────────────────────
print("\n── Part 5: Bundled Dataset Lookups ──\n")

ls = pyoccam.load_landslides()
print(f"Landslides dataset: {ls}")

# Decode some variables from the bundled lookups
print("\nSoil Taxonomic Orders in landslides dataset:")
for code, name in sorted(ls.lookups['TaxOrder'].items()):
    print(f"  {code} = {name}")

print("\nRock types:")
for code, name in sorted(ls.lookups['Geol_rock_Type'].items()):
    print(f"  {code} = {name}")

print(f"\nTotal variables with lookups: {len(ls.lookups)}")

# ──────────────────────────────────────────────────────────
# PART 6: Fit Report Analyzer
# ──────────────────────────────────────────────────────────
print("\n── Part 6: Fit Report Analyzer ──\n")

# The FitReportAnalyzer parses fit report text and automatically identifies:
#   - Model quality (information capture, LR statistics)
#   - Interesting conditional DV patterns (high/low accuracy combos)
#   - Confusion matrix performance insights
#   - Actionable recommendations

from pyoccam import FitReportAnalyzer

# We already have fit_report2 and cm from Part 4 -- analyze them!
print("Analyzing the fit report from Part 4...\n")
analyzer = FitReportAnalyzer(fit_report2, cm_dict=cm)
analyzer.print_summary()

# You can also get the findings as a structured dict for programmatic use:
findings = analyzer.analyze()
print(f"\nProgrammatic access examples:")
print(f"  Overview: {findings['overview'].get('info_capture', 'N/A')}")
print(f"  Patterns found: {len(findings['conditional_patterns'])}")
print(f"  Recommendations: {len(findings['recommendations'])}")

# ──────────────────────────────────────────────────────────
# Cleanup
# ──────────────────────────────────────────────────────────
print("\n── Cleanup ──\n")
print("Generated files:")
for f in ["sample_mydata.txt", "sample_mydata_lookups.csv",
          "sample_mydata_split.txt", "sample_mydata_split_lookups.csv"]:
    if os.path.exists(f):
        print(f"  {f} ({os.path.getsize(f):,} bytes)")

print("\nDone! These files can be safely deleted or kept for reference.")
