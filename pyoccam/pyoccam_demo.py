#!/usr/bin/env python3
"""
PyOccam Demo - Traditional OCCAM Workflow with Data Objects
Following the standard OCCAM manual approach:
1. Load data (as data objects)
2. Search for best model
3. Examine search results
4. Fit the best model
5. Examine fit results
"""

import pyoccam
import os
import time
from datetime import datetime

data = pyoccam.load_landslides()

# Configuration
DATA_NAME = "stratified_300k_binary_dv_5class_hdr.txt"                # Which dataset: "dementia" or "landslides"
SEARCH_TYPE = "full-up"           # Algorithm: loopless-up or full-up
SEARCH_LEVELS = 7                     # Search depth in lattice
SEARCH_WIDTH = 3                      # Models to keep at each level
TARGET_STATE = "0"                    # For confusion matrix (DV negative state)
OUTPUT_FORMAT = "tab"                # Output format: space, tab, or comma

print("="*70)
print("PYOCCAM DEMO - TRADITIONAL OCCAM WORKFLOW")
print("="*70)
print(f"Configuration:")
print(f"  Dataset: {DATA_NAME}")
print(f"  Search: {SEARCH_TYPE}, levels={SEARCH_LEVELS}, width={SEARCH_WIDTH}")
print(f"  Output format: {OUTPUT_FORMAT}")
print(f"  Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("="*70)

# ==============================================================================
# STEP 1: LOAD DATA (As Data Objects)
# ==============================================================================
print("\nSTEP 1: Load Data")
print("-" * 40)

# Load data using the appropriate function
if DATA_NAME == "dementia":
    data = pyoccam.load_dementia()
elif DATA_NAME == "landslides":
    data = pyoccam.load_landslides()
else:
    # Load custom data file - assumes file is in current directory
    data = pyoccam.load_data(DATA_NAME)

# Display data information (sklearn-style attributes)
print(f"\nDataset Information:")
print(f"  Data file: {os.path.basename(data.data_file)}")
print(f"  Samples: {data.n_samples}")
print(f"  Features: {data.n_features}")
print(f"  Target: {data.target_name}")
print(f"  Test data: {'Yes' if data.has_test_data else 'No'}")

# Show feature names
print(f"\nFeature variables ({data.n_features}):")
for i, var in enumerate(data.feature_names[:10], 1):  # Show first 10
    print(f"  {i:2d}. {var}")
if len(data.feature_names) > 10:
    print(f"  ... and {len(data.feature_names)-10} more")

# ==============================================================================
# STEP 2: CONFIGURE SEARCH
# ==============================================================================
print("\nSTEP 2: Configure Search Settings")
print("-" * 40)

# Get the manager from the data object
manager = data.manager

# Set output format
if OUTPUT_FORMAT == "comma":
    manager.set_report_separator(pyoccam.COMMASEP)
elif OUTPUT_FORMAT == "tab":
    manager.set_report_separator(pyoccam.TABSEP)
else:
    manager.set_report_separator(pyoccam.SPACESEP)

# IMPORTANT: Don't include ID or Model - they're added automatically!
manager.set_report_variables("Level$I, h, ddf, dLR, Alpha, Inf, %dH(DV), dAIC, dBIC")
manager.set_ref_model("bottom")

print("✓ Configuration set:")
print(f"  Reference model: bottom")
print(f"  Output format: {OUTPUT_FORMAT}")

# ==============================================================================
# STEP 3: RUN SEARCH
# ==============================================================================
print("\nSTEP 3: Search for Best Models")
print("-" * 40)
print(f"Running {SEARCH_TYPE} search...")
print(f"  Levels: {SEARCH_LEVELS}")
print(f"  Width: {SEARCH_WIDTH}")

start_time = time.time()

# Run search using the manager
search_report = manager.generate_search_report(
    search_type=SEARCH_TYPE,
    levels=SEARCH_LEVELS,
    width=SEARCH_WIDTH,
    include_test_data=data.has_test_data  # Use data object's test data status
)

elapsed = time.time() - start_time
print(f"\n✓ Search completed in {elapsed:.2f} seconds")

# ==============================================================================
# STEP 4: EXAMINE SEARCH RESULTS
# ==============================================================================
print("\nSTEP 4: Examine Search Results")
print("-" * 40)

# Get best models by different criteria
best_bic = manager.get_best_model_by_bic()
best_aic = manager.get_best_model_by_aic()
best_info = manager.get_best_model_by_information()

print("Best models found:")
print(f"  By BIC:         {best_bic}")
print(f"  By AIC:         {best_aic}")
print(f"  By Information: {best_info}")
print(f"\nTotal models kept: {manager.get_search_model_count()}")

# Display search report (first part)
print("\nSearch Report (first 30 lines):")
print("="*70)
lines = search_report.split('\n')
for line in lines[:30]:
    print(line)
if len(lines) > 30:
    print(f"... ({len(lines)-30} more lines)")

# Save search report
search_filename = f"search_{SEARCH_TYPE}_{DATA_NAME}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
with open(search_filename, 'w') as f:
    f.write(search_report)
print(f"\n✓ Search report saved to: {search_filename}")

# ==============================================================================
# STEP 5: FIT THE BEST MODEL
# ==============================================================================
print("\nSTEP 5: Fit the Best Model")
print("-" * 40)

if best_bic:
    print(f"Generating fit report for: {best_bic}")
    print(f"Target state for confusion matrix: {TARGET_STATE}")
    
    start_fit = time.time()
    
    # Generate comprehensive fit report
    fit_report = manager.generate_fit_report(best_bic, TARGET_STATE)
    
    elapsed_fit = time.time() - start_fit
    print(f"\n✓ Fit report generated in {elapsed_fit:.2f} seconds")
    
    # ==============================================================================
    # STEP 6: EXAMINE FIT RESULTS
    # ==============================================================================
    print("\nSTEP 6: Examine Fit Results")
    print("-" * 40)
    
    # Check what's in the report
    components = []
    if "Conditional" in fit_report or "CONDITIONAL" in fit_report:
        components.append("Conditional probability tables")
    if "Confusion" in fit_report or "CONFUSION" in fit_report:
        components.append("Confusion matrix")
    if "Residuals" in fit_report or "RESIDUALS" in fit_report:
        components.append("Residuals")
    
    print(f"Report contains: {', '.join(components) if components else 'Standard fit statistics'}")
    
    # Display key sections
    print("\nFit Report (first 50 lines):")
    print("="*70)
    fit_lines = fit_report.split('\n')
    for line in fit_lines[:50]:
        print(line)
    if len(fit_lines) > 50:
        print(f"... ({len(fit_lines)-50} more lines)")
    
    # Save fit report
    fit_filename = f"fit_{best_bic.replace(':', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    with open(fit_filename, 'w') as f:
        f.write(fit_report)
    print(f"\n✓ Fit report saved to: {fit_filename}")
    
    # Get and display model statistics
    print("\nModel Statistics:")
    print("-" * 40)
    try:
        stats = manager.get_model_statistics(best_bic)
        print(f"Model:         {stats.name}")
        print(f"Information:   {stats.information*100:.2f}%")
        print(f"dBIC:          {stats.dbic:.2f}")
        print(f"dAIC:          {stats.daic:.2f}")
        print(f"Alpha:         {stats.alpha:.6f}")
        print(f"% Correct:     {stats.pct_correct_data:.2f}%")
    except:
        print("(Model statistics available in the fit report)")

# ==============================================================================
# ALTERNATIVE: Use Data Object's Convenience Method
# ==============================================================================
print("\n" + "="*70)
print("ALTERNATIVE: Quick Search Method")
print("="*70)
print("You can also use the data object's quick_search() method:")
print('  best = data.quick_search(search_type="full-up", levels=3, width=3)')
print("\nThis runs a search and returns the best model name directly.")

# ==============================================================================
# SUMMARY
# ==============================================================================
print("\n" + "="*70)
print("ANALYSIS COMPLETE")
print("="*70)
print(f"Total time: {time.time() - start_time:.2f} seconds")
print(f"\nOutput files created:")
print(f"  - {search_filename}")
if 'fit_filename' in locals():
    print(f"  - {fit_filename}")

print("\nObjects available for further analysis:")
print("  'data'    - The data object with .n_samples, .feature_names, etc.")
print("  'manager' - The VBMManager (same as data.manager)")

print("\nExample commands:")
print('  data.quick_search("full-up", 5, 5)  # Quick search on this data')
print('  manager.generate_fit_report("IV:ApZ:EdZ", "0")')
print('  stats = manager.get_model_statistics("IV:ApZ")')
print("="*70)