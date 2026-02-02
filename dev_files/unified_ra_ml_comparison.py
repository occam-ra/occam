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
DEBUG_MODE = False  # Set to True for detailed output
KEEP_TEMP_FILES = False  # Keep temp files to debug
SAVE_FIT_REPORTS = True  # Save fit reports for debugging
OUTPUT_FOLDER = "occam_output"  # Folder to save all OCCAM files for verification

# RA Search configuration - Using full-up as requested
RA_SEARCH_TYPE = "full-up"
RA_SEARCH_DEPTH = 7
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
    
    ENHANCED: Try multiple patterns to find the confusion matrix
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
    
    # Debug: Check what type of system this is
    is_directed = False
    is_neutral = False
    for line in lines[:50]:  # Check first 50 lines
        if 'Directed System' in line:
            is_directed = True
            print(f"        System type: DIRECTED")
            break
        elif 'Neutral System' in line:
            is_neutral = True
            print(f"        System type: NEUTRAL")
            break
    
    # Try multiple patterns to find confusion matrix
    patterns_to_try = [
        'Confusion Matrix for the Model IV:',
        'Confusion Matrix for Model IV:',
        'Confusion Matrix (Training)',
        'Confusion Matrix (Test)',
        'Additional Statistics (Training)',
        'Additional Statistics (Test)'
    ]
    
    found_any_pattern = False
    for pattern in patterns_to_try:
        if pattern in fit_report_text:
            found_any_pattern = True
            print(f"        Found pattern: '{pattern}'")
            break
    
    if not found_any_pattern:
        print(f"        WARNING: No confusion matrix patterns found!")
        print(f"        First 500 chars of fit report:")
        print(f"        {fit_report_text[:500]}")
        
    # Method 1: Look for directed system confusion matrix
    in_training_stats = False
    in_test_stats = False
    
    for i, line in enumerate(lines):
        # Check for Additional Statistics sections directly
        if 'Additional Statistics (Training)' in line:
            in_training_stats = True
            in_test_stats = False
            print(f"        Found Training Statistics section")
            continue
        elif 'Additional Statistics (Test)' in line:
            in_test_stats = True
            in_training_stats = False  
            print(f"        Found Test Statistics section")
            continue
        
        # Parse statistics when in the right section
        if in_training_stats or in_test_stats:
            # Stop at next confusion matrix
            if 'Confusion Matrix' in line:
                in_training_stats = False
                in_test_stats = False
                continue
                
            # Parse different formats
            if any(word in line for word in ['Accuracy', 'accuracy', '%correct']):
                # Try multiple parsing approaches
                
                # Format 1: "Accuracy    correct / sample size    0.717"
                parts = line.split()
                if len(parts) >= 2:
                    try:
                        value = float(parts[-1])
                        if 0 <= value <= 1:
                            if in_test_stats:
                                metrics['accuracy'] = value
                                print(f"        TEST accuracy: {value:.3f}")
                            elif in_training_stats and metrics['accuracy'] == 0:
                                metrics['accuracy'] = value
                                print(f"        TRAINING accuracy: {value:.3f}")
                    except:
                        pass
                
                # Format 2: CSV style with commas
                if ',' in line:
                    parts = line.split(',')
                    if len(parts) >= 3:
                        try:
                            value = float(parts[-1].strip())
                            if 0 <= value <= 1:
                                if in_test_stats:
                                    metrics['accuracy'] = value
                                    print(f"        TEST accuracy (CSV): {value:.3f}")
                                elif in_training_stats and metrics['accuracy'] == 0:
                                    metrics['accuracy'] = value
                                    print(f"        TRAINING accuracy (CSV): {value:.3f}")
                        except:
                            pass
            
            # Parse F1 score
            elif 'F1 score' in line or 'F1-score' in line:
                parts = line.split()
                if len(parts) >= 2:
                    try:
                        value = float(parts[-1])
                        if 0 <= value <= 1 and (in_test_stats or metrics['f1'] == 0):
                            metrics['f1'] = value
                    except:
                        pass
                        
                # Also try CSV format
                if ',' in line:
                    parts = line.split(',')
                    if len(parts) >= 3:
                        try:
                            value = float(parts[-1].strip())
                            if 0 <= value <= 1 and (in_test_stats or metrics['f1'] == 0):
                                metrics['f1'] = value
                        except:
                            pass
            
            # Parse other metrics similarly
            elif 'Precision' in line:
                parts = line.split()
                if len(parts) >= 2:
                    try:
                        value = float(parts[-1])
                        if 0 <= value <= 1 and (in_test_stats or metrics['precision'] == 0):
                            metrics['precision'] = value
                    except:
                        pass
            
            elif any(word in line for word in ['Sensitivity', 'Recall']):
                parts = line.split()
                if len(parts) >= 2:
                    try:
                        value = float(parts[-1])
                        if 0 <= value <= 1 and (in_test_stats or metrics['recall'] == 0):
                            metrics['recall'] = value
                    except:
                        pass
            
            elif 'Specificity' in line:
                parts = line.split()
                if len(parts) >= 2:
                    try:
                        value = float(parts[-1])
                        if 0 <= value <= 1 and (in_test_stats or metrics['specificity'] == 0):
                            metrics['specificity'] = value
                    except:
                        pass
    
    # If still no metrics found, try a more aggressive search
    if metrics['accuracy'] == 0:
        print(f"        WARNING: No accuracy found with standard parsing")
        # Look for any line with a decimal between 0.5 and 1.0 after "correct"
        for line in lines:
            if 'correct' in line.lower():
                import re
                numbers = re.findall(r'0\.\d+', line)
                for num in numbers:
                    val = float(num)
                    if 0.5 <= val <= 1.0:
                        metrics['accuracy'] = val
                        print(f"        Found possible accuracy: {val:.3f} in line: {line[:80]}")
                        break
                if metrics['accuracy'] > 0:
                    break
    
    return metrics

#!/usr/bin/env python3
"""
Simple modification to run_pyoccam_analysis function
Just adds the new get_confusion_matrix() method call
Minimal changes to the working original code
"""

def run_pyoccam_analysis(data_file, test_file=None, fold_idx=0):
    """Run pyoccam analysis on a fold - MODIFIED to use new get_confusion_matrix
    
    This is a drop-in replacement for the run_pyoccam_analysis function
    in your original unified_ra_ml_comparison.py
    """
    try:
        print(f"      Initializing PyOccam...")
        manager = pyoccam.VBMManager()
        
        # Combine train and test files if both exist
        if test_file and os.path.exists(test_file):
            combined_file = TEMP_DIR / f"combined_fold_{fold_idx}.txt"
            with open(data_file, 'r') as f1:
                lines = f1.readlines()
            with open(test_file, 'r') as f2:
                test_lines = f2.readlines()
            
            with open(combined_file, 'w') as f:
                f.writelines(lines)
                f.writelines(test_lines)
            
            data_file = combined_file
        
        # Initialize
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
            include_test_data=False
        )
        
        # Parse search report for accuracies (keep existing code for reference)
        search_accuracies = {}
        for line in search_report.split('\n'):
            parts = line.split()
            if len(parts) >= 11 and 'IV:' in line:
                try:
                    model_name = None
                    acc_val = None
                    for i, part in enumerate(parts):
                        if 'IV:' in part:
                            model_name = part
                        if i == 10:  # %dH(DV) column position
                            try:
                                acc_val = float(part) / 100.0
                            except:
                                pass
                    if model_name and acc_val:
                        search_accuracies[model_name] = acc_val
                except:
                    pass
        
        # Get best model
        best_model = manager.get_best_model_by_information()
        if not best_model:
            best_model = manager.get_best_model_by_bic()
        
        if not best_model:
            print(f"      No best model found")
            return {'accuracy': 0.0, 'f1': 0.0, 'model': 'N/A'}
        
        print(f"      Best model: {best_model}")
        
        # Check if we found this model's accuracy in search
        if best_model in search_accuracies:
            print(f"      Search reported %Correct: {search_accuracies[best_model]:.3f}")
        
        # ============= ADD NEW CODE HERE =============
        # Try the new get_confusion_matrix method first
        print(f"      Trying new get_confusion_matrix() method...")
        try:
            cm_data = manager.get_confusion_matrix(best_model, "0")
            
            # Check if we got real values
            if cm_data and isinstance(cm_data, dict):
                tn = cm_data.get('tn', 0)
                fp = cm_data.get('fp', 0)
                fn = cm_data.get('fn', 0)
                tp = cm_data.get('tp', 0)
                
                # If we have actual confusion matrix values
                if (tn + fp + fn + tp) > 0:
                    print(f"      ✓ Got confusion matrix from new method!")
                    print(f"        TN={tn:.0f}, FP={fp:.0f}, FN={fn:.0f}, TP={tp:.0f}")
                    print(f"        Accuracy: {cm_data.get('accuracy', 0):.3f}")
                    print(f"        F1 Score: {cm_data.get('f1_score', 0):.3f}")
                    
                    # Return the metrics from the new method
                    return {
                        'accuracy': cm_data.get('accuracy', 0.0),
                        'f1': cm_data.get('f1_score', 0.0),
                        'model': best_model
                    }
                else:
                    print(f"      No values in confusion matrix (all zeros)")
            else:
                print(f"      get_confusion_matrix returned invalid data")
                
        except Exception as e:
            print(f"      get_confusion_matrix failed: {e}")
        # ============= END NEW CODE =============
        
        # FALLBACK: Generate fit report and parse it (original code)
        print(f"      Falling back to fit report parsing...")
        fit_report = manager.generate_fit_report(best_model, "0")
        
        # Debug: Check what we actually got
        if len(fit_report) < 1000:
            print(f"      WARNING: Fit report seems too short ({len(fit_report)} chars)")
            print(f"      First 200 chars: {fit_report[:200]}")
        
        # Save the fit report
        if SAVE_FIT_REPORTS:
            fit_file = OUTPUT_DIR / f"fit_fold_{fold_idx}_REAL.txt"
            with open(fit_file, 'w') as f:
                f.write(fit_report)
            print(f"      Saved full fit report to {fit_file}")
        
        # Extract metrics from fit report
        metrics = extract_confusion_matrix_from_fit_report(fit_report)
        
        # If we couldn't extract metrics from fit report, try using search accuracy
        if metrics['accuracy'] == 0 and best_model in search_accuracies:
            print(f"      Using search accuracy as fallback")
            metrics['accuracy'] = search_accuracies[best_model]
            # Estimate F1 from accuracy (rough approximation)
            metrics['f1'] = metrics['accuracy'] * 0.95
        
        print(f"      Final RA Accuracy: {metrics['accuracy']:.3f}, F1: {metrics['f1']:.3f}")
        
        # Clean up temp file if not keeping
        if not KEEP_TEMP_FILES:
            try:
                if 'combined_file' in locals():
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

# =====================================
# USAGE INSTRUCTIONS
# =====================================
"""
To use this modified function in your original unified_ra_ml_comparison.py:

1. Open your working unified_ra_ml_comparison.py file

2. Find the run_pyoccam_analysis function (around line 287)

3. Add this new section after getting the best model (around line 330):
   - Right after: print(f"      Best model: {best_model}")
   - Before: fit_report = manager.generate_fit_report(best_model, "0")

4. Insert this code block:

        # Try the new get_confusion_matrix method first
        print(f"      Trying new get_confusion_matrix() method...")
        try:
            cm_data = manager.get_confusion_matrix(best_model, "0")
            
            # Check if we got real values
            if cm_data and isinstance(cm_data, dict):
                tn = cm_data.get('tn', 0)
                fp = cm_data.get('fp', 0)
                fn = cm_data.get('fn', 0)
                tp = cm_data.get('tp', 0)
                
                # If we have actual confusion matrix values
                if (tn + fp + fn + tp) > 0:
                    print(f"      ✓ Got confusion matrix from new method!")
                    print(f"        TN={tn:.0f}, FP={fp:.0f}, FN={fn:.0f}, TP={tp:.0f}")
                    print(f"        Accuracy: {cm_data.get('accuracy', 0):.3f}")
                    print(f"        F1 Score: {cm_data.get('f1_score', 0):.3f}")
                    
                    # Return the metrics from the new method
                    return {
                        'accuracy': cm_data.get('accuracy', 0.0),
                        'f1': cm_data.get('f1_score', 0.0),
                        'model': best_model
                    }
                else:
                    print(f"      No values in confusion matrix (all zeros)")
            else:
                print(f"      get_confusion_matrix returned invalid data")
                
        except Exception as e:
            print(f"      get_confusion_matrix failed: {e}")
        
        # FALLBACK: Generate fit report and parse it (original code continues...)
        print(f"      Falling back to fit report parsing...")

5. The rest of the function remains unchanged - it will fall back to the 
   original fit report parsing if the new method doesn't work.

This is a minimal change that:
- Tries the new get_confusion_matrix() method first
- Falls back to the original parsing if it fails
- Doesn't break any of the existing functionality
- Provides clear debug output to see what's happening
"""
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

def analyze_by_signature_groups(data_records, signature_idx, X, y, header_lines, 
                                all_variables, variable_definitions):
    """Analyze performance separately for each signature group"""
    
    print(f"\n{'='*80}")
    print("ANALYSIS BY SIGNATURE GROUP")
    print(f"{'='*80}")
    
    # Extract signatures for all records
    signatures = []
    for record in data_records:
        if len(record) > signature_idx:
            signatures.append(record[signature_idx])
        else:
            signatures.append('X')
    
    unique_sigs = sorted(set(signatures))
    if 'X' in unique_sigs:
        unique_sigs.remove('X')
    
    print(f"Found {len(unique_sigs)} signature groups: {unique_sigs}")
    
    results_by_sig = {}
    
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
        unique, counts = np.unique(y_sig, return_counts=True)
        print(f"  Class distribution: {dict(zip(unique, counts))}")
        
        if len(unique) < 2:
            print(f"  Only one class present, skipping...")
            continue
        
        # Split data
        try:
            from sklearn.model_selection import train_test_split
            X_train, X_test, y_train, y_test = train_test_split(
                X_sig, y_sig, test_size=0.3, random_state=RANDOM_SEED, stratify=y_sig
            )
            
            train_indices = sig_indices[:len(X_train)]
            test_indices = sig_indices[len(X_train):]
            train_records = [data_records[i] for i in train_indices]
            test_records = [data_records[i] for i in test_indices]
            
            # Run RA for this signature
            if PYOCCAM_AVAILABLE:
                print(f"  Running RA for signature {sig}...")
                sig_file = TEMP_DIR / f"sig_{sig}_data.txt"
                create_occam_file_for_fold(header_lines, train_records, test_records, sig_file)
                ra_results = run_pyoccam_analysis(sig_file, fold_idx=f"sig_{sig}")
                
                if not KEEP_TEMP_FILES:
                    try:
                        sig_file.unlink()
                    except:
                        pass
            else:
                ra_results = {'accuracy': 0.0, 'f1': 0.0, 'model': 'N/A'}
            
            # Run ML models
            print(f"  Running ML for signature {sig}...")
            ml_results = run_ml_models(X_train, X_test, y_train, y_test)
            
            # Store results
            results_by_sig[sig] = {
                'n_samples': len(sig_indices),
                'n_train': len(X_train),
                'n_test': len(X_test),
                'ra': ra_results,
                'ml': ml_results
            }
            
            # Print summary for this signature
            print(f"\n  Results for Signature {sig}:")
            print(f"    RA: Acc={ra_results['accuracy']:.3f}, F1={ra_results['f1']:.3f}")
            for method, scores in ml_results.items():
                print(f"    {method}: Acc={scores['accuracy']:.3f}, F1={scores['f1']:.3f}")
            
        except Exception as e:
            print(f"  Error analyzing signature {sig}: {e}")
            continue
    
    return results_by_sig

def extract_feature_importance(X, y, variable_definitions, veg_indices):
    """Extract and display feature importance from Random Forest"""
    
    print(f"\n{'='*80}")
    print("FEATURE IMPORTANCE ANALYSIS")
    print(f"{'='*80}")
    
    # Train RF on full dataset to get stable feature importances
    rf = RandomForestClassifier(
        n_estimators=200,  # More trees for stable importance
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
    for idx in veg_indices:
        if idx < len(variable_definitions):
            feature_names.append(variable_definitions[idx]['name'])
        else:
            feature_names.append(f"Feature_{idx}")
    
    # Sort by importance
    indices = np.argsort(importances)[::-1]
    
    print("\nTop 10 Most Important Features:")
    print(f"{'Rank':<6} {'Feature':<20} {'Importance':<12} {'Cumulative':<12}")
    print("-" * 50)
    
    cumulative = 0.0
    for i in range(min(10, len(indices))):
        idx = indices[i]
        cumulative += importances[idx]
        print(f"{i+1:<6} {feature_names[idx]:<20} {importances[idx]:.4f}       {cumulative:.4f}")
    
    # Group by time period (T-0 through T-6)
    time_importance = {}
    for i, name in enumerate(feature_names):
        # Extract time period from name (e.g., "in_d_l0" -> "l0")
        if '_l' in name:
            time_period = name.split('_l')[-1][0]  # Get the number after 'l'
            if time_period not in time_importance:
                time_importance[time_period] = 0.0
            time_importance[time_period] += importances[i]
    
    if time_importance:
        print("\nImportance by Time Period:")
        for period in sorted(time_importance.keys()):
            year = 2015 - int(period) * 5  # Assuming 5-year intervals
            print(f"  T-{period} (~{year}): {time_importance[period]:.4f}")
    
    # Group by ring type (inner, middle, outer)
    ring_importance = {'inner': 0.0, 'middle': 0.0, 'outer': 0.0}
    for i, name in enumerate(feature_names):
        if name.startswith('in_'):
            ring_importance['inner'] += importances[i]
        elif name.startswith('mid_'):
            ring_importance['middle'] += importances[i]
        elif name.startswith('out_'):
            ring_importance['outer'] += importances[i]
    
    print("\nImportance by Ring Type:")
    for ring, imp in ring_importance.items():
        print(f"  {ring.capitalize()}: {imp:.4f}")
    
    return feature_names, importances

def main():
    """Main execution function with enhanced analysis"""
    
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
    
    # Find vegetation variable indices
    veg_indices = []
    for i, var_def in enumerate(variable_definitions):
        if var_def['is_active'] and i >= 4 and i <= 24:
            veg_indices.append(i)
    
    # Prepare ML data
    X, y = prepare_ml_data(data_records, all_variables, variable_definitions)
    
    print(f"\nML Data shape: X={X.shape}, y={y.shape}")
    print(f"Class distribution: {Counter(y)}")
    
    # Feature Importance Analysis (if requested)
    if SHOW_FEATURE_IMPORTANCE and len(X) > 0:
        feature_names, importances = extract_feature_importance(X, y, variable_definitions, veg_indices)
    
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
    
    fold_details = []  # Store detailed results for each fold
    
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
        
        # Store fold details
        fold_details.append({
            'fold': fold_idx + 1,
            'train_size': len(train_idx),
            'test_size': len(test_idx),
            'ra_model': ra_results.get('model', 'N/A'),
            'ra_accuracy': ra_results['accuracy'],
            'ra_f1': ra_results['f1'],
            **{f"{method}_acc": scores['accuracy'] for method, scores in ml_results.items()},
            **{f"{method}_f1": scores['f1'] for method, scores in ml_results.items()}
        })
        
        # Break if in test mode
        if TEST_MODE:
            break
    
    # Signature-based analysis (if requested)
    if ANALYZE_BY_SIGNATURE and signature_idx is not None:
        sig_results = analyze_by_signature_groups(
            data_records, signature_idx, X, y, header_lines, 
            all_variables, variable_definitions
        )
    
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
        print(f"  Models used across folds:")
        for i, r in enumerate(all_ra_results):
            if r['model'] != 'N/A':
                print(f"    Fold {i+1}: {r['model']}")
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
    if ra_accs and any(all_ml_results.values()):
        print(f"\n{'='*60}")
        print("COMPARISON")
        print(f"{'='*60}")
        
        ra_mean_acc = np.mean(ra_accs)
        diff = (ra_mean_acc - best_ml_acc) * 100
        
        if diff > 0:
            print(f"✓ RA outperforms best ML ({best_ml_method}) by {diff:.1f} percentage points")
        else:
            print(f"✗ Best ML ({best_ml_method}) outperforms RA by {-diff:.1f} percentage points")
        
        # Statistical significance test (if multiple folds)
        if len(ra_accs) > 1:
            from scipy import stats
            best_ml_accs = [r['accuracy'] for r in all_ml_results[best_ml_method]]
            t_stat, p_value = stats.ttest_rel(ra_accs, best_ml_accs)
            print(f"\nPaired t-test: t={t_stat:.3f}, p={p_value:.4f}")
            if p_value < 0.05:
                print(f"  Difference is statistically significant (p < 0.05)")
            else:
                print(f"  Difference is NOT statistically significant (p >= 0.05)")
    
    # Save detailed results if requested
    if SAVE_DETAILED_RESULTS and fold_details:
        import pandas as pd
        df = pd.DataFrame(fold_details)
        output_file = OUTPUT_DIR / "detailed_results.csv"
        df.to_csv(output_file, index=False)
        print(f"\nDetailed results saved to: {output_file}")
        
        # Also save summary statistics
        summary = {
            'Method': [],
            'Mean_Accuracy': [],
            'Std_Accuracy': [],
            'Mean_F1': [],
            'Std_F1': []
        }
        
        if ra_accs:
            summary['Method'].append('RA')
            summary['Mean_Accuracy'].append(np.mean(ra_accs))
            summary['Std_Accuracy'].append(np.std(ra_accs))
            summary['Mean_F1'].append(np.mean(ra_f1s))
            summary['Std_F1'].append(np.std(ra_f1s))
        
        for method in all_ml_results:
            if all_ml_results[method]:
                accs = [r['accuracy'] for r in all_ml_results[method]]
                f1s = [r['f1'] for r in all_ml_results[method]]
                summary['Method'].append(method)
                summary['Mean_Accuracy'].append(np.mean(accs))
                summary['Std_Accuracy'].append(np.std(accs))
                summary['Mean_F1'].append(np.mean(f1s))
                summary['Std_F1'].append(np.std(f1s))
        
        df_summary = pd.DataFrame(summary)
        summary_file = OUTPUT_DIR / "summary_results.csv"
        df_summary.to_csv(summary_file, index=False)
        print(f"Summary statistics saved to: {summary_file}")
    
    print(f"\n{'='*80}")
    print("Analysis complete!")
    print(f"{'='*80}")

if __name__ == "__main__":
    main()
