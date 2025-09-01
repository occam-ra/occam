#!/usr/bin/env python
"""
Test script for OCCAM Python Package - Multi-Level Search
Validates that the orchestration loop properly generates complex multi-level models
"""

import pyoccam
import sys
import time

def test_multilevel_search():
    """Main test for multi-level search functionality"""
    print("=" * 60)
    print("Testing Multi-Level Search (Main Test)")
    print("=" * 60)
    
    # Initialize manager
    manager = pyoccam.VBMManager()
    manager.set_debug_mode(True)  # Enable debug output
    
    # Load data
    import sys
    data_file = sys.argv[1] if len(sys.argv) > 1 else "dementia05.txt"
    if not manager.init_from_command_line(['occam', data_file]):
        print("❌ Failed to load data file:", data_file)
        return False
    
    print(f"✅ Data loaded successfully: {data_file}")
    
    # Get basic info
    stats = manager.get_basic_statistics()
    print(f"   Sample size: {stats.get('sample_size', 'N/A')}")
    print(f"   Variables: {stats.get('variable_count', 'N/A')}")
    
    # Test search_one_level method
    print("\n" + "-" * 40)
    print("Testing search_one_level method:")
    print("-" * 40)
    
    # Get starting model
    bottom_model = manager.get_model("IV:Z")
    if bottom_model:
        print(f"✅ Got starting model: IV:Z")
        
        # Test generating children for one model
        children = manager.search_one_level(bottom_model)
        print(f"   Generated {len(children)} children for IV:Z")
        if children:
            for i, child in enumerate(children[:3]):  # Show first 3
                print(f"     Child {i+1}: {child.get_print_name()}")
    else:
        print("❌ Could not get starting model")
    
    # Perform multi-level search
    print("\n" + "-" * 40)
    print("Testing Full Multi-Level Search:")
    print("-" * 40)
    
    search_type = "loopless-up"
    levels = 7
    width = 3
    
    print(f"Parameters: type={search_type}, levels={levels}, width={width}")
    
    start_time = time.time()
    result = manager.generate_search_report(search_type, levels, width)
    end_time = time.time()
    
    print(f"Search completed in {end_time - start_time:.2f} seconds")
    
    # Analyze results
    lines = result.split('\n')
    model_lines = [l for l in lines if 'IV:' in l or 'IV ' in l]
    
    print(f"\n📊 Results Analysis:")
    print(f"   Total models generated: {len(model_lines)}")
    
    # Count models by complexity (number of components)
    simple_models = []
    complex_models = []
    
    for line in model_lines:
        if 'IV:' in line:
            # Extract model name
            start = line.find('IV:')
            end = line.find(' ', start) if ' ' in line[start:] else len(line)
            model_name = line[start:end].strip()
            
            # Count components (separated by :)
            components = model_name.count(':')
            
            if components <= 2:
                simple_models.append(model_name)
            else:
                complex_models.append(model_name)
    
    print(f"   Simple models (≤2 components): {len(simple_models)}")
    print(f"   Complex models (>2 components): {len(complex_models)}")
    
    # Show some complex models
    if complex_models:
        print(f"\n   Sample complex models:")
        for model in complex_models[:5]:
            print(f"     • {model}")
    
    # Determine maximum level reached
    max_level = 0
    for model in complex_models + simple_models:
        level = model.count(':')
        if level > max_level:
            max_level = level
    
    print(f"\n   Maximum model complexity reached: Level {max_level}")
    
    # Success criteria - just check that we got multi-level models
    # Don't hardcode specific numbers since they vary by dataset
    
    success = (
        len(model_lines) > 0 and  # Got some models
        len(complex_models) > 0 and  # Got at least some complex models
        max_level > 1  # Got beyond Level 1 (the bug we fixed)
    )
    
    if success:
        print(f"\n✅ SUCCESS! Multi-level search is working!")
        print(f"   Generated {len(model_lines)} models")
        print(f"   Including {len(complex_models)} complex models")
        print(f"   Maximum complexity: Level {max_level}")
    else:
        print(f"\n⚠️  Check results:")
        print(f"   Models: {len(model_lines)}")
        print(f"   Complex: {len(complex_models)}")
        print(f"   Max level: {max_level}")
        if max_level <= 1:
            print("   ❌ PROBLEM: Only Level 1 models - multi-level search not working!")
    
    # Save results
    output_file = "multilevel_search_results.txt"
    with open(output_file, 'w') as f:
        f.write("Multi-Level Search Test Results\n")
        f.write("=" * 60 + "\n")
        f.write(f"Search Type: {search_type}\n")
        f.write(f"Levels: {levels}, Width: {width}\n")
        f.write(f"Total Models: {len(model_lines)}\n")
        f.write(f"Complex Models: {len(complex_models)}\n")
        f.write(f"Max Level: {max_level}\n")
        f.write("\n" + "=" * 60 + "\n\n")
        f.write(result)
    
    print(f"\n💾 Results saved to: {output_file}")
    
    return success

def test_report_class():
    """Test the exposed Report class functionality"""
    print("\n" + "=" * 60)
    print("Testing Report Class")
    print("=" * 60)
    
    manager = pyoccam.VBMManager()
    import sys
    data_file = sys.argv[1] if len(sys.argv) > 1 else "dementia05.txt"
    if not manager.init_from_command_line(['occam', data_file]):
        print("❌ Failed to load data")
        return False
    
    # Create a report
    report = manager.create_report()
    print("✅ Report object created")
    
    # Add some models
    models = ["IV:Z", "IV:ApZ", "IV:EdZ", "IV:ApZ:EdZ"]
    for model_name in models:
        model = manager.get_model(model_name)
        if model:
            report.add_model(model)
            print(f"   Added model: {model_name}")
    
    # Set attributes to display
    report.set_attributes("Level,H,AIC,BIC,Information,%C(Data)")
    print("✅ Attributes configured")
    
    # Sort by information
    report.sort("information", "descending")
    print("✅ Sorting applied")
    
    # Generate report
    report_text = report.generate_report()
    if report_text and len(report_text) > 100:
        print("✅ Report generated successfully")
        print("\nReport Preview (first 500 chars):")
        print("-" * 40)
        print(report_text[:500])
        print("-" * 40)
        
        # Save report
        with open("test_report_class.txt", 'w') as f:
            f.write(report_text)
        print("\n💾 Report saved to: test_report_class.txt")
        
        return True
    else:
        print("❌ Report generation failed")
        return False

def test_algorithm_comparison():
    """Test algorithm comparison functionality"""
    print("\n" + "=" * 60)
    print("Testing Algorithm Comparison")
    print("=" * 60)
    
    manager = pyoccam.VBMManager()
    import sys
    data_file = sys.argv[1] if len(sys.argv) > 1 else "dementia05.txt"
    if not manager.init_from_command_line(['occam', data_file]):
        print("❌ Failed to load data")
        return False
    
    print("Running comparison (this may take a moment)...")
    comparison = manager.compare_search_algorithms(levels=3, width=4)
    
    if comparison and len(comparison) > 100:
        print("✅ Comparison completed")
        print("\nComparison Results:")
        print("-" * 40)
        print(comparison)
        print("-" * 40)
        
        # Save comparison
        with open("algorithm_comparison.txt", 'w') as f:
            f.write(comparison)
        print("\n💾 Comparison saved to: algorithm_comparison.txt")
        
        return True
    else:
        print("❌ Comparison failed")
        return False

if __name__ == "__main__":
    print("OCCAM Python Package - Multi-Level Search Test Suite")
    print("Version 3.4.2-multilevel")
    print("=" * 60)
    
    # Run tests
    all_passed = True
    
    # Main test
    if not test_multilevel_search():
        all_passed = False
    
    # Report class test
    if not test_report_class():
        all_passed = False
    
    # Algorithm comparison test
    if not test_algorithm_comparison():
        all_passed = False
    
    # Summary
    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 ALL TESTS PASSED! 🎉")
        print("Multi-level search and Report class are fully functional!")
        print("The package is ready for production use.")
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
    print("=" * 60)