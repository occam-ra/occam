#!/usr/bin/env python
"""
test_build.py - Quick test to verify PyOccam built correctly
"""

import sys

print("=" * 60)
print("PyOccam Build Test")
print("=" * 60)
print(f"Python: {sys.version}")
print()

try:
    # Test import
    print("Testing import...")
    import pyoccam
    print("✓ PyOccam imported successfully")
    print(f"  Version: {pyoccam.__version__}")
    print()
    
    # Test VBMManager availability
    print("Testing VBMManager...")
    manager = pyoccam.VBMManager()
    print("✓ VBMManager created successfully")
    print()
    
    # Test data loading
    print("Testing data loading...")
    dementia_file = "dementia05.txt"
    success = manager.init_from_command_line(["occam", dementia_file])
    if success:
        print(f"✓ Data loaded successfully")
        
        # Get basic info
        variables = manager.get_variable_list()
        sample_size = manager.get_sample_size()
        
        print(f"  Variables: {variables}")
        print(f"  Sample size: {sample_size}")
        print()
        
        # Test search
        print("Testing search...")
        report = manager.generate_search_report("loopless-up", 3, 3, False)
        lines = report.strip().split('\n')
        print(f"✓ Search completed successfully")
        print(f"  Report lines: {len(lines)}")
        print(f"  First line: {lines[0][:80]}...")
        
    else:
        print("✗ Failed to load data file")
        print(f"  Make sure {dementia_file} exists")
    
    print()
    print("=" * 60)
    print("BUILD TEST PASSED!")
    print("=" * 60)
    
except ImportError as e:
    print(f"✗ Import failed: {e}")
    print("\nMake sure you built with:")
    print("  python setup.py build_ext --compiler=mingw32 --inplace")
    sys.exit(1)
    
except Exception as e:
    print(f"✗ Test failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)