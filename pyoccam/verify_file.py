#!/usr/bin/env python3
"""
Verify that the C++ file has all the fflush fixes
"""
import os

cpp_file = r"pyoccam_pybind11.cpp"

if not os.path.exists(cpp_file):
    print(f"❌ File not found: {cpp_file}")
    exit(1)

with open(cpp_file, 'r', encoding='utf-8', errors='ignore') as f:
    content = f.read()

# Count fflush calls
fflush_count = content.count('fflush(temp')
rewind_count = content.count('rewind(temp')

print(f"Checking: {cpp_file}")
print(f"  fflush(temp...) calls: {fflush_count}")
print(f"  rewind(temp...) calls: {rewind_count}")

if fflush_count == 4 and rewind_count == 4:
    print("\n✓ CORRECT! File has all 4 fflush fixes")
elif fflush_count == 0:
    print("\n❌ WRONG FILE! No fflush calls found - you're using an old version")
    print("   Download pyoccam_pybind11_no_hang.cpp again")
else:
    print(f"\n⚠️  PARTIAL! Expected 4 fflush, found {fflush_count}")
    
# Check module name
if 'PYBIND11_MODULE(_pyoccam' in content:
    print("✓ Module name is correct: _pyoccam")
elif 'PYBIND11_MODULE(pyoccam2' in content:
    print("❌ Module name is wrong: pyoccam2 (should be _pyoccam)")
else:
    print("⚠️  Module name not found")

# Check for get_confusion_matrix
if 'py::dict get_confusion_matrix()' in content:
    print("✓ get_confusion_matrix() method exists (no parameters)")
else:
    print("❌ get_confusion_matrix() method missing or has wrong signature")
