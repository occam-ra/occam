#!/usr/bin/env python3
"""
OCCAM Python Package Demo
Complete workflow demonstration matching server output
"""

import pyoccam
import os
import time
from datetime import datetime

# Configuration
DATA_FILE = "dementia05.txt"          # Your data file  
SEARCH_TYPE = "loopless-up"           # Algorithm: loopless-up or full-up
SEARCH_LEVELS = 7                     # Search depth in lattice
SEARCH_WIDTH = 3                      # Models to keep at each level
TARGET_STATE = "0"                    # For confusion matrix (DV negative state)
OUTPUT_FORMAT = "space"                # Output format: space, tab, or comma

print("="*70)
print("OCCAM PYTHON PACKAGE DEMO")
print("="*70)
print(f"Configuration:")
print(f"  Data file: {DATA_FILE}")
print(f"  Search: {SEARCH_TYPE}, levels={SEARCH_LEVELS}, width={SEARCH_WIDTH}")
print(f"  Output format: {OUTPUT_FORMAT}")
print(f"  Analysis started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("="*70)

# Check data file exists
if not os.path.exists(DATA_FILE):
    print(f"❌ Error: Data file '{DATA_FILE}' not found")
    print("   Please ensure your data file is in the current directory")
    exit(1)

# ==============================================================================
# INITIALIZATION
# ==============================================================================
print("\n🔧 Initializing OCCAM Manager...")

manager = pyoccam.VBMManager()

# Initialize with data file
args = ["occam", DATA_FILE]
success = manager.init_from_command_line(args)

if not success:
    print("❌ Error: Failed to initialize OCCAM manager")
    print("   Check that your data file exists and is properly formatted")
    exit(1)

print("✅ OCCAM Manager initialized successfully")

# Display dataset information
print("\n📊 Dataset Information:")
print("-" * 40)
print(manager.get_basic_statistics())

# Display variables
variables = manager.get_variable_list()
print(f"\nVariables detected ({len(variables)}):")
for i, var in enumerate(variables, 1):
    print(f"  {i:2d}. {var}")

print(f"\nSample size: {manager.get_sample_size()}")
print(f"Has test data: {manager.has_test_data()}")

# ==============================================================================
# CONFIGURATION
# ==============================================================================
print("\n⚙️ Configuring report settings...")

# Set output format
if OUTPUT_FORMAT == "comma":
    manager.set_report_separator(pyoccam.COMMASEP)
elif OUTPUT_FORMAT == "tab":
    manager.set_report_separator(pyoccam.TABSEP)
else:
    manager.set_report_separator(pyoccam.SPACESEP)

# Set report variables (what columns to show)
manager.set_report_variables("ID$I, Model, Level$I, h, ddf, dLR, Alpha, Inf, %dH(DV), dAIC, dBIC")

# Set reference model for statistics
manager.set_ref_model("bottom")

print("✅ Configuration complete")

# ==============================================================================
# SEARCH PHASE
# ==============================================================================
print("\n" + "="*70)
print("SEARCH PHASE")
print("="*70)
print(f"Performing {SEARCH_TYPE} search...")
print(f"  Levels: {SEARCH_LEVELS}")
print(f"  Width: {SEARCH_WIDTH}")
print()

start_time = time.time()

# Generate search report with automatic best model tracking
search_report = manager.generate_search_report(
    search_type=SEARCH_TYPE,
    levels=SEARCH_LEVELS,
    width=SEARCH_WIDTH,
    include_test_data=False  # Set to True if your data has test data
)

elapsed = time.time() - start_time

print(f"✅ Search completed in {elapsed:.2f} seconds")

# Get best models (these are tracked automatically during search)
best_bic = manager.get_best_model_by_bic()
best_aic = manager.get_best_model_by_aic()
best_info = manager.get_best_model_by_information()

print(f"\n🏆 Best Models Found:")
print(f"  By BIC:         {best_bic}")
print(f"  By AIC:         {best_aic}")
print(f"  By Information: {best_info}")

# Display search report (first 50 lines)
print("\n" + "-"*70)
print("SEARCH REPORT (first 50 lines):")
print("-"*70)
lines = search_report.split('\n')
for i, line in enumerate(lines[:50]):
    print(line)
if len(lines) > 50:
    print(f"... ({len(lines)-50} more lines)")

# Save search report
search_filename = f"search_{SEARCH_TYPE}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
with open(search_filename, 'w') as f:
    f.write(search_report)
print(f"\n💾 Search report saved to: {search_filename}")

# ==============================================================================
# FIT PHASE
# ==============================================================================
if best_bic:
    print("\n" + "="*70)
    print("FIT PHASE")
    print("="*70)
    print(f"Generating detailed fit report for best model: {best_bic}")
    print(f"Target state for confusion matrix: {TARGET_STATE}")
    print()
    
    start_fit = time.time()
    
    # Generate fit report with confusion matrix
    fit_report = manager.generate_fit_report(best_bic, TARGET_STATE)
    
    elapsed_fit = time.time() - start_fit
    
    print(f"✅ Fit report generated in {elapsed_fit:.2f} seconds")
    
    # Check what components are in the report
    components = []
    if "CONDITIONAL PROBABILITY" in fit_report or "Conditional DV" in fit_report:
        components.append("Conditional Probability Tables")
    if "CONFUSION MATRIX" in fit_report or "Confusion Matrix" in fit_report:
        components.append("Confusion Matrix")
    if "RESIDUALS" in fit_report or "Residuals" in fit_report:
        components.append("Residuals")
    
    print(f"\nReport components: {', '.join(components) if components else 'None detected'}")
    
    # Display fit report (first 100 lines)
    print("\n" + "-"*70)
    print("FIT REPORT (first 100 lines):")
    print("-"*70)
    fit_lines = fit_report.split('\n')
    for i, line in enumerate(fit_lines[:100]):
        print(line)
    if len(fit_lines) > 100:
        print(f"... ({len(fit_lines)-100} more lines)")
    
    # Save fit report
    fit_filename = f"fit_{best_bic.replace(':', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    with open(fit_filename, 'w') as f:
        f.write(fit_report)
    print(f"\n💾 Fit report saved to: {fit_filename}")
    
    # Try to get confusion matrix separately if available
    try:
        cm = manager.get_confusion_matrix(best_bic, TARGET_STATE)
        if cm and 'accuracy' in cm:
            print(f"\n📈 Model Performance Metrics:")
            print(f"  Accuracy:    {cm.get('accuracy', 'N/A'):.3f}")
            print(f"  Sensitivity: {cm.get('sensitivity', 'N/A'):.3f}")
            print(f"  Specificity: {cm.get('specificity', 'N/A'):.3f}")
    except:
        pass

# ==============================================================================
# ADDITIONAL FUNCTIONALITY
# ==============================================================================
print("\n" + "="*70)
print("ADDITIONAL FEATURES AVAILABLE")
print("="*70)

print("\n📚 Available Methods:")
print("  • manager.get_variable_list() - Get all variables")
print("  • manager.get_sample_size() - Get sample size")
print("  • manager.has_test_data() - Check for test data")
print("  • manager.get_basic_statistics() - Get data statistics")
print("  • manager.get_available_search_types() - List search algorithms")
print("  • manager.generate_search_report() - Run search")
print("  • manager.generate_fit_report() - Fit specific model")
print("  • manager.get_best_model_by_bic() - Get best BIC model")
print("  • manager.get_best_model_by_aic() - Get best AIC model")
print("  • manager.get_best_model_by_information() - Get best info model")

print("\n🎯 Interactive Usage Examples:")
print('  # Run different search')
print('  report = manager.generate_search_report("full-up", 5, 5, False)')
print('  ')
print('  # Fit specific model')
print('  fit = manager.generate_fit_report("IV:ApZ:EdZ", "0")')
print('  ')
print('  # Get confusion matrix')
print('  cm = manager.get_confusion_matrix("IV:ApZ", "0")')

print("\n" + "="*70)
print(f"✨ OCCAM Analysis Complete!")
print(f"Total execution time: {time.time() - start_time:.2f} seconds")
print("="*70)

# Keep manager available for interactive use
print("\n💡 The 'manager' object is available for interactive exploration.")
print("   You can continue analyzing using the methods shown above.")
