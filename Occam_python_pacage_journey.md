# OCCAM Python Package Development Journey
## Complete Reproducible Reference

**Date**: October 17, 2025  
**Status**: Confusion Matrix Extraction Working ✅  
**Version**: pyoccam 0.1.2

---

## 🎯 Project Goal

Port OCCAM (Organizational Complexity Analysis Method) from a C++ program with Python web wrapper to a modern Python package suitable for Jupyter notebooks and data science workflows.

**Source Repository**: https://github.com/occam-ra/occam  
**Key Reference Files**: `weboccam.py`, `pyoccam.py`, `ocutils.py`  
**Gold Standard**: Server output PDFs (dementia05 loopless and full-up search results)

---

## 📊 Progress Overview

### Journey Phases
1. **Initial Setup** (July 2025) - Math header conflicts, compiler issues
2. **MinGW Migration** (July-August 2025) - Windows compatibility, build system
3. **API Discovery** (August 2025) - Finding what actually exists in OCCAM
4. **Report Integration** (September 2025) - Using OCCAM's built-in Report class
5. **Confusion Matrix** (October 2025) - Direct C++ API access without text parsing

### Current Completion: ~98%
- ✅ Data loading and validation
- ✅ Multi-level search with all algorithms
- ✅ Statistics computation (BIC, AIC, Information)
- ✅ Report generation matching server format
- ✅ Best model tracking and selection
- ✅ **Confusion matrix extraction** (NEW - Oct 17, 2025)
- ⏳ Test data confusion matrix verification (in progress)

---

## 🔥 Critical Discoveries

### Discovery #1: Search Type Naming Convention
**Problem**: Search would silently fail  
**Root Cause**: All search types require "-up" suffix  

```python
# ❌ WRONG - spent days debugging
manager.set_search_type("loopless")  

# ✅ CORRECT
manager.set_search_type("loopless-up")
```

**Valid search types**: `loopless-up`, `full-up`, `disjoint-up`, `chain-up`

---

### Discovery #2: Statistics Computation Sequence
**Problem**: All model statistics returned -1.0000  
**Root Cause**: Methods must be called in exact order  

```cpp
// Critical sequence - order matters!
void computeAllStatistics(Model* model) {
    manager.makeFitTable(model);              // Step 1: Create fit table
    manager.computeL2Statistics(model);       // Step 2: AIC, BIC, LR, alpha
    manager.computeDependentStatistics(model);// Step 3: For directed systems
    manager.computeInformationStatistics(model); // Step 4: Information measures
    manager.computePercentCorrect(model);     // Step 5: Prediction accuracy
}
```

---

### Discovery #3: OCCAM Has Built-in Report Class
**Problem**: Manual string formatting was error-prone and didn't match server  
**Solution**: OCCAM already has a sophisticated `Report` class!

```cpp
// Pattern from ocutils.py:
Report* report = new Report(&manager);
report->setSeparator(3);  // Space-separated
report->setAttributes("ID$I, Model, Level$I, h, ddf, dLR, Alpha, Inf, %dH(DV), dAIC, dBIC");
report->addModel(model);
report->sort("information", Direction::Descending);  // Enum, not string!
report->print(temp_file);
```

---

### Discovery #4: MinGW is Required on Windows
**Problem**: MSVC compilation failed with namespace conflicts  
**Root Cause**: OCCAM is Unix-centric, Python built with MinGW, ABI incompatibility

**Solution**: Use MinGW compiler exclusively
```bash
python setup.py build_ext --compiler=mingw32 --inplace
```

**Required setup.py configuration**:
```python
class build_ext_mingw(build_ext_orig):
    def build_extensions(self):
        compiler = new_compiler(compiler='mingw32')
        customize_compiler(compiler)
        self.compiler = compiler
        super().build_extensions()

extra_compile_args=["-std=c++14", "-O2", "-w", "-DMS_WIN64"],
cmdclass={'build_ext': build_ext_mingw},
```

---

### Discovery #5: Math Header Conflicts
**Problem**: Compiler finding OCCAM's `Math.h` instead of system `<math.h>`  
**Solution**: Rename OCCAM's header to `OccamMath.h`

```cpp
// All OCCAM files changed from:
#include "Math.h"
// To:
#include "OccamMath.h"

// System math stays as:
#include <math.h>
```

**Windows compatibility patches**:
```cpp
// ManagerBase.cpp and Model.cpp
#define _USE_MATH_DEFINES
#include <math.h>
#include <cmath>

using std::fabs;
using std::sqrt;
using std::log;
using std::exp;
using std::pow;

#ifndef M_LN2
#define M_LN2 0.693147180559945309417
#endif
```

---

### Discovery #6: API Methods That Actually Exist
Many methods we assumed existed... don't!

**✅ Methods that WORK**:
```cpp
// VBMManager
manager.initFromCommandLine(argc, argv)
manager.setRefModel("bottom")
manager.setSearch("loopless-up")  // NOT setSearchType!
manager.makeModel("IV:ApZ", true)
manager.makeFitTable(model)
manager.computeL2Statistics(model)
manager.getTopRefModel()
manager.getBottomRefModel()
manager.getVariableList()
manager.getFitTable()  // Returns the fit table

// Report
report->setSeparator(1-4)  // 1=tab, 2=comma, 3=space, 4=HTML
report->addModel(model)
report->sort("information", Direction::Descending)
report->print(FILE*)
```

**❌ Methods that DON'T EXIST**:
```cpp
manager.setSearchType()     // Use setSearch() instead
manager.doSearch()          // Must implement manually
manager.getSearchResults()  // Must track manually
relation->getFitTable()     // Only manager has this
table->getDistribution()    // Must iterate manually
```

---

### Discovery #7: Confusion Matrix Direct Access
**Date**: October 17, 2025  
**Problem**: Text parsing was unreliable and didn't work for all models  
**Solution**: Add `computeConfusionMatrix()` method directly to VBMManager

**The Breakthrough**:
```cpp
// VBMManager.cpp - New method
ConfusionMatrixData VBMManager::computeConfusionMatrix(Model* model, const char* target_state) {
    // 1. Get fit table from manager (NOT from relation!)
    Table* fit_table = getFitTable();
    
    // 2. Use ManagerBase::makeProjection (3-parameter version)
    ManagerBase::makeProjection(inputData, input_table, predRelWithDV);
    
    // 3. Manually iterate through tuples (no getDistribution!)
    for (int dv_state = 0; dv_state < dv_card; dv_state++) {
        KeySegment* full_key = new KeySegment[keysize];
        Key::copyKey(base_key, full_key, keysize);
        Key::setKeyValue(full_key, keysize, var_list, dv_index, dv_state);
        
        long fit_idx = fit_table->indexOf(full_key, true);
        if (fit_idx >= 0) {
            fit_prob[i][dv_state] = fit_table->getValue(fit_idx);
        }
    }
    
    // 4. Compute TP, TN, FP, FN by examining fit rules
    return result;
}
```

**Key Lessons**:
- `Relation::getFitTable()` doesn't exist → use `VBMManager::getFitTable()`
- `VBMManager::makeProjection()` takes 0 params → use `ManagerBase::makeProjection()` with 3 params
- `Table::getDistribution()` doesn't exist → iterate manually with `getKey()`, `getValue()`, `indexOf()`

---

## 🔧 Build System Configuration

### Windows Build Requirements
**Compiler**: MinGW32 (NOT MSVC!)  
**Python**: Must use Anaconda Python (built with MinGW)  
**Build Command**: `python setup.py build_ext --compiler=mingw32 --inplace`

### setup.py Key Sections
```python
Extension(
    'pyoccam._pyoccam',
    sources=[
        'pyoccam/pyoccam_pybind11.cpp',
        # ... all cpp files ...
    ],
    include_dirs=['include'],
    libraries=[],  # Empty! Manual DLL linking
    extra_compile_args=["-std=c++14", "-O2", "-w", "-DMS_WIN64"],
    extra_link_args=[r"C:\...\python39.dll"],  # Direct DLL link
    language='c++'
)
```

### Windows Compatibility Patches
```cpp
// ManagerBase.cpp
#ifdef _WIN32
    #include <io.h>
    #include <process.h>
    #define strcasecmp _stricmp
    #define strncasecmp _strnicmp
    #pragma warning(disable: 4996)
    #ifndef M_LN2
    #define M_LN2 0.693147180559945309417
    #endif
#else
    #include <unistd.h>
    #include <cxxabi.h>
#endif
```

---

## 📝 Complete Working Python API

### Basic Usage Pattern
```python
import pyoccam

# 1. Initialize and load data
manager = pyoccam.VBMManager()
if not manager.init_from_command_line(["occam", "dementia05.txt"]):
    print("Failed to load data")
    exit(1)

# 2. Configure
manager.set_report_separator(pyoccam.SPACESEP)
manager.set_ref_model("bottom")

# 3. Run search
search_report = manager.generate_search_report(
    search_type="loopless-up",  # Must have "-up" suffix!
    levels=7,
    width=3
)

# 4. Get best models
best_bic = manager.get_best_model_by_bic()
best_aic = manager.get_best_model_by_aic()
best_info = manager.get_best_model_by_information()

# 5. Generate detailed fit report
fit_report = manager.generate_fit_report(best_bic, target_state="0")

# 6. Extract confusion matrix (NEW!)
cm = manager.get_confusion_matrix(best_bic, target_state="0")

print(f"Model: {best_bic}")
print(f"Accuracy: {cm['accuracy']:.3f}")
print(f"Sensitivity: {cm['sensitivity']:.3f}")
print(f"Specificity: {cm['specificity']:.3f}")
print(f"TN={cm['TN']:.0f}, FP={cm['FP']:.0f}")
print(f"FN={cm['FN']:.0f}, TP={cm['TP']:.0f}")
```

### Model Notation (CRITICAL!)
```python
# Independence model (2 relations):
"IV:ApZ"  # Ap and Z are INDEPENDENT - no prediction!

# Predictive model (2 relations):  
"IV:Ap:Z"  # Ap PREDICTS Z - can compute confusion matrix!

# Multi-component predictive model:
"IV:Ap:Z:Ed:Z"  # Both Ap and Ed predict Z
```

---

## 🎉 Major Milestones

### Phase 1: Initial Setup (July 2025)
- ❌ MSVC compilation failed
- ❌ All statistics showing -1.0
- ❌ Manual string formatting error-prone

### Phase 2: MinGW Migration (July-August 2025)
- ✅ Switched to MinGW compiler
- ✅ Fixed math header conflicts
- ✅ Windows compatibility patches applied

### Phase 3: API Discovery (August 2025)
- ✅ Found correct statistics computation sequence
- ✅ Discovered search type "-up" requirement
- ✅ Mapped actual vs assumed API methods

### Phase 4: Report Integration (September 2025)
- ✅ Integrated OCCAM's built-in Report class
- ✅ Search reports matching server format
- ✅ Best model tracking implemented

### Phase 5: Confusion Matrix (October 2025)
- ✅ Added direct C++ API for confusion matrix
- ✅ No text parsing required
- ✅ Real values from actual model predictions
- ⏳ Test data support verification (in progress)

---

## 📊 Current Test Results

### Successful Confusion Matrix Extraction (Oct 17, 2025)
```
Testing: IV:ApZ
  ✓ SUCCESS!
    TN=358  FP=84
    FN=196  TP=210
    Accuracy: 0.670
    Sensitivity: 0.517
    Specificity: 0.810

Testing: IV:EdZ
  ✓ SUCCESS!
    TN=432  FP=10
    FN=360  TP=46
    Accuracy: 0.564
    Specificity: 0.977  (very conservative predictor)

Testing: IV:ApZ:EdZ  
  ✓ SUCCESS!
    TN=352  FP=90
    FN=168  TP=238
    Accuracy: 0.696  (best so far!)
```

---

## 🔮 Remaining Work (~2%)

### Immediate Priority
- [ ] Verify test data confusion matrix calculation
- [ ] Test with dataset that has train/test split
- [ ] Ensure `has_test_data` flag works correctly
- [ ] Verify test CM values match expected results

### Future Enhancements
- [ ] Direct contingency table access (beyond confusion matrix)
- [ ] Component-wise analysis for multi-relation models
- [ ] Cross-validation helper functions
- [ ] sklearn-compatible estimator interface

---

## 🎓 Key Lessons for Reproducibility

### If Starting Fresh
1. **Use MinGW on Windows** - MSVC will not work
2. **Rename Math.h first** - Prevents compiler confusion
3. **Follow the exact statistics sequence** - Order matters!
4. **Use "-up" suffix on all searches** - Will fail silently otherwise
5. **Check methods exist before calling** - Many assumed methods don't exist
6. **Use ManagerBase::makeProjection** - Not VBMManager::makeProjection
7. **Iterate tables manually** - No getDistribution() method
8. **Reference ocutils.py patterns** - Shows how original Python wrapper worked

### Common Pitfalls to Avoid
- ❌ Assuming MSVC will work (it won't)
- ❌ Using relation->getFitTable() (doesn't exist)
- ❌ Calling table->getDistribution() (doesn't exist)
- ❌ Forgetting "-up" on search types (silent failure)
- ❌ Wrong statistics computation order (all -1.0)
- ❌ Mixing independence and predictive model notation
- ❌ Parsing text reports when API access exists

---

## 📚 Reference Documentation

### Essential Files
- `VBMManager.h/cpp` - Main manager class
- `ManagerBase.h/cpp` - Base class with projection methods
- `Table.h/cpp` - Data table with tuples
- `Report.h/cpp` - Output formatting
- `ReportPrintConditionalDV.cpp` - Confusion matrix reference implementation
- `ocutils.py` - Original Python patterns
- `weboccam.py` - Web interface reference

### Server Output (Gold Standard)
- `server_search_output_dementia05_loopless.PDF`
- `server_search_output_dementia05_full-up.PDF`
- `SY_sample_pts_to_occam3_shuffle_split42_hdr_server_fit.csv`

### Key CSV Test Files
- `dementia05_search_fullup.csv` - Full search results
- `dementia05_fit_IV_ApZ_EdZ_CZ.csv` - Fit report with CM
- `SY_sample_pts_to_occam3_*` - Test data splits

---

## ✅ Success Criteria Met

- ✅ Compiles cleanly on Windows with MinGW
- ✅ All search algorithms working correctly
- ✅ Statistics match server output exactly
- ✅ Reports formatted identically to server
- ✅ Best model selection working
- ✅ Confusion matrices extract real values
- ✅ No heap corruption or memory errors
- ✅ Model switching works smoothly
- ⏳ Test data confusion matrices (verification in progress)

---

**Last Updated**: October 17, 2025  
**Status**: Production-ready for training data analysis  
**Next**: Verify test data confusion matrix support

---

*This document synthesizes months of development work into a reproducible guide. The key is following OCCAM's existing patterns rather than trying to impose external frameworks.*