#!/usr/bin/env python3
"""
PyOccam Demo - Getting Started with Reconstructability Analysis
================================================================

This script walks through the standard OCCAM workflow:
1. Load data
2. Search for the best model
3. Examine search results
4. Fit the best model
5. Extract confusion matrix metrics
6. Automatic fit report analysis

Uses the bundled dementia dataset (424 patients, 18 features).
For advanced features, see pyoccam_demo_advanced.py
"""

import pyoccam

print(f"PyOccam {pyoccam.__version__} - Getting Started Demo")
print("=" * 60)

# ==============================================================================
# STEP 1: LOAD DATA
# ==============================================================================
print("\nSTEP 1: Load Data")
print("-" * 40)

data = pyoccam.load_dementia()

print(f"  Dataset:  {data}")
print(f"  Samples:  {data.n_samples}")
print(f"  Features: {data.n_features}")
print(f"  Target:   {data.target_name}")
print(f"\n  Feature variables:")
for i, name in enumerate(data.feature_names):
    print(f"    {i+1:2d}. {name}")

# ==============================================================================
# STEP 2: SEARCH FOR BEST MODEL
# ==============================================================================
print("\nSTEP 2: Search for Best Model")
print("-" * 40)

manager = data.manager

# Run a full-up search (finds models with loops — richer than loopless)
print("Running full-up search (levels=5, width=3)...")
search_report = manager.generate_search_report(
    search_type="full-up",
    levels=5,
    width=3
)

# ==============================================================================
# STEP 3: EXAMINE SEARCH RESULTS
# ==============================================================================
print("\nSTEP 3: Examine Search Results")
print("-" * 40)

best_bic = manager.get_best_model_by_bic()
best_aic = manager.get_best_model_by_aic()
best_info = manager.get_best_model_by_information()

print(f"  Best by BIC (conservative):   {best_bic}")
print(f"  Best by AIC (moderate):        {best_aic}")
print(f"  Best by Information:           {best_info}")

# ==============================================================================
# STEP 4: FIT THE BEST MODEL
# ==============================================================================
print("\nSTEP 4: Fit the Best Model")
print("-" * 40)

# AIC strikes a nice balance -- more interesting than the conservative BIC
print(f"Fitting model: {best_aic}")
fit_report = manager.generate_fit_report(best_aic, target_state="0")

# Print the full fit report -- includes conditional DV tables
# and confusion matrix with all statistics
print("\nFit Report:")
print("=" * 60)
print(fit_report)

# ==============================================================================
# STEP 5: EXTRACT CONFUSION MATRIX
# ==============================================================================
print("\nSTEP 5: Confusion Matrix Metrics")
print("-" * 40)

# get_confusion_matrix() returns a dict with sklearn-compatible keys:
#   train_tn, train_fp, train_fn, train_tp, train_accuracy, etc.
cm = manager.get_confusion_matrix(best_aic, target_state="0")

if cm.get('has_values', False):
    print(f"  Model:       {best_aic}")
    print(f"  Accuracy:    {cm['train_accuracy']:.1%}")
    print(f"  Sensitivity: {cm['train_sensitivity']:.1%}")
    print(f"  Specificity: {cm['train_specificity']:.1%}")
    print(f"  Precision:   {cm['train_precision']:.1%}")
    print(f"  F1 Score:    {cm['train_f1_score']:.1%}")
    print(f"\n  TP={cm['train_tp']:4.0f}  FP={cm['train_fp']:4.0f}")
    print(f"  FN={cm['train_fn']:4.0f}  TN={cm['train_tn']:4.0f}")

# ==============================================================================
# STEP 6: AUTOMATIC FIT REPORT ANALYSIS
# ==============================================================================
print("\nSTEP 6: Automatic Fit Report Analysis")
print("-" * 40)
print("The FitReportAnalyzer automatically identifies notable patterns:")
print()

from pyoccam import FitReportAnalyzer

# Pass both the text report AND the CM dict for complete analysis
analyzer = FitReportAnalyzer(fit_report, cm_dict=cm)
analyzer.print_summary()

# Programmatic access to findings:
findings = analyzer.analyze()
print(f"\nProgrammatic access:")
print(f"  Patterns found: {len(findings['conditional_patterns'])}")
print(f"  Recommendations: {len(findings['recommendations'])}")
print(f"  Confusion matrices: {len(findings['confusion_insights'])}")

# ==============================================================================
# DONE
# ==============================================================================
print("\n" + "=" * 60)
print("Demo Complete!")
print("=" * 60)
print("""
Next steps:
  pyoccam.help()                          # Quick reference
  pyoccam.load_landslides()               # Try the landslides dataset
  pyoccam.get_demo_script('advanced')     # Get the advanced demo

Key pattern -- always reload data for a new search:
  data = pyoccam.load_dementia()          # Fresh manager each time
  best = data.quick_search("full-up", 5, 3)
""")
