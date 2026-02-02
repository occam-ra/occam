#!/usr/bin/env python3
"""
Example: Using OCCAM Python Package with occ.cpp orchestration
This mirrors the weboccam.py approach
"""

import pyoccam
from datetime import datetime

def main():
    """Demonstrate the new OCCAM Python architecture"""
    
    print("🚀 OCCAM Python Package - occ.cpp Orchestration Example")
    print("=" * 60)
    print(f"Version: {pyoccam.__version__}")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Initialize OCCAM manager
    print("\n📊 Initializing OCCAM Manager...")
    manager = pyoccam.VBMManager()
    
    # Load data file
    data_file = "dementia05.txt"
    if not manager.init_from_command_line(["occam", data_file]):
        print("❌ Failed to initialize OCCAM")
        return False
    
    print(f"✅ Loaded data file: {data_file}")
    
    # Display basic information
    print("\n📈 Dataset Information:")
    print("-" * 30)
    
    stats = manager.get_basic_statistics()
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    variables = manager.get_variable_list()
    print(f"  Variables: {len(variables)}")
    for i, var in enumerate(variables[:5], 1):  # Show first 5
        print(f"    {i}. {var}")
    if len(variables) > 5:
        print(f"    ... and {len(variables) - 5} more")
    
    # Configure search
    print("\n🔍 Configuring Search:")
    print("-" * 25)
    
    search_type = "loopless-up"
    levels = 7
    width = 3
    
    manager.set_report_separator(pyoccam.SPACESEP)
    manager.set_ref_model("bottom")
    
    print(f"  Search Type: {search_type}")
    print(f"  Levels: {levels}")
    print(f"  Width: {width}")
    print(f"  Reference: bottom")
    
    # Perform search by calling occ.cpp
    print("\n⚡ Calling occ.cpp for search...")
    print("-" * 35)
    
    # This is where the magic happens - Python calls occ.cpp!
    search_output = manager.generate_search_report(search_type, levels, width)
    
    if search_output.startswith("ERROR:"):
        print(f"❌ Search failed: {search_output}")
        return False
    
    print("✅ Search completed successfully!")
    
    # Display the PERFECT server output
    print("\n📋 SEARCH RESULTS (from occ.cpp):")
    print("=" * 50)
    print(search_output)
    
    # Extract best models
    print("\n🏆 Best Models:")
    print("-" * 20)
    
    best_bic = manager.get_best_model_by_bic()
    best_aic = manager.get_best_model_by_aic()
    best_info = manager.get_best_model_by_information()
    
    if best_bic:
        print(f"  Best by BIC: {best_bic}")
    if best_aic:
        print(f"  Best by AIC: {best_aic}")
    if best_info:
        print(f"  Best by Information: {best_info}")
    
    # Perform fit analysis on best model
    if best_bic:
        print(f"\n🔬 Fit Analysis for {best_bic}:")
        print("-" * 40)
        
        print("⚡ Calling occ.cpp for fit analysis...")
        fit_output = manager.generate_fit_report(best_bic, "0")
        
        if not fit_output.startswith("ERROR:"):
            print("✅ Fit analysis completed!")
            
            # Show first part of fit output
            fit_lines = fit_output.split('\n')[:20]  # First 20 lines
            for line in fit_lines:
                if line.strip():
                    print(f"  {line}")
            
            if len(fit_output.split('\n')) > 20:
                print("  ... (truncated)")
            
            # Get confusion matrix
            print("\n📊 Confusion Matrix:")
            print("-" * 25)
            
            cm = manager.get_confusion_matrix(best_bic, "0")
            if "error" not in cm:
                for metric, value in cm.items():
                    print(f"  {metric.capitalize()}: {value:.3f}")
            else:
                print(f"  Error: {cm['error']}")
        else:
            print(f"❌ Fit failed: {fit_output}")
    
    print("\n🎉 Analysis Complete!")
    print("=" * 40)
    print("✅ Successfully called occ.cpp for both search and fit")
    print("✅ Parsed perfect server output")
    print("✅ Extracted best models and statistics")
    
    return True

def quick_example():
    """Show the convenience functions"""
    
    print("\n🚀 Quick Convenience Functions:")
    print("=" * 35)
    
    # Quick search
    print("📊 Quick search...")
    result = pyoccam.search("dementia05.txt", "loopless-up", 3, 3)
    
    if not result.startswith("ERROR:"):
        print("✅ Quick search successful!")
        print("First few lines:")
        for line in result.split('\n')[:5]:
            if line.strip():
                print(f"  {line}")
    else:
        print(f"❌ Quick search failed: {result}")

if __name__ == "__main__":
    try:
        success = main()
        
        if success:
            quick_example()
            
        print(f"\n✨ Demo completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Error during demo: {e}")
        import traceback
        traceback.print_exc()
