#!/usr/bin/env python
"""
Test script to debug search and best model selection issues
"""

import pyoccam2

def main():
    print("=" * 70)
    print("SEARCH AND BEST MODEL DEBUG TEST")
    print("=" * 70)
    
    # Initialize manager
    manager = pyoccam2.VBMManager()
    success = manager.init_from_command_line(["occam", "dementia05.txt"])
    print(f"Initialization: {'Success' if success else 'Failed'}")
    
    if not success:
        print("ERROR: Failed to initialize. Check that dementia05.txt exists.")
        return
    
    # Get basic info
    print(f"Sample size: {manager.get_sample_size()}")
    variables = manager.get_variable_list()
    print(f"Variables: {', '.join(variables)}")
    print()
    
    # Configure search
    print("=" * 70)
    print("SEARCH CONFIGURATION")
    print("=" * 70)
    manager.set_ref_model("bottom")
    manager.set_alpha_threshold(0.05)
    manager.set_debug_mode(True)  # Enable debug output
    print("Reference model: bottom")
    print("Alpha threshold: 0.05")
    print("Search type: full-up")
    print("Levels: 7")
    print("Width: 3")
    print()
    
    # Run search
    print("=" * 70)
    print("RUNNING SEARCH")
    print("=" * 70)
    
    try:
        report = manager.generate_search_report("full-up", 7, 3, False)
        
        # Check if we got a report
        if report.startswith("Error"):
            print(f"ERROR: {report}")
            return
            
        # Print first part of report to see what models were found
        lines = report.split('\n')
        print("First 50 lines of search report:")
        print("-" * 40)
        for i, line in enumerate(lines[:50]):
            print(line)
        print("-" * 40)
        print(f"Total lines in report: {len(lines)}")
        print()
        
    except Exception as e:
        print(f"ERROR during search: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Check best models
    print("=" * 70)
    print("BEST MODEL SELECTION")
    print("=" * 70)
    
    try:
        best_bic = manager.get_best_model_by_bic()
        best_aic = manager.get_best_model_by_aic()
        best_info = manager.get_best_model_by_information()
        best_info_alpha = manager.get_best_model_by_info_alpha()
        
        print(f"Best by BIC: {best_bic if best_bic else 'NONE FOUND'}")
        print(f"Best by AIC: {best_aic if best_aic else 'NONE FOUND'}")
        print(f"Best by Info: {best_info if best_info else 'NONE FOUND'}")
        print(f"Best by Info+Alpha: {best_info_alpha if best_info_alpha else 'NONE FOUND'}")
        print()
        
        # Expected results
        print("EXPECTED (from server):")
        print("Best by BIC: IV:ApZ:EdZ:CZ")
        print("Best by AIC: IV:ApZ:EdCZ:EdKZ:LZ")
        print("Best by Info: IV:ApZ:EdCZ:EdKZ:LZ")
        print("Best by Info+Alpha: IV:ApZ:EdZ:AgZ:CZ:KZ")
        print()
        
    except Exception as e:
        print(f"ERROR getting best models: {e}")
        import traceback
        traceback.print_exc()
    
    # Get kept models
    print("=" * 70)
    print("KEPT MODELS FROM SEARCH")
    print("=" * 70)
    
    try:
        kept_models = manager.get_kept_models()
        print(f"Number of kept models: {len(kept_models)}")
        
        if kept_models:
            print("\nFirst 10 kept models:")
            for i, model in enumerate(kept_models[:10]):
                print(f"{i+1}. {model.name}")
                print(f"   Level: {model.level}, Info: {model.information:.6f}")
                print(f"   dBIC: {model.dbic:.2f}, dAIC: {model.daic:.2f}")
                print(f"   IncAlpha: {model.incr_alpha:.6f}, Reachable: {model.incr_alpha_reachable}")
        else:
            print("NO KEPT MODELS FOUND!")
            
    except Exception as e:
        print(f"ERROR getting kept models: {e}")
        import traceback
        traceback.print_exc()
    
    # Debug incremental alpha status
    print("\n" + "=" * 70)
    print("INCREMENTAL ALPHA DEBUG")
    print("=" * 70)
    
    try:
        manager.debug_incr_alpha_status()
    except Exception as e:
        print(f"ERROR in debug_incr_alpha_status: {e}")
    
    # Test specific model creation
    print("\n" + "=" * 70)
    print("TEST SPECIFIC MODEL CREATION")
    print("=" * 70)
    
    test_models = [
        "IV:Z",
        "IV:ApZ",
        "IV:ApZ:EdZ",
        "IV:ApZ:EdZ:CZ",
        "IV:ApZ:EdZ:AgZ:CZ:KZ"
    ]
    
    for model_name in test_models:
        try:
            stats = manager.get_model_statistics(model_name)
            print(f"\n{model_name}:")
            print(f"  Info: {stats.information:.6f}")
            print(f"  dBIC: {stats.dbic:.2f}")
            print(f"  IncAlpha: {stats.incr_alpha:.6f}")
        except Exception as e:
            print(f"\n{model_name}: ERROR - {e}")
    
    print("\n" + "=" * 70)
    print("TEST COMPLETE")
    print("=" * 70)

if __name__ == "__main__":
    main()
