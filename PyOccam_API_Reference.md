# PyOccam API Reference Guide
**Version 0.1.2 | November 2025**

Complete reference for the PyOccam Python package - Python bindings for OCCAM Reconstructability Analysis.

---

## Table of Contents
1. [Quick Start](#quick-start)
2. [Package Installation](#package-installation)
3. [Data Loading API](#data-loading-api)
4. [VBMManager API](#vbmmanager-api)
5. [Model Class API](#model-class-api)
6. [Constants](#constants)
7. [Complete Workflow Examples](#complete-workflow-examples)
8. [Troubleshooting](#troubleshooting)

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

# Get confusion matrix as dictionary (v0.9.0 uses sklearn-compatible train_* keys)
cm = manager.get_confusion_matrix(best, target_state="0")
print(f"Accuracy: {cm['train_accuracy']:.3f}")
print(f"TN={cm['train_tn']:.0f}, FP={cm['train_fp']:.0f}, FN={cm['train_fn']:.0f}, TP={cm['train_tp']:.0f}")
```

---

## Package Installation

### From Test PyPI
```bash
pip install -i https://test.pypi.org/simple/ pyoccam
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
print(pyoccam.__version__)  # Should print: 0.1.2
```

---

## Data Loading API

### `load_dementia()`
Load the built-in dementia (Alzheimer's Disease) dataset.

**Returns:** `OccamData` object

**Example:**
```python
data = pyoccam.load_dementia()
# Output: âœ“ Loaded dementia: 424 samples, 10 features

print(data.n_samples)      # 424
print(data.n_features)     # 10
print(data.feature_names)  # ['Apoe', 'Zyg', 'Ed', 'Kn', 'Gn', 'A', 'Se', ...]
print(data.target_name)    # 'CaseControl'
print(data.has_test_data)  # False (unless test data was loaded)
```

---

### `load_landslides()`
Load the built-in landslides dataset.

**Returns:** `OccamData` object

**Example:**
```python
data = pyoccam.load_landslides()
# Output: âœ“ Loaded landslides: N samples, M features
```

---

### `load_data(filename)`
Load any OCCAM data file.

**Parameters:**
- `filename` (str): Path to data file or name of packaged file

**Returns:** `OccamData` object

**Example:**
```python
# Load from absolute path
data = pyoccam.load_data("/path/to/mydata.txt")

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
- `DESCR` (str): Dataset description (if available)

**Methods:**

#### `quick_search(search_type="loopless-up", levels=3, width=3)`
Run a quick search on this data.

**Example:**
```python
data = pyoccam.load_dementia()
best = data.quick_search(levels=5, width=3)
print(f"Best model: {best}")
```

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
- `args` (list): Command line arguments as list of strings
  - First element should be "occam" (program name)
  - Second element should be the data file path
  - Additional arguments can specify options

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
- `separator` (int): Separator type
  - `pyoccam.TABSEP` (1): Tab-separated
  - `pyoccam.COMMASEP` (2): Comma-separated
  - `pyoccam.SPACESEP` (3): Space-separated (default)
  - `pyoccam.HTMLFORMAT` (4): HTML format

**Example:**
```python
manager.set_report_separator(pyoccam.SPACESEP)  # Recommended
```

---

#### `set_report_variables(variables)`
Set which variables/statistics to display in reports.

**Parameters:**
- `variables` (str): Comma-separated list of variable names

**Available Variables:**
- `level$I`: Search level (integer format)
- `h`: Entropy
- `ddf`: Degrees of freedom delta (use `ddf$I` for integer)
- `lr`: Likelihood ratio
- `alpha`: p-value
- `%dH(DV)`: Percent of DV entropy explained
- `information`: Information (transmission)
- `daic`: AIC relative to reference
- `dbic`: BIC relative to reference
- `incr_alpha`: Incremental alpha (p-value vs. progenitor)
- `pct_correct_data`: Percent correct on training data
- `pct_correct_test`: Percent correct on test data (if available)

**Important:** Do NOT include `ID$I` or `Model` in the variables list - these are added automatically.

**Example:**
```python
# Standard format (no ID or Model)
manager.set_report_variables("level$I, h, ddf, lr, alpha, %dH(DV), daic, dbic")

# With incremental alpha
manager.set_report_variables("level$I, h, ddf, alpha, %dH(DV), daic, dbic, incr_alpha")

# With test data statistics
manager.set_report_variables("level$I, h, ddf, alpha, daic, dbic, pct_correct_data, pct_correct_test")
```

---

#### `set_ref_model(model_name)`
Set the reference model for statistics computation.

**Parameters:**
- `model_name` (str): Reference model name
  - `"bottom"`: Bottom model (independence model) - **recommended**
  - `"top"`: Top model (saturated model)
  - `"default"`: Default model
  - Or any specific model name like `"IV:ABC"`

**Example:**
```python
manager.set_ref_model("bottom")  # Most common choice
```

---

#### `set_search_type(search_type)`
Set the search algorithm type.

**Parameters:**
- `search_type` (str): One of the following:
  - `"loopless-up"`: Loopless ascending (most common)
  - `"loopless-down"`: Loopless descending
  - `"full-up"`: Full ascending
  - `"full-down"`: Full descending
  - `"disjoint-up"`: Disjoint ascending
  - `"disjoint-down"`: Disjoint descending
  - `"chain-up"`: Chain ascending
  - `"chain-down"`: Chain descending

**Example:**
```python
manager.set_search_type("loopless-up")
```

---

#### `set_debug_mode(enable)`
Enable or disable debug output.

**Parameters:**
- `enable` (bool): True to enable debug output, False to disable

**Example:**
```python
manager.set_debug_mode(True)  # Enable detailed output
```

---

### Fit Configuration Methods

#### `set_calc_expected_dv(enable)`
Set whether to calculate expected dependent variable values.

**Parameters:**
- `enable` (bool): True to calculate expected DV values

**Example:**
```python
manager.set_calc_expected_dv(True)
```

---

#### `set_skip_trained_model_table(skip)`
Skip the trained model table in fit output.

**Parameters:**
- `skip` (bool): True to skip the table

**Example:**
```python
manager.set_skip_trained_model_table(False)  # Include the table
```

---

#### `set_skip_ivi_tables(skip)`
Skip the IVI (Individual Variable Information) tables in fit output.

**Parameters:**
- `skip` (bool): True to skip IVI tables

**Example:**
```python
manager.set_skip_ivi_tables(True)  # Skip for cleaner output
```

---

#### `set_fit_classifier_target(target_state)`
Set target state for classifier confusion matrix.

**Parameters:**
- `target_state` (str): Target state value (e.g., "0", "1", "positive")

**Example:**
```python
manager.set_fit_classifier_target("1")  # Treat "1" as positive class
```

---

#### `set_default_fit_model(model_name)`
Set default model for fit comparison.

**Parameters:**
- `model_name` (str): Model name to use as default

**Example:**
```python
manager.set_default_fit_model("bottom")
```

---

### Main Analysis Methods

#### `generate_search_report(search_type, levels, width, include_test_data=False)`
Perform beam search and generate formatted report of best models.

**Parameters:**
- `search_type` (str): Search algorithm (e.g., "loopless-up")
- `levels` (int): Number of levels to search
- `width` (int): Beam width (number of models to keep per level)
- `include_test_data` (bool): **Ignored** - test data columns are automatically included if test data is present

**Returns:** `str` - Formatted report as string

**Example:**
```python
# Basic search
report = manager.generate_search_report("loopless-up", levels=7, width=3)
print(report)

# Output example:
# ID  Model           Level  h       ddf  Alpha    %dH(DV)  dAIC    dBIC
# 1   IV              1      6.234   420  0.000    0.00     0.00    0.00
# 2   IV:ApZ          2      5.891   418  0.023    5.50     -8.34   3.21
# 3   IV:ApZ:EdK      3      5.645   416  0.045    9.45     -14.2   6.54
```

**Notes:**
- Models are stored internally and can be retrieved with `get_kept_models()`
- Best models by various criteria are tracked automatically
- Search results persist until next search is run

---

#### `generate_fit_report(model_name, target_state="0")`
Generate complete fit report for a specific model.

**Parameters:**
- `model_name` (str): Model to fit (e.g., "IV:ApZ:EdK")
- `target_state` (str): Target state for confusion matrix (default: "0")

**Returns:** `str` - Formatted fit report including:
- Model structure
- Fit statistics
- Contingency tables
- Confusion matrix (if target state is specified)
- Test data performance (if test data available)

**Example:**
```python
best = manager.get_best_model_by_bic()
fit_report = manager.generate_fit_report(best, target_state="0")
print(fit_report)

# Output includes:
# - Fit statistics (H, dDF, LR, Alpha, AIC, BIC)
# - Trained model table
# - Confusion matrix:
#           Predicted
#           0      1
# Actual 0  TN     FP
#        1  FN     TP
# - Performance metrics (accuracy, sensitivity, specificity, etc.)
```

---

#### `get_confusion_matrix(model_name, target_state="0")`
Get confusion matrix for a model as a Python dictionary.

**⚠️ v0.9.0 uses sklearn-compatible naming:** All keys use lowercase with explicit `train_` and `test_` prefixes, following sklearn's `cross_validate()` pattern.

**Parameters:**
- `model_name` (str): **REQUIRED** - Model name (e.g., from `get_best_model_by_bic()`)
- `target_state` (str): **REQUIRED** - Target state value (default: "0")

**Returns:** `dict` with the following keys:

**Always Present (Training Data):**
- `'train_tn'` (float): True negatives
- `'train_fp'` (float): False positives
- `'train_fn'` (float): False negatives
- `'train_tp'` (float): True positives
- `'train_accuracy'` (float): Overall accuracy
- `'train_sensitivity'` (float): True positive rate (recall/TPR)
- `'train_specificity'` (float): True negative rate (TNR)
- `'train_precision'` (float): Positive predictive value (PPV)
- `'train_npv'` (float): Negative predictive value (NPV)
- `'train_f1_score'` (float): Harmonic mean of precision and recall
- `'has_values'` (bool): Whether valid values were retrieved

**Present When Test Data Available:**
- `'test_tn'`, `'test_fp'`, `'test_fn'`, `'test_tp'` (float): Test confusion matrix
- `'test_accuracy'` (float): Test set accuracy
- `'test_sensitivity'` (float): Test set sensitivity
- `'test_specificity'` (float): Test set specificity
- `'test_precision'` (float): Test set precision
- `'test_npv'` (float): Test set NPV
- `'test_f1_score'` (float): Test set F1 score
- `'has_test_data'` (bool): True if test metrics are available

**Example (v0.9.0):**
```python
# CORRECT USAGE - Must pass model_name and target_state!
best = manager.get_best_model_by_bic()
cm = manager.get_confusion_matrix(best, target_state="0")  # ✓ CORRECT

# WRONG USAGE - Will raise TypeError!
# cm = manager.get_confusion_matrix()  # ✗ WRONG - missing arguments!

if cm['has_values']:
    # Training data - Use lowercase with train_ prefix!
    print(f"Training Confusion Matrix:")
    print(f"  TN={cm['train_tn']:.0f}, FP={cm['train_fp']:.0f}")
    print(f"  FN={cm['train_fn']:.0f}, TP={cm['train_tp']:.0f}")
    print(f"\nTraining Performance:")
    print(f"  Accuracy:    {cm['train_accuracy']:.3f}")
    print(f"  Sensitivity: {cm['train_sensitivity']:.3f}")
    print(f"  Specificity: {cm['train_specificity']:.3f}")
    print(f"  Precision:   {cm['train_precision']:.3f}")
    print(f"  NPV:         {cm['train_npv']:.3f}")
    print(f"  F1 Score:    {cm['train_f1_score']:.3f}")
    
    # Test data (if available) - Use lowercase with test_ prefix!
    if cm['has_test_data']:
        print(f"\nTest Performance:")
        print(f"  TN={cm['test_tn']:.0f}, FP={cm['test_fp']:.0f}")
        print(f"  FN={cm['test_fn']:.0f}, TP={cm['test_tp']:.0f}")
        print(f"  Accuracy:    {cm['test_accuracy']:.3f}")
        print(f"  Sensitivity: {cm['test_sensitivity']:.3f}")
        print(f"  Specificity: {cm['test_specificity']:.3f}")
        
        # Check for overfitting
        gap = cm['train_accuracy'] - cm['test_accuracy']
        if gap > 0.1:
            print(f"  ⚠️ Large train-test gap: {gap:.3f}")
```

**Key Naming Pattern (v0.9.0):**
```python
# Training metrics - ALL lowercase with train_ prefix
cm['train_tn']          # True negatives
cm['train_fp']          # False positives
cm['train_fn']          # False negatives
cm['train_tp']          # True positives
cm['train_accuracy']    # Accuracy
cm['train_sensitivity'] # Sensitivity/Recall
cm['train_specificity'] # Specificity
cm['train_precision']   # Precision/PPV
cm['train_npv']         # Negative Predictive Value
cm['train_f1_score']    # F1 Score

# Test metrics - ALL lowercase with test_ prefix
cm['test_tn']           # Test true negatives
cm['test_fp']           # Test false positives
cm['test_fn']           # Test false negatives
cm['test_tp']           # Test true positives
cm['test_accuracy']     # Test accuracy
cm['test_sensitivity']  # Test sensitivity
cm['test_specificity']  # Test specificity
cm['test_precision']    # Test precision
cm['test_npv']          # Test NPV
cm['test_f1_score']     # Test F1 score

# Flags - lowercase
cm['has_values']        # True if matrix computed
cm['has_test_data']     # True if test data available
```

**Important Notes:**
- **Sklearn Compatibility**: Naming follows sklearn's `cross_validate()` pattern with explicit `train_` and `test_` prefixes
- **All Lowercase**: Unlike some older examples, v0.9.0 uses ALL lowercase (e.g., `train_tn` not `train_TN`)
- **Smart Caching**: Results are cached - subsequent calls with same model/target are instant
- **Automatic Generation**: First call automatically runs `generate_fit_report()` internally if needed
- **Always Check `has_values`**: Ensure the confusion matrix was successfully computed before accessing values
- **Target State Must Exist**: The target_state must be a valid state in your dependent variable

---

### Best Model Selection Methods

After running `generate_search_report()`, these methods return the best model according to different criteria:

#### `get_best_model_by_bic()`
Get best model by BIC (Bayesian Information Criterion).

**Returns:** `str` - Model name with lowest BIC (most parsimonious)

**Example:**
```python
report = manager.generate_search_report("loopless-up", 7, 3)
best = manager.get_best_model_by_bic()
print(f"Best BIC model: {best}")  # e.g., "IV:ApZ:EdK"
```

---

#### `get_best_model_by_aic()`
Get best model by AIC (Akaike Information Criterion).

**Returns:** `str` - Model name with lowest AIC

---

#### `get_best_model_by_information()`
Get best model by information, following the official OCCAM manual definition.

**OCCAM Manual Definition (Section IV):** "The best model by Information is the model with highest information where ALL steps from the starting model have Incremental Alpha < 0.05." This ensures every step in the path is statistically significant.

**Returns:** `str` - Model name with highest information where all incremental steps are statistically significant (Inc.Alpha < 0.05). Returns empty string if no models meet the criterion.

**Example:**
```python
# Get statistically defensible best model by information
best = manager.get_best_model_by_information()

# This returns only models marked with * in OCCAM search output
# (models "reachable" via all statistically significant steps)
```

**Why This Matters:**
- Models with Inc.Alpha > 0.05 may be overfitting
- The "highest raw information" model may include components that don't significantly improve prediction
- This method returns scientifically defensible models for publication

---

### Model Operations

#### `make_model(model_name, make_fit_table=False)`
Create a model and optionally compute its statistics.

**Parameters:**
- `model_name` (str): Model structure (e.g., "IV:ABC:DEF")
- `make_fit_table` (bool): If True, compute fit table and all statistics

**Returns:** `Model` object

**Example:**
```python
# Just create the model structure
model = manager.make_model("IV:ApZ")

# Create model and compute all statistics
model = manager.make_model("IV:ApZ:EdK", make_fit_table=True)
print(f"Model: {model.name}")
print(f"BIC: {model.bic:.2f}")
print(f"Information: {model.information:.4f}")
```

---

#### `get_model_statistics(model_name)`
Get complete statistics for a specific model. Equivalent to `make_model(model_name, make_fit_table=True)`.

**Parameters:**
- `model_name` (str): Model structure

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
Get list of all variable names in the dataset.

**Returns:** `list` of strings (variable names in order, with dependent variable last)

**Example:**
```python
vars = manager.get_variable_list()
print(vars)  # ['Apoe', 'Zyg', 'Ed', 'Kn', ..., 'CaseControl']
print(f"Dependent variable: {vars[-1]}")
```

---

#### `get_basic_statistics()`
Get basic dataset statistics as formatted string.

**Returns:** `str` - Multi-line string with:
- Sample size
- Number of variables
- H(data) - entropy of the data
- Test data status

**Example:**
```python
stats = manager.get_basic_statistics()
print(stats)
# Output:
# Sample size: 424
# Variables: 11
# H(data): 6.234
# Test data: None
```

---

#### `get_sample_size()`
Get the number of samples in the dataset.

**Returns:** `int` - Number of samples

**Example:**
```python
n = manager.get_sample_size()
print(f"Dataset has {n} samples")
```

---

#### `has_test_data()`
Check if test data is available.

**Returns:** `bool` - True if test data is present

**Example:**
```python
if manager.has_test_data():
    print("Test data available - will compute test performance")
    # Set up test data reporting
    manager.set_report_variables("level$I, h, ddf, alpha, daic, dbic, pct_correct_data, pct_correct_test")
else:
    print("No test data - using training data only")
```

---

#### `get_available_search_types()`
Get list of available search algorithm types.

**Returns:** `list` of strings

**Example:**
```python
types = manager.get_available_search_types()
print(types)
# ['loopless-up', 'loopless-down', 'full-up', 'full-down',
#  'disjoint-up', 'disjoint-down', 'chain-up', 'chain-down']
```

---

### Report Access Methods

#### `get_kept_models()`
Get list of all models kept from the last beam search.

**Returns:** `list` of `Model` objects

**Example:**
```python
manager.generate_search_report("loopless-up", 5, 3)
models = manager.get_kept_models()

for model in models:
    print(f"{model.name}: BIC={model.bic:.2f}, Info={model.information:.4f}")
```

---

#### `get_search_model_count()`
Get count of models kept from the last search.

**Returns:** `int` - Number of kept models

**Example:**
```python
count = manager.get_search_model_count()
print(f"Search found {count} models")
```

---

## Model Class API

The `Model` class represents a single OCCAM model with its statistics.

### Attributes

All attributes are read/write:

- `name` (str): Model name (e.g., "IV:ApZ:EdK")
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
- `pct_coverage` (float): Percent coverage (for test data)
- `pct_missed_test` (float): Percent missed in test data (0.0 if no test data)
- `incr_alpha` (float): Incremental alpha (vs progenitor model)
- `level` (int): Search level

### Example

```python
manager = data.manager
manager.generate_search_report("loopless-up", 7, 3)

models = manager.get_kept_models()
for model in models:
    print(f"Model: {model.name}")
    print(f"  Level: {model.level}")
    print(f"  H: {model.h:.3f}")
    print(f"  BIC: {model.bic:.2f}")
    print(f"  Information: {model.information:.4f}")
    print(f"  Alpha: {model.alpha:.6f}")
    print(f"  % Correct: {model.pct_correct_data:.1f}%")
    if model.pct_correct_test > 0:
        print(f"  % Correct (test): {model.pct_correct_test:.1f}%")
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

**Example:**
```python
print(f"Using PyOccam version {pyoccam.__version__}")
manager.set_report_separator(pyoccam.SPACESEP)
```

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
print("\nRunning beam search...")
report = manager.generate_search_report("loopless-up", levels=7, width=3)
print(report)

# 4. Get best model
best = manager.get_best_model_by_bic()
print(f"\nBest model by BIC: {best}")

# 5. Generate fit report
print("\nFit Report:")
fit_report = manager.generate_fit_report(best, target_state="0")
print(fit_report)

# 6. Extract confusion matrix
cm = manager.get_confusion_matrix(best, target_state="0")
print(f"\nConfusion Matrix Analysis:")
print(f"  Accuracy: {cm['accuracy']:.3f}")
print(f"  Sensitivity: {cm['sensitivity']:.3f}")
print(f"  Specificity: {cm['specificity']:.3f}")
print(f"  F1 Score: {cm['f1_score']:.3f}")
```

---

### Model Comparison

```python
import pyoccam

data = pyoccam.load_dementia()
manager = data.manager
manager.set_report_separator(pyoccam.SPACESEP)

# Run search
manager.generate_search_report("loopless-up", 7, 3)

# Get different "best" models
best_bic = manager.get_best_model_by_bic()
best_aic = manager.get_best_model_by_aic()
best_info = manager.get_best_model_by_information()  # OCCAM manual definition: highest info with inc.alpha < 0.05

print("Model Selection Comparison:")
print(f"  Best BIC (most parsimonious): {best_bic}")
print(f"  Best AIC (intermediate):      {best_aic}")
print(f"  Best Information (stat sig):  {best_info}")

# Compare specific models
for model_name in [best_bic, best_aic, best_info]:
    if model_name:  # Check not empty
        model = manager.get_model_statistics(model_name)
        print(f"\n{model.name}:")
        print(f"  BIC: {model.bic:.2f}")
        print(f"  AIC: {model.aic:.2f}")
        print(f"  Information: {model.information:.4f}")
        print(f"  % Correct: {model.pct_correct_data:.1f}%")
```

---

### Working with Test Data

```python
import pyoccam

# Load data with test split
data = pyoccam.load_data("data_with_test.txt")
manager = data.manager

# Check if test data is present
if manager.has_test_data():
    print("Test data detected - configuring for train/test analysis")
    
    # Include test columns in reports
    manager.set_report_variables(
        "level$I, h, ddf, alpha, daic, dbic, "
        "pct_correct_data, pct_correct_test, pct_missed_test"
    )
    
    # Run search (test columns auto-included)
    report = manager.generate_search_report("loopless-up", 5, 3)
    print(report)
    
    # Get best model and confusion matrix
    best = manager.get_best_model_by_bic()
    cm = manager.get_confusion_matrix(best, "0")
    
    # Training performance (v0.9.0+ uses train_* prefix)
    print(f"\nTraining Data:")
    print(f"  Accuracy: {cm['train_accuracy']:.3f}")
    print(f"  TN={cm['train_tn']:.0f}, FP={cm['train_fp']:.0f}, FN={cm['train_fn']:.0f}, TP={cm['train_tp']:.0f}")
    
    # Test performance (v0.9.0+ uses test_* prefix with lowercase)
    if cm['has_test_data']:
        print(f"\nTest Data:")
        print(f"  Accuracy: {cm['test_accuracy']:.3f}")
        print(f"  Sensitivity: {cm['test_sensitivity']:.3f}")
        print(f"  Specificity: {cm['test_specificity']:.3f}")
        print(f"  TN={cm['test_tn']:.0f}, FP={cm['test_fp']:.0f}, FN={cm['test_fn']:.0f}, TP={cm['test_tp']:.0f}")
else:
    print("No test data - using training data only")
```

---

### Advanced: Exploring Multiple Search Strategies

```python
import pyoccam

data = pyoccam.load_dementia()
manager = data.manager
manager.set_report_separator(pyoccam.SPACESEP)
manager.set_report_variables("level$I, h, ddf, alpha, daic, dbic")

search_types = ["loopless-up", "disjoint-up", "chain-up"]
results = {}

for search_type in search_types:
    print(f"\nRunning {search_type} search...")
    report = manager.generate_search_report(search_type, levels=5, width=3)
    best = manager.get_best_model_by_bic()
    
    # Get statistics for best model
    model = manager.get_model_statistics(best)
    results[search_type] = {
        'model': model.name,
        'bic': model.bic,
        'info': model.information,
        'alpha': model.alpha
    }
    
    print(f"  Best: {model.name} (BIC={model.bic:.2f})")

# Summary comparison
print("\n" + "="*60)
print("Search Strategy Comparison:")
print("="*60)
for search_type, res in results.items():
    print(f"{search_type:15s} {res['model']:20s} BIC={res['bic']:7.2f} Info={res['info']:.4f}")
```

---

### Quick One-Liner Analysis

```python
import pyoccam

# Load data and run search in one line
data, best = pyoccam.quick_search("dementia05.txt", "loopless-up", levels=7, width=3)

# Generate fit report
fit_report = data.manager.generate_fit_report(best, "0")
print(fit_report)

# Get confusion matrix
cm = data.manager.get_confusion_matrix(best, "0")
print(f"Accuracy: {cm['accuracy']:.3f}")
```

---

### Using the Convenience Wrapper

```python
import pyoccam

# Using OccamData's convenience method
data = pyoccam.load_dementia()

# Quick search directly on the data object
best = data.quick_search(search_type="loopless-up", levels=5, width=3)

# Access manager for detailed analysis
manager = data.manager
cm = manager.get_confusion_matrix(best, "0")
print(f"Best model: {best}")
print(f"Accuracy: {cm['accuracy']:.3f}")
```

---

## Troubleshooting

### Common Issues

#### Import Error: Module Not Found
```python
# Error: ModuleNotFoundError: No module named 'pyoccam'

# Solution: Rebuild the extension
# In Anaconda PowerShell:
python setup.py clean --all
python setup.py build_ext --inplace --compiler=mingw32
pip install -e .
```

#### Import Error: DLL Load Failed
```python
# Error: ImportError: DLL load failed while importing _pyoccam

# Solution: Ensure MinGW is in PATH and rebuild
# Check MinGW installation:
gcc --version  # Should show MinGW

# Rebuild:
python setup.py clean --all
python setup.py build_ext --inplace --compiler=mingw32
```

#### Empty Model Name from get_best_model_*
```python
best = manager.get_best_model_by_bic()
if not best or best == "":
    print("No models found - did you run generate_search_report first?")
    
# Solution: Always run generate_search_report before calling get_best_model_*
manager.generate_search_report("loopless-up", 7, 3)
best = manager.get_best_model_by_bic()  # Now works
```

#### Confusion Matrix Returns Empty
```python
cm = manager.get_confusion_matrix("IV:ApZ", "0")
if not cm['has_values']:
    print("No confusion matrix - check model name and target state")
    
# Solution: Ensure model name is correct and was in the search results
# Or call generate_fit_report first:
manager.generate_fit_report("IV:ApZ", "0")
cm = manager.get_confusion_matrix("IV:ApZ", "0")  # Now works
```

#### Invalid Search Type
```python
# Error: Unknown search type

# Solution: Use exact strings with "-up" or "-down" suffix
manager.generate_search_report("loopless-up", 7, 3)  # Correct
# NOT: "loopless" or "loopless_up"

# Check available types:
print(manager.get_available_search_types())
```

#### Data File Not Found
```python
# Error: FileNotFoundError

# Solution: Use absolute paths or ensure file is in current directory
import os
print(os.getcwd())  # Check current directory
data = pyoccam.load_data(os.path.abspath("mydata.txt"))
```

---

### Best Practices

1. **Always call `generate_search_report()` before `get_best_model_*()`**
   ```python
   # Good
   manager.generate_search_report("loopless-up", 7, 3)
   best = manager.get_best_model_by_bic()
   
   # Bad - will return empty string
   best = manager.get_best_model_by_bic()  # No search run yet!
   ```

2. **Use SPACESEP for readable reports**
   ```python
   manager.set_report_separator(pyoccam.SPACESEP)  # Recommended
   ```

3. **Don't include ID or Model in report variables**
   ```python
   # Good
   manager.set_report_variables("level$I, h, ddf, alpha, daic, dbic")
   
   # Bad - ID and Model are added automatically
   manager.set_report_variables("ID$I, Model, level$I, h")  # Don't do this
   ```

4. **Check for test data before accessing test metrics**
   ```python
   if manager.has_test_data():
       manager.set_report_variables("..., pct_correct_test")
   ```

5. **Cache confusion matrix results when needed repeatedly**
   ```python
   # First call generates report and caches
   cm = manager.get_confusion_matrix(best, "0")
   
   # Subsequent calls with same model/target are instant
   cm2 = manager.get_confusion_matrix(best, "0")  # Returns cached result
   
   # Different model or target generates new report
   cm3 = manager.get_confusion_matrix(best, "1")  # New computation
   ```

6. **Use appropriate search levels and width**
   ```python
   # For initial exploration: shallow and narrow
   manager.generate_search_report("loopless-up", levels=3, width=3)
   
   # For thorough analysis: deeper and wider
   manager.generate_search_report("loopless-up", levels=7, width=5)
   
   # Balance time vs thoroughness based on dataset size
   ```

---

### Performance Tips

- **Beam search parameters**: Larger width and more levels increase computation time
- **Reference model**: Use "bottom" for most analyses (computationally efficient)
- **Confusion matrix caching**: Reuse the same Model instance to benefit from caching
- **Report variables**: Only include variables you need to reduce string processing

---

## Getting Help

```python
# Show quick help
pyoccam.help()

# Access demo materials
demo_path = pyoccam.get_demo_script(copy_to_current=True)
notebook_path = pyoccam.get_demo_notebook(copy_to_current=True)

# Run the demo
pyoccam.run_demo()

# Check version
print(pyoccam.__version__)
```

---

## Additional Resources

- **GitHub Repository**: https://github.com/occam-ra/occam
- **Test PyPI**: https://test.pypi.org/project/pyoccam/
- **OCCAM Manual**: See `Occam_Manual.pdf` in project files

---

**Last Updated:** November 2025  
**Version:** 0.1.2  
**Status:** Production Ready for Research Use
