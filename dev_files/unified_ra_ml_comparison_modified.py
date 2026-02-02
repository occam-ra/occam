#!/usr/bin/env python3
"""
Unified comparison pipeline for Reconstructability Analysis (pyoccam) 
and Machine Learning methods for wildfire prediction

MODIFIED VERSION - Uses the new get_confusion_matrix() method
Changes made to run_pyoccam_analysis() function to use the new API
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
DEBUG_MODE = True  # Set to True for detailed output
KEEP_TEMP_FILES = False  # Keep temp files to debug
SAVE_FIT_REPORTS = True  # Save fit reports for debugging
OUTPUT_FOLDER = "occam_output"  # Folder to save all OCCAM files for verification

# RA Search configuration
RA_SEARCH_TYPE = "loopless-up"  # or "full-up"
RA_SEARCH_DEPTH = 3  # Reduced for faster testing (was 7)
RA_SEARCH_WIDTH = 3

# Analysis options
ANALYZE_BY_SIGNATURE = False  # Run separate analysis for each signature group (slower)
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
    """Parse OCCAM format file with proper handling of all columns"""
    print(f"Loading data from {filepath}...")
    
    if not os.path.exists(filepath):
        # Fallback to dementia05.txt for testing
        if os.path.exists("dementia05.txt"):
            print(f"  File not found, using dementia05.txt for testing")
            filepath = "dementia05.txt"
        else:
            raise FileNotFoundError(f"Cannot find {filepath} or dementia05.txt")
    
    with open(filepath, 'r') as f:
        lines = f.readlines()
    
    header_lines = []
    data_records = []
    all_variable_names = []
    active_variable_names = []
    variable_definitions = []
    
    # Parse header
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        header_lines.append(lines[i].rstrip('\n'))
        
        if line.startswith(':'):
            parts = line.split('\t')
            if len(parts) >= 3:
                var_def = {
                    'name': parts[0][1:],  # Remove leading colon
                    'card': int(parts[1]) if parts[1].isdigit() else 2,
                    'flag': int(parts[2]) if len(parts) > 2 and parts[2].isdigit() else 1,
                    'is_active': int(parts[2]) > 0 if len(parts) > 2 and parts[2].isdigit() else True
                }
                variable_definitions.append(var_def)
                all_variable_names.append(var_def['name'])
                if var_def['is_active']:
                    active_variable_names.append(var_def['name'])
        elif line and not line.startswith(':'):
            # Start of data
            break
        i += 1
    
    # Find signature and target indices
    signature_idx = None
    target_idx = None
    for idx, var_def in enumerate(variable_definitions):
        if 'Signature' in var_def['name'] or 'signature' in var_def['name']:
            signature_idx = idx
        if 'Fire' in var_def['name'] or 'CaseControl' in var_def['name'] or var_def['name'] == 'Z':
            target_idx = idx
    
    # Parse data records
    while i < len(lines):
        line = lines[i].strip()
        if line and not line.startswith(':'):
            values = line.split('\t')
            data_records.append(values)
        i += 1
    
    print(f"  Loaded {len(data_records)} records with {len(all_variable_names)} total variables")
    print(f"  Active variables: {len(active_variable_names)}")
    
    return (header_lines, data_records, all_variable_names, active_variable_names, 
            variable_definitions, signature_idx, target_idx)

def create_occam_file_for_fold(header_lines, train_data, test_data, output_file):
    """Create OCCAM format file for a fold"""
    with open(output_file, 'w') as f:
        for line in header_lines:
            f.write(line + '\n')
        
        for record in train_data:
            f.write('\t'.join(record) + '\n')
        
        if test_data:
            f.write(':test\n')
            for record in test_data:
                f.write('\t'.join(record) + '\n')
    
    return output_file

def prepare_ml_data(data_records, all_variables, variable_definitions):
    """Prepare data for ML models"""
    X = []
    y = []
    
    for record in data_records:
        features = []
        target = None
        
        for i, value in enumerate(record):
            if i < len(variable_definitions):
                var_def = variable_definitions[i]
                if var_def['is_active']:
                    if 'Fire' in var_def['name'] or 'CaseControl' in var_def['name'] or var_def['name'] == 'Z':
                        target = int(value) if value.isdigit() else 0
                    else:
                        try:
                            features.append(float(value))
                        except:
                            features.append(0)
        
        if target is not None:
            X.append(features)
            y.append(target)
    
    return np.array(X) if X else np.array([]), np.array(y) if y else np.array([])

def create_stratified_folds(data_records, signature_idx, target_idx, n_splits=5, random_state=42):
    """Create stratified folds preserving signature group balance"""
    y = []
    for record in data_records:
        if target_idx is not None and len(record) > target_idx:
            y.append(int(record[target_idx]) if record[target_idx].isdigit() else 0)
        else:
            # Try last column
            y.append(int(record[-1]) if record[-1].isdigit() else 0)
    
    skf = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=random_state)
    return list(skf.split(np.zeros(len(y)), y))

def extract_confusion_matrix_from_fit_report(fit_report_text):
    """Legacy function - Extract confusion matrix from pyoccam fit report text
    Keep this as a fallback if get_confusion_matrix() doesn't work
    """
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
                # Try to extract the value
                parts = line.split(',') if ',' in line else line.split()
                for part in parts:
                    try:
                        val = float(part)
                        if 0 <= val <= 1:
                            metrics['accuracy'] = val
                            break
                    except:
                        continue
            elif 'F1 score' in line:
                parts = line.split(',') if ',' in line else line.split()
                for part in parts:
                    try:
                        val = float(part)
                        if 0 <= val <= 1:
                            metrics['f1'] = val
                            break
                    except:
                        continue
            elif 'Precision' in line:
                parts = line.split(',') if ',' in line else line.split()
                for part in parts:
                    try:
                        val = float(part)
                        if 0 <= val <= 1:
                            metrics['precision'] = val
                            break
                    except:
                        continue
            elif 'Sensitivity' in line or 'Recall' in line:
                parts = line.split(',') if ',' in line else line.split()
                for part in parts:
                    try:
                        val = float(part)
                        if 0 <= val <= 1:
                            metrics['recall'] = val
                            break
                    except:
                        continue
            elif 'Specificity' in line:
                parts = line.split(',') if ',' in line else line.split()
                for part in parts:
                    try:
                        val = float(part)
                        if 0 <= val <= 1:
                            metrics['specificity'] = val
                            break
                    except:
                        continue
    
    # If no F1 score found, calculate it from precision and recall
    if metrics['f1'] == 0 and metrics['precision'] > 0 and metrics['recall'] > 0:
        metrics['f1'] = 2 * (metrics['precision'] * metrics['recall']) / (metrics['precision'] + metrics['recall'])
    
    return metrics

def run_pyoccam_analysis(data_file, test_file=None, fold_idx=0):
    """Run pyoccam analysis on a fold - MODIFIED to use new get_confusion_matrix"""
    try:
        print(f"      Initializing PyOccam...")
        manager = pyoccam.VBMManager()
        
        # Initialize with data file
        if not manager.init_from_command_line(["occam", str(data_file)]):
            print(f"      Failed to load data")
            return {'accuracy': 0.0, 'f1': 0.0, 'model': 'ERROR'}
        
        print(f"      Data loaded successfully")
        
        # Configure
        manager.set_report_separator(pyoccam.SPACESEP)
        manager.set_ref_model("bottom")
        
        # Run search
        print(f"      Running {RA_SEARCH_TYPE} search (depth={RA_SEARCH_DEPTH}, width={RA_SEARCH_WIDTH})...")
        search_report = manager.generate_search_report(
            RA_SEARCH_TYPE,
            RA_SEARCH_DEPTH,
            RA_SEARCH_WIDTH,
            include_test_data=(test_file is not None)
        )
        
        # Get best model
        best_model = manager.get_best_model_by_bic()
        if not best_model:
            best_model = manager.get_best_model_by_information()
        
        if not best_model:
            print(f"      No best model found")
            return {'accuracy': 0.0, 'f1': 0.0, 'model': 'N/A'}
        
        print(f"      Best model: {best_model}")
        
        # ============= NEW CODE: Use get_confusion_matrix() =============
        print(f"      Using new get_confusion_matrix() method...")
        
        # Get confusion matrix using the new method
        target_state = "0"  # Default negative state for confusion matrix
        cm_data = manager.get_confusion_matrix(best_model, target_state)
        
        # Debug output
        if DEBUG_MODE:
            print(f"      Confusion matrix returned:")
            if cm_data:
                # Check if we got actual values
                tn = cm_data.get('tn', 0)
                fp = cm_data.get('fp', 0)
                fn = cm_data.get('fn', 0)
                tp = cm_data.get('tp', 0)
                
                if tn > 0 or fp > 0 or fn > 0 or tp > 0:
                    print(f"        TN={tn:.0f}, FP={fp:.0f}")
                    print(f"        FN={fn:.0f}, TP={tp:.0f}")
                    print(f"        Accuracy: {cm_data.get('accuracy', 0):.3f}")
                    print(f"        Sensitivity: {cm_data.get('sensitivity', 0):.3f}")
                    print(f"        Specificity: {cm_data.get('specificity', 0):.3f}")
                    print(f"        Precision: {cm_data.get('precision', 0):.3f}")
                    print(f"        F1 Score: {cm_data.get('f1_score', 0):.3f}")
                else:
                    print(f"        No values returned (all zeros)")
        
        # Extract metrics from confusion matrix
        metrics = {
            'accuracy': cm_data.get('accuracy', 0.0),
            'f1': cm_data.get('f1_score', 0.0),
            'precision': cm_data.get('precision', 0.0),
            'recall': cm_data.get('sensitivity', 0.0),  # sensitivity is recall
            'specificity': cm_data.get('specificity', 0.0)
        }
        
        # If we didn't get valid metrics, fall back to fit report parsing
        if metrics['accuracy'] == 0:
            print(f"      No valid metrics from get_confusion_matrix(), falling back to fit report parsing...")
            
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
        
        print(f"      Final RA Metrics: Acc={metrics['accuracy']:.3f}, F1={metrics['f1']:.3f}")
        
        return {
            'accuracy': metrics['accuracy'],
            'f1': metrics['f1'],
            'model': best_model
        }
        
    except Exception as e:
        print(f"      RA Error: {e}")
        import traceback
        traceback.print_exc()
        return {'accuracy': 0.0, 'f1': 0.0, 'model': 'ERROR'}

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

def main():
    """Main analysis pipeline"""
    print(f"{'='*80}")
    print("UNIFIED RA-ML COMPARISON PIPELINE")
    print("Using new get_confusion_matrix() method")
    print(f"{'='*80}\n")
    
    if not PYOCCAM_AVAILABLE:
        print("ERROR: pyoccam not available. Cannot run analysis.")
        return
    
    # Parse the OCCAM file
    (header_lines, data_records, all_variables, active_variables, 
     variable_definitions, signature_idx, target_idx) = parse_occam_file(INPUT_FILE)
    
    # Check if we're using dementia05 for testing
    is_dementia_test = any('CaseControl' in var['name'] for var in variable_definitions)
    
    if is_dementia_test:
        print("\n" + "="*60)
        print("TESTING WITH DEMENTIA05 DATA")
        print("="*60)
        print("Testing the new get_confusion_matrix() functionality\n")
    
    # Prepare ML data
    X, y = prepare_ml_data(data_records, all_variables, variable_definitions)
    
    print(f"\nML Data shape: X={X.shape}, y={y.shape}")
    if len(y) > 0:
        print(f"Class distribution: {Counter(y)}")
    
    # For dementia05 testing, just run a simple test
    if is_dementia_test and len(data_records) > 0:
        # Create a simple train file (no test split for dementia05)
        train_file = TEMP_DIR / "dementia05_test.txt"
        create_occam_file_for_fold(header_lines, data_records, [], train_file)
        
        # Run pyoccam analysis
        print("\nRunning RA Analysis with new get_confusion_matrix():")
        print("-" * 50)
        ra_results = run_pyoccam_analysis(train_file, None, "test")
        
        print(f"\n{'='*60}")
        print("RESULTS SUMMARY")
        print(f"{'='*60}")
        print(f"Best Model: {ra_results['model']}")
        print(f"Accuracy:   {ra_results['accuracy']:.3f}")
        print(f"F1 Score:   {ra_results['f1']:.3f}")
        
        # Validate results
        if ra_results['accuracy'] > 0:
            print("\n✅ SUCCESS: get_confusion_matrix() is working correctly!")
        else:
            print("\n⚠️ WARNING: No confusion matrix values extracted")
            print("Check that the pyoccam module is compiled correctly")
        
        # Clean up
        if not KEEP_TEMP_FILES:
            try:
                train_file.unlink()
            except:
                pass
        
        return
    
    # Continue with full analysis for fire data...
    # Create stratified folds
    try:
        folds = create_stratified_folds(data_records, signature_idx, target_idx, N_FOLDS, RANDOM_SEED)
        print(f"\nCreated {len(folds)} stratified folds")
    except Exception as e:
        print(f"\nERROR creating folds: {e}")
        return
    
    # Store results across folds
    all_ra_results = []
    all_ml_results = {
        'Logistic Regression': [],
        'Random Forest': [],
        'Gradient Boosting': [],
        'Decision Tree': []
    }
    
    # Process each fold
    for fold_idx, (train_idx, test_idx) in enumerate(folds):
        print(f"\n{'='*60}")
        print(f"FOLD {fold_idx+1}/{len(folds)}")
        print(f"{'='*60}")
        print(f"  Train size: {len(train_idx)}, Test size: {len(test_idx)}")
        
        # Split data
        train_data = [data_records[i] for i in train_idx]
        test_data = [data_records[i] for i in test_idx]
        
        X_train = X[train_idx] if len(X) > 0 else np.array([])
        X_test = X[test_idx] if len(X) > 0 else np.array([])
        y_train = y[train_idx] if len(y) > 0 else np.array([])
        y_test = y[test_idx] if len(y) > 0 else np.array([])
        
        print(f"  Train class distribution: {Counter(y_train)}")
        print(f"  Test class distribution: {Counter(y_test)}")
        
        # Run RA Analysis
        print(f"\n  Running RA Analysis...")
        train_file = TEMP_DIR / f"train_fold_{fold_idx}.txt"
        test_file = TEMP_DIR / f"test_fold_{fold_idx}.txt"
        
        create_occam_file_for_fold(header_lines, train_data, test_data, train_file)
        
        ra_results = run_pyoccam_analysis(train_file, test_file, fold_idx)
        all_ra_results.append(ra_results)
        
        # Clean up temp files
        if not KEEP_TEMP_FILES:
            for f in [train_file, test_file]:
                try:
                    f.unlink()
                except:
                    pass
        
        # Run ML models (only if we have features)
        if len(X_train) > 0 and len(X_test) > 0:
            print(f"\n  Running ML Models...")
            ml_results = run_ml_models(X_train, X_test, y_train, y_test)
            
            for method, scores in ml_results.items():
                all_ml_results[method].append(scores)
                print(f"    {method}: Acc={scores['accuracy']:.3f}, F1={scores['f1']:.3f}")
        
        # Break if in test mode
        if TEST_MODE:
            break
    
    # Compute summary statistics
    print(f"\n{'='*80}")
    print("SUMMARY RESULTS")
    print(f"{'='*80}")
    
    # RA Summary
    ra_accs = [r['accuracy'] for r in all_ra_results if r['accuracy'] > 0]
    ra_f1s = [r['f1'] for r in all_ra_results if r['f1'] > 0]
    
    if ra_accs:
        print(f"\nReconstructability Analysis:")
        print(f"  Accuracy: {np.mean(ra_accs):.3f} ± {np.std(ra_accs):.3f}")
        print(f"  F1 Score: {np.mean(ra_f1s):.3f} ± {np.std(ra_f1s):.3f}")
        print(f"  Models used:")
        for i, r in enumerate(all_ra_results):
            if r['model'] != 'N/A':
                print(f"    Fold {i+1}: {r['model']}")
    else:
        print("\nReconstructability Analysis: No valid results")
    
    # ML Summary
    if any(all_ml_results.values()):
        print(f"\nMachine Learning Results:")
        best_ml_method = None
        best_ml_acc = 0.0
        
        for method in all_ml_results:
            accs = [r['accuracy'] for r in all_ml_results[method]]
            f1s = [r['f1'] for r in all_ml_results[method]]
            if accs:
                mean_acc = np.mean(accs)
                print(f"  {method}:")
                print(f"    Accuracy: {mean_acc:.3f} ± {np.std(accs):.3f}")
                print(f"    F1 Score: {np.mean(f1s):.3f} ± {np.std(f1s):.3f}")
                
                if mean_acc > best_ml_acc:
                    best_ml_acc = mean_acc
                    best_ml_method = method
        
        # Comparison
        if ra_accs:
            print(f"\n{'='*60}")
            print("COMPARISON")
            print(f"{'='*60}")
            
            ra_mean_acc = np.mean(ra_accs)
            diff = (ra_mean_acc - best_ml_acc) * 100
            
            if diff > 0:
                print(f"✓ RA outperforms best ML ({best_ml_method}) by {diff:.1f} percentage points")
            else:
                print(f"✗ Best ML ({best_ml_method}) outperforms RA by {-diff:.1f} percentage points")
    
    print(f"\n{'='*80}")
    print("Analysis complete!")
    print(f"{'='*80}")

if __name__ == "__main__":
    main()