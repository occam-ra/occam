#!/usr/bin/env python
"""
Simple working example for pyoccam2
Tests the basic functionality with dementia05.txt data
"""

import pyoccam2
import os

def main():
    print("=" * 60)
    print("PyOCCAM2 Simple Example")
    print("=" * 60 + "\n")

    # 1. Create manager instance
    print("1. Creating VBMManager...")
    manager = pyoccam2.VBMManager()

    # 2. Initialize with data file
    print("2. Loading data file...")
    data_file = "dementia05.txt"

    # Check if data file exists
    if not os.path.exists(data_file):
        # Try in occam_data directory
        alt_path = os.path.join("occam_data", data_file)
        if os.path.exists(alt_path):
            data_file = alt_path
        else:
            print(f"Error: Cannot find {data_file}")
            print("Please ensure dementia05.txt is in the current directory or occam_data/")
            return

    # Initialize from command line
    success = manager.init_from_command_line(["occam", data_file])
    if not success:
        print("Error: Failed to initialize manager with data file")
        return

    print(f"   ✓ Data loaded from {data_file}\n")

    # 3. Set configuration
    print("3. Configuring manager...")
    manager.set_report_separator(pyoccam2.SPACESEP)
    manager.set_ref_model("bottom")
    print("   ✓ Configuration set\n")

    # 4. Run a simple search
    print("4. Running loopless search (3 levels, width 3)...")
    search_report = manager.generate_search_report("full-up", 7, 3)

    # Show first few lines of report
    lines = search_report.split('\n')
    for line in lines[:50]:  # Show first 20 lines
        print(line)

    if len(lines) > 50:
        print(f"... ({len(lines) - 50} more lines)\n")

    # 5. Get best models
    print("5. Best models identified:")
    best_bic = manager.get_best_model_by_bic()
    best_aic = manager.get_best_model_by_aic()
    best_info = manager.get_best_model_by_information()

    if best_bic:
        print(f"   Best by BIC: {best_bic}")
    if best_aic:
        print(f"   Best by AIC: {best_aic}")
    if best_info:
        print(f"   Best by Information: {best_info}")

    print()

    # 6. Generate fit report for best model
    if best_bic:
        print(f"6. Generating fit report for {best_bic}...")
        fit_report = manager.generate_fit_report(best_bic)

        # Show first few lines
        lines = fit_report.split('\n')
        for line in lines[:100]:  # Show first 15 lines
            print(line)

        if len(lines) > 100:
            print(f"... ({len(lines) - 100} more lines)\n")

    print("\n" + "=" * 60)
    print("✓ Example completed successfully!")
    print("=" * 60)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
