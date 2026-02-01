# OCCAM Fit Analyzer - Quick Start Guide

## The Simplest Way to Analyze Your Fit Reports

### Step 1: Open `analyze_fit.py` in your editor

Find these lines at the top:

```python
# ============================================================================
# CONFIGURATION - Edit these settings
# ============================================================================

# Path to the fit report file to analyze
FIT_REPORT_FILE = None  # <-- EDIT THIS LINE
```

### Step 2: Set your file path

Change `None` to your fit report file:

```python
FIT_REPORT_FILE = 'dementia05_fit_IV_ApZ_EdZ_CZ.csv'
```

Or use a full path:

```python
FIT_REPORT_FILE = '/path/to/my/fit_report.txt'
```

### Step 3: Run it!

```bash
python analyze_fit.py
```

The analysis prints to your console. Done!

## Want to Save to a File?

Also set:

```python
OUTPUT_FILE = 'my_analysis.txt'
```

Then when you run it:
```bash
python analyze_fit.py
# Prints: Analysis complete! Output written to: my_analysis.txt
```

## Customize the Analysis

Want stricter or more lenient thresholds? Edit these:

```python
# Analysis thresholds (adjust as needed)
HIGH_ACCURACY_THRESHOLD = 90   # % correct for "high accuracy" states
LOW_ACCURACY_THRESHOLD = 60    # % correct for "low accuracy" states
SPARSE_DATA_THRESHOLD = 5      # minimum samples for reliable predictions
SIGNIFICANCE_THRESHOLD = 0.05  # p-value threshold for significance
LARGE_MISMATCH_THRESHOLD = 20  # % difference between observed and predicted
```

### Example: Stricter Analysis

```python
HIGH_ACCURACY_THRESHOLD = 95   # Only report exceptional accuracy
LOW_ACCURACY_THRESHOLD = 70    # Flag more potential problems
SPARSE_DATA_THRESHOLD = 10     # Require more samples for reliability
```

### Example: More Lenient

```python
HIGH_ACCURACY_THRESHOLD = 85   # Broader "high accuracy" definition  
LOW_ACCURACY_THRESHOLD = 50    # Only flag serious problems
SPARSE_DATA_THRESHOLD = 3      # Accept smaller sample sizes
```

## Alternative: Command Line

Don't want to edit the file? Use command line instead:

```bash
python analyze_fit.py your_fit_report.txt
```

Command-line argument overrides the config setting.

## What You Get

The analyzer automatically identifies:

- ✓ **High accuracy states** - where your model predicts exceptionally well
- ⚠️ **Low accuracy states** - problem areas needing investigation  
- ℹ️ **Sparse data warnings** - unreliable predictions due to small samples
- **Significant classification rules** - statistically validated patterns
- **Model quality metrics** - LR tests, information capture, transmission
- **Confusion matrix insights** - sensitivity, specificity, F1 scores
- **Actionable recommendations** - specific next steps

## Examples Included

We've included several example scripts:

1. **example_config_usage.py** - Basic config-based workflow
2. **demo_analyze_fit.py** - Programmatic API usage
3. **example_threshold_comparison.py** - Compare strict vs. standard vs. lenient thresholds

Try them to see different ways to use the analyzer!

## Need Help?

See the full **FIT_ANALYZER_README.md** for:
- Detailed interpretation guide
- What each metric means
- Batch processing examples
- Integration with PyOccam
- Customization options

---

**Pro tip**: Start with the standard thresholds, run your analysis, then adjust thresholds based on what you learn about your data.
