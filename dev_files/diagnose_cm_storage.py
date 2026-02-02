#!/usr/bin/env python3
"""
Diagnostic: Why isn't the CM storage code being triggered?

This tests two hypotheses:
1. Python is loading old cached .pyd that doesn't have the storage code
2. The storage code exists but checkTarget is false
"""

import sys
import os
import time
from pathlib import Path

print("="*80)
print("CM STORAGE DIAGNOSTIC")
print("="*80)
print()

# Check 1: Find the pyoccam module
print("CHECK 1: Finding pyoccam module...")
print("-"*80)

try:
    import pyoccam
    print(f"OK pyoccam imported from: {pyoccam.__file__}")
    
    # Check module timestamp
    module_path = Path(pyoccam.__file__)
    if module_path.exists():
        mod_time = module_path.stat().st_mtime
        mod_date = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(mod_time))
        age_hours = (time.time() - mod_time) / 3600
        print(f"  Module timestamp: {mod_date}")
        print(f"  Module age: {age_hours:.1f} hours")
        
        if age_hours > 24:
            print(f"  WARNING: Module is {age_hours/24:.1f} days old!")
            print(f"      You may be loading old cached code!")
    else:
        print(f"  WARNING: Module file not found!")
        
except ImportError as e:
    print(f"ERROR Cannot import pyoccam: {e}")
    sys.exit(1)

print()

# Check 2: Try to get a confusion matrix
print("CHECK 2: Testing CM storage with dementia05...")
print("-"*80)

try:
    # Initialize
    mgr = pyoccam.VBMManager()
    if not mgr.init_from_command_line(["occam", "dementia05.txt"]):
        print("ERROR Failed to load dementia05.txt")
        sys.exit(1)
    
    print("OK Loaded dementia05.txt")
    
    # Get DV info
    var_list = mgr.get_variable_list()
    print(f"\n  Variable list (last 3 variables):")
    if isinstance(var_list, list):
        for var in var_list[-3:]:
            print(f"    {var}")
    else:
        # If it's a string
        for line in str(var_list).strip().split('\n')[-3:]:
            print(f"    {line}")
    
    # Test with known good model
    model_name = "IV:ApZ:EdZ:CZ"
    target_state = "0"
    
    print(f"\n  Testing model: {model_name}")
    print(f"  Target state: '{target_state}'")
    print()
    print("  Calling get_confusion_matrix()...")
    print("  (Watch for debug output on stderr)")
    print("-"*80)
    
    sys.stdout.flush()
    
    # This should trigger the storage code
    cm = mgr.get_confusion_matrix(model_name, target_state)
    
    sys.stdout.flush()
    
    print("-"*80)
    print()
    
    # Analyze results
    if "error" in cm:
        print(f"ERROR returned: {cm['error']}")
        print()
        print("  This means:")
        print("    - The storage code RAN (you have the new code!)")
        print("    - But has_values was FALSE")
        print("    - Likely because checkTarget was FALSE")
        print()
        print("  ROOT CAUSE: target_state doesn't match DV labels")
        print()
        
    elif cm.get('TN', 0) == 0 and cm.get('TP', 0) == 0:
        print(f"ERROR Got all zeros")
        print(f"  TN={cm.get('TN')}, FP={cm.get('FP')}, FN={cm.get('FN')}, TP={cm.get('TP')}")
        print()
        print("  This means:")
        print("    - Either checkTarget was FALSE (CM never computed)")
        print("    - Or you're loading OLD code that doesn't have storage")
        print()
        print("  If you saw NO debug output above, you're loading OLD code!")
        print()
        
    else:
        total = cm.get('TN', 0) + cm.get('FP', 0) + cm.get('FN', 0) + cm.get('TP', 0)
        print(f"OK Got valid confusion matrix!")
        print(f"  TN={cm.get('TN')}, FP={cm.get('FP')}, FN={cm.get('FN')}, TP={cm.get('TP')}")
        print(f"  Total={total} (expected 424)")
        print(f"  Accuracy={cm.get('accuracy', 0):.3f}")
        print()
        print("  SUCCESS! The storage code is working!")
        print()

except Exception as e:
    print(f"ERROR Exception: {e}")
    import traceback
    traceback.print_exc()

print()
print("="*80)
print("WHAT TO DO NEXT:")
print("="*80)
print()

print("If you saw the debug message '[CM persisted] TN=... FP=... FN=... TP=...':")
print("  -> Storage code is working! Issue is with checkTarget or target_state")
print("  -> Try different target states or check DV labels")
print()

print("If you saw NO debug output:")
print("  -> Python is loading OLD cached .pyd file!")
print("  -> Solution:")
print("     1. Close ALL Python/Jupyter sessions")
print("     2. Delete: c:\\projects\\occam\\py\\_pyoccam.*.pyd")
print("     3. cd c:\\projects\\occam")
print("     4. mingw32-make clean")
print("     5. mingw32-make")
print("     6. Start fresh Python and test again")
print()

print("If you saw an 'error' dict:")
print("  -> Storage code exists but checkTarget failed")
print("  -> Check that target_state matches actual DV labels exactly")
print()
