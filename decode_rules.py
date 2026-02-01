#!/usr/bin/env python3
"""
WTNSY Landslide Rule Decoder
============================

Translates encoded rule values into human-readable descriptions.
For use with Ensemble RA output.

Usage:
    python decode_rules.py rules_volcanic_20260113_004608.csv
    python decode_rules.py --rule "El=5,Tp=15,Ro=1,Tt=3"

Date: January 13, 2026
"""

import pandas as pd
import re
import sys
from pathlib import Path

# =============================================================================
# VARIABLE ABBREVIATION MAPPINGS
# =============================================================================

ABBREV_TO_NAME = {
    'El': 'Elevation',
    'Sl': 'Slope', 
    'As': 'Aspect',
    'Fd': 'Fault Density',
    'Rd': 'Road Density',
    'Sd': 'Stream Density',
    'Cl': 'Clay Content',
    'Lc': 'Land Cover',
    'To': 'Soil Order',
    'Dc': 'Drainage Class',
    'Gd': 'Geomorphic Description',
    'Ts': 'Soil Suborder',
    'Tg': 'Soil Great Group',
    'Tb': 'Soil Subgroup',
    'Tp': 'Particle Size',
    'Ro': 'Rock Type',
    'Tt': 'Tectonic Setting',
    'Z': 'Landslide'
}

# =============================================================================
# VALUE DECODERS - Based on WTNSY encoding schemes
# =============================================================================

# Elevation bins (DEM_binned) - approximate ranges in meters
ELEVATION_DECODE = {
    1: 'Very Low (<150m)',
    2: 'Low (150-300m)',
    3: 'Moderate (300-450m)',
    4: 'High (450-600m)',
    5: 'Very High (>600m)'
}

# Slope bins (slope_binned) - degrees
SLOPE_DECODE = {
    1: 'Flat (<10°)',
    2: 'Gentle (10-20°)',
    3: 'Moderate (20-30°)',
    4: 'Steep (30-45°)',
    5: 'Very Steep (>45°)'
}

# Aspect bins
ASPECT_DECODE = {
    0: 'Flat',
    1: 'North',
    2: 'Northeast',
    3: 'East',
    4: 'Southeast',
    5: 'South',
    6: 'Southwest',
    7: 'West',
    8: 'Northwest'
}

# Clay content bins (increasing with value)
CLAY_DECODE = {
    1: 'Very Low Clay (<10%)',
    2: 'Low Clay (10-20%)',
    3: 'Moderate Clay (20-30%)',
    4: 'High Clay (30-40%)',
    5: 'Very High Clay (>40%)'
}

# Fault density bins (increasing with value)
FAULT_DENSITY_DECODE = {
    1: 'Low Fault Density',
    2: 'Moderate Fault Density',
    3: 'High Fault Density',
    4: 'Very High Fault Density'
}

# Road density bins
ROAD_DENSITY_DECODE = {
    1: 'Low Road Density',
    2: 'Moderate Road Density',
    3: 'High Road Density'
}

# Drainage class (from SSURGO)
DRAINAGE_CLASS_DECODE = {
    1: 'Excessively Drained',
    2: 'Somewhat Excessively Drained',
    3: 'Well Drained',
    4: 'Moderately Well Drained',
    5: 'Somewhat Poorly Drained',
    6: 'Poorly Drained',
    7: 'Very Poorly Drained'
}

# Land cover (NLCD 2021)
LAND_COVER_DECODE = {
    1: 'Open Water',
    2: 'Developed Open Space',
    3: 'Developed Low Intensity',
    4: 'Developed Medium Intensity',
    5: 'Developed High Intensity',
    6: 'Barren Land',
    7: 'Deciduous Forest',
    8: 'Evergreen Forest',
    9: 'Mixed Forest',
    10: 'Shrub/Scrub',
    11: 'Grassland/Herbaceous',
    12: 'Pasture/Hay',
    13: 'Cultivated Crops',
    14: 'Woody Wetlands',
    15: 'Emergent Herbaceous Wetlands'
}

# Soil Taxonomic Order
SOIL_ORDER_DECODE = {
    1: 'Alfisols',
    2: 'Andisols',
    3: 'Entisols',
    4: 'Histosols',
    5: 'Inceptisols',
    6: 'Mollisols',
    7: 'Spodosols',
    8: 'Ultisols'
}

# Rock Type (ThematicRo - simplified volcanic/sedimentary)
ROCK_TYPE_DECODE = {
    1: 'Volcanic - Basalt',
    2: 'Volcanic - Andesite',
    3: 'Sedimentary - Sandstone',
    4: 'Sedimentary - Siltstone',
    5: 'Sedimentary - Mudstone',
    6: 'Volcanic - Mixed',
    7: 'Sedimentary - Mixed',
    8: 'Intrusive'
}

# Tectonic Setting (ThematicTe)
TECTONIC_DECODE = {
    1: 'Coast Range - Western',
    2: 'Coast Range - Central',
    3: 'Coast Range - Eastern',
    4: 'Cascade Foothills',
    5: 'Willamette Valley Margin',
    6: 'Subduction Zone Proximal',
    7: 'Marine Terrace',
    8: 'Uplift Zone',
    9: 'Stable Platform',
    10: 'Transitional',
    11: 'Volcanic Plateau',
    12: 'Alluvial',
    13: 'Colluvial',
    14: 'Residual',
    15: 'Coastal Plain'
}

# Particle Size Class (taxpartsize)
PARTICLE_SIZE_DECODE = {
    1: 'Ashy',
    2: 'Ashy-skeletal',
    3: 'Clayey',
    4: 'Clayey-skeletal',
    5: 'Coarse-loamy',
    6: 'Coarse-silty',
    7: 'Fine',
    8: 'Fine-loamy',
    9: 'Fine-silty',
    10: 'Loamy',
    11: 'Loamy-skeletal',
    12: 'Medial',
    13: 'Medial-skeletal',
    14: 'Sandy',
    15: 'Medial over loamy-skeletal',  # Common in volcanic
    16: 'Sandy-skeletal',
    17: 'Pumiceous'
}

# Soil Subgroup (selected common ones)
SOIL_SUBGROUP_DECODE = {
    6: 'Typic Hapludands',
    9: 'Typic Fulvudands', 
    11: 'Alic Hapludands',
    22: 'Typic Dystrudepts',
    24: 'Andic Dystrudepts',
    35: 'Typic Humudepts',
    # Add more as needed from actual data
}

# Landslide outcome
LANDSLIDE_DECODE = {
    0: 'No Landslide (Stable)',
    1: 'Landslide Present'
}

# Master decoder dictionary
DECODERS = {
    'El': ELEVATION_DECODE,
    'Sl': SLOPE_DECODE,
    'As': ASPECT_DECODE,
    'Cl': CLAY_DECODE,
    'Fd': FAULT_DENSITY_DECODE,
    'Rd': ROAD_DENSITY_DECODE,
    'Dc': DRAINAGE_CLASS_DECODE,
    'Lc': LAND_COVER_DECODE,
    'To': SOIL_ORDER_DECODE,
    'Tp': PARTICLE_SIZE_DECODE,
    'Tb': SOIL_SUBGROUP_DECODE,
    'Ro': ROCK_TYPE_DECODE,
    'Tt': TECTONIC_DECODE,
    'Z': LANDSLIDE_DECODE
}

# =============================================================================
# DECODER FUNCTIONS
# =============================================================================

def decode_value(abbrev: str, value: int) -> str:
    """Decode a single variable value."""
    decoder = DECODERS.get(abbrev, {})
    if value in decoder:
        return decoder[value]
    return f"Code {value}"


def decode_rule_string(rule_str: str) -> str:
    """
    Decode a rule like "El=5,Tp=15,Ro=1,Tt=3 -> Z=0" into human-readable form.
    """
    # Split into condition and outcome
    if '->' in rule_str:
        condition, outcome = rule_str.split('->')
        condition = condition.strip()
        outcome = outcome.strip()
    else:
        condition = rule_str
        outcome = None
    
    # Parse conditions
    decoded_conditions = []
    for part in condition.split(','):
        part = part.strip()
        if '=' in part:
            abbrev, value = part.split('=')
            abbrev = abbrev.strip()
            try:
                value = int(value.strip())
            except ValueError:
                value = value.strip()
            
            var_name = ABBREV_TO_NAME.get(abbrev, abbrev)
            decoded_val = decode_value(abbrev, value) if isinstance(value, int) else value
            decoded_conditions.append(f"{var_name}: {decoded_val}")
    
    result = "\n  AND ".join(decoded_conditions)
    
    if outcome:
        outcome_parts = outcome.split('=')
        if len(outcome_parts) == 2:
            outcome_abbrev = outcome_parts[0].strip()
            outcome_val = int(outcome_parts[1].strip())
            outcome_decoded = decode_value(outcome_abbrev, outcome_val)
            result += f"\n  → PREDICTION: {outcome_decoded}"
    
    return result


def format_rule_for_practitioner(rule_row: dict) -> str:
    """Format a rule row from CSV into practitioner-friendly text."""
    iv_states = rule_row.get('iv_states', '')
    predicted = rule_row.get('predicted_dv', '')
    confidence = rule_row.get('confidence', 0)
    frequency = rule_row.get('frequency', 0)
    accuracy = rule_row.get('accuracy', 0)
    
    # Build the rule string
    rule_str = f"{iv_states} -> Z={predicted}"
    decoded = decode_rule_string(rule_str)
    
    output = f"""
{'='*60}
RULE: {iv_states} → Z={predicted}
{'='*60}
CONDITIONS:
  {decoded.split('→')[0].strip()}

PREDICTION: {'LANDSLIDE LIKELY' if str(predicted) == '1' else 'STABLE TERRAIN'}

STATISTICS:
  - Sample Size: {frequency:.0f} locations
  - Confidence: {confidence:.1f}%
  - Accuracy: {accuracy:.0f}%
"""
    return output


def decode_rules_csv(filepath: str, top_n: int = 25) -> str:
    """Decode rules from a CSV file."""
    df = pd.read_csv(filepath)
    
    output_lines = []
    output_lines.append("=" * 80)
    output_lines.append("DECODED LANDSLIDE PREDICTION RULES")
    output_lines.append("=" * 80)
    output_lines.append(f"\nSource: {Path(filepath).name}")
    output_lines.append(f"Total rules: {len(df)}")
    output_lines.append(f"Showing top {min(top_n, len(df))} by sample size\n")
    
    # Sort by frequency
    if 'frequency' in df.columns:
        df = df.sort_values('frequency', ascending=False)
    
    for i, (_, row) in enumerate(df.head(top_n).iterrows(), 1):
        output_lines.append(f"\n{'─'*60}")
        output_lines.append(f"RULE #{i}")
        output_lines.append(f"{'─'*60}")
        
        iv_states = row.get('iv_states', '')
        predicted = row.get('predicted_dv', 0)
        confidence = row.get('confidence', 0)
        frequency = row.get('frequency', 0)
        accuracy = row.get('accuracy', 0)
        
        # Parse the IV states (format: "El=5|Ro=1|Tt=3")
        if '|' in str(iv_states):
            parts = str(iv_states).split('|')
        else:
            parts = str(iv_states).split(',')
        
        output_lines.append("\nIF:")
        for part in parts:
            if '=' in part:
                abbrev, val = part.split('=')
                abbrev = abbrev.strip()
                try:
                    val = int(val.strip())
                except:
                    val = val.strip()
                var_name = ABBREV_TO_NAME.get(abbrev, abbrev)
                decoded_val = decode_value(abbrev, val) if isinstance(val, int) else val
                output_lines.append(f"  • {var_name} = {decoded_val}")
        
        # Prediction
        outcome = "🔴 LANDSLIDE LIKELY" if str(predicted) == '1' else "🟢 STABLE TERRAIN"
        output_lines.append(f"\nTHEN: {outcome}")
        
        # Stats
        output_lines.append(f"\nSTATISTICS:")
        output_lines.append(f"  • Samples: {frequency:.0f}")
        output_lines.append(f"  • Confidence: {confidence:.1f}%")
        output_lines.append(f"  • Accuracy: {accuracy:.0f}%")
    
    return '\n'.join(output_lines)


def create_practitioner_summary(volcanic_rules: str, sedimentary_rules: str = None) -> str:
    """Create a practitioner-friendly summary document."""
    
    summary = """
╔══════════════════════════════════════════════════════════════════════════════╗
║                    LANDSLIDE RISK ASSESSMENT GUIDELINES                      ║
║                   Oregon Coast Range - WTNSY Watersheds                      ║
╚══════════════════════════════════════════════════════════════════════════════╝

OVERVIEW
────────
This document provides decision rules for assessing landslide susceptibility
based on Reconstructability Analysis (RA) of ~19,000 sample points across
the Wilson-Trask-Nestucca-Siletz-Yaquina watersheds.

Rules are stratified by geology:
  • VOLCANIC terrain (basalt, andesite) - 6,948 samples
  • SEDIMENTARY terrain (sandstone, siltstone) - 12,559 samples

HOW TO USE THIS GUIDE
─────────────────────
1. First determine if your site is on VOLCANIC or SEDIMENTARY rock
2. Check the applicable rules below
3. Rules are listed by reliability (sample size and confidence)
4. Multiple matching rules = higher certainty


╔══════════════════════════════════════════════════════════════════════════════╗
║                          VOLCANIC TERRAIN RULES                              ║
╚══════════════════════════════════════════════════════════════════════════════╝

KEY FINDINGS:
• Elevation is the dominant predictor
• High elevation (>600m) areas are generally stable
• Low elevation (<150m) with certain soil types = high risk

"""
    summary += volcanic_rules if volcanic_rules else "[Volcanic rules would go here]"
    
    if sedimentary_rules:
        summary += """

╔══════════════════════════════════════════════════════════════════════════════╗
║                        SEDIMENTARY TERRAIN RULES                             ║
╚══════════════════════════════════════════════════════════════════════════════╝

KEY FINDINGS:
• Elevation AND Tectonic Setting interact (non-additive effect!)
• Soil subgroup classification is highly predictive
• Slope plays a stronger role than in volcanic terrain

"""
        summary += sedimentary_rules
    
    summary += """

════════════════════════════════════════════════════════════════════════════════
METHODOLOGY NOTES
════════════════════════════════════════════════════════════════════════════════

• Rules extracted using Reconstructability Analysis (RA)
• Minimum thresholds: 20 samples, 85% confidence, 90% accuracy, p<0.05
• Validated using spatial cross-validation (7km hexagonal blocks)
• Full methodology: [Journal Reference TBD]

For questions: Contact Portland State University Research Team
════════════════════════════════════════════════════════════════════════════════
"""
    
    return summary


# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    if len(sys.argv) > 1:
        arg = sys.argv[1]
        
        if arg == '--rule':
            # Decode a single rule
            if len(sys.argv) > 2:
                rule = sys.argv[2]
                print("\nDecoded Rule:")
                print(decode_rule_string(rule))
        
        elif arg.endswith('.csv'):
            # Decode rules from CSV
            filepath = arg
            if Path(filepath).exists():
                output = decode_rules_csv(filepath)
                print(output)
                
                # Save decoded version
                output_path = Path(filepath).stem + '_decoded.txt'
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(output)
                print(f"\n✓ Saved to: {output_path}")
            else:
                print(f"File not found: {filepath}")
        
        else:
            print(f"Unknown argument: {arg}")
            print("\nUsage:")
            print("  python decode_rules.py rules.csv")
            print("  python decode_rules.py --rule \"El=5,Tp=15,Ro=1\"")
    
    else:
        # Demo mode - decode some example rules
        print("\n" + "="*60)
        print("RULE DECODER DEMO")
        print("="*60)
        
        examples = [
            "El=5,Tp=15,Ro=1,Tt=3 -> Z=0",
            "El=1,Cl=1,Ro=6,Tt=15 -> Z=1",
            "El=1,Sl=2,Tb=9,Tt=1 -> Z=1",
            "El=5,Dc=7,Ro=6,Tt=11 -> Z=0"
        ]
        
        for rule in examples:
            print(f"\nOriginal: {rule}")
            print("-" * 40)
            print(decode_rule_string(rule))
