#!/usr/bin/env python3
"""
Run full-up search with 5-fold cross-validation

For OCCAM to use CV, we need to create data files with :test markers
marking different folds as test data for each iteration.
"""

import pyoccam
import numpy as np
from pathlib import Path
import time

def run_occam_on_fold(data_file, search_type="full-up", levels=7, width=3):
    """
    Run OCCAM search and return confusion matrix
    
    Returns: dict with model info and confusion matrix
    """
    print(f"\n  Running {search_type} search (levels={levels}, width={width})...")
    
    # Initialize
    manager = pyoccam.VBMManager()
    manager.init_from_command_line(["occam", data_file])
    
    # Check if test data present
    has_test = manager.has_test_data()
    sample_size = manager.get_sample_size()
    
    print(f"  Sample size: {sample_size:.0f}")
    print(f"  Has test data: {has_test}")
    
    # Run search
    start_time = time.time()
    manager.generate_search_report(search_type, levels, width)
    elapsed = time.time() - start_time
    print(f"  Search completed in {elapsed:.2f}s")
    
    # Get best models
    best_bic = manager.get_best_model_by_bic()
    best_aic = manager.get_best_model_by_aic()
    best_info = manager.get_best_model_by_information()
    
    print(f"  Best by BIC: {best_bic}")
    print(f"  Best by AIC: {best_aic}")
    print(f"  Best by Information: {best_info}")
    
    # Use Information criterion (standard)
    best_model = best_info
    
    # Get confusion matrix
    print(f"  Getting confusion matrix for {best_model}...")
    cm = manager.get_confusion_matrix(best_model, "0")
    
    result = {
        'model': best_model,
        'best_bic': best_bic,
        'best_aic': best_aic,
        'best_info': best_info,
        'has_test_data': has_test,
        'sample_size': sample_size,
        'search_time': elapsed,
        'confusion_matrix': cm
    }
    
    return result

def print_cm_results(result, label=""):
    """Print confusion matrix results nicely"""
    cm = result['confusion_matrix']
    
    print(f"\n{'='*80}")
    print(f"{label}")
    print(f"{'='*80}")
    print(f"Model: {result['model']}")
    print(f"Has test data: {result['has_test_data']}")
    print(f"Sample size: {result['sample_size']:.0f}")
    print(f"Search time: {result['search_time']:.2f}s")
    print(f"\nConfusion Matrix:")
    print(f"                Predicted")
    print(f"                Neg    Pos")
    print(f"  Actual  Neg   {cm['tn']:3.0f}    {cm['fp']:3.0f}")
    print(f"          Pos   {cm['fn']:3.0f}    {cm['tp']:3.0f}")
    print(f"\nPerformance Metrics:")
    print(f"  Accuracy:    {cm['accuracy']:.3f} ({cm['accuracy']*100:.1f}%)")
    print(f"  Sensitivity: {cm['sensitivity']:.3f} (Recall/TPR)")
    print(f"  Specificity: {cm['specificity']:.3f} (TNR)")
    print(f"  Precision:   {cm['precision']:.3f} (PPV)")
    print(f"  F1 Score:    {cm['f1_score']:.3f}")
    print()

def create_cv_folds(data_file, n_folds=5, output_dir="cv_folds", seed=42):
    """
    Create n-fold CV splits with :test markers
    
    Returns: list of temporary data file paths
    """
    print(f"\nCreating {n_folds}-fold CV splits from {data_file}...")
    
    # Read the original data file
    with open(data_file, 'r') as f:
        lines = f.readlines()
    
    # Find where data starts (after cardinality lines)
    data_start_idx = 0
    for i, line in enumerate(lines):
        if line.strip() and not line.startswith(':') and ',' in line:
            # Check if this looks like a header or data line
            if not any(c.isdigit() for c in line.split(',')[0]):
                # Likely header
                data_start_idx = i
                break
    
    # Get header and data
    header_lines = lines[:data_start_idx+1]
    data_lines = lines[data_start_idx+1:]
    
    # Remove any existing :test markers
    data_lines = [line for line in data_lines if not line.strip().startswith(':test')]
    
    n_samples = len(data_lines)
    print(f"  Found {n_samples} data samples")
    
    # Create shuffled indices for CV
    np.random.seed(seed)
    indices = np.random.permutation(n_samples)
    
    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    fold_files = []
    fold_size = n_samples // n_folds
    
    for fold in range(n_folds):
        # Determine test indices for this fold
        test_start = fold * fold_size
        test_end = (fold + 1) * fold_size if fold < n_folds - 1 else n_samples
        test_indices = set(indices[test_start:test_end])
        
        print(f"  Fold {fold+1}: {len(test_indices)} test samples, {n_samples - len(test_indices)} train samples")
        
        # Create new data file with :test marker
        fold_filename = output_path / f"{Path(data_file).stem}_fold{fold+1}.txt"
        
        with open(fold_filename, 'w') as f:
            # Write header
            for line in header_lines:
                f.write(line)
            
            # Write data with :test markers
            for i, line in enumerate(data_lines):
                if i in test_indices:
                    f.write(':test\n')
                f.write(line)
        
        fold_files.append(str(fold_filename))
    
    print(f"  Created {len(fold_files)} fold files in {output_dir}/")
    return fold_files

def run_cross_validation(data_file, n_folds=5, search_type="full-up", levels=7, width=3):
    """
    Run n-fold cross-validation
    
    Returns: list of results for each fold
    """
    print(f"\n{'='*80}")
    print(f"RUNNING {n_folds}-FOLD CROSS-VALIDATION")
    print(f"{'='*80}")
    print(f"Dataset: {data_file}")
    print(f"Search: {search_type} (levels={levels}, width={width})")
    
    # Create CV folds
    fold_files = create_cv_folds(data_file, n_folds=n_folds)
    
    # Run OCCAM on each fold
    results = []
    for i, fold_file in enumerate(fold_files):
        print(f"\n{'='*80}")
        print(f"FOLD {i+1}/{n_folds}")
        print(f"{'='*80}")
        
        result = run_occam_on_fold(fold_file, search_type, levels, width)
        result['fold'] = i + 1
        results.append(result)
        
        # Print summary
        cm = result['confusion_matrix']
        print(f"\n  Fold {i+1} Results:")
        print(f"    Model: {result['model']}")
        print(f"    Accuracy: {cm['accuracy']:.3f}")
        print(f"    F1 Score: {cm['f1_score']:.3f}")
    
    return results

def summarize_cv_results(results):
    """Calculate and print CV summary statistics"""
    print(f"\n{'='*80}")
    print(f"CROSS-VALIDATION SUMMARY")
    print(f"{'='*80}")
    
    # Extract metrics
    accuracies = [r['confusion_matrix']['accuracy'] for r in results]
    sensitivities = [r['confusion_matrix']['sensitivity'] for r in results]
    specificities = [r['confusion_matrix']['specificity'] for r in results]
    precisions = [r['confusion_matrix']['precision'] for r in results]
    f1_scores = [r['confusion_matrix']['f1_score'] for r in results]
    
    print(f"\nMetrics across {len(results)} folds:")
    print(f"{'Metric':<20} {'Mean':<10} {'Std':<10} {'Min':<10} {'Max':<10}")
    print(f"{'-'*60}")
    
    for name, values in [
        ('Accuracy', accuracies),
        ('Sensitivity', sensitivities),
        ('Specificity', specificities),
        ('Precision', precisions),
        ('F1 Score', f1_scores)
    ]:
        mean_val = np.mean(values)
        std_val = np.std(values)
        min_val = np.min(values)
        max_val = np.max(values)
        print(f"{name:<20} {mean_val:.3f}      {std_val:.3f}      {min_val:.3f}      {max_val:.3f}")
    
    # Show models selected in each fold
    print(f"\nModels selected by fold:")
    for r in results:
        print(f"  Fold {r['fold']}: {r['model']}")
    
    print()

# =============================================================================
# MAIN SCRIPT
# =============================================================================

if __name__ == "__main__":
    print("="*80)
    print("OCCAM FULL-UP SEARCH WITH CROSS-VALIDATION")
    print("="*80)
    
    # Configuration
    SEARCH_TYPE = "full-up"
    LEVELS = 7
    WIDTH = 3
    N_FOLDS = 5
    
    print(f"\nConfiguration:")
    print(f"  Search type: {SEARCH_TYPE}")
    print(f"  Levels: {LEVELS}")
    print(f"  Width: {WIDTH}")
    print(f"  CV folds: {N_FOLDS}")
    
    # =========================================================================
    # OPTION 1: Single run on existing data (if it has :test marker)
    # =========================================================================
    
    print(f"\n{'='*80}")
    print("PART 1: SINGLE RUN ON EXISTING DATASETS")
    print(f"{'='*80}")
    
    # Dementia dataset (no test data)
    print("\n--- DEMENTIA DATASET ---")
    dementia_result = run_occam_on_fold("dementia05.txt", SEARCH_TYPE, LEVELS, WIDTH)
    print_cm_results(dementia_result, "DEMENTIA05 RESULTS")
    
    # Landslides dataset (has test data)
    print("\n--- LANDSLIDES DATASET ---")
    landslides_result = run_occam_on_fold(
        "SY_sample_pts_to_occam3_shuffle_split42_hdr.txt", 
        SEARCH_TYPE, LEVELS, WIDTH
    )
    print_cm_results(landslides_result, "LANDSLIDES RESULTS")
    
    # =========================================================================
    # OPTION 2: 5-fold Cross-Validation
    # =========================================================================
    
    print(f"\n{'='*80}")
    print("PART 2: 5-FOLD CROSS-VALIDATION")
    print(f"{'='*80}")
    
    # Choose which dataset to run CV on
    print("\nRunning 5-fold CV on dementia dataset...")
    dementia_cv_results = run_cross_validation(
        "dementia05.txt", 
        n_folds=N_FOLDS,
        search_type=SEARCH_TYPE,
        levels=LEVELS,
        width=WIDTH
    )
    summarize_cv_results(dementia_cv_results)
    
    print("\nRunning 5-fold CV on landslides dataset...")
    landslides_cv_results = run_cross_validation(
        "SY_sample_pts_to_occam3_shuffle_split42_hdr.txt",
        n_folds=N_FOLDS,
        search_type=SEARCH_TYPE,
        levels=LEVELS,
        width=WIDTH
    )
    summarize_cv_results(landslides_cv_results)
    
    # =========================================================================
    # FINAL SUMMARY
    # =========================================================================
    
    print(f"\n{'='*80}")
    print("COMPLETE SUMMARY")
    print(f"{'='*80}")
    print(f"\nSingle Run Results:")
    print(f"  Dementia:   Accuracy = {dementia_result['confusion_matrix']['accuracy']:.3f}")
    print(f"  Landslides: Accuracy = {landslides_result['confusion_matrix']['accuracy']:.3f}")
    
    print(f"\n5-Fold CV Results (Mean ± Std):")
    dem_acc = [r['confusion_matrix']['accuracy'] for r in dementia_cv_results]
    lan_acc = [r['confusion_matrix']['accuracy'] for r in landslides_cv_results]
    print(f"  Dementia:   {np.mean(dem_acc):.3f} ± {np.std(dem_acc):.3f}")
    print(f"  Landslides: {np.mean(lan_acc):.3f} ± {np.std(lan_acc):.3f}")
    
    print(f"\n✓ All analyses complete!")
    print()
