# Ensemble RA: Mining High-Confidence Rules from Specialist Models

**Version**: 1.0.0  
**Date**: January 13, 2025  
**Compatible with**: PyOccam 0.9.2+  
**Location**: `D:\projects\occam\ensemble_ra.py`

---

## Overview

The Ensemble RA module implements a **two-tier prediction approach** for Reconstructability Analysis that extracts high-confidence prediction rules from "specialist" models that lose on BIC/AIC but excel at specific state combinations.

### The Key Insight

When OCCAM runs a beam search, it ranks models by various criteria (BIC, AIC, %correct). The **BIC-best model** is typically a good generalist - it balances accuracy against complexity. But models that "lose" on BIC often do so because they're **overfit** - they have more parameters than justified by the complexity penalty.

However, **overfitting is a feature, not a bug** for rule extraction. These specialist models have memorized specific IV state combinations perfectly. We can:

1. Use the BIC-best model as a reliable **base/fallback**
2. Extract **specific high-confidence rules** from the specialists
3. Create a two-tier prediction: use the rule if we have one, otherwise fall back to base

---

## Quick Start

### With PyOccam Manager (Full Workflow)

```python
import pyoccam
from ensemble_ra import EnsembleRAClassifier

# Load your data
data = pyoccam.load_landslides()  # or load_dementia(), load_data("myfile.txt")
manager = data.manager

# Create ensemble classifier
ensemble = EnsembleRAClassifier(manager, dv_name="Z")

# Configure rule acceptance thresholds
ensemble.configure_thresholds(
    min_frequency=10,      # Minimum sample count for a rule
    min_confidence=85.0,   # Minimum calc.q(DV|IV) percentage
    min_accuracy=90.0,     # Minimum %correct
    max_p_margin=0.05      # Maximum p-value vs marginal (significance)
)

# Run the complete workflow
ensemble.run_ensemble_workflow(
    search_type="full-up",           # or "loopless-up"
    levels=7,                        # search depth
    width=3,                         # beam width
    min_specialist_accuracy=0.76,    # specialists must beat this %C(Data)
    max_specialist_cover=80.0        # specialists must be selective (low cover)
)

# View results
print(ensemble.get_summary())

# Export rules
ensemble.export_rules_csv("my_rules.csv")
```

### Standalone Mode (Existing Files)

```python
from ensemble_ra import EnsembleRAClassifier

# Create classifier without manager
ensemble = EnsembleRAClassifier(dv_name="Z")

# Configure thresholds
ensemble.configure_thresholds(
    min_frequency=10,
    min_confidence=85.0,
    min_accuracy=90.0,
    max_p_margin=0.05
)

# Load existing search results
ensemble.load_search_results("search_full-up_landslides_20251111_004715.txt")

# Mine rules from existing fit report(s)
ensemble.mine_from_fit_file("fit_IV_ElTwZ_HbZ_LcZ_SlZ_TcZ_20251111_004715.txt")

# View and export
print(ensemble.get_summary())
ensemble.export_rules_csv("rules.csv")
```

---

## What the Workflow Does

1. **Runs search** → Gets all models with `%C(Data)` (accuracy) and `%cover`
2. **Picks base model** → Best BIC (conservative, high coverage)
3. **Finds specialists** → Models that "lost" on BIC but have HIGH accuracy + LOW coverage
4. **Generates fit reports for specialists** → These weren't fitted in normal workflow
5. **Mines high-confidence rules** → Extracts specific IV→DV predictions meeting thresholds
6. **Two-tier prediction**: specific rule → use it; no rule → fall back to base model

---

## API Reference

### EnsembleRAClassifier

#### Constructor
```python
EnsembleRAClassifier(manager=None, dv_name="Z")
```

#### Key Methods

| Method | Description |
|--------|-------------|
| `configure_thresholds(min_frequency, min_confidence, min_accuracy, max_p_margin)` | Set rule acceptance criteria |
| `run_ensemble_workflow(search_type, levels, width, ...)` | Run full integrated workflow |
| `load_search_results(filepath)` | Load existing search output |
| `mine_from_fit_file(filepath, model_name)` | Extract rules from fit report |
| `predict(iv_states)` | Make prediction → (dv, source, confidence) |
| `get_rules(sort_by)` | Get accepted rules as list |
| `get_summary(top_n)` | Human-readable summary |
| `export_rules_csv(filepath)` | Export to CSV |

---

## Example Results (Landslide Data)

From 9 specialist models, extracted **88 high-confidence rules** covering 1896 samples:

```
TOP RULES BY FREQUENCY:
  1. El=2,Hb=3,Lc=2,Sl=2,Tc=3 → Z=0  [n=72, conf=95.5%, acc=97%]
  2. El=2,Gl=2,Hb=3,Lc=2,Sl=2,Tc=3 → Z=0  [n=63, conf=96.2%, acc=98%]
  3. Cv=2,Hb=3,Lc=2,Sl=2,Tc=3 → Z=0  [n=61, conf=95.6%, acc=93%]
  4. Cv=2,Hb=1,Lc=1,Tc=2 → Z=1  [n=55, conf=96.7%, acc=98%]
```

### Key Patterns Discovered

**Landslide prone (Z=1):**
- LandCover=1 (forest), TaxClass=2, Elevation=1 (lower), Habitat=1

**Stable areas (Z=0):**
- LandCover=2 (developed), TaxClass=3, Elevation=2 (higher), Habitat=3

---

## Threshold Guidelines

| Use Case | min_frequency | min_confidence | min_accuracy | max_p_margin |
|----------|---------------|----------------|--------------|--------------|
| Exploratory | 5 | 70% | 80% | 0.10 |
| **Standard** | **10** | **85%** | **90%** | **0.05** |
| High-stakes | 20 | 95% | 95% | 0.01 |

---

## Files

| File | Description |
|------|-------------|
| `ensemble_ra.py` | Main module |
| `analyze_fit.py` | Fit report analyzer (optional, improves parsing) |
| `rules.csv` | Example output from landslide analysis |
| `results4.txt` | Full output log from test run |

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2025-01-13 | Initial release |
