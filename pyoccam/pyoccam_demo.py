#!/usr/bin/env python
"""
pyoccam_demo.py - Canonical demonstration of pyoccam2 functionality

This script demonstrates the complete workflow for using OCCAM through Python:
1. Loading data (with automatic test data detection)
2. Running search algorithms (loopless, full, disjoint, chain)
3. Selecting best models by different criteria (BIC, AIC, Information)
4. Generating detailed fit reports for specific models
5. Outputting results to screen, file, or both

Copyright (c) 2025 Portland State University OCCAM Project
Licensed under GPL v3 or later
"""

import pyoccam2
import sys
import os
from datetime import datetime

# ============================================================================
# CONFIGURATION SECTION - Modify these settings as needed
# ============================================================================

# Data Configuration
DATA_FILE = "stratified_300k_with_dupes_binary_dv_hdr.txt"  # Input data file
# DATA_FILE = "dementia05.txt"  # Alternative example dataset

# Search Configuration
SEARCH_TYPE = "loopless-up"    # Options: loopless-up, full-up, disjoint-up, chain-up
SEARCH_LEVELS = 7               # Number of levels to search
SEARCH_WIDTH = 3                # Beam width (models kept per level)
ALPHA_THRESHOLD = 0.05          # Significance threshold for incremental alpha

# Model Selection
BEST_MODEL_CRITERION = "bic"    # Options: bic, aic, information, info_alpha
# bic: Best by Bayesian Information Criterion (favors simpler models)
# aic: Best by Akaike Information Criterion
# information: Best by information content (% uncertainty reduced)
# info_alpha: Best by information with all incremental alphas < threshold

# Output Configuration
OUTPUT_TO_SCREEN = True         # Print results to console
OUTPUT_TO_FILE = True           # Save results to files
OUTPUT_DIR = "occam_output"     # Directory for output files
OUTPUT_FORMAT = "space"         # Options: space, csv, tab, html

# Fit Report Configuration
GENERATE_FIT_REPORT = True      # Generate detailed fit report for best model
FIT_TARGET_STATE = "0"          # Target state for confusion matrix (for binary DV)
SKIP_RESIDUALS = False          # Skip residual tables in fit report
SKIP_IVI_TABLES = False         # Skip IVI tables in fit report

# Debug Configuration
DEBUG_MODE = False              # Enable detailed debug output

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def create_output_directory():
    """Create output directory if it doesn't exist"""
    if OUTPUT_TO_FILE and not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
        print(f"Created output directory: {OUTPUT_DIR}")

def get_separator_constant(format_name):
    """Convert format name to pyoccam2 separator constant"""
    separators = {
        "tab": pyoccam2.TABSEP,
        "csv": pyoccam2.COMMASEP,
        "space": pyoccam2.SPACESEP,
        "html": pyoccam2.HTMLFORMAT
    }
    return separators.get(format_name.lower(), pyoccam2.SPACESEP)

def save_output(content, filename, description=""):
    """Save output to file and optionally print to screen"""
    if OUTPUT_TO_SCREEN:
        print(content)
    
    if OUTPUT_TO_FILE:
        filepath = os.path.join(OUTPUT_DIR, filename)
        with open(filepath, 'w') as f:
            f.write(content)
        print(f"\n{description} saved to: {filepath}")

def format_header(title, char="=", width=80):
    """Create a formatted header for output"""
    line = char * width
    return f"\n{line}\n{title}\n{line}\n"

# ============================================================================
# MAIN ANALYSIS WORKFLOW
# ============================================================================

def main():
    """
    Main workflow demonstrating pyoccam2 functionality
    """
    
    # Print header
    print(format_header("OCCAM PYTHON INTERFACE (pyoccam2) DEMONSTRATION"))
    print(f"Version: {pyoccam2.__version__}")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Create output directory if needed
    create_output_directory()
    
    # ========================================================================
    # STEP 1: Initialize OCCAM and Load Data
    # ========================================================================
    
    print(format_header("STEP 1: DATA LOADING", "-"))
    
    # Create VBMManager instance (Variable-Based Manager for directed systems)
    manager = pyoccam2.VBMManager()
    
    # Enable debug mode if configured
    if DEBUG_MODE:
        manager.set_debug_mode(True)
        print("Debug mode: ENABLED")
    
    # Load data file
    print(f"Loading data file: {DATA_FILE}")
    success = manager.init_from_command_line(["occam", DATA_FILE])
    
    if not success:
        print(f"ERROR: Failed to load data file '{DATA_FILE}'")
        print("Please check that the file exists and is in valid OCCAM format")
        sys.exit(1)
    
    # Display basic statistics
    stats = manager.get_basic_statistics()
    print("\nData Statistics:")
    print(stats)
    
    # Check for test data
    has_test = manager.has_test_data()
    if has_test:
        print("✓ Test data detected - will include test performance metrics")
    else:
        print("ℹ No test data found - using training data only")
    
    # Get variable information
    variables = manager.get_variable_list()
    print(f"\nVariables ({len(variables)}):")
    if len(variables) <= 20:
        for i, var in enumerate(variables):
            print(f"  {i+1:2d}. {var}")
    else:
        # Show first and last few for large datasets
        for i in range(5):
            print(f"  {i+1:2d}. {variables[i]}")
        print("  ...")
        for i in range(len(variables)-3, len(variables)):
            print(f"  {i+1:2d}. {variables[i]}")
    
    # ========================================================================
    # STEP 2: Configure OCCAM Settings
    # ========================================================================
    
    print(format_header("STEP 2: CONFIGURATION", "-"))
    
    # Set reference model (for computing relative statistics)
    manager.set_ref_model("bottom")  # Use independence model as reference
    print("Reference model: bottom (independence)")
    
    # Set alpha threshold for significance testing
    # Note: This would need to be exposed in the C++ bindings if not already
    print(f"Alpha threshold: {ALPHA_THRESHOLD}")
    
    # Set output format
    separator = get_separator_constant(OUTPUT_FORMAT)
    manager.set_report_separator(separator)
    print(f"Output format: {OUTPUT_FORMAT}")
    
    # Configure fit report options if needed
    if GENERATE_FIT_REPORT:
        manager.set_fit_classifier_target(FIT_TARGET_STATE)
        manager.set_skip_trained_model_table(SKIP_RESIDUALS)
        manager.set_skip_ivi_tables(SKIP_IVI_TABLES)
        print(f"Fit report target state: {FIT_TARGET_STATE}")
    
    # ========================================================================
    # STEP 3: Run Search Algorithm
    # ========================================================================
    
    print(format_header(f"STEP 3: {SEARCH_TYPE.upper()} SEARCH", "-"))
    
    print(f"Search parameters:")
    print(f"  Type: {SEARCH_TYPE}")
    print(f"  Levels: {SEARCH_LEVELS}")
    print(f"  Width: {SEARCH_WIDTH} (models kept per level)")
    print(f"  Test data: {'included' if has_test else 'not available'}")
    
    print(f"\nRunning search...")
    
    # Generate search report
    # include_test_data parameter ensures test columns appear if test data exists
    search_report = manager.generate_search_report(
        search_type=SEARCH_TYPE,
        levels=SEARCH_LEVELS,
        width=SEARCH_WIDTH,
        include_test_data=has_test
    )
    
    # Save search report
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    search_filename = f"{SEARCH_TYPE}_search_{timestamp}.txt"
    save_output(search_report, search_filename, "Search report")
    
    # Also save as CSV if requested
    if OUTPUT_FORMAT != "csv" and OUTPUT_TO_FILE:
        manager.set_report_separator(pyoccam2.COMMASEP)
        csv_report = manager.generate_search_report(
            search_type=SEARCH_TYPE,
            levels=SEARCH_LEVELS,
            width=SEARCH_WIDTH,
            include_test_data=has_test
        )
        csv_filename = f"{SEARCH_TYPE}_search_{timestamp}.csv"
        save_output(csv_report, csv_filename, "CSV search report")
        # Reset separator
        manager.set_report_separator(separator)
    
    # ========================================================================
    # STEP 4: Analyze Search Results and Select Best Model
    # ========================================================================
    
    print(format_header("STEP 4: MODEL SELECTION", "-"))
    
    # Get best models by different criteria
    best_models = {
        "bic": manager.get_best_model_by_bic(),
        "aic": manager.get_best_model_by_aic(),
        "information": manager.get_best_model_by_information(),
        "info_alpha": manager.get_best_model_by_info_alpha()
    }
    
    print("Best models found:")
    for criterion, model_name in best_models.items():
        if model_name:
            print(f"  {criterion.upper():12s}: {model_name}")
        else:
            print(f"  {criterion.upper():12s}: (none found)")
    
    # Select model based on configured criterion
    selected_model = best_models.get(BEST_MODEL_CRITERION)
    
    if not selected_model:
        print(f"\nWARNING: No model found using criterion '{BEST_MODEL_CRITERION}'")
        # Fall back to best by information
        selected_model = best_models.get("information")
        if selected_model:
            print(f"Falling back to best by information: {selected_model}")
    
    if not selected_model:
        print("ERROR: No models found in search results")
        sys.exit(1)
    
    print(f"\n✓ Selected model (by {BEST_MODEL_CRITERION}): {selected_model}")
    
    # Get detailed statistics for selected model
    model_stats = manager.get_model_statistics(selected_model)
    print(f"\nSelected model statistics:")
    print(f"  Entropy (H):        {model_stats.h:.4f}")
    print(f"  Information:        {model_stats.information:.4f} ({model_stats.information*100:.2f}%)")
    print(f"  Degrees of freedom: {model_stats.df:.0f}")
    print(f"  Likelihood ratio:   {model_stats.lr:.4f}")
    print(f"  Alpha (p-value):    {model_stats.alpha:.6f}")
    print(f"  AIC:                {model_stats.aic:.4f}")
    print(f"  BIC:                {model_stats.bic:.4f}")
    print(f"  Delta AIC:          {model_stats.daic:.4f}")
    print(f"  Delta BIC:          {model_stats.dbic:.4f}")
    
    if has_test:
        print(f"  % Correct (train):  {model_stats.pct_correct_data:.2f}%")
        print(f"  % Correct (test):   {model_stats.pct_correct_test:.2f}%")
        print(f"  % Coverage:         {model_stats.pct_coverage:.2f}%")
        print(f"  % Missed (test):    {model_stats.pct_missed_test:.2f}%")
    else:
        print(f"  % Correct (data):   {model_stats.pct_correct_data:.2f}%")
    
    # ========================================================================
    # STEP 5: Generate Detailed Fit Report
    # ========================================================================
    
    if GENERATE_FIT_REPORT:
        print(format_header("STEP 5: FIT REPORT", "-"))
        
        print(f"Generating detailed fit report for: {selected_model}")
        print(f"Target state for confusion matrix: {FIT_TARGET_STATE}")
        
        # Generate fit report
        fit_report = manager.generate_fit_report(
            model_name=selected_model,
            target_state=FIT_TARGET_STATE
        )
        
        # Save fit report
        fit_filename = f"fit_report_{selected_model.replace(':', '_')}_{timestamp}.txt"
        save_output(fit_report, fit_filename, "Fit report")
        
        print("\nFit report includes:")
        print("  • Model statistics and goodness of fit")
        print("  • Contingency table (observed vs expected frequencies)")
        if not SKIP_RESIDUALS:
            print("  • Residual analysis")
        if not SKIP_IVI_TABLES:
            print("  • IVI (Independent Variable Importance) tables")
        print("  • Conditional probability tables")
        print("  • Confusion matrix for prediction accuracy")
        if has_test:
            print("  • Performance on test data")
    
    # ========================================================================
    # STEP 6: Summary and Next Steps
    # ========================================================================
    
    print(format_header("ANALYSIS COMPLETE", "="))
    
    print("Summary of results:")
    print(f"  • Data file: {DATA_FILE}")
    print(f"  • Sample size: {manager.get_sample_size()}")
    print(f"  • Variables: {len(variables)}")
    print(f"  • Search type: {SEARCH_TYPE}")
    print(f"  • Models evaluated: {manager.get_search_model_count()}")
    print(f"  • Best model: {selected_model}")
    print(f"  • Selection criterion: {BEST_MODEL_CRITERION}")
    
    if OUTPUT_TO_FILE:
        print(f"\nAll output files saved to: {OUTPUT_DIR}/")
    
    print("\nNext steps:")
    print("  1. Review the search report to understand the model space")
    print("  2. Examine the fit report for detailed model interpretation")
    print("  3. Consider running alternative search types for comparison")
    print("  4. Try different model selection criteria (BIC vs AIC vs Information)")
    print("  5. If you have test data, validate model performance on held-out data")
    
    print("\nFor more information:")
    print("  • OCCAM manual: https://www.pdx.edu/sysc/research-discrete-multivariate-modeling")
    print("  • GitHub repository: https://github.com/occam-ra/occam")
    
    return 0

# ============================================================================
# SCRIPT ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\nAnalysis interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nERROR: {str(e)}")
        if DEBUG_MODE:
            import traceback
            traceback.print_exc()
        sys.exit(1)