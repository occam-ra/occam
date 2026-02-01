#!/usr/bin/env python
"""
Test the simplest report output - just pass through what Report class generates
"""

import pyoccam2

def test_simple_report():
    """Test simplest report generation - no post-processing"""
    
    print("=" * 80)
    print("SIMPLE REPORT TEST - NO POST-PROCESSING")
    print("=" * 80)
    
    # Initialize manager
    manager = pyoccam2.VBMManager()
    
    # Load data
    success = manager.init_from_command_line(["occam", "dementia05.txt"])
    if not success:
        print("ERROR: Failed to load data")
        return False
    
    # Test with tab separator for cleaner output
    print("\n1. Testing with TAB separator (might be cleaner):")
    print("-" * 80)
    
    manager.set_report_separator(1)  # Tab
    report = manager.generate_search_report("loopless-up", levels=1, width=3)
    
    # Just print exactly what we get
    print(report)
    
    # Test with comma separator
    print("\n2. Testing with COMMA separator:")
    print("-" * 80)
    
    manager.set_report_separator(2)  # Comma
    report = manager.generate_search_report("loopless-up", levels=1, width=3)
    
    # Print first 2000 chars to avoid too much output
    if len(report) > 2000:
        print(report[:2000] + "\n... (truncated)")
    else:
        print(report)
    
    # Test with default space separator
    print("\n3. Testing with SPACE separator (default):")
    print("-" * 80)
    
    manager.set_report_separator(3)  # Space
    report = manager.generate_search_report("loopless-up", levels=1, width=3)
    
    # Count how many times each model appears
    lines = report.split('\n')
    model_counts = {}
    for line in lines:
        if "IV:" in line:
            # Extract model name
            parts = line.split()
            for part in parts:
                if "IV:" in part:
                    model_name = part
                    model_counts[model_name] = model_counts.get(model_name, 0) + 1
                    break
    
    print("Model appearance counts:")
    for model, count in model_counts.items():
        print(f"  {model}: appears {count} times")
    
    # Just show the search progress and first few unique lines
    print("\nFirst part of report:")
    seen = set()
    count = 0
    for line in lines:
        if line not in seen:
            print(line)
            seen.add(line)
            count += 1
            if count > 20:  # Limit output
                print("... (remaining output omitted)")
                break
    
    return True

if __name__ == "__main__":
    import sys
    success = test_simple_report()
    print("\n" + "=" * 80)
    print("Simple report test complete.")
    print("The Report class output is passed through exactly as generated.")
    print("=" * 80)
    sys.exit(0 if success else 1)