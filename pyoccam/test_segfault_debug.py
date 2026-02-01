#!/usr/bin/env python3
"""
Minimal test to identify segfault location with checkpoints
"""
import sys
import os

# Add project path
sys.path.insert(0, 'D:\\projects\\occam\\pyoccam')

import pyoccam

print("="*80)
print("SEGFAULT DEBUG TEST - WITH CHECKPOINTS")
print("="*80)
print()

# Initialize
print("Step 1: Creating VBMManager...")
manager = pyoccam.VBMManager()

print("Step 2: Loading data...")
if not manager.init_from_command_line(["occam", "dementia05.txt"]):
    print("Failed to load data")
    exit(1)

print("✓ Data loaded successfully")
print()

# Test with the model that causes segfault
model_name = "IV:ApZ"
target = "0"

print(f"Step 3: Calling get_confusion_matrix('{model_name}', '{target}')...")
print(f"Watch for CHECKPOINT messages below to see where it crashes:")
print()

try:
    cm = manager.get_confusion_matrix(model_name, target)
    print("\n✓ SUCCESS! CM retrieved without segfault:")
    print(f"  has_values: {cm.get('has_values', False)}")
    if 'error' in cm:
        print(f"  Error: {cm['error']}")
    else:
        print(f"  TN={cm.get('TN', 0):.0f}, FP={cm.get('FP', 0):.0f}")
        print(f"  FN={cm.get('FN', 0):.0f}, TP={cm.get('TP', 0):.0f}")
except Exception as e:
    print(f"\n✗ Python Exception: {e}")
    import traceback
    traceback.print_exc()
