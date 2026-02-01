#!/usr/bin/env python3
"""
Example: Using analyze_fit.py with config settings

This shows how to set up the analyzer with config at the top of the script.
Just edit the FIT_REPORT_FILE and run!
"""

# Copy this template and customize for your analysis

# ============================================================================
# CONFIGURATION - Edit these settings
# ============================================================================

# Path to your fit report file
FIT_REPORT_FILE = '/mnt/project/dementia05_fit_IV_ApZ_EdZ_CZ.csv'

# Optional: Save output to file instead of printing
OUTPUT_FILE = None  # e.g., 'dementia_analysis.txt'

# Optional: Adjust analysis thresholds
HIGH_ACCURACY_THRESHOLD = 90   # % correct for "high accuracy" states
LOW_ACCURACY_THRESHOLD = 60    # % correct for "low accuracy" states
SPARSE_DATA_THRESHOLD = 5      # minimum samples for reliable predictions
SIGNIFICANCE_THRESHOLD = 0.05  # p-value threshold for significance
LARGE_MISMATCH_THRESHOLD = 20  # % difference between observed and predicted

# ============================================================================
# Analysis Code (no need to edit below this line)
# ============================================================================

# Method 1: Direct import and use
from analyze_fit import FitReportAnalyzer

with open(FIT_REPORT_FILE, 'r') as f:
    report = f.read()

analyzer = FitReportAnalyzer(report)

if OUTPUT_FILE:
    import io
    import contextlib
    
    string_buffer = io.StringIO()
    with contextlib.redirect_stdout(string_buffer):
        analyzer.print_summary()
    
    with open(OUTPUT_FILE, 'w') as f:
        f.write(string_buffer.getvalue())
    
    print(f"✓ Analysis complete! Output written to: {OUTPUT_FILE}")
else:
    analyzer.print_summary()

# Method 2: Get structured data for further processing
findings = analyzer.analyze()

# Example: Check if model has issues
has_low_accuracy = any(p['type'] == 'low_accuracy' for p in findings['conditional_patterns'])
if has_low_accuracy:
    print("\n⚠️  Note: Model has some low-accuracy states that may need investigation")

# Example: Report key metrics
print(f"\nKey Metrics:")
print(f"  Information Capture: {findings['overview'].get('info_capture', 'N/A')}")
print(f"  Transmission: {findings['overview'].get('transmission', 'N/A')}")
print(f"  Number of Recommendations: {len(findings['recommendations'])}")
