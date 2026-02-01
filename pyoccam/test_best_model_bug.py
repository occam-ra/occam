"""
Test script to verify get_best_model_by_information() behavior.

EXPECTED (per OCCAM Manual Section IV "Search Output"):
- get_best_model_by_information() should return the model with highest 
  information where ALL steps from starting model have Inc.Alpha < 0.05
- This is what the OCCAM manual calls "best model by Information"

BEFORE FIX:
- get_best_model_by_information() returned highest RAW information (ignoring Inc.Alpha)
- incr_alpha_reachable was never set for non-reference models

AFTER FIX:
- get_best_model_by_information() returns highest info WHERE ALL STEPS ARE SIGNIFICANT
- get_best_model_by_raw_information() returns highest raw info (may overfit)
- incr_alpha_reachable is properly calculated for all models
"""

import sys
sys.path.insert(0, 'd:/projects/occam')

import pyoccam

print("="*70)
print(f"PyOccam version: {pyoccam.__version__}")
print("TEST: get_best_model_by_information() behavior")
print("="*70)

# Load test data
data = pyoccam.load_dementia()
manager = data.manager

# Enable debug mode to see incr_alpha values
manager.set_debug_mode(True)

# Run search
print("\n" + "="*70)
print("RUNNING SEARCH (debug mode ON - watch for reachability tracking)")
print("="*70 + "\n")

report = manager.generate_search_report("loopless-up", 5, 3)

# Get best models by different criteria
best_bic = manager.get_best_model_by_bic()
best_aic = manager.get_best_model_by_aic()
best_info = manager.get_best_model_by_information()  # OCCAM manual definition
best_info_alpha = manager.get_best_model_by_info_alpha()  # Deprecated alias

# Check if raw_information method exists (new in v0.1.3)
try:
    best_raw = manager.get_best_model_by_raw_information()
except AttributeError:
    best_raw = "N/A (method not available)"

print("\n" + "="*70)
print("RESULTS:")
print("="*70)
print(f"  Best by BIC:              {best_bic}")
print(f"  Best by AIC:              {best_aic}")
print(f"  Best by Information:      {best_info}")
print(f"  Best by Info+Alpha:       {best_info_alpha}  (deprecated alias)")
print(f"  Best by Raw Information:  {best_raw}")

# Verify the fix
print("\n" + "="*70)
print("VERIFICATION:")
print("="*70)

# Check 1: get_best_model_by_information() should equal get_best_model_by_info_alpha()
if best_info == best_info_alpha:
    print("✓ get_best_model_by_information() == get_best_model_by_info_alpha()")
    print("  Both return the OCCAM manual definition (highest info with all steps significant)")
else:
    print("✗ MISMATCH! These should be equal after the fix:")
    print(f"    get_best_model_by_information(): {best_info}")
    print(f"    get_best_model_by_info_alpha():  {best_info_alpha}")

# Check 2: If raw info != info, then the fix is working
if best_raw != "N/A (method not available)":
    if best_raw != best_info:
        print("\n✓ get_best_model_by_raw_information() != get_best_model_by_information()")
        print("  The Inc.Alpha < 0.05 constraint is being applied correctly!")
        print(f"    Raw info model:    {best_raw}")
        print(f"    OCCAM def model:   {best_info}")
    else:
        print("\n○ get_best_model_by_raw_information() == get_best_model_by_information()")
        print("  (This can happen if the highest info model also has all steps significant)")

# Check 3: Empty string indicates no models are reachable
if not best_info:
    print("\n⚠️  WARNING: get_best_model_by_information() returned EMPTY STRING!")
    print("   This means NO models have all steps with Inc.Alpha < 0.05")
    print("   The independence model would be the safest choice in this case.")

# Get all kept models and show their info and incr_alpha
print("\n" + "="*70)
print("ALL KEPT MODELS:")
print("="*70)

models = manager.get_kept_models()
print(f"{'Model':<25} {'Info%':>8} {'Inc.Alpha':>12} {'Level':>6}")
print("-"*55)

# Count reachable models
reachable_count = 0
for m in sorted(models, key=lambda x: x.information, reverse=True):
    info_pct = m.information * 100
    # Check if incr_alpha < 0.05 (we can't directly check reachability from Python)
    is_sig = "  *" if m.incr_alpha < 0.05 else ""
    print(f"{m.name:<25} {info_pct:>7.2f}% {m.incr_alpha:>12.6f}{is_sig} {m.level:>5}")
    if m.incr_alpha < 0.05:
        reachable_count += 1

print("\n* = Inc.Alpha < 0.05 for this step")
print(f"\nModels with Inc.Alpha < 0.05 at their step: {reachable_count}/{len(models)}")

print("\n" + "="*70)
print("TEST COMPLETE")
print("="*70)
