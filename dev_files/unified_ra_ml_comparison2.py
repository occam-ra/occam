#!/usr/bin/env python3
"""
Enhanced Wildfire Analysis: RA vs ML with Signature Group Partitioning
Version 7.1 - Fixed confusion matrix parsing

NEW FEATURES:
- Proper test confusion matrix extraction from fit reports
- Signature group partitioning (analyze each cluster A-E separately)
- Feature importance analysis (temporal patterns, ring importance)
- Per-signature performance metrics
"""

import pandas as pd
import numpy as np
import os
import sys
import tempfile
import re
import time
import gc
from pathlib import Path
from collections import Counter, defaultdict
from datetime import datetime

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
from sklearn.metrics import (accuracy_score, f1_score, precision_score, 
                            recall_score, confusion_matrix, classification_report)

import warnings
warnings.filterwarnings('ignore')

# ===== CONFIGURATION =====
INPUT_FILE = 'fire_data_split_all_signature_groups_nlcd_rebinned_sigs.txt'
RANDOM_SEED = 42
N_FOLDS = 5
TEST_MODE = False  # Set to True for quick testing
DEBUG_MODE = True

# Signature mapping
SIGNATURE_NAMES = {
    'A': 'Evergreen-dominated (Coastal/Cascade)',
    'B': 'Mixed shrub-grass foothill mosaic', 
    'C': 'Central Valley & foothills (developed/cropland)',
    'D': 'Northern Sierran Foothills (grass dominant)',
    'E': 'Cold-desert shrublands'
}

# ===== OUTPUT DIRECTORY =====
OUTPUT_DIR = Path('occam_output')
OUTPUT_DIR.mkdir(exist_ok=True)


def load_and_prepare_data(filepath):
    """Load and prepare the wildfire dataset from OCCAM format"""
    print(f"\n{'='*60}")
    print(f"Loading data from: {filepath}")
    print(f"{'='*60}")
    
    # Parse OCCAM format file
    with open(filepath, 'r') as f:
        lines = f.readlines()
    
    # Find variable definitions and data section
    variables = []
    data_lines = []
    mode = 'header'
    
    for line in lines:
        line = line.strip()
        
        # Skip empty lines and comments
        if not line or line.startswith('#'):
            continue
        
        # Check for section markers
        if line == ':nominal':
            mode = 'nominal'
            continue
        elif line == ':data':
            mode = 'data'
            continue
        elif line == ':test':
            # We'll handle test data separately in pyoccam
            break
        
        # Parse based on current mode
        if mode == 'nominal':
            # Format: varname, cardinality, type, abbreviation
            # Example: FOD_ID, 7405,0,fo
            parts = [p.strip() for p in line.split(',')]
            if len(parts) >= 4:
                var_name = parts[0]
                cardinality = int(parts[1])
                var_type = int(parts[2])  # 0=ignore, 1=IV, 2=DV
                abbreviation = parts[3]
                
                variables.append({
                    'name': var_name,
                    'cardinality': cardinality,
                    'type': var_type,
                    'abbrev': abbreviation
                })
        
        elif mode == 'data':
            # Data rows are tab or space separated
            if '\t' in line:
                parts = line.split('\t')
            else:
                parts = line.split()
            data_lines.append(parts)
    
    print(f"✓ Found {len(variables)} variable definitions")
    print(f"✓ Found {len(data_lines)} data lines")
    
    # Get column names from variables (use actual names, not abbreviations)
    column_names = [var['name'] for var in variables]
    
    # Create DataFrame
    df = pd.DataFrame(data_lines, columns=column_names if len(column_names) == len(data_lines[0]) else None)
    
    print(f"✓ Loaded {len(df)} records with {len(df.columns)} columns")
    print(f"  Columns: {', '.join(df.columns[:5])}... (showing first 5)")
    
    # Convert numeric columns and encode categorical ones
    numeric_count = 0
    for col in df.columns:
        try:
            # Try converting to numeric
            df[col] = pd.to_numeric(df[col], errors='coerce')
            # If successful and not all NaN, it's numeric
            if not df[col].isna().all():
                numeric_count += 1
            else:
                # If all NaN, it's categorical - label encode it
                df[col] = df[col].astype(str)
                le_col = LabelEncoder()
                df[col] = le_col.fit_transform(df[col])
        except:
            # If conversion fails, it's categorical - label encode it
            le_col = LabelEncoder()
            df[col] = le_col.fit_transform(df[col])
    
    print(f"  Converted {numeric_count} numeric columns, encoded {len(df.columns) - numeric_count} categorical columns")
    
    # Get signature distribution
    if 'sig_grp' in df.columns:
        sig_counts = df['sig_grp'].value_counts().sort_index()
        print(f"\n📊 Signature Distribution:")
        for sig, count in sig_counts.items():
            sig_name = SIGNATURE_NAMES.get(sig, 'Unknown')
            print(f"  {sig} ({sig_name}): {count} fires")
    
    # Target variable
    if 'FIRE_SIZE_CLASS' in df.columns:
        target_dist = df['FIRE_SIZE_CLASS'].value_counts()
        print(f"\n🎯 Target Distribution:")
        for cls, count in target_dist.items():
            print(f"  {cls}: {count} fires ({count/len(df)*100:.1f}%)")
    
    return df


def extract_confusion_matrix_metrics(fit_report_text):
    """
    Extract TEST confusion matrix and metrics from pyoccam fit report.
    
    The fit report contains multiple confusion matrices.
    We need the TEST matrix for the main model (not component relations).
    """
    metrics = {
        'accuracy': None,
        'f1': None, 
        'precision': None,
        'recall': None,
        'sensitivity': None,
        'specificity': None,
        'tn': 0,
        'fp': 0,
        'fn': 0,
        'tp': 0
    }
    
    if 'Confusion Matrix' not in fit_report_text:
        return metrics
    
    lines = fit_report_text.split('\n')
    
    # Find the main model's TEST confusion matrix
    in_model_cm = False
    in_test_section = False
    found_cm_matrix = False
    
    for i, line in enumerate(lines):
        # Check if we're entering the main model CM section
        if 'Confusion Matrix for the Model IV:' in line:
            in_model_cm = True
            continue
        
        # Look for Test section within model CM
        if in_model_cm and 'Confusion Matrix for Fit Rule (Test)' in line:
            in_test_section = True
            continue
        
        # Parse the actual confusion matrix table
        if in_test_section and not found_cm_matrix:
            # Look for matrix rows
            # Format: "Z=0    | TN=170.000 FP=51.000 AN=221.000"
            if 'TN=' in line and 'FP=' in line:
                tn_match = re.search(r'TN=([\d.]+)', line)
                fp_match = re.search(r'FP=([\d.]+)', line)
                if tn_match and fp_match:
                    metrics['tn'] = int(float(tn_match.group(1)))
                    metrics['fp'] = int(float(fp_match.group(1)))
                continue
            
            if 'FN=' in line and 'TP=' in line:
                fn_match = re.search(r'FN=([\d.]+)', line)
                tp_match = re.search(r'TP=([\d.]+)', line)
                if fn_match and tp_match:
                    metrics['fn'] = int(float(fn_match.group(1)))
                    metrics['tp'] = int(float(tp_match.group(1)))
                    found_cm_matrix = True
                continue
        
        # Parse metrics from "Additional Statistics (Test)" section
        if in_test_section and found_cm_matrix:
            if 'Accuracy' in line or '%correct' in line:
                match = re.search(r'([\d.]+)$', line.strip())
                if match:
                    metrics['accuracy'] = float(match.group(1))
            
            elif 'F1 score' in line:
                match = re.search(r'([\d.]+)$', line.strip())
                if match:
                    metrics['f1'] = float(match.group(1))
            
            elif 'Precision' in line and 'Negative' not in line:
                match = re.search(r'([\d.]+)$', line.strip())
                if match:
                    metrics['precision'] = float(match.group(1))
            
            elif 'Sensitivity' in line or 'Recall' in line:
                match = re.search(r'([\d.]+)$', line.strip())
                if match:
                    metrics['recall'] = float(match.group(1))
                    metrics['sensitivity'] = float(match.group(1))
            
            elif 'Specificity' in line:
                match = re.search(r'([\d.]+)$', line.strip())
                if match:
                    metrics['specificity'] = float(match.group(1))
            
            # Stop at next confusion matrix
            elif 'Confusion Matrix for' in line and 'Test' not in line:
                break
    
    # Compute from CM if not found in report
    if not metrics['accuracy'] and (metrics['tn'] + metrics['fp'] + metrics['fn'] + metrics['tp']) > 0:
        total = metrics['tn'] + metrics['fp'] + metrics['fn'] + metrics['tp']
        metrics['accuracy'] = (metrics['tn'] + metrics['tp']) / total
        
        # Compute F1 if we have TP
        if metrics['tp'] > 0:
            precision = metrics['tp'] / (metrics['tp'] + metrics['fp']) if (metrics['tp'] + metrics['fp']) > 0 else 0
            recall = metrics['tp'] / (metrics['tp'] + metrics['fn']) if (metrics['tp'] + metrics['fn']) > 0 else 0
            metrics['f1'] = (2 * precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
            metrics['precision'] = precision
            metrics['recall'] = recall
    
    return metrics


def parse_ra_model_structure(model_name):
    """
    Parse RA model to extract which features are used.
    Example: IV:I0M0Z:M2Z:O4Z:O5Z:ElevZ
    """
    components = model_name.split(':')
    
    structure = {
        'temporal_periods': [],
        'rings': {'inner': [], 'middle': [], 'outer': []},
        'includes_elevation': False,
        'num_components': len(components) - 1
    }
    
    for comp in components[1:]:  # Skip 'IV'
        # Check for elevation
        if 'Elev' in comp:
            structure['includes_elevation'] = True
            continue
        
        # Extract temporal period (T-0 to T-6)
        match = re.search(r'([IMO])(\d+)', comp)
        if match:
            ring_letter = match.group(1)
            time_period = int(match.group(2))
            
            structure['temporal_periods'].append(time_period)
            
            # Map to ring
            ring_map = {'I': 'inner', 'M': 'middle', 'O': 'outer'}
            if ring_letter in ring_map:
                structure['rings'][ring_map[ring_letter]].append(time_period)
    
    structure['temporal_periods'] = sorted(list(set(structure['temporal_periods'])))
    
    return structure


def analyze_feature_importance_rf(model, feature_names, top_n=20):
    """Extract and analyze Random Forest feature importance"""
    importances = model.feature_importances_
    indices = np.argsort(importances)[::-1]
    
    feature_importance = []
    for i in range(min(top_n, len(feature_names))):
        idx = indices[i]
        feature_importance.append({
            'feature': feature_names[idx],
            'importance': importances[idx],
            'rank': i + 1
        })
    
    # Aggregate by temporal period and ring
    temporal_importance = defaultdict(float)
    ring_importance = defaultdict(float)
    
    for feat, imp in zip(feature_names, importances):
        # Parse feature name (e.g., "I0", "M2", "O5")
        match = re.search(r'([IMO])(\d+)', feat)
        if match:
            ring = match.group(1)
            time = int(match.group(2))
            
            temporal_importance[time] += imp
            
            ring_map = {'I': 'inner', 'M': 'middle', 'O': 'outer'}
            if ring in ring_map:
                ring_importance[ring_map[ring]] += imp
    
    return {
        'top_features': feature_importance,
        'temporal_importance': dict(temporal_importance),
        'ring_importance': dict(ring_importance)
    }


def run_pyoccam_analysis(X_train, y_train, X_test, y_test, fold, signature='ALL'):
    """Run pyoccam RA analysis with proper test confusion matrix extraction"""
    
    if not PYOCCAM_AVAILABLE:
        return None
    
    print(f"\n  🔬 Running RA analysis (Fold {fold}, Sig {signature})...")
    
    # Create temporary files
    train_file = OUTPUT_DIR / f'train_fold{fold}_sig{signature}.txt'
    test_file = OUTPUT_DIR / f'test_fold{fold}_sig{signature}.txt'
    combined_file = OUTPUT_DIR / f'combined_fold{fold}_sig{signature}.txt'
    
    try:
        # Prepare training data
        train_df = X_train.copy()
        train_df['TARGET'] = y_train
        
        # Write training file
        with open(train_file, 'w') as f:
            f.write(f":nominal TARGET\n")
            for col in X_train.columns:
                f.write(f":nominal {col}\n")
            f.write("\n")
            
            for _, row in train_df.iterrows():
                values = [str(int(row[col])) for col in train_df.columns]
                f.write(','.join(values) + '\n')
        
        # Prepare test data
        test_df = X_test.copy()
        test_df['TARGET'] = y_test
        
        with open(test_file, 'w') as f:
            f.write(f":nominal TARGET\n")
            for col in X_test.columns:
                f.write(f":nominal {col}\n")
            f.write("\n")
            
            for _, row in test_df.iterrows():
                values = [str(int(row[col])) for col in test_df.columns]
                f.write(','.join(values) + '\n')
        
        # Run pyoccam on training data to find best model
        manager = pyoccam.VBMManager()
        manager.init_from_command_line([
            "pyoccam",
            str(train_file),
            f"TARGET"
        ])
        
        # Search for best model
        manager.set_ref_model("bottom")
        search_report = manager.generate_search_report("full-up", 5, 3)
        
        # Get search results
        search_report = manager.getSearchReport()
        
        # Parse best model
        lines = search_report.strip().split('\n')
        best_model = None
        for line in lines:
            if line.strip() and not line.startswith('#') and '\t' in line:
                parts = line.split('\t')
                if len(parts) >= 2:
                    best_model = parts[1].strip()
                    break
        
        if not best_model:
            print("    ⚠ No best model found in search")
            return None
        
        print(f"    ✓ Best model: {best_model[:50]}...")
        
        # Create combined file with :test marker for proper test evaluation
        with open(combined_file, 'w') as f:
            f.write(f":nominal TARGET\n")
            for col in X_train.columns:
                f.write(f":nominal {col}\n")
            f.write("\n")
            
            # Training data
            for _, row in train_df.iterrows():
                values = [str(int(row[col])) for col in train_df.columns]
                f.write(','.join(values) + '\n')
            
            # Test marker
            f.write(':test\n')
            
            # Test data
            for _, row in test_df.iterrows():
                values = [str(int(row[col])) for col in test_df.columns]
                f.write(','.join(values) + '\n')
        
        # Reinitialize manager with combined file
        manager_test = pyoccam.VBMManager()
        manager_test.initFromCommandLine([
            "pyoccam",
            str(combined_file),
            "TARGET"
        ])
        
        # Generate fit report with test data to get test confusion matrix
        fit_report = manager_test.generate_fit_report(best_model, "0")
        
        # Extract metrics from fit report
        metrics = extract_confusion_matrix_metrics(fit_report)
        
        # Save fit report for debugging
        fit_file = OUTPUT_DIR / f'fit_fold{fold}_sig{signature}.txt'
        with open(fit_file, 'w') as f:
            f.write(fit_report)
        
        if DEBUG_MODE:
            print(f"    📄 Saved fit report to {fit_file}")
            print(f"    🔍 CM: TN={metrics['tn']}, FP={metrics['fp']}, FN={metrics['fn']}, TP={metrics['tp']}")
        
        # Parse model structure
        model_structure = parse_ra_model_structure(best_model)
        
        results = {
            'model': best_model,
            'accuracy': metrics['accuracy'],
            'f1': metrics['f1'],
            'precision': metrics['precision'],
            'recall': metrics['recall'],
            'sensitivity': metrics['sensitivity'],
            'specificity': metrics['specificity'],
            'confusion_matrix': {
                'tn': metrics['tn'],
                'fp': metrics['fp'],
                'fn': metrics['fn'],
                'tp': metrics['tp']
            },
            'model_structure': model_structure,
            'search_report': search_report,
            'fit_report': fit_report
        }
        
        if metrics['accuracy']:
            print(f"    ✓ Test Accuracy: {metrics['accuracy']:.3f}")
            print(f"    ✓ CM: TN={metrics['tn']}, FP={metrics['fp']}, FN={metrics['fn']}, TP={metrics['tp']}")
        else:
            print(f"    ⚠ Could not extract test accuracy from fit report")
        
        return results
        
    except Exception as e:
        print(f"    ✗ RA analysis failed: {str(e)}")
        if DEBUG_MODE:
            import traceback
            traceback.print_exc()
        return None
    
    finally:
        # Cleanup
        for f in [train_file, test_file, combined_file]:
            if f.exists():
                try:
                    f.unlink()
                except:
                    pass


def run_ml_analysis(X_train, y_train, X_test, y_test, fold, signature='ALL'):
    """Run ML models and extract feature importance"""
    
    print(f"\n  🤖 Running ML analysis (Fold {fold}, Sig {signature})...")
    
    models = {
        'Logistic Regression': LogisticRegression(max_iter=1000, random_state=RANDOM_SEED),
        'Random Forest': RandomForestClassifier(n_estimators=100, random_state=RANDOM_SEED),
        'Gradient Boosting': GradientBoostingClassifier(n_estimators=100, random_state=RANDOM_SEED),
        'Decision Tree': DecisionTreeClassifier(max_depth=10, random_state=RANDOM_SEED)
    }
    
    results = {}
    
    for name, model in models.items():
        try:
            # Train
            model.fit(X_train, y_train)
            
            # Predict
            y_pred = model.predict(X_test)
            
            # Metrics
            acc = accuracy_score(y_test, y_pred)
            f1 = f1_score(y_test, y_pred, average='weighted', zero_division=0)
            prec = precision_score(y_test, y_pred, average='weighted', zero_division=0)
            rec = recall_score(y_test, y_pred, average='weighted', zero_division=0)
            
            result = {
                'accuracy': acc,
                'f1': f1,
                'precision': prec,
                'recall': rec,
                'predictions': y_pred,
                'model': model
            }
            
            # Feature importance for tree-based models
            if hasattr(model, 'feature_importances_'):
                importance_analysis = analyze_feature_importance_rf(
                    model, X_train.columns.tolist()
                )
                result['feature_importance'] = importance_analysis
            
            results[name] = result
            print(f"    ✓ {name}: {acc:.3f}")
            
        except Exception as e:
            print(f"    ✗ {name} failed: {str(e)}")
            results[name] = None
    
    return results


def analyze_by_signature(df, n_folds=5):
    """
    Run analysis partitioned by signature group.
    Returns results for each signature separately plus overall.
    """
    
    results = {
        'overall': {'RA': [], 'ML': []},
        'by_signature': {}
    }
    
    # Initialize signature results
    for sig in SIGNATURE_NAMES.keys():
        results['by_signature'][sig] = {'RA': [], 'ML': []}
    
    # Prepare features (vegetation columns - the ones with type=1 that are IVs)
    feature_cols = [col for col in df.columns if col.startswith(('in_d_l', 'mid_d_l', 'out_d_l'))]
    
    # Add elevation if present
    if 'elev_bin' in df.columns:
        feature_cols.append('elev_bin')
    
    print(f"\n📋 Using {len(feature_cols)} features: {', '.join(feature_cols[:10])}...")
    
    # Encode target - use LARGE_FIRE column (the DV column with type=2)
    if 'LARGE_FIRE' not in df.columns:
        print(f"ERROR: Target column 'LARGE_FIRE' not found!")
        print(f"Available columns: {df.columns.tolist()}")
        return results
    
    le = LabelEncoder()
    y = le.fit_transform(df['LARGE_FIRE'])
    
    # Get signature column for partitioning
    sig_col = 'pyrome_sig' if 'pyrome_sig' in df.columns else 'sig_grp'
    if sig_col not in df.columns:
        print(f"WARNING: No signature column found (looked for 'pyrome_sig' or 'sig_grp')")
        sig_col = None
    
    # === OVERALL ANALYSIS ===
    print(f"\n{'='*60}")
    print(f"OVERALL ANALYSIS (All Signatures Combined)")
    print(f"{'='*60}")
    
    X = df[feature_cols]
    skf = StratifiedKFold(n_splits=n_folds, shuffle=True, random_state=RANDOM_SEED)
    
    for fold, (train_idx, test_idx) in enumerate(skf.split(X, y), 1):
        print(f"\nFold {fold}/{n_folds}")
        
        X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
        y_train, y_test = y[train_idx], y[test_idx]
        
        # RA
        ra_results = run_pyoccam_analysis(X_train, y_train, X_test, y_test, fold, 'ALL')
        if ra_results:
            results['overall']['RA'].append(ra_results)
        
        # ML
        ml_results = run_ml_analysis(X_train, y_train, X_test, y_test, fold, 'ALL')
        results['overall']['ML'].append(ml_results)
        
        if TEST_MODE:
            break
    
    # === BY-SIGNATURE ANALYSIS ===
    if sig_col and sig_col in df.columns:
        for sig in SIGNATURE_NAMES.keys():
            print(f"\n{'='*60}")
            print(f"SIGNATURE {sig}: {SIGNATURE_NAMES[sig]}")
            print(f"{'='*60}")
            
            # Filter to this signature
            sig_df = df[df[sig_col] == sig]
            
            if len(sig_df) < 100:
                print(f"⚠ Skipping {sig} - only {len(sig_df)} samples")
                continue
            
            X_sig = sig_df[feature_cols]
            y_sig = le.transform(sig_df['LARGE_FIRE'])
            
            skf_sig = StratifiedKFold(n_splits=min(n_folds, 3), shuffle=True, random_state=RANDOM_SEED)
            
            for fold, (train_idx, test_idx) in enumerate(skf_sig.split(X_sig, y_sig), 1):
                print(f"\nSignature {sig} - Fold {fold}")
                
                X_train, X_test = X_sig.iloc[train_idx], X_sig.iloc[test_idx]
                y_train, y_test = y_sig[train_idx], y_sig[test_idx]
                
                # RA
                ra_results = run_pyoccam_analysis(X_train, y_train, X_test, y_test, fold, sig)
                if ra_results:
                    results['by_signature'][sig]['RA'].append(ra_results)
                
                # ML
                ml_results = run_ml_analysis(X_train, y_train, X_test, y_test, fold, sig)
                results['by_signature'][sig]['ML'].append(ml_results)
                
                if TEST_MODE:
                    break
    
    return results


def summarize_results(results):
    """Create comprehensive summary of all results"""
    
    print(f"\n{'='*60}")
    print(f"FINAL RESULTS SUMMARY")
    print(f"{'='*60}")
    
    # === OVERALL RESULTS ===
    print(f"\n📊 OVERALL (All Signatures):")
    print(f"{'-'*60}")
    
    # RA Overall
    ra_overall = results['overall']['RA']
    if ra_overall:
        accuracies = [r['accuracy'] for r in ra_overall if r['accuracy'] is not None]
        if accuracies:
            print(f"\n  RA (Reconstructability Analysis):")
            print(f"    Mean Accuracy: {np.mean(accuracies):.3f} ± {np.std(accuracies):.3f}")
            print(f"    Range: [{min(accuracies):.3f}, {max(accuracies):.3f}]")
            
            # Show model structure from first fold
            if ra_overall[0]['model_structure']:
                struct = ra_overall[0]['model_structure']
                print(f"    Temporal periods used: T-{struct['temporal_periods']}")
                print(f"    Includes elevation: {struct['includes_elevation']}")
    
    # ML Overall
    ml_overall = results['overall']['ML']
    if ml_overall:
        print(f"\n  ML Methods:")
        
        for method in ['Random Forest', 'Logistic Regression', 'Gradient Boosting', 'Decision Tree']:
            accuracies = []
            for fold_results in ml_overall:
                if fold_results and method in fold_results and fold_results[method]:
                    accuracies.append(fold_results[method]['accuracy'])
            
            if accuracies:
                print(f"    {method}:")
                print(f"      Mean Accuracy: {np.mean(accuracies):.3f} ± {np.std(accuracies):.3f}")
        
        # Feature importance from Random Forest
        print(f"\n  🌟 Feature Importance (Random Forest, Fold 1):")
        if ml_overall[0] and 'Random Forest' in ml_overall[0]:
            rf_result = ml_overall[0]['Random Forest']
            if rf_result and 'feature_importance' in rf_result:
                fi = rf_result['feature_importance']
                
                print(f"\n    Top 10 Features:")
                for feat in fi['top_features'][:10]:
                    print(f"      {feat['rank']:2d}. {feat['feature']:8s}  {feat['importance']:.4f}")
                
                print(f"\n    Temporal Importance:")
                for time in sorted(fi['temporal_importance'].keys()):
                    imp = fi['temporal_importance'][time]
                    print(f"      T-{time}: {imp:.4f}")
                
                print(f"\n    Ring Importance:")
                for ring in ['inner', 'middle', 'outer']:
                    if ring in fi['ring_importance']:
                        print(f"      {ring.capitalize():8s}: {fi['ring_importance'][ring]:.4f}")
    
    # === BY-SIGNATURE RESULTS ===
    print(f"\n{'='*60}")
    print(f"RESULTS BY SIGNATURE GROUP:")
    print(f"{'='*60}")
    
    for sig in SIGNATURE_NAMES.keys():
        if sig not in results['by_signature'] or not results['by_signature'][sig]['RA']:
            continue
        
        print(f"\n{sig}: {SIGNATURE_NAMES[sig]}")
        print(f"{'-'*60}")
        
        # RA
        ra_sig = results['by_signature'][sig]['RA']
        if ra_sig:
            accuracies = [r['accuracy'] for r in ra_sig if r['accuracy'] is not None]
            if accuracies:
                print(f"  RA: {np.mean(accuracies):.3f} ± {np.std(accuracies):.3f}")
        
        # ML
        ml_sig = results['by_signature'][sig]['ML']
        if ml_sig:
            for method in ['Random Forest']:
                accuracies = []
                for fold_results in ml_sig:
                    if fold_results and method in fold_results and fold_results[method]:
                        accuracies.append(fold_results[method]['accuracy'])
                
                if accuracies:
                    print(f"  {method}: {np.mean(accuracies):.3f} ± {np.std(accuracies):.3f}")
    
    # Save detailed results
    save_detailed_results(results)


def save_detailed_results(results):
    """Save detailed results to CSV files"""
    
    # Overall RA results
    ra_rows = []
    for fold, result in enumerate(results['overall']['RA'], 1):
        if result and result['accuracy']:
            row = {
                'Fold': fold,
                'Signature': 'ALL',
                'Accuracy': result['accuracy'],
                'F1': result.get('f1'),
                'Precision': result.get('precision'),
                'Recall': result.get('recall'),
                'Model': result['model'][:100],
                'TN': result['confusion_matrix']['tn'],
                'FP': result['confusion_matrix']['fp'],
                'FN': result['confusion_matrix']['fn'],
                'TP': result['confusion_matrix']['tp']
            }
            
            # Add model structure info
            if result['model_structure']:
                struct = result['model_structure']
                row['Temporal_Periods'] = str(struct['temporal_periods'])
                row['Uses_Elevation'] = struct['includes_elevation']
                row['Num_Components'] = struct['num_components']
            
            ra_rows.append(row)
    
    if ra_rows:
        ra_df = pd.DataFrame(ra_rows)
        ra_df.to_csv(OUTPUT_DIR / 'ra_results_overall.csv', index=False)
        print(f"\n✓ Saved RA results to ra_results_overall.csv")
    
    # ML results
    ml_rows = []
    for fold, fold_results in enumerate(results['overall']['ML'], 1):
        if fold_results:
            for method, result in fold_results.items():
                if result:
                    ml_rows.append({
                        'Fold': fold,
                        'Signature': 'ALL',
                        'Method': method,
                        'Accuracy': result['accuracy'],
                        'F1': result['f1'],
                        'Precision': result['precision'],
                        'Recall': result['recall']
                    })
    
    if ml_rows:
        ml_df = pd.DataFrame(ml_rows)
        ml_df.to_csv(OUTPUT_DIR / 'ml_results_overall.csv', index=False)
        print(f"✓ Saved ML results to ml_results_overall.csv")
    
    # By-signature results
    sig_rows = []
    for sig in SIGNATURE_NAMES.keys():
        if sig in results['by_signature']:
            # RA
            for fold, result in enumerate(results['by_signature'][sig]['RA'], 1):
                if result and result['accuracy']:
                    sig_rows.append({
                        'Fold': fold,
                        'Signature': sig,
                        'Method': 'RA',
                        'Accuracy': result['accuracy'],
                        'F1': result.get('f1')
                    })
            
            # ML
            for fold, fold_results in enumerate(results['by_signature'][sig]['ML'], 1):
                if fold_results:
                    for method, result in fold_results.items():
                        if result:
                            sig_rows.append({
                                'Fold': fold,
                                'Signature': sig,
                                'Method': method,
                                'Accuracy': result['accuracy'],
                                'F1': result['f1']
                            })
    
    if sig_rows:
        sig_df = pd.DataFrame(sig_rows)
        sig_df.to_csv(OUTPUT_DIR / 'results_by_signature.csv', index=False)
        print(f"✓ Saved signature results to results_by_signature.csv")


def main():
    """Main execution"""
    
    print(f"\n{'='*60}")
    print(f"WILDFIRE ANALYSIS: RA vs ML with Signature Partitioning")
    print(f"Version 7.1 - Fixed Confusion Matrix Parsing")
    print(f"{'='*60}")
    print(f"Mode: {'TEST (1 fold)' if TEST_MODE else f'FULL ({N_FOLDS} folds)'}")
    print(f"PyOccam: {'Available' if PYOCCAM_AVAILABLE else 'Not Available'}")
    
    # Load data
    df = load_and_prepare_data(INPUT_FILE)
    
    # Run analysis
    results = analyze_by_signature(df, n_folds=N_FOLDS)
    
    # Summarize
    summarize_results(results)
    
    print(f"\n{'='*60}")
    print(f"Analysis complete! Results saved to {OUTPUT_DIR}/")
    print(f"{'='*60}\n")


if __name__ == '__main__':
    main()
