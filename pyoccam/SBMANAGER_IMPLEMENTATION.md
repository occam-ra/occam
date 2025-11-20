# SBMManager Implementation in pybind11

## Overview

SBMManager (State-Based Manager) support has been successfully added to `pyoccam_pybind11.cpp`. This enables State-Based Modeling operations in Python 3, completing the core functionality needed for the Flask web server migration.

## What Was Added

### PySBMManager Class

A complete C++ wrapper class `PySBMManager` was added to `pyoccam_pybind11.cpp` (lines 764-1314), providing:

1. **Initialization**
   - `init_from_command_line()` - Initialize from command-line style arguments

2. **Configuration Methods**
   - `set_report_separator()` - Configure output format
   - `set_report_variables()` - Select which statistics to display
   - `set_ref_model()` - Set reference model
   - `set_search_type()` - Configure search algorithm
   - `set_debug_mode()` - Enable debug output
   - `set_calc_expected_dv()` - Calculate expected DV values
   - `set_skip_trained_model_table()` - Skip trained model output
   - `set_skip_ivi_tables()` - Skip IVI tables
   - `set_fit_classifier_target()` - Set target for confusion matrix
   - `set_default_fit_model()` - Set default comparison model

3. **Core Operations**
   - `generate_search_report()` - Perform beam search and generate report
   - `generate_fit_report()` - Fit a specific model and generate report

4. **Model Access**
   - `get_best_model_by_bic()` - Best model by BIC criterion
   - `get_best_model_by_aic()` - Best model by AIC criterion
   - `get_best_model_by_information()` - Best model by information
   - `get_best_model_by_info_alpha()` - Best model with incr_alpha < 0.05
   - `make_model()` - Create a state-based model
   - `get_model_statistics()` - Get statistics for a model
   - `get_kept_models()` - Get all models kept from search

5. **Information Getters**
   - `get_variable_list()` - List of variable names
   - `get_basic_statistics()` - Basic statistics string
   - `get_sample_size()` - Sample size
   - `has_test_data()` - Check for test data
   - `get_available_search_types()` - Available SB search types
   - `get_search_model_count()` - Count of kept models

## Key Differences from VBMManager

The main difference between PySBMManager and PyVBMManager is the model creation method:

- **VBMManager**: Uses `manager.makeModel(name, makeProject)`
- **SBMManager**: Uses `manager.makeSbModel(name, makeProject)`

Otherwise, the APIs are identical, which allows for polymorphic usage in the Flask wrapper.

## Search Types for State-Based Modeling

PySBMManager supports these search types:
- `sb-loopless-up`
- `sb-loopless-down`
- `sb-full-up`
- `sb-full-down`
- `sb-disjoint-up`
- `sb-disjoint-down`
- `sb-chain-up`
- `sb-chain-down`

## Python Module Integration

The SBMManager class is exposed in the pybind11 module (lines 1418-1492) as:

```python
import _pyoccam

# Create state-based manager
sbm = _pyoccam.SBMManager()

# Initialize from data file
sbm.init_from_command_line(["occam", "datafile.txt"])

# Perform search
report = sbm.generate_search_report("sb-loopless-up", levels=5, width=3)

# Fit a specific model
fit_report = sbm.generate_fit_report("AB:01,BC:10")
```

## Flask Wrapper Integration

The `OccamManager` wrapper in `flask_app/occam_wrapper.py` has been updated to support SBMManager:

```python
from occam_wrapper import OccamManager

# Create state-based manager
oc = OccamManager("SB")
oc.init_from_file("datafile.txt")

# Use same API as VB manager
report = oc.do_search("sb-loopless-up", levels=5, width=3)
fit = oc.do_fit("AB:01,BC:10")
```

The wrapper provides a unified interface for both VB and SB modeling.

## Implementation Details

### Internal State Tracking

Like PyVBMManager, PySBMManager maintains:
- `kept_models` - Vector of models kept from beam search
- `best_models` - Map of best models by criterion
- `all_models_seen` - Map of all models generated (for deduplication)

### Statistics Computation

The `computeModelStatistics()` helper computes all standard statistics:
- L2 (log-likelihood) statistics
- Dependent variable statistics
- Information statistics
- Percent correct
- Incremental alpha

### Report Generation

Reports are generated using the OCCAM `Report` class, with support for:
- Multiple output formats (TAB, CSV, SPACE, HTML)
- Configurable variable display
- Automatic test data column inclusion
- Sorted output

### Test Data Support

Full test data support is included:
- Auto-detection of test data in input files
- Test performance metrics in reports
- Confusion matrix for classifier evaluation

## Building

To rebuild the module with SBMManager support:

```bash
cd /path/to/pyoccam
# Build instructions TBD - requires pybind11, GMP, Boost
```

Prebuilt wheels may need to be regenerated to include this new functionality.

## Testing

Test the SBMManager implementation:

```python
import _pyoccam

# Create manager
sbm = _pyoccam.SBMManager()

# Test initialization
success = sbm.init_from_command_line(["occam", "test_data.txt"])
print(f"Initialization: {'OK' if success else 'FAILED'}")

# Test search
report = sbm.generate_search_report("sb-loopless-up", 3, 2)
print(report)

# Test fit
fit = sbm.generate_fit_report("IV:1,DV:0")
print(fit)
```

## Version

This implementation is included in version 0.1.3 of the pyoccam module.

## References

- Original SBMManager: `cpp/pyoccam.cpp` lines 740-1263
- SBMManager C++ class: `include/SBMManager.h`
- PySBMManager implementation: `pyoccam/pyoccam_pybind11.cpp` lines 764-1314
- Module bindings: `pyoccam/pyoccam_pybind11.cpp` lines 1418-1492
- Flask wrapper: `flask_app/occam_wrapper.py`
