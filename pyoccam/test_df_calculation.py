#!/usr/bin/env python
"""
Test degrees of freedom calculation
"""

import pyoccam2

def test_df():
    """Check df calculation for models"""
    
    print("=" * 70)
    print("DEGREES OF FREEDOM TEST")
    print("=" * 70)
    
    # Initialize manager
    manager = pyoccam2.VBMManager()
    success = manager.init_from_command_line(["occam", "dementia05.txt"])
    
    if not success:
        print("ERROR: Failed to load data")
        return
    
    # Set reference model explicitly
    manager.set_ref_model("bottom")
    
    print("\n1. Model Complexity Check:")
    print("-" * 50)
    
    # For these simple models, df should be small
    test_models = [
        ("IV:Z", "Independence (baseline)", 0),  # No free parameters
        ("IV:ApZ", "APOE (2 states) × Z (2 states)", 1),  # (2-1)×(2-1) = 1
        ("IV:EdZ", "Education (3 states) × Z (2 states)", 2),  # (3-1)×(2-1) = 2
        ("IV:AgZ", "AgeLastExam (3 states) × Z (2 states)", 2),  # (3-1)×(2-1) = 2
        ("IV:CZ", "rs7561528 (3 states) × Z (2 states)", 2),  # (3-1)×(2-1) = 2
        ("IV:KZ", "rs11193130 (4 states) × Z (2 states)", 3),  # (4-1)×(2-1) = 3
        ("IV:PZ", "rs3865444 (4 states) × Z (2 states)", 3),  # (4-1)×(2-1) = 3
    ]
    
    print(f"{'Model':<10} {'Description':<40} {'Expected df':<12} {'Actual df':<15}")
    print("-" * 80)
    
    for model_name, desc, expected_df in test_models:
        model = manager.make_model(model_name, True)
        print(f"{model_name:<10} {desc:<40} {expected_df:<12} {model.df:<15.0f}")
    
    print("\n2. Diagnosis:")
    print("-" * 50)
    
    ref_model = manager.make_model("IV:Z", True)
    apz_model = manager.make_model("IV:ApZ", True)
    
    if ref_model.df > 1000000:
        print("✗ PROBLEM: df values are in the millions/billions!")
        print(f"  Reference model df = {ref_model.df:.0f}")
        print(f"  This looks like state space size, not degrees of freedom")
        print()
        print("  The issue is likely:")
        print("  1. We're reading the wrong attribute (maybe 'df' is state space)")
        print("  2. We need to call computeDF() to calculate proper df")
        print("  3. We should be using 'ddf' (delta df) not 'df'")
    else:
        print("✓ df values look reasonable")
    
    # Check what attributes are available
    print("\n3. Available Model Attributes:")
    print("-" * 50)
    
    # These are common OCCAM model attributes
    attrs_to_check = [
        "h", "information", "aic", "bic", "lr", "alpha",
        "df", "ddf", "dAIC", "dBIC", "pct_correct",
        "pct_correct_data", "incr_alpha", "level",
        "processed", "progenitor", "delta_df"
    ]
    
    print(f"Checking attributes for model IV:ApZ:")
    for attr in attrs_to_check:
        try:
            value = apz_model.__getattribute__(attr)
            if value is not None and value != 0:
                print(f"  {attr:<20} = {value}")
        except:
            pass

if __name__ == "__main__":
    test_df()