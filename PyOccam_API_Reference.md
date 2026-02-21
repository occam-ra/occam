# PyOccam API Reference Guide
**Version 0.9.5 | February 2026**

Complete reference for the PyOccam Python package — Python bindings for OCCAM Reconstructability Analysis.

---

## Table of Contents
1. [Quick Start](#quick-start)
2. [Package Installation](#package-installation)
3. [Data Loading API](#data-loading-api)
4. [CSV Conversion API](#csv-conversion-api)
5. [Lookup Tables API](#lookup-tables-api)
6. [VBMManager API](#vbmmanager-api)
7. [Model Class API](#model-class-api)
8. [FitReportAnalyzer API](#fitreportanalyzer-api)
9. [Constants](#constants)
10. [Complete Workflow Examples](#complete-workflow-examples)
11. [Troubleshooting](#troubleshooting)

---

## Quick Start

```python
import pyoccam

# Load built-in dataset
data = pyoccam.load_dementia()
print(data)  # Shows: OccamData(n_samples=424, n_features=10, target='CaseControl')

# Get manager for analysis
manager = data.manager

# Run a beam search
report = manager.generate_search_report("loopless-up", levels=7, width=3)
print(report)  # Formatted table of best models

# Get best model
best = manager.get_best_model_by_bic()
print(f"Best model: {best}")  # e.g., "IV:ApZ:EdK:GnA"

# Generate fit report with confusion matrix
fit_report = manager.generate_fit_report(best, target_state="0")
print(fit_report)

# Get confusion matrix as dictionary (sklearn-compatible keys)
cm = manager.get_confusion_matrix(best, target_state="0")
print(f"Accuracy: {cm['train_accuracy']:.3f}")
print(f"TN={cm['train_tn']:.0f}, FP={cm['train_fp']:.0f}")
print(f"FN={cm['train_fn']:.0f}, TP={cm['train_tp']:.0f}")
```

---

## Package Installation

### From Test PyPI (current)
```bash
pip install -i https://test.pypi.org/simple/ pyoccam
```

### From PyPI (when available)
```bash
pip install pyoccam
```

### From Source (Windows with MinGW)
```bash
# In Anaconda PowerShell with pyoccam-build environment
conda activate pyoccam-build
python setup.py clean --all
python setup.py build_ext --inplace --compiler=mingw32
pip install -e .
```

### Verify Installation
```python
import pyoccam
print(pyoccam.__version__)  # Should print: 0.9.5
pyoccam.help()              # Show full usage guide
```

---

## Data Loading API

### `load_dementia()`
Load the built-in dementia (Alzheimer's Disease) dataset.

**Returns:** `OccamData` object

**Example:**
```python
data = pyoccam.load_dementia()
# Output: [OK] Loaded dementia: 424 samples, 10 features

print(data.n_samples)      # 424
print(data.n_features)     # 10
print(data.feature_names)  # ['Apoe', 'Zyg', 'Ed', 'Kn', 'Gn', 'A', 'Se', ...]
print(data.target_name)    # 'CaseControl'
print(data.has_test_data)  # False (unless test data was loaded)
```

---

### `load_landslides()`
Load the built-in landslides dataset with lookup tables.

**Returns:** `OccamData` object with `.lookups` populated

**Example:**
```python
data = pyoccam.load_landslides()
# Output: [OK] Loaded landslides: 1077 samples, 20 features, 21 lookup tables

# Decode variable encodings using lookup tables
print(data.lookups['TaxOrder'])      # {0: 'Alfisols', 1: 'Andisols', ...}
print(data.lookups['GeomDesc'][7])   # 'hillslopes'
```

---

### `load_data(filename)`
Load any OCCAM-format data file.

**Parameters:**
- `filename` (str): Path to data file or name of packaged file

**Returns:** `OccamData` object

**Example:**
```python
# Load from absolute path
data = pyoccam.load_data("D:/data/mydata.txt")

# Load from relative path
data = pyoccam.load_data("mydata.txt")

# Load packaged file by name
data = pyoccam.load_data("dementia05.txt")
```

---

### `OccamData` Class
Container for dataset information (similar to sklearn's Bunch).

**Attributes:**
- `data_file` (str): Path to the data file
- `n_samples` (int): Number of samples
- `n_features` (int): Number of features (excluding dependent variable)
- `feature_names` (list): List of feature variable names
- `target_name` (str): Name of dependent variable
- `has_test_data` (bool): Whether test data is present
- `manager` (VBMManager): VBMManager instance for analysis
- `lookups` (dict or None): Lookup tables mapping encoded integers to original values
- `DESCR` (str): Dataset description (if available)

**Methods:**

#### `quick_search(search_type="full-up", levels=3, width=3)`
Run a quick search on this data.

**Example:**
```python
data = pyoccam.load_dementia()
best = data.quick_search(levels=5, width=3)
print(f"Best model: {best}")
```

---

## CSV Conversion API

### `make_occam_input_from_csv(csv_filename, ...)`
Convert a standard CSV file to OCCAM input format. Automatically detects categorical columns, computes cardinality, and generates variable definitions. Columns with cardinality > `max_cardinality` are automatically excluded.

Also aliased as `pyoccam.csv_to_occam()`.

**Parameters:**
- `csv_filename` (str): Path to input CSV file
- `output_filename` (str, optional): Output file path (default: same name with `.txt`)
- `max_cardinality` (int): Max unique values before a column is excluded (default: 20)
- `dv_column` (str or int, optional): Dependent variable column name or index (default: last column)
- `exclude_columns` (list, optional): Column names to always exclude (e.g., `['ID', 'Name']`)
- `test_split` (float, optional): Fraction for test set (0.0-1.0, default: None = no split)
- `random_state` (int): Random seed for reproducible splits (default: 42)
- `verbose` (bool): Print progress messages (default: True)

**Returns:** `tuple` of `(output_path_str, OccamData)`

**Example - Basic conversion:**
```python
output_file, data = pyoccam.make_occam_input_from_csv("mydata.csv")
# Automatically:
#   - Identifies DV as last column
#   - Excludes high-cardinality columns (IDs, continuous values)
#   - Generates lookup tables: mydata_lookups.csv
#   - Returns ready-to-analyze OccamData
```

**Example - With train/test split:**
```python
output_file, data = pyoccam.make_occam_input_from_csv(
    "mydata.csv",
    test_split=0.2,                    # 20% held out for testing
    random_state=42,                   # Reproducible split
    exclude_columns=["site_id"],       # Always exclude these
    dv_column="risk"                   # Specify DV by name
)

# Now analyze with validation
best = data.quick_search(levels=7, width=3)
cm = data.manager.get_confusion_matrix(best, target_state="0")
print(f"Train accuracy: {cm['train_accuracy']:.1%}")
print(f"Test accuracy:  {cm['test_accuracy']:.1%}")
```

**Generated files:**
- `mydata.txt` - OCCAM input file
- `mydata_lookups.csv` - Value mapping table (variable, encoded_value, original_value)

---

## Lookup Tables API

### `load_lookups(csv_path)`
Load a consolidated lookup CSV into a nested dictionary.

**Parameters:**
- `csv_path` (str): Path to CSV with columns: `variable`, `encoded_value`, `original_value`

**Returns:** `dict` of `{variable_name: {encoded_int: original_str}}`

**Example:**
```python
lookups = pyoccam.load_lookups("mydata_lookups.csv")
print(lookups['soil_type'])      # {0: 'clay', 1: 'loam', 2: 'sand', ...}
print(lookups['soil_type'][1])   # 'loam'
```

---

### `save_lookups(lookups, csv_path)`
Save a lookup dictionary to consolidated CSV format.

**Parameters:**
- `lookups` (dict): Nested dict of `{variable_name: {encoded_int: original_str}}`
- `csv_path` (str): Output file path

---

## VBMManager API

The `VBMManager` class is the core engine for OCCAM analysis. Access it through `data.manager` or create directly.

### Creating a VBMManager

```python
# Option 1: Through data loading (recommended)
data = pyoccam.load_dementia()
manager = data.manager

# Option 2: Create directly
manager = pyoccam.VBMManager()
success = manager.init_from_command_line(["occam", "datafile.txt"])
if not success:
    raise RuntimeError("Failed to initialize")
```

---

### Initialization Methods

#### `init_from_command_line(args)`
Initialize OCCAM from command line arguments.

**Parameters:**
- `args` (list): Command line arguments as list of strings. First element should be `"occam"` (program name), second should be the data file path.

**Returns:** `bool` - True if successful

**Example:**
```python
manager = pyoccam.VBMManager()
success = manager.init_from_command_line(["occam", "data.txt"])

# With additional options
success = manager.init_from_command_line([
    "occam", 
    "data.txt",
    ":nominal",  # Treat all variables as nominal
])
```

---

### Configuration Methods

#### `set_report_separator(separator)`
Set the separator for report formatting.

**Parameters:**
- `separator` (int): One of `pyoccam.TABSEP` (1), `pyoccam.COMMASEP` (2), `pyoccam.SPACESEP` (3, recommended), `pyoccam.HTMLFORMAT` (4)

**Example:**
```python
manager.set_report_separator(pyoccam.SPACESEP)  # Recommended
```

---

#### `set_report_variables(variables)`
Set which variables/statistics to display in reports.

**Parameters:**
- `variables` (str): Comma-separated list of variable names

**Available Variables:** `level$I`, `h`, `ddf` (use `ddf$I` for integer), `lr`, `alpha`, `%dH(DV)`, `information`, `daic`, `dbic`, `incr_alpha`, `pct_correct_data`, `pct_correct_test`

**Important:** Do NOT include `ID$I` or `Model` in the variables list - these are added automatically.

**Example:**
```python
# Standard format
manager.set_report_variables("level$I, h, ddf, lr, alpha, %dH(DV), daic, dbic")

# With incremental alpha
manager.set_report_variables("level$I, h, ddf, alpha, %dH(DV), daic, dbic, incr_alpha")

# With test data statistics
manager.set_report_variables(
    "level$I, h, ddf, alpha, daic, dbic, pct_correct_data, pct_correct_test"
)
```

---

#### `set_ref_model(model_name)`
Set the reference model for statistics computation.

**Parameters:**
- `model_name` (str): `"bottom"` (recommended), `"top"`, `"default"`, or a specific model

**Example:**
```python
manager.set_ref_model("bottom")  # Most common choice
```

---

#### `set_search_type(search_type)`
Set the search algorithm type.

**Parameters:**
- `search_type` (str): One of `"loopless-up"`, `"loopless-down"`, `"full-up"`, `"full-down"`, `"disjoint-up"`, `"disjoint-down"`, `"chain-up"`, `"chain-down"`

---

#### `set_debug_mode(enable)`
Enable or disable debug output.

**Parameters:**
- `enable` (bool): True to enable, False to disable

---

### Fit Configuration Methods

#### `set_calc_expected_dv(enable)`
Set whether to calculate expected dependent variable values.

#### `set_skip_trained_model_table(skip)`
Skip the trained model table in fit output.

#### `set_skip_ivi_tables(skip)`
Skip the IVI (Individual Variable Information) tables in fit output.

#### `set_fit_classifier_target(target_state)`
Set target state for classifier confusion matrix.

**Parameters:**
- `target_state` (str): Target state value (e.g., "0", "1")

#### `set_default_fit_model(model_name)`
Set default model for fit comparison.

---

### Main Analysis Methods

#### `generate_search_report(search_type, levels, width, include_test_data=False)`
Perform beam search and generate formatted report of best models.

**Parameters:**
- `search_type` (str): Search algorithm (e.g., `"loopless-up"`, `"full-up"`)
- `levels` (int): Number of levels to search
- `width` (int): Beam width (models to keep per level)
- `include_test_data` (bool): **Ignored** - test data columns are automatically included if present

**Returns:** `str` - Formatted report

**Notes:**
- Models are stored internally and can be retrieved with `get_kept_models()`
- Best models by various criteria are tracked automatically
- **Must be called before `get_best_model_*()`** methods

---

#### `generate_fit_report(model_name, target_state="0")`
Generate complete fit report for a specific model.

**Parameters:**
- `model_name` (str): Model to fit (e.g., `"IV:ApZ:EdK"`)
- `target_state` (str): Target state for confusion matrix (default: `"0"`)

**Returns:** `str` - Formatted fit report including model structure, fit statistics, contingency tables, confusion matrix, and test data performance (if available)

---

#### `get_confusion_matrix(model_name, target_state="0")`
Get confusion matrix for a model as a Python dictionary.

**Parameters:**
- `model_name` (str): Model name
- `target_state` (str): Target state value (default: `"0"`)

**Returns:** `dict` with sklearn-compatible keys:

| Key | Type | Description |
|-----|------|-------------|
| `train_tn` | float | True Negatives (training) |
| `train_fp` | float | False Positives (training) |
| `train_fn` | float | False Negatives (training) |
| `train_tp` | float | True Positives (training) |
| `train_accuracy` | float | Overall accuracy (training) |
| `train_sensitivity` | float | True Positive Rate / Recall (training) |
| `train_specificity` | float | True Negative Rate (training) |
| `train_precision` | float | Positive Predictive Value (training) |
| `train_npv` | float | Negative Predictive Value (training) |
| `train_f1_score` | float | Harmonic mean of precision and recall (training) |
| `has_values` | bool | Whether valid values were retrieved |
| `has_test_data` | bool | Whether test data metrics are available |

**If test data is available, these additional keys are present:**

| Key | Type | Description |
|-----|------|-------------|
| `test_tn` | float | True Negatives (test) |
| `test_fp` | float | False Positives (test) |
| `test_fn` | float | False Negatives (test) |
| `test_tp` | float | True Positives (test) |
| `test_accuracy` | float | Overall accuracy (test) |
| `test_sensitivity` | float | True Positive Rate / Recall (test) |
| `test_specificity` | float | True Negative Rate (test) |
| `test_precision` | float | Positive Predictive Value (test) |
| `test_npv` | float | Negative Predictive Value (test) |
| `test_f1_score` | float | Harmonic mean of precision and recall (test) |

**Example:**
```python
best = manager.get_best_model_by_bic()
cm = manager.get_confusion_matrix(best, target_state="0")

if cm['has_values']:
    print(f"Training Confusion Matrix:")
    print(f"  TN={cm['train_tn']:.0f}, FP={cm['train_fp']:.0f}")
    print(f"  FN={cm['train_fn']:.0f}, TP={cm['train_tp']:.0f}")
    print(f"  Accuracy:    {cm['train_accuracy']:.3f}")
    print(f"  Sensitivity: {cm['train_sensitivity']:.3f}")
    print(f"  Specificity: {cm['train_specificity']:.3f}")
    print(f"  Precision:   {cm['train_precision']:.3f}")
    print(f"  F1 Score:    {cm['train_f1_score']:.3f}")
    
    if cm['has_test_data']:
        print(f"\nTest Performance:")
        print(f"  TN={cm['test_tn']:.0f}, FP={cm['test_fp']:.0f}")
        print(f"  FN={cm['test_fn']:.0f}, TP={cm['test_tp']:.0f}")
        print(f"  Accuracy:    {cm['test_accuracy']:.3f}")
        print(f"  Sensitivity: {cm['test_sensitivity']:.3f}")
        print(f"  Specificity: {cm['test_specificity']:.3f}")
```

**Important Notes:**
- **Key naming follows sklearn convention**: All keys use `train_` and `test_` prefixes with lowercase names, matching `sklearn.model_selection.cross_validate()` patterns.
- **Smart Caching**: Repeated calls with the same model/target return cached values instantly.
- **Automatic Generation**: On first call for a model/target combination, it automatically runs the fit report internally.
- The confusion matrix uses a **double-swap pattern** internally to ensure consistency between printed output and extracted values.

---

### Best Model Selection Methods

After running `generate_search_report()`, these methods return the best model name:

#### `get_best_model_by_bic()`
Best model by BIC (Bayesian Information Criterion). Most parsimonious - **recommended for most analyses**.

#### `get_best_model_by_aic()`
Best model by AIC (Akaike Information Criterion). Less conservative than BIC.

#### `get_best_model_by_information()`
Best model by information (highest transmission).

#### `get_best_model_by_info_alpha()`
Best model by information where incremental alpha < 0.05 (highest information that is significantly better than its parent model).

**Returns:** `str` - Model name (e.g., `"IV:ApZ:EdK"`)

**Example:**
```python
report = manager.generate_search_report("loopless-up", 7, 3)
best_bic = manager.get_best_model_by_bic()
best_aic = manager.get_best_model_by_aic()
best_info = manager.get_best_model_by_information()
best_sig = manager.get_best_model_by_info_alpha()

print(f"Best BIC: {best_bic}")
print(f"Best AIC: {best_aic}")
print(f"Best Info: {best_info}")
print(f"Best Significant: {best_sig}")
```

---

### Model Operations

#### `make_model(model_name, make_fit_table=False)`
Create a model and optionally compute its statistics.

**Parameters:**
- `model_name` (str): Model structure (e.g., `"IV:ABC:DEF"`)
- `make_fit_table` (bool): If True, compute fit table and all statistics

**Returns:** `Model` object

---

#### `get_model_statistics(model_name)`
Get complete statistics for a specific model. Equivalent to `make_model(model_name, make_fit_table=True)`.

**Returns:** `Model` object with all statistics computed

**Example:**
```python
stats = manager.get_model_statistics("IV:ApZ:EdK:GnA")
print(f"H = {stats.h:.3f}")
print(f"dDF = {stats.df:.0f}")
print(f"LR = {stats.lr:.2f}")
print(f"Alpha = {stats.alpha:.6f}")
print(f"dBIC = {stats.dbic:.2f}")
print(f"% Correct = {stats.pct_correct_data:.2f}%")
```

---

### Information Methods

#### `get_variable_list()`
**Returns:** `list` of strings - variable names in order, with dependent variable last.

#### `get_basic_statistics()`
**Returns:** `str` - Multi-line string with sample size, variable count, H(data), and test data status.

#### `get_sample_size()`
**Returns:** `int` - Number of samples.

#### `has_test_data()`
**Returns:** `bool` - True if test data is present.

#### `get_available_search_types()`
**Returns:** `list` of strings - Available search algorithm names.

---

### Report Access Methods

#### `get_kept_models()`
Get list of all models kept from the last beam search.

**Returns:** `list` of `Model` objects

#### `get_search_model_count()`
**Returns:** `int` - Number of kept models from last search.

---

## Model Class API

The `Model` class represents a single OCCAM model with its statistics.

### Attributes

- `name` (str): Model name (e.g., `"IV:ApZ:EdK"`)
- `h` (float): Entropy H
- `information` (float): Information (transmission)
- `aic` (float): Akaike Information Criterion
- `bic` (float): Bayesian Information Criterion
- `daic` (float): Delta AIC (relative to reference)
- `dbic` (float): Delta BIC (relative to reference)
- `alpha` (float): p-value
- `df` (float): Degrees of freedom delta
- `lr` (float): Likelihood ratio
- `pct_correct_data` (float): Percent correct on training data
- `pct_correct_test` (float): Percent correct on test data (0.0 if no test data)
- `pct_coverage` (float): Percent coverage
- `pct_missed_test` (float): Percent missed in test data
- `incr_alpha` (float): Incremental alpha (vs progenitor model)
- `level` (int): Search level

---

## FitReportAnalyzer API

The `FitReportAnalyzer` class automatically parses fit report text and identifies model quality, interesting conditional DV patterns, confusion matrix insights, and actionable recommendations.

### Import

```python
from pyoccam import FitReportAnalyzer
```

### Constructor

```python
FitReportAnalyzer(fit_report_text, cm_dict=None)
```

**Parameters:**
- `fit_report_text` (str): Output from `manager.generate_fit_report()`
- `cm_dict` (dict, optional): Confusion matrix dictionary from `manager.get_confusion_matrix()` - enables richer analysis when provided

### Methods

#### `print_summary()`
Print a human-readable analysis summary to stdout.

#### `analyze()`
Get findings as a structured dictionary for programmatic use.

**Returns:** `dict` with keys:
- `overview`: Model quality summary (sample size, info capture, transmission)
- `model_quality`: Statistical significance details
- `conditional_patterns`: Interesting IV->DV patterns found
- `confusion_matrix`: Performance insights from CM analysis
- `recommendations`: Actionable suggestions

### Example

```python
# Get fit report and confusion matrix
fit_report = manager.generate_fit_report(best, target_state="0")
cm = manager.get_confusion_matrix(best, target_state="0")

# Analyze
analyzer = FitReportAnalyzer(fit_report, cm_dict=cm)
analyzer.print_summary()  # Human-readable output

# Programmatic access
findings = analyzer.analyze()
print(f"Info capture: {findings['overview'].get('info_capture', 'N/A')}")
print(f"Patterns found: {len(findings['conditional_patterns'])}")
print(f"Recommendations: {len(findings['recommendations'])}")
```

### Command-Line Usage

```bash
python -m pyoccam.analyze_fit my_fit_report.txt
```

---

## Constants

### Report Separators
- `pyoccam.TABSEP` = 1 - Tab-separated
- `pyoccam.COMMASEP` = 2 - Comma-separated
- `pyoccam.SPACESEP` = 3 - Space-separated (**recommended**)
- `pyoccam.HTMLFORMAT` = 4 - HTML format

### Version
- `pyoccam.__version__` - Package version string

---

## Complete Workflow Examples

### Basic Analysis Pipeline

```python
import pyoccam

# 1. Load data
data = pyoccam.load_dementia()
print(f"Loaded {data.n_samples} samples with {data.n_features} features")

# 2. Get manager and configure
manager = data.manager
manager.set_report_separator(pyoccam.SPACESEP)
manager.set_report_variables("level$I, h, ddf, lr, alpha, %dH(DV), daic, dbic")
manager.set_ref_model("bottom")

# 3. Run beam search
report = manager.generate_search_report("loopless-up", levels=7, width=3)
print(report)

# 4. Get best model
best = manager.get_best_model_by_bic()
print(f"\nBest model by BIC: {best}")

# 5. Generate fit report
fit_report = manager.generate_fit_report(best, target_state="0")
print(fit_report)

# 6. Extract confusion matrix
cm = manager.get_confusion_matrix(best, target_state="0")
print(f"\nConfusion Matrix Analysis:")
print(f"  Accuracy:    {cm['train_accuracy']:.3f}")
print(f"  Sensitivity: {cm['train_sensitivity']:.3f}")
print(f"  Specificity: {cm['train_specificity']:.3f}")
print(f"  F1 Score:    {cm['train_f1_score']:.3f}")
```

---

### CSV to OCCAM with Train/Test Validation

```python
import pyoccam

# 1. Convert CSV with train/test split
output_file, data = pyoccam.make_occam_input_from_csv(
    "survey_data.csv",
    test_split=0.2,
    random_state=42,
    exclude_columns=["respondent_id"]
)

# 2. Explore lookup tables
print(f"Variables with lookups: {list(data.lookups.keys())}")
for code, name in sorted(data.lookups['education'].items()):
    print(f"  {code} = {name}")

# 3. Search
manager = data.manager
report = manager.generate_search_report("full-up", 7, 3)
best = manager.get_best_model_by_aic()

# 4. Fit and extract confusion matrix
fit_report = manager.generate_fit_report(best, target_state="0")
cm = manager.get_confusion_matrix(best, target_state="0")

print(f"\nTraining: {cm['train_accuracy']:.1%} accuracy")
print(f"  TP={cm['train_tp']:.0f}  FP={cm['train_fp']:.0f}")
print(f"  FN={cm['train_fn']:.0f}  TN={cm['train_tn']:.0f}")

if cm.get('has_test_data'):
    print(f"\nTest: {cm['test_accuracy']:.1%} accuracy")
    print(f"  TP={cm['test_tp']:.0f}  FP={cm['test_fp']:.0f}")
    print(f"  FN={cm['test_fn']:.0f}  TN={cm['test_tn']:.0f}")

# 5. Automated analysis
from pyoccam import FitReportAnalyzer
analyzer = FitReportAnalyzer(fit_report, cm_dict=cm)
analyzer.print_summary()
```

---

### Model Comparison

```python
import pyoccam

data = pyoccam.load_dementia()
manager = data.manager

# Run search
manager.generate_search_report("loopless-up", 7, 3)

# Get different "best" models
best_bic = manager.get_best_model_by_bic()
best_aic = manager.get_best_model_by_aic()
best_info = manager.get_best_model_by_information()
best_sig = manager.get_best_model_by_info_alpha()

print("Model Selection Comparison:")
print(f"  Best BIC:  {best_bic}")
print(f"  Best AIC:  {best_aic}")
print(f"  Best Info: {best_info}")
print(f"  Best Sig:  {best_sig}")

# Compare statistics
for model_name in [best_bic, best_aic, best_info]:
    if model_name:
        model = manager.get_model_statistics(model_name)
        print(f"\n{model.name}:")
        print(f"  BIC: {model.bic:.2f}")
        print(f"  AIC: {model.aic:.2f}")
        print(f"  Info: {model.information:.4f}")
        print(f"  % Correct: {model.pct_correct_data:.1f}%")
```

---

### Working with Test Data

```python
import pyoccam

# Load data with test split (from CSV or pre-split OCCAM file)
output, data = pyoccam.make_occam_input_from_csv("mydata.csv", test_split=0.2)
manager = data.manager

# Check for test data
if manager.has_test_data():
    print("Test data detected")
    
    # Include test columns in reports
    manager.set_report_variables(
        "level$I, h, ddf, alpha, daic, dbic, "
        "pct_correct_data, pct_correct_test"
    )
    
    # Search and fit
    report = manager.generate_search_report("loopless-up", 5, 3)
    best = manager.get_best_model_by_bic()
    cm = manager.get_confusion_matrix(best, "0")
    
    # Training performance
    print(f"\nTraining: {cm['train_accuracy']:.1%} accuracy")
    print(f"  Sensitivity: {cm['train_sensitivity']:.3f}")
    print(f"  Specificity: {cm['train_specificity']:.3f}")
    
    # Test performance
    if cm['has_test_data']:
        print(f"\nTest: {cm['test_accuracy']:.1%} accuracy")
        print(f"  Sensitivity: {cm['test_sensitivity']:.3f}")
        print(f"  Specificity: {cm['test_specificity']:.3f}")
        
        # Train/test gap
        gap = cm['train_accuracy'] - cm['test_accuracy']
        print(f"\nTrain/test gap: {gap:.1%}")
```

---

### Quick One-Liner Analysis

```python
import pyoccam

# Load and search in one line
data, best = pyoccam.quick_search("dementia05.txt", "loopless-up", levels=7, width=3)

# Fit and extract
fit_report = data.manager.generate_fit_report(best, "0")
cm = data.manager.get_confusion_matrix(best, "0")
print(f"Accuracy: {cm['train_accuracy']:.3f}")
```

---

### Multiple Search Strategies

```python
import pyoccam

data = pyoccam.load_dementia()
manager = data.manager

search_types = ["loopless-up", "disjoint-up", "chain-up"]
results = {}

for search_type in search_types:
    print(f"\nRunning {search_type} search...")
    report = manager.generate_search_report(search_type, levels=5, width=3)
    best = manager.get_best_model_by_bic()
    model = manager.get_model_statistics(best)
    results[search_type] = {
        'model': model.name, 'bic': model.bic,
        'info': model.information, 'alpha': model.alpha
    }
    print(f"  Best: {model.name} (BIC={model.bic:.2f})")

# Summary
print("\n" + "=" * 60)
print("Search Strategy Comparison:")
for st, res in results.items():
    print(f"  {st:15s} {res['model']:20s} BIC={res['bic']:7.2f} Info={res['info']:.4f}")
```

---

## Troubleshooting

### Common Issues

#### Import Error: Module Not Found
```python
# Error: ModuleNotFoundError: No module named 'pyoccam'
# Solution: Rebuild the extension
python setup.py clean --all
python setup.py build_ext --inplace --compiler=mingw32
pip install -e .
```

#### Import Error: DLL Load Failed
```python
# Error: ImportError: DLL load failed while importing _pyoccam
# Solution: Ensure MinGW is in PATH
gcc --version  # Should show MinGW
# Then rebuild
```

#### Empty Model Name from get_best_model_*
```python
best = manager.get_best_model_by_bic()
if not best or best == "":
    print("No models found - run generate_search_report first!")
    
# Always run search before getting best model:
manager.generate_search_report("loopless-up", 7, 3)
best = manager.get_best_model_by_bic()  # Now works
```

#### Confusion Matrix Returns Empty
```python
cm = manager.get_confusion_matrix("IV:ApZ", "0")
if not cm.get('has_values'):
    print("No confusion matrix - check model name and target state")
```

#### Running from Wrong Directory
**Critical**: Never run scripts from *within* the `pyoccam/` package directory. This causes namespace conflicts. Always run from the parent directory containing `setup.py`.

---

### Best Practices

1. **Always call `generate_search_report()` before `get_best_model_*()`**

2. **Use SPACESEP for readable reports**: `manager.set_report_separator(pyoccam.SPACESEP)`

3. **Don't include ID or Model in report variables** - they are added automatically

4. **Check for test data before accessing test metrics**: `if cm.get('has_test_data'):`

5. **Use sklearn-prefixed keys** for confusion matrix: `cm['train_accuracy']`, not `cm['accuracy']`

6. **Cache confusion matrix results**: Same model/target returns cached values instantly

7. **Run from project root**, not from inside the `pyoccam/` directory

---

### Performance Tips

- **Beam search parameters**: Larger width and more levels increase computation time
- **Reference model**: Use `"bottom"` for most analyses (computationally efficient)
- **Confusion matrix caching**: Reuse the same model/target to benefit from caching
- **Report variables**: Only include variables you need to reduce string processing

---

## Getting Help

```python
# Show quick help with all available functions
pyoccam.help()

# Access demo materials
pyoccam.get_demo_script('basic', copy_to_current=True)    # Basic demo
pyoccam.get_demo_script('advanced', copy_to_current=True)  # Model comparison
pyoccam.get_demo_script('csv', copy_to_current=True)       # CSV conversion

# Run the demo
pyoccam.run_demo()

# Check version
print(pyoccam.__version__)
```

---

## Additional Resources

- **GitHub Repository**: https://github.com/occam-ra/occam (branch: `pyoccam-port`)
- **Test PyPI**: https://test.pypi.org/project/pyoccam/
- **OCCAM Manual**: See `Occam_Manual.pdf` in project files (Martin Zwick, Portland State University)

---

**Last Updated:** February 2026
**Version:** 0.9.5
**Status:** Production Ready for Research Use
