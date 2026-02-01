#!/usr/bin/env python3
"""
Example: Comparing Different Threshold Settings

This demonstrates how different threshold settings affect the analysis.
"""

from analyze_fit import FitReportAnalyzer
import copy

# Load a fit report
with open('/mnt/project/dementia05_fit_IV_ApZ_EdZ_CZ.csv', 'r') as f:
    report = f.read()

print("=" * 80)
print("COMPARING THRESHOLD SETTINGS")
print("=" * 80)

# Define three different threshold profiles
configs = {
    'Strict': {
        'HIGH_ACCURACY_THRESHOLD': 95,
        'LOW_ACCURACY_THRESHOLD': 70,
        'SPARSE_DATA_THRESHOLD': 10,
        'LARGE_MISMATCH_THRESHOLD': 15,
    },
    'Standard': {
        'HIGH_ACCURACY_THRESHOLD': 90,
        'LOW_ACCURACY_THRESHOLD': 60,
        'SPARSE_DATA_THRESHOLD': 5,
        'LARGE_MISMATCH_THRESHOLD': 20,
    },
    'Lenient': {
        'HIGH_ACCURACY_THRESHOLD': 85,
        'LOW_ACCURACY_THRESHOLD': 50,
        'SPARSE_DATA_THRESHOLD': 3,
        'LARGE_MISMATCH_THRESHOLD': 30,
    }
}

# Run analysis with each config
results = {}
for config_name, thresholds in configs.items():
    # Temporarily set global thresholds
    import analyze_fit
    for key, value in thresholds.items():
        setattr(analyze_fit, key, value)
    
    # Run analysis
    analyzer = FitReportAnalyzer(report)
    findings = analyzer.analyze()
    results[config_name] = findings

# Compare results
print("\n" + "=" * 80)
print("COMPARISON SUMMARY")
print("=" * 80)

for config_name in ['Strict', 'Standard', 'Lenient']:
    findings = results[config_name]
    
    print(f"\n{config_name} Configuration:")
    print(f"  Thresholds: {configs[config_name]}")
    
    # Count pattern types
    pattern_counts = {}
    for pattern in findings['conditional_patterns']:
        ptype = pattern['type']
        pattern_counts[ptype] = pattern_counts.get(ptype, 0) + pattern['count']
    
    print(f"  Patterns found:")
    print(f"    High accuracy states: {pattern_counts.get('high_accuracy', 0)}")
    print(f"    Low accuracy states: {pattern_counts.get('low_accuracy', 0)}")
    print(f"    Sparse data states: {pattern_counts.get('sparse_data', 0)}")
    print(f"    Significant rules: {pattern_counts.get('significant_rules', 0)}")
    print(f"    Prediction mismatches: {pattern_counts.get('prediction_mismatch', 0)}")
    print(f"  Total recommendations: {len(findings['recommendations'])}")

print("\n" + "=" * 80)
print("INTERPRETATION")
print("=" * 80)
print("""
Strict thresholds:
  - Catches more potential issues
  - Good for publication-quality analysis
  - May flag things that aren't actually problems

Standard thresholds:
  - Balanced approach
  - Good for general analysis
  - Recommended starting point

Lenient thresholds:
  - Focuses on serious issues only
  - Good for exploratory analysis
  - May miss subtle problems
""")

# Show detailed breakdown for standard config
print("\n" + "=" * 80)
print("DETAILED ANALYSIS (Standard Configuration)")
print("=" * 80)

analyzer = FitReportAnalyzer(report)
# Reset to standard thresholds
import analyze_fit
for key, value in configs['Standard'].items():
    setattr(analyze_fit, key, value)

analyzer.print_summary()
