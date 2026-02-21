
import pyoccam

output_file, data = pyoccam.make_occam_input_from_csv("sample_mydata.csv")

  # With train/test split for validation
output_file, data = pyoccam.make_occam_input_from_csv(
    "sample_mydata.csv",
    test_split=0.2,               # 20% held out for testing
    random_state=42,              # Reproducible split
    max_cardinality=20,           # Exclude columns with >20 unique values
    dv_column="target",           # Specify DV column by name
    exclude_columns=["ID", "Name"] # Always exclude these columns
)

  # Then analyze
best = data.quick_search()
cm = data.manager.get_confusion_matrix(best, target_state="0")