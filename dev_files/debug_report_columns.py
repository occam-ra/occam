#!/usr/bin/env python
"""
Debug the report column issues
"""

import pyoccam2

def debug_columns():
    """Debug report column problems"""
    
    print("=" * 80)
    print("DEBUGGING REPORT COLUMNS")
    print("=" * 80)
    
    # Initialize manager
    manager = pyoccam2.VBMManager()
    
    # Load data
    success = manager.init_from_command_line(["occam", "dementia05.txt"])
    if not success:
        print("ERROR: Failed to load data")
        return False
    
    # Test different report configurations
    print("\n1. Testing with default report variables:")
    print("-" * 80)
    
    report = manager.generate_search_report("loopless-up", levels=1, width=3)
    lines = report.split('\n')
    
    # Find and print header line
    for i, line in enumerate(lines):
        if "MODEL" in line or "Model" in line:
            print(f"Header line {i}: {line[:150]}")  # Truncate if too long
    
    # Try different separators
    print("\n2. Testing with tab separator:")
    print("-" * 80)
    
    manager.set_report_separator(1)  # Tab
    report = manager.generate_search_report("loopless-up", levels=1, width=3)
    lines = report.split('\n')
    
    # Show first few lines
    for i, line in enumerate(lines[8:15]):  # Skip search progress
        if line.strip():
            # Replace tabs with | for visibility
            display_line = line.replace('\t', '|')
            if len(display_line) > 150:
                display_line = display_line[:150] + "..."
            print(f"Line {i+8}: {display_line}")
    
    print("\n3. Testing with comma separator:")
    print("-" * 80)
    
    manager.set_report_separator(2)  # Comma
    report = manager.generate_search_report("loopless-up", levels=1, width=3)
    lines = report.split('\n')
    
    # Show first few lines
    for i, line in enumerate(lines[8:15]):
        if line.strip():
            if len(line) > 150:
                line = line[:150] + "..."
            print(f"Line {i+8}: {line}")
    
    print("\n4. Testing custom report variables:")
    print("-" * 80)
    
    # Try simpler attribute list
    manager.set_report_separator(3)  # Space
    manager.set_report_variables("h, information, aic, bic")
    report = manager.generate_search_report("loopless-up", levels=1, width=3)
    lines = report.split('\n')
    
    # Show header and first few data lines
    print("With custom variables (h, information, aic, bic):")
    for i, line in enumerate(lines[8:15]):
        if line.strip():
            if len(line) > 150:
                line = line[:150] + "..."
            print(f"Line {i+8}: {line}")
    
    # Check a single model's attributes directly
    print("\n5. Checking model attributes directly:")
    print("-" * 80)
    
    kept = manager.get_kept_models()
    if kept and len(kept) > 1:
        model = kept[1]  # Get a non-reference model
        print(f"Model: {model.name}")
        print(f"  h = {model.h}")
        print(f"  information = {model.information}")
        print(f"  lr = {model.lr}")
        print(f"  alpha = {model.alpha}")
        print(f"  aic = {model.aic}")
        print(f"  bic = {model.bic}")
        print(f"  daic = {model.daic}")
        print(f"  dbic = {model.dbic}")
        print(f"  df = {model.df}")
    
    return True

if __name__ == "__main__":
    import sys
    success = debug_columns()
    print("\n" + "=" * 80)
    print("Debug complete.")
    print("=" * 80)
    sys.exit(0 if success else 1)