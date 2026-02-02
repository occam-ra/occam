# OCCAM Python Package - Complete Project Reference
*Last Updated: 2025-01-09 - Confusion Matrix Extraction Working!*

## 🎯 Current Status: ~85% Complete ✅

### 📚 **The Complete Journey**
1. **Started**: Manual string formatting, statistics showing -1.0000
2. **Discovery #1**: Found `"loopless"` should be `"loopless-up"` (critical fix!)
3. **Breakthrough #1**: Created `create_fitted_model()` helper to compute statistics
4. **Revelation #1**: OCCAM already has Report class that does all formatting!
5. **Discovery #2**: Model::getLevel() doesn't exist - track manually
6. **Fix #1**: Windows stdout redirection issues - use temp files
7. **Fix #2**: Unicode characters (≠) breaking Windows - use ASCII
8. **Discovery #3**: BIC/AIC need to be computed as differences from reference
9. **Fix #3**: Duplicate models in report - trust ModelCache for uniqueness
10. **Breakthrough #2**: Confusion matrix uses printf() → stdout (not captured)
11. **THE FIX**: Changed printf() to fprintf(fd, ...) in Report.cpp - WORKING! ✅

---

## 🎉 **MAJOR WIN: Confusion Matrix Extraction** (January 9, 2025)

### **The Problem (Months of Struggle)**
- Confusion matrices were printed to console but not captured in reports
- `get_confusion_matrix()` always returned zeros
- Text parsing from fit reports found nothing

### **The Root Cause**
```cpp
// In Report.cpp - the confusion matrix functions used printf()
void printConfusionMatrixCSV(...) {
    printf(",Actual,|,Rule\n");  // Goes to STDOUT - not captured!
    printf(",Z=0,|,TN=,%0.3f,FP=,%0.3f\n", tn, fp);
}

// But captureOutput() only reads from FILE*
output += captureOutput([](FILE* f) {
    report->printConditional_DV(f, ...);  // Captures fprintf(f, ...) only
});
```

### **The Solution (Simple & Clean!)**
Changed all confusion matrix functions from `printf()` to `fprintf(fd, ...)`:

**Files Modified:**
1. **Report.cpp** - 6 functions changed (~60 lines)
   - Added `fprintd(FILE* fd, double d)` helper
   - Changed `printConfusionMatrixCSV(FILE* fd, ...)` - added fd parameter
   - Changed `printConfusionMatrixStatsCSV(FILE* fd, ...)` - added fd parameter
   - Changed `printConfusionMatrixHTML(FILE* fd, ...)` - added fd parameter
   - Changed `printConfusionMatrixStatsHTML(FILE* fd, ...)` - added fd parameter
   - Changed `Report::printConfusionMatrix(FILE* fd, ...)` - added fd parameter

2. **Report.h** - 1 declaration changed
   - Added `FILE* fd` as first parameter to `printConfusionMatrix()`

3. **ReportPrintConditionalDV.cpp** - 4 small changes
   - Changed 3 error message `printf()` calls to `fprintf(fd, ...)`
   - Added `fd` as first parameter to `printConfusionMatrix()` call

**Total: ~65 lines across 3 files**

### **Why This Works**
```
BEFORE:
printConditional_DV(FILE* fd, ...) 
  → fprintf(fd, ...)  ✓ Captured
  → printConfusionMatrix(...)
      → printf(...)   ✗ Goes to stdout, NOT captured

AFTER:
printConditional_DV(FILE* fd, ...)
  → fprintf(fd, ...)  ✓ Captured  
  → printConfusionMatrix(fd, ...)
      → fprintf(fd, ...)  ✓ NOW CAPTURED!
```

### **Results**
```python
# BEFORE (always zeros):
cm = manager.get_confusion_matrix("IV:ApZ", "0")
# {'tn': 0.0, 'fp': 0.0, 'fn': 0.0, 'tp': 0.0, 'accuracy': 0.0}

# AFTER (real values!):
cm = manager.get_confusion_matrix("IV:ApZ", "0")
# {'tn': 179.0, 'fp': 42.0, 'fn': 98.0, 'tp': 105.0, 
#  'accuracy': 0.670, 'sensitivity': 0.517, 'specificity': 0.810,
#  'precision': 0.714, 'f1_score': 0.600}
```

**Perfect match with server output!** 🎊

---

## ✅ **What's Working Now (VERIFIED 2025-01-09)**

### **Core Functionality**
- ✅ Multi-level search with proper statistics computation
- ✅ BIC/AIC/Information calculations
- ✅ Best model identification  
- ✅ Search reports matching server format
- ✅ Fit reports with confusion matrices **with real values!**
- ✅ **Confusion matrix extraction returning actual TN/FP/FN/TP**
- ✅ **All performance metrics (accuracy, sensitivity, specificity, precision, F1)**
- ✅ Windows compilation without errors
- ✅ No duplicate models in output
- ✅ ASCII-only output (no Unicode issues)

### **API Methods That Work**
```python
import pyoccam

# Initialize
manager = pyoccam.VBMManager()
manager.init_from_command_line(["occam", "data.txt"])

# Configure
manager.set_report_separator(pyoccam.SPACESEP)
manager.set_report_variables("ID$I, Model, Level$I, h, ddf, Alpha, Inf, dAIC, dBIC")

# Search
search_report = manager.generate_search_report("loopless-up", 7, 3, False)

# Get best models
best_bic = manager.get_best_model_by_bic()  # Returns model name string
best_aic = manager.get_best_model_by_aic()
best_info = manager.get_best_model_by_information()

# Generate fit report
fit_report = manager.generate_fit_report(best_bic, "0")  # target_state="0"

# NEW: Get confusion matrix with REAL VALUES!
cm = manager.get_confusion_matrix(best_bic, "0")
print(f"Accuracy: {cm['accuracy']:.3f}")
print(f"TN={cm['tn']}, FP={cm['fp']}, FN={cm['fn']}, TP={cm['tp']}")
```

---

## 💡 **Critical Discoveries Along the Way**

### **1. The Search Type Bug** (First Big Fix)
```python
# WRONG (silent failure):
manager.set_search_type("loopless")

# CORRECT:
manager.set_search_type("loopless-up")
# Valid: loopless-up, full-up, disjoint-up, chain-up, etc.
```

### **2. The Statistics Computation Sequence**
```cpp
// The exact order matters!
void computeModelStatistics(Model* model) {
    manager.makeFitTable(model);
    manager.computeL2Statistics(model);
    manager.computeDependentStatistics(model);
    manager.computeInformationStatistics(model);
    manager.computePercentCorrect(model);
    
    // Calculate dAIC and dBIC (higher is better)
    Model* refModel = manager.getBottomRefModel();
    double daic = refModel->getAttribute("aic") - model->getAttribute("aic");
    double dbic = refModel->getAttribute("bic") - model->getAttribute("bic");
    model->setAttribute("daic", daic);
    model->setAttribute("dbic", dbic);
}
```

### **3. The Report Class Integration**
```cpp
// OCCAM already has a sophisticated Report class!
Report* report = new Report(&manager);
report->setSeparator(3);  // SPACESEP
report->setAttributes("ID$I, Model, Level$I, h, ddf, dLR, Alpha, Inf, %dH(DV), dAIC, dBIC");
for (Model* model : all_models) {
    report->addModel(model);
}
report->sort("information", Direction::Descending);  // Direction is enum!
report->print(temp_file);
```

### **4. Windows-Compatible Output Capture**
```cpp
// DON'T try to redirect stdout on Windows!
// Use temp files instead:
std::string captureOutput(std::function<void(FILE*)> func) {
    char tempname[L_tmpnam];
    tmpnam(tempname);
    FILE* temp = fopen(tempname, "w+");
    func(temp);
    rewind(temp);
    // Read contents
    fclose(temp);
    remove(tempname);
    return output;
}
```

### **5. The Confusion Matrix Printf Problem** (Latest Fix!)
```cpp
// PROBLEM: printf() goes to stdout, not the FILE*
printf("Confusion Matrix...\n");  // Lost!

// SOLUTION: Use fprintf(fd, ...) instead
fprintf(fd, "Confusion Matrix...\n");  // Captured!
```

---

## 🔧 **Build and Compilation**

### **Windows (MinGW Required)**
```bash
# Install MinGW32
# Set up environment

cd pyoccam
python setup.py clean --all
python setup.py build_ext --inplace --compiler=mingw32
```

### **Critical Compiler Flags**
```python
ext_modules = [
    Extension(
        'pyoccam',
        sources=[...],
        extra_compile_args=['-std=c++14', '-O2', '-w', '-DMS_WIN64'],
        extra_link_args=['-static'],  # Static linking
        libraries=[]  # Don't auto-link Python lib
    )
]
```

---

## 📊 **API Reference**

### **VBMManager Methods (Verified Working)**

#### **Initialization**
```python
manager = pyoccam.VBMManager()
success = manager.init_from_command_line(["occam", "datafile.txt"])
```

#### **Configuration**
```python
manager.set_report_separator(pyoccam.SPACESEP)  # or COMMASEP, TABSEP
manager.set_report_variables("ID$I, Model, h, ddf, Alpha, Inf, dAIC, dBIC")
manager.set_ref_model("bottom")  # or specific model name
```

#### **Search**
```python
search_report = manager.generate_search_report(
    search_type="loopless-up",  # Must include "-up" suffix
    levels=7,
    width=3,
    include_test_data=False
)
```

#### **Model Selection**
```python
best_bic = manager.get_best_model_by_bic()
best_aic = manager.get_best_model_by_aic()
best_info = manager.get_best_model_by_information()
```

#### **Fit Report**
```python
fit_report = manager.generate_fit_report(
    model_name="IV:ApZ:EdZ",
    target_state="0"  # For confusion matrix
)
```

#### **Confusion Matrix (NEW - WORKING!)**
```python
cm = manager.get_confusion_matrix("IV:ApZ", "0")
# Returns dict with:
# 'tn', 'fp', 'fn', 'tp' - raw confusion matrix values
# 'accuracy' - (TP+TN)/Total
# 'sensitivity' - TP/(TP+FN) - True Positive Rate / Recall
# 'specificity' - TN/(TN+FP) - True Negative Rate  
# 'precision' - TP/(TP+FP) - Positive Predictive Value
# 'npv' - TN/(TN+FN) - Negative Predictive Value
# 'f1_score' - Harmonic mean of precision and sensitivity
```

#### **Utility Methods**
```python
sample_size = manager.get_sample_size()
variables = manager.get_variable_list()  # Returns list of variable names
```

---

## 📝 **Code Patterns That Work**

### **Complete Analysis Pipeline**
```python
import pyoccam

# 1. Initialize
manager = pyoccam.VBMManager()
manager.init_from_command_line(["occam", "dementia05.txt"])

# 2. Configure
manager.set_report_separator(pyoccam.SPACESEP)
manager.set_report_variables("ID$I, Model, Level$I, h, ddf, Alpha, Inf, dAIC, dBIC")

# 3. Search
print("Running search...")
search_report = manager.generate_search_report("loopless-up", 7, 3, False)
print(search_report)

# 4. Get best model
best_model = manager.get_best_model_by_bic()
print(f"Best model: {best_model}")

# 5. Generate fit report
fit_report = manager.generate_fit_report(best_model, "0")
print(fit_report)

# 6. Get confusion matrix
cm = manager.get_confusion_matrix(best_model, "0")
print(f"\nConfusion Matrix Results:")
print(f"  Accuracy:    {cm['accuracy']:.3f}")
print(f"  Sensitivity: {cm['sensitivity']:.3f}")
print(f"  Specificity: {cm['specificity']:.3f}")
print(f"  Precision:   {cm['precision']:.3f}")
print(f"  F1 Score:    {cm['f1_score']:.3f}")
print(f"\nRaw Values:")
print(f"  TN={cm['tn']:.0f}, FP={cm['fp']:.0f}")
print(f"  FN={cm['fn']:.0f}, TP={cm['tp']:.0f}")
```

---

## ⚠️ **Known Issues and Limitations**

### **Still TODO**
- 🔧 Component-wise analysis with detailed statistics
- 🔧 Direct Table object access for contingency tables
- 🔧 Progress callbacks for long searches
- 🔧 Simplified wrapper API (hiding complexity)

### **API Limitations**
```python
# ❌ Don't use - these don't work:
manager.make_fit_table()  # Returns bool, not Table object
manager.get_fit_table()   # Doesn't exist

# ✅ Use instead:
fit_report = manager.generate_fit_report(model, "0")  # Text report
cm = manager.get_confusion_matrix(model, "0")  # Structured data
```

---

## 🎓 **Key Learnings**

### **OCCAM Architecture Understanding**
1. **SearchBase**: Generates children from one parent model
2. **VBMManager**: Orchestrates multi-level beam search
3. **Report**: Handles all output formatting (separate from manager)
4. **Model**: Stores structure and statistics
5. **Table**: Holds contingency/fit tables (internal use)

### **Statistics Flow**
```
makeModel() → makeFitTable() → computeL2Statistics() → 
computeDependentStatistics() → computeInformationStatistics() → 
computePercentCorrect()
```

### **Why fprintf() Not printf()**
- `printf()` → stdout → NOT captured by file redirection
- `fprintf(fd, ...)` → FILE* → captured by captureOutput()
- This is why stdout redirection was so problematic
- The fprintf solution is cleaner and more portable

---

## 📚 **References and Resources**

### **GitHub Repository**
- Main repo: https://github.com/occam-ra/occam
- Key files: `weboccam.py`, `ocutils.py`, `pyoccam.py`

### **Gold Standard Outputs**
- `server_search_output_dementia05_loopless.PDF` - Loopless search
- `server_search_output_dementia05_full-up.PDF` - Full-up search

### **Critical Source Files**
- `Report.cpp` - Report generation and formatting
- `ReportPrintConditionalDV.cpp` - Conditional probability and confusion matrices
- `VBMManager.cpp` - Core manager functionality
- `SearchBase.cpp` - Search algorithm base class
- `Model.cpp` - Model structure and statistics

---

## 🎉 **Success Metrics**

### **What We Achieved**
- ✅ Working multi-level beam search
- ✅ Proper statistics computation matching server output
- ✅ Report class integration for clean formatting
- ✅ Best model selection by BIC/AIC/Information
- ✅ **Real confusion matrix extraction with all metrics**
- ✅ Windows/MinGW compilation
- ✅ Jupyter notebook compatibility
- ✅ Clean Python API

### **Verification Tests**
```python
# Test 1: Basic search
manager.generate_search_report("loopless-up", 3, 3, False)
# ✅ Returns properly formatted report with statistics

# Test 2: Model selection  
best = manager.get_best_model_by_bic()
# ✅ Returns model name string

# Test 3: Confusion matrix
cm = manager.get_confusion_matrix(best, "0")
# ✅ Returns dict with TN=179, FP=42, FN=98, TP=105
# ✅ Accuracy=0.670, matching server output exactly!
```

---

## 🚀 **What's Next**

### **Future Enhancements (Priority Order)**
1. **Simplified API**: Create high-level wrapper functions
2. **Direct table access**: Expose Table objects for contingency tables
3. **Component analysis**: Detailed per-component statistics
4. **Progress callbacks**: For long-running searches
5. **Test data support**: Proper train/test split handling
6. **PyPI packaging**: Make pip-installable

### **Research Applications**
- Exploratory data analysis with reconstructability analysis
- Model comparison using information-theoretic criteria
- Predictive modeling with interpretable structures
- Integration with scikit-learn and pandas workflows

---

## 📖 **For Future AI Assistants**

### **If You're Continuing This Work:**

1. **The confusion matrix is NOW WORKING** - uses fprintf(fd, ...) not printf()
2. **Search types need "-up" suffix** - "loopless-up" not "loopless"
3. **Statistics must be computed in order** - see computeModelStatistics()
4. **Use Report class for formatting** - don't build strings manually
5. **Windows needs MinGW** - not MSVC, not standard g++
6. **No stdout redirection** - use temp files for capturing output
7. **Direction is an enum** - include Types.h, use Direction::Descending

### **Critical Files**
- `pyoccam_pybind11.cpp` - Python bindings (latest version)
- `Report.cpp` - Fixed confusion matrix functions
- `Report.h` - Updated function signatures
- `ReportPrintConditionalDV.cpp` - Updated function calls

### **Build Command**
```bash
python setup.py clean --all
python setup.py build_ext --inplace --compiler=mingw32
```

### **Test Command**
```bash
python test_confusion_matrix_debug.py  # Verify confusion matrix works
python -c "import pyoccam; print('✅ Import successful')"
```

---

## 🎊 **Final Status: Production Ready!**

**The OCCAM Python package is now ~85% complete and production-ready for:**
- Reconstructability analysis in Jupyter notebooks
- Integration with Python data science workflows
- Model comparison using information-theoretic criteria
- Predictive modeling with confusion matrix evaluation

**The remaining 15% consists of:**
- Nice-to-have features (progress callbacks, simplified API)
- Advanced features (component analysis, direct table access)
- Polish (better error messages, comprehensive tests)

**The core functionality is solid, verified, and ready for real research use!** 🎉

---

*Last Updated: January 9, 2025*  
*Status: Confusion Matrix Extraction WORKING ✅*  
*Next Milestone: PyPI Package Release*
