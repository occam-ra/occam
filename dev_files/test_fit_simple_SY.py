#!/usr/bin/env python
"""
Simple test to debug where fit report is hanging
"""

import pyoccam2
import sys

def test_step_by_step():
    """Test fit report step by step to find where it hangs"""
    
    print("DEBUGGING FIT REPORT HANG")
    print("=" * 80)
    
    # Step 1: Initialize
    print("\n1. Initializing manager...")
    manager = pyoccam2.VBMManager()
    print("   ✓ Manager created")
    
    # Step 2: Load data
    print("\n2. Loading data...")
    success = manager.init_from_command_line(["occam", "SY_sample_pts_to_occam3_shuffle_split_hdr_no_test_sqz.txt"])
    if not success:
        print("   ✗ Failed to load data")
        return False
    print("   ✓ Data loaded")
    
    # Step 3: Configure
    print("\n3. Configuring...")
    manager.set_report_separator(pyoccam2.TABSEP)
    manager.set_ref_model("bottom")
    print("   ✓ Configuration set")
    
    # Step 4: Try making a simple model first
    print("\n4. Testing make_model...")
    try:
        model = manager.make_model("IV:Z", False)  # Independence model, no fit table
        print(f"   ✓ Made model: {model.name}")
    except Exception as e:
        print(f"   ✗ Error making model: {e}")
        return False
    
    # Step 5: Try making a model with fit table
    print("\n5. Testing make_model with fit table...")
    try:
        model = manager.make_model("IV:Z", True)  # With fit table
        print(f"   ✓ Made model with fit table: {model.name}")
        print(f"     H = {model.h:.4f}")
        print(f"     Information = {model.information:.4f}")
    except Exception as e:
        print(f"   ✗ Error making model with fit table: {e}")
        return False
    
    # Step 6: Try a simple model fit report
    print("\n6. Testing fit report for IV:Z...")
    print("   Calling generate_fit_report...")
    sys.stdout.flush()  # Flush output before potential hang
    
    try:
        fit_report = manager.generate_fit_report("IV:Z")
        print("   ✓ Fit report generated")
        print("\n" + "=" * 80)
        print("FIT REPORT OUTPUT:")
        print("=" * 80)
        print(fit_report)
    except Exception as e:
        print(f"   ✗ Error generating fit report: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Step 7: Try a more complex model
    print("\n7. Testing fit report for IV:ApZ...")
    print("   Calling generate_fit_report...")
    sys.stdout.flush()
    
    try:
        fit_report = manager.generate_fit_report("IV:ElLcZ:FdZ:GlGdZ")
        print("   ✓ Fit report generated")
        print("\n" + "=" * 80)
        print("FIT REPORT OUTPUT:")
        print("=" * 80)
        print(fit_report)
    except Exception as e:
        print(f"   ✗ Error generating fit report: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print("\n" + "=" * 80)
    print("✅ All tests passed - no hanging detected")
    return True

def test_minimal():
    """Absolute minimal test"""
    print("\nMINIMAL TEST")
    print("=" * 80)
    
    manager = pyoccam2.VBMManager()
    print("1. Manager created")
    
    success = manager.init_from_command_line(["occam", "SY_sample_pts_to_occam3_shuffle_split_hdr_no_test_sqz.txt"])
    print(f"2. Data loaded: {success}")
    
    if success:
        print("3. Attempting fit report for IV:Z...")
        sys.stdout.flush()
        
        # Try the simplest possible fit
        try:
            # First just try to make the model
            print("   3a. Making model...")
            model = manager.make_model("IV:ElLcZ:FdZ:GlGdZ", True)
            print(f"   3b. Model made: {model.name}")
            
            # Now try the fit report
            print("   3c. Generating fit report...")
            fit_report = manager.generate_fit_report("IV:ElLcZ:FdZ:GlGdZ")
            print("   3d. Fit report generated!")
            
            # Print first 500 chars to see if we got output
            print("\nFirst 500 chars of output:")
            print(fit_report[:500] if len(fit_report) > 500 else fit_report)
            
        except Exception as e:
            print(f"ERROR: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    return True

def main():
    """Run debugging tests"""
    
    print("PYOCCAM2 FIT REPORT HANG DEBUGGING")
    print("Version 40: Fixed version without lambdas")
    print("=" * 80)
    
    # First try minimal test
    success1 = test_minimal()
    
    if success1:
        # If minimal works, try step by step
        print("\n\n")
        success2 = test_step_by_step()
        return success2
    
    return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)