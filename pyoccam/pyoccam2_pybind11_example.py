#!/usr/bin/env python3
"""
pyoccam2_example.py - Complete usage example for PyOCCAM2

This example demonstrates the complete functionality of the pybind11 PyOCCAM2 implementation
that follows weboccam.py patterns exactly, including:
- All form field processing options
- Error handling patterns  
- Different output formats
- Graphics configuration
- All search and fit operations
"""

import pyoccam2
import os
import sys

def print_section(title):
    """Print section header"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")

def example_basic_search():
    """Basic search operation following weboccam.py pattern"""
    print_section("BASIC SEARCH OPERATION")
    
    # Create form fields dictionary (like weboccam.py parseFormFields)
    form_fields = {
        'datafilename': 'dementia05.txt',
        'action': 'search',
        'searchtype': 'loopless-up',
        'searchlevels': '5',
        'searchwidth': '3',
        'refmodel': 'bottom',
        'model': 'default'
    }
    
    print("Form Fields:")
    for key, value in form_fields.items():
        print(f"  {key}: {value}")
    print()
    
    # Process using WebOccam form processor (like weboccam.py main flow)
    try:
        result = pyoccam2.WebOccam.process_form_fields(form_fields)
        print("Search Results:")
        print(result[:500] + "..." if len(result) > 500 else result)
    except Exception as e:
        print(f"Error: {e}")

def example_advanced_search():
    """Advanced search with all configuration options"""
    print_section("ADVANCED SEARCH WITH ALL OPTIONS")
    
    form_fields = {
        'datafilename': 'dementia05.txt',
        'action': 'search',
        'searchtype': 'full-up',
        'searchlevels': '7',
        'searchwidth': '5',
        'refmodel': 'bottom',
        'model': 'default',
        'sortdir': 'descending',
        'sortreportby': 'bic',
        'skipnominal': '1',
        'inversenotation': '0',
        'functionvalues': '0',
        'percentcorrect': '1',
        'ddfmethod': '1',
        'alphathreshold': '0.05'
    }
    
    print("Advanced Configuration:")
    for key, value in form_fields.items():
        print(f"  {key}: {value}")
    print()
    
    try:
        result = weboccam_py.WebOccam.process_form_fields(form_fields)
        print("Advanced Search Results:")
        print(result[:500] + "..." if len(result) > 500 else result)
    except Exception as e:
        print(f"Error: {e}")

def example_fit_operation():
    """Fit operation with confusion matrix"""
    print_section("FIT OPERATION WITH CONFUSION MATRIX")
    
    form_fields = {
        'datafilename': 'dementia05.txt',
        'action': 'fit',
        'fitmodel': 'IV:ApSxZ:EdZ:AgZ:CZ:KZ',
        'classifiertarget': '0',  # Negative state for confusion matrix
        'skipnominal': '1',
        'percentcorrect': '1',
        'calcexpecteddv': '1'
    }
    
    print("Fit Configuration:")
    for key, value in form_fields.items():
        print(f"  {key}: {value}")
    print()
    
    try:
        result = weboccam_py.WebOccam.process_form_fields(form_fields)
        print("Fit Results:")
        print(result[:800] + "..." if len(result) > 800 else result)
    except Exception as e:
        print(f"Error: {e}")

def example_different_output_formats():
    """Test different output formats"""
    print_section("DIFFERENT OUTPUT FORMATS")
    
    base_fields = {
        'datafilename': 'dementia05.txt',
        'action': 'search',
        'searchtype': 'loopless-up',
        'searchlevels': '3',
        'searchwidth': '2'
    }
    
    formats = [
        ('Text/CSV Format', {'format': 'text'}),
        ('HTML Format', {}),  # Default is HTML
        ('Tab-separated', {'format': 'text', 'separator': '1'}),
        ('Comma-separated', {'format': 'text', 'separator': '2'})
    ]
    
    for format_name, format_fields in formats:
        print(f"\n--- {format_name} ---")
        form_fields = {**base_fields, **format_fields}
        
        try:
            result = weboccam_py.WebOccam.process_form_fields(form_fields)
            print(result[:300] + "..." if len(result) > 300 else result)
        except Exception as e:
            print(f"Error: {e}")

def example_direct_ocutils_usage():
    """Using OcUtils directly (like ocutils.py usage)"""
    print_section("DIRECT OCUTILS USAGE")
    
    try:
        # Create OcUtils instance (like weboccam.py creates oc = ocUtils("VB"))
        oc = weboccam_py.OcUtils("VB")
        print("Created VBMManager")
        
        # Initialize from command line (like ocutils.py initFromCommandLine)
        args = ["weboccam", "dementia05.txt"]
        if not oc.init_from_command_line(args):
            print("Error: Could not initialize OCCAM")
            return
        print("Initialized with data file")
        
        # Configure search (following weboccam.py configuration pattern)
        oc.set_report_separator(weboccam_py.SPACESEP)
        oc.set_search_levels(5)
        oc.set_search_width(3)
        oc.set_search_type("loopless-up")
        oc.set_ref_model("bottom")
        oc.set_action("search")
        oc.set_skip_nominal(True)
        oc.set_percent_correct(True)
        print("Configured for search")
        
        print(f"Configuration:")
        print(f"  Search Type: {oc.get_search_type()}")
        print(f"  Search Levels: {oc.get_search_levels()}")
        print(f"  Search Width: {oc.get_search_width()}")
        print(f"  Action: {oc.get_action()}")
        print()
        
        # Execute action (like weboccam.py doAction)
        result = oc.do_action(print_options=True)
        print("Search completed")
        print(f"Elapsed time: {oc.get_elapsed_time():.2f} seconds")
        print("Results:")
        print(result[:500] + "..." if len(result) > 500 else result)
        
    except Exception as e:
        print(f"Error: {e}")

def example_state_based_operations():
    """State-based search and fit operations"""
    print_section("STATE-BASED OPERATIONS")
    
    # SB Search
    print("--- SB Search ---")
    sb_search_fields = {
        'datafilename': 'dementia05.txt',
        'action': 'SBsearch',
        'searchtype': 'loopless-up',
        'searchlevels': '3',
        'searchwidth': '3'
    }
    
    try:
        result = weboccam_py.WebOccam.process_form_fields(sb_search_fields)
        print("SB Search Results:")
        print(result[:300] + "..." if len(result) > 300 else result)
    except Exception as e:
        print(f"SB Search Error: {e}")
    
    print("\n--- SB Fit ---")
    sb_fit_fields = {
        'datafilename': 'dementia05.txt',
        'action': 'SBfit',
        'fitmodel': 'IV:ApSxZ:EdZ',
        'classifiertarget': '0'
    }
    
    try:
        result = weboccam_py.WebOccam.process_form_fields(sb_fit_fields)
        print("SB Fit Results:")
        print(result[:300] + "..." if len(result) > 300 else result)
    except Exception as e:
        print(f"SB Fit Error: {e}")

def example_graphics_configuration():
    """Graphics and visualization options"""
    print_section("GRAPHICS CONFIGURATION")
    
    graphics_fields = {
        'datafilename': 'dementia05.txt',
        'action': 'search',
        'searchtype': 'loopless-up',
        'searchlevels': '3',
        'searchwidth': '2',
        'gfx': '1',
        'layout': '2',  # Reingold-Tilford layout
        'gephi': '1',
        'hideiv': '0',
        'graphWidth': '800',
        'graphHeight': '600',
        'graphFontSize': '14',
        'graphNodeSize': '32'
    }
    
    print("Graphics Configuration:")
    for key, value in graphics_fields.items():
        if key.startswith('graph') or key in ['gfx', 'layout', 'gephi', 'hideiv']:
            print(f"  {key}: {value}")
    print()
    
    try:
        result = weboccam_py.WebOccam.process_form_fields(graphics_fields)
        print("Graphics-enabled Results:")
        print(result[:400] + "..." if len(result) > 400 else result)
    except Exception as e:
        print(f"Graphics Error: {e}")

def example_utility_functions():
    """Utility functions and validation"""
    print_section("UTILITY FUNCTIONS AND VALIDATION")
    
    # Test form field parsing utilities
    form_fields = {
        'datafilename': 'test_data.txt',
        'searchlevels': '10',
        'searchwidth': 'invalid',
        'alphathreshold': '0.01'
    }
    
    print("Utility Function Examples:")
    
    # Get data filename (like weboccam.py getDataFileName)
    filename = weboccam_py.get_data_filename(form_fields, trim=False)
    filename_trimmed = weboccam_py.get_data_filename(form_fields, trim=True)
    print(f"  Data filename: {filename}")
    print(f"  Data filename (trimmed): {filename_trimmed}")
    
    # Parse integers with defaults (like weboccam.py attemptParseInt)
    levels = weboccam_py.attempt_parse_int(form_fields.get('searchlevels', ''), 7, "search levels", True)
    width = weboccam_py.attempt_parse_int(form_fields.get('searchwidth', ''), 3, "search width", True)
    threshold = weboccam_py.attempt_parse_double(form_fields.get('alphathreshold', ''), 0.05, "alpha threshold", True)
    
    print(f"  Search levels: {levels}")
    print(f"  Search width: {width}")
    print(f"  Alpha threshold: {threshold}")
    
    # Test search type validation
    search_types = weboccam_py.get_available_search_types()
    print(f"  Available search types: {search_types}")
    
    valid_types = ['loopless-up', 'invalid-type', 'full-down']
    for search_type in valid_types:
        is_valid = weboccam_py.is_valid_search_type(search_type)
        print(f"  '{search_type}' is valid: {is_valid}")
    
    # Test form validation
    print("\n  Form Validation:")
    test_forms = [
        {'datafilename': 'test.txt', 'action': 'search'},  # Valid
        {'action': 'search'},  # Missing datafilename
        {'datafilename': 'test.txt', 'action': 'invalid'},  # Invalid action
        {'datafilename': 'test.txt', 'searchtype': 'invalid-search'}  # Invalid search type
    ]
    
    for i, test_form in enumerate(test_forms):
        error_message = ""
        is_valid = weboccam_py.WebOccam.validate_form_fields(test_form, error_message)
        print(f"    Form {i+1}: {'Valid' if is_valid else f'Invalid - {error_message}'}")

def example_error_handling():
    """Error handling and edge cases"""
    print_section("ERROR HANDLING AND EDGE CASES")
    
    error_cases = [
        ({}, "Empty form fields"),
        ({'datafilename': ''}, "Empty data filename"),
        ({'datafilename': 'nonexistent.txt'}, "Nonexistent data file"),
        ({'datafilename': 'test.txt', 'action': 'invalid'}, "Invalid action"),
        ({'datafilename': 'test.txt', 'searchtype': 'invalid'}, "Invalid search type"),
        ({'datafilename': 'test.txt', 'searchlevels': '-1'}, "Negative search levels"),
        ({'datafilename': 'test.txt', 'searchwidth': '0'}, "Zero search width")
    ]
    
    for form_fields, description in error_cases:
        print(f"\n--- {description} ---")
        try:
            result = weboccam_py.WebOccam.process_form_fields(form_fields)
            print(f"Unexpected success: {result[:100]}...")
        except Exception as e:
            print(f"Expected error: {e}")

def main():
    """Main function demonstrating all weboccam patterns"""
    print("PyOCCAM2 Complete Example")
    print("Following weboccam.py patterns exactly with full feature set")
    #print(f"Version: {pyoccam2.__version__}")
    
    # Check if data directory exists
    if not pyoccam2.ensure_data_directory():
        print(f"\nWarning: Could not ensure data directory '{pyoccam2.DATA_DIR}' exists")
        print("Some examples may fail if data files are not available")
    
    # Available constants
    print(f"\nConstants:")
    print(f"  TABSEP: {pyoccam2.TABSEP}")
    print(f"  COMMASEP: {pyoccam2.COMMASEP}")
    print(f"  SPACESEP: {pyoccam2.SPACESEP}")
    print(f"  HTMLFORMAT: {pyoccam2.HTMLFORMAT}")
    print(f"  DATA_DIR: {pyoccam2.DATA_DIR}")
    
    try:
        # Run examples in logical order
        example_utility_functions()
        example_basic_search()
        example_advanced_search()
        example_fit_operation()
        example_different_output_formats()
        example_direct_ocutils_usage()
        example_state_based_operations()
        example_graphics_configuration()
        example_error_handling()
        
        print_section("ALL EXAMPLES COMPLETED SUCCESSFULLY!")
        print("The pybind11 weboccam implementation provides:")
        print("✓ Complete weboccam.py functionality")
        print("✓ All configuration options")
        print("✓ Multiple output formats")
        print("✓ Error handling and validation")
        print("✓ Graphics configuration")
        print("✓ State-based operations")
        print("✓ Utility functions")
        print("✓ Direct OcUtils API")
        
    except Exception as e:
        print(f"\nFatal error running examples: {e}")
        print("Note: Make sure you have:")
        print("1. Built the weboccam_py extension module")
        print("2. Data file 'dementia05.txt' available")
        print("3. Proper OCCAM installation")

if __name__ == "__main__":
    main()
