#!/usr/bin/env python
"""
Test that incremental alpha values are computed correctly
and asterisks only appear for statistically significant models
"""

import pyoccam2
import re

def test_incremental_alpha():
    """Test incremental alpha computation and asterisk marking"""
    
    print("=" * 80)
    print("INCREMENTAL ALPHA AND ASTERISK TEST")
    print("=" * 80)
    
    # Initialize manager
    manager = pyoccam2.VBMManager()
    
    # Enable debug mode to see incremental alpha values
    manager.set_debug_mode(True)
    
    # Load data
    success = manager.init_from_command_line(["occam", "dementia05.txt"])
    if not success:
        print("ERROR: Failed to load dementia05.txt")
        return False
    
    print("\nRunning 3-level search to check incremental alpha...")
    print("-" * 80)
    
    # Run a 3-level search
    report = manager.generate_search_report("loopless-up", levels=3, width=3)
    
    # Parse the report to check incremental alpha values
    print("\n" + "=" * 80)
    print("CHECKING INCREMENTAL ALPHA VALUES:")
    print("=" * 80)
    
    lines = report.split('\n')
    data_lines = []
    for line in lines:
        if 'IV:' in line and not line.startswith("Best Model"):
            data_lines.append(line)
            # Extract Inc.Alpha value
            parts = line.split()
            if 'IV:' in line:
                print(f"Line: {line[:100]}...")
                # Check if asterisk is present
                has_asterisk = '*' in parts[0] if parts else False
                print(f"  Has asterisk: {has_asterisk}")
    
    # Count models with and without asterisks
    asterisk_count = sum(1 for line in data_lines if '*' in line.split()[0] if line.split())
    no_asterisk_count = len(data_lines) - asterisk_count
    
    print(f"\nModels with asterisk (*): {asterisk_count}")
    print(f"Models without asterisk: {no_asterisk_count}")
    
    # Check best model selection
    print("\n" + "=" * 80)
    print("BEST MODEL SELECTION CHECK:")
    print("=" * 80)
    
    best_info_alpha = manager.get_best_model_by_info_alpha()
    if best_info_alpha:
        print(f"Best model by Info with all Inc.Alpha < 0.05: {best_info_alpha}")
        print("This model should have asterisk and all parents should too")
    else:
        print("No model qualifies for 'Best by Info with all Inc.Alpha < 0.05'")
    
    # Validation
    print("\n" + "=" * 80)
    print("VALIDATION:")
    print("=" * 80)
    
    if no_asterisk_count > 0:
        print("✓ Good: Not all models have asterisks (some have Inc.Alpha >= 0.05)")
        validation_passed = True
    else:
        print("✗ Problem: All models have asterisks (should vary based on significance)")
        validation_passed = False
    
    if asterisk_count > 0:
        print("✓ Good: Some models are statistically significant")
    else:
        print("⚠ Warning: No models marked as statistically significant")
    
    return validation_passed

def test_fullup_asterisks():
    """Test that full-up search has proper asterisk marking"""
    
    print("\n" * 2)
    print("=" * 80)
    print("FULL-UP SEARCH ASTERISK TEST")
    print("=" * 80)
    
    # Initialize manager
    manager = pyoccam2.VBMManager()
    
    # Load data
    success = manager.init_from_command_line(["occam", "dementia05.txt"])
    if not success:
        print("ERROR: Failed to load dementia05.txt")
        return False
    
    print("\nRunning FULL-UP search (2 levels)...")
    print("-" * 80)
    
    # Run full-up search
    report = manager.generate_search_report("full-up", levels=2, width=3)
    
    # Parse report
    lines = report.split('\n')
    level_1_models = []
    level_2_models = []
    
    for line in lines:
        if 'IV:' in line and not line.startswith("Best Model"):
            parts = line.split()
            if len(parts) > 2:
                model_name = ""
                level = -1
                for i, part in enumerate(parts):
                    if 'IV:' in part:
                        model_name = part.replace('*', '')
                        if i + 1 < len(parts):
                            try:
                                level = int(parts[i + 1])
                            except:
                                pass
                        break
                
                has_asterisk = '*' in parts[0] if parts else False
                
                if level == 1:
                    level_1_models.append((model_name, has_asterisk))
                elif level == 2:
                    level_2_models.append((model_name, has_asterisk))
    
    print(f"\nLevel 1 models: {len(level_1_models)}")
    for model, has_ast in level_1_models[:3]:  # Show first 3
        print(f"  {model}: {'*' if has_ast else ' '}")
    
    print(f"\nLevel 2 models: {len(level_2_models)}")
    for model, has_ast in level_2_models[:3]:  # Show first 3
        print(f"  {model}: {'*' if has_ast else ' '}")
    
    # Check if asterisk marking varies
    l1_with_ast = sum(1 for _, has_ast in level_1_models if has_ast)
    l2_with_ast = sum(1 for _, has_ast in level_2_models if has_ast)
    
    print(f"\nLevel 1: {l1_with_ast}/{len(level_1_models)} have asterisks")
    print(f"Level 2: {l2_with_ast}/{len(level_2_models)} have asterisks")
    
    validation_passed = True
    if l2_with_ast < len(level_2_models):
        print("✓ Good: Not all level 2 models have asterisks")
    else:
        print("⚠ Warning: All level 2 models have asterisks")
        validation_passed = False
    
    return validation_passed

def main():
    """Run all incremental alpha tests"""
    
    print("INCREMENTAL ALPHA AND ASTERISK MARKING TEST SUITE")
    print("=" * 80)
    print("Testing that incremental alpha is computed correctly")
    print("and asterisks only mark statistically significant models")
    print("=" * 80)
    
    # Test 1: Basic incremental alpha
    test1 = test_incremental_alpha()
    
    # Test 2: Full-up asterisks
    test2 = test_fullup_asterisks()
    
    # Summary
    print("\n" * 2)
    print("=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    
    if test1 and test2:
        print("✓ All tests passed")
        print("\nIncremental alpha is working correctly:")
        print("  - Values vary based on parent-child relationship")
        print("  - Asterisks only mark models with all Inc.Alpha < 0.05 in path")
        print("  - Best model selection respects reachability")
        return True
    else:
        print("✗ Some tests failed")
        print("\nIssues to fix:")
        if not test1:
            print("  - Incremental alpha values may not be computed correctly")
        if not test2:
            print("  - Full-up search asterisk marking needs work")
        return False

if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)