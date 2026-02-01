#!/usr/bin/env python3
"""
Example: Complete Configuration Template

This shows ALL available configuration options in analyze_fit.py.
Copy this template and adjust thresholds to suit your needs.
"""

# ============================================================================
# BASIC CONFIGURATION
# ============================================================================

FIT_REPORT_FILE = '/mnt/project/dementia05_fit_IV_ApZ_EdZ_CZ.csv'
OUTPUT_FILE = None  # Set to filename to save output

# ============================================================================
# CONDITIONAL DV PATTERN THRESHOLDS
# ============================================================================

# What counts as "high" or "low" accuracy?
HIGH_ACCURACY_THRESHOLD = 90   # % - States with this accuracy or higher are "high"
LOW_ACCURACY_THRESHOLD = 60    # % - States below this are flagged as "low"

# Sample size requirements for different analyses
SPARSE_DATA_THRESHOLD = 5       # Minimum samples to trust predictions at all
MIN_FREQ_FOR_LOW_ACCURACY = 10  # Minimum samples before flagging low accuracy
MIN_FREQ_FOR_SIGNIFICANCE = 10  # Minimum samples to report significant rules
MIN_FREQ_FOR_MISMATCH = 10      # Minimum samples to report obs vs pred mismatches

# Statistical thresholds
SIGNIFICANCE_THRESHOLD = 0.05       # p-value: below this is "significant"
LARGE_MISMATCH_THRESHOLD = 20       # % difference between observed and predicted

# ============================================================================
# OVERVIEW ASSESSMENT THRESHOLDS
# ============================================================================

# Information capture levels (%)
# These determine how we describe the model's complexity capture
INFO_CAPTURE_LOW = 10       # Below this = "Low information capture"
INFO_CAPTURE_MODERATE = 30  # Below this = "Moderate" (otherwise check high threshold)
INFO_CAPTURE_HIGH = 60      # Above this = "High information capture"

# Transmission (T) strength thresholds
# These describe the IV:DV relationship strength
TRANSMISSION_WEAK = 0.3     # Below this = "weak relationship"
TRANSMISSION_STRONG = 0.7   # Above this = "strong relationship"
# (Between weak and strong = "moderate relationship")

# ============================================================================
# MODEL QUALITY THRESHOLDS
# ============================================================================

# p-value significance levels for likelihood ratio tests
P_HIGHLY_SIGNIFICANT = 0.001  # p < this = "highly significant"
P_SIGNIFICANT = 0.05          # p < this = "significant" (otherwise "not significant")

# ============================================================================
# CONFUSION MATRIX THRESHOLDS
# ============================================================================

# Overall accuracy level boundaries (%)
ACCURACY_EXCELLENT = 80  # >= this = "Excellent"
ACCURACY_GOOD = 70       # >= this = "Good"
ACCURACY_MODERATE = 60   # >= this = "Moderate" (otherwise "Poor")

# Performance metric thresholds (0.0 to 1.0)
LOW_SENSITIVITY_THRESHOLD = 0.5   # Below this triggers "Low sensitivity" warning
LOW_SPECIFICITY_THRESHOLD = 0.5   # Below this triggers "Low specificity" warning
LOW_F1_THRESHOLD = 0.5            # Below this triggers "Low F1" warning

# Class balance threshold
CLASS_IMBALANCE_THRESHOLD = 20  # % deviation from 50% to flag as "imbalanced"
# (e.g., 70/30 split would be 20% away from 50%, so flagged as imbalanced)

# ============================================================================
# RUN THE ANALYSIS
# ============================================================================

from analyze_fit import FitReportAnalyzer
import analyze_fit

# Apply all the configuration settings
analyze_fit.FIT_REPORT_FILE = FIT_REPORT_FILE
analyze_fit.OUTPUT_FILE = OUTPUT_FILE

analyze_fit.HIGH_ACCURACY_THRESHOLD = HIGH_ACCURACY_THRESHOLD
analyze_fit.LOW_ACCURACY_THRESHOLD = LOW_ACCURACY_THRESHOLD
analyze_fit.SPARSE_DATA_THRESHOLD = SPARSE_DATA_THRESHOLD
analyze_fit.MIN_FREQ_FOR_LOW_ACCURACY = MIN_FREQ_FOR_LOW_ACCURACY
analyze_fit.MIN_FREQ_FOR_SIGNIFICANCE = MIN_FREQ_FOR_SIGNIFICANCE
analyze_fit.MIN_FREQ_FOR_MISMATCH = MIN_FREQ_FOR_MISMATCH
analyze_fit.SIGNIFICANCE_THRESHOLD = SIGNIFICANCE_THRESHOLD
analyze_fit.LARGE_MISMATCH_THRESHOLD = LARGE_MISMATCH_THRESHOLD

analyze_fit.INFO_CAPTURE_LOW = INFO_CAPTURE_LOW
analyze_fit.INFO_CAPTURE_MODERATE = INFO_CAPTURE_MODERATE
analyze_fit.INFO_CAPTURE_HIGH = INFO_CAPTURE_HIGH
analyze_fit.TRANSMISSION_WEAK = TRANSMISSION_WEAK
analyze_fit.TRANSMISSION_STRONG = TRANSMISSION_STRONG

analyze_fit.P_HIGHLY_SIGNIFICANT = P_HIGHLY_SIGNIFICANT
analyze_fit.P_SIGNIFICANT = P_SIGNIFICANT

analyze_fit.ACCURACY_EXCELLENT = ACCURACY_EXCELLENT
analyze_fit.ACCURACY_GOOD = ACCURACY_GOOD
analyze_fit.ACCURACY_MODERATE = ACCURACY_MODERATE
analyze_fit.LOW_SENSITIVITY_THRESHOLD = LOW_SENSITIVITY_THRESHOLD
analyze_fit.LOW_SPECIFICITY_THRESHOLD = LOW_SPECIFICITY_THRESHOLD
analyze_fit.LOW_F1_THRESHOLD = LOW_F1_THRESHOLD
analyze_fit.CLASS_IMBALANCE_THRESHOLD = CLASS_IMBALANCE_THRESHOLD

# Load and analyze
with open(FIT_REPORT_FILE, 'r') as f:
    report = f.read()

analyzer = FitReportAnalyzer(report)
analyzer.print_summary()

print("\n" + "=" * 80)
print("CONFIGURATION USED")
print("=" * 80)
print(f"""
Accuracy Thresholds:
  High accuracy: ≥{HIGH_ACCURACY_THRESHOLD}%
  Low accuracy: <{LOW_ACCURACY_THRESHOLD}%
  
Sample Size Requirements:
  Sparse data: <{SPARSE_DATA_THRESHOLD} samples
  Low accuracy flagging: ≥{MIN_FREQ_FOR_LOW_ACCURACY} samples
  Significance reporting: ≥{MIN_FREQ_FOR_SIGNIFICANCE} samples
  Mismatch reporting: ≥{MIN_FREQ_FOR_MISMATCH} samples
  
Statistical:
  Significance: p<{SIGNIFICANCE_THRESHOLD}
  Large mismatch: >{LARGE_MISMATCH_THRESHOLD}% difference
  
Information Capture:
  Low: <{INFO_CAPTURE_LOW}%
  Moderate: {INFO_CAPTURE_LOW}-{INFO_CAPTURE_HIGH}%
  High: >{INFO_CAPTURE_HIGH}%
  
Transmission:
  Weak: <{TRANSMISSION_WEAK}
  Moderate: {TRANSMISSION_WEAK}-{TRANSMISSION_STRONG}
  Strong: >{TRANSMISSION_STRONG}
  
Confusion Matrix:
  Excellent accuracy: ≥{ACCURACY_EXCELLENT}%
  Good accuracy: ≥{ACCURACY_GOOD}%
  Moderate accuracy: ≥{ACCURACY_MODERATE}%
  Low metric threshold: <{LOW_SENSITIVITY_THRESHOLD}
  Class imbalance: >{CLASS_IMBALANCE_THRESHOLD}% deviation from 50/50
""")
