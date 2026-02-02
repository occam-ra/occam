#!/usr/bin/env python3
"""
Unified comparison pipeline for Reconstructability Analysis (pyoccam) 
and Machine Learning methods for wildfire prediction

UPDATED VERSION - Uses new get_confusion_matrix() method directly
"""

import pandas as pd
import numpy as np
import os
import sys
import tempfile
import re
import time
import gc
import io
import contextlib
from pathlib import Path
from collections import Counter

try:
    import pyoccam
    PYOCCAM_AVAILABLE = True
    print(f"PyOccam {pyoccam.__version__} loaded successfully")
except ImportError:
    PYOCCAM_AVAILABLE = False
    print("Warning: pyoccam not found, will use fallback RA results")

from sklearn.model_selection import train_test_split, cross_val_score, StratifiedKFold
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.tree import DecisionTreeClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score, confusion_matrix
from sklearn.metrics import classification_report

# Add scipy for statistical tests
try:
    from scipy import stats
    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False
    print("Warning: scipy not found, statistical tests will be skipped")

# ===== CONFIGURATION =====
# Updated to use the new file with signatures included
INPUT_FILE = 'fire_data_split_all_signature_groups_nlcd_rebinned_sigs.txt'
RANDOM_SEED = 42

# FOLD CONTROL - Set to 1 for testing, 5 for full analysis
TEST_MODE = False  # Set to False for full 5-fold analysis
N_FOLDS = 1 if TEST_MODE else 5  # 1 fold for testing, 5 for full cross-validation

# Debug and output options
DEBUG_MODE = True  # Set to True for detailed output of confusion matrix
KEEP_TEMP_FILES = False  # Keep temp files to debug
SAVE_FIT_REPORTS = True  # Save fit reports for debugging
OUTPUT_FOLDER = "occam_output"  # Folder to save all OCCAM files for verification

# RA Search configuration - Using full-up as requested
RA_SEARCH_TYPE = "loopless-up"  # Change to full-up if needed
RA_SEARCH_DEPTH = 3  # Reduced for faster testing
RA_SEARCH_WIDTH = 3

# Analysis options
ANALYZE_BY_SIGNATURE = True  # Run separate analysis for each signature group
SHOW_FEATURE_IMPORTANCE = True  # Display feature importance from RF
SAVE_DETAILED_RESULTS = True  # Save CSV with detailed results

# Create output directories
TEMP_DIR = Path("temp_ra_files")
TEMP_DIR.mkdir(exist_ok=True)
OUTPUT_DIR = Path(OUTPUT_FOLDER)
OUTPUT_DIR.mkdir(exist_ok=True)

# Signature mapping
SIGNATURE_NAMES = {
    'A': 'Evergreen-dominated',
    'B': 'Mixed shrub-grass foothill',
    'C': 'Central Valley & foothills',
    'D': 'Northern Sierran Foothills',
    'E': 'Cold-desert shrublands'
}

def parse_occam_file(filepath):
    """Parse OCCAM format file with proper handling of all columns
    
    CRITICAL: Handles both comma-separated variable definitions (dementia05.txt style)
    and other OCCAM formats. Tracks all columns including ignored ones (flag=0).
    """
    print(f"Loading data from {filepath}...")
    
    if not os.path.exists(filepath):
        # Use dementia05.txt for testing if the fire data doesn't exist
        print(f"  File not found, using dementia05.txt for testing")
        filepath = 'dementia05.txt'
    
    with open(filepath, 'r') as f:
        lines = f.readlines()
    
    print(f"  Detected OCCAM format file")
    
    header_lines = []
    data_records = []
    all_variable_names = []  # ALL variables including ignored
    active_variable_names = []  # Only active variables
    variable_definitions = []
    in_data_section = False
    in_nominal_section = False
    
    for line in lines:
        line_raw = line.rstrip('\n')  # Keep tabs but remove newline
        line_stripped = line.strip()
        
        # Skip empty lines in header, but not in data
        if not line_stripped:
            if not in_data_section:
                continue
        
        # Skip comment lines
        if line_stripped.startswith('#'):
            continue
            
        # Check for section markers
        if line_stripped == ':nominal':
            in_nominal_section = True
            in_data_section = False
            header_lines.append(line_raw)
            continue
        elif line_stripped == ':data':
            in_data_section = True
            in_nominal_section = False
            header_lines.append(line_raw)
            continue
        elif line_stripped.startswith(':'):
            # Other directives like :no-frequency
            header_lines.append(line_raw)
            in_nominal_section = False
            continue
        
        # Parse variable definitions (COMMA-separated with possible tabs)
        if in_nominal_section:
            # Split by tab first to separate name from the rest
            tab_parts = line_raw.split('\t')
            if tab_parts and tab_parts[0]:
                # The first part contains name and the comma-separated values
                first_part = tab_parts[0].strip()
                # Now split by comma
                parts = [p.strip() for p in first_part.split(',')]
                
                if len(parts) >= 4:
                    var_name = parts[0]
                    cardinality = int(parts[1]) if parts[1].isdigit() else 2
                    flag = int(parts[2]) if parts[2].isdigit() else 0  # 0=ignore, 1=IV, 2=DV
                    abbreviation = parts[3]
                    
                    # Add to ALL variables list (for column position tracking)
                    all_variable_names.append(var_name)
                    
                    # Only add to active list if it's an IV or DV
                    if flag > 0:
                        active_variable_names.append(var_name)
                    
                    variable_definitions.append({
                        'name': var_name,
                        'cardinality': cardinality,
                        'flag': flag,
                        'abbreviation': abbreviation,
                        'is_active': flag > 0
                    })
                    
            header_lines.append(line_raw)
        
        # Parse data rows
        elif in_data_section:
            # Data rows are tab-separated
            values = line_raw.split('\t')
            if values and values[0] and not values[0].startswith('#'):
                data_records.append(values)
    
    # Find signature and target indices
    signature_idx = None
    target_idx = None
    for idx, var_def in enumerate(variable_definitions):
        if 'Signature' in var_def['name'] or 'signature' in var_def['name']:
            signature_idx = idx
        if 'Fire' in var_def['name'] or 'CaseControl' in var_def['name']:
            target_idx = idx
    
    print(f"  Loaded {len(data_records)} records with {len(all_variable_names)} total variables")
    print(f"  Active variables: {len(active_variable_names)}")
    if active_variable_names:
        print(f"  Variable list: {', '.join(active_variable_names[:10])}" + 
              (" ..." if len(active_variable_names) > 10 else ""))
    if signature_idx is not None:
        print(f"  Signature column at index: {signature_idx}")
    if target_idx is not None:
        print(f"  Target column at index: {target_idx} ({variable_definitions[target_idx]['name']})")
    
    return (header_lines, data_records, all_variable_names, active_variable_names, 
            variable_definitions, signature_idx, target_idx)

def create_occam_file_for_fold(header_lines, train_data, test_data, output_file):
    """Create OCCAM format file for a fold with test data
    
    Preserves the exact header format from the original file.
    """
    with open(output_file, 'w') as f:
        # Write header lines exactly as they were
        for line in header_lines:
            if isinstance(line, str):
                # Make sure line ends with newline
                if not line.endswith('\n'):
                    f.write(line + '\n')
                else:
                    f.write(line)
        
        # Write data section
        f.write(":data\n")
        for record in train_data:
            f.write('\t'.join(record) + '\n')
        
        # Write test data if provided
        if test_data:
            f.write(f":test {len(test_data)}\n")
            for record in test_data:
                f.write('\t'.join(record) + '\n')
    
    return output_file

def prepare_ml_data(data_records, all_variables, variable_definitions):
    """Prepare data for ML models
    
    Extracts features and target from data records based on variable definitions.
    Handles missing values represented as '.' in the data.
    """
    X = []
    y = []
    
    for record in data_records:
        features = []
        target = None
        
        for i, value in enumerate(record):
            if i < len(variable_definitions):
                var_def = variable_definitions[i]
                
                # Skip ignored variables (flag=0)
                if var_def['flag'] == 0:
                    continue
                    
                # Handle target variable (flag=2)
                if var_def['flag'] == 2:
                    if value and value != '.':
                        try:
                            target = int(value)
                        except:
                            target = None
                # Handle feature variables (flag=1)
                elif var_def['flag'] == 1:
                    if value and value != '.':
                        try:
                            features.append(float(value))
                        except:
                            features.append(0.0)  # Default for non-numeric
                    else:
                        features.append(0.0)  # Default for missing
        
        # Only add records with valid target
        if target is not None and len(features) > 0:
            X.append(features)
            y.append(target)
    
    return np.array(X), np.array(y)

def create_stratified_folds(data_records, signature_idx, target_idx, n_splits=5, random_state=42):
    """Create stratified folds preserving signature group balance"""
    y = []
    for record in data_records:
        if target_idx is not None and len(record) > target_idx:
            y.append(int(record[target_idx]))
        else:
            y.append(int(record[-1]))  # Assume last column is target
    
    skf = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=random_state)
    return list(skf.split(np.zeros(len(y)), y))

def extract_confusion_matrix_from_fit_report(fit_report_text):
    """Legacy function - Extract confusion matrix from pyoccam fit report text"""
    metrics = {
        'accuracy': 0.0,
        'f1': 0.0,
        'precision': 0.0,
        'recall': 0.0,
        'specificity': 0.0
    }
    
    if not fit_report_text:
        return metrics
    
    lines = fit_report_text.split('\n')
    
    # Look for Additional Statistics section
    in_stats = False
    for line in lines:
        if 'Additional Statistics' in line:
            in_stats = True
            continue
        
        if in_stats:
            if 'accuracy' in line.lower() or '%correct' in line:
                parts = line.split()
                if len(parts) >= 2:
                    try:
                        value = float(parts[-1])
                        if 0 <= value <= 1:
                            metrics['accuracy'] = value
                    except:
                        pass
            elif 'F1 score' in line:
                parts = line.split()
                if len(parts) >= 2:
                    try:
                        value = float(parts[-1])
                        if 0 <= value <= 1:
                            metrics['f1'] = value
                    except:
                        pass
            elif 'Precision' in line:
                parts = line.split()
                if len(parts) >= 2:
                    try:
                        value = float(parts[-1])
                        if 0 <= value <= 1:
                            metrics['precision'] = value
                    except:
                        pass
            elif 'Sensitivity' in line or 'Recall' in line:
                parts = line.split()
                if len(parts) >= 2:
                    try:
                        value = float(parts[-1])
                        if 0 <= value <= 1:
                            metrics['recall'] = value
                    except:
                        pass
            elif 'Specificity' in line:
                parts = line.split()
                if len(parts) >= 2:
                    try:
                        value = float(parts[-1])
                        if 0 <= value <= 1:
                            metrics['specificity'] = value
                    except:
                        pass
    
    return metrics

def run_pyoccam_analysis(data_file, test_file=None, fold_idx=0):
    """Run pyoccam analysis on a fold - UPDATED to use new get_confusion_matrix"""
    try:
        print(f"      Initializing PyOccam...")
        manager = pyoccam.VBMManager()
        
        # Initialize
        if not manager.init_from_command_line(["occam", str(data_file)]):
            print(f"      Failed to load data")
            return {'accuracy': 0.0, 'f1': 0.0, 'model': 'ERROR'}
        
        print(f"      Data loaded successfully")
        sample_size = manager.get_sample_size()
        print(f"      Sample size: {sample_size}")
        
        # Configure
        manager.set_report_separator(pyoccam.SPACESEP)
        manager.set_ref_model("bottom")
        
        # Run search
        print(f"      Running {RA_SEARCH_TYPE} search (depth={RA_SEARCH_DEPTH}, width={RA_SEARCH_WIDTH})...")
        search_report = manager.generate_search_report(
            RA_SEARCH_TYPE,
            RA_SEARCH_DEPTH,
            RA_SEARCH_WIDTH,
            include_test_data=False
        )
        
        # Get best model
        best_model = manager.get_best_model_by_bic()
        if not best_model:
            best_model = manager.get_best_model_by_information()
        
        if not best_model:
            print(f"      No best model found")
            return {'accuracy': 0.0, 'f1': 0.0, 'model': 'N/A'}
        
        print(f"      Best model: {best_model}")
        
        # Determine target state for confusion matrix
        # For dementia05, Z is the DV with states 0 and 1
        # Default/negative state should be "0"
        target_state = "0"
        
        # NEW: Try to get confusion matrix directly using the new method
        print(f"      Getting confusion matrix (target_state={target_state})...")
        cm_data = manager.get_confusion_matrix(best_model, target_state)
        
        # Debug output to see what we got
        if DEBUG_MODE or fold_idx == "test":
            print(f"\n      📊 Confusion Matrix Values:")
            if cm_data.get('tn', 0) > 0 or cm_data.get('tp', 0) > 0:
                print(f"        ┌────────────────────────────┐")
                print(f"        │         Predicted          │")
                print(f"        │     Negative    Positive   │")
                print(f"        ├────────────────────────────┤")
                print(f"        │ Actual Negative │ TN={cm_data.get('tn', 0):3.0f}  FP={cm_data.get('fp', 0):3.0f} │")
                print(f"        │        Positive │ FN={cm_data.get('fn', 0):3.0f}  TP={cm_data.get('tp', 0):3.0f} │")
                print(f"        └────────────────────────────┘")
                print(f"\n      📈 Performance Metrics:")
                print(f"        Accuracy:    {cm_data.get('accuracy', 0):.3f}")
                print(f"        Sensitivity: {cm_data.get('sensitivity', 0):.3f} (Recall/TPR)")
                print(f"        Specificity: {cm_data.get('specificity', 0):.3f} (TNR)")
                print(f"        Precision:   {cm_data.get('precision', 0):.3f} (PPV)")
                print(f"        F1 Score:    {cm_data.get('f1_score', 0):.3f}")
            else:
                print(f"        ⚠️ No confusion matrix values returned")
            
            # Check for any warnings or debug info
            if 'warning' in cm_data:
                print(f"        WARNING: {cm_data['warning']}")
            if 'debug_info' in cm_data:
                print(f"        DEBUG: {cm_data['debug_info']}")
        
        # Use the confusion matrix data if available
        metrics = {
            'accuracy': cm_data.get('accuracy', 0.0),
            'f1': cm_data.get('f1_score', 0.0),
            'precision': cm_data.get('precision', 0.0),
            'recall': cm_data.get('sensitivity', 0.0),
            'specificity': cm_data.get('specificity', 0.0)
        }
        
        # If we didn't get valid metrics from get_confusion_matrix, fall back to fit report parsing
        if metrics['accuracy'] == 0:
            print(f"      No data from get_confusion_matrix, trying fit report...")
            
            # Generate fit report
            fit_report = manager.generate_fit_report(best_model, target_state)
            
            # Save fit report if requested
            if SAVE_FIT_REPORTS:
                fit_file = OUTPUT_DIR / f"fit_fold_{fold_idx}.txt"
                with open(fit_file, 'w') as f:
                    f.write(fit_report)
                print(f"      Saved fit report to {fit_file}")
            
            # Extract metrics from fit report text
            metrics = extract_confusion_matrix_from_fit_report(fit_report)
        
        print(f"\n      ✅ Final Metrics: Acc={metrics['accuracy']:.3f}, F1={metrics['f1']:.3f}")
        
        return {
            'accuracy': metrics['accuracy'],
            'f1': metrics['f1'],
            'precision': metrics['precision'],
            'recall': metrics['recall'],
            'specificity': metrics['specificity'],
            'model': best_model
        }
        
    except Exception as e:
        print(f"      RA Error: {e}")
        import traceback
        traceback.print_exc()
        return {'accuracy': 0.0, 'f1': 0.0, 'precision': 0.0, 'recall': 0.0, 
                'specificity': 0.0, 'model': 'ERROR'}

def run_ml_models(X_train, X_test, y_train, y_test):
    """Run ML models on a fold"""
    results = {}
    
    # Logistic Regression
    lr = LogisticRegression(random_state=RANDOM_SEED, max_iter=1000, C=1.0)
    lr.fit(X_train, y_train)
    y_pred = lr.predict(X_test)
    results['Logistic Regression'] = {
        'accuracy': accuracy_score(y_test, y_pred),
        'f1': f1_score(y_test, y_pred, average='weighted')
    }
    
    # Random Forest
    rf = RandomForestClassifier(
        n_estimators=100,
        max_depth=10,
        min_samples_split=10,
        min_samples_leaf=5,
        random_state=RANDOM_SEED,
        n_jobs=-1
    )
    rf.fit(X_train, y_train)
    y_pred = rf.predict(X_test)
    results['Random Forest'] = {
        'accuracy': accuracy_score(y_test, y_pred),
        'f1': f1_score(y_test, y_pred, average='weighted')
    }
    
    # Gradient Boosting
    gb = GradientBoostingClassifier(
        n_estimators=100,
        max_depth=5,
        min_samples_split=10,
        min_samples_leaf=5,
        random_state=RANDOM_SEED
    )
    gb.fit(X_train, y_train)
    y_pred = gb.predict(X_test)
    results['Gradient Boosting'] = {
        'accuracy': accuracy_score(y_test, y_pred),
        'f1': f1_score(y_test, y_pred, average='weighted')
    }
    
    # Decision Tree
    dt = DecisionTreeClassifier(
        max_depth=8,
        min_samples_split=10,
        min_samples_leaf=5,
        random_state=RANDOM_SEED
    )
    dt.fit(X_train, y_train)
    y_pred = dt.predict(X_test)
    results['Decision Tree'] = {
        'accuracy': accuracy_score(y_test, y_pred),
        'f1': f1_score(y_test, y_pred, average='weighted')
    }
    
    return results

def extract_feature_importance(X, y, variable_definitions, veg_indices):
    """Extract and display feature importance from Random Forest"""
    
    print(f"\n{'='*80}")
    print("FEATURE IMPORTANCE ANALYSIS")
    print(f"{'='*80}")
    
    # Train RF on full dataset to get stable feature importances
    rf = RandomForestClassifier(
        n_estimators=200,
        max_depth=10,
        min_samples_split=10,
        min_samples_leaf=5,
        random_state=RANDOM_SEED,
        n_jobs=-1
    )
    
    rf.fit(X, y)
    importances = rf.feature_importances_
    
    # Get feature names
    feature_names = []
    for i, var_def in enumerate(variable_definitions):
        if var_def['is_active'] and not ('Fire' in var_def['name'] or 'CaseControl' in var_def['name']):
            feature_names.append(var_def['name'])
    
    # Sort by importance
    indices = np.argsort(importances)[::-1]
    
    print("\nTop 20 Most Important Features:")
    for i in range(min(20, len(indices))):
        idx = indices[i]
        if idx < len(feature_names):
            print(f"  {i+1:2d}. {feature_names[idx]:30s} {importances[idx]:.4f}")
    
    return feature_names, importances

def main():
    """Main analysis pipeline"""
    print(f"{'='*80}")
    print("UNIFIED RA-ML COMPARISON PIPELINE")
    print(f"{'='*80}\n")
    
    if not PYOCCAM_AVAILABLE:
        print("ERROR: pyoccam not available. Cannot run analysis.")
        return
    
    # Test with dementia05.txt if fire data doesn't exist
    INPUT_FILE_TEST = INPUT_FILE
    if not os.path.exists(INPUT_FILE):
        print(f"Note: {INPUT_FILE} not found")
        print(f"Using dementia05.txt for testing confusion matrix functionality")
        INPUT_FILE_TEST = "dementia05.txt"
    
    # Parse the OCCAM file
    (header_lines, data_records, all_variables, active_variables, 
     variable_definitions, signature_idx, target_idx) = parse_occam_file(INPUT_FILE_TEST)
    
    # Show what we parsed
    print(f"\nParsed {len(variable_definitions)} variables:")
    for i, var_def in enumerate(variable_definitions[:5]):  # Show first 5
        print(f"  {i}: {var_def['name']} (card={var_def['cardinality']}, flag={var_def['flag']}, active={var_def['is_active']})")
    if len(variable_definitions) > 5:
        print(f"  ... and {len(variable_definitions)-5} more")
    
    # Prepare ML data
    X, y = prepare_ml_data(data_records, all_variables, variable_definitions)
    
    print(f"\nML Data shape: X={X.shape}, y={y.shape}")
    if len(y) > 0:
        print(f"Class distribution: {Counter(y)}")
    
    # For testing with dementia05, run a simple analysis
    if INPUT_FILE_TEST == "dementia05.txt" and len(data_records) > 0:
        print("\n" + "="*60)
        print("TESTING WITH DEMENTIA05 DATA")
        print("="*60)
        
        # Create a simple train file
        train_file = TEMP_DIR / "dementia05_test.txt"
        create_occam_file_for_fold(header_lines, data_records, [], train_file)
        
        # Run pyoccam analysis
        print("\nTesting new get_confusion_matrix() method:")
        print("-" * 40)
        ra_results = run_pyoccam_analysis(train_file, None, "test")
        
        print(f"\n📊 Results Summary:")
        print(f"  Best Model: {ra_results['model']}")
        print(f"  Accuracy: {ra_results['accuracy']:.3f}")
        print(f"  F1 Score: {ra_results['f1']:.3f}")
        print(f"  Precision: {ra_results['precision']:.3f}")
        print(f"  Recall: {ra_results['recall']:.3f}")
        print(f"  Specificity: {ra_results['specificity']:.3f}")
        
        # Validate the results
        if ra_results['accuracy'] > 0:
            print("\n✅ SUCCESS: get_confusion_matrix() is working!")
            print("   The confusion matrix values are being extracted correctly.")
        else:
            print("\n⚠️ WARNING: No confusion matrix values extracted")
            print("   Check the debug output above for details")
        
        # Clean up
        if not KEEP_TEMP_FILES:
            try:
                train_file.unlink()
            except:
                pass
        
        print("\n" + "="*60)
        print("TEST COMPLETE")
        print("="*60)
        return
    
    # Continue with full analysis for fire data...
    print("\n" + "="*60)
    print("FULL ANALYSIS WITH FIRE DATA")
    print("="*60)
    
    # Create stratified folds
    try:
        folds = create_stratified_folds(data_records, signature_idx, target_idx, N_FOLDS, RANDOM_SEED)
        print(f"\nCreated {len(folds)} stratified folds")
    except Exception as e:
        print(f"\nERROR in creating cross-validation splits: {e}")
        return
    
    # [Rest of analysis code continues here for fire data...]
    
    print(f"\n{'='*80}")
    print("Analysis complete!")
    print(f"{'='*80}")

if __name__ == "__main__":
    main()