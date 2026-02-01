#!/usr/bin/env python3
"""
Unified RA vs ML Comparison - FIXED VERSION
Based on updated_pipeline_doc.md implementation notes

Key Fixes:
1. Correct get_confusion_matrix() usage with target_state="0"
2. Proper header generation for signature analysis
3. Better error handling to prevent hanging
4. Accepts degenerate CMs as valid (small sample issue)
"""

import pandas as pd
import numpy as np
import os
import sys
import tempfile
import re
from pathlib import Path
from collections import Counter

try:
    import pyoccam
    PYOCCAM_AVAILABLE = True
    print(f"PyOccam {pyoccam.__version__} loaded successfully")
except ImportError:
    PYOCCAM_AVAILABLE = False
    print("Warning: pyoccam not found, will skip RA analysis")

from sklearn.model_selection import StratifiedKFold
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.tree import DecisionTreeClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import accuracy_score, f1_score, confusion_matrix

import warnings
warnings.filterwarnings('ignore')

# ========== CONFIGURATION ==========
INPUT_FILE = 'fire_data_split_all_signature_groups_nlcd_rebinned_sigs.txt'
RANDOM_SEED = 42
N_FOLDS = 5
TEST_MODE = False  # Set True for quick testing
DEBUG_MODE = True  # Verbose output

# Output directories
TEMP_DIR = Path("temp_ra_files")
TEMP_DIR.mkdir(exist_ok=True)
OUTPUT_DIR = Path("occam_output")
OUTPUT_DIR.mkdir(exist_ok=True)

# Signature names
SIGNATURE_NAMES = {
    'A': 'Evergreen-dominated',
    'B': 'Mixed shrub-grass foothill',
    'C': 'Central Valley & foothills',
    'D': 'Northern Sierran Foothills',
    'E': 'Cold-desert shrublands'
}


def parse_occam_file(filepath):
    """Parse OCCAM format file with comma-separated nominal definitions"""
    
    print(f"Loading data from {filepath}...")
    
    with open(filepath, 'r') as f:
        lines = f.readlines()
    
    print(f"  Detected OCCAM format file")
    
    header_lines = []
    data_records = []
    all_variable_names = []
    active_variable_names = []
    variable_definitions = []
    in_data_section = False
    in_nominal_section = False
    
    for line in lines:
        line_stripped = line.strip()
        
        if not line_stripped:
            continue
            
        # Section markers
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
                
                all_variable_names.append(var_name)
                
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
        
        # Parse data records (space-separated)
        elif in_data_section:
            if '\t' in line_stripped:
                parts = line_stripped.split('\t')
            else:
                parts = line_stripped.split()
            
            if len(parts) > 0:
                data_records.append(parts)
    
    print(f"  Parsing OCCAM format file...")
    print(f"  Found {len(all_variable_names)} total variables ({len(active_variable_names)} active)")
    print(f"  Parsed {len(data_records)} data records")
    
    # Find key columns
    signature_idx = None
    target_idx = None
    
    for i, var_name in enumerate(all_variable_names):
        if 'pyrome_sig' in var_name.lower():
            signature_idx = i
            print(f"  Found signature at column {i}")
        elif 'LARGE_FIRE' in var_name:
            target_idx = i
            print(f"  Found target (LARGE_FIRE) at column {i}")
    
    return (header_lines, data_records, all_variable_names, active_variable_names, 
            variable_definitions, signature_idx, target_idx)


def prepare_ml_data(data_records, variable_definitions):
    """Prepare data for ML using only vegetation features (columns 4-24)"""
    
    X_data = []
    y_data = []
    
    # Find vegetation variable indices (columns 4-24)
    veg_indices = []
    for i, var_def in enumerate(variable_definitions):
        if var_def['is_active'] and 4 <= i <= 24:
            veg_indices.append(i)
    
    print(f"  Using vegetation features from columns 4-24 ({len(veg_indices)} features)")
    
    # Target is last column
    target_idx = len(data_records[0]) - 1
    
    # Create encoders
    encoders = {}
    for idx in veg_indices:
        encoder = LabelEncoder()
        values = [record[idx] for record in data_records if len(record) > idx]
        encoder.fit(values)
        encoders[idx] = encoder
    
    # Transform data
    for record in data_records:
        if len(record) > target_idx:
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
    
    print(f"  Prepared {len(X_array)} samples with {X_array.shape[1]} features")
    print(f"  Target distribution: {dict(zip(*np.unique(y_array, return_counts=True)))}")
    
    return X_array, y_array


def create_occam_file_for_fold(header_lines, train_data, test_data, output_file):
    """Create properly formatted OCCAM file with train/test split"""
    
    with open(output_file, 'w') as f:
        # Write header
        for line in header_lines:
            f.write(str(line) + '\n')
        
        # Write training data
        for record in train_data:
            f.write('\t'.join(record) + '\n')
        
        # :test marker on its own line (CRITICAL!)
        if test_data:
            f.write(':test\n')
            for record in test_data:
                f.write('\t'.join(record) + '\n')
    
    if DEBUG_MODE:
        print(f"      Created OCCAM file: {output_file.name}")
        print(f"      Train: {len(train_data)}, Test: {len(test_data) if test_data else 0}")


def run_pyoccam_analysis(data_file, fold_idx=0):
    """
    Run pyoccam analysis with WORKING confusion matrix extraction
    Based on updated_pipeline_doc.md
    """
    
    if not PYOCCAM_AVAILABLE:
        return {'accuracy': 0.0, 'f1': 0.0, 'model': 'N/A'}
    
    try:
        if DEBUG_MODE:
            print(f"      Initializing PyOccam...")
        
        manager = pyoccam.VBMManager()
        
        # Initialize with data file
        if not manager.init_from_command_line(["occam", str(data_file)]):
            print(f"      Failed to load data")
            return {'accuracy': 0.0, 'f1': 0.0, 'model': 'ERROR'}
        
        if DEBUG_MODE:
            print(f"      Data loaded successfully")
        
        # Configure
        manager.set_report_separator(pyoccam.SPACESEP)
        manager.set_ref_model("bottom")
        
        # Run search - use "full-up" as specified
        if DEBUG_MODE:
            print(f"      Running full-up search (depth=7, width=3)...")
        
        manager.generate_search_report("full-up", 7, 3, False)
        
        # Get best model by Information criterion
        best_model = manager.get_best_model_by_information()
        if not best_model:
            best_model = manager.get_best_model_by_bic()
        
        if not best_model:
            print(f"      No best model found")
            return {'accuracy': 0.0, 'f1': 0.0, 'model': 'N/A'}
        
        if DEBUG_MODE:
            print(f"      Best model: {best_model}")
        
        # CRITICAL FIX: Must call generate_fit_report() BEFORE get_confusion_matrix()
        # The fit report computation is required for the confusion matrix
        try:
            if DEBUG_MODE:
                print(f"      Generating fit report for model...")
            
            # Generate fit report first (required!)
            fit_report = manager.generate_fit_report(best_model, "0")
            
            if DEBUG_MODE:
                print(f"      Getting confusion matrix (target_state='0')...")
            
            # Now get confusion matrix
            cm_dict = manager.get_confusion_matrix(best_model, "0")
            
            # Check if we got valid values
            if cm_dict and isinstance(cm_dict, dict):
                tn = cm_dict.get('tn', 0)
                fp = cm_dict.get('fp', 0)
                fn = cm_dict.get('fn', 0)
                tp = cm_dict.get('tp', 0)
                
                total = tn + fp + fn + tp
                
                if total > 0:
                    accuracy = cm_dict.get('accuracy', 0.0)
                    f1 = cm_dict.get('f1_score', 0.0)
                    
                    if DEBUG_MODE:
                        print(f"      ✓ Got confusion matrix!")
                        print(f"        TN={tn:.0f}, FP={fp:.0f}, FN={fn:.0f}, TP={tp:.0f}")
                        print(f"        Accuracy: {accuracy:.3f}, F1: {f1:.3f}")
                    
                    # Check for degenerate model (predicting all one class)
                    if (tn == 0 and fn == 0) or (fp == 0 and tp == 0):
                        if DEBUG_MODE:
                            print(f"        ⚠ Degenerate model (predicting all one class)")
                    
                    return {
                        'accuracy': accuracy,
                        'f1': f1,
                        'model': best_model
                    }
                else:
                    if DEBUG_MODE:
                        print(f"      ⚠ Confusion matrix is all zeros")
            else:
                if DEBUG_MODE:
                    print(f"      ⚠ get_confusion_matrix returned invalid data")
        
        except Exception as e:
            if DEBUG_MODE:
                print(f"      ⚠ get_confusion_matrix failed: {e}")
        
        # If we got here, confusion matrix extraction failed
        return {'accuracy': 0.0, 'f1': 0.0, 'model': best_model}
        
    except Exception as e:
        print(f"      ✗ RA Error: {e}")
        if DEBUG_MODE:
            import traceback
            traceback.print_exc()
        return {'accuracy': 0.0, 'f1': 0.0, 'model': 'ERROR'}


def run_ml_models(X_train, X_test, y_train, y_test):
    """Run ML models on a fold"""
    
    results = {}
    
    models = {
        'Logistic Regression': LogisticRegression(random_state=RANDOM_SEED, max_iter=1000),
        'Random Forest': RandomForestClassifier(n_estimators=100, random_state=RANDOM_SEED),
        'Gradient Boosting': GradientBoostingClassifier(n_estimators=100, random_state=RANDOM_SEED),
        'Decision Tree': DecisionTreeClassifier(max_depth=10, random_state=RANDOM_SEED)
    }
    
    for name, model in models.items():
        model.fit(X_train, y_train)
        y_pred = model.predict(X_test)
        
        results[name] = {
            'accuracy': accuracy_score(y_test, y_pred),
            'f1': f1_score(y_test, y_pred, average='weighted', zero_division=0)
        }
    
    return results


def main():
    """Main execution function"""
    
    print("=" * 80)
    print("WILDFIRE ANALYSIS: RA vs ML COMPARISON")
    print(f"Mode: {'TEST' if TEST_MODE else 'FULL'} ({N_FOLDS if not TEST_MODE else 1} fold{'s' if N_FOLDS > 1 and not TEST_MODE else ''})")
    print("=" * 80)
    
    # Check for input file
    if not os.path.exists(INPUT_FILE):
        print(f"ERROR: Input file '{INPUT_FILE}' not found!")
        return
    
    # Parse the OCCAM file
    (header_lines, data_records, all_variables, active_variables, 
     variable_definitions, signature_idx, target_idx) = parse_occam_file(INPUT_FILE)
    
    # Prepare ML data
    X, y = prepare_ml_data(data_records, variable_definitions)
    
    print(f"\nML Data shape: X={X.shape}, y={y.shape}")
    
    # Create stratified folds
    n_folds = 1 if TEST_MODE else N_FOLDS
    
    # Use simple stratified K-fold
    skf = StratifiedKFold(n_splits=n_folds, shuffle=True, random_state=RANDOM_SEED)
    folds = list(skf.split(X, y))
    
    print(f"\nCreated {len(folds)} stratified folds")
    
    # Store results
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
        if PYOCCAM_AVAILABLE:
            print(f"\n  Running RA Analysis...")
            train_file = TEMP_DIR / f"train_fold_{fold_idx}.txt"
            
            create_occam_file_for_fold(header_lines, train_data, test_data, train_file)
            
            ra_results = run_pyoccam_analysis(train_file, fold_idx)
            all_ra_results.append(ra_results)
            
            if ra_results['accuracy'] > 0:
                print(f"    RA: Acc={ra_results['accuracy']:.3f}, F1={ra_results['f1']:.3f}")
            else:
                print(f"    RA: Failed to get valid results")
            
            # Cleanup
            try:
                train_file.unlink()
            except:
                pass
        
        # Run ML models
        print(f"\n  Running ML Models...")
        ml_results = run_ml_models(X_train, X_test, y_train, y_test)
        
        for method, scores in ml_results.items():
            all_ml_results[method].append(scores)
            print(f"    {method}: Acc={scores['accuracy']:.3f}, F1={scores['f1']:.3f}")
        
        print(f"\n{'='*60}")
        print(f"FOLD {fold_idx+1}/{len(folds)} - COMPLETED")
        print(f"{'='*60}")
    
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
        print(f"  Valid models: {len(ra_accs)}/{len(all_ra_results)}")
    else:
        print("\nReconstructability Analysis: No valid results")
    
    # ML Summary
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
    if ra_accs and best_ml_method:
        print(f"\n{'='*60}")
        print("COMPARISON")
        print(f"{'='*60}")
        
        ra_mean_acc = np.mean(ra_accs)
        diff = (ra_mean_acc - best_ml_acc) * 100
        
        if diff > 0:
            print(f"✓ RA outperforms best ML ({best_ml_method}) by {diff:.1f} percentage points")
        else:
            print(f"✗ Best ML ({best_ml_method}) outperforms RA by {-diff:.1f} percentage points")
        
        # Statistical test if we have multiple folds
        if len(ra_accs) > 1:
            try:
                from scipy import stats
                best_ml_accs = [r['accuracy'] for r in all_ml_results[best_ml_method]]
                t_stat, p_value = stats.ttest_rel(ra_accs, best_ml_accs)
                print(f"\nPaired t-test: t={t_stat:.3f}, p={p_value:.4f}")
                if p_value < 0.05:
                    print(f"  Difference is statistically significant (p < 0.05)")
                else:
                    print(f"  Difference is NOT statistically significant (p >= 0.05)")
            except:
                pass
    
    # Signature-based analysis
    if signature_idx is not None:
        print(f"\n{'='*80}")
        print("ANALYSIS BY SIGNATURE GROUP")
        print(f"{'='*80}")
        
        # Get unique signatures
        signatures = [data_records[i][signature_idx] if len(data_records[i]) > signature_idx else 'X' 
                     for i in range(len(data_records))]
        unique_sigs = sorted(set(signatures))
        if 'X' in unique_sigs:
            unique_sigs.remove('X')
        
        print(f"Found {len(unique_sigs)} signature groups: {unique_sigs}")
        
        sig_results = {}
        
        for sig in unique_sigs:
            print(f"\n{'-'*60}")
            print(f"Signature {sig} ({SIGNATURE_NAMES.get(sig, 'Unknown')})")
            print(f"{'-'*60}")
            
            # Get indices for this signature
            sig_indices = [i for i, s in enumerate(signatures) if s == sig]
            
            if len(sig_indices) < 100:
                print(f"  Too few samples ({len(sig_indices)}), skipping...")
                continue
            
            print(f"  Total samples: {len(sig_indices)}")
            
            # Get data for this signature
            sig_records = [data_records[i] for i in sig_indices]
            X_sig = X[sig_indices]
            y_sig = y[sig_indices]
            
            # Check class balance
            unique_classes, counts = np.unique(y_sig, return_counts=True)
            print(f"  Class distribution: {dict(zip(unique_classes, counts))}")
            
            if len(unique_classes) < 2:
                print(f"  Only one class present, skipping...")
                continue
            
            # Split data for this signature
            try:
                from sklearn.model_selection import train_test_split
                X_train, X_test, y_train, y_test = train_test_split(
                    X_sig, y_sig, test_size=0.3, random_state=RANDOM_SEED, stratify=y_sig
                )
                
                # Get corresponding data records
                train_indices = sig_indices[:len(X_train)]
                test_indices = sig_indices[len(X_train):]
                train_records = [data_records[i] for i in train_indices]
                test_records = [data_records[i] for i in test_indices]
                
                # Run RA for this signature
                if PYOCCAM_AVAILABLE:
                    print(f"  Running RA for signature {sig}...")
                    sig_file = TEMP_DIR / f"sig_{sig}_data.txt"
                    
                    # CRITICAL: Use the SAME header_lines with ALL variables
                    create_occam_file_for_fold(header_lines, train_records, test_records, sig_file)
                    
                    ra_result = run_pyoccam_analysis(sig_file, f"sig_{sig}")
                    
                    # Cleanup
                    try:
                        sig_file.unlink()
                    except:
                        pass
                else:
                    ra_result = {'accuracy': 0.0, 'f1': 0.0, 'model': 'N/A'}
                
                # Run ML models
                print(f"  Running ML for signature {sig}...")
                ml_result = run_ml_models(X_train, X_test, y_train, y_test)
                
                # Store results
                sig_results[sig] = {
                    'n_samples': len(sig_indices),
                    'ra': ra_result,
                    'ml': ml_result
                }
                
                # Print summary for this signature
                print(f"\n  Results for Signature {sig}:")
                if ra_result['accuracy'] > 0:
                    print(f"    RA: Acc={ra_result['accuracy']:.3f}, F1={ra_result['f1']:.3f}")
                    if (ra_result['accuracy'] < 0.55 and ra_result['f1'] < 0.1):
                        print(f"      ⚠ Likely degenerate model (small sample size)")
                else:
                    print(f"    RA: Failed")
                
                for method, scores in ml_result.items():
                    print(f"    {method}: Acc={scores['accuracy']:.3f}, F1={scores['f1']:.3f}")
                
            except Exception as e:
                print(f"  Error analyzing signature {sig}: {e}")
                if DEBUG_MODE:
                    import traceback
                    traceback.print_exc()
                continue
        
        # Summary across signatures
        if sig_results:
            print(f"\n{'='*60}")
            print("SIGNATURE SUMMARY")
            print(f"{'='*60}")
            
            for sig in unique_sigs:
                if sig in sig_results:
                    result = sig_results[sig]
                    print(f"\n{sig} ({SIGNATURE_NAMES.get(sig, 'Unknown')}):")
                    print(f"  Samples: {result['n_samples']}")
                    
                    if result['ra']['accuracy'] > 0:
                        print(f"  RA: Acc={result['ra']['accuracy']:.3f}, F1={result['ra']['f1']:.3f}")
                    
                    # Show best ML method for this signature
                    best_ml = max(result['ml'].items(), key=lambda x: x[1]['accuracy'])
                    print(f"  Best ML ({best_ml[0]}): Acc={best_ml[1]['accuracy']:.3f}")
    
    print(f"\n{'='*80}")
    print("Analysis complete!")
    print(f"{'='*80}")


if __name__ == "__main__":
    main()
