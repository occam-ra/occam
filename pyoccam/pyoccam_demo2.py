#!/usr/bin/env python3
"""
PyOccam Demo - Simple but Powerful OCCAM Analysis
=================================================

This script demonstrates the core OCCAM workflow:
1. Load data
2. Run search to find best models  
3. Fit a specific model (user can specify)
4. Display results and save to files

Usage:
    python pyoccam_demo.py                    # Use defaults
    python pyoccam_demo.py mydata.txt         # Use your data
"""

import pyoccam
import os
import sys
from datetime import datetime

# =============================================================================
# CONFIGURATION - Modify these as needed
# =============================================================================

# Default settings
DEFAULT_DATA_FILE = "dementia05.txt"
SEARCH_TYPE = "loopless-up"           # loopless-up or full-up
SEARCH_LEVELS = 5                     # Search depth (3-7 recommended)
SEARCH_WIDTH = 3                      # Models to keep per level (3-5 recommended)

# Report settings
REPORT_VARIABLES = "Level$I, h, ddf, dLR, Alpha, %dH(DV), dAIC, dBIC"
SELECTION_CRITERION = "BIC"           # BIC, AIC, or Information

# Output settings
OUTPUT_FORMAT = "space"               # space, tab, or comma
SAVE_TO_FILES = True                  # Save results to files?

print("="*70)
print("PYOCCAM DEMO - Simple but Powerful OCCAM Analysis")
print("="*70)
print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

# =============================================================================
# STEP 1: LOAD DATA
# =============================================================================

# Determine data file
if len(sys.argv) > 1:
    data_file = sys.argv[1]
    print(f"Using data file from command line: {data_file}")
else:
    data_file = DEFAULT_DATA_FILE
    print(f"Using default data file: {data_file}")

# Check if file exists
if not os.path.exists(data_file):
    print(f"❌ Error: Data file '{data_file}' not found!")
    print("Make sure the file is in the current directory or provide full path.")
    sys.exit(1)

# Initialize OCCAM Manager
print(f"\n📊 Loading data: {data_file}")
print("-" * 40)

manager = pyoccam.VBMManager()
success = manager.init_from_command_line(["occam", data_file])

if not success:
    print(f"❌ Error: Failed to load {data_file}")
    print("Check that the file is properly formatted OCCAM data.")
    sys.exit(1)

print("✅ Data loaded successfully!")

# Display basic information
print(f"\n📈 Dataset Information:")
print("-" * 40)
print(manager.get_basic_statistics())

variables = manager.get_variable_list()
print(f"Variables ({len(variables)}):")
for i, var in enumerate(variables, 1):
    print(f"  {i:2d}. {var}")

# =============================================================================
# STEP 2: CONFIGURE AND RUN SEARCH
# =============================================================================

print(f"\n🔍 Running Search Analysis")
print("-" * 40)
print(f"Algorithm: {SEARCH_TYPE}")
print(f"Levels: {SEARCH_LEVELS}")
print(f"Width: {SEARCH_WIDTH}")
print(f"Selection: {SELECTION_CRITERION}")

# Configure manager
manager.set_report_variables(REPORT_VARIABLES)
if OUTPUT_FORMAT == "comma":
    manager.set_report_separator(pyoccam.COMMASEP)
elif OUTPUT_FORMAT == "tab":
    manager.set_report_separator(pyoccam.TABSEP)
else:
    manager.set_report_separator(pyoccam.SPACESEP)

# Run search
print(f"\n⚡ Searching for best models...")
search_report = manager.generate_search_report(SEARCH_TYPE, SEARCH_LEVELS, SEARCH_WIDTH)

# Get best models
best_bic = manager.get_best_model_by_bic()
best_aic = manager.get_best_model_by_aic()
best_info = manager.get_best_model_by_information()

print(f"✅ Search complete!")
print(f"\n🏆 Best Models Found:")
print(f"  By BIC: {best_bic}")
print(f"  By AIC: {best_aic}")
print(f"  By Information: {best_info}")

# Select model based on criterion
if SELECTION_CRITERION == "BIC":
    selected_model = best_bic
elif SELECTION_CRITERION == "AIC":
    selected_model = best_aic
else:
    selected_model = best_info

print(f"\n🎯 Selected model ({SELECTION_CRITERION}): {selected_model}")

# =============================================================================
# STEP 3: SAVE SEARCH RESULTS
# =============================================================================

if SAVE_TO_FILES:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    search_filename = f"occam_search_{timestamp}.txt"
    
    print(f"\n💾 Saving search results to: {search_filename}")
    manager.write_report(search_filename)
    print(f"✅ Search report saved!")

# =============================================================================
# STEP 4: USER MODEL INPUT (Interactive)
# =============================================================================

print(f"\n🎛️  Model Fitting Options")
print("-" * 40)
print(f"1. Fit the selected model: {selected_model}")
print(f"2. Enter your own model to fit")
print(f"3. Skip fitting")

try:
    choice = input("Choose option (1-3, or press Enter for option 1): ").strip()
    
    if choice == "2":
        print("\nEnter your model (e.g., 'IV:ABC', 'IV:A:BC', etc.):")
        custom_model = input("Model: ").strip()
        if custom_model:
            fit_model = custom_model
            print(f"Will fit your model: {fit_model}")
        else:
            fit_model = selected_model
            print(f"No model entered, using selected: {fit_model}")
    elif choice == "3":
        fit_model = None
        print("Skipping model fitting.")
    else:
        fit_model = selected_model
        print(f"Using selected model: {fit_model}")
        
except KeyboardInterrupt:
    print(f"\nUsing selected model: {selected_model}")
    fit_model = selected_model

# =============================================================================
# STEP 5: FIT MODEL AND DISPLAY RESULTS
# =============================================================================

if fit_model:
    print(f"\n⚙️  Fitting Model: {fit_model}")
    print("-" * 40)
    
    try:
        fit_report = manager.generate_fit_report(fit_model)
        print(f"✅ Model fit complete!")
        
        # Display fit summary
        print(f"\n📊 Fit Results Summary:")
        print("-" * 40)
        print(f"Model: {fit_model}")
        
        # Save fit report
        if SAVE_TO_FILES:
            fit_filename = f"occam_fit_{fit_model.replace(':', '_')}_{timestamp}.txt"
            # Remove invalid filename characters
            fit_filename = "".join(c for c in fit_filename if c.isalnum() or c in "._-")
            
            print(f"\n💾 Saving fit report to: {fit_filename}")
            manager.write_fit_report(fit_filename)
            print(f"✅ Fit report saved!")
            
    except Exception as e:
        print(f"❌ Error fitting model '{fit_model}': {e}")
        print("Make sure the model syntax is correct (e.g., 'IV:ABC' or 'IV:A:BC')")

# =============================================================================
# STEP 6: SUMMARY AND FILES GENERATED
# =============================================================================

print(f"\n📋 Analysis Summary")
print("="*70)
print(f"Data file: {os.path.basename(data_file)}")
print(f"Sample size: {manager.get_sample_size()}")
print(f"Variables: {len(variables)}")
print(f"Search algorithm: {SEARCH_TYPE}")
print(f"Search levels: {SEARCH_LEVELS}")
print(f"Search width: {SEARCH_WIDTH}")
print(f"Selection criterion: {SELECTION_CRITERION}")
print(f"Best model: {selected_model}")

if SAVE_TO_FILES:
    print(f"\n📁 Files Generated:")
    if 'search_filename' in locals():
        print(f"  • Search report: {search_filename}")
    if 'fit_filename' in locals():
        print(f"  • Fit report: {fit_filename}")

print(f"\n✨ Next Steps:")
print(f"  1. Review the search report to understand model space")
if fit_model:
    print(f"  2. Examine the fit report for detailed model statistics")
print(f"  3. Try different search parameters for comparison")
print(f"  4. Consider fitting other models from the search results")

print(f"\n🎉 Analysis complete! {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("="*70)
