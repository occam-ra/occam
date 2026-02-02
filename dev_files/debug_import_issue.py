#!/usr/bin/env python3
"""
Debug why the import isn't working even with correct __init__.py
"""

import os
import sys
import glob

print("=" * 60)
print("DEBUGGING PYOCCAM IMPORT ISSUE")
print("=" * 60)

# 1. Check the compiled module exists
print("\n1. Looking for compiled module (pyoccam.pyd):")
print("-" * 40)
pyd_files = glob.glob("pyoccam/*.pyd") + glob.glob("pyoccam/*.so")
if pyd_files:
    for pyd in pyd_files:
        size = os.path.getsize(pyd) / 1024 / 1024
        print(f"✓ Found: {pyd} ({size:.1f} MB)")
        
        # Check the actual filename
        filename = os.path.basename(pyd)
        print(f"  Filename: {filename}")
        
        # Check if it's the right name
        if filename.startswith("pyoccam.cp"):
            print(f"  ✓ Correct naming pattern for Python extension")
        else:
            print(f"  ⚠️ Unexpected filename pattern")
else:
    print("✗ No .pyd or .so files found in pyoccam/")
    print("  This is the problem! No compiled module to import.")

# 2. Try to import the module directly
print("\n2. Attempting direct import of compiled module:")
print("-" * 40)

# Add pyoccam directory to path temporarily
sys.path.insert(0, 'pyoccam')

try:
    # Try to import the compiled module directly
    import pyoccam as compiled_module
    print("✓ Direct import of 'pyoccam' module worked")
    print(f"  Module file: {compiled_module.__file__}")
    print(f"  Has VBMManager: {hasattr(compiled_module, 'VBMManager')}")
    if hasattr(compiled_module, 'VBMManager'):
        print("  ✓ VBMManager found in compiled module!")
    
    # Show what's in it
    attrs = [x for x in dir(compiled_module) if not x.startswith('_')]
    print(f"  Available attributes: {attrs[:10]}...")  # First 10
    
except ImportError as e:
    print(f"✗ Direct import failed: {e}")
    print("  The compiled module cannot be imported directly")

# Remove from path
sys.path.pop(0)

# 3. Try the package import
print("\n3. Testing package import (import pyoccam):")
print("-" * 40)

# Clear any cached imports
if 'pyoccam' in sys.modules:
    del sys.modules['pyoccam']
    print("  Cleared cached import")

try:
    import pyoccam as pkg
    print("✓ Package import worked")
    print(f"  Package __file__: {pkg.__file__}")
    print(f"  Package __version__: {getattr(pkg, '__version__', 'NOT FOUND')}")
    
    # Check what got imported
    attrs = [x for x in dir(pkg) if not x.startswith('_')]
    print(f"  Attributes in package: {len(attrs)} total")
    
    # Look for key items
    has_vbm = hasattr(pkg, 'VBMManager')
    has_constants = all(hasattr(pkg, c) for c in ['SPACESEP', 'COMMASEP', 'TABSEP'])
    
    print(f"  Has VBMManager: {has_vbm}")
    print(f"  Has constants: {has_constants}")
    
    if not has_vbm:
        print("\n  ⚠️ VBMManager NOT imported!")
        print("  The 'from .pyoccam import *' line isn't working")
        
        # Check if there's an import error
        print("\n  Trying to debug the import failure...")
        
        # Try to import with error details
        try:
            exec("from .pyoccam import *", pkg.__dict__)
        except Exception as e:
            print(f"  Import error: {e}")
            
except ImportError as e:
    print(f"✗ Package import failed: {e}")

print("\n" + "=" * 60)
print("DIAGNOSIS:")
print("=" * 60)

if not pyd_files:
    print("""
PROBLEM: No compiled module (.pyd file) in pyoccam/ directory

SOLUTION:
1. The build might have put the .pyd file somewhere else
2. Check the build output for where the .pyd was created
3. Move any pyoccam*.pyd file to the pyoccam/ directory
4. Or rebuild with: python setup.py build_ext --inplace
""")
elif pyd_files and not has_vbm:
    print("""
PROBLEM: Compiled module exists but import isn't working

POSSIBLE CAUSES:
1. The .pyd file might be for a different Python version
2. Missing DLL dependencies (libgcc_s_seh-1.dll, etc.)
3. The module name inside the .pyd doesn't match

SOLUTION:
1. Check that you're using the same Python version that built the module
2. Copy MinGW DLLs to pyoccam/ directory
3. Rebuild for your current Python version
""")
else:
    print("Everything looks OK - the import should work!")

print("\n✅ To test in Python/Jupyter:")
print("   import pyoccam")
print("   manager = pyoccam.VBMManager()")
