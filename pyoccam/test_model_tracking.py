#!/usr/bin/env python
"""
Test script to validate OCCAM's beam search implementation
Demonstrates how beam search keeps only WIDTH best models at each level
"""

import pyoccam2

def test_beam_search():
    """Test OCCAM's beam search implementation"""
    
    print("=" * 70)
    print("OCCAM BEAM SEARCH TEST")
    print("=" * 70)
    
    # Initialize manager
    manager = pyoccam2.VBMManager()
    
    # Load data
    print("\n1. Loading data...")
    success = manager.init_from_command_line(["occam", "dementia05.txt"])
    if not success:
        print("ERROR: Failed to load data")
        return
    
    print("   Data loaded successfully")
    print(f"   Sample size: {manager.get_sample_size()}")
    print(f"   Variables: {', '.join(manager.get_variable_list())}")
    
    # Configure
    print("\n2. Configuring search...")
    manager.set_report_separator(pyoccam2.SPACESEP)
    manager.set_ref_model("bottom")
    print("   Report separator: SPACE")
    print("   Reference model: bottom")
    
    # Run search with width=3, levels=3
    print("\n3. Running beam search...")
    print("   Algorithm: loopless-up")
    print("   Levels: 3")
    print("   Width: 3 (beam size - keep 3 best models per level)")
    
    search_report = manager.generate_search_report("loopless-up", levels=3, width=3)
    
    # Get the kept models (the beam)
    kept_models = manager.get_kept_models()
    
    print("\n4. Beam Search Results:")
    print("-" * 50)
    print(f"   Total models in beam (kept): {len(kept_models)}")
    print(f"   Expected maximum: 1 + (3 * 3) = 10 models")
    print(f"   (1 reference + up to 3 per level for 3 levels)")
    
    # Show kept models by level
    print("\n5. Beam Models by Level:")
    print("-" * 50)
    levels_dict = {}
    for model in kept_models:
        level = model.level
        if level not in levels_dict:
            levels_dict[level] = []
        levels_dict[level].append(model)
    
    for level in sorted(levels_dict.keys()):
        models_at_level = levels_dict[level]
        print(f"\n   Level {level}: {len(models_at_level)} models in beam")
        # Sort by dBIC for display
        models_at_level.sort(key=lambda m: m.dbic, reverse=True)
        for model in models_at_level:
            print(f"      {model.name:20s} dBIC={model.dbic:8.3f} dAIC={model.daic:8.3f}")
    
    # Get best models (from the beam)
    print("\n6. Best Models (from beam):")
    print("-" * 50)
    best_bic = manager.get_best_model_by_bic()
    best_aic = manager.get_best_model_by_aic()
    best_info = manager.get_best_model_by_information()
    
    print(f"   Best by BIC:         {best_bic}")
    print(f"   Best by AIC:         {best_aic}")
    print(f"   Best by Information: {best_info}")
    
    # Verify best models are in kept set
    kept_names = {m.name for m in kept_models}
    print("\n7. Verification:")
    print("-" * 50)
    
    for criterion, model_name in [("BIC", best_bic), ("AIC", best_aic), ("Information", best_info)]:
        if model_name:
            assert model_name in kept_names, f"Best {criterion} model not in kept set!"
            print(f"   ✓ Best {criterion} model is in the beam (as expected)")
    
    # Show search report
    print("\n8. Search Report (beam models):")
    print("=" * 70)
    print(search_report)
    
    # Key insights
    print("\n9. Key Insights about Beam Search:")
    print("-" * 50)
    print("   - Only WIDTH best models kept at each level")
    print("   - Only kept models expanded at next level")
    print("   - Best model MUST be in the kept set")
    print("   - No exponential explosion of models")
    print("   - Efficient and tractable search")

def compare_beam_widths():
    """Compare different beam widths to show the effect"""
    
    print("\n" + "=" * 70)
    print("COMPARING DIFFERENT BEAM WIDTHS")
    print("=" * 70)
    
    widths = [1, 3, 5, 10]
    
    for width in widths:
        print(f"\n--- Beam Width = {width} ---")
        
        manager = pyoccam2.VBMManager()
        manager.init_from_command_line(["occam", "dementia05.txt"])
        manager.set_ref_model("bottom")
        
        # Run search
        _ = manager.generate_search_report("loopless-up", levels=3, width=width)
        
        kept = manager.get_kept_models()
        best_bic = manager.get_best_model_by_bic()
        
        print(f"   Beam size (kept models): {len(kept)}")
        print(f"   Best BIC model: {best_bic}")
        
        # Calculate theoretical maximum
        max_possible = 1 + (width * 3)  # ref + (width per level × levels)
        print(f"   Theoretical maximum: {max_possible}")
        print(f"   Efficiency: {len(kept)}/{max_possible} slots used")

def demonstrate_beam_pruning():
    """Show how beam search prunes the search space"""
    
    print("\n" + "=" * 70)
    print("BEAM SEARCH PRUNING DEMONSTRATION")
    print("=" * 70)
    
    manager = pyoccam2.VBMManager()
    manager.init_from_command_line(["occam", "dementia05.txt"])
    manager.set_ref_model("bottom")
    
    # Run with very narrow beam
    print("\n--- Narrow Beam (width=1) - Greedy Search ---")
    _ = manager.generate_search_report("loopless-up", levels=5, width=1)
    narrow_models = manager.get_kept_models()
    narrow_best = manager.get_best_model_by_bic()
    
    # Run with wider beam
    print("\n--- Wide Beam (width=5) - Broader Search ---")
    manager2 = pyoccam2.VBMManager()
    manager2.init_from_command_line(["occam", "dementia05.txt"])
    manager2.set_ref_model("bottom")
    _ = manager2.generate_search_report("loopless-up", levels=5, width=5)
    wide_models = manager2.get_kept_models()
    wide_best = manager2.get_best_model_by_bic()
    
    print("\nResults:")
    print(f"   Narrow beam (width=1): {len(narrow_models)} models, best = {narrow_best}")
    print(f"   Wide beam (width=5):   {len(wide_models)} models, best = {wide_best}")
    
    if narrow_best != wide_best:
        print("\n   ⚠ Different best models found!")
        print("   The narrow beam may have pruned away better models.")
        print("   This demonstrates why beam width matters.")
    else:
        print("\n   ✓ Same best model found with both widths.")
        print("   The narrow beam was sufficient for this search.")

if __name__ == "__main__":
    # Run main test
    test_beam_search()
    
    # Compare widths
    compare_beam_widths()
    
    # Demonstrate pruning
    demonstrate_beam_pruning()
    
    print("\n" + "=" * 70)
    print("TEST COMPLETE")
    print("=" * 70)