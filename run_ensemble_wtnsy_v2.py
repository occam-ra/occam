#!/usr/bin/env python3
"""
Ensemble RA for WTNSY Landslides - Version 2
=============================================

Enhanced version with:
- Full search report saving
- Custom base model selection
- Model ranking by accuracy vs coverage
- Practitioner-friendly rule export

Usage:
    python run_ensemble_wtnsy_v2.py                    # Run full workflow
    python run_ensemble_wtnsy_v2.py --search-only     # Just search, show all models
    python run_ensemble_wtnsy_v2.py --base IV:ElZ:ClZ:RoZ  # Custom base model

Date: January 13, 2026
"""

import pandas as pd
import numpy as np
import yaml
import sys
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Optional
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
from ensemble_ra import EnsembleRAClassifier, SearchOutputParser
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
# FUNCTIONS
# =============================================================================

def prepare_features(df: pd.DataFrame) -> Tuple[pd.DataFrame, np.ndarray]:
    """Extract features and target - handles NaN values properly."""
    predictor_cols = [col for col in PREDICTOR_COLUMNS if col in df.columns]
    
    if len(predictor_cols) != len(PREDICTOR_COLUMNS):
        missing = set(PREDICTOR_COLUMNS) - set(predictor_cols)
        print(f"  ⚠️  Warning: {len(missing)} predictor columns not found: {missing}")
    
    X = df[predictor_cols].copy()
    y = df[TARGET_COL].values
    
    # Handle missing values
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
        X_train_int = X_train.astype(int)
        X_test_int = X_test.astype(int)
        
        with open(output_file, 'w') as f:
            f.write(':nominal\n')
            
            for col in feature_cols:
                abbrev = VARIABLE_ABBREVS.get(col, col[:2])
                combined_values = np.concatenate([X_train_int[col].values, X_test_int[col].values])
                unique_values = np.unique(combined_values[~pd.isna(combined_values)])
                cardinality = len(unique_values)
                
                rebin_str = REBINNING_MAP.get(col, '')
                if rebin_str:
                    f.write(f'{col},{cardinality},1,{abbrev},{rebin_str}\n')
                else:
                    f.write(f'{col},{cardinality},1,{abbrev}\n')
            
            f.write(f'{TARGET_COL},2,2,Z\n')
            
            f.write(':data\n')
            for i in range(len(X_train_int)):
                row_vals = [str(X_train_int.iloc[i][col]) for col in feature_cols]
                row_vals.append(str(int(y_train[i])))
                f.write(' '.join(row_vals) + '\n')
            
            f.write(':test\n')
            for i in range(len(X_test_int)):
                row_vals = [str(X_test_int.iloc[i][col]) for col in feature_cols]
                row_vals.append(str(int(y_test[i])))
                f.write(' '.join(row_vals) + '\n')
        
        return True
    
    except Exception as e:
        print(f"    ✗ Failed to create OCCAM file: {e}")
        return False


def format_model_table(models: list, top_n: int = 30) -> str:
    """Format models as a nice table sorted by accuracy."""
    lines = []
    lines.append("\n" + "="*100)
    lines.append("ALL MODELS RANKED BY ACCURACY (with coverage)")
    lines.append("="*100)
    lines.append(f"{'Rank':<5} {'Model':<40} {'Accuracy':>10} {'Coverage':>10} {'dBIC':>10} {'Level':>6}")
    lines.append("-"*100)
    
    # Sort by accuracy descending
    sorted_models = sorted(models, key=lambda m: m.pct_correct_data, reverse=True)
    
    for i, m in enumerate(sorted_models[:top_n], 1):
        lines.append(f"{i:<5} {m.name:<40} {m.pct_correct_data:>9.1f}% {m.pct_cover:>9.1f}% {m.dbic:>10.2f} {m.level:>6}")
    
    if len(sorted_models) > top_n:
        lines.append(f"... and {len(sorted_models) - top_n} more models")
    
    return "\n".join(lines)


def format_coverage_accuracy_tradeoff(models: list) -> str:
    """Show the coverage vs accuracy tradeoff."""
    lines = []
    lines.append("\n" + "="*100)
    lines.append("COVERAGE vs ACCURACY TRADEOFF (Pareto frontier candidates)")
    lines.append("="*100)
    lines.append(f"{'Model':<45} {'Accuracy':>10} {'Coverage':>10} {'Acc×Cov':>12}")
    lines.append("-"*100)
    
    # Find Pareto-optimal models (not dominated by another in both dimensions)
    pareto = []
    for m in models:
        dominated = False
        for other in models:
            if (other.pct_correct_data > m.pct_correct_data and 
                other.pct_cover >= m.pct_cover):
                dominated = True
                break
            if (other.pct_cover > m.pct_cover and 
                other.pct_correct_data >= m.pct_correct_data):
                dominated = True
                break
        if not dominated:
            pareto.append(m)
    
    # Sort by coverage
    pareto.sort(key=lambda m: m.pct_cover, reverse=True)
    
    for m in pareto[:20]:
        score = m.pct_correct_data * m.pct_cover / 100
        lines.append(f"{m.name:<45} {m.pct_correct_data:>9.1f}% {m.pct_cover:>9.1f}% {score:>11.1f}")
    
    return "\n".join(lines)


def run_search_only(stratum_name: str, csv_path: Path) -> dict:
    """Run just the search phase to explore all models."""
    
    print(f"\n{'='*80}")
    print(f"SEARCH ANALYSIS: {stratum_name.upper()} STRATUM")
    print(f"{'='*80}")
    
    # Load data
    print(f"\nLoading data from {csv_path.name}...")
    df = pd.read_csv(csv_path)
    print(f"  Total samples: {len(df):,}")
    print(f"  Landslide rate: {df[TARGET_COL].mean()*100:.1f}%")
    
    # Prepare features
    print("\nPreparing features...")
    X, y = prepare_features(df)
    
    # Split train/test
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=TEST_SIZE, random_state=42, stratify=y
    )
    print(f"  Train: {len(X_train):,}, Test: {len(X_test):,}")
    
    # Create OCCAM file
    occam_file = OUTPUT_DIR / f'occam_{stratum_name}_search_{RUN_TIMESTAMP}.txt'
    create_occam_file(X_train, y_train, X_test, y_test, occam_file)
    
    # Load into PyOccam
    print("\nInitializing PyOccam...")
    data = pyoccam.load_data(str(occam_file))
    manager = data.manager
    
    # Run search
    print(f"\nRunning {SEARCH_TYPE} search (levels={SEARCH_LEVELS}, width={SEARCH_WIDTH})...")
    search_output = manager.generate_search_report(SEARCH_TYPE, SEARCH_LEVELS, SEARCH_WIDTH)
    
    # Save full search report
    search_file = OUTPUT_DIR / f'search_{stratum_name}_{RUN_TIMESTAMP}.txt'
    with open(search_file, 'w', encoding='utf-8') as f:
        f.write(search_output)
    print(f"✓ Saved search report: {search_file.name}")
    
    # Parse results
    parser = SearchOutputParser()
    models, best_models = parser.parse(search_output)
    
    print(f"\nFound {len(models)} models")
    print(f"  Best by BIC: {best_models.get('bic', 'N/A')}")
    print(f"  Best by AIC: {best_models.get('aic', 'N/A')}")
    print(f"  Best by Information: {best_models.get('information', 'N/A')}")
    
    # Show model tables
    print(format_model_table(models))
    print(format_coverage_accuracy_tradeoff(models))
    
    # Save model summary
    summary_file = OUTPUT_DIR / f'models_{stratum_name}_{RUN_TIMESTAMP}.txt'
    with open(summary_file, 'w', encoding='utf-8') as f:
        f.write(f"SEARCH ANALYSIS: {stratum_name.upper()}\n")
        f.write(f"Timestamp: {RUN_TIMESTAMP}\n")
        f.write(f"Samples: {len(df):,} ({df[TARGET_COL].mean()*100:.1f}% landslides)\n\n")
        f.write(f"Best by BIC: {best_models.get('bic', 'N/A')}\n")
        f.write(f"Best by AIC: {best_models.get('aic', 'N/A')}\n")
        f.write(f"Best by Information: {best_models.get('information', 'N/A')}\n")
        f.write(format_model_table(models, top_n=50))
        f.write("\n\n")
        f.write(format_coverage_accuracy_tradeoff(models))
    print(f"✓ Saved model summary: {summary_file.name}")
    
    return {
        'models': models,
        'best_models': best_models,
        'manager': manager,
        'occam_file': occam_file
    }


def run_ensemble_with_custom_base(stratum_name: str, csv_path: Path,
                                   custom_base: Optional[str] = None) -> dict:
    """Run ensemble RA workflow with optional custom base model."""
    
    print(f"\n{'='*80}")
    print(f"PROCESSING {stratum_name.upper()} STRATUM")
    if custom_base:
        print(f"  Custom base model: {custom_base}")
    print(f"{'='*80}")
    
    # Load data
    print(f"\nLoading data from {csv_path.name}...")
    df = pd.read_csv(csv_path)
    print(f"  Total samples: {len(df):,}")
    print(f"  Landslide rate: {df[TARGET_COL].mean()*100:.1f}%")
    
    # Prepare features
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
    
    # Run search first to get all models
    print(f"\nRunning {SEARCH_TYPE} search (levels={SEARCH_LEVELS}, width={SEARCH_WIDTH})...")
    search_output = manager.generate_search_report(SEARCH_TYPE, SEARCH_LEVELS, SEARCH_WIDTH)
    
    # Save full search report
    search_file = OUTPUT_DIR / f'search_{stratum_name}_{RUN_TIMESTAMP}.txt'
    with open(search_file, 'w', encoding='utf-8') as f:
        f.write(search_output)
    print(f"✓ Saved search report: {search_file.name}")
    
    # Parse search results
    parser = SearchOutputParser()
    models, best_models = parser.parse(search_output)
    print(f"  Found {len(models)} models")
    
    # Save model ranking
    models_file = OUTPUT_DIR / f'models_{stratum_name}_{RUN_TIMESTAMP}.txt'
    with open(models_file, 'w', encoding='utf-8') as f:
        f.write(format_model_table(models, top_n=50))
        f.write("\n\n")
        f.write(format_coverage_accuracy_tradeoff(models))
    print(f"✓ Saved model ranking: {models_file.name}")
    
    # Create ensemble classifier
    print("\nCreating Ensemble RA Classifier...")
    ensemble = EnsembleRAClassifier(manager, dv_name='Z')
    ensemble.configure_thresholds(
        min_frequency=MIN_FREQUENCY,
        min_confidence=MIN_CONFIDENCE,
        min_accuracy=MIN_ACCURACY,
        max_p_margin=MAX_P_MARGIN
    )
    
    # Store search results in ensemble
    ensemble.search_models = models
    ensemble.best_models = best_models
    
    # Determine base model
    if custom_base:
        # Verify custom base exists in search results
        valid_names = [m.name for m in models]
        if custom_base in valid_names:
            ensemble.base_model = custom_base
            base_data = next(m for m in models if m.name == custom_base)
            ensemble.stats.base_model = custom_base
            ensemble.stats.base_model_accuracy = base_data.pct_correct_data
            ensemble.stats.base_model_cover = base_data.pct_cover
            print(f"  Using custom base model: {custom_base}")
            print(f"    Accuracy: {base_data.pct_correct_data:.1f}%")
            print(f"    Coverage: {base_data.pct_cover:.1f}%")
        else:
            print(f"  ⚠️  Custom base '{custom_base}' not found in search results!")
            print(f"  Falling back to BIC-best...")
            custom_base = None
    
    if not custom_base:
        # Use BIC-best as default
        ensemble.base_model = best_models.get('bic', best_models.get('aic', ''))
        if not ensemble.base_model and models:
            ensemble.base_model = min(models, key=lambda m: m.dbic).name
        
        base_data = next((m for m in models if m.name == ensemble.base_model), None)
        if base_data:
            ensemble.stats.base_model = ensemble.base_model
            ensemble.stats.base_model_accuracy = base_data.pct_correct_data
            ensemble.stats.base_model_cover = base_data.pct_cover
    
    print(f"\nBase model: {ensemble.base_model}")
    
    # Find specialists
    specialists = []
    for model in models:
        if model.name == ensemble.base_model:
            continue
        if model.name == 'IV:Z' or model.level == 0:
            continue
        if (model.pct_correct_data >= MIN_SPECIALIST_ACCURACY * 100 and 
            model.pct_cover <= MAX_SPECIALIST_COVER):
            specialists.append(model)
    
    specialists.sort(key=lambda m: m.pct_correct_data, reverse=True)
    ensemble.stats.n_specialists = len(specialists)
    ensemble.stats.specialists = [s.name for s in specialists]
    
    print(f"\nFound {len(specialists)} specialist models to mine")
    for s in specialists[:10]:
        print(f"   {s.name}: acc={s.pct_correct_data:.1f}%, cover={s.pct_cover:.1f}%")
    if len(specialists) > 10:
        print(f"   ... and {len(specialists) - 10} more")
    
    # Mine rules from specialists
    print("\nMining rules from specialists...")
    total_rules = 0
    for specialist in specialists:
        try:
            fit_report = manager.generate_fit_report(specialist.name, target_state="0")
            n_rules = ensemble._mine_rules_from_fit(fit_report, specialist.name)
            if n_rules > 0:
                print(f"   {specialist.name}: +{n_rules} rules")
            total_rules += n_rules
        except Exception as e:
            print(f"   {specialist.name}: Error - {e}")
    
    ensemble.stats.n_rules_total = total_rules
    ensemble.stats.n_rules_accepted = len(ensemble.rules)
    
    # Load base model for fallback
    print(f"\nLoading base model rules for fallback...")
    try:
        base_fit = manager.generate_fit_report(ensemble.base_model, target_state="0")
        base_rules = ensemble.fit_parser.parse_fit_report(base_fit, ensemble.base_model)
        ensemble.base_model_rules = {r.iv_key(): r for r in base_rules}
        print(f"   Base model has {len(ensemble.base_model_rules)} state combinations")
    except Exception as e:
        print(f"   Could not load base model: {e}")
    
    print("\nWorkflow complete!")
    print(f"   Total specialist rules: {len(ensemble.rules)}")
    
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
        'base_coverage': ensemble.stats.base_model_cover,
        'n_rules': len(ensemble.rules),
        'total_coverage': sum(r.frequency for r in ensemble.rules.values()),
        'ensemble': ensemble,
        'all_models': models
    }


# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Ensemble RA for WTNSY Landslides')
    parser.add_argument('--search-only', action='store_true', 
                       help='Run search only, show all models without mining rules')
    parser.add_argument('--base', type=str, default=None,
                       help='Custom base model (e.g., IV:ElZ:ClZ:RoZ)')
    parser.add_argument('--stratum', type=str, default=None,
                       choices=['volcanic', 'sedimentary'],
                       help='Process only one stratum')
    args = parser.parse_args()
    
    print("="*80)
    print("WTNSY LANDSLIDE ENSEMBLE RA ANALYSIS v2")
    print("="*80)
    print(f"\nTimestamp: {RUN_TIMESTAMP}")
    print(f"Output directory: {OUTPUT_DIR}")
    
    if args.search_only:
        print("\n*** SEARCH-ONLY MODE ***")
    if args.base:
        print(f"\n*** CUSTOM BASE MODEL: {args.base} ***")
    
    # Determine which strata to process
    strata_to_process = STRATA
    if args.stratum:
        strata_to_process = {args.stratum: STRATA[args.stratum]}
    
    # Check input files
    print("\nChecking input files...")
    for stratum_name, stratum_file in strata_to_process.items():
        if stratum_file.exists():
            df = pd.read_csv(stratum_file)
            print(f"  ✓ {stratum_name:15s} {len(df):,} samples")
        else:
            print(f"  ✗ {stratum_name:15s} FILE NOT FOUND")
            sys.exit(1)
    
    # Run analysis
    results = {}
    
    for stratum_name, stratum_file in strata_to_process.items():
        try:
            if args.search_only:
                results[stratum_name] = run_search_only(stratum_name, stratum_file)
            else:
                results[stratum_name] = run_ensemble_with_custom_base(
                    stratum_name, stratum_file, custom_base=args.base
                )
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
        elif args.search_only:
            print(f"  Models found: {len(result.get('models', []))}")
            print(f"  BIC best: {result.get('best_models', {}).get('bic', 'N/A')}")
        else:
            print(f"  Base model: {result['base_model']}")
            print(f"  Base accuracy: {result['base_accuracy']:.1f}%")
            print(f"  Base coverage: {result.get('base_coverage', 0):.1f}%")
            print(f"  Specialist rules: {result['n_rules']}")
            print(f"  Samples covered: {result['total_coverage']:.0f}")
    
    print("\n" + "="*80)
    print(f"Output files in: {OUTPUT_DIR}")
    print("="*80 + "\n")
