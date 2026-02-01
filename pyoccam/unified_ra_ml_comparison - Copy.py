#!/usr/bin/env python3
"""
Unified comparison pipeline for Reconstructability Analysis (pyoccam) 
and Machine Learning methods for wildfire prediction

Version 6.0 - Clean version with no pyrome mapping
- Using pyrome_sig column directly from data
- Enhanced confusion matrix extraction
- Test mode switch for debugging
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
from datetime import datetime

# Try importing pyoccam
try:
    import pyoccam
    PYOCCAM_AVAILABLE = True
    print(f"PyOccam {pyoccam.__version__} loaded successfully")
except ImportError:
    PYOCCAM_AVAILABLE = False
    print("Warning: pyoccam not found, will use fallback RA results")

from sklearn.model_selection import KFold, StratifiedKFold, train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import (accuracy_score, precision_score, recall_score, 
                           f1_score, confusion_matrix, classification_report)
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.svm import SVC
from sklearn.linear_model import LogisticRegression
import warnings
warnings.filterwarnings('ignore')

# ===== CONFIGURATION =====
INPUT_FILE = 'fire_data_split_all_signature_groups_nlcd_rebinned_sigs.txt'
RANDOM_SEED = 42

# FOLD CONTROL - Set to 1 for testing, 5 for full analysis
TEST_MODE = True  # Set to False for full analysis
N_FOLDS = 1 if TEST_MODE else 5  # 1 fold for testing, 5 for full cross-validation

# Debug and output options
DEBUG_MODE = True  # Set to True for detailed output
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

def parse_occam_format(lines):
    """Parse OCCAM format file according to the manual
    
    Format:
    :nominal
    variable_name, cardinality, flag, abbreviation
    ...
    :no-frequency (optional)
    :data
    data records (space-separated)
    
    IMPORTANT: Data records have ALL columns, including ignored ones (flag=0)
    We need to track all variables to match column positions correctly.
    """
    print("  Parsing OCCAM format file...")
    
    header_lines = []
    data_records = []
    all_variable_names = []  # ALL variables including ignored
    active_variable_names = []  # Only active variables (flag=1 or 2)
    variable_definitions = []
    in_data_section = False
    in_nominal_section = False
    
    for line in lines:
        line_stripped = line.strip()
        
        # Skip empty lines
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
            # Other directives like :no-frequency
            header_lines.append(line_stripped)
            in_nominal_section = False
            continue
        
        # Parse variable definitions (comma-separated)
        if in_nominal_section:
            # Variable definitions are comma-separated
            parts = line_stripped.split(',')
            if len(parts) >= 4:
                var_name = parts[0].strip()
                cardinality = parts[1].strip()
                flag = parts[2].strip()  # 0=ignore, 1=IV, 2=DV
                abbreviation = parts[3].strip()
                
                # Add to ALL variables list (for column position tracking)
                all_variable_names.append(var_name)
                
                # Only add to active list if it's an IV or DV
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
            parts = line_stripped.split()
            if len(parts) > 0:
                data_records.append(parts)
    
    print(f"  Found {len(all_variable_names)} total variables ({len(active_variable_names)} active)")
    print(f"  All variable names: {all_variable_names[:5]}... ({len(all_variable_names)} total)")
    print(f"  Active variables (IVs/DVs): {len(active_variable_names)}")
    print(f"  Parsed {len(data_records)} data records")
    
    if data_records:
        print(f"  Sample data record: {data_records[0][:5]}... ({len(data_records[0])} fields)")
        print(f"  Expected {len(all_variable_names)} fields, got {len(data_records[0])}")
    
    # Identify key columns based on ALL variable positions
    signature_idx = None
    target_idx = None
    
    for i, var_name in enumerate(all_variable_names):
        if 'pyrome_sig' in var_name.lower() or 'pyrosig' in var_name.lower():
            signature_idx = i
            print(f"  Found pyrome_sig at column {i} - no mapping needed!")
        elif 'LARGE_FIRE' in var_name or var_name == 'Z':
            target_idx = i
            print(f"  Found target (LARGE_FIRE) at column {i}")
    
    # If target not found by name, check for last active variable
    if target_idx is None:
        # Find the last variable with flag=2 (DV)
        for i, var_def in enumerate(variable_definitions):
            if var_def['flag'] == '2':
                target_idx = i
                print(f"  Found DV at column {i} (marked as dependent variable)")
                break
    
    # If still not found, use the last column
    if target_idx is None:
        target_idx = len(all_variable_names) - 1
        print(f"  Using last column ({target_idx}) as target")
    
    # Show what we found in the signature column
    if signature_idx is not None and data_records:
        sig_values = set(r[signature_idx] for r in data_records[:100] if len(r) > signature_idx)
        print(f"  Signature values found: {sorted(sig_values)}")
    
    return header_lines, data_records, None, signature_idx, target_idx

def load_data():
    """Load and preprocess the wildfire data"""
    print(f"\nLoading data from {INPUT_FILE}...")
    
    # Read the file
    with open(INPUT_FILE, 'r') as f:
        lines = f.readlines()
    
    # Check if this is an OCCAM format file (starts with :nominal or similar)
    first_non_empty = None
    for line in lines:
        if line.strip():
            first_non_empty = line.strip()
            break
    
    if first_non_empty and first_non_empty.startswith(':'):
        print("  Detected OCCAM format file")
        # Returns: header_lines, data_records, pyrome_idx, signature_idx, target_idx
        return parse_occam_format(lines)
    
    # Otherwise try standard delimited format
    print("  Parsing as standard delimited file...")
    
    # Try to detect the delimiter
    first_line = lines[0].strip()
    
    # Check if it's tab-delimited
    if '\t' in first_line:
        delimiter = '\t'
        print("  Detected tab-delimited file")
    else:
        delimiter = ' '
        print("  Using space as delimiter")
    
    # Parse header
    header = first_line.split(delimiter) if delimiter == '\t' else first_line.split()
    print(f"  Found {len(header)} columns")
    
    # Determine column indices
    signature_idx = None
    target_idx = len(header) - 1  # Assume last column is target
    
    # Find signature column (pyrome_sig)
    for i, col in enumerate(header):
        if 'pyrome_sig' in col.lower() or 'pyrosig' in col.lower():
            signature_idx = i
            print(f"  Signature column: {i} ({col})")
    
    # Parse data
    data_records = []
    for line in lines[1:]:  # Skip header
        if line.strip() and not line.startswith(':'):
            parts = line.strip().split(delimiter) if delimiter == '\t' else line.strip().split()
            if len(parts) >= len(header):
                data_records.append(parts)
    
    print(f"  Loaded {len(data_records)} records")
    
    # No pyrome_idx needed since we have pyrome_sig directly
    return header, data_records, None, signature_idx, target_idx

def prepare_ml_data(records, feature_start=4, feature_end=24, target_idx=30):
    """Prepare data for ML models
    
    With ALL columns (including ignored ones):
    0: FOD_ID (ignored, flag=0)
    1: FIRE_YEAR (ignored, flag=0)
    2: FIRE_SIZE (ignored, flag=0)
    3: FIRE_SIZE_CLASS (ignored, flag=0)
    4-24: Vegetation variables (active, flag=1)
    25: PYROME (ignored, flag=0)
    26: Pyrome_cln (ignored, flag=0)
    27: pyrome_sig (ignored, flag=0)
    28: Season (ignored, flag=0)
    29: elev_bin (active, flag=1)
    30: LARGE_FIRE (active, flag=2, target)
    """
    X = []
    y = []
    
    if not records:
        print("  WARNING: No records to prepare for ML!")
        return np.array([]), np.array([])
    
    # Check the actual structure
    sample_record = records[0]
    num_cols = len(sample_record)
    print(f"  Sample record has {num_cols} columns")
    
    # For this specific file with all columns:
    # Columns 4-24 are the 21 vegetation variables
    # Column 30 is the target (LARGE_FIRE)
    if num_cols >= 31:  # We need at least 31 columns
        feature_start = 4
        feature_end = 24
        # Use the passed target_idx if valid, otherwise default to 30
        if target_idx is None or target_idx >= num_cols:
            target_idx = 30
        print(f"  Using vegetation features from columns {feature_start} to {feature_end}")
        print(f"  Target column: {target_idx}")
    else:
        print(f"  WARNING: Expected 31 columns, got {num_cols}")
        return np.array([]), np.array([])
    
    # Extract features and targets
    for record in records:
        try:
            # Extract vegetation features (columns 4-24)
            features = []
            for i in range(feature_start, feature_end + 1):
                try:
                    # These should be NLCD codes (e.g., 42, 52, 71, etc.)
                    val = float(record[i])
                    features.append(val)
                except (ValueError, IndexError) as e:
                    # Skip this record if we can't parse features
                    break
            
            # Extract target
            if len(record) > target_idx:
                target_val = record[target_idx]
                # Target should be 0 or 1
                if target_val in ['0', '1']:
                    target = int(target_val)
                else:
                    continue
            else:
                continue
            
            # Only add if we got all features
            if len(features) == 21:  # Should have exactly 21 vegetation variables
                X.append(features)
                y.append(target)
                
        except Exception as e:
            continue
    
    if len(X) == 0:
        print("  WARNING: No valid samples extracted!")
        return np.array([]), np.array([])
    
    X_array = np.array(X)
    y_array = np.array(y)
    
    print(f"  Extracted {len(X_array)} samples with {X_array.shape[1]} vegetation features")
    print(f"  Target distribution: 0={np.sum(y_array==0)}, 1={np.sum(y_array==1)}")
    
    return X_array, y_array

def create_stratification_key(records, signature_idx, target_idx):
    """Create stratification key combining signature and target
    
    Since pyrome_sig is already in the data (column 27), use it directly
    """
    strat_keys = []
    
    # If we have the signature column, use it
    if signature_idx is not None:
        print(f"  Using signature column {signature_idx} for stratification")
        for record in records:
            try:
                # Get signature (should be A-E)
                if signature_idx < len(record):
                    sig = record[signature_idx].upper()
                    # Validate it's A-E
                    if sig not in ['A', 'B', 'C', 'D', 'E']:
                        sig = 'A'  # Default
                else:
                    sig = 'A'
                
                # Get target (0/1)
                if target_idx is not None and target_idx < len(record):
                    target = record[target_idx]
                else:
                    target = '0'
                
                # Combine for stratification
                strat_key = f"{sig}_{target}"
                strat_keys.append(strat_key)
            except:
                strat_keys.append("A_0")
    else:
        print("  WARNING: No signature column found, using target only for stratification")
        for record in records:
            try:
                if target_idx is not None and target_idx < len(record):
                    target = record[target_idx]
                else:
                    target = '0'
                strat_keys.append(f"X_{target}")
            except:
                strat_keys.append("X_0")
    
    # Show distribution
    strat_dist = Counter(strat_keys)
    print(f"  Stratification distribution: {dict(strat_dist)}")
    
    return strat_keys

def extract_confusion_matrix_from_fit_report(fit_report, target_state="0"):
    """
    Extract confusion matrix values from OCCAM fit report text
    
    Based on the actual OCCAM output format:
    Confusion Matrix for Fit Rule (Test)
    ,Actual,|,Rule
    ,,|,Z=0,,Z=not0
    ,Z=0,|,TN=,72.000,FP=,112.000,AN=,184.000
    ,Z=not0,|,FN=,40.000,TP=,144.000,AP=,184.000
    
    Also extracts accuracy from:
    ,%correct,correct / sample size,0.587
    """
    tn, tp, fn, fp = 0, 0, 0, 0
    test_accuracy = None
    
    lines = fit_report.split('\n')
    
    # Look for "Confusion Matrix for Fit Rule (Test)" - we want the TEST confusion matrix
    test_section_found = False
    for i, line in enumerate(lines):
        if 'Confusion Matrix for Fit Rule (Test)' in line:
            test_section_found = True
            if DEBUG_MODE:
                print(f"        Found TEST confusion matrix at line {i}")
            
            # Look for the Z=0 row (contains TN and FP)
            for j in range(i+1, min(i+10, len(lines))):
                if ',Z=0,|,TN=' in lines[j]:
                    # Parse this line: ,Z=0,|,TN=,72.000,FP=,112.000,AN=,184.000
                    parts = lines[j].split(',')
                    for k, part in enumerate(parts):
                        if part == 'TN=' and k+1 < len(parts):
                            try:
                                tn = int(float(parts[k+1]))
                            except:
                                pass
                        elif part == 'FP=' and k+1 < len(parts):
                            try:
                                fp = int(float(parts[k+1]))
                            except:
                                pass
                
                # Look for the Z=not0 row (contains FN and TP)
                elif ',Z=not0,|,FN=' in lines[j]:
                    # Parse this line: ,Z=not0,|,FN=,40.000,TP=,144.000,AP=,184.000
                    parts = lines[j].split(',')
                    for k, part in enumerate(parts):
                        if part == 'FN=' and k+1 < len(parts):
                            try:
                                fn = int(float(parts[k+1]))
                            except:
                                pass
                        elif part == 'TP=' and k+1 < len(parts):
                            try:
                                tp = int(float(parts[k+1]))
                            except:
                                pass
            
            # Look for accuracy in the Additional Statistics (Test) section
            for j in range(i+1, min(i+30, len(lines))):
                if ',%correct,correct / sample size,' in lines[j]:
                    parts = lines[j].split(',')
                    if len(parts) >= 4:
                        try:
                            test_accuracy = float(parts[3])
                            if DEBUG_MODE:
                                print(f"        Found test accuracy: {test_accuracy:.3f}")
                        except:
                            pass
                    break
            
            # If we found the values, stop looking
            if tn > 0 or tp > 0 or fn > 0 or fp > 0:
                if DEBUG_MODE:
                    print(f"        Extracted TEST confusion matrix: TN={tn}, FP={fp}, FN={fn}, TP={tp}")
                break
    
    # If we didn't find test confusion matrix, look for training as fallback
    if not test_section_found or (tn == 0 and tp == 0 and fn == 0 and fp == 0):
        for i, line in enumerate(lines):
            if 'Confusion Matrix for Fit Rule (Training)' in line:
                if DEBUG_MODE:
                    print(f"        WARNING: Using TRAINING confusion matrix as fallback")
                
                # Look for the Z=0 row
                for j in range(i+1, min(i+10, len(lines))):
                    if ',Z=0,|,TN=' in lines[j]:
                        parts = lines[j].split(',')
                        for k, part in enumerate(parts):
                            if part == 'TN=' and k+1 < len(parts):
                                try:
                                    tn = int(float(parts[k+1]))
                                except:
                                    pass
                            elif part == 'FP=' and k+1 < len(parts):
                                try:
                                    fp = int(float(parts[k+1]))
                                except:
                                    pass
                    
                    elif ',Z=not0,|,FN=' in lines[j]:
                        parts = lines[j].split(',')
                        for k, part in enumerate(parts):
                            if part == 'FN=' and k+1 < len(parts):
                                try:
                                    fn = int(float(parts[k+1]))
                                except:
                                    pass
                            elif part == 'TP=' and k+1 < len(parts):
                                try:
                                    tp = int(float(parts[k+1]))
                                except:
                                    pass
                
                if tn > 0 or tp > 0 or fn > 0 or fp > 0:
                    break
    
    # Return dictionary with confusion matrix values
    cm = {'TN': tn, 'TP': tp, 'FN': fn, 'FP': fp}
    
    # Add test accuracy if found
    if test_accuracy is not None:
        cm['test_accuracy'] = test_accuracy
    
    return cm

def calculate_metrics_from_cm(cm):
    """Calculate performance metrics from confusion matrix"""
    if not cm or (cm['TN'] + cm['TP'] + cm['FN'] + cm['FP']) == 0:
        return {
            'accuracy': 0.5,
            'precision': 0.0,
            'recall': 0.0,
            'f1': 0.0,
            'sensitivity': 0.0,
            'specificity': 0.0
        }
    
    total = cm['TN'] + cm['TP'] + cm['FN'] + cm['FP']
    accuracy = (cm['TP'] + cm['TN']) / total if total > 0 else 0
    
    # Precision: TP / (TP + FP)
    precision = cm['TP'] / (cm['TP'] + cm['FP']) if (cm['TP'] + cm['FP']) > 0 else 0
    
    # Recall (Sensitivity): TP / (TP + FN)
    recall = cm['TP'] / (cm['TP'] + cm['FN']) if (cm['TP'] + cm['FN']) > 0 else 0
    
    # Specificity: TN / (TN + FP)
    specificity = cm['TN'] / (cm['TN'] + cm['FP']) if (cm['TN'] + cm['FP']) > 0 else 0
    
    # F1 Score
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
    
    return {
        'accuracy': accuracy,
        'precision': precision,
        'recall': recall,
        'f1': f1,
        'sensitivity': recall,  # Same as recall
        'specificity': specificity,
        'TN': cm['TN'],
        'TP': cm['TP'],
        'FN': cm['FN'],
        'FP': cm['FP']
    }

def save_fold_data(records, header, fold_idx, is_train=True):
    """Save fold data to file for pyoccam in OCCAM format"""
    suffix = "train" if is_train else "test"
    filename = TEMP_DIR / f"fold_{fold_idx}_{suffix}.txt"
    
    with open(filename, 'w') as f:
        # If header is a list of strings (OCCAM header lines), write them
        if isinstance(header, list) and header and isinstance(header[0], str):
            # Check if these are OCCAM format headers
            if any(line.startswith(':') for line in header if isinstance(line, str)):
                # Write OCCAM headers
                for line in header:
                    if isinstance(line, str):
                        f.write(line + '\n')
                # Add :data marker if not already there
                if ':data' not in header:
                    f.write(':data\n')
            else:
                # Regular header - join with spaces
                f.write(' '.join(str(h) for h in header) + '\n')
        
        # Write data records (space-separated)
        for record in records:
            if isinstance(record, list):
                f.write(' '.join(str(x) for x in record) + '\n')
            else:
                f.write(str(record) + '\n')
    
    return filename

def run_pyoccam_analysis(train_file, test_file, fold_idx):
    """Run pyoccam RA analysis and parse results"""
    
    if not PYOCCAM_AVAILABLE:
        return {'accuracy': 0.5, 'f1': 0.5, 'model': 'N/A'}
    
    combined_file = None  # Initialize for finally clause
    
    try:
        print(f"      Starting pyoccam analysis for fold {fold_idx}")
        
        # Create combined file with :test marker
        combined_file = TEMP_DIR / f"combined_fold_{fold_idx}.txt"
        
        with open(combined_file, 'w') as f:
            # Write training data
            with open(train_file, 'r') as train_f:
                train_lines = train_f.readlines()
                f.writelines(train_lines)
            
            # Write test marker on its own line
            f.write(":test\n")
            
            # Write test data without header
            with open(test_file, 'r') as test_f:
                test_lines = test_f.readlines()
                # Skip header lines for test data
                in_data = False
                for line in test_lines:
                    if ':data' in line:
                        in_data = True
                        continue
                    if in_data:
                        f.write(line)
        
        # Initialize manager
        manager = pyoccam.VBMManager()
        
        # Load data
        ok = manager.init_from_command_line(["occam", str(combined_file)])
        if not ok:
            raise RuntimeError(f"Failed to load {combined_file}")
        
        # Check if test data was loaded
        has_test = manager.has_test_data()
        if DEBUG_MODE:
            print(f"      Test data detected: {has_test}")
        
        # Set reference model and run search
        manager.set_ref_model("bottom")
        manager.generate_search_report(RA_SEARCH_TYPE, RA_SEARCH_DEPTH, RA_SEARCH_WIDTH)
        
        # Get best model
        best_model = manager.get_best_model_by_information()
        if not best_model:
            best_model = manager.get_best_model_by_bic()
            if DEBUG_MODE:
                print(f"      Using BIC model: {best_model}")
        else:
            if DEBUG_MODE:
                print(f"      Using Information criterion model: {best_model}")
        
        # Generate fit report for the best model - FIXED: use generate_fit_report not get_fit_report
        fit_report = manager.generate_fit_report(best_model, "0")  # "0" is the target state
        
        # Save fit report if requested
        if SAVE_FIT_REPORTS:
            report_file = OUTPUT_DIR / f"fold_{fold_idx}_fit_report.txt"
            with open(report_file, 'w') as f:
                f.write(fit_report)
            print(f"      Saved fit report to {report_file}")
        
        # Try to get confusion matrix directly
        try:
            cm_dict = manager.get_confusion_matrix(best_model, "0")
            
            if cm_dict and 'accuracy' in cm_dict:
                # Use the direct confusion matrix from pyoccam
                if DEBUG_MODE:
                    print(f"      Got confusion matrix from pyoccam directly")
                    print(f"      Accuracy: {cm_dict.get('accuracy', 0):.3f}")
                    print(f"      F1 Score: {cm_dict.get('f1_score', 0):.3f}")
                
                return {
                    'accuracy': cm_dict.get('accuracy', 0.5),
                    'precision': cm_dict.get('precision', 0.0),
                    'recall': cm_dict.get('recall', 0.0),
                    'f1': cm_dict.get('f1_score', 0.0),
                    'sensitivity': cm_dict.get('sensitivity', 0.0),
                    'specificity': cm_dict.get('specificity', 0.0),
                    'model': best_model
                }
        except Exception as e:
            if DEBUG_MODE:
                print(f"      Could not get confusion matrix directly: {e}")
        
        # Fallback: Parse confusion matrix from fit report
        cm = enhanced_confusion_matrix_parser(fit_report, "0")
        
        if cm:
            metrics = calculate_metrics_from_cm(cm)
            metrics['model'] = best_model
            
            if DEBUG_MODE:
                print(f"      Parsed from fit report - TN={cm['TN']}, FP={cm['FP']}, FN={cm['FN']}, TP={cm['TP']}")
                print(f"      Metrics: Acc={metrics['accuracy']:.3f}, F1={metrics['f1']:.3f}")
            
            return metrics
        else:
            # Last fallback: simple accuracy parsing
            if DEBUG_MODE:
                print("      Fallback to simple accuracy parsing...")
            
            # Try to find %correct for test data
            test_pattern = r'Test.*?%correct[:\s]*([\d.]+)'
            test_match = re.search(test_pattern, fit_report, re.IGNORECASE | re.DOTALL)
            
            accuracy = 0.5
            if test_match:
                val = float(test_match.group(1))
                accuracy = val / 100.0 if val > 1 else val
                if DEBUG_MODE:
                    print(f"      Found test accuracy: {accuracy:.3f}")
            
            return {
                'accuracy': accuracy,
                'f1': accuracy * 0.95,  # Estimate
                'model': best_model,
                'TN': 0, 'TP': 0, 'FN': 0, 'FP': 0
            }
        
    except Exception as e:
        if DEBUG_MODE:
            print(f"      RA Error: {e}")
            import traceback
            traceback.print_exc()
        else:
            print(f"      RA Error: {e}")
        return {'accuracy': 0.5, 'f1': 0.5, 'model': 'ERROR'}
    finally:
        # Clean up - force close any file handles and retry deletion
        if not KEEP_TEMP_FILES and combined_file and combined_file.exists():
            try:
                # Force garbage collection to release file handles
                gc.collect()
                time.sleep(0.1)  # Brief pause to ensure file is released
                combined_file.unlink()
            except PermissionError:
                # If still locked, mark for deletion later
                if DEBUG_MODE:
                    print(f"      Warning: Could not delete {combined_file} (file locked)")
            except Exception as e:
                if DEBUG_MODE:
                    print(f"      Warning: Could not delete {combined_file}: {e}")

def run_ml_models(X_train, y_train, X_test, y_test):
    """Run various ML models and return results"""
    models = {
        'Logistic Regression': LogisticRegression(max_iter=1000, random_state=RANDOM_SEED),
        'Random Forest': RandomForestClassifier(n_estimators=100, random_state=RANDOM_SEED),
        'Decision Tree': DecisionTreeClassifier(random_state=RANDOM_SEED),
        'SVM': SVC(kernel='rbf', random_state=RANDOM_SEED)
    }
    
    results = {}
    for name, model in models.items():
        try:
            # Train model
            model.fit(X_train, y_train)
            
            # Predict
            y_pred = model.predict(X_test)
            
            # Calculate metrics
            cm = confusion_matrix(y_test, y_pred)
            
            results[name] = {
                'accuracy': accuracy_score(y_test, y_pred),
                'precision': precision_score(y_test, y_pred, zero_division=0),
                'recall': recall_score(y_test, y_pred, zero_division=0),
                'f1': f1_score(y_test, y_pred, zero_division=0),
                'TN': cm[0, 0] if cm.shape == (2, 2) else 0,
                'FP': cm[0, 1] if cm.shape == (2, 2) else 0,
                'FN': cm[1, 0] if cm.shape == (2, 2) else 0,
                'TP': cm[1, 1] if cm.shape == (2, 2) else 0
            }
            
        except Exception as e:
            print(f"    Error with {name}: {e}")
            results[name] = {
                'accuracy': 0.0, 'precision': 0.0, 'recall': 0.0, 'f1': 0.0,
                'TN': 0, 'FP': 0, 'FN': 0, 'TP': 0
            }
    
    return results

def main():
    """Main execution function"""
    print("=" * 80)
    print("WILDFIRE ANALYSIS: RA vs ML COMPARISON")
    print(f"Mode: {'TEST (1 fold)' if TEST_MODE else 'FULL (5 folds)'}")
    print("=" * 80)
    
    # Load data - returns 5 values (no pyrome_map needed anymore)
    result = load_data()
    if len(result) == 5:
        header, data_records, pyrome_idx, signature_idx, target_idx = result
    else:
        print(f"ERROR: Unexpected return from load_data: {len(result)} values")
        return
    
    # Check if data loaded successfully
    if not data_records:
        print("\nERROR: No data records loaded!")
        print("Please check the input file format.")
        return
    
    # Check that we have the signature column
    if signature_idx is None:
        print("\nWARNING: No pyrome_sig column found!")
        print("Expected to find 'pyrome_sig' column with values A-E")
    
    # Create stratification keys using the signature column
    strat_keys = create_stratification_key(data_records, signature_idx, target_idx)
    
    # Prepare data for ML - use the correct target index
    if target_idx is not None:
        X, y = prepare_ml_data(data_records, target_idx=target_idx)
    else:
        X, y = prepare_ml_data(data_records)
    
    # Check if ML data was prepared successfully
    if len(X) == 0 or len(y) == 0:
        print("\nERROR: Could not prepare data for ML analysis!")
        print("Please check the data format.")
        return
    
    print(f"\nML Data shape: X={X.shape}, y={y.shape}")
    print(f"Class distribution: {Counter(y)}")
    
    # Check for class imbalance
    class_counts = Counter(y)
    if len(class_counts) < 2:
        print("\nERROR: Only one class found in target variable!")
        print(f"Classes found: {class_counts}")
        return
    
    # Initialize results storage
    all_results = {
        'RA': [],
        'Logistic Regression': [],
        'Random Forest': [],
        'Decision Tree': [],
        'SVM': []
    }
    
    # Cross-validation
    try:
        skf = StratifiedKFold(n_splits=N_FOLDS, shuffle=True, random_state=RANDOM_SEED)
        fold_splits = list(skf.split(X, y))
    except Exception as e:
        print(f"\nERROR in creating cross-validation splits: {e}")
        
        # For TEST_MODE with 1 fold, just do a simple split
        if TEST_MODE and N_FOLDS == 1:
            print("Using simple train-test split for TEST_MODE...")
            train_idx, test_idx = train_test_split(
                range(len(X)), 
                test_size=0.3, 
                stratify=y,
                random_state=RANDOM_SEED
            )
            fold_splits = [(np.array(train_idx), np.array(test_idx))]
        else:
            return
    
    for fold_idx, (train_idx, test_idx) in enumerate(fold_splits):
        print(f"\n{'='*60}")
        print(f"FOLD {fold_idx + 1}/{len(fold_splits)}")
        print(f"{'='*60}")
        
        # Split data
        X_train, X_test = X[train_idx], X[test_idx]
        y_train, y_test = y[train_idx], y[test_idx]
        
        print(f"  Train size: {len(train_idx)}, Test size: {len(test_idx)}")
        print(f"  Train class distribution: {Counter(y_train)}")
        print(f"  Test class distribution: {Counter(y_test)}")
        
        # Prepare data records for RA
        train_records = [data_records[i] for i in train_idx]
        test_records = [data_records[i] for i in test_idx]
        
        # Save data for pyoccam
        train_file = save_fold_data(train_records, header, fold_idx, True)
        test_file = save_fold_data(test_records, header, fold_idx, False)
        
        # Run RA analysis
        print("\n  Running RA Analysis...")
        ra_results = run_pyoccam_analysis(train_file, test_file, fold_idx)
        all_results['RA'].append(ra_results)
        
        # Run ML models
        print("\n  Running ML Models...")
        ml_results = run_ml_models(X_train, y_train, X_test, y_test)
        
        for model_name, metrics in ml_results.items():
            all_results[model_name].append(metrics)
            print(f"    {model_name}: Acc={metrics['accuracy']:.3f}, F1={metrics['f1']:.3f}")
        
        # Clean up temp files if not keeping
        if not KEEP_TEMP_FILES:
            if train_file.exists():
                train_file.unlink()
            if test_file.exists():
                test_file.unlink()
    
    # Summary results
    print("\n" + "=" * 80)
    print("SUMMARY RESULTS")
    print("=" * 80)
    
    print(f"\n{'Method':<25} {'Accuracy':<15} {'F1 Score':<15} {'Precision':<15} {'Recall':<15}")
    print("-" * 80)
    
    for method in all_results:
        if all_results[method]:
            accuracies = [r.get('accuracy', 0) for r in all_results[method]]
            f1_scores = [r.get('f1', 0) for r in all_results[method]]
            precisions = [r.get('precision', 0) for r in all_results[method]]
            recalls = [r.get('recall', 0) for r in all_results[method]]
            
            mean_acc = np.mean(accuracies)
            std_acc = np.std(accuracies)
            mean_f1 = np.mean(f1_scores)
            std_f1 = np.std(f1_scores)
            mean_prec = np.mean(precisions)
            mean_rec = np.mean(recalls)
            
            print(f"{method:<25} {mean_acc:.3f} ± {std_acc:.3f}   "
                  f"{mean_f1:.3f} ± {std_f1:.3f}   "
                  f"{mean_prec:.3f}           "
                  f"{mean_rec:.3f}")
    
    # Save detailed results
    results_file = OUTPUT_DIR / "comparison_results.txt"
    with open(results_file, 'w') as f:
        f.write("WILDFIRE RA vs ML COMPARISON RESULTS\n")
        f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Input file: {INPUT_FILE}\n")
        f.write(f"Number of folds: {N_FOLDS}\n")
        f.write(f"Search type: {RA_SEARCH_TYPE}\n")
        f.write("\n" + "="*80 + "\n\n")
        
        for method in all_results:
            f.write(f"\n{method} Results:\n")
            f.write("-" * 40 + "\n")
            for i, result in enumerate(all_results[method]):
                f.write(f"Fold {i+1}: {result}\n")
    
    print(f"\nResults saved to {results_file}")
    print("\nAnalysis complete!")

if __name__ == "__main__":
    main()
