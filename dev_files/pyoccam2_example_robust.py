#!/usr/bin/env python3
"""
Example: Using OCCAM Python Package - Robust Version
Works with current pyoccam setup and handles missing attributes gracefully
"""

import sys
from datetime import datetime

def main():
    """Demonstrate OCCAM Python functionality with current setup"""
    
    print("🚀 OCCAM Python Package - Current Setup Test")
    print("=" * 60)
    
    # Try to import pyoccam and handle different possible setups
    try:
        import pyoccam
        print("✅ pyoccam imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import pyoccam: {e}")
        print("Please ensure pyoccam is installed and in your Python path")
        return False
    
    # Try to get version, but don't fail if it doesn't exist
    try:
        version = getattr(pyoccam, '__version__', 'Unknown')
        print(f"Version: {version}")
    except:
        print("Version: Unknown (no __version__ attribute)")
    
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Try to check what's available in the pyoccam module
    print("\n🔍 Available pyoccam attributes:")
    print("-" * 35)
    pyoccam_attrs = [attr for attr in dir(pyoccam) if not attr.startswith('_')]
    for attr in pyoccam_attrs[:10]:  # Show first 10
        print(f"  • {attr}")
    if len(pyoccam_attrs) > 10:
        print(f"  ... and {len(pyoccam_attrs) - 10} more")
    
    # Try to initialize OCCAM manager
    print("\n📊 Initializing OCCAM Manager...")
    
    # Check if VBMManager exists
    if hasattr(pyoccam, 'VBMManager'):
        try:
            manager = pyoccam.VBMManager()
            print("✅ VBMManager created successfully")
        except Exception as e:
            print(f"❌ Failed to create VBMManager: {e}")
            return False
    else:
        print("❌ VBMManager not found in pyoccam module")
        print("Available classes/functions:")
        for attr in pyoccam_attrs:
            attr_obj = getattr(pyoccam, attr)
            if callable(attr_obj):
                print(f"  • {attr} (callable)")
            else:
                print(f"  • {attr}")
        return False
    
    # Try to load data file
    data_file = "dementia05.txt"
    print(f"\n📁 Loading data file: {data_file}")
    
    # Check if the data file exists
    import os
    if not os.path.exists(data_file):
        print(f"❌ Data file '{data_file}' not found in current directory")
        print("Current directory:", os.getcwd())
        print("Files in current directory:")
        for file in os.listdir('.')[:10]:  # Show first 10 files
            print(f"  • {file}")
        return False
    
    # Try to initialize with data file
    try:
        if hasattr(manager, 'init_from_command_line'):
            success = manager.init_from_command_line(["occam", data_file])
            if success:
                print(f"✅ Loaded data file: {data_file}")
            else:
                print(f"❌ Failed to load data file: {data_file}")
                return False
        else:
            print("❌ Manager doesn't have init_from_command_line method")
            print("Available manager methods:")
            manager_methods = [attr for attr in dir(manager) if not attr.startswith('_')]
            for method in manager_methods:
                print(f"  • {method}")
            return False
    except Exception as e:
        print(f"❌ Error initializing manager: {e}")
        return False
    
    # Try to get basic information
    print("\n📈 Dataset Information:")
    print("-" * 30)
    
    # Try different methods to get basic stats
    stats = {}
    
    if hasattr(manager, 'get_basic_statistics'):
        try:
            stats = manager.get_basic_statistics()
            print("✅ Got basic statistics:")
            for key, value in stats.items():
                print(f"  {key}: {value}")
        except Exception as e:
            print(f"⚠️ Error getting basic statistics: {e}")
    
    if hasattr(manager, 'get_variable_list'):
        try:
            variables = manager.get_variable_list()
            print(f"✅ Variables: {len(variables)}")
            for i, var in enumerate(variables[:5], 1):  # Show first 5
                print(f"    {i}. {var}")
            if len(variables) > 5:
                print(f"    ... and {len(variables) - 5} more")
        except Exception as e:
            print(f"⚠️ Error getting variable list: {e}")
    
    if hasattr(manager, 'get_sample_size'):
        try:
            sample_size = manager.get_sample_size()
            print(f"✅ Sample size: {sample_size}")
        except Exception as e:
            print(f"⚠️ Error getting sample size: {e}")
    
    # Try to perform a search
    print("\n🔍 Testing Search Functionality:")
    print("-" * 35)
    
    if hasattr(manager, 'generate_search_report'):
        try:
            print("⚡ Attempting search...")
            
            # Configure search
            search_type = "loopless-up"
            levels = 3  # Smaller search for testing
            width = 2
            
            # Set configuration if methods exist
            if hasattr(manager, 'set_report_separator'):
                try:
                    # Try to use constants if available
                    spacesep = getattr(pyoccam, 'SPACESEP', 3)
                    manager.set_report_separator(spacesep)
                    print(f"✅ Set report separator to {spacesep}")
                except Exception as e:
                    print(f"⚠️ Error setting report separator: {e}")
            
            if hasattr(manager, 'set_ref_model'):
                try:
                    manager.set_ref_model("bottom")
                    print("✅ Set reference model to 'bottom'")
                except Exception as e:
                    print(f"⚠️ Error setting reference model: {e}")
            
            # Attempt the search
            print(f"🔍 Calling generate_search_report({search_type}, {levels}, {width})...")
            
            search_output = manager.generate_search_report(search_type, levels, width)
            
            if search_output and not search_output.startswith("ERROR"):
                print("✅ Search completed successfully!")
                
                # Show first part of output
                lines = search_output.split('\n')[:15]  # First 15 lines
                print("\n📋 Search Output (first 15 lines):")
                print("-" * 40)
                for line in lines:
                    if line.strip():
                        print(f"  {line}")
                
                if len(search_output.split('\n')) > 15:
                    print("  ... (truncated)")
                
                # Try to get best models
                print("\n🏆 Testing Best Model Extraction:")
                print("-" * 35)
                
                if hasattr(manager, 'get_best_model_by_bic'):
                    try:
                        best_bic = manager.get_best_model_by_bic()
                        if best_bic:
                            print(f"✅ Best by BIC: {best_bic}")
                        else:
                            print("⚠️ No best BIC model found")
                    except Exception as e:
                        print(f"⚠️ Error getting best BIC model: {e}")
                
                if hasattr(manager, 'get_best_model_by_information'):
                    try:
                        best_info = manager.get_best_model_by_information()
                        if best_info:
                            print(f"✅ Best by Information: {best_info}")
                        else:
                            print("⚠️ No best Information model found")
                    except Exception as e:
                        print(f"⚠️ Error getting best Information model: {e}")
                
            else:
                print(f"❌ Search failed: {search_output}")
                return False
                
        except Exception as e:
            print(f"❌ Error during search: {e}")
            import traceback
            traceback.print_exc()
            return False
    else:
        print("❌ generate_search_report method not available")
        print("Available manager methods:")
        manager_methods = [attr for attr in dir(manager) if not attr.startswith('_') and callable(getattr(manager, attr))]
        for method in manager_methods:
            print(f"  • {method}")
        return False
    
    print("\n🎉 Test Complete!")
    print("=" * 40)
    print("✅ Successfully tested current pyoccam setup")
    
    return True

def test_direct_occ_call():
    """Test calling occ.cpp directly if available"""
    
    print("\n🔧 Testing Direct occ.cpp Call:")
    print("=" * 35)
    
    import subprocess
    import os
    
    # Look for occ executable
    possible_names = ['occ.exe', 'occ', 'occam.exe', 'occam']
    occ_exe = None
    
    for name in possible_names:
        if os.path.exists(name):
            occ_exe = name
            break
    
    if not occ_exe:
        print("⚠️ No occ executable found in current directory")
        return False
    
    print(f"✅ Found executable: {occ_exe}")
    
    # Test calling it
    try:
        result = subprocess.run([occ_exe, "--help"], 
                               capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            print("✅ occ.cpp executable responds to --help")
            print("First few lines of help:")
            for line in result.stdout.split('\n')[:5]:
                if line.strip():
                    print(f"  {line}")
        else:
            print(f"⚠️ occ.cpp returned exit code {result.returncode}")
            
    except Exception as e:
        print(f"⚠️ Error calling occ.cpp: {e}")
        return False
    
    return True

if __name__ == "__main__":
    try:
        success = main()
        
        if success:
            test_direct_occ_call()
            
        print(f"\n✨ Demo completed!")
        
    except Exception as e:
        print(f"\n❌ Error during demo: {e}")
        import traceback
        traceback.print_exc()