#!/usr/bin/env python
"""
Test script for pyoccam2 version 38 - with fit reports
Tests both search and fit functionality
"""

import pyoccam2 as pyoccam
import time

def test_search_and_fit():
    """Test search functionality followed by fit on best model"""
    
    print("=" * 80)
    print("OCCAM Python Package - Version 38 Test")
    print("Testing Search and Fit Functionality")
    print("=" * 80)
    
    # Initialize manager
    print("\n1. Initializing OCCAM...")
    manager = pyoccam.VBMManager()
    
    # Load data file
    data_file = "dementia05.txt"  # Or use full path
    success = manager.init_from_command_line(["occam", data_file])
    
    if not success:
        print(f"   ERROR: Failed to load {data_file}")
        return
    
    print(f"   ✓ Loaded {data_file}")
    print(f"   ✓ Sample size: {manager.get_sample_size()}")
    
    # Configure report settings
    print("\n2. Configuring report settings...")
    manager.set_report_separator(pyoccam.SPACESEP)
    manager.set_report_variables("ID$I, Model, Level$I, h, ddf, dLR, Alpha, Inf, %dH(DV), dAIC, dBIC")
    manager.set_ref_model("bottom")
    print("   ✓ Report configured")
    
    # Perform search
    print("\n3. Performing loopless-up search...")
    print("   Parameters: levels=3, width=3")
    
    start_time = time.time()
    search_report = manager.generate_search_report(
        search_type="loopless-up",
        levels=3,  # Keep it reasonable for testing
        width=3,
        include_test_data=False
    )
    search_time = time.time() - start_time
    
    print(f"   ✓ Search completed in {search_time:.2f} seconds")
    
    # Display search results (first 2000 chars)
    print("\n" + "=" * 80)
    print("SEARCH RESULTS:")
    print("=" * 80)
    print(search_report[:2000])
    if len(search_report) > 2000:
        print("\n... [truncated for display] ...")
    
    # Get best models
    print("\n4. Identifying best models...")
    best_bic = manager.get_best_model_by_bic()
    best_aic = manager.get_best_model_by_aic()
    best_info = manager.get_best_model_by_information()
    
    print(f"   Best by BIC: {best_bic}")
    print(f"   Best by AIC: {best_aic}")
    print(f"   Best by Information: {best_info}")
    
    # Generate fit report for best BIC model
    if best_bic:
        print(f"\n5. Generating fit report for best BIC model: {best_bic}")
        
        start_time = time.time()
        fit_report = manager.generate_fit_report(
            model_name=best_bic,
            target_state="0"  # Use Z=0 as negative class for confusion matrix
        )
        fit_time = time.time() - start_time
        
        print(f"   ✓ Fit report generated in {fit_time:.2f} seconds")
        
        # Display fit results (first 3000 chars)
        print("\n" + "=" * 80)
        print("FIT REPORT:")
        print("=" * 80)
        print(fit_report[:3000])
        if len(fit_report) > 3000:
            print("\n... [truncated for display] ...")
    
    # Test a specific model fit
    print("\n6. Testing fit for a specific model...")
    test_model = "IV:ApZ:EdZ:AgZ"  # A model we know should work
    
    print(f"   Fitting model: {test_model}")
    start_time = time.time()
    specific_fit = manager.generate_fit_report(
        model_name=test_model,
        target_state=""  # No confusion matrix for this one
    )
    fit_time = time.time() - start_time
    
    print(f"   ✓ Fit completed in {fit_time:.2f} seconds")
    
    # Show just the first part
    print("\n   Model Statistics:")
    lines = specific_fit.split('\n')
    for line in lines[:20]:  # Show first 20 lines
        if line.strip():
            print(f"   {line}")
    
    print("\n" + "=" * 80)
    print("TEST COMPLETED SUCCESSFULLY!")
    print("=" * 80)
    
    # Save reports to files
    print("\n7. Saving reports to files...")
    
    with open("search_report_v38.txt", "w") as f:
        f.write(search_report)
    print("   ✓ Search report saved to search_report_v38.txt")
    
    if best_bic:
        with open("fit_report_v38.txt", "w") as f:
            f.write(fit_report)
        print("   ✓ Fit report saved to fit_report_v38.txt")
    
    print("\nAll tests completed!")

if __name__ == "__main__":
    test_search_and_fit()