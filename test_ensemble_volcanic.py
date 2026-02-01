"""
Quick Test: Run Ensemble RA on WTNSY Volcanic Stratum
A simplified version to verify the workflow works
"""

import pandas as pd
import numpy as np
import sys
sys.path.insert(0, r'D:\projects\occam')

import pyoccam
from ensemble_ra import EnsembleRAClassifier
from pathlib import Path
from datetime import datetime
from sklearn.model_selection import train_test_split

# ============================================================================
# CONFIGURATION
# ============================================================================

VOLCANIC_FILE = Path(r"C:\projects\spatial_ra\landslides_RA\WTNSY_data\preprocessed\strata\WTNSY_volcanic_stratum.csv")
OUTPUT_DIR = Path(r"D:\projects\occam\wtnsy_ensemble_output")
OUTPUT_DIR.mkdir(exist_ok=True)

# Use a smaller subset of top predictors for faster testing
TOP_VARIABLES = {
    'DEM_binned': ('El', 5),
    'slope_binned': ('Sl', 5),
    'NLCD_2021_encoded': ('Lc', 15),
    'taxsubgrp_encoded': ('Tb', 48),
    'taxpartsize_encoded': ('Tp', 17),
    'ThematicRo_encoded': ('Ro', 7),
}

DV_NAME = 'LS'
DV_ABBREV = 'Z'

# ============================================================================
# MAIN
# ============================================================================

print("="*80)
print("WTNSY VOLCANIC STRATUM - ENSEMBLE RA TEST")
print("="*80)

# Load data
print(f"\nLoading data from {VOLCANIC_FILE}...")
df = pd.read_csv(VOLCANIC_FILE)
print(f"  Total samples: {len(df)}")
print(f"  Landslide rate: {df['LS'].mean()*100:.1f}%")

# Filter to available variables
available_vars = {k: v for k, v in TOP_VARIABLES.items() if k in df.columns}
print(f"\nVariables to use: {list(available_vars.keys())}")

# Check for missing values in the columns we need
cols_to_use = list(available_vars.keys()) + ['LS']
print(f"\nChecking for missing values...")
for col in cols_to_use:
    n_missing = df[col].isna().sum()
    if n_missing > 0:
        print(f"  {col}: {n_missing} missing ({n_missing/len(df)*100:.1f}%)")

# Drop rows with any missing values in our columns
df_clean = df[cols_to_use].dropna()
print(f"\nAfter dropping NaN rows: {len(df_clean)} samples (dropped {len(df) - len(df_clean)})")
print(f"  Landslide rate: {df_clean['LS'].mean()*100:.1f}%")

# Subsample for quick test (optional - comment out for full run)
# df_clean = df_clean.sample(n=2000, random_state=42)
# print(f"  Subsampled to: {len(df_clean)}")

# Build OCCAM format
lines = [":nominal"]
var_order = []
for i, (col_name, (abbrev, card)) in enumerate(available_vars.items(), 1):
    actual_max = int(df_clean[col_name].max()) + 1
    actual_card = max(card, actual_max)
    lines.append(f"{col_name}, {actual_card}, 1, v{i:02d}")
    var_order.append(col_name)
lines.append(f"LS, 2, 2, Z")
lines.append(":no-frequency")

# Split train/test
train_df, test_df = train_test_split(df_clean, test_size=0.2, random_state=42, stratify=df_clean['LS'])

lines.append(":data")
for _, row in train_df.iterrows():
    values = [str(int(row[col])) for col in var_order] + [str(int(row['LS']))]
    lines.append(" ".join(values))

lines.append(":test")
for _, row in test_df.iterrows():
    values = [str(int(row[col])) for col in var_order] + [str(int(row['LS']))]
    lines.append(" ".join(values))

# Save OCCAM file
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
occam_file = OUTPUT_DIR / f"occam_volcanic_test_{timestamp}.txt"
with open(occam_file, 'w') as f:
    f.write("\n".join(lines))
print(f"\nCreated OCCAM file: {occam_file}")
print(f"  Training: {len(train_df)}, Test: {len(test_df)}")

# Load into PyOccam
print("\nLoading into PyOccam...")
data = pyoccam.load_data(str(occam_file))
manager = data.manager
print(f"  Loaded: {data.n_samples} samples, {data.n_features} features")

# Create ensemble
print("\nCreating Ensemble RA Classifier...")
ensemble = EnsembleRAClassifier(manager, dv_name='Z')
ensemble.configure_thresholds(
    min_frequency=15,      # n >= 15 for rule acceptance
    min_confidence=85.0,   # 85% confidence
    min_accuracy=90.0,     # 90% accuracy
    max_p_margin=0.05      # p < 0.05 significance
)

# Run ensemble workflow (conservative settings for test)
print("\nRunning ensemble workflow (levels=4, width=3)...")
ensemble.run_ensemble_workflow(
    search_type="full-up",
    levels=4,              # Limited for faster test
    width=3,
    min_specialist_accuracy=0.68,
    max_specialist_cover=85.0
)

# Results
print("\n" + ensemble.get_summary())

# Export
rules_file = OUTPUT_DIR / f"rules_volcanic_test_{timestamp}.csv"
ensemble.export_rules_csv(str(rules_file))
print(f"\nRules exported to: {rules_file}")
