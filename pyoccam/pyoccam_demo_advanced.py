#!/usr/bin/env python
"""
PyOccam Advanced Demo
=====================

This script demonstrates advanced PyOccam features including:
1. CSV conversion with train/test splits
2. Model selection strategies comparison
3. Sklearn pipeline integration
4. Batch processing patterns

For basic usage, see pyoccam_demo.py
"""

import pyoccam
print(f"PyOccam {pyoccam.__version__} - Advanced Demo")
print("=" * 70)

# ============================================================================
# PART 1: Working with CSV Data and Train/Test Splits
# ============================================================================

print("\n" + "=" * 70)
print("PART 1: CSV Conversion with Train/Test Split")
print("=" * 70)

# For this demo, we'll create a sample CSV file
# In practice, you'd use your own data file

import csv
import tempfile
import os

# Create sample data (simulating a GIS landslide dataset)
sample_data = [
    ["slope", "aspect", "elevation", "landcover", "landslide"],
    ["steep", "north", "high", "forest", "1"],
    ["gentle", "south", "low", "grass", "0"],
    ["steep", "east", "high", "bare", "1"],
    ["moderate", "west", "medium", "forest", "0"],
    ["steep", "north", "high", "bare", "1"],
    ["gentle", "south", "low", "urban", "0"],
    ["steep", "east", "medium", "forest", "1"],
    ["moderate", "north", "high", "grass", "0"],
    ["steep", "west", "high", "bare", "1"],
    ["gentle", "east", "low", "forest", "0"],
    ["steep", "south", "medium", "bare", "1"],
    ["moderate", "west", "low", "grass", "0"],
    ["steep", "north", "high", "forest", "1"],
    ["gentle", "south", "medium", "urban", "0"],
    ["steep", "east", "high", "bare", "1"],
    ["moderate", "north", "low", "grass", "0"],
    ["steep", "west", "medium", "forest", "1"],
    ["gentle", "east", "high", "urban", "0"],
    ["steep", "south", "high", "bare", "1"],
    ["moderate", "north", "medium", "grass", "0"],
] * 20  # Repeat to get more samples

# Write to temp file
temp_csv = os.path.join(tempfile.gettempdir(), "sample_landslide.csv")
with open(temp_csv, 'w', newline='') as f:
    writer = csv.writer(f)
    for row in sample_data:
        writer.writerow(row)

print(f"\nCreated sample CSV: {temp_csv}")
print(f"Total rows: {len(sample_data) - 1}")

# Convert WITH train/test split
output_file, data = pyoccam.make_occam_input_from_csv(
    temp_csv,
    test_split=0.2,      # 20% held out for testing
    random_state=42,     # Reproducible
    dv_column="landslide",
    verbose=True
)

print(f"\nData object: {data}")
print(f"Has test data: {data.has_test_data}")

# ============================================================================
# PART 2: Model Selection Strategies Comparison
# ============================================================================

print("\n" + "=" * 70)
print("PART 2: Comparing Model Selection Strategies")
print("=" * 70)

# Use the built-in dementia dataset for richer analysis
dementia = pyoccam.load_dementia()
manager = dementia.manager

# Run a comprehensive search
print("\nRunning search...")
report = manager.generate_search_report("loopless-up", levels=7, width=5)

# Get best models by different criteria
best_bic = manager.get_best_model_by_bic()
best_aic = manager.get_best_model_by_aic()
best_info = manager.get_best_model_by_information()

print("\nBest models by different criteria:")
print(f"  BIC (most conservative):    {best_bic}")
print(f"  AIC (moderate):             {best_aic}")
print(f"  Information (alpha<0.05):   {best_info}")

# Compare their confusion matrices
print("\nConfusion Matrix Comparison:")
print("-" * 60)

for name, model in [("BIC", best_bic), ("AIC", best_aic), ("Info", best_info)]:
    cm = manager.get_confusion_matrix(model, target_state="0")
    if cm.get('has_values', False):
        print(f"{name:5s} | {model:25s} | Acc={cm['train_accuracy']:.1%} | "
              f"Sens={cm['train_sensitivity']:.1%} | Spec={cm['train_specificity']:.1%}")

# ============================================================================
# PART 3: Sklearn Pipeline Integration
# ============================================================================

print("\n" + "=" * 70)
print("PART 3: Sklearn Pipeline Integration")
print("=" * 70)

try:
    from sklearn.base import BaseEstimator, ClassifierMixin
    from sklearn.model_selection import cross_val_score
    import numpy as np
    
    SKLEARN_AVAILABLE = True
except ImportError:
    print("sklearn not available - skipping pipeline demo")
    print("Install with: pip install scikit-learn")
    SKLEARN_AVAILABLE = False

if SKLEARN_AVAILABLE:
    
    class OccamClassifier(BaseEstimator, ClassifierMixin):
        """
        Sklearn-compatible wrapper for PyOccam models.
        
        This allows PyOccam to be used in sklearn pipelines, cross-validation,
        and model comparison workflows.
        
        Parameters:
            search_type: Type of search ("loopless-up", "full-up", etc.)
            levels: Search depth
            width: Beam width
            selection: Model selection criterion ("bic", "aic", "information")
        """
        
        def __init__(self, search_type="loopless-up", levels=5, width=3, 
                     selection="bic"):
            self.search_type = search_type
            self.levels = levels
            self.width = width
            self.selection = selection
            self.manager_ = None
            self.best_model_ = None
            self.classes_ = None
            
        def fit(self, X, y):
            """Fit the OCCAM model to training data."""
            # Convert numpy arrays to OCCAM format
            # This is a simplified version - real implementation would
            # need to handle the OCCAM file format properly
            
            # For demo, we'll use the dementia dataset directly
            self.manager_ = pyoccam.VBMManager()
            
            # In a real implementation, you'd:
            # 1. Write X, y to a temp OCCAM file
            # 2. Load it into manager
            # 3. Run search
            
            # For this demo, use dementia data
            data = pyoccam.load_dementia()
            self.manager_ = data.manager
            
            # Run search
            self.manager_.generate_search_report(
                self.search_type, self.levels, self.width
            )
            
            # Select best model
            if self.selection == "bic":
                self.best_model_ = self.manager_.get_best_model_by_bic()
            elif self.selection == "aic":
                self.best_model_ = self.manager_.get_best_model_by_aic()
            else:
                self.best_model_ = self.manager_.get_best_model_by_information()
            
            self.classes_ = np.array([0, 1])
            return self
        
        def predict(self, X):
            """Predict class labels."""
            # In real implementation, would use model for prediction
            # For demo, return dummy predictions
            return np.zeros(len(X), dtype=int)
        
        def score(self, X, y):
            """Return accuracy score."""
            if self.manager_ is None:
                return 0.0
            cm = self.manager_.get_confusion_matrix(self.best_model_, target_state="0")
            return cm.get('train_accuracy', 0.0)
    
    print("\nOccamClassifier example:")
    print("-" * 40)
    
    # Create classifier
    clf = OccamClassifier(search_type="loopless-up", levels=5, selection="bic")
    
    # Fit (uses dementia data internally for demo)
    clf.fit(None, None)
    
    print(f"Best model: {clf.best_model_}")
    print(f"Score: {clf.score(None, None):.1%}")
    
    print("\nNote: Full sklearn integration requires converting data between")
    print("numpy arrays and OCCAM format. See PRACTICAL_GUIDE.md for details.")

# ============================================================================
# PART 4: Batch Processing Pattern
# ============================================================================

print("\n" + "=" * 70)
print("PART 4: Batch Processing Pattern")
print("=" * 70)

# Demonstrate processing multiple datasets/configurations

datasets = [
    ("Dementia", pyoccam.load_dementia),
    ("Landslides", pyoccam.load_landslides),
]

search_configs = [
    ("loopless-up", 5, 3),
    ("full-up", 4, 3),
]

print("\nBatch results:")
print("-" * 80)
print(f"{'Dataset':<12} {'Search':<15} {'Best Model':<25} {'Accuracy':<10}")
print("-" * 80)

for ds_name, loader in datasets:
    try:
        data = loader()
        manager = data.manager
        
        for search_type, levels, width in search_configs:
            try:
                report = manager.generate_search_report(search_type, levels, width)
                best = manager.get_best_model_by_bic()
                cm = manager.get_confusion_matrix(best, target_state="0")
                acc = cm.get('train_accuracy', 0.0)
                
                print(f"{ds_name:<12} {search_type:<15} {best:<25} {acc:.1%}")
            except Exception as e:
                print(f"{ds_name:<12} {search_type:<15} ERROR: {e}")
                
    except Exception as e:
        print(f"{ds_name:<12} LOAD ERROR: {e}")

# ============================================================================
# PART 5: Command Line Usage Examples
# ============================================================================

print("\n" + "=" * 70)
print("PART 5: Command Line Usage")
print("=" * 70)

print("""
CSV conversion with train/test split from command line:

  # Basic conversion with 20% test split
  python -m pyoccam csv2occam mydata.csv --test-split 0.2

  # With exclusions and custom cardinality
  python -m pyoccam csv2occam mydata.csv \\
      --test-split 0.3 \\
      --random-state 42 \\
      --max-cardinality 25 \\
      --exclude "ID,x,y,OBJECTID" \\
      --dv target_column

  # Just convert, don't run search
  python -m pyoccam csv2occam mydata.csv --test-split 0.2 --no-search
""")

# ============================================================================
# Cleanup
# ============================================================================

# Remove temp files
try:
    os.remove(temp_csv)
    os.remove(output_file)
except:
    pass

print("\n" + "=" * 70)
print("Advanced Demo Complete!")
print("=" * 70)
print("\nFor more examples, see:")
print("  - PRACTICAL_GUIDE.md - Real-world tips from landslide/wildfire projects")
print("  - PyOccam_API_Reference.md - Complete API documentation")
print("  - pyoccam.help() - Quick reference")
