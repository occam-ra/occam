#!/usr/bin/env python3
"""
PyOCCAM2 CSV Report Generator
Generates search reports in CSV format matching server output
"""

import pyoccam2
import csv
import sys
import time
from datetime import datetime

def generate_csv_search_report(manager, search_type="full-up", levels=7, width=3, 
                               output_file="search_report.csv", debug=True):
    """
    Generate a CSV search report matching OCCAM server format
    """
    
    # Set debug mode
    manager.set_debug_mode(debug)
    
    # Generate the search report (internal format)
    print(f"Running {search_type} search (levels={levels}, width={width})...")
    start_time = time.time()
    
    search_output = manager.generate_search_report(
        search_type=search_type,
        levels=levels,
        width=width,
        include_test_data=False
    )
    
    elapsed = time.time() - start_time
    
    # Parse the text output to extract model data
    # This is a temporary solution - ideally we'd get structured data directly
    models = []
    lines = search_output.split('\n')
    
    # Find the table section
    in_table = False
    for line in lines:
        if '---' in line:
            in_table = True
            continue
        if in_table and line.strip() and not line.startswith('='):
            parts = line.split()
            if len(parts) >= 11 and parts[0].isdigit():
                try:
                    model_data = {
                        'ID': int(parts[0].rstrip('*')),
                        'MODEL': parts[1],
                        'Level': int(parts[2]),
                        'H': float(parts[3]),
                        'dDF': int(parts[4]),
                        'dLR': float(parts[5]),
                        'Alpha': float(parts[6]),
                        'Inf': float(parts[7]),
                        '%dH(DV)': float(parts[8]),
                        'dAIC': float(parts[9]),
                        'dBIC': float(parts[10]),
                        'Inc.Alpha': 0.0,  # TODO: get from model
                        'Prog.': 0,  # TODO: get from model
                        '%C(Data)': 0.0,  # TODO: get from model
                        '%cover': 0.0,  # TODO: get from model
                        'asterisk': '*' in parts[0]
                    }
                    models.append(model_data)
                except (ValueError, IndexError) as e:
                    print(f"Warning: Could not parse line: {line}")
                    continue
    
    # Write CSV file
    with open(output_file, 'w', newline='') as csvfile:
        # Write header information (matching server format)
        csvfile.write("Option settings:\n")
        csvfile.write(f"Data file\t{data_file}\n")
        csvfile.write(f"Starting model\tbottom\n")
        csvfile.write(f"Search direction\tup\n")
        csvfile.write(f"Ref model\tbottom\n")
        csvfile.write(f"Models to consider\t{search_type.replace('-up', '')}\n")
        csvfile.write(f"Search width\t{width}\n")
        csvfile.write(f"Search levels\t{levels}\n")
        csvfile.write(f"Search sort by\tbic\n")
        csvfile.write(f"Search preference\tdescending\n")
        csvfile.write(f"Report sort by\tinformation\n")
        csvfile.write(f"Report preference\tdescending\n")
        csvfile.write("\n")
        
        # Write statistics
        csvfile.write(f"Sample Size\t{manager.get_sample_size()}\n")
        csvfile.write("\n")
        
        # Write the main table header
        fieldnames = ['ID', 'MODEL', 'Level', 'H', 'dDF', 'dLR', 'Alpha', 
                     'Inf', '%dH(DV)', 'dAIC', 'dBIC', 'Inc.Alpha', 
                     'Prog.', '%C(Data)', '%cover']
        
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter='\t')
        writer.writeheader()
        
        # Write model data
        for model in models:
            # Format ID with asterisk if needed
            id_str = str(model['ID'])
            if model.get('asterisk'):
                id_str += '*'
            
            row = {k: model[k] for k in fieldnames if k != 'ID'}
            row['ID'] = id_str
            writer.writerow(row)
        
        # Write footer with best models
        csvfile.write("\n")
        best_bic = manager.get_best_model_by_bic()
        best_aic = manager.get_best_model_by_aic()
        best_info = manager.get_best_model_by_information()
        
        if best_bic:
            csvfile.write(f"Best Model(s) by dBIC:\n")
            csvfile.write(f"{best_bic}\n")
        if best_aic:
            csvfile.write(f"Best Model(s) by dAIC:\n")
            csvfile.write(f"{best_aic}\n")
        if best_info:
            csvfile.write(f"Best Model(s) by Information:\n")
            csvfile.write(f"{best_info}\n")
        
        csvfile.write(f"\nRun time: {elapsed:.6f} seconds\n")
    
    print(f"CSV report saved to: {output_file}")
    return models

def compare_with_server(models, server_csv_file):
    """
    Compare our results with server output
    """
    print("\n" + "="*60)
    print("COMPARISON WITH SERVER OUTPUT")
    print("="*60)
    
    # Read server CSV
    server_models = []
    with open(server_csv_file, 'r') as f:
        # Skip header lines until we find the table
        for line in f:
            if line.startswith('ID\tMODEL'):
                break
        
        # Read the data
        reader = csv.DictReader(f, delimiter='\t')
        for row in reader:
            if row['ID'] and row['ID'].strip():
                server_models.append(row)
    
    # Compare top models
    if len(models) > 0 and len(server_models) > 0:
        print("\nTop Model Comparison:")
        print("-" * 40)
        
        our_top = models[-1] if models else None
        server_top = server_models[0] if server_models else None
        
        if our_top and server_top:
            print(f"Our top model: {our_top['MODEL']}")
            print(f"  dAIC: {our_top['dAIC']:.4f}")
            print(f"  dBIC: {our_top['dBIC']:.4f}")
            print()
            print(f"Server top model: {server_top['MODEL']}")
            print(f"  dAIC: {float(server_top['dAIC']):.4f}")
            print(f"  dBIC: {float(server_top['dBIC']):.4f}")
            print()
            
            # Check sign issue
            if our_top['dAIC'] < 0 and float(server_top['dAIC']) > 0:
                print("⚠️  SIGN ISSUE DETECTED!")
                print("   Our dAIC is negative, server is positive")
                print("   This suggests the delta calculation is inverted")
            
            # Check magnitude
            our_magnitude = abs(our_top['dAIC'])
            server_magnitude = abs(float(server_top['dAIC']))
            diff = abs(our_magnitude - server_magnitude)
            
            print(f"\nMagnitude difference for dAIC: {diff:.4f}")
            if diff < 5:
                print("✓ Magnitudes are close (within 5)")
            else:
                print("✗ Magnitudes differ significantly")

if __name__ == "__main__":
    # Configuration
    data_file = "dementia05.txt"
    search_type = "full-up"
    search_levels = 7
    search_width = 3
    
    print("="*60)
    print("PyOCCAM2 CSV Report Generator")
    print("="*60)
    print()
    
    # Create manager and load data
    print("1. Initializing manager...")
    manager = pyoccam2.VBMManager()
    
    print(f"2. Loading data from {data_file}...")
    if not manager.init_from_command_line(["occam", data_file]):
        print("Error: Could not load data file")
        sys.exit(1)
    
    # Configure manager
    print("3. Configuring manager...")
    manager.set_report_separator(pyoccam2.SPACESEP)
    manager.set_ref_model("bottom")
    
    # Generate CSV report
    print("4. Generating CSV report...")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_file = f"search_{search_type}_{timestamp}.csv"
    
    models = generate_csv_search_report(
        manager, 
        search_type=search_type,
        levels=search_levels,
        width=search_width,
        output_file=csv_file,
        debug=True
    )
    
    # If server CSV exists, compare
    server_csv = "dementia05_search_fullup.csv"
    import os
    if os.path.exists(server_csv):
        compare_with_server(models, server_csv)
    else:
        print(f"\nNote: Server CSV '{server_csv}' not found for comparison")
    
    print("\n✓ Complete!")
