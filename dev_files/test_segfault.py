#!/usr/bin/env python3
"""
Test different search types to isolate segfault issue
"""

import _pyoccam as pyoccam
import sys

print("="*60)
print("TESTING SEARCH TYPES FOR SEGFAULT")
print("="*60)

# Initialize and load data
print("\n1. Loading data...")
try:
    manager = pyoccam.VBMManager()
    manager.init_from_command_line(["occam", "dementia05.txt"])
    print("✓ Data loaded")
except Exception as e:
    print(f"✗ Failed to load data: {e}")
    sys.exit(1)

# Test different search types with minimal parameters
search_tests = [
    ("loopless-up", 2, 2),
    ("loopless-down", 2, 2),
    ("full-up", 2, 2),      # This one causes segfault?
    ("full-down", 2, 2),
]

for search_type, levels, width in search_tests:
    print(f"\n" + "-"*40)
    print(f"Testing: {search_type} (levels={levels}, width={width})")
    print("-"*40)
    
    try:
        print("Starting search...", end=" ")
        sys.stdout.flush()
        
        # Try the search
        report = manager.generate_search_report(search_type, levels, width, False)
        
        print("✓ Complete")
        
        # Try to get best model
        best = manager.get_best_model_by_bic()
        if best:
            print(f"  Best model: {best}")
        else:
            print("  No best model found")
            
    except Exception as e:
        print(f"✗ FAILED")
        print(f"  Error: {e}")
        import traceback
        traceback.print_exc()
        
        # Don't continue if we hit an error
        print("\n⚠️ Stopping tests due to error")
        break

print("\n" + "="*60)
print("If the program crashes before this line, it's a segfault")
print("="*60)
