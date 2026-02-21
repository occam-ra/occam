#!/usr/bin/env python
"""
PyOccam Advanced Demo
=====================

This script demonstrates advanced PyOccam features using REAL landslide
susceptibility data from the Oregon Coast Range, including:
1. Loading and exploring real geospatial data
2. Model selection strategies comparison
3. Confusion matrix analysis across models
4. Batch processing patterns
5. CSV conversion for your own data
6. Command line usage examples

For basic usage, see pyoccam_demo.py
"""

import pyoccam
print(f"PyOccam {pyoccam.__version__} - Advanced Demo")
print("=" * 70)

# ============================================================================
# PART 1: Exploring the Landslides Dataset
# ============================================================================

print("\n" + "=" * 70)
print("PART 1: Exploring Real Landslide Susceptibility Data")
print("=" * 70)

# The landslides dataset is rich in categorical variables derived from
# GIS layers. Continuous variables like slope, elevation, and TWI have
# been binned (reclassified) into discrete categories -- a common GIS
# preprocessing step that makes the data ideal for Reconstructability
# Analysis, which operates on discrete/nominal data.

landslides = pyoccam.load_landslides()
print(f"\nDataset: {landslides}")
print(f"Samples: {landslides.n_samples}")
print(f"Features: {landslides.n_features}")
print(f"Target: {landslides.target_name}")
print(f"\nFeature variables:")
for i, name in enumerate(landslides.feature_names):
    print(f"  {i+1:2d}. {name}")

# ============================================================================
# PART 2: Model Selection Strategies Comparison
# ============================================================================

print("\n" + "=" * 70)
print("PART 2: Comparing Model Selection Strategies on Landslides")
print("=" * 70)

manager = landslides.manager

# Run a comprehensive search
print("\nRunning full-up search (levels=7, width=5)...")
report = manager.generate_search_report("full-up", levels=7, width=5)

# Get best models by different criteria
best_bic = manager.get_best_model_by_bic()
best_aic = manager.get_best_model_by_aic()
best_info = manager.get_best_model_by_information()

print("\nBest models by different criteria:")
print(f"  BIC (most conservative):    {best_bic}")
print(f"  AIC (moderate):             {best_aic}")
print(f"  Information (alpha<0.05):   {best_info}")

# ============================================================================
# PART 3: Confusion Matrix Analysis
# ============================================================================

print("\n" + "=" * 70)
print("PART 3: Confusion Matrix Comparison")
print("=" * 70)

import sys, io

print("\nComparing accuracy, sensitivity, and specificity:")
print("-" * 80)
print(f"{'Criterion':<10} {'Model':<42} {'Acc':>6} {'Sens':>6} {'Spec':>6}")
print("-" * 80)

for name, model in [("BIC", best_bic), ("AIC", best_aic), ("Info", best_info)]:
    # Suppress stdout from get_confusion_matrix (it prints fit report text)
    old_stdout = sys.stdout
    sys.stdout = io.StringIO()
    try:
        cm = manager.get_confusion_matrix(model, target_state="0")
    finally:
        sys.stdout = old_stdout
    if cm.get('has_values', False):
        print(f"{name:<10} {model:<42} "
              f"{cm['train_accuracy']:5.1%} "
              f"{cm['train_sensitivity']:5.1%} "
              f"{cm['train_specificity']:5.1%}")

# Show detailed confusion matrix for the BIC model
print(f"\nDetailed confusion matrix for BIC model: {best_bic}")
old_stdout = sys.stdout
sys.stdout = io.StringIO()
try:
    cm = manager.get_confusion_matrix(best_bic, target_state="0")
finally:
    sys.stdout = old_stdout
if cm.get('has_values', False):
    print(f"  TP={cm['train_tp']:4.0f}  FP={cm['train_fp']:4.0f}")
    print(f"  FN={cm['train_fn']:4.0f}  TN={cm['train_tn']:4.0f}")
    print(f"  Precision: {cm['train_precision']:.1%}")
    print(f"  NPV:       {cm['train_npv']:.1%}")

# ============================================================================
# PART 4: Batch Processing - Compare Both Datasets
# ============================================================================

print("\n" + "=" * 70)
print("PART 4: Batch Processing - Comparing Datasets and Search Types")
print("=" * 70)

datasets = [
    ("Dementia", pyoccam.load_dementia),
    ("Landslides", pyoccam.load_landslides),
]

search_configs = [
    ("full-up", 5, 3, "shallow"),
    ("full-up", 7, 5, "deep"),
]

print(f"\n{'Dataset':<12} {'Depth':<16} {'Best Model (BIC)':<40} {'Accuracy':<10}")
print("-" * 80)

for ds_name, loader in datasets:
    for search_type, levels, width, label in search_configs:
        try:
            # Reload data fresh for each search -- the C++ manager
            # cannot be reused across multiple searches
            data = loader()
            mgr = data.manager
            
            report = mgr.generate_search_report(search_type, levels, width)
            best = mgr.get_best_model_by_bic()
            
            # Suppress stdout from get_confusion_matrix (it prints fit report text)
            old_stdout = sys.stdout
            sys.stdout = io.StringIO()
            try:
                cm = mgr.get_confusion_matrix(best, target_state="0")
            finally:
                sys.stdout = old_stdout
            
            acc = cm.get('train_accuracy', 0.0)
            depth_label = f"{label} ({levels}x{width})"
            print(f"{ds_name:<12} {depth_label:<16} {best:<40} {acc:.1%}")
        except Exception as e:
            print(f"{ds_name:<12} {label:<16} ERROR: {e}")

# ============================================================================
# PART 5: CSV Conversion for Your Own Data
# ============================================================================

print("\n" + "=" * 70)
print("PART 5: Converting Your Own CSV Data")
print("=" * 70)

print("""
To use your own CSV data with PyOccam:

  # Basic conversion (last column = DV)
  output_file, data = pyoccam.make_occam_input_from_csv("mydata.csv")

  # With train/test split for validation
  output_file, data = pyoccam.make_occam_input_from_csv(
      "mydata.csv",
      test_split=0.2,               # 20% held out for testing
      random_state=42,              # Reproducible split
      max_cardinality=20,           # Exclude columns with >20 unique values
      dv_column="target",           # Specify DV column by name
      exclude_columns=["ID", "Name"] # Always exclude these columns
  )

  # Then analyze
  best = data.quick_search()
  cm = data.manager.get_confusion_matrix(best, target_state="0")

Or from the command line:

  python -m pyoccam csv2occam mydata.csv --test-split 0.2
  python -m pyoccam csv2occam mydata.csv --dv LS --exclude x,y,Pt_ID
""")

# ============================================================================
# Done
# ============================================================================

print("=" * 70)
print("Advanced Demo Complete!")
print("=" * 70)
print("\nFor more info: pyoccam.help()")
