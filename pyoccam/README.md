# PyOccam

**Python bindings for OCCAM Reconstructability Analysis**

[![Build Wheels](https://github.com/occam-ra/occam/actions/workflows/build-wheels.yml/badge.svg)](https://github.com/occam-ra/occam/actions/workflows/build-wheels.yml)

## What is PyOccam?

PyOccam wraps the OCCAM Reconstructability Analysis tools in a modern Python package. It provides information-theoretic modeling for categorical data, useful for:

- Environmental modeling (landslides, wildfires)
- Biomedical research (disease risk factors)
- Social science and survey analysis
- Any domain with discrete/categorical variables

OCCAM discovers significant variable relationships while emphasizing **interpretability** over black-box prediction.

## Installation

```bash
pip install pyoccam
```

## Quick Start

```python
import pyoccam

# Load built-in dataset
data = pyoccam.load_dementia()
print(f"Loaded {data.n_samples} samples, {data.n_features} features")

# Run search to find best model
manager = data.manager
report = manager.generate_search_report("loopless-up", levels=5, width=3)
print(report)

# Get best model by BIC
best = manager.get_best_model_by_bic()
print(f"Best model: {best}")

# Generate fit report with confusion matrix
fit_report = manager.generate_fit_report(best, target_state="0")
print(fit_report)

# Get confusion matrix as dictionary
cm = manager.get_confusion_matrix(best, target_state="0")
print(f"Accuracy: {cm['train_accuracy']:.1%}")
```

## Convert Your Own CSV Data

```python
import pyoccam

# Convert CSV to OCCAM format with train/test split
output_file, data = pyoccam.make_occam_input_from_csv(
    "mydata.csv",
    test_split=0.2,                  # 20% held out for validation
    random_state=42,                 # Reproducible split
    max_cardinality=20,              # Exclude columns with >20 unique values
    dv_column="target",              # Specify dependent variable
    exclude_columns=["ID", "Name"]   # Always exclude these
)

# Analyze - now with train AND test metrics!
best = data.quick_search()
cm = data.manager.get_confusion_matrix(best, target_state="0")
print(f"Train accuracy: {cm['train_accuracy']:.1%}")
print(f"Test accuracy:  {cm['test_accuracy']:.1%}")
```

Or from the command line:

```bash
# With 20% test split
python -m pyoccam csv2occam mydata.csv --test-split 0.2 --exclude ID,Name
```

## Model Selection Methods

```python
# Different criteria for "best" model:
best_bic = manager.get_best_model_by_bic()           # Most parsimonious (recommended)
best_aic = manager.get_best_model_by_aic()           # Less penalty for complexity  
best_info = manager.get_best_model_by_information()  # Highest info, alpha < 0.05
```

## Built-in Datasets

```python
data = pyoccam.load_dementia()    # Alzheimer's disease risk factors
data = pyoccam.load_landslides()  # Geological hazard data
data = pyoccam.load_data("file.txt")  # Any OCCAM format file
```

## Search Types

- `"loopless-up"` - Bottom-up search, no feedback loops (recommended for directed systems)
- `"loopless-down"` - Top-down search, no loops
- `"full-up"` - Bottom-up with loops allowed
- `"full-down"` - Top-down with loops allowed

## Links

- **Practical Guide**: [PRACTICAL_GUIDE.md](https://github.com/occam-ra/occam/blob/pyoccam-port/PRACTICAL_GUIDE.md) - Tips from real projects
- **OCCAM Manual**: [PDF](https://pdxscholar.library.pdx.edu/sysc_fac/145/) - Complete theory & reference
- **Source Code**: [github.com/occam-ra/occam](https://github.com/occam-ra/occam)
- **Web Interface**: [occam.hsd.pdx.edu](https://occam.hsd.pdx.edu/)

## License

GPL v3 - See LICENSE file

## Credits

OCCAM was developed at Portland State University by Prof. Martin Zwick and contributors including Ken Willett, Joe Fusion, and H. Forrest Alexander. Python bindings by David Percy.
