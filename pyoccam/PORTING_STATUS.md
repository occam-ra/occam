# Python 3 Porting Status

## Summary

The `pyoccam_pybind11.cpp` provides modern Python 3 bindings for OCCAM using pybind11.
This document tracks what has been ported vs. what remains from the original `cpp/pyoccam.cpp`.

## Completed ✅

### PyVBMManager (Variable-Based Modeling)
- ✅ init_from_command_line
- ✅ Beam search with proper incremental alpha
- ✅ Fit report generation
- ✅ Search report generation
- ✅ Test data support
- ✅ Model statistics
- ✅ Best model selection (BIC, AIC, Information)
- ✅ Variable list access
- ✅ Basic statistics
- ✅ Configuration setters

### PySBMManager (State-Based Modeling) ✅ NEW!
- ✅ init_from_command_line
- ✅ Beam search with proper incremental alpha
- ✅ Fit report generation (using makeSbModel)
- ✅ Search report generation
- ✅ Test data support
- ✅ Model statistics
- ✅ Best model selection (BIC, AIC, Information)
- ✅ Variable list access
- ✅ Basic statistics
- ✅ Configuration setters
- ✅ All methods mirroring PyVBMManager

### PyModel
- ✅ All standard statistics fields
- ✅ Test data fields (pct_correct_test, pct_coverage, pct_missed_test)

## Still Missing from Original ❌

### Report Class
The original exposes a `Report` class for more granular control:
- addModel
- setDefaultFitModel
- setAttributes
- sort
- setSeparator
- printReport
- writeReport
- printConditional_DV
- printResiduals

Currently, the pybind11 version generates reports internally within PyVBMManager.

### Model Class (Low-level)
Direct Model manipulation methods:
- getRelation
- get (attribute access)
- setProgenitor / getProgenitor
- setID
- isEquivalentTo
- deleteFitTable
- dump

Most of these are handled internally, but some may be needed for advanced use cases.

### Relation Class
Low-level relation operations - probably not needed for web server.

## Recommendations

For the Flask web server migration:

1. **Priority 1**: Add SBMManager to pybind11 bindings
   - Copy PyVBMManager structure
   - Adapt for SBMManager C++ class
   - Add to module definition

2. **Priority 2**: Create Python wrapper layer (`occam.py`)
   - Provide compatibility shim for old code
   - Map old API calls to new pybind11 API
   - Handle Report class functionality via wrapper

3. **Priority 3**: Low-level classes (if needed)
   - Assess if Model/Relation direct access is needed
   - Most operations work through Manager classes

## Next Steps

1. Test current pybind11 bindings with VB modeling
2. Add SBMManager support
3. Create ocutils.py wrapper for new bindings
4. Migrate Flask web server to use new bindings
