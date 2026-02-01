# OCCAM Fit Report Analyzer

A Python tool for automatically analyzing OCCAM fit reports and identifying notable patterns, outliers, and insights.

## Overview

This analyzer processes OCCAM fit reports (text output from fit operations) and provides:

- **Summary statistics**: Sample size, information capture, transmission values
- **Model quality assessment**: Likelihood ratio tests, significance levels
- **Conditional DV patterns**: High/low accuracy states, sparse data, significant rules
- **Confusion matrix analysis**: Performance metrics, class balance, strengths/weaknesses
- **Actionable recommendations**: Based on the findings

## Getting Started

**1. Open `analyze_fit.py` in your text editor**

**2. Edit the config at the top:**
```python
FIT_REPORT_FILE = 'dementia05_fit_IV_ApZ_EdZ_CZ.csv'  # Your fit report
```

**3. Run it:**
```bash
python analyze_fit.py
```

That's it! The analysis will print to your console. To save to a file, also set:
```python
OUTPUT_FILE = 'my_analysis.txt'
```

## Quick Start

### Method 1: Config-Based Usage (Easiest)

Edit the configuration at the top of `analyze_fit.py`:

```python
# ============================================================================
# CONFIGURATION - Edit these settings
# ============================================================================

# Path to the fit report file to analyze
FIT_REPORT_FILE = 'dementia05_fit_IV_ApZ_EdZ_CZ.csv'

# Optional: Path to save the analysis output
OUTPUT_FILE = 'analysis_output.txt'  # or None to print to console

# Analysis thresholds (adjust as needed)
HIGH_ACCURACY_THRESHOLD = 90   # % correct for "high accuracy" states
LOW_ACCURACY_THRESHOLD = 60    # % correct for "low accuracy" states
SPARSE_DATA_THRESHOLD = 5      # minimum samples for reliable predictions
```

Then just run:
```bash
python analyze_fit.py
```

### Method 2: Command Line Usage

```bash
# Basic usage
python analyze_fit.py your_fit_report.txt

# With captured output
python analyze_fit.py dementia05_fit.csv > analysis_summary.txt
```

**Note**: Command-line argument overrides the config file setting.

### Python API

```python
from analyze_fit import FitReportAnalyzer

# Load a fit report
with open('your_fit_report.txt', 'r') as f:
    report = f.read()

# Create analyzer and print summary
analyzer = FitReportAnalyzer(report)
analyzer.print_summary()

# Or get structured findings
findings = analyzer.analyze()

# Access specific components
print(findings['overview'])
print(findings['model_quality'])
print(findings['conditional_patterns'])
print(findings['confusion_insights'])
print(findings['recommendations'])
```

## What It Analyzes

### 1. Overview Metrics

- **Sample size**: Training and test set sizes
- **Model complexity**: Number of IVs, model structure
- **Information capture**: How much of the data's complexity the model captures
- **Transmission**: Strength of IV:DV relationship

**Interpretation:**
- Information capture < 10%: Model may be too simple
- Information capture 30-60%: Good balance
- Transmission < 0.3: Weak relationships
- Transmission > 0.7: Strong relationships

### 2. Model Quality

- **LR vs. Independence**: Does the model add value over assuming independence?
- **LR vs. Saturated**: Does the model fit the data well?

**Key thresholds:**
- p < 0.001: Highly significant
- p < 0.05: Significant
- p > 0.05: Not significant (potential concern)

### 3. Conditional DV Patterns

Identifies interesting patterns in the conditional DV table:

**High Accuracy States** (≥90% correct, n≥5)
- States where the model predicts extremely well
- Indicates strong signal in these variable combinations

**Low Accuracy States** (<60% correct, n≥10)
- ⚠️ Problem areas where model struggles
- May indicate confounding factors or missing variables
- Should be investigated for data quality issues

**Sparse Data** (n<5)
- ℹ️ States with too few samples for reliable predictions
- Predictions should be interpreted with caution

**Significant Rules** (p<0.05, n≥10)
- States where classification rules are statistically significant
- High confidence predictions

**Prediction Mismatches** (>20% difference between observed and predicted)
- ⚠️ Indicates model misspecification
- Model assumptions may not hold for these states

### 4. Confusion Matrix Performance

For each confusion matrix, analyzes:

**Overall Accuracy**
- Excellent: ≥80%
- Good: 70-80%
- Moderate: 60-70%
- Poor: <60%

**Key Metrics:**
- **Sensitivity (Recall)**: TP / (TP + FN) - ability to identify positives
- **Specificity**: TN / (TN + FP) - ability to identify negatives
- **Precision**: TP / (TP + FP) - accuracy of positive predictions
- **NPV**: TN / (TN + FN) - accuracy of negative predictions
- **F1 Score**: Harmonic mean of precision and sensitivity

**Class Balance:**
- Balanced: 40-60% split
- Imbalanced: >60% or <40% in one class

**Common Issues:**
- Low sensitivity: Many false negatives (missing true cases)
- Low specificity: Many false positives (over-predicting)
- Low F1: Poor overall classification performance

## Understanding the Output

### Symbol Meanings

- ✓ : Positive finding (e.g., significant rules)
- ⚠️ : Warning or concern (e.g., low accuracy)
- ℹ️ : Informational note (e.g., sparse data)

### Example Output Interpretation

```
🎯 CONDITIONAL DV PATTERNS
  IV:ApZ:EdZ:CZ:
    • 3 state(s) with ≥90% prediction accuracy
      - 0,0,1: 100.0% correct (n=12)
```
**Interpretation**: The model predicts perfectly for the state (Ap=0, Ed=0, C=1) based on 12 samples.

```
    • ⚠️ 2 state(s) with <60% accuracy (n≥10)
      - 1,2,0: 45.5% correct (n=22)
```
**Interpretation**: The model struggles with state (Ap=1, Ed=2, C=0), only getting 45.5% correct despite having 22 samples. This suggests confounding factors or data quality issues.

```
🎲 CONFUSION MATRIX PERFORMANCE
  IV:ApZ:EdZ:CZ:
    • Good overall accuracy: 72.5%
    • Strongest: Specificity = 0.856
    • Weakest: Sensitivity = 0.623
    ⚠️  Low sensitivity - many false negatives
```
**Interpretation**: The model is good at identifying negatives (specificity=0.856) but misses many positive cases (sensitivity=0.623). Consider adjusting the classification threshold or adding variables to improve sensitivity.

## Programmatic Usage Examples

### Example 1: Batch Processing

```python
import glob
from analyze_fit import FitReportAnalyzer

# Analyze all fit reports in a directory
for filepath in glob.glob('fit_reports/*.txt'):
    with open(filepath) as f:
        report = f.read()
    
    analyzer = FitReportAnalyzer(report)
    findings = analyzer.analyze()
    
    # Extract key metric
    info_capture = findings['overview'].get('info_capture', 'N/A')
    print(f"{filepath}: {info_capture}")
```

### Example 2: Finding Best Model

```python
from analyze_fit import FitReportAnalyzer

reports = {
    'model1': open('model1_fit.txt').read(),
    'model2': open('model2_fit.txt').read(),
    'model3': open('model3_fit.txt').read(),
}

best_model = None
best_f1 = 0

for name, report in reports.items():
    analyzer = FitReportAnalyzer(report)
    findings = analyzer.analyze()
    
    # Get F1 score from first confusion matrix
    if findings['confusion_insights']:
        f1 = findings['confusion_insights'][0]['f1']
        if f1 > best_f1:
            best_f1 = f1
            best_model = name

print(f"Best model: {best_model} (F1={best_f1:.3f})")
```

### Example 3: Export to DataFrame

```python
import pandas as pd
from analyze_fit import FitReportAnalyzer

with open('fit_report.txt') as f:
    report = f.read()

analyzer = FitReportAnalyzer(report)
findings = analyzer.analyze()

# Convert confusion matrices to DataFrame
cm_df = pd.DataFrame(findings['confusion_insights'])
print(cm_df[['relation', 'pct_correct', 'f1', 'sensitivity', 'specificity']])
```

## Requirements

- Python 3.6+
- NumPy
- Standard library only (re, typing)

## Customization

### Complete Configuration Options

The analyzer includes **24 configurable thresholds** at the top of `analyze_fit.py`. Here's the complete reference:

#### File Paths
```python
FIT_REPORT_FILE = None    # Input fit report file
OUTPUT_FILE = None        # Output file (None = print to console)
```

#### Conditional DV Pattern Thresholds
```python
# Accuracy boundaries
HIGH_ACCURACY_THRESHOLD = 90   # % - States ≥ this are "high accuracy"
LOW_ACCURACY_THRESHOLD = 60    # % - States < this are "low accuracy"

# Sample size requirements
SPARSE_DATA_THRESHOLD = 5       # Min samples for reliable predictions
MIN_FREQ_FOR_LOW_ACCURACY = 10  # Min samples to flag low accuracy
MIN_FREQ_FOR_SIGNIFICANCE = 10  # Min samples to report significant rules
MIN_FREQ_FOR_MISMATCH = 10      # Min samples to report mismatches

# Statistical
SIGNIFICANCE_THRESHOLD = 0.05       # p-value threshold
LARGE_MISMATCH_THRESHOLD = 20       # % obs vs pred difference
```

#### Overview Assessment Thresholds
```python
# Information capture levels (%)
INFO_CAPTURE_LOW = 10       # Below this = "Low"
INFO_CAPTURE_MODERATE = 30  # Below this = "Moderate"
INFO_CAPTURE_HIGH = 60      # Above this = "High"

# Transmission strength
TRANSMISSION_WEAK = 0.3     # Below this = "weak"
TRANSMISSION_STRONG = 0.7   # Above this = "strong"
```

#### Model Quality Thresholds
```python
# p-value significance levels
P_HIGHLY_SIGNIFICANT = 0.001  # Below this = "highly significant"
P_SIGNIFICANT = 0.05          # Below this = "significant"
```

#### Confusion Matrix Thresholds
```python
# Accuracy level boundaries (%)
ACCURACY_EXCELLENT = 80  # >= this = "Excellent"
ACCURACY_GOOD = 70       # >= this = "Good"
ACCURACY_MODERATE = 60   # >= this = "Moderate"

# Performance metrics (0.0 to 1.0)
LOW_SENSITIVITY_THRESHOLD = 0.5   # Triggers warning
LOW_SPECIFICITY_THRESHOLD = 0.5   # Triggers warning
LOW_F1_THRESHOLD = 0.5            # Triggers warning

# Class balance
CLASS_IMBALANCE_THRESHOLD = 20  # % deviation from 50/50
```

### Example Configurations

#### Strict Configuration (Publication Quality)
Catches more potential issues, good for rigorous analysis:

```python
HIGH_ACCURACY_THRESHOLD = 95
LOW_ACCURACY_THRESHOLD = 70
MIN_FREQ_FOR_LOW_ACCURACY = 15
MIN_FREQ_FOR_SIGNIFICANCE = 15
SPARSE_DATA_THRESHOLD = 10
LARGE_MISMATCH_THRESHOLD = 15
ACCURACY_EXCELLENT = 85
ACCURACY_GOOD = 75
ACCURACY_MODERATE = 65
LOW_SENSITIVITY_THRESHOLD = 0.6
LOW_SPECIFICITY_THRESHOLD = 0.6
CLASS_IMBALANCE_THRESHOLD = 15
```

#### Standard Configuration (Default)
Balanced approach, recommended starting point:

```python
HIGH_ACCURACY_THRESHOLD = 90
LOW_ACCURACY_THRESHOLD = 60
MIN_FREQ_FOR_LOW_ACCURACY = 10
SPARSE_DATA_THRESHOLD = 5
ACCURACY_EXCELLENT = 80
ACCURACY_GOOD = 70
LOW_SENSITIVITY_THRESHOLD = 0.5
CLASS_IMBALANCE_THRESHOLD = 20
```

#### Lenient Configuration (Exploratory)
Focus on serious issues, fewer false alarms:

```python
HIGH_ACCURACY_THRESHOLD = 85
LOW_ACCURACY_THRESHOLD = 50
MIN_FREQ_FOR_LOW_ACCURACY = 8
SPARSE_DATA_THRESHOLD = 3
LARGE_MISMATCH_THRESHOLD = 30
ACCURACY_EXCELLENT = 75
ACCURACY_MODERATE = 55
LOW_SENSITIVITY_THRESHOLD = 0.4
CLASS_IMBALANCE_THRESHOLD = 25
```

### Choosing Thresholds

Not sure which thresholds to use? Here's a guide:

#### When to Use **Stricter** Thresholds

Use strict thresholds when:
- Preparing for publication or external review
- Need high confidence in all findings
- Working with high-stakes decisions (medical, financial)
- Have large sample sizes (>1000)
- Want to minimize false positives

**Effect**: More warnings, catches subtle issues, may flag some non-issues

#### When to Use **Standard** Thresholds (Default)

Use standard thresholds when:
- Starting analysis of a new dataset
- General exploration and model development
- Typical reconstructability analysis
- Medium sample sizes (100-1000)
- Balanced approach needed

**Effect**: Reasonable balance, catches important issues without overwhelming

#### When to Use **Lenient** Thresholds

Use lenient thresholds when:
- Exploratory data analysis
- Small sample sizes (<100)
- Preliminary screening of many models
- Want only serious issues flagged
- Limited time for investigation

**Effect**: Fewer warnings, focus on critical problems, may miss subtle issues

#### Threshold-by-Threshold Guide

**Sample Size Thresholds**:
- `SPARSE_DATA_THRESHOLD`: Lower for small datasets, higher for large ones
- `MIN_FREQ_FOR_*`: Set based on your confidence needs and sample sizes

**Accuracy Thresholds**:
- `HIGH_ACCURACY_THRESHOLD`: Raise if you have very predictable relationships
- `LOW_ACCURACY_THRESHOLD`: Lower if your data is inherently noisy

**Statistical Thresholds**:
- `SIGNIFICANCE_THRESHOLD`: Use 0.01 for Bonferroni corrections, 0.05 standard
- `P_HIGHLY_SIGNIFICANT`: Adjust based on how many tests you're running

**Performance Thresholds**:
- `LOW_SENSITIVITY_THRESHOLD`: Raise (e.g., 0.6-0.7) if false negatives are costly
- `LOW_SPECIFICITY_THRESHOLD`: Raise (e.g., 0.6-0.7) if false positives are costly
- Set both high if you need excellent overall performance

**Information Capture**:
- Adjust based on your data's inherent complexity
- Complex domains (genetics, social science): lower boundaries
- Simpler domains: higher boundaries

### Quick Setup

See `complete_config_template.py` for a ready-to-use template with all options documented.

## Known Limitations

1. **Text Format Dependency**: Relies on specific OCCAM output format. Changes to OCCAM's output format may require updates.

2. **Component Relations**: For component relations (like ApZ, EdZ, CZ), the Data and Model parts are equal, so some analyses are simplified.

3. **Binary DV Only**: Currently designed for binary dependent variables. Multi-state DVs may not be fully analyzed.

4. **English Only**: Output and recommendations are in English only.

## Tips for Best Results

1. **Full Reports**: Provide complete fit report output, including header, LR stats, conditional tables, and confusion matrices.

2. **Clean Input**: Remove any non-report content (timestamps, debug output) for cleaner parsing.

3. **Compare Across Models**: Use the analyzer to compare different model specifications systematically.

4. **Follow Recommendations**: The analyzer identifies issues but doesn't fix them. Use the recommendations as a starting point for model improvement.

5. **Domain Knowledge**: Combine the analyzer's statistical insights with your domain expertise for best interpretation.

## Integration with PyOccam

This analyzer works with text output from OCCAM fit operations. To integrate with PyOccam:

```python
import pyoccam

# Run a fit operation
mgr = pyoccam.VBMManager()
mgr.initFromCommandLine(['data.txt'])
mgr.setAction('fit')
mgr.doAction('IV:ApZ:EdZ')

# Get the report
report_text = mgr.getReportString()

# Analyze
from analyze_fit import FitReportAnalyzer
analyzer = FitReportAnalyzer(report_text)
analyzer.print_summary()
```

## Future Enhancements

Potential future additions:
- Visualization generation (matplotlib plots)
- HTML report output
- Multi-state DV support
- Comparative analysis across multiple models
- Threshold auto-tuning based on dataset characteristics
- Integration with pandas for tabular output

## Contributing

Found a bug or have a suggestion? Issues and pull requests welcome!

## License

Same as OCCAM - GPL version 3 or later

## References

For more information on OCCAM and reconstructability analysis:
- OCCAM Manual: Occam_manual_v3_4_1_20210119.pdf
- OCCAM GitHub: https://github.com/occam-ra/occam

---

Last updated: 2025-12-16
