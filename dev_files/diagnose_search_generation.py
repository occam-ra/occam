#!/usr/bin/env python
"""
Diagnose why some models aren't being generated during search
"""

import pyoccam2

def diagnose_search_generation():
    """Figure out why IV:AgZ and other models aren't being generated"""
    
    print("=" * 80)
    print("SEARCH GENERATION DIAGNOSIS")
    print("=" * 80)
    
    # Initialize manager
    manager = pyoccam2.VBMManager()
    success = manager.init_from_command_line(["occam", "dementia05.txt"])
    
    if not success:
        print("ERROR: Failed to load data")
        return
    
    # Get variable list to understand the mapping
    variables = manager.get_variable_list()
    print("\n1. Variables in dataset:")
    print("-" * 50)
    for i, var in enumerate(variables):
        print(f"  {i:2}: {var}")
    
    # Test individual models to see which ones exist
    print("\n2. Testing which single-variable models can be created:")
    print("-" * 50)
    
    # Try different abbreviations
    test_abbrevs = ['Ap', 'Sx', 'Ed', 'Ag', 'A', 'B', 'C', 'D', 'E', 'F', 
                    'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'P', 'Z']
    
    valid_models = []
    for abbrev in test_abbrevs:
        model_name = f"IV:{abbrev}Z"
        try:
            model = manager.make_model(model_name, False)  # Don't compute stats yet
            if model.name != "ERROR":
                valid_models.append((model_name, model))
                print(f"  ✓ {model_name} exists")
        except:
            pass
    
    print(f"\nFound {len(valid_models)} valid single-variable models")
    
    # Now test the search to see what it generates
    print("\n3. Testing search generation at Level 1:")
    print("-" * 50)
    
    # Run search with debug mode
    manager.set_debug_mode(True)
    print("\nRunning search with debug output...")
    report = manager.generate_search_report("loopless-up", levels=1, width=50)  # Large width to keep all
    
    # Get the generated models
    kept = manager.get_kept_models()
    level1 = [m for m in kept if m.level == 1]
    
    print(f"\n4. Search generated {len(level1)} models at Level 1:")
    print("-" * 50)
    
    # Sort by name for comparison
    level1.sort(key=lambda m: m.name)
    for model in level1:
        print(f"  {model.name}: dBIC={model.dbic:.2f}, Info={model.information:.4f}")
    
    # Compare with expected
    print("\n5. Analysis:")
    print("-" * 50)
    
    expected_count = len(variables) - 1  # All variables except DV
    actual_count = len(level1)
    
    if actual_count < expected_count:
        print(f"✗ PROBLEM: Only {actual_count} models generated, expected ~{expected_count}")
        print("\nMissing models (found manually but not in search):")
        
        search_names = {m.name for m in level1}
        for model_name, _ in valid_models:
            if model_name not in search_names:
                print(f"  - {model_name}")
    else:
        print(f"✓ Generated expected number of models ({actual_count})")
    
    # Check if Age model is there
    age_model = next((m for m in level1 if 'Ag' in m.name), None)
    if age_model:
        print(f"\n✓ Age model found: {age_model.name}")
    else:
        print("\n✗ Age model (IV:AgZ) NOT found in search results!")
    
    # Show top models by different criteria
    print("\n6. Top models by different criteria:")
    print("-" * 50)
    
    # Sort by dBIC
    level1.sort(key=lambda m: m.dbic, reverse=True)
    print("\nBy dBIC (search selection criterion):")
    for model in level1[:5]:
        print(f"  {model.name}: dBIC={model.dbic:.2f}")
    
    # Sort by information
    level1.sort(key=lambda m: m.information, reverse=True)
    print("\nBy Information (report display criterion):")
    for model in level1[:5]:
        print(f"  {model.name}: Info={model.information:.4f}")
    
    return level1

if __name__ == "__main__":
    models = diagnose_search_generation()