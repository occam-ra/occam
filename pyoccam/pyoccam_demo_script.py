#!/usr/bin/env python3
"""
PyOccam Demo - Clean Implementation
Demonstrates search, fit, and analysis workflow
"""

import pyoccam
import os
from datetime import datetime

# ==============================================================================
# CONFIGURATION
# ==============================================================================

# Default settings (can be overridden by command-line arguments)
DATA_FILE = "dementia05.txt"           # Input data file
SEARCH_TYPE = "loopless-up"            # Options: loopless-up, full-up, disjoint-up, chain-up  
SEARCH_LEVELS = 7                      # Search depth
SEARCH_WIDTH = 3                       # Beam width
OUTPUT_DIR = "occam_output"            # Output directory

# ==============================================================================
# MAIN WORKFLOW
# ==============================================================================

def run_occam_analysis(data_file=DATA_FILE, 
                       search_type=SEARCH_TYPE,
                       search_levels=SEARCH_LEVELS, 
                       search_width=SEARCH_WIDTH,
                       custom_model=None,
                       save_output=True):
    """
    Run complete OCCAM analysis workflow
    
    Args:
        data_file: Path to input data file
        search_type: Type of search algorithm
        search_levels: Number of levels to search
        search_width: Beam width for search
        custom_model: Optional custom model string to fit (e.g., "IV:ApSxZ:EdZ:CZ")
        save_output: Whether to save results to files
    
    Returns:
        tuple: (manager, search_report, fit_report, best_model)
    """
    
    print("=" * 70)
    print("🚀 PyOccam Analysis")
    print("=" * 70)
    
    # 1. Initialize Manager
    print(f"\n📁 Loading data: {data_file}")
    manager = pyoccam.VBMManager()
    
    if not manager.init_from_command_line(["occam", data_file]):
        print(f"❌ Error: Could not load {data_file}")
        return None, None, None, None
    
    print(f"✓ Loaded {manager.get_sample_size()} samples")
    
    # Display variables
    variables = manager.get_variable_list()
    print(f"✓ Found {len(variables)} variables: {', '.join(variables[:5])}...")
    
    # 2. Configure Search
    print(f"\n🔍 Performing {search_type} search")
    print(f"   Levels: {search_levels}, Width: {search_width}")
    
    # Set report variables (excluding ID and Model for cleaner output)
    manager.set_report_variables("Level$I, h, ddf, dLR, Alpha, %dH(DV), dAIC, dBIC")
    
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
        
        # Parse BIC improvement from search results
        for line in search_report.split('\n'):
            if best_model in line and 'dBIC' in search_report:
                parts = line.split()
                if len(parts) > 7:
                    try:
                        dbic = float(parts[-1])
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
    
    return manager, search_report, fit_report, best_model


def interactive_mode():
    """Run in interactive mode with user prompts"""
    
    print("\n🎯 PyOccam Interactive Mode")
    print("-" * 40)
    
    # Get data file
    data_file = input(f"Data file [{DATA_FILE}]: ").strip() or DATA_FILE
    
    if not os.path.exists(data_file):
        print(f"❌ File not found: {data_file}")
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
    manager, search_report, fit_report, best_model = run_occam_analysis(
        data_file=data_file,
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


if __name__ == "__main__":
    import sys
    
    # Check for command-line arguments
    if len(sys.argv) > 1:
        # Non-interactive mode with file argument
        data_file = sys.argv[1]
        
        # Optional: parse additional arguments
        search_type = sys.argv[2] if len(sys.argv) > 2 else SEARCH_TYPE
        search_levels = int(sys.argv[3]) if len(sys.argv) > 3 else SEARCH_LEVELS
        search_width = int(sys.argv[4]) if len(sys.argv) > 4 else SEARCH_WIDTH
        
        run_occam_analysis(
            data_file=data_file,
            search_type=search_type,
            search_levels=search_levels,
            search_width=search_width
        )
    else:
        # Interactive mode
        interactive_mode()
