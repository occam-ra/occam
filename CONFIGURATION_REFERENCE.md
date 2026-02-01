# OCCAM Fit Analyzer - Configuration Quick Reference

## All 24 Configurable Thresholds

### Files
| Setting | Default | Description |
|---------|---------|-------------|
| `FIT_REPORT_FILE` | None | Input fit report file path |
| `OUTPUT_FILE` | None | Output file (None = console) |

### Conditional DV Patterns

#### Accuracy Boundaries
| Setting | Default | Strict | Lenient | Description |
|---------|---------|--------|---------|-------------|
| `HIGH_ACCURACY_THRESHOLD` | 90% | 95% | 85% | States ≥ this are "high accuracy" |
| `LOW_ACCURACY_THRESHOLD` | 60% | 70% | 50% | States < this are "low accuracy" |

#### Sample Size Requirements
| Setting | Default | Strict | Lenient | Description |
|---------|---------|--------|---------|-------------|
| `SPARSE_DATA_THRESHOLD` | 5 | 10 | 3 | Min samples for reliable predictions |
| `MIN_FREQ_FOR_LOW_ACCURACY` | 10 | 15 | 8 | Min samples to flag low accuracy |
| `MIN_FREQ_FOR_SIGNIFICANCE` | 10 | 15 | 8 | Min samples to report significant rules |
| `MIN_FREQ_FOR_MISMATCH` | 10 | 15 | 8 | Min samples to report obs/pred mismatches |

#### Statistical
| Setting | Default | Strict | Lenient | Description |
|---------|---------|--------|---------|-------------|
| `SIGNIFICANCE_THRESHOLD` | 0.05 | 0.01 | 0.10 | p-value threshold for significance |
| `LARGE_MISMATCH_THRESHOLD` | 20% | 15% | 30% | % difference between observed and predicted |

### Overview Assessment

#### Information Capture Levels
| Setting | Default | Strict | Lenient | Description |
|---------|---------|--------|---------|-------------|
| `INFO_CAPTURE_LOW` | 10% | 15% | 8% | Below this = "Low information capture" |
| `INFO_CAPTURE_MODERATE` | 30% | 35% | 25% | Below this = "Moderate" |
| `INFO_CAPTURE_HIGH` | 60% | 65% | 55% | Above this = "High information capture" |

#### Transmission Strength
| Setting | Default | Strict | Lenient | Description |
|---------|---------|--------|---------|-------------|
| `TRANSMISSION_WEAK` | 0.3 | 0.4 | 0.25 | Below this = "weak relationship" |
| `TRANSMISSION_STRONG` | 0.7 | 0.75 | 0.65 | Above this = "strong relationship" |

### Model Quality

#### p-value Significance
| Setting | Default | Strict | Lenient | Description |
|---------|---------|--------|---------|-------------|
| `P_HIGHLY_SIGNIFICANT` | 0.001 | 0.0001 | 0.01 | Below this = "highly significant" |
| `P_SIGNIFICANT` | 0.05 | 0.01 | 0.10 | Below this = "significant" |

### Confusion Matrices

#### Accuracy Levels
| Setting | Default | Strict | Lenient | Description |
|---------|---------|--------|---------|-------------|
| `ACCURACY_EXCELLENT` | 80% | 85% | 75% | ≥ this = "Excellent" |
| `ACCURACY_GOOD` | 70% | 75% | 65% | ≥ this = "Good" |
| `ACCURACY_MODERATE` | 60% | 65% | 55% | ≥ this = "Moderate" |

#### Performance Metrics
| Setting | Default | Strict | Lenient | Description |
|---------|---------|--------|---------|-------------|
| `LOW_SENSITIVITY_THRESHOLD` | 0.5 | 0.6 | 0.4 | Below this triggers warning |
| `LOW_SPECIFICITY_THRESHOLD` | 0.5 | 0.6 | 0.4 | Below this triggers warning |
| `LOW_F1_THRESHOLD` | 0.5 | 0.6 | 0.4 | Below this triggers warning |

#### Class Balance
| Setting | Default | Strict | Lenient | Description |
|---------|---------|--------|---------|-------------|
| `CLASS_IMBALANCE_THRESHOLD` | 20% | 15% | 25% | % deviation from 50/50 to flag |

## Common Adjustments

### For Small Datasets (n<100)
```python
SPARSE_DATA_THRESHOLD = 3
MIN_FREQ_FOR_LOW_ACCURACY = 5
MIN_FREQ_FOR_SIGNIFICANCE = 5
MIN_FREQ_FOR_MISMATCH = 5
```

### For Large Datasets (n>1000)
```python
SPARSE_DATA_THRESHOLD = 10
MIN_FREQ_FOR_LOW_ACCURACY = 20
MIN_FREQ_FOR_SIGNIFICANCE = 20
MIN_FREQ_FOR_MISMATCH = 20
```

### For Noisy Data
```python
LOW_ACCURACY_THRESHOLD = 50  # Lower expectations
HIGH_ACCURACY_THRESHOLD = 85
LARGE_MISMATCH_THRESHOLD = 30  # More tolerance
```

### For High-Stakes Decisions
```python
LOW_ACCURACY_THRESHOLD = 70  # Higher bar
LOW_SENSITIVITY_THRESHOLD = 0.7  # Can't miss true cases
LOW_SPECIFICITY_THRESHOLD = 0.7  # Can't have false alarms
SIGNIFICANCE_THRESHOLD = 0.01  # More stringent
```

### For Multiple Testing
```python
SIGNIFICANCE_THRESHOLD = 0.01  # Bonferroni-style
P_HIGHLY_SIGNIFICANT = 0.0001
P_SIGNIFICANT = 0.01
```

## Usage Pattern

1. **Start with defaults** - Run analysis with standard thresholds
2. **Review results** - See what's flagged, what's missed
3. **Adjust thresholds** - Based on your domain knowledge
4. **Re-run** - Compare results
5. **Document** - Save your final configuration

## Pro Tips

- **Don't over-tune**: Adjusting thresholds to make warnings disappear defeats the purpose
- **Domain matters**: Medical/financial = strict, exploratory = lenient
- **Sample size matters**: Small samples need lenient thresholds
- **Compare configs**: Use `example_threshold_comparison.py` to see effects
- **Document your choice**: Note why you chose specific thresholds

## See Also

- `complete_config_template.py` - Full template with all options
- `example_threshold_comparison.py` - Compare strict vs standard vs lenient
- `FIT_ANALYZER_README.md` - Complete documentation
