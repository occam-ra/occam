import pyoccam
from ensemble_ra import EnsembleRAClassifier

# Load data
data = pyoccam.load_landslides()

# Create and configure ensemble
ensemble = EnsembleRAClassifier(data.manager, dv_name="Z")
ensemble.configure_thresholds(min_frequency=10, min_confidence=85, min_accuracy=90)

# Run workflow - this:
# 1. Runs search
# 2. Picks BIC-best as base model
# 3. Finds specialists (high acc, low cover)
# 4. Generates fit reports for specialists
# 5. Mines high-confidence rules
ensemble.run_ensemble_workflow("full-up", levels=7, width=3)

# Results
print(ensemble.get_summary())
ensemble.export_rules_csv("rules.csv")