#!/usr/bin/env python3
"""
Diagnostic script to find and fix pyoccam installation issues
"""

import os
import sys
import glob

print("="*70)
print("PYOCCAM INSTALLATION DIAGNOSTIC")
print("="*70)

# 1. Check current directory
print(f"\n1. Current directory: {os.getcwd()}")

# 2. Find all .pyd and .so files
print("\n2. Looking for compiled modules (.pyd/.so):")
pyd_files = glob.glob("*.pyd") + glob.glob("*.so")
pyd_files += glob.glob("pyoccam/*.pyd") + glob.glob("pyoccam/*.so")
pyd_files += glob.glob("**/*.pyd", recursive=True) + glob.glob("**/*.so", recursive=True)
pyd_files = list(set(pyd_files))  # Remove duplicates

if pyd_files:
    for pyd in pyd_files:
        size = os.path.getsize(pyd) / 1024 / 1024  # MB
        mtime = os.path.getmtime(pyd)
        print(f"  ✓ Found: {pyd} ({size:.1f} MB)")
else:
    print(f"  ✗ No .pyd or .so files found")

# 3. Check for pyoccam directory and __init__.py
print("\n3. Checking package structure:")
if os.path.exists("pyoccam"):
    print("  ✓ pyoccam/ directory exists")
    
    init_file = "pyoccam/__init__.py"
    if os.path.exists(init_file):
        print(f"  ✓ {init_file} exists")
        with open(init_file, 'r') as f:
            content = f.read()
            print(f"    Contents: {repr(content[:100])}")
    else:
        print(f"  ✗ {init_file} missing!")
else:
    print("  ✗ pyoccam/ directory missing")

# 4. Try various import methods
print("\n4. Testing imports:")

# Method 1: Direct import
try:
    import pyoccam
    print("  ✓ 'import pyoccam' works")
    print(f"    pyoccam.__file__ = {pyoccam.__file__}")
    
    if hasattr(pyoccam, 'VBMManager'):
        print("  ✓ pyoccam.VBMManager exists!")
    else:
        print(f"  ✗ pyoccam.VBMManager not found")
        print(f"    Available: {[x for x in dir(pyoccam) if not x.startswith('_')]}")
        
        # Check if it's nested
        if hasattr(pyoccam, 'pyoccam'):
            print("  ! Found nested pyoccam.pyoccam")
            if hasattr(pyoccam.pyoccam, 'VBMManager'):
                print("  ✓ pyoccam.pyoccam.VBMManager exists!")
except ImportError as e:
    print(f"  ✗ 'import pyoccam' failed: {e}")

# Method 2: Import from pyoccam.pyoccam
try:
    from pyoccam import pyoccam as pyoccam_inner
    print("  ✓ 'from pyoccam import pyoccam' works")
    if hasattr(pyoccam_inner, 'VBMManager'):
        print("  ✓ Found VBMManager in nested module")
except ImportError as e:
    print(f"  ✗ 'from pyoccam import pyoccam' failed: {e}")

# Method 3: Direct file import
pyd_path = None
for pyd in pyd_files:
    if 'pyoccam' in os.path.basename(pyd):
        pyd_path = pyd
        break

if pyd_path:
    print(f"\n5. Attempting direct load of {pyd_path}:")
    import importlib.util
    try:
        spec = importlib.util.spec_from_file_location("pyoccam_direct", pyd_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        print(f"  ✓ Direct load successful")
        if hasattr(module, 'VBMManager'):
            print(f"  ✓ VBMManager found in directly loaded module")
    except Exception as e:
        print(f"  ✗ Direct load failed: {e}")

# 6. Provide solution
print("\n" + "="*70)
print("DIAGNOSIS COMPLETE")
print("="*70)

print("\nRECOMMENDED FIXES:")

if not pyd_files:
    print("\n1. No compiled module found. Build it:")
    print("   python setup.py build_ext --inplace --compiler=mingw32")

elif "pyoccam/pyoccam.pyd" in pyd_files or "pyoccam/pyoccam.so" in pyd_files:
    print("\n1. Module is in package structure (pyoccam/pyoccam.pyd)")
    print("   Ensure pyoccam/__init__.py contains:")
    print("   from .pyoccam import *")
    
elif "pyoccam.pyd" in pyd_files or "pyoccam.so" in pyd_files:
    print("\n1. Module is at root level (pyoccam.pyd)")
    print("   This should work with 'import pyoccam'")
    print("   If not, check if the pybind module name matches:")
    print("   PYBIND11_MODULE(pyoccam, m) { ... }")

print("\n2. To rebuild cleanly:")
print("   rmdir /s /q build         (Windows)")
print("   rm -rf build             (Linux/Mac)")
print("   del pyoccam\\*.pyd       (Windows)")  
print("   rm pyoccam/*.so          (Linux/Mac)")
print("   python setup.py build_ext --inplace --compiler=mingw32")

print("\n3. To use the module right now (workaround):")
print("   If pyoccam.pyoccam.VBMManager exists, update demo:")
print("   from pyoccam.pyoccam import VBMManager")
print("   manager = VBMManager()")
