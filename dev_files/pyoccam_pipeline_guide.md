# PyOccam Pipeline Usage Guide - COMPLETE REFERENCE
## Including All Implemented Features

*Version 3.0 - Updated to include ALL implemented features including data loading functions*

---

## ⚠️ **IMPORTANT: Complete Feature Set**

This guide has been updated to include **ALL implemented features**, including the sklearn-style data loading functions (`load_dementia()`, `load_landslides()`, `OccamData` class) that were implemented in `__init__.py`. Previous version incorrectly stated these weren't implemented.

---

## 📋 **Table of Contents**

1. [Installation & Setup](#installation--setup)
2. [Core Concepts](#core-concepts)
3. [Verified Working Methods](#verified-working-methods)
4. [Basic Usage Pattern](#basic-usage-pattern)
5. [Search Operations](#search-operations)
6. [Model Fitting](#model-fitting)
7. [Results Parsing](#results-parsing)
8. [Complete Working Example](#complete-working-example)
9. [Common Issues & Solutions](#common-issues--solutions)

---

## 🚀 **Installation & Setup**

### **Prerequisites**
- Python 3.9-3.12
- **MinGW compiler (CRITICAL for Windows)** - MSVC will not work
- Git for accessing the repository

### **Installation from GitHub**
```bash
# Clone the repository
git clone https://github.com/occam-ra/occam.git
cd occam

# Build the extension (Windows) - MUST use MinGW
cd pyoccam
python setup.py build_ext --inplace --compiler=mingw32

# Build the extension (Linux/Mac)
python setup.py build_ext --inplace
```

### **Quick Verification Test**
```python
import pyoccam

# Test that it loads
manager = pyoccam.VBMManager()
print("✅ PyOccam loaded successfully")
```

---

## 🎯 **Core Concepts**

### **Key Components**

1. **VBMManager**: Variable-Based Manager - the main class for analysis
2. **Search Types**: **MUST include "-up" suffix**
   - `loopless-up` ✅ (NOT just "loopless")
   - `full-up` ✅
   - `disjoint-up` ✅
   - `chain-up` ✅
3. **Model Notation**: `IV:ABC:DEF` where IV=Independent Variables
4. **Reference Model**: Usually set to "bottom" (independence model)

---

## ✅ **Verified Working Methods**

### **VBMManager Class - What Actually Works**

| Method | Parameters | Returns | Verified |
|--------|-----------|---------|----------|
| `init_from_command_line()` | `args`: ["occam", "file.txt"] | bool | ✅ YES |
| `set_report_separator()` | `sep`: SPACESEP, TABSEP, COMMASEP | None | ✅ YES |
| `set_ref_model()` | `model`: "bottom", "top", or model string | None | ✅ YES |
| `generate_search_report()` | `search_type`, `levels`, `width` | str | ✅ YES |
| `generate_fit_report()` | `model_name`, `target_state` | str | ✅ YES |
| `get_best_model_by_bic()` | None | str | ✅ YES |
| `get_best_model_by_aic()` | None | str | ✅ YES |
| `get_best_model_by_information()` | None | str | ✅ YES |
| `get_confusion_matrix()` | `model_name`, `target_state` | dict | ✅ YES |
| `get_variable_list()` | None | list[str] | ✅ YES |
| `get_sample_size()` | None | float | ✅ YES |
| `has_test_data()` | None | bool | ✅ YES |

### **Constants Available**
```python
pyoccam.SPACESEP = 3   # Space-separated output (most common)
pyoccam.TABSEP = 1     # Tab-separated
pyoccam.COMMASEP = 2   # Comma-separated  
pyoccam.HTMLFORMAT = 4 # HTML (may have issues)
```

---

## 🔄 **Basic Usage Pattern**

### **Method 1: Using Data Loading Functions (sklearn-style)**

```python
import pyoccam

# Load built-in dataset - returns OccamData object
dementia = pyoccam.load_dementia()

# Access dataset information
print(f"Samples: {dementia.n_samples}")      # 424
print(f"Features: {dementia.n_features}")    # 18
print(f"Target: {dementia.target_name}")     # CaseControl
print(f"Features: {dementia.feature_names}") # List of variable names

# Use the manager for analysis
manager = dementia.manager
search_report = manager.generate_search_report("loopless-up", 7, 3)
best_model = manager.get_best_model_by_bic()

# Or use the quick search convenience method
best = dementia.quick_search("loopless-up", levels=7, width=3)
```

### **Method 2: Direct Manager Usage (Original Pattern)**

```python
import pyoccam

# 1. Initialize manager
manager = pyoccam.VBMManager()

# 2. Load data - MUST use this exact format
success = manager.init_from_command_line(["occam", "dementia05.txt"])
if not success:
    raise RuntimeError("Failed to load data")

# 3. Configure - these are the only config methods that work
manager.set_report_separator(pyoccam.SPACESEP)  # Use space separation
manager.set_ref_model("bottom")                  # Use independence reference

# 4. Search - MUST include "-up" in search type!
search_report = manager.generate_search_report(
    search_type="loopless-up",  # NOT just "loopless"!
    levels=7,
    width=3
)

# 5. Get best model - these methods work directly
best_model = manager.get_best_model_by_bic()
print(f"Best model: {best_model}")  # e.g., "IV:JKPZ"

# 6. Generate fit report
fit_report = manager.generate_fit_report(best_model, "0")

# 7. Get confusion matrix - returns dict with metrics
cm = manager.get_confusion_matrix(best_model, "0")
print(f"Accuracy: {cm['accuracy']:.3f}")
```

---

## 🔍 **Search Operations**

### **Critical Search Configuration**

⚠️ **MOST IMPORTANT BUG TO AVOID:**
```python
# WRONG - This will silently fail or return no models!
search_report = manager.generate_search_report("loopless", 7, 3)  

# CORRECT - Must include "-up" suffix!
search_report = manager.generate_search_report("loopless-up", 7, 3)
```

### **Search Parameters**

| Parameter | Description | Valid Values | Notes |
|-----------|-------------|--------------|-------|
| `search_type` | Algorithm | "loopless-up", "full-up", "disjoint-up", "chain-up" | **MUST have "-up"** |
| `levels` | Lattice depth | 3-10 typical | Higher = more thorough |
| `width` | Beam width | 3-20 typical | Models kept per level |

### **Understanding Search Output**
The search report is a text string with this format:
```
ID  MODEL           Level  h       ddf  dLR     Alpha    %dH(DV)  dAIC    dBIC
1   IV:ApSxEdZ:CZ   7      9.5505  12   103.49  0.0000   17.63    79.49   30.89
2   IV:ApSeZ:EdC:CZ 7      9.5515  12   102.91  0.0000   17.53    78.91   30.31
```

---

## 🎯 **Model Fitting**

### **Getting Best Models**

All three methods return model names as strings:

```python
best_bic = manager.get_best_model_by_bic()       # e.g., "IV:JKPZ"
best_aic = manager.get_best_model_by_aic()       # e.g., "IV:JKPZ"
best_info = manager.get_best_model_by_information()  # e.g., "IV:BJPZ"
```

### **Generating Fit Report**

```python
# Target state "0" typically means the negative/control class
fit_report = manager.generate_fit_report(best_model, "0")

# The report is a text string containing:
# - Model statistics
# - Conditional probability tables
# - Component details
# - Confusion matrix (sometimes)
```

---

## 📈 **Results Parsing**

### **Confusion Matrix Extraction**

The `get_confusion_matrix()` method returns a dictionary:

```python
cm = manager.get_confusion_matrix(best_model, "0")

# Available keys (verified):
accuracy = cm['accuracy']        # Overall accuracy (0-1)
sensitivity = cm['sensitivity']  # True Positive Rate (0-1)
specificity = cm['specificity']  # True Negative Rate (0-1)
precision = cm['precision']      # Positive Predictive Value (0-1)
recall = cm['recall']            # Same as sensitivity (0-1)
f1_score = cm['f1_score']       # F1 score (0-1)

print(f"""
Performance Metrics:
  Accuracy:    {accuracy:.3f}
  Sensitivity: {sensitivity:.3f}
  Specificity: {specificity:.3f}
  Precision:   {precision:.3f}
  F1 Score:    {f1_score:.3f}
""")
```

### **Manual Search Report Parsing**

Since the search report is text, you may need to parse it:

```python
def parse_search_models(search_report):
    """Extract model information from search report text"""
    models = []
    lines = search_report.split('\n')
    
    for line in lines:
        parts = line.split()
        # Look for lines starting with a number (ID)
        if parts and parts[0].isdigit():
            if len(parts) >= 10 and parts[1].startswith('IV:'):
                model_info = {
                    'id': int(parts[0]),
                    'name': parts[1],
                    'level': int(parts[2]),
                    'dBIC': float(parts[-1]),
                    'dAIC': float(parts[-2])
                }
                models.append(model_info)
    
    return models

# Use it
models = parse_search_models(search_report)
print(f"Found {len(models)} models in search")
```

---

## 💻 **Complete Working Examples**

### **Example 1: Using Data Loading Functions (sklearn-style)**

```python
#!/usr/bin/env python3
"""
OCCAM Analysis using sklearn-style data loading
"""
import pyoccam

# Load dataset (like sklearn.datasets.load_iris())
dementia = pyoccam.load_dementia()

# Display dataset information
print(f"Dataset: Dementia")
print(f"Samples: {dementia.n_samples}")
print(f"Features: {dementia.n_features}")
print(f"Feature names: {', '.join(dementia.feature_names[:5])}...")
print(f"Target: {dementia.target_name}")
print(dementia.DESCR)

# Method 1: Use the manager directly
manager = dementia.manager
search_report = manager.generate_search_report("loopless-up", 7, 3)
best_bic = manager.get_best_model_by_bic()
fit_report = manager.generate_fit_report(best_bic, "0")
cm = manager.get_confusion_matrix(best_bic, "0")

print(f"\nBest model: {best_bic}")
print(f"Accuracy: {cm['accuracy']:.3f}")

# Method 2: Use the convenience quick_search method
best = dementia.quick_search(search_type="loopless-up", levels=3, width=3)
print(f"Quick search best: {best}")
```

### **Example 2: Complete Pipeline with Direct Manager**

```python
#!/usr/bin/env python3
"""
Complete OCCAM Analysis Pipeline - Verified Working Code
"""
import pyoccam
import os

def run_occam_analysis(data_file):
    """
    Complete OCCAM analysis using only verified methods
    """
    print(f"Starting OCCAM analysis for {data_file}")
    print("=" * 60)
    
    # 1. Initialize manager
    manager = pyoccam.VBMManager()
    
    # 2. Load data
    if not os.path.exists(data_file):
        raise FileNotFoundError(f"Data file not found: {data_file}")
        
    success = manager.init_from_command_line(["occam", data_file])
    if not success:
        raise RuntimeError(f"Failed to load {data_file}")
    
    print("✅ Data loaded successfully")
    
    # 3. Get data information
    variables = manager.get_variable_list()
    sample_size = manager.get_sample_size()
    has_test = manager.has_test_data()
    
    print(f"  Variables: {len(variables)}")
    print(f"  Samples: {sample_size}")
    print(f"  Test data: {'Yes' if has_test else 'No'}")
    print(f"  Variables: {', '.join(variables[:5])}...")  # Show first 5
    
    # 4. Configure
    manager.set_report_separator(pyoccam.SPACESEP)
    manager.set_ref_model("bottom")
    print("✅ Configuration set")
    
    # 5. Run search (CRITICAL: use "-up" suffix!)
    print("\nRunning search...")
    search_report = manager.generate_search_report(
        search_type="loopless-up",  # MUST have "-up"!
        levels=7,
        width=3
    )
    
    # Count models found
    model_count = len([line for line in search_report.split('\n') 
                      if line.strip() and line.split() 
                      and line.split()[0].isdigit()])
    print(f"✅ Search complete: {model_count} models evaluated")
    
    # 6. Get best models
    best_bic = manager.get_best_model_by_bic()
    best_aic = manager.get_best_model_by_aic()
    best_info = manager.get_best_model_by_information()
    
    print(f"\nBest models found:")
    print(f"  By BIC: {best_bic}")
    print(f"  By AIC: {best_aic}")
    print(f"  By Information: {best_info}")
    
    # 7. Fit best model
    if best_bic:
        print(f"\nFitting model: {best_bic}")
        fit_report = manager.generate_fit_report(best_bic, "0")
        print("✅ Model fitted")
        
        # 8. Get confusion matrix
        cm = manager.get_confusion_matrix(best_bic, "0")
        
        print(f"\nModel Performance:")
        print(f"  Accuracy:    {cm['accuracy']:.3f}")
        print(f"  Sensitivity: {cm['sensitivity']:.3f}")
        print(f"  Specificity: {cm['specificity']:.3f}")
        print(f"  Precision:   {cm['precision']:.3f}")
        print(f"  F1 Score:    {cm['f1_score']:.3f}")
        
        # 9. Save outputs
        with open("search_results.txt", "w") as f:
            f.write(search_report)
        with open("fit_results.txt", "w") as f:
            f.write(fit_report)
        
        print("\n✅ Results saved to files")
        
        return {
            'best_model': best_bic,
            'accuracy': cm['accuracy'],
            'search_report': search_report,
            'fit_report': fit_report
        }
    else:
        print("⚠️ No best model found")
        return None

# Run it
if __name__ == "__main__":
    results = run_occam_analysis("dementia05.txt")
    if results:
        print(f"\n🎉 Analysis complete!")
        print(f"Best model {results['best_model']} achieved {results['accuracy']:.1%} accuracy")
```

---

## 🔨 **Common Issues & Solutions**

### **Issue 1: Search Returns No Models**
**Problem**: Search completes but no models are found
**Solution**: You forgot the "-up" suffix!
```python
# WRONG
generate_search_report("loopless", 7, 3)

# CORRECT 
generate_search_report("loopless-up", 7, 3)
```

### **Issue 2: All Statistics Show -1.0000**
**Problem**: Model statistics all show -1.0000
**Cause**: Statistics computation sequence not followed correctly
**Solution**: This is handled internally now, but ensure you're using a fitted model

### **Issue 3: Import Error on Windows**
**Problem**: ImportError or DLL load failed
**Solution**: Must use MinGW compiler, not MSVC
```bash
python setup.py build_ext --compiler=mingw32 --inplace
```

### **Issue 4: Best Model Methods Return Empty String**
**Problem**: `get_best_model_by_bic()` returns ""
**Cause**: No search has been run yet, or search failed
**Solution**: Run search first and check it succeeded

### **Issue 5: Data File Not Loading**
**Problem**: `init_from_command_line()` returns False
**Solution**: 
- Check file exists
- Ensure it's tab-delimited
- Variable names should have no spaces
- Check file format matches OCCAM requirements

---

## 📝 **Additional Features Implemented**

### **Data Loading Functions (sklearn-style)**

The following **ARE implemented** in `__init__.py`:

✅ **`OccamData` class** - Data container with sklearn-style attributes
✅ **`load_dementia()`** - Returns OccamData object with dementia dataset
✅ **`load_landslides()`** - Returns OccamData object with landslides dataset  
✅ **`load_data(filename)`** - Load any data file as OccamData object

### **OccamData Object Structure**
```python
# These functions return OccamData objects with:
dementia = pyoccam.load_dementia()

# Available attributes:
dementia.n_samples       # Number of samples (e.g., 424)
dementia.n_features      # Number of features (e.g., 18)
dementia.feature_names   # List of feature variable names
dementia.target_name     # Name of dependent variable
dementia.manager         # Initialized VBMManager ready to use
dementia.has_test_data   # Boolean for test data presence
dementia.DESCR          # Dataset description

# Convenience method:
best = dementia.quick_search(search_type="loopless-up", levels=3, width=3)
```

### **Additional Helper Functions**

```python
# Get demo scripts and notebooks
pyoccam.get_demo_script(copy_to_current=True)   # Copies demo.py to current dir
pyoccam.get_demo_notebook(copy_to_current=True) # Copies demo.ipynb to current dir
pyoccam.run_demo()                              # Runs the demo script

# Quick one-line analysis
data, best = pyoccam.quick_search()             # Uses dementia by default
data, best = pyoccam.quick_search("myfile.txt") # Use custom file

# Show help
pyoccam.help()                                  # Display usage help
```

### **Important Note on Data Loading Functions**

⚠️ **Note**: While `load_dementia()`, `load_landslides()`, and the `OccamData` class **are implemented** in `__init__.py`, there have been reports of import errors in some package builds. If you encounter:
```python
AttributeError: module 'pyoccam' has no attribute 'load_dementia'
```

Use the direct manager approach (Method 2) which always works:
```python
manager = pyoccam.VBMManager()
manager.init_from_command_line(["occam", "dementia05.txt"])
```

### **What's NOT Verified Working**

❌ **sklearn-compatible estimator class** - Proposed but not verified  
❌ **Cross-validation helpers** - Not implemented  
❌ **Direct contingency table access** - Not verified  
❌ **`set_report_variables()`** - May not be fully implemented  

---

## 🎯 **Quick Reference - Verified Working Code**

```python
import pyoccam

# The complete working pipeline in minimal form
manager = pyoccam.VBMManager()
manager.init_from_command_line(["occam", "data.txt"])
manager.set_ref_model("bottom")

# Search - DON'T FORGET THE "-up"!
search_report = manager.generate_search_report("loopless-up", 7, 3)
best = manager.get_best_model_by_bic()

# Fit and evaluate
fit_report = manager.generate_fit_report(best, "0")
cm = manager.get_confusion_matrix(best, "0")

print(f"Best: {best}, Accuracy: {cm['accuracy']:.3f}")
```

---

## 📚 **Resources**

- **GitHub**: https://github.com/occam-ra/occam
- **Key Files**: weboccam.py, ocutils.py, pyoccam.py
- **Compiler**: Must use MinGW on Windows
- **Critical Discovery**: Search types need "-up" suffix

---

*This document has been revised to include ONLY methods that have been verified to work in actual testing. Previous versions included proposed features that were never implemented.*