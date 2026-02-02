#!/usr/bin/env python3
"""
Find which source file is actually being compiled
"""

import os
import glob
import re

print("=" * 60)
print("FINDING SOURCE FILE BEING COMPILED")
print("=" * 60)

# 1. Look for all .cpp files that might be compiled
print("\n1. Looking for pybind11 source files:")
print("-" * 40)

cpp_files = glob.glob("pyoccam/*.cpp") + glob.glob("*.cpp") + glob.glob("pyoccam/pyoccam*.cpp")
cpp_files = list(set(cpp_files))  # Remove duplicates

for cpp in cpp_files:
    size = os.path.getsize(cpp) / 1024
    print(f"\nFound: {cpp} ({size:.1f} KB)")
    
    # Check what module it defines
    with open(cpp, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
        
        # Look for PYBIND11_MODULE
        module_match = re.search(r'PYBIND11_MODULE\s*\(\s*(\w+)', content)
        if module_match:
            module_name = module_match.group(1)
            print(f"  Module name: {module_name}")
        
        # Look for key classes
        if 'VBMManager' in content:
            print(f"  ✓ Contains VBMManager")
        if 'class OCCAM' in content or 'py::class_<OCCAM>' in content:
            print(f"  ⚠️ Contains OCCAM class")
        if 'SearchResults' in content:
            print(f"  ⚠️ Contains SearchResults")
        if 'quick_search' in content:
            print(f"  ⚠️ Contains quick_search")

# 2. Check setup.py to see what it's compiling
print("\n2. Checking setup.py source configuration:")
print("-" * 40)

if os.path.exists("setup.py"):
    with open("setup.py", 'r') as f:
        setup_content = f.read()
    
    # Find the sources list
    sources_match = re.search(r'sources\s*=\s*\[(.*?)\]', setup_content, re.DOTALL)
    if sources_match:
        sources = sources_match.group(1)
        print("Sources in setup.py:")
        
        # Extract the main pybind file
        pybind_match = re.search(r'["\']([^"\']*pybind[^"\']*\.cpp)["\']', sources)
        if pybind_match:
            pybind_file = pybind_match.group(1)
            print(f"  Main pybind file: {pybind_file}")
            
            # Check if this file exists
            if os.path.exists(pybind_file):
                print(f"  ✓ File exists")
            else:
                print(f"  ✗ File does NOT exist!")
                print(f"    This is the problem - setup.py points to non-existent file")

# 3. Look for the correct pyoccam_pybind11.cpp
print("\n3. Checking pyoccam_pybind11.cpp content:")
print("-" * 40)

correct_file = "pyoccam/pyoccam_pybind11.cpp"
if os.path.exists(correct_file):
    with open(correct_file, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read(1000)  # First 1000 chars
    
    if 'VBMManager' in content:
        print(f"✓ {correct_file} contains VBMManager - this is the right file!")
    else:
        print(f"✗ {correct_file} does NOT contain VBMManager")
        print("  First 200 chars:")
        print(content[:200])
else:
    print(f"✗ {correct_file} not found")

print("\n" + "=" * 60)
print("DIAGNOSIS:")
print("=" * 60)

print("""
If setup.py is compiling the wrong file:

1. Edit setup.py and make sure the Extension sources includes:
   'pyoccam/pyoccam_pybind11.cpp'
   
2. Make sure there's only ONE pybind .cpp file being compiled

3. Delete any old .cpp files that define OCCAM or SearchResults

4. Rebuild with the corrected setup.py
""")
