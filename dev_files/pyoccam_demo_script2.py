#!/usr/bin/env python3
"""
PyOccam Demo - Clean Implementation
Demonstrates search, fit, and analysis workflow using built-in or custom data

Built-in datasets available:
  - dementia:   Alzheimer's/dementia risk factors (424 samples, 18 features)
  - landslides: Geological hazard prediction (1277 samples, 5 features)

Usage:
  python pyoccam_demo.py              # Interactive mode
  python pyoccam_demo.py demo         # Quick demo with both datasets
  python pyoccam_demo.py dementia     # Analyze dementia dataset
  python pyoccam_demo.py landslides   # Analyze landslides dataset
  python pyoccam_demo.py mydata.txt   # Analyze your own data
"""

import pyoccam
import os
from datetime import datetime

# ==============================================================================
# CONFIGURATION
# ==============================================================================

# Default settings (can be overridden by command-line arguments)
DEFAULT_DATASET = "fire_data_split_all_signature_groups_nlcd_rebinned.txt"            # Options: "dementia", "landslides", or path to file
SEARCH_TYPE = "loopless-up"            # Options: loopless-up, full-up, disjoint-up, chain-up  
SEARCH_LEVELS = 7                      # Search depth
SEARCH_WIDTH = 3                       # Beam width
OUTPUT_DIR = "occam_output"            # Output directory

# ==============================================================================
# MAIN WORKFLOW
# ==============================================================================

def run_occam_analysis(data_source=DEFAULT_DATASET, 
                       search_type=SEARCH_TYPE,
                       search_levels=SEARCH_LEVELS, 
                       search_width=SEARCH_WIDTH,
                       custom_model=None,
                       save_output=True):
    """
    Run complete OCCAM analysis workflow
    
    Args:
        data_source: "dementia", "landslides", or path to custom data file
        search_type: Type of search algorithm
        search_levels: Number of levels to search
        search_width: Beam width for search
        custom_model: Optional custom model string to fit (e.g., "IV:ApSxZ:EdZ:CZ")
        save_output: Whether to save results to files
    
    Returns:
        tuple: (data_object, manager, search_report, fit_report, best_model)
    """
    
    print("=" * 70)
    print("🚀 PyOccam Analysis")
    print("=" * 70)
    
    # 1. Load Data
    print(f"\n📁 Loading data: {data_source}")
    
    # Check if using built-in dataset or custom file
    if data_source.lower() == "dementia":
        data = pyoccam.load_dementia()
        dataset_name = "Dementia (built-in)"
    elif data_source.lower() == "landslides":
        data = pyoccam.load_landslides()
        dataset_name = "Landslides (built-in)"
    else:
        # Load custom data file
        if not os.path.exists(data_source):
            print(f"❌ Error: File not found: {data_source}")
            return None, None, None, None, None
        data = pyoccam.load_data(data_source)
        dataset_name = os.path.basename(data_source)
    
    # Get manager from data object
    manager = data.manager
    
    print(f"✓ Dataset: {dataset_name}")
    print(f"✓ Samples: {data.n_samples}")
    print(f"✓ Features: {data.n_features}")
    print(f"✓ Target: {data.target_name}")
    
    # Display feature names
    if hasattr(data, 'feature_names') and data.feature_names:
        print(f"✓ Variables: {', '.join(data.feature_names[:5])}...")
    
    # 2. Configure Search
    print(f"\n🔍 Performing {search_type} search")
    print(f"   Levels: {search_levels}, Width: {search_width}")
    
    # Set report variables (excluding ID and Model for cleaner output)
    manager.set_report_variables("Level$I, h, ddf, dLR, Alpha, %C, %dH(DV), dAIC, dBIC")
    
    # 3. Run Search
    search_report = manager.generate_search_report(
        search_type=search_type,
        levels=search_levels,
        width=search_width,
        include_test_data=False
    )
    
    # Extract best model
    best_model = manager.get_best_model_by_bic()
    
    if best_model:
        print(f"\n✨ Best model found: {best_model}")
        
        # Parse BIC improvement and percent correct from search results
        for line in search_report.split('\n'):
            if best_model in line and 'dBIC' in search_report:
                parts = line.split()
                if len(parts) >= 11:  # Need at least 11 parts with %C included
                    try:
                        # Typical order: ID Model Level h ddf dLR Alpha %C %dH(DV) dAIC dBIC
                        percent_correct = float(parts[7])  # %C position
                        dbic = float(parts[10])  # dBIC position
                        print(f"   Percent correct: {percent_correct:.2f}%")
                        print(f"   BIC improvement: {dbic:.4f}")
                    except:
                        pass
                break
    else:
        print("⚠️ No best model found in search")
    
    # 4. Fit Model (best model or custom)
    fit_report = ""
    model_to_fit = custom_model if custom_model else best_model
    
    if model_to_fit:
        print(f"\n📊 Fitting model: {model_to_fit}")
        fit_report = manager.generate_fit_report(
            model_to_fit,
            use_ipf_start=False,
            skip_trained_model_table=False,
            skip_ivi_tables=False
        )
        
        # Extract key statistics
        if "Percent Correct" in fit_report:
            for line in fit_report.split('\n'):
                if "Percent Correct" in line:
                    print(f"   {line.strip()}")
                    break
    
    # 5. Save Results
    if save_output:
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save search report
        search_file = os.path.join(OUTPUT_DIR, f"search_{search_type}_{timestamp}.txt")
        with open(search_file, 'w') as f:
            f.write(search_report)
        print(f"\n💾 Saved search report: {search_file}")
        
        # Save fit report
        if fit_report:
            fit_file = os.path.join(OUTPUT_DIR, f"fit_{model_to_fit.replace(':', '_')}_{timestamp}.txt")
            with open(fit_file, 'w') as f:
                f.write(fit_report)
            print(f"💾 Saved fit report: {fit_file}")
    
    print("\n✅ Analysis complete!")
    print("=" * 70)
    
    return data, manager, search_report, fit_report, best_model


def interactive_mode():
    """Run in interactive mode with user prompts"""
    
    print("\n🎯 PyOccam Interactive Mode")
    print("-" * 40)
    
    # Choose data source
    print("\nAvailable datasets:")
    print("  1. dementia   - Built-in dementia dataset")
    print("  2. landslides - Built-in landslides dataset")
    print("  3. custom     - Use your own data file")
    
    choice = input("\nSelect dataset [1/2/3 or dementia/landslides/filename]: ").strip()
    
    # Determine data source
    if choice in ['1', 'dementia']:
        data_source = "dementia"
    elif choice in ['2', 'landslides']:
        data_source = "landslides"
    else:
        # Get custom file path
        if choice == '3' or choice == 'custom':
            data_source = input("Enter path to your data file: ").strip()
        else:
            data_source = choice  # Assume they entered a filename
        
        if not os.path.exists(data_source):
            print(f"❌ File not found: {data_source}")
            return
    
    # Get search parameters
    print("\nSearch types: loopless-up, full-up, disjoint-up, chain-up")
    search_type = input(f"Search type [{SEARCH_TYPE}]: ").strip() or SEARCH_TYPE
    
    try:
        levels = input(f"Search levels [{SEARCH_LEVELS}]: ").strip()
        search_levels = int(levels) if levels else SEARCH_LEVELS
        
        width = input(f"Search width [{SEARCH_WIDTH}]: ").strip()
        search_width = int(width) if width else SEARCH_WIDTH
    except ValueError:
        print("❌ Invalid number, using defaults")
        search_levels = SEARCH_LEVELS
        search_width = SEARCH_WIDTH
    
    # Run initial analysis
    data, manager, search_report, fit_report, best_model = run_occam_analysis(
        data_source=data_source,
        search_type=search_type,
        search_levels=search_levels,
        search_width=search_width
    )
    
    if not manager:
        return
    
    # Offer to fit custom model
    print("\n" + "=" * 70)
    custom = input("\n🎯 Enter a custom model to fit (or press Enter to skip): ").strip()
    
    if custom:
        print(f"\n📊 Fitting custom model: {custom}")
        try:
            custom_report = manager.generate_fit_report(
                custom,
                use_ipf_start=False,
                skip_trained_model_table=False,
                skip_ivi_tables=False
            )
            
            # Save custom fit
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            os.makedirs(OUTPUT_DIR, exist_ok=True)
            custom_file = os.path.join(OUTPUT_DIR, f"fit_custom_{timestamp}.txt")
            
            with open(custom_file, 'w') as f:
                f.write(custom_report)
            
            print(f"✓ Custom model fitted")
            print(f"💾 Saved to: {custom_file}")
            
        except Exception as e:
            print(f"❌ Error fitting model: {e}")


def demo_quick_start():
    """Quick demo using built-in data"""
    print("\n🚀 Quick Start Demo")
    print("=" * 70)
    
    # Demo with dementia dataset
    print("\n1️⃣ Dementia Dataset Analysis")
    print("-" * 40)
    data, best = pyoccam.quick_search("dementia", "loopless-up", 7, 3)
    
    if data:
        print(f"   Dataset: {data.DESCR if hasattr(data, 'DESCR') else 'Dementia'}")
        print(f"   Samples: {data.n_samples}")
        print(f"   Features: {data.n_features}")
        print(f"   Best model: {best}")
        print(f"   Variables: {', '.join(data.feature_names[:5])}...")
    
    # Demo with landslides dataset  
    print("\n2️⃣ Landslides Dataset Analysis")
    print("-" * 40)
    data, best = pyoccam.quick_search("landslides", "full-up", 5, 3)
    
    if data:
        print(f"   Dataset: {data.DESCR if hasattr(data, 'DESCR') else 'Landslides'}")
        print(f"   Samples: {data.n_samples}")
        print(f"   Features: {data.n_features}")
        print(f"   Best model: {best}")
        print(f"   Variables: {', '.join(data.feature_names[:5])}")
    
    print("\n" + "=" * 70)
    print("📊 Dataset Comparison:")
    print("-" * 40)
    print("Dataset     | Samples | Features | Best Model")
    print("------------|---------|----------|------------")
    print("Dementia    | 424     | 18       | (varies by search)")
    print("Landslides  | 1277    | 5        | (varies by search)")
    
    print("\n✅ Quick demo complete!")
    print("Run in interactive mode for full analysis.")


if __name__ == "__main__":
    import sys
    
    # Check for command-line arguments
    if len(sys.argv) > 1:
        if sys.argv[1] in ['--help', '-h']:
            print("""
PyOccam Demo Script
==================

Usage:
  python pyoccam_demo.py                    # Interactive mode
  python pyoccam_demo.py demo               # Quick demo with built-in data
  python pyoccam_demo.py dementia           # Analyze dementia dataset
  python pyoccam_demo.py landslides         # Analyze landslides dataset
  python pyoccam_demo.py <datafile>         # Analyze custom data file
  python pyoccam_demo.py <data> <search> <levels> <width>  # Full parameters

Examples:
  python pyoccam_demo.py demo
  python pyoccam_demo.py dementia loopless-up 7 3
  python pyoccam_demo.py mydata.txt full-up 5 5
            """)
        elif sys.argv[1] == 'demo':
            # Run quick demo
            demo_quick_start()
        else:
            # Parse arguments
            data_source = sys.argv[1]
            
            # Optional: parse additional arguments
            search_type = sys.argv[2] if len(sys.argv) > 2 else SEARCH_TYPE
            search_levels = int(sys.argv[3]) if len(sys.argv) > 3 else SEARCH_LEVELS
            search_width = int(sys.argv[4]) if len(sys.argv) > 4 else SEARCH_WIDTH
            
            run_occam_analysis(
                data_source=data_source,
                search_type=search_type,
                search_levels=search_levels,
                search_width=search_width
            )
    else:
        # Interactive mode
        interactive_mode()
