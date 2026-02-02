"""Test the CSV to OCCAM converter"""
import sys
sys.path.insert(0, r"D:\projects\occam")

import pyoccam

# Test with the WTNSY file
csv_file = r"C:\projects\spatial_ra\landslides_RA\WTNSY_data\preprocessed\WTNSY_clean.csv"

print("="*70)
print("Testing make_occam_input_from_csv()")
print("="*70)

# Convert CSV to OCCAM format
output_file, data = pyoccam.make_occam_input_from_csv(
    csv_file,
    max_cardinality=20,
    exclude_columns=['x', 'y', 'Pt_ID', 'OBJECTID', 'mukey', 'cokey', 'Shape_Leng', 'Shape_Area'],
    verbose=True
)

if data:
    print("\n" + "="*70)
    print("Running quick search on converted data...")
    print("="*70)
    best = data.quick_search(search_type="loopless-up", levels=3, width=3)
    
    print(f"\nBest model: {best}")
    
    # Get confusion matrix
    cm = data.manager.get_confusion_matrix(best, target_state="0")
    if cm.get('has_values', False):
        print(f"\nAccuracy: {cm['train_accuracy']:.1%}")
