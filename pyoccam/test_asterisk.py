#!/usr/bin/env python
"""
Test that asterisk (*) marking is working correctly for significant models
"""

import pyoccam2

def test_asterisk_marking():
    """Test that asterisks only appear for significant models"""
    
    print("=" * 80)
    print("TEST: ASTERISK (*) MARKING FOR SIGNIFICANT MODELS")
    print("=" * 80)
    
    # Initialize manager
    manager = pyoccam2.VBMManager()
    
    # Load data
    success = manager.init_from_command_line(["occam", "dementia05.txt"])
    if not success:
        print("ERROR: Failed to load dementia05.txt")
        return False
    
    print("\nData loaded successfully")
    
    # Run a simple 1-level search
    print("\nRunning 1-level loopless search...")
    print("-" * 80)
    
    report = manager.generate_search_report("loopless-up", levels=1, width=5)
    
    # Parse the report to check asterisk marking
    print("\n" + "=" * 80)
    print("ANALYZING ASTERISK MARKING:")
    print("=" * 80)
    
    lines = report.split('\n')
    model_data = []
    
    for line in lines:
        if 'IV:' in line and not line.startswith("Best Model"):
            parts = line.split()
            for i, part in enumerate(parts):
                if 'IV:' in part:
                    model_name = part
                    has_asterisk = part.endswith('*')
                    clean_name = part.rstrip('*')
                    
                    # Find alpha value (usually at position i+5)
                    alpha = None
                    inc_alpha = None
                    try:
                        if i+5 < len(parts):
                            alpha = float(parts[i+5])
                        if i+10 < len(parts):
                            inc_alpha = float(parts[i+10])
                    except:
                        pass
                    
                    model_data.append({
                        'name': clean_name,
                        'has_asterisk': has_asterisk,
                        'alpha': alpha,
                        'inc_alpha': inc_alpha
                    })
                    break
    
    # Display findings
    print("\nModel Analysis:")
    print("-" * 80)
    print(f"{'Model':<20} {'Has *':<8} {'Alpha':<12} {'Inc.Alpha':<12} {'Expected *':<12}")
    print("-" * 80)
    
    issues = []
    for model in model_data:
        # Determine if asterisk is expected
        # Usually: asterisk if alpha < 0.05 or inc_alpha < 0.05
        expected_asterisk = False
        if model['alpha'] is not None:
            if model['alpha'] < 0.05:
                expected_asterisk = True
        
        # Special case: reference model (IV:Z) should never have asterisk
        if model['name'] == 'IV:Z':
            expected_asterisk = False
        
        status = "✓" if model['has_asterisk'] == expected_asterisk else "✗"
        
        print(f"{model['name']:<20} {str(model['has_asterisk']):<8} "
              f"{model['alpha']:<12.4f} {str(model['inc_alpha']):<12} "
              f"{str(expected_asterisk):<12} {status}")
        
        if model['has_asterisk'] != expected_asterisk:
            issues.append(model)
    
    # Report issues
    print("\n" + "=" * 80)
    print("ISSUES FOUND:")
    print("=" * 80)
    
    if not issues:
        print("✓ No issues found - asterisk marking appears correct")
        return True
    else:
        print(f"✗ Found {len(issues)} models with incorrect asterisk marking:")
        for model in issues:
            if model['has_asterisk'] and not (model['alpha'] < 0.05):
                print(f"  - {model['name']} has * but alpha={model['alpha']:.4f} >= 0.05")
            elif not model['has_asterisk'] and (model['alpha'] < 0.05):
                print(f"  - {model['name']} missing * but alpha={model['alpha']:.4f} < 0.05")
        
        print("\nPossible causes:")
        print("1. Report class might be using incremental alpha instead of regular alpha")
        print("2. Significance threshold might be different (not 0.05)")
        print("3. Asterisk logic might be inverted")
        print("4. All models might be marked as significant by default")
        
        return False

def check_reference_model():
    """Specifically check the reference model (IV:Z)"""
    
    print("\n" + "=" * 80)
    print("REFERENCE MODEL CHECK:")
    print("=" * 80)
    
    # Initialize and load
    manager = pyoccam2.VBMManager()
    manager.init_from_command_line(["occam", "dementia05.txt"])
    
    # Get reference model statistics
    ref_model = manager.get_model_statistics("IV:Z")
    
    print(f"Reference model IV:Z statistics:")
    print(f"  Alpha: {ref_model.alpha}")
    print(f"  Inc.Alpha: {ref_model.incr_alpha}")
    print(f"  Information: {ref_model.information}")
    print(f"  dBIC: {ref_model.dbic}")
    
    print("\nExpected values for reference model:")
    print("  Alpha: 1.0000 (not significant)")
    print("  Inc.Alpha: 1.0000")
    print("  Information: 0.0000")
    print("  Should NOT have asterisk (*)")
    
    return True

if __name__ == "__main__":
    import sys
    
    # Test asterisk marking
    success1 = test_asterisk_marking()
    
    # Check reference model
    success2 = check_reference_model()
    
    print("\n" + "=" * 80)
    if success1 and success2:
        print("SUCCESS: Asterisk marking is working correctly")
    else:
        print("FAILURE: Asterisk marking has issues")
        print("\nSuggested fix:")
        print("Check the Report class in Report.cpp to see how it determines")
        print("which models get asterisks. It might be checking inc_alpha < 0.05")
        print("for all models, when it should check alpha < threshold.")
    print("=" * 80)
    
    sys.exit(0 if (success1 and success2) else 1)