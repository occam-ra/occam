#!/usr/bin/env python3
"""
Check what's actually in the pyoccam module
"""

import sys
import os

print("="*60)
print("CHECKING PYOCCAM MODULE")
print("="*60)

# Check Python version and path
print(f"\nPython: {sys.version}")
print(f"Python executable: {sys.executable}")

# Check current directory
print(f"\nCurrent directory: {os.getcwd()}")

# List .pyd and .so files (compiled extensions)
print("\nCompiled extension files in current directory:")
for f in os.listdir('.'):
    if f.endswith('.pyd') or f.endswith('.so') or f.startswith('_pyoccam'):
        size = os.path.getsize(f)
        print(f"  {f} ({size:,} bytes)")

# Try to import pyoccam and see what's in it
print("\n" + "-"*40)
print("Attempting to import pyoccam...")
print("-"*40)

try:
    import pyoccam
    print("✓ pyoccam imported successfully")
    
    # Check what's in the module
    print("\nModule location:", pyoccam.__file__ if hasattr(pyoccam, '__file__') else "Unknown")
    
    print("\nModule contents (dir(pyoccam)):")
    contents = dir(pyoccam)
    for item in sorted(contents):
        if not item.startswith('_'):
            print(f"  • {item}")
    
    # Check if it's the compiled module or Python wrapper
    print("\nChecking for VBMManager...")
    if hasattr(pyoccam, 'VBMManager'):
        print("✓ VBMManager found in pyoccam")
    else:
        print("✗ VBMManager NOT found in pyoccam")
        
        # Maybe it's in _pyoccam?
        if hasattr(pyoccam, '_pyoccam'):
            print("\nFound _pyoccam submodule, checking contents:")
            for item in dir(pyoccam._pyoccam):
                if not item.startswith('_'):
                    print(f"  • {item}")
    
    # Try different import approaches
    print("\n" + "-"*40)
    print("Trying different imports:")
    print("-"*40)
    
    # Try importing _pyoccam directly
    try:
        import _pyoccam
        print("✓ _pyoccam imported directly")
        if hasattr(_pyoccam, 'VBMManager'):
            print("  ✓ VBMManager found in _pyoccam")
            print("\n  You should use: from _pyoccam import VBMManager")
    except ImportError as e:
        print(f"✗ Cannot import _pyoccam directly: {e}")
    
    # Check if pyoccam.py exists and what it contains
    if os.path.exists('pyoccam.py'):
        print("\n" + "-"*40)
        print("Found pyoccam.py wrapper file")
        print("-"*40)
        with open('pyoccam.py', 'r') as f:
            lines = f.readlines()
            print(f"File has {len(lines)} lines")
            print("\nFirst 30 lines:")
            for i, line in enumerate(lines[:30]):
                print(f"{i+1:3}: {line.rstrip()}")
                
except ImportError as e:
    print(f"✗ Failed to import pyoccam: {e}")
    
    # Try to import _pyoccam directly
    try:
        print("\nTrying to import _pyoccam directly...")
        import _pyoccam
        print("✓ _pyoccam imported successfully!")
        print("\n_pyoccam contents:")
        for item in dir(_pyoccam):
            if not item.startswith('_'):
                print(f"  • {item}")
                
        print("\n💡 SOLUTION: Use _pyoccam directly:")
        print("   import _pyoccam as pyoccam")
        print("   manager = pyoccam.VBMManager()")
        
    except ImportError as e2:
        print(f"✗ Failed to import _pyoccam: {e2}")
        print("\n⚠️ The compiled module may not be built correctly")

print("\n" + "="*60)
