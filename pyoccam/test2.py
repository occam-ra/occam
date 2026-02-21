import pyoccam

# Convert CSV → OCCAM format + lookups
output_file, data = pyoccam.make_occam_input_from_csv(
    "sample_mydata.csv",
    exclude_columns=["site_id"],
    test_split=0.2,
    random_state=42
)

# Check lookups got created
print(data.lookups['soil_type'])      # {0: 'Alfisols', 1: 'Andisols', ...}
print(data.lookups['vegetation'][2])  # some vegetation class

# Verify the lookup CSV file exists alongside the .txt
print(f"Lookup file: {output_file.replace('.txt', '_lookups.csv')}")