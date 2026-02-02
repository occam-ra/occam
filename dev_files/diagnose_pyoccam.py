#!/usr/bin/env python3
"""
Diagnostic: Which pyoccam are we using?
"""
import sys

print("="*80)
print("PYOCCAM IMPORT DIAGNOSTIC")
print("="*80)
print()

# Check what gets imported
print("1. Attempting to import pyoccam...")
try:
    import pyoccam
    print("[OK] pyoccam imported")
except ImportError as e:
    print(f"[ERROR] Failed to import: {e}")
    sys.exit(1)

print()
print("2. Checking pyoccam location:")
print(f"   Module file: {pyoccam.__file__}")
print()

print("3. Checking pyoccam attributes:")
print(f"   Has VBMManager: {hasattr(pyoccam, 'VBMManager')}")
print(f"   Has utils: {hasattr(pyoccam, 'utils')}")
print(f"   Has manager: {hasattr(pyoccam, 'manager')}")
print()

print("4. Checking VBMManager class:")
if hasattr(pyoccam, 'VBMManager'):
    mgr_class = pyoccam.VBMManager
    print(f"   Class module: {mgr_class.__module__}")
    print(f"   Has get_confusion_matrix: {hasattr(mgr_class, 'get_confusion_matrix')}")
    
    # Check if it's a Python class or C++ class
    import inspect
    if inspect.isclass(mgr_class):
        # Check the source
        try:
            source_file = inspect.getsourcefile(mgr_class)
            print(f"   Source file: {source_file}")
            print("   [WARNING] This is a PYTHON class, not C++!")
        except (TypeError, OSError):
            print("   [OK] This appears to be a C++ extension class (no Python source)")
    print()

print("5. Creating VBMManager instance...")
try:
    manager = pyoccam.VBMManager()
    print("[OK] VBMManager instance created")
    print()
    
    print("6. Checking get_confusion_matrix method:")
    if hasattr(manager, 'get_confusion_matrix'):
        method = manager.get_confusion_matrix
        print(f"   Method exists: Yes")
        print(f"   Method type: {type(method)}")
        
        # Try to get the module
        if hasattr(method, '__module__'):
            print(f"   Module: {method.__module__}")
        
        # Check if it's implemented in Python or C++
        try:
            import inspect
            sig = inspect.signature(method)
            print(f"   Signature: {sig}")
            
            # Try to get source - if this works, it's Python
            try:
                source = inspect.getsource(method)
                print("   [WARNING] Method has Python source - this is NOT the C++ implementation!")
                print("   First 200 chars of source:")
                print("   " + source[:200].replace('\n', '\n   '))
            except (TypeError, OSError):
                print("   [OK] No Python source - this appears to be a C++ method")
        except Exception as e:
            print(f"   Could not inspect: {e}")
    else:
        print("   [ERROR] get_confusion_matrix method NOT FOUND!")
    print()
    
except Exception as e:
    print(f"[ERROR] Failed to create instance: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("="*80)
print("DIAGNOSIS:")
print("="*80)
print()

# Determine what we found
if hasattr(pyoccam, 'manager') or hasattr(pyoccam, 'utils'):
    print("[ERROR] pyoccam has 'manager' or 'utils' attributes")
    print("        This suggests the PYTHON wrapper is being imported")
    print("        instead of the C++ pybind11 module!")
    print()
    print("SOLUTION: Make sure you're importing the compiled _pyoccam extension,")
    print("          not the Python wrapper files (manager.py, utils.py)")
else:
    print("[OK] pyoccam appears to be the C++ extension")
    print()
    print("Next step: Check why get_confusion_matrix isn't working")

print("="*80)
