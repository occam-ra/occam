#!/usr/bin/env python3
"""
Test script to debug pyoccam file reading issue
"""

import pyoccam
import os

def test_minimal_file():
    """Create and test a minimal OCCAM file"""
    
    # Create minimal test file with just a few variables
    content = """:nominal
FOD_ID, 7405,0,fo
FIRE_YEAR, 6,0,fi
FIRE_SIZE, 1417,0,a
FIRE_SIZE_, 7,0,FS
LARGE_FIRE, 2,2,Z
:no-frequency
:data
400541474 2019 0.10 A 0
400348036 2018 0.50 B 0
400614256 2020 1.95 B 0
"""
    
    # Write with LF line endings only
    with open('test_minimal.txt', 'wb') as f:
        f.write(content.encode('utf-8'))
    
    print("Created test_minimal.txt")
    print("="*60)
    
    # Check what was written
    with open('test_minimal.txt', 'rb') as f:
        written_bytes = f.read()
    
    print(f"File size: {len(written_bytes)} bytes")
    has_cr = b'\r' in written_bytes
    has_lf = b'\n' in written_bytes
    print(f"Contains CR: {has_cr}")
    print(f"Contains LF: {has_lf}")
    
    # Show first 100 bytes in hex
    print("\nFirst 100 bytes in hex:")
    for i in range(0, min(100, len(written_bytes)), 16):
        hex_str = ' '.join(f'{b:02x}' for b in written_bytes[i:i+16])
        ascii_str = ''.join(chr(b) if 32 <= b < 127 else '.' for b in written_bytes[i:i+16])
        print(f"{hex_str:48} | {ascii_str}")
    
    print("\n" + "="*60)
    print("Testing with pyoccam...")
    
    try:
        manager = pyoccam.VBMManager()
        success = manager.init_from_command_line(["occam", "test_minimal.txt"])
        
        if success:
            print("SUCCESS! File loaded into pyoccam")
            variables = manager.get_variable_list()
            print(f"Variables found: {variables}")
        else:
            print("FAILED to load file into pyoccam")
    except Exception as e:
        print(f"ERROR: {e}")
    
    # Clean up
    if os.path.exists('test_minimal.txt'):
        os.remove('test_minimal.txt')
    
    return success

def test_with_all_vegetation_vars():
    """Test with all vegetation variables included"""
    
    content = """:nominal
FOD_ID, 7405,0,fo
FIRE_YEAR, 6,0,fi
FIRE_SIZE, 1417,0,a
FIRE_SIZE_, 7,0,FS
in_d_l0, 8,1,I0,[99(11,12,21,22,23,24,31,90,95);41(41);42(42);43(43);52(52);71(71);81(81);82(82)]
mid_d_l0, 8,1,M0,[99(11,12,21,22,23,24,31,90,95);41(41);42(42);43(43);52(52);71(71);81(81);82(82)]
out_d_l0, 8,1,O0,[99(11,12,21,22,23,24,31,90,95);41(41);42(42);43(43);52(52);71(71);81(81);82(82)]
LARGE_FIRE, 2,2,Z
:no-frequency
:data
400541474 2019 0.10 A 81 81 81 0
400348036 2018 0.50 B 71 42 42 0
"""
    
    with open('test_with_veg.txt', 'wb') as f:
        f.write(content.encode('utf-8'))
    
    print("\n" + "="*60)
    print("Testing with vegetation variables...")
    
    try:
        manager = pyoccam.VBMManager()
        success = manager.init_from_command_line(["occam", "test_with_veg.txt"])
        
        if success:
            print("SUCCESS! File with vegetation vars loaded")
        else:
            print("FAILED to load file with vegetation vars")
    except Exception as e:
        print(f"ERROR: {e}")
    
    # Clean up
    if os.path.exists('test_with_veg.txt'):
        os.remove('test_with_veg.txt')
    
    return success

def compare_with_original():
    """Compare our test file with the original"""
    
    original_path = 'fire_data_split_all_signature_groups_nlcd_rebinned_sigs.txt'
    
    if not os.path.exists(original_path):
        print(f"Original file not found: {original_path}")
        return
    
    print("\n" + "="*60)
    print("Comparing with original file...")
    
    # Read first few lines of original
    with open(original_path, 'rb') as f:
        orig_bytes = f.read(200)
    
    print("Original file - first 200 bytes:")
    for i in range(0, min(200, len(orig_bytes)), 16):
        hex_str = ' '.join(f'{b:02x}' for b in orig_bytes[i:i+16])
        ascii_str = ''.join(chr(b) if 32 <= b < 127 else '.' for b in orig_bytes[i:i+16])
        print(f"{hex_str:48} | {ascii_str}")
    
    # Try loading original with pyoccam
    print("\nTrying to load original file with pyoccam...")
    try:
        manager = pyoccam.VBMManager()
        success = manager.init_from_command_line(["occam", original_path])
        
        if success:
            print("SUCCESS! Original file loads fine")
            print(f"Sample size: {manager.get_sample_size()}")
            print(f"Has test data: {manager.has_test_data()}")
        else:
            print("FAILED to load original file!")
    except Exception as e:
        print(f"ERROR loading original: {e}")

if __name__ == "__main__":
    print("PYOCCAM FILE FORMAT DEBUGGING")
    print("="*60)
    
    # Test 1: Minimal file
    success1 = test_minimal_file()
    
    # Test 2: With vegetation variables  
    success2 = test_with_all_vegetation_vars()
    
    # Test 3: Compare with original
    compare_with_original()
    
    print("\n" + "="*60)
    print("SUMMARY:")
    print(f"  Minimal file: {'PASSED' if success1 else 'FAILED'}")
    print(f"  With veg vars: {'PASSED' if success2 else 'FAILED'}")
    
    if not success1:
        print("\nThe issue appears to be with pyoccam itself or the format")
        print("Check if pyoccam needs a specific format or if there's a version issue")
