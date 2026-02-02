# PyOccam Practical Guide

## Lessons Learned from Real-World Analysis Projects

This guide captures practical tips and lessons learned from analyzing landslide susceptibility (WTNSY data) and wildfire occurrence (PYROME data) using PyOccam.

---

## Table of Contents

1. [Converting CSV Data](#converting-csv-data)
2. [GIS Data Preparation Tips](#gis-data-preparation-tips)
3. [Avoiding Data Leakage](#avoiding-data-leakage)
4. [Model Selection Strategies](#model-selection-strategies)
5. [Interpreting Results](#interpreting-results)
6. [Batch Processing Multiple Regions](#batch-processing-multiple-regions)
7. [Common Pitfalls and Solutions](#common-pitfalls-and-solutions)

---

## Converting CSV Data

### Basic Usage

```python
import pyoccam

# Simple conversion - last column becomes DV
output_file, data = pyoccam.make_occam_input_from_csv("mydata.csv")

# With train/test split for validation
output_file, data = pyoccam.make_occam_input_from_csv(
    "mydata.csv",
    test_split=0.2,                       # 20% held out for testing
    random_state=42,                      # Reproducible split
    output_filename="mydata_occam.txt",  # Custom output name
    max_cardinality=20,                   # Exclude columns with >20 unique values
    dv_column="LS",                       # Specify DV by name (or index)
    exclude_columns=["ID", "x", "y"],     # Always exclude these
    verbose=True                          # Show progress
)

# Then run analysis - test metrics now available!
if data:
    best = data.quick_search()
    cm = data.manager.get_confusion_matrix(best, target_state="0")
    print(f"Train: {cm['train_accuracy']:.1%}")
    print(f"Test:  {cm['test_accuracy']:.1%}")  # Validates model!
```

### Command Line Usage

```bash
# Basic - converts and runs quick search
python -m pyoccam csv2occam mydata.csv

# With 20% test split for validation
python -m pyoccam csv2occam mydata.csv --test-split 0.2

# Full options with test split
python -m pyoccam csv2occam mydata.csv \
    --test-split 0.2 \
    --random-state 42 \
    --max-cardinality 25 \
    --dv target_column \
    --exclude "ID,x,y,geometry,Shape_Leng,Shape_Area" \
    --output output.txt

# Short form
python -m pyoccam csv2occam mydata.csv -t 0.2 -r 42 -c 25 -d LS -e "x,y,Pt_ID"

# Skip automatic search (just convert)
python -m pyoccam csv2occam mydata.csv --test-split 0.2 --no-search

# See all options
python -m pyoccam csv2occam --help
```

### What the Converter Does

1. **Reads CSV** with automatic encoding detection (handles UTF-8 BOM)
2. **Analyzes cardinality** of each column
3. **Auto-excludes** columns with:
   - Cardinality > max_cardinality (default 20)
   - Cardinality < 2 (constant columns)
   - Names in your exclude list
4. **Generates abbreviations** (2-letter codes) automatically
5. **Maps values to indices** (0, 1, 2, ...)
6. **Writes OCCAM format** with proper headers
7. **Returns ready-to-analyze** OccamData object

---

## GIS Data Preparation Tips

### Columns to ALWAYS Exclude

When working with GIS/spatial data, these columns should typically be excluded:

```python
GIS_EXCLUDE = [
    # Identifiers
    "OBJECTID", "FID", "Pt_ID", "ID", "UID",

    # Coordinates (continuous, high cardinality)
    "x", "y", "X", "Y", "lat", "lon", "latitude", "longitude",

    # Geometry fields
    "Shape_Length", "Shape_Area", "Shape_Leng", "geometry",

    # Database keys (often high cardinality)
    "mukey", "cokey", "areasymbol",

    # Timestamps
    "date", "timestamp", "created_at"
]

output_file, data = pyoccam.make_occam_input_from_csv(
    "gis_data.csv",
    exclude_columns=GIS_EXCLUDE
)
```

### Binning Continuous Variables

OCCAM works with categorical data. Continuous variables must be binned BEFORE conversion:

```python
import pandas as pd

df = pd.read_csv("raw_data.csv")

# Bin elevation into categories
df['elev_class'] = pd.cut(df['elevation'], 
                          bins=[0, 500, 1000, 1500, 2000, 9999],
                          labels=['VL', 'L', 'M', 'H', 'VH'])

# Bin slope into categories  
df['slope_class'] = pd.cut(df['slope_deg'],
                           bins=[0, 5, 15, 30, 45, 90],
                           labels=['flat', 'gentle', 'moderate', 'steep', 'cliff'])

# Save binned data
df.to_csv("binned_data.csv", index=False)

# Now convert to OCCAM format
output_file, data = pyoccam.make_occam_input_from_csv("binned_data.csv")
```

### Recommended Cardinality Limits

| Data Type                    | Recommended max_cardinality |
| ---------------------------- | --------------------------- |
| Small dataset (<500 samples) | 10-15                       |
| Medium dataset (500-5000)    | 15-25                       |
| Large dataset (>5000)        | 20-30                       |

**Rule of thumb**: Each category combination needs enough samples to be statistically meaningful. With 10 binary variables, you have 1024 possible states!

---

## Checklist Before Analysis

- [ ] No ID columns included
- [ ] No coordinate columns included
- [ ] No columns derived FROM the dependent variable
- [ ] No columns filled in AFTER outcome was determined
- [ ] Accuracy is reasonable (not 100% or suspiciously high)

---

## Model Selection Strategies

### Three Methods, Three Purposes

```python
# 1. BIC - Most Conservative (Recommended for publication)
best = manager.get_best_model_by_bic()
# Heavily penalizes complexity
# Best for: Final model selection, avoiding overfitting

# 2. AIC - Moderate
best = manager.get_best_model_by_aic()
# Less penalty than BIC
# Best for: Exploratory analysis, larger datasets

# 3. Information with Alpha < 0.05 (OCCAM Manual Definition)
best = manager.get_best_model_by_information()
# Highest information capture WHERE every step is statistically significant
# Best for: Finding strongest predictive relationships
```

### When to Use Each

| Situation                 | Recommended Method         |
| ------------------------- | -------------------------- |
| Small sample size (<500)  | BIC                        |
| Publication/reporting     | BIC                        |
| Exploratory analysis      | AIC or Information         |
| Large dataset (>5000)     | Information                |
| Many potential predictors | BIC (to avoid overfitting) |

### Understanding the Search Report

```
ID    Model                 Level   h        ddf    dLR      Alpha    Inf      %dH(DV)  dAIC      dBIC
1     IV:ApZ:EdZ:CZ         3       9.5271   35     0.0000   19.9787  47.2800  -94.4607
2*    IV:ApZ:EdZ            2       9.6093   5      0.0000   11.7427  58.9328  38.6841
```

- **`*` marker**: Model is on the "best by alpha" path (all steps significant)
- **h**: Entropy (lower = better fit)
- **ddf**: Degrees of freedom difference from reference
- **Alpha**: p-value for model improvement (want < 0.05)
- **Inf**: Information captured
- **%dH(DV)**: Percent reduction in DV uncertainty
- **dBIC/dAIC**: Difference from reference (negative = better)

---

## Interpreting Results

### Confusion Matrix Metrics

```python
cm = manager.get_confusion_matrix(best, target_state="0")

print(f"Accuracy:    {cm['train_accuracy']:.1%}")    # Overall correct
print(f"Sensitivity: {cm['train_sensitivity']:.1%}") # True positives / All positives
print(f"Specificity: {cm['train_specificity']:.1%}") # True negatives / All negatives
print(f"Precision:   {cm['train_precision']:.1%}")   # True positives / Predicted positives
print(f"F1 Score:    {cm['train_f1_score']:.3f}")    # Harmonic mean of precision & sensitivity
```

### Which Metric Matters?

| Application             | Primary Metric | Why                              |
| ----------------------- | -------------- | -------------------------------- |
| Landslide early warning | Sensitivity    | Missing a landslide is costly    |
| Medical screening       | Sensitivity    | Missing disease is dangerous     |
| Spam filtering          | Precision      | False positives annoy users      |
| Balanced importance     | F1 Score       | Balances precision & sensitivity |
| General reporting       | Accuracy       | Easy to understand               |

### Model Notation

```python
"IV:ApZ"      # Ap INDEPENDENT of Z (no prediction possible)
"IV:Ap:Z"     # Ap PREDICTS Z (can compute confusion matrix)
"IV:Ap:Ed:Z"  # Both Ap and Ed predict Z (joint model)
"IV:ApEd:Z"   # Ap and Ed together predict Z (interaction term)
```

---

## Batch Processing Multiple Regions

### Example: Processing Multiple PYROME Regions

```python
import pyoccam
import os
from pathlib import Path

# Configuration
DATA_DIR = Path("C:/projects/wildfires/pyrome_data")
OUTPUT_DIR = Path("C:/projects/wildfires/results")
OUTPUT_DIR.mkdir(exist_ok=True)

REGIONS = [
    "Blue_Mountains",
    "Columbia_Plateau", 
    "Northern_Rockies",
    "Sierra_Nevada",
    # ... etc
]

EXCLUDE_COLS = ["x", "y", "OBJECTID", "mukey", "cokey"]

results = []

for region in REGIONS:
    print(f"\n{'='*60}")
    print(f"Processing: {region}")
    print(f"{'='*60}")

    csv_file = DATA_DIR / f"{region}_data.csv"

    if not csv_file.exists():
        print(f"  SKIP: File not found")
        continue

    try:
        # Convert and load
        output_file, data = pyoccam.make_occam_input_from_csv(
            str(csv_file),
            max_cardinality=25,
            exclude_columns=EXCLUDE_COLS,
            verbose=False
        )

        # Run search
        manager = data.manager
        manager.set_report_separator(pyoccam.TABSEP)
        report = manager.generate_search_report("loopless-up", levels=5, width=3)

        # Get best model
        best = manager.get_best_model_by_bic()

        # Get metrics
        cm = manager.get_confusion_matrix(best, target_state="0")

        # Save detailed results
        with open(OUTPUT_DIR / f"{region}_search.txt", 'w') as f:
            f.write(report)

        fit_report = manager.generate_fit_report(best, target_state="0")
        with open(OUTPUT_DIR / f"{region}_fit.txt", 'w') as f:
            f.write(fit_report)

        # Collect summary
        results.append({
            'region': region,
            'best_model': best,
            'n_samples': data.n_samples,
            'accuracy': cm.get('train_accuracy', 0),
            'sensitivity': cm.get('train_sensitivity', 0),
            'specificity': cm.get('train_specificity', 0)
        })

        print(f"  Best: {best}")
        print(f"  Accuracy: {cm.get('train_accuracy', 0):.1%}")

    except Exception as e:
        print(f"  ERROR: {e}")
        results.append({'region': region, 'error': str(e)})

# Save summary
import csv
with open(OUTPUT_DIR / "summary.csv", 'w', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=results[0].keys())
    writer.writeheader()
    writer.writerows(results)

print(f"\n{'='*60}")
print(f"Complete! Results in {OUTPUT_DIR}")
```

---

## Common Pitfalls and Solutions

### 1. "Search returns no models"

**Cause**: Search type missing `-up` or `-down` suffix

```python
# WRONG
manager.set_search_type("loopless")

# CORRECT
report = manager.generate_search_report("loopless-up", levels=5, width=3)
```

### 2. "All statistics show -1.0"

**Cause**: Statistics not computed (internal OCCAM requirement)

**Solution**: Use `generate_search_report()` or `generate_fit_report()` which handle this automatically.

### 3. "Import works but functions fail"

**Cause**: Old version cached in site-packages

```python
# Check which version is loaded
import pyoccam
print(pyoccam.__file__)  # Should point to your development folder

# Fix: Uninstall old version
# pip uninstall pyoccam

# Or force local version:
import sys
sys.path.insert(0, r"D:\projects\occam")
import pyoccam
```

### 4. "CSV converter gives wrong cardinality"

**Cause**: Missing values counted as unique category

**Solution**: Clean data first or handle NA values:

```python
import pandas as pd
df = pd.read_csv("data.csv")
df = df.fillna("MISSING")  # Or df.dropna()
df.to_csv("data_clean.csv", index=False)
```

### 5. "Confusion matrix shows all zeros"

**Cause**: Model is independence model (no prediction)

```python
# Check if model has prediction capability
model = manager.get_best_model_by_bic()
print(model)

# If it shows "IV:XY" (variables joined), it's independence
# If it shows "IV:X:Y" (colon between each), it CAN predict
```

### 6. "Different results on different runs"

**Cause**: OCCAM is deterministic - this shouldn't happen unless:

- Different data file loaded
- Different search parameters
- Different reference model

Always verify:

```python
print(f"Data file: {data.data_file}")
print(f"Samples: {data.n_samples}")
print(f"Features: {data.n_features}")
```

---

## Quick Reference Card

```python
import pyoccam

# Load data
data = pyoccam.load_dementia()           # Built-in
data = pyoccam.load_landslides()         # Built-in
data = pyoccam.load_data("file.txt")     # Any OCCAM file

# Convert CSV with train/test split
out, data = pyoccam.make_occam_input_from_csv(
    "data.csv", 
    test_split=0.2,          # 20% test set
    random_state=42,         # Reproducible
    max_cardinality=20
)

# Configure
manager = data.manager
manager.set_report_separator(pyoccam.SPACESEP)  # or TABSEP, COMMASEP

# Search
report = manager.generate_search_report("loopless-up", levels=5, width=3)

# Best models
best = manager.get_best_model_by_bic()           # Conservative
best = manager.get_best_model_by_aic()           # Moderate  
best = manager.get_best_model_by_information()   # Liberal (alpha<0.05)

# Fit report
fit = manager.generate_fit_report(best, target_state="0")

# Confusion matrix (train AND test if split was used)
cm = manager.get_confusion_matrix(best, target_state="0")
print(f"Train: {cm['train_accuracy']:.1%}, Test: {cm.get('test_accuracy', 'N/A')}")
```

---

*Last updated: February 2026*
*Based on lessons from Landslides_RA and Wildfires_RA projects*
