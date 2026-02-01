#!/usr/bin/env python3
"""
Ensemble RA for WTNSY Landslides
================================

Runs ensemble RA workflow on stratified landslide data.
Follows established patterns from automated_regional_analysis_enhanced.py

Usage:
    python run_ensemble_wtnsy.py

Date: January 13, 2026
"""

import pandas as pd
import numpy as np
import yaml
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple
import warnings
warnings.filterwarnings('ignore')

# =============================================================================
# CONFIGURATION
# =============================================================================

PROJECT_PATH = Path(r'C:\projects\spatial_ra\landslides_RA')
STRATA_DIR = PROJECT_PATH / 'WTNSY_data' / 'preprocessed' / 'strata'
OUTPUT_DIR = Path(r'D:\projects\occam\wtnsy_ensemble_output')
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

PYOCCAM_PATH = Path(r'D:\projects\occam')

# Variable config
VARIABLE_CONFIG = PROJECT_PATH / 'wtnsy_variable_config.yaml'

# Strata to analyze
STRATA = {
    'volcanic': STRATA_DIR / 'WTNSY_volcanic_stratum.csv',
    'sedimentary': STRATA_DIR / 'WTNSY_sedimentary_stratum.csv'
}

# Target column
TARGET_COL = 'LS'

# Ensemble thresholds
MIN_FREQUENCY = 20
MIN_CONFIDENCE = 85.0
MIN_ACCURACY = 90.0
MAX_P_MARGIN = 0.05

# Ensemble search settings
SEARCH_TYPE = 'full-up'
SEARCH_LEVELS = 7
SEARCH_WIDTH = 5
MIN_SPECIALIST_ACCURACY = 0.68
MAX_SPECIALIST_COVER = 85.0

# Test fraction
TEST_SIZE = 0.30

RUN_TIMESTAMP = datetime.now().strftime('%Y%m%d_%H%M%S')

# =============================================================================
# SETUP
# =============================================================================

# Add PyOccam to path
if str(PYOCCAM_PATH) not in sys.path:
    sys.path.insert(0, str(PYOCCAM_PATH))

if str(PROJECT_PATH) not in sys.path:
    sys.path.insert(0, str(PROJECT_PATH))

# Import PyOccam
import pyoccam
from ensemble_ra import EnsembleRAClassifier
print(f"✓ PyOccam {pyoccam.__version__} loaded")

from sklearn.model_selection import train_test_split

# =============================================================================
# LOAD VARIABLE CONFIGURATION
# =============================================================================

print("\n" + "="*80)
print("LOADING VARIABLE CONFIGURATION")
print("="*80)

# Load YAML config
with open(VARIABLE_CONFIG, 'r') as f:
    VAR_CONFIG = yaml.safe_load(f)

# Build predictor columns and abbreviations
PREDICTOR_COLUMNS = []
VARIABLE_ABBREVS = {}

for var_name, config in VAR_CONFIG.items():
    if config.get('enabled', True):
        PREDICTOR_COLUMNS.append(var_name)
        VARIABLE_ABBREVS[var_name] = config.get('abbrev', var_name[:2])

print(f"  Loaded: {VARIABLE_CONFIG.name}")
print(f"  {len(PREDICTOR_COLUMNS)} variables enabled")

# Load rebinning map with ABSOLUTE path resolution
try:
    from rebinning_utils import get_rebinning_string
    
    REBINNING_MAP = {}
    for var_name, var_config in VAR_CONFIG.items():
        if not var_config.get('enabled', True):
            continue
        rebin_config_rel = var_config.get('rebinning_config')
        if rebin_config_rel:
            # Convert relative path to absolute using PROJECT_PATH
            rebin_config_abs = PROJECT_PATH / rebin_config_rel
            try:
                rebin_string = get_rebinning_string(str(rebin_config_abs))
                if rebin_string:
                    REBINNING_MAP[var_name] = rebin_string
                    print(f"    ✓ Loaded rebinning for {var_name}")
            except Exception as e:
                print(f"    ⚠️  Warning: Could not load rebinning for {var_name}: {e}")
    
    if REBINNING_MAP:
        print(f"  {len(REBINNING_MAP)} variables with rebinning")
except ImportError:
    print("  ⚠️  rebinning_utils not found, skipping rebinning")
    REBINNING_MAP = {}

print("="*80)

# =============================================================================
# FUNCTIONS (following landslides_spatial_cv_driver.py patterns)
# =============================================================================

def prepare_features(df: pd.DataFrame) -> Tuple[pd.DataFrame, np.ndarray]:
    """Extract features and target - handles NaN values properly."""
    # Use only enabled columns from YAML config
    predictor_cols = [col for col in PREDICTOR_COLUMNS if col in df.columns]
    
    if len(predictor_cols) != len(PREDICTOR_COLUMNS):
        missing = set(PREDICTOR_COLUMNS) - set(predictor_cols)
        print(f"  ⚠️  Warning: {len(missing)} predictor columns not found: {missing}")
    
    X = df[predictor_cols].copy()
    y = df[TARGET_COL].values
    
    # Handle missing values (same pattern as driver script)
    for col in X.columns:
        if X[col].isna().any():
            n_missing = X[col].isna().sum()
            if X[col].dtype == 'object' or X[col].nunique() < 20:
                mode_val = X[col].mode()[0] if len(X[col].mode()) > 0 else 0
                X[col] = X[col].fillna(mode_val)
            else:
                median_val = X[col].median()
                X[col] = X[col].fillna(median_val if not np.isnan(median_val) else 0)
            print(f"    Filled {n_missing} NaN in {col}")
    
    return X, y


def create_occam_file(X_train: pd.DataFrame, y_train: np.ndarray,
                     X_test: pd.DataFrame, y_test: np.ndarray,
                     output_file: Path) -> bool:
    """Create OCCAM format file with rebinning support."""
    try:
        feature_cols = X_train.columns.tolist()
        
        # Ensure integers
        X_train_int = X_train.astype(int)
        X_test_int = X_test.astype(int)
        
        with open(output_file, 'w') as f:
            f.write(':nominal\n')
            
            # Write feature variables
            for col in feature_cols:
                abbrev = VARIABLE_ABBREVS.get(col, col[:2])
                
                # Get cardinality from COMBINED train+test
                combined_values = np.concatenate([X_train_int[col].values, X_test_int[col].values])
                unique_values = np.unique(combined_values[~pd.isna(combined_values)])
                cardinality = len(unique_values)
                
                # Check for rebinning string
                rebin_str = REBINNING_MAP.get(col, '')
                if rebin_str:
                    f.write(f'{col},{cardinality},1,{abbrev},{rebin_str}\n')
                else:
                    f.write(f'{col},{cardinality},1,{abbrev}\n')
            
            # Write target variable
            f.write(f'{TARGET_COL},2,2,Z\n')
            
            # Write training data
            f.write(':data\n')
            for i in range(len(X_train_int)):
                row_vals = [str(X_train_int.iloc[i][col]) for col in feature_cols]
                row_vals.append(str(int(y_train[i])))
                f.write(' '.join(row_vals) + '\n')
            
            # Write test data
            f.write(':test\n')
            for i in range(len(X_test_int)):
                row_vals = [str(X_test_int.iloc[i][col]) for col in feature_cols]
                row_vals.append(str(int(y_test[i])))
                f.write(' '.join(row_vals) + '\n')
        
        return True
    
    except Exception as e:
        print(f"    ✗ Failed to create OCCAM file: {e}")
        return False


def run_ensemble_on_stratum(stratum_name: str, csv_path: Path) -> dict:
    """Run ensemble RA workflow on a single stratum."""
    
    print(f"\n{'='*80}")
    print(f"PROCESSING {stratum_name.upper()} STRATUM")
    print(f"{'='*80}")
    
    # Load data
    print(f"\nLoading data from {csv_path.name}...")
    df = pd.read_csv(csv_path)
    print(f"  Total samples: {len(df):,}")
    print(f"  Landslide rate: {df[TARGET_COL].mean()*100:.1f}%")
    
    # Prepare features (handles NaN)
    print("\nPreparing features...")
    X, y = prepare_features(df)
    print(f"  Features: {len(X.columns)}")
    print(f"  Samples: {len(X):,}")
    
    # Split train/test
    print(f"\nSplitting train/test ({1-TEST_SIZE:.0%}/{TEST_SIZE:.0%})...")
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=TEST_SIZE, random_state=42, stratify=y
    )
    print(f"  Train: {len(X_train):,} ({y_train.sum():,} LS, {y_train.mean()*100:.1f}%)")
    print(f"  Test:  {len(X_test):,} ({y_test.sum():,} LS, {y_test.mean()*100:.1f}%)")
    
    # Create OCCAM file
    occam_file = OUTPUT_DIR / f'occam_{stratum_name}_{RUN_TIMESTAMP}.txt'
    print(f"\nCreating OCCAM file: {occam_file.name}")
    
    if not create_occam_file(X_train, y_train, X_test, y_test, occam_file):
        return {'error': 'Failed to create OCCAM file'}
    
    # Load into PyOccam
    print("\nInitializing PyOccam...")
    data = pyoccam.load_data(str(occam_file))
    manager = data.manager
    print(f"  ✓ Loaded: {data.n_samples} samples, {data.n_features} features")
    
    # Create ensemble classifier
    print("\nCreating Ensemble RA Classifier...")
    ensemble = EnsembleRAClassifier(manager, dv_name='Z')
    ensemble.configure_thresholds(
        min_frequency=MIN_FREQUENCY,
        min_confidence=MIN_CONFIDENCE,
        min_accuracy=MIN_ACCURACY,
        max_p_margin=MAX_P_MARGIN
    )
    
    # Run ensemble workflow
    print(f"\nRunning ensemble workflow (levels={SEARCH_LEVELS}, width={SEARCH_WIDTH})...")
    ensemble.run_ensemble_workflow(
        search_type=SEARCH_TYPE,
        levels=SEARCH_LEVELS,
        width=SEARCH_WIDTH,
        min_specialist_accuracy=MIN_SPECIALIST_ACCURACY,
        max_specialist_cover=MAX_SPECIALIST_COVER
    )
    
    # Print summary
    print("\n" + ensemble.get_summary())
    
    # Export rules
    rules_file = OUTPUT_DIR / f'rules_{stratum_name}_{RUN_TIMESTAMP}.csv'
    ensemble.export_rules_csv(str(rules_file))
    
    # Save summary
    summary_file = OUTPUT_DIR / f'summary_{stratum_name}_{RUN_TIMESTAMP}.txt'
    with open(summary_file, 'w', encoding='utf-8') as f:
        f.write(ensemble.get_summary())
    print(f"\n✓ Saved: {summary_file.name}")
    
    return {
        'stratum': stratum_name,
        'base_model': ensemble.stats.base_model,
        'base_accuracy': ensemble.stats.base_model_accuracy,
        'n_rules': len(ensemble.rules),
        'total_coverage': sum(r.frequency for r in ensemble.rules.values()),
        'ensemble': ensemble
    }


# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    print("="*80)
    print("WTNSY LANDSLIDE ENSEMBLE RA ANALYSIS")
    print("="*80)
    print(f"\nTimestamp: {RUN_TIMESTAMP}")
    print(f"Output directory: {OUTPUT_DIR}")
    
    # Check input files
    print("\nChecking input files...")
    for stratum_name, stratum_file in STRATA.items():
        if stratum_file.exists():
            df = pd.read_csv(stratum_file)
            print(f"  ✓ {stratum_name:15s} {len(df):,} samples")
        else:
            print(f"  ✗ {stratum_name:15s} FILE NOT FOUND")
            sys.exit(1)
    
    # Run on each stratum
    results = {}
    
    for stratum_name, stratum_file in STRATA.items():
        try:
            results[stratum_name] = run_ensemble_on_stratum(stratum_name, stratum_file)
        except Exception as e:
            print(f"\n✗ Error processing {stratum_name}: {e}")
            import traceback
            traceback.print_exc()
            results[stratum_name] = {'error': str(e)}
    
    # Final summary
    print("\n" + "="*80)
    print("ANALYSIS COMPLETE")
    print("="*80)
    
    for stratum_name, result in results.items():
        print(f"\n{stratum_name.upper()}:")
        if 'error' in result:
            print(f"  Status: FAILED - {result['error']}")
        else:
            print(f"  Base model: {result['base_model']}")
            print(f"  Base accuracy: {result['base_accuracy']:.1f}%")
            print(f"  Specialist rules: {result['n_rules']}")
            print(f"  Samples covered: {result['total_coverage']:.0f}")
    
    print("\n" + "="*80)
    print(f"Output files in: {OUTPUT_DIR}")
    print("="*80 + "\n")
