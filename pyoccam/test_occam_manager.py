#!/usr/bin/env python3
"""
Test the current OccamManager to see what it can do
"""

import os
from datetime import datetime

def test_occam_manager():
    """Test your current OccamManager class"""
    
    print("🔍 TESTING CURRENT OccamManager")
    print("=" * 50)
    
    # Import your current pyoccam
    try:
        import pyoccam
        print("✅ pyoccam imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import: {e}")
        return False
    
    # Create OccamManager instance
    try:
        manager = pyoccam.OccamManager()
        print("✅ OccamManager created successfully")
    except Exception as e:
        print(f"❌ Failed to create OccamManager: {e}")
        return False
    
    # Explore what methods OccamManager has
    print("\n📋 OccamManager Methods:")
    print("-" * 30)
    
    manager_methods = [attr for attr in dir(manager) if not attr.startswith('_')]
    for i, method in enumerate(manager_methods, 1):
        attr_obj = getattr(manager, method)
        if callable(attr_obj):
            print(f"  {i:2d}. {method}() - callable")
        else:
            print(f"  {i:2d}. {method} - attribute")
    
    print(f"\nTotal methods/attributes: {len(manager_methods)}")
    
    # Test data file loading
    data_file = "dementia05.txt"
    print(f"\n📁 Testing Data File Loading:")
    print("-" * 35)
    
    if not os.path.exists(data_file):
        print(f"❌ Data file '{data_file}' not found")
        print("Current directory:", os.getcwd())
        # Look for any .txt files
        txt_files = [f for f in os.listdir('.') if f.endswith('.txt')]
        if txt_files:
            print("Available .txt files:")
            for f in txt_files[:5]:
                print(f"  • {f}")
            data_file = txt_files[0]  # Use first available
            print(f"🔄 Using {data_file} instead")
        else:
            print("No .txt files found")
            return False
    
    # Try common initialization methods
    init_methods_to_try = [
        'init_from_command_line',
        'initFromCommandLine', 
        'initialize',
        'load_data',
        'loadData',
        'setDataFile',
        'set_data_file'
    ]
    
    print(f"\n🔧 Testing Initialization Methods:")
    print("-" * 40)
    
    initialized = False
    for method_name in init_methods_to_try:
        if hasattr(manager, method_name):
            print(f"✅ Found method: {method_name}")
            try:
                method = getattr(manager, method_name)
                
                # Try different argument patterns
                for args in [
                    [data_file],
                    ["occam", data_file],
                    [data_file, "VB"],
                ]:
                    try:
                        print(f"   Trying: {method_name}({args})")
                        result = method(args)
                        print(f"   Result: {result}")
                        if result:  # If it returned True or success
                            initialized = True
                            print(f"   ✅ SUCCESS with {args}")
                            break
                    except Exception as e:
                        print(f"   ⚠️ Failed with {args}: {e}")
                
                if initialized:
                    break
                    
            except Exception as e:
                print(f"❌ Error calling {method_name}: {e}")
        else:
            print(f"⚠️ Method {method_name} not found")
    
    if not initialized:
        print("❌ Could not initialize manager with any method")
        return False
    
    print("✅ Manager initialized successfully!")
    
    # Test search methods
    print(f"\n🔍 Testing Search Methods:")
    print("-" * 30)
    
    search_methods_to_try = [
        'generate_search_report',
        'generateSearchReport',
        'search',
        'doSearch',
        'do_search',
        'performSearch',
        'runSearch'
    ]
    
    for method_name in search_methods_to_try:
        if hasattr(manager, method_name):
            print(f"✅ Found search method: {method_name}")
            try:
                method = getattr(manager, method_name)
                
                # Try simple search call
                print(f"   Testing {method_name}...")
                
                # Try different argument patterns
                test_args = [
                    [],
                    ["loopless-up"],
                    ["loopless-up", 3, 3],
                    [{"search_type": "loopless-up", "levels": 3, "width": 3}]
                ]
                
                for args in test_args:
                    try:
                        print(f"   Trying: {method_name}({args})")
                        result = method(*args) if isinstance(args, list) else method(args)
                        
                        if result and len(str(result)) > 10:  # Got substantial result
                            print(f"   ✅ SUCCESS! Got result ({len(str(result))} characters)")
                            print("   First 200 characters:")
                            print(f"   {str(result)[:200]}...")
                            return True
                        else:
                            print(f"   ⚠️ Got result but seems empty: {result}")
                            
                    except Exception as e:
                        print(f"   ⚠️ Failed with {args}: {e}")
                        
            except Exception as e:
                print(f"❌ Error with {method_name}: {e}")
        else:
            print(f"⚠️ Method {method_name} not found")
    
    # Test any other callable methods
    print(f"\n🧪 Testing Other Callable Methods:")
    print("-" * 35)
    
    for method_name in manager_methods:
        if callable(getattr(manager, method_name)) and method_name not in search_methods_to_try + init_methods_to_try:
            print(f"🔍 Testing {method_name}()...")
            try:
                method = getattr(manager, method_name)
                
                # Try calling with no arguments
                try:
                    result = method()
                    print(f"   ✅ {method_name}() returned: {result}")
                except TypeError:
                    # Maybe it needs arguments
                    print(f"   ⚠️ {method_name}() needs arguments")
                except Exception as e:
                    print(f"   ⚠️ {method_name}() error: {e}")
                    
            except Exception as e:
                print(f"   ❌ Error with {method_name}: {e}")
    
    return True

def test_direct_occ():
    """Test if occ.cpp is available for direct calls"""
    
    print(f"\n🔧 Testing Direct occ.cpp Access:")
    print("-" * 35)
    
    import subprocess
    
    # Look for occ executable
    possible_names = ['occ.exe', 'occ', 'occam.exe', 'occam']
    
    for exe_name in possible_names:
        if os.path.exists(exe_name):
            print(f"✅ Found executable: {exe_name}")
            
            # Test calling it
            try:
                # Try --help first
                result = subprocess.run([exe_name, "--help"], 
                                       capture_output=True, text=True, timeout=5)
                
                if result.returncode == 0:
                    print(f"✅ {exe_name} --help works")
                    if result.stdout:
                        lines = result.stdout.split('\n')[:3]
                        for line in lines:
                            if line.strip():
                                print(f"     {line}")
                    return exe_name
                else:
                    print(f"⚠️ {exe_name} --help returned code {result.returncode}")
                    
            except subprocess.TimeoutExpired:
                print(f"⚠️ {exe_name} timed out")
            except Exception as e:
                print(f"⚠️ Error calling {exe_name}: {e}")
        else:
            print(f"⚠️ {exe_name} not found")
    
    print("❌ No working occ executable found")
    return None

def main():
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Test current OccamManager
    manager_works = test_occam_manager()
    
    # Test direct occ access
    occ_exe = test_direct_occ()
    
    print(f"\n🎯 SUMMARY:")
    print("=" * 20)
    print(f"Current OccamManager: {'✅ Working' if manager_works else '❌ Needs work'}")
    print(f"Direct occ.cpp access: {'✅ Available' if occ_exe else '❌ Not found'}")
    
    if manager_works:
        print("\n💡 RECOMMENDATION: Enhance your current OccamManager")
    elif occ_exe:
        print("\n💡 RECOMMENDATION: Implement Python orchestration calling occ.cpp")
    else:
        print("\n💡 RECOMMENDATION: Fix C++ bindings and include occ.exe")
    
    return manager_works or occ_exe

if __name__ == "__main__":
    try:
        success = main()
        print(f"\n✨ Analysis complete: {'Success' if success else 'Issues found'}")
    except Exception as e:
        print(f"\n❌ Error during analysis: {e}")
        import traceback
        traceback.print_exc()
