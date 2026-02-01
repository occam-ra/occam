#!/usr/bin/env python3
"""
Test script to diagnose PyOccam import issues
Run this to see what's happening with the module
"""

import sys
import os
from pathlib import Path

print("=" * 60)
print("PyOccam Import Diagnostic")
print("=" * 60)

# 1. Check Python version and platform
print(f"\n1. Environment:")
print(f"   Python: {sys.version}")
print(f"   Platform: {sys.platform}")
print(f"   Current dir: {os.getcwd()}")

# 2. Try to import pyoccam
print(f"\n2. Attempting import pyoccam...")
try:
    import pyoccam
    print(f"   ✓ pyoccam imported successfully")
    print(f"   Package location: {pyoccam.__file__}")
    print(f"   Package version: {getattr(pyoccam, '__version__', 'unknown')}")
except ImportError as e:
    print(f"   ✗ Import failed: {e}")
    sys.exit(1)

# 3. Check what's in the pyoccam module
print(f"\n3. Contents of pyoccam module:")
pyoccam_contents = dir(pyoccam)
print(f"   Total attributes: {len(pyoccam_contents)}")

# Check for key components
key_components = {
    'VBMManager': 'Main manager class',
    'Model': 'Model class',
    'SPACESEP': 'Space separator constant',
    'COMMASEP': 'Comma separator constant',
    'TABSEP': 'Tab separator constant',
    'HTMLFORMAT': 'HTML format constant'
}

print(f"\n   Key components:")
for comp, desc in key_components.items():
    if comp in pyoccam_contents:
        print(f"   ✓ {comp}: {desc}")
    else:
        print(f"   ✗ {comp}: MISSING - {desc}")

# 4. Check the package directory
print(f"\n4. Package directory contents:")
if hasattr(pyoccam, '__file__'):
    pkg_dir = Path(pyoccam.__file__).parent
    print(f"   Directory: {pkg_dir}")
    
    # List all files
    files = list(pkg_dir.glob("*"))
    print(f"   Files ({len(files)}):")
    
    # Categorize files
    pyd_files = []
    so_files = []
    dll_files = []
    py_files = []
    txt_files = []
    other_files = []
    
    for f in sorted(files):
        if f.suffix == '.pyd':
            pyd_files.append(f.name)
        elif f.suffix == '.so':
            so_files.append(f.name)
        elif f.suffix == '.dll':
            dll_files.append(f.name)
        elif f.suffix == '.py':
            py_files.append(f.name)
        elif f.suffix == '.txt':
            txt_files.append(f.name)
        else:
            other_files.append(f.name)
    
    if pyd_files:
        print(f"\n   .pyd files (Windows extensions):")
        for f in pyd_files:
            print(f"      {f}")
    
    if so_files:
        print(f"\n   .so files (Linux/Mac extensions):")
        for f in so_files:
            print(f"      {f}")
    
    if dll_files:
        print(f"\n   .dll files (Windows dependencies):")
        for f in dll_files:
            print(f"      {f}")
    
    if py_files:
        print(f"\n   .py files:")
        for f in py_files:
            print(f"      {f}")
    
    if txt_files:
        print(f"\n   .txt data files:")
        for f in txt_files:
            print(f"      {f}")

# 5. Try to create VBMManager
print(f"\n5. Testing VBMManager creation:")
if hasattr(pyoccam, 'VBMManager'):
    try:
        manager = pyoccam.VBMManager()
        print(f"   ✓ VBMManager created successfully")
        
        # Check methods
        methods = [m for m in dir(manager) if not m.startswith('_')]
        print(f"   Methods available: {len(methods)}")
        
        # Check for key methods
        key_methods = [
            'init_from_command_line',
            'generate_search_report',
            'generate_fit_report',
            'get_best_model_by_bic'
        ]
        
        for method in key_methods:
            if hasattr(manager, method):
                print(f"   ✓ {method}")
            else:
                print(f"   ✗ {method} - MISSING")
                
    except Exception as e:
        print(f"   ✗ Failed to create VBMManager: {e}")
else:
    print(f"   ✗ VBMManager not found in pyoccam module")

# 6. Try alternative imports
print(f"\n6. Trying alternative import methods:")

# Try importing from submodule
try:
    from pyoccam import pyoccam as submodule
    print(f"   ✓ Found pyoccam.pyoccam submodule")
    if hasattr(submodule, 'VBMManager'):
        print(f"   ✓ VBMManager found in submodule")
        print(f"   Fix: In __init__.py, use: from .pyoccam import *")
except ImportError:
    print(f"   ✗ No pyoccam.pyoccam submodule")

# Try direct file import
if sys.platform == "win32":
    pyd_path = pkg_dir / "pyoccam.pyd" if 'pkg_dir' in locals() else None
    if pyd_path and pyd_path.exists():
        print(f"   ✓ Found pyoccam.pyd at {pyd_path}")
        try:
            import importlib.util
            spec = importlib.util.spec_from_file_location("pyoccam_direct", pyd_path)
            pyoccam_direct = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(pyoccam_direct)
            if hasattr(pyoccam_direct, 'VBMManager'):
                print(f"   ✓ Can import VBMManager directly from .pyd")
        except Exception as e:
            print(f"   ✗ Direct import failed: {e}")

print("\n" + "=" * 60)
print("Diagnostic complete!")
print("=" * 60)

# Provide recommendations
print("\nRECOMMENDATIONS:")
if 'VBMManager' not in pyoccam_contents:
    print("• VBMManager is not imported properly")
    print("• Check that the .pyd/.so file exists in the package directory")
    print("• Verify the __init__.py has: from .pyoccam import *")
    print("• Make sure the module was built with: python setup.py build_ext --inplace")
else:
    print("• PyOccam appears to be installed correctly")
    print("• You can use: manager = pyoccam.VBMManager()")
