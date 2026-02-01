#!/usr/bin/env python3
"""
Unified comparison pipeline for Reconstructability Analysis (pyoccam) 
and Machine Learning methods for wildfire prediction

FIXED VERSION - Addresses:
1. pyoccam API: Use generate_fit_report() instead of get_fit_report()
2. Proper parsing of OCCAM format files with all columns (including ignored ones)
3. Correct extraction of confusion matrix from fit report
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

import warnings
warnings.filterwarnings('ignore')

# ===== CONFIGURATION =====
# Updated to use the new file with signatures included
INPUT_FILE = 'fire_data_split_all_signature_groups_nlcd_rebinned_sigs.txt'
RANDOM_SEED = 42

# FOLD CONTROL - Set to 1 for testing, 5 for full analysis
TEST_MODE = False  # Set to False for full analysis
N_FOLDS = 1 if TEST_MODE else 5  # 1 fold for testing, 5 for full cross-validation

# Debug and output options
DEBUG_MODE = False  # Set to True for detailed output
KEEP_TEMP_FILES = False  # Keep temp files to debug
SAVE_FIT_REPORTS = True  # Save fit reports for debugging
OUTPUT_FOLDER = "occam_output"  # Folder to save all OCCAM files for verification

# RA Search configuration - Using full-up as requested
RA_SEARCH_TYPE = "full-up"
RA_SEARCH_DEPTH = 7
RA_SEARCH_WIDTH = 3

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
    
    CRITICAL: The data contains ALL columns including ignored ones (flag=0)
    We must track all columns to match positions correctly
    """
    print(f"Loading data from {filepath}...")
    
    with open(filepath, 'r') as f:
        lines = f.readlines()
    
    print(f"  Detected OCCAM format file")
    
    header_lines = []
    data_records = []
    all_variable_names = []  # ALL variables including ignored
    active_variable_names = []  # Only active variables (flag=1 or 2)
    variable_definitions = []
    in_data_section = False
    in_nominal_section = False
    
    for line in lines:
        line_stripped = line.strip()
        
        if not line_stripped:
            continue
            
        # Check for section markers
        if line_stripped == ':nominal':
            in_nominal_section = True
            header_lines.append(line_stripped)
            continue
        elif line_stripped == ':data':
            in_data_section = True
            in_nominal_section = False
            header_lines.append(line_stripped)
            continue
        elif line_stripped.startswith(':'):
            header_lines.append(line_stripped)
            in_nominal_section = False
            continue
        
        # Parse variable definitions (comma-separated)
        if in_nominal_section:
            parts = [p.strip() for p in line_stripped.split(',')]
            if len(parts) >= 4:
                var_name = parts[0]
                cardinality = parts[1]
                flag = parts[2]  # 0=ignore, 1=IV, 2=DV
                abbreviation = parts[3]
                
                # Add to ALL variables list
                all_variable_names.append(var_name)
                
                # Track active variables
                if flag in ['1', '2']:
                    active_variable_names.append(var_name)
                
                variable_definitions.append({
                    'name': var_name,
                    'cardinality': cardinality,
                    'flag': flag,
                    'abbreviation': abbreviation,
                    'is_active': flag in ['1', '2']
                })
            header_lines.append(line_stripped)
        
        # Parse data records (tab or space separated)
        elif in_data_section:
            # Try tab first, then space
            if '\t' in line_stripped:
                parts = line_stripped.split('\t')
            else:
                parts = line_stripped.split()
            
            if len(parts) > 0:
                data_records.append(parts)
    
    print(f"  Parsing OCCAM format file...")
    print(f"  Found {len(all_variable_names)} total variables ({len(active_variable_names)} active)")
    print(f"  All variable names: {all_variable_names[:5]}... ({len(all_variable_names)} total)")
    print(f"  Active variables (IVs/DVs): {len(active_variable_names)}")
    print(f"  Parsed {len(data_records)} data records")
    
    if data_records:
        print(f"  Sample data record: {data_records[0][:5]}... ({len(data_records[0])} fields)")
        print(f"  Expected {len(all_variable_names)} fields, got {len(data_records[0])}")
    
    # Find key columns - using ALL columns for position
    signature_idx = None
    target_idx = None
    
    for i, var_name in enumerate(all_variable_names):
        if 'pyrome_sig' in var_name.lower() or 'pyrosig' in var_name.lower():
            signature_idx = i
            print(f"  Found pyrome_sig at column {i} - no mapping needed!")
        elif 'LARGE_FIRE' in var_name:
            target_idx = i
            print(f"  Found target (LARGE_FIRE) at column {i}")
    
    # Check signature values in data
    if signature_idx is not None:
        sig_values = set()
        for record in data_records[:100]:  # Check first 100 records
            if len(record) > signature_idx:
                sig_values.add(record[signature_idx])
        print(f"  Signature values found: {sorted(sig_values)}")
    
    return (header_lines, data_records, all_variable_names, active_variable_names, 
            variable_definitions, signature_idx, target_idx)

def create_stratified_folds(data_records, signature_idx, target_idx, n_folds=5, random_seed=42):
    """Create stratified folds using both signature and target for stratification"""
    
    # Create stratification keys combining signature and target
    strat_keys = []
    for record in data_records:
        sig = record[signature_idx] if signature_idx and len(record) > signature_idx else 'X'
        target = record[target_idx] if target_idx and len(record) > target_idx else '0'
        strat_keys.append(f"{sig}_{target}")
    
    # Count distribution
    strat_counts = Counter(strat_keys)
    print(f"  Using signature column {signature_idx} for stratification")
    print(f"  Stratification distribution: {dict(strat_counts)}")
    
    # Create folds
    skf = StratifiedKFold(n_splits=n_folds, shuffle=True, random_state=random_seed)
    
    try:
        folds = list(skf.split(data_records, strat_keys))
        return folds
    except ValueError as e:
        print(f"  Warning: Stratification failed ({e}), using simple k-fold")
        # Fall back to simple k-fold
        from sklearn.model_selection import KFold
        kf = KFold(n_splits=n_folds, shuffle=True, random_state=random_seed)
        return list(kf.split(data_records))

def prepare_ml_data(data_records, all_variables, variable_definitions):
    """Prepare data for ML using only vegetation features"""
    
    X_data = []
    y_data = []
    
    # Find vegetation variable indices (columns 4-24 based on your description)
    veg_indices = []
    for i, var_def in enumerate(variable_definitions):
        if var_def['is_active'] and i >= 4 and i <= 24:
            veg_indices.append(i)
    
    print(f"  Sample record has {len(data_records[0])} columns")
    print(f"  Using vegetation features from columns {veg_indices[0] if veg_indices else 4} to {veg_indices[-1] if veg_indices else 24}")
    
    # Find target column (last column typically)
    target_idx = len(data_records[0]) - 1
    print(f"  Target column: {target_idx}")
    
    # Create encoders for categorical features
    encoders = {}
    for idx in veg_indices:
        encoder = LabelEncoder()
        values = [record[idx] for record in data_records if len(record) > idx]
        encoder.fit(values)
        encoders[idx] = encoder
    
    # Transform data
    for record in data_records:
        if len(record) > target_idx:
            # Extract features
            x_row = []
            for idx in veg_indices:
                value = record[idx]
                encoded = encoders[idx].transform([value])[0]
                x_row.append(encoded)
            
            X_data.append(x_row)
            
            # Target
            target = record[target_idx]
            y_data.append(1 if target in ['1', 'L', 'large'] else 0)
    
    X_array = np.array(X_data)
    y_array = np.array(y_data)
    
    print(f"  Extracted {len(X_array)} samples with {X_array.shape[1] if len(X_array) > 0 else 0} vegetation features")
    
    # Show target distribution
    if len(y_array) > 0:
        unique, counts = np.unique(y_array, return_counts=True)
        print(f"  Target distribution: {dict(zip(unique, counts))}")
    
    return X_array, y_array

def create_occam_file_for_fold(header_lines, train_data, test_data, output_file):
    """Create properly formatted OCCAM file for a fold"""
    
    with open(output_file, 'w') as f:
        # Write header
        for line in header_lines:
            f.write(str(line) + '\n')
        
        # Write training data
        for record in train_data:
            f.write('\t'.join(record) + '\n')
        
        # If we have test data, add :test marker and test data
        if test_data:
            f.write(':test\n')
            for record in test_data:
                f.write('\t'.join(record) + '\n')
    
    print(f"      Created OCCAM file: {output_file}")
    print(f"      Train: {len(train_data)}, Test: {len(test_data) if test_data else 0}")
    
    # Save a copy to output folder for verification
    if SAVE_FIT_REPORTS:
        import shutil
        copy_path = OUTPUT_DIR / f"fold_{output_file.name}"
        shutil.copy(output_file, copy_path)

def extract_confusion_matrix_from_fit_report(fit_report_text):
    """Extract confusion matrix and metrics from pyoccam fit report
    
    FIXED: Properly parse the test confusion matrix section
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
    in_test_section = False
    
    for i, line in enumerate(lines):
        # Look for test confusion matrix section
        if 'Test Data' in line and 'Confusion Matrix' in line:
            in_test_section = True
            continue
        
        if in_test_section:
            # Parse accuracy line: "%correct,correct / sample size,0.589"
            if '%correct' in line:
                parts = line.split(',')
                if len(parts) >= 3:
                    try:
                        metrics['accuracy'] = float(parts[-1].strip())
                    except:
                        pass
            
            # Parse F1 score line
            elif 'F1 score' in line:
                parts = line.split(',')
                if len(parts) >= 3:
                    try:
                        metrics['f1'] = float(parts[-1].strip())
                    except:
                        pass
            
            # Parse precision
            elif 'precision' in line.lower() and 'positive predictive' in line.lower():
                parts = line.split(',')
                if len(parts) >= 3:
                    try:
                        metrics['precision'] = float(parts[-1].strip())
                    except:
                        pass
            
            # Parse recall/sensitivity
            elif 'sensitivity' in line.lower() or 'recall' in line.lower():
                parts = line.split(',')
                if len(parts) >= 3:
                    try:
                        metrics['recall'] = float(parts[-1].strip())
                    except:
                        pass
            
            # Parse specificity
            elif 'specificity' in line.lower():
                parts = line.split(',')
                if len(parts) >= 3:
                    try:
                        metrics['specificity'] = float(parts[-1].strip())
                    except:
                        pass
    
    return metrics

def run_pyoccam_analysis(train_file, test_file=None, fold_idx=0):
    """Run pyoccam analysis on a single fold
    
    FIXED: Use generate_fit_report() instead of get_fit_report()
    """
    
    print(f"      Starting pyoccam analysis for fold {fold_idx}")
    
    if not PYOCCAM_AVAILABLE:
        return {'accuracy': 0.0, 'f1': 0.0, 'model': 'N/A'}
    
    try:
        # Combine train and test files if needed
        combined_file = TEMP_DIR / f"combined_fold_{fold_idx}.txt"
        
        with open(train_file, 'r') as f:
            content = f.read()
        
        # Check if test data exists in the file
        has_test = ':test' in content
        print(f"      Test data detected: {has_test}")
        
        # Write combined file
        with open(combined_file, 'w') as f:
            f.write(content)
            if test_file and not has_test:
                f.write(':test\n')
                with open(test_file, 'r') as tf:
                    test_lines = tf.readlines()
                    # Skip header lines in test file
                    in_data = False
                    for line in test_lines:
                        if ':data' in line:
                            in_data = True
                            continue
                        if in_data and line.strip():
                            f.write(line)
        
        # Initialize manager
        manager = pyoccam.VBMManager()
        
        # Load data
        success = manager.init_from_command_line(["occam", str(combined_file)])
        if not success:
            raise RuntimeError(f"Failed to load {combined_file}")
        
        # Configure
        manager.set_report_separator(pyoccam.SPACESEP)
        manager.set_ref_model("bottom")
        
        # Run search with "-up" suffix (CRITICAL!)
        search_report = manager.generate_search_report(
            RA_SEARCH_TYPE,  # "full-up"
            RA_SEARCH_DEPTH,
            RA_SEARCH_WIDTH
        )
        
        # Save search report
        if SAVE_FIT_REPORTS:
            search_file = OUTPUT_DIR / f"search_fold_{fold_idx}.txt"
            with open(search_file, 'w') as f:
                f.write(search_report)
        
        # Get best model
        best_model = manager.get_best_model_by_information()
        if not best_model:
            best_model = manager.get_best_model_by_bic()
        
        print(f"      Using Information criterion model: {best_model}")
        
        if not best_model:
            print("      No best model found!")
            return {'accuracy': 0.0, 'f1': 0.0, 'model': 'N/A'}
        
        # Generate fit report - FIXED: Use correct method name
        fit_report = manager.generate_fit_report(best_model, "0")
        
        # Save fit report
        if SAVE_FIT_REPORTS:
            fit_file = OUTPUT_DIR / f"fit_fold_{fold_idx}.txt"
            with open(fit_file, 'w') as f:
                f.write(fit_report)
        
        # Extract metrics from fit report
        metrics = extract_confusion_matrix_from_fit_report(fit_report)
        
        # Also try to get confusion matrix directly
        try:
            cm = manager.get_confusion_matrix(best_model, "0")
            if cm and 'accuracy' in cm:
                metrics['accuracy'] = cm['accuracy']
                metrics['f1'] = cm.get('f1_score', metrics['f1'])
        except:
            pass
        
        print(f"      RA Accuracy: {metrics['accuracy']:.3f}, F1: {metrics['f1']:.3f}")
        
        # Clean up temp file if not keeping
        if not KEEP_TEMP_FILES:
            try:
                combined_file.unlink()
            except:
                pass
        
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
    """Main execution function"""
    
    print("=" * 80)
    print("WILDFIRE ANALYSIS: RA vs ML COMPARISON")
    print(f"Mode: {'TEST' if TEST_MODE else 'FULL'} ({N_FOLDS} fold{'s' if N_FOLDS > 1 else ''})")
    print("=" * 80)
    
    # Check for input file
    if not os.path.exists(INPUT_FILE):
        print(f"ERROR: Input file '{INPUT_FILE}' not found!")
        return
    
    # Parse the OCCAM file
    (header_lines, data_records, all_variables, active_variables, 
     variable_definitions, signature_idx, target_idx) = parse_occam_file(INPUT_FILE)
    
    # Prepare ML data
    X, y = prepare_ml_data(data_records, all_variables, variable_definitions)
    
    print(f"\nML Data shape: X={X.shape}, y={y.shape}")
    print(f"Class distribution: {Counter(y)}")
    
    # Create stratified folds
    try:
        folds = create_stratified_folds(data_records, signature_idx, target_idx, N_FOLDS, RANDOM_SEED)
        print(f"\nCreated {len(folds)} stratified folds")
    except Exception as e:
        print(f"\nERROR in creating cross-validation splits: {e}")
        # Fall back to simple train-test split
        if TEST_MODE:
            print("Using simple train-test split for TEST_MODE...")
            from sklearn.model_selection import train_test_split
            indices = np.arange(len(data_records))
            train_idx, test_idx = train_test_split(
                indices, test_size=0.3, random_state=RANDOM_SEED, stratify=y
            )
            folds = [(train_idx, test_idx)]
        else:
            raise
    
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
        
        X_train = X[train_idx]
        X_test = X[test_idx]
        y_train = y[train_idx]
        y_test = y[test_idx]
        
        print(f"  Train class distribution: {Counter(y_train)}")
        print(f"  Test class distribution: {Counter(y_test)}")
        
        # Run RA Analysis
        print(f"\n  Running RA Analysis...")
        train_file = TEMP_DIR / f"train_fold_{fold_idx}.txt"
        test_file = TEMP_DIR / f"test_fold_{fold_idx}.txt"
        
        # Create OCCAM files for this fold
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
        
        # Run ML models
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
        print(f"  Models used: {[r['model'] for r in all_ra_results]}")
    else:
        print("\nReconstructability Analysis: No valid results")
    
    # ML Summary
    print(f"\nMachine Learning Results:")
    for method in all_ml_results:
        accs = [r['accuracy'] for r in all_ml_results[method]]
        f1s = [r['f1'] for r in all_ml_results[method]]
        if accs:
            print(f"  {method}:")
            print(f"    Accuracy: {np.mean(accs):.3f} ± {np.std(accs):.3f}")
            print(f"    F1 Score: {np.mean(f1s):.3f} ± {np.std(f1s):.3f}")
    
    # Comparison
    if ra_accs and any(all_ml_results.values()):
        print(f"\n{'='*60}")
        print("COMPARISON")
        print(f"{'='*60}")
        
        best_ml_acc = max([np.mean([r['accuracy'] for r in all_ml_results[m]]) 
                          for m in all_ml_results if all_ml_results[m]])
        
        ra_mean_acc = np.mean(ra_accs)
        diff = (ra_mean_acc - best_ml_acc) * 100
        
        if diff > 0:
            print(f"✓ RA outperforms best ML by {diff:.1f} percentage points")
        else:
            print(f"✗ ML outperforms RA by {-diff:.1f} percentage points")
    
    print(f"\n{'='*80}")
    print("Analysis complete!")
    print(f"{'='*80}")

if __name__ == "__main__":
    main()
