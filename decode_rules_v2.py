#!/usr/bin/env python3
"""
WTNSY Landslide Rule Decoder v2
================================

Translates encoded rule values into human-readable descriptions.
Uses REBINNED group names for maximum interpretability.

Usage:
    python decode_rules_v2.py rules_volcanic_20260113_012632.csv
    python decode_rules_v2.py --rule "El=5,Tp=3,Ro=1,Tt=3"

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
    'Gd': 'Geomorphic Desc',
    'Ts': 'Soil Suborder',
    'Tg': 'Soil Great Group',
    'Tb': 'Soil Subgroup',
    'Tp': 'Particle Size',
    'Ro': 'Rock Type',
    'Tt': 'Tectonic Setting',
    'Z': 'Landslide'
}

# =============================================================================
# REBINNED VALUE DECODERS - From YAML configs
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

# Stream density bins
STREAM_DENSITY_DECODE = {
    1: 'Low Stream Density',
    2: 'Moderate Stream Density',
    3: 'High Stream Density'
}

# Drainage class (from SSURGO) - REBINNED
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

# =============================================================================
# REBINNED CATEGORICAL VARIABLES - From YAML configs
# =============================================================================

# Particle Size Class (taxpartsize) - REBINNED from 17 to 7 groups
PARTICLE_SIZE_DECODE = {
    1: 'Fine/Clayey (high plasticity)',
    2: 'Fine-Loamy/Silty (high water retention)',
    3: 'MEDIAL VOLCANIC (water-sensitive ash!)',  # THE KEY ONE
    4: 'Mixed Medial-Over (complex hydrology)',
    5: 'Coarse/Sandy (low cohesion)',
    6: 'Loamy-Skeletal (rock fragments)',
    7: 'Other particle sizes'
}

# Soil Subgroup (taxsubgrp) - REBINNED from 58 to 7 groups
SOIL_SUBGROUP_DECODE = {
    1: '⚠️ ANDIC DYSTRUDEPTS (THE KILLER SOIL)',  # Marine sediment + volcanic ash
    2: 'Volcanic Andisols (well-developed ash)',
    3: 'Marine Dystrudepts (no volcanic influence)',
    4: '✓ POORLY DRAINED AQUIC (THE SAFE ZONE)',  # Wetlands, flat positions
    5: 'Recent Alluvial (young floodplain)',
    6: 'Well-Drained Upland (ridges/upper slopes)',
    7: 'Other subgroups'
}

# Soil Great Group (taxgrtgroup) - Common groups in Coast Range
SOIL_GREAT_GROUP_DECODE = {
    1: 'Humudepts',
    2: 'Dystrudepts', 
    3: 'Hapludands',
    4: 'Fulvudands',
    5: 'Melanudands',
    6: 'Fulvudands (high OM volcanic)',
    7: 'Endoaquepts',
    8: 'Haplorthods',
    9: 'Udifluvents',
    10: 'Udorthents',
    11: 'Cryaquepts',
    12: 'Haplocryands',
    13: 'Cryorthods',
    14: 'Humudepts (common in sedimentary)',
    15: 'Dystrochrepts',
    16: 'Haplumbrepts',
    17: 'Eutrochrepts',
    18: 'Fragiochrepts',
    19: 'Vitricryands',
    20: 'Udivitrands',
    21: 'Hapludalfs',
    22: 'Fulvudands (volcanic, high risk)',
}

# Geomorphic Description - REBINNED from 41 to 8 groups  
GEOMDESC_DECODE = {
    1: 'Hillslope/Mountain slopes',
    2: 'Ridges and summits',
    3: 'Valleys and draws',
    4: 'Terraces and benches',
    5: 'Floodplains',
    6: 'Coastal features',
    7: 'Glacial features',
    8: 'Other landforms'
}

# Rock Type (ThematicRo)
ROCK_TYPE_DECODE = {
    1: 'Basalt (volcanic)',
    2: 'Andesite (volcanic)',
    3: 'Sandstone (sedimentary)',
    4: 'Siltstone (sedimentary)',
    5: 'Mudstone (sedimentary)',
    6: 'Mixed Volcanic',
    7: 'Mixed Sedimentary',
    8: 'Intrusive igneous'
}

# Tectonic Setting (ThematicTe)
TECTONIC_DECODE = {
    1: '⚠️ COAST RANGE WESTERN (high risk zone)',
    2: 'Coast Range Central',
    3: 'Coast Range Eastern',
    4: 'Cascade Foothills',
    5: 'Willamette Valley Margin',
    6: 'Subduction Zone Proximal',
    7: 'Marine Terrace',
    8: 'Uplift Zone',
    9: '✓ STABLE PLATFORM (low risk)',
    10: 'Transitional Zone',
    11: 'Volcanic Plateau',
    12: 'Alluvial',
    13: 'Colluvial',
    14: 'Residual',
    15: '⚠️ COASTAL PLAIN (high risk in volcanic)'
}

# Landslide outcome
LANDSLIDE_DECODE = {
    0: '🟢 STABLE (No Landslide)',
    1: '🔴 LANDSLIDE'
}

# Master decoder dictionary
DECODERS = {
    'El': ELEVATION_DECODE,
    'Sl': SLOPE_DECODE,
    'As': ASPECT_DECODE,
    'Cl': CLAY_DECODE,
    'Fd': FAULT_DENSITY_DECODE,
    'Rd': ROAD_DENSITY_DECODE,
    'Sd': STREAM_DENSITY_DECODE,
    'Dc': DRAINAGE_CLASS_DECODE,
    'Lc': LAND_COVER_DECODE,
    'To': SOIL_ORDER_DECODE,
    'Tg': SOIL_GREAT_GROUP_DECODE,
    'Tb': SOIL_SUBGROUP_DECODE,
    'Tp': PARTICLE_SIZE_DECODE,
    'Gd': GEOMDESC_DECODE,
    'Ro': ROCK_TYPE_DECODE,
    'Tt': TECTONIC_DECODE,
    'Z': LANDSLIDE_DECODE
}

# Short versions for compact display
DECODERS_SHORT = {
    'El': {1: '<150m', 2: '150-300m', 3: '300-450m', 4: '450-600m', 5: '>600m'},
    'Sl': {1: '<10°', 2: '10-20°', 3: '20-30°', 4: '30-45°', 5: '>45°'},
    'Cl': {1: '<10%', 2: '10-20%', 3: '20-30%', 4: '30-40%', 5: '>40%'},
    'Tp': {1: 'Clayey', 2: 'Fine-Loamy', 3: 'MEDIAL-VOLC', 4: 'Mixed-Medial', 5: 'Sandy', 6: 'Loamy-Skel', 7: 'Other'},
    'Tb': {1: 'KILLER-SOIL', 2: 'Volc-Andisol', 3: 'Marine-Dyst', 4: 'SAFE-AQUIC', 5: 'Alluvial', 6: 'Upland', 7: 'Other'},
    'Tt': {1: 'CR-WEST⚠️', 2: 'CR-Central', 3: 'CR-East', 7: 'Terrace', 9: 'STABLE✓', 10: 'Trans', 11: 'Volc-Plat', 15: 'COASTAL⚠️'},
    'Ro': {1: 'Basalt', 2: 'Andesite', 3: 'Sandstone', 4: 'Siltstone', 5: 'Mudstone', 6: 'Mixed-Volc', 7: 'Mixed-Sed', 8: 'Intrusive'},
    'Z': {0: 'STABLE', 1: 'LANDSLIDE'}
}

# =============================================================================
# DECODER FUNCTIONS
# =============================================================================

def decode_value(abbrev: str, value: int, short: bool = False) -> str:
    """Decode a single variable value."""
    if short:
        decoder = DECODERS_SHORT.get(abbrev, DECODERS.get(abbrev, {}))
    else:
        decoder = DECODERS.get(abbrev, {})
    
    if value in decoder:
        return decoder[value]
    return f"Code {value}"


def decode_rule_string(rule_str: str, short: bool = False) -> str:
    """
    Decode a rule like "El=5,Tp=3,Ro=1,Tt=3 -> Z=0" into human-readable form.
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
            decoded_val = decode_value(abbrev, value, short) if isinstance(value, int) else value
            
            if short:
                decoded_conditions.append(f"{abbrev}={decoded_val}")
            else:
                decoded_conditions.append(f"{var_name}: {decoded_val}")
    
    if short:
        result = " + ".join(decoded_conditions)
    else:
        result = "\n  AND ".join(decoded_conditions)
    
    if outcome:
        outcome_parts = outcome.split('=')
        if len(outcome_parts) == 2:
            outcome_abbrev = outcome_parts[0].strip()
            outcome_val = int(outcome_parts[1].strip())
            outcome_decoded = decode_value(outcome_abbrev, outcome_val, short)
            if short:
                result += f" → {outcome_decoded}"
            else:
                result += f"\n  → PREDICTION: {outcome_decoded}"
    
    return result


def decode_rules_csv(filepath: str, top_n: int = 25, format_type: str = 'full') -> str:
    """
    Decode rules from a CSV file.
    
    format_type: 'full', 'compact', or 'table'
    """
    df = pd.read_csv(filepath)
    
    output_lines = []
    
    if format_type == 'table':
        return decode_rules_as_table(df, top_n)
    
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
        iv_states = row.get('iv_states', '')
        predicted = row.get('predicted_dv', 0)
        confidence = row.get('confidence', 0)
        frequency = row.get('frequency', 0)
        accuracy = row.get('accuracy', 0)
        
        # Parse the IV states
        if '|' in str(iv_states):
            parts = str(iv_states).split('|')
        else:
            parts = str(iv_states).split(',')
        
        if format_type == 'compact':
            # Compact one-liner format
            decoded_parts = []
            for part in parts:
                if '=' in part:
                    abbrev, val = part.split('=')
                    abbrev = abbrev.strip()
                    try:
                        val = int(val.strip())
                        decoded = decode_value(abbrev, val, short=True)
                    except:
                        decoded = val
                    decoded_parts.append(f"{abbrev}={decoded}")
            
            outcome = "🔴 LS" if str(predicted) == '1' else "🟢 STABLE"
            rule_str = " + ".join(decoded_parts)
            output_lines.append(f"{i:2}. {rule_str} → {outcome}  [n={frequency:.0f}, {confidence:.0f}% conf]")
        
        else:  # full format
            output_lines.append(f"\n{'─'*60}")
            output_lines.append(f"RULE #{i}")
            output_lines.append(f"{'─'*60}")
            
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


def decode_rules_as_table(df: pd.DataFrame, top_n: int = 25) -> str:
    """Format rules as a markdown table for papers."""
    lines = []
    lines.append("| # | Conditions | Prediction | n | Conf | Acc |")
    lines.append("|---|------------|------------|---|------|-----|")
    
    if 'frequency' in df.columns:
        df = df.sort_values('frequency', ascending=False)
    
    for i, (_, row) in enumerate(df.head(top_n).iterrows(), 1):
        iv_states = row.get('iv_states', '')
        predicted = row.get('predicted_dv', 0)
        confidence = row.get('confidence', 0)
        frequency = row.get('frequency', 0)
        accuracy = row.get('accuracy', 0)
        
        # Parse and decode
        if '|' in str(iv_states):
            parts = str(iv_states).split('|')
        else:
            parts = str(iv_states).split(',')
        
        decoded_parts = []
        for part in parts:
            if '=' in part:
                abbrev, val = part.split('=')
                abbrev = abbrev.strip()
                try:
                    val = int(val.strip())
                    decoded = decode_value(abbrev, val, short=True)
                except:
                    decoded = val
                decoded_parts.append(f"{abbrev}={decoded}")
        
        conditions = " + ".join(decoded_parts)
        outcome = "🔴 LS" if str(predicted) == '1' else "🟢 STABLE"
        
        lines.append(f"| {i} | {conditions} | {outcome} | {frequency:.0f} | {confidence:.0f}% | {accuracy:.0f}% |")
    
    return '\n'.join(lines)


def create_practitioner_cards(df: pd.DataFrame, stratum: str = "Unknown") -> str:
    """Create field-ready decision cards."""
    lines = []
    lines.append("╔" + "═"*70 + "╗")
    lines.append(f"║  LANDSLIDE RISK DECISION CARDS - {stratum.upper()} TERRAIN".ljust(71) + "║")
    lines.append("╚" + "═"*70 + "╝")
    lines.append("")
    
    if 'frequency' in df.columns:
        df = df.sort_values('frequency', ascending=False)
    
    # Separate stable and landslide rules
    stable_rules = df[df['predicted_dv'] == 0].head(10)
    landslide_rules = df[df['predicted_dv'] == 1].head(10)
    
    lines.append("🟢 LOW RISK INDICATORS (predict STABLE)")
    lines.append("─" * 70)
    for _, row in stable_rules.iterrows():
        iv_states = row.get('iv_states', '')
        confidence = row.get('confidence', 0)
        frequency = row.get('frequency', 0)
        
        if '|' in str(iv_states):
            parts = str(iv_states).split('|')
        else:
            parts = str(iv_states).split(',')
        
        decoded_parts = []
        for part in parts:
            if '=' in part:
                abbrev, val = part.split('=')
                try:
                    decoded = decode_value(abbrev.strip(), int(val.strip()), short=True)
                except:
                    decoded = val.strip()
                decoded_parts.append(decoded)
        
        lines.append(f"  ✓ {' + '.join(decoded_parts)}")
        lines.append(f"    ({confidence:.0f}% confident, n={frequency:.0f})")
        lines.append("")
    
    lines.append("")
    lines.append("🔴 HIGH RISK INDICATORS (predict LANDSLIDE)")
    lines.append("─" * 70)
    for _, row in landslide_rules.iterrows():
        iv_states = row.get('iv_states', '')
        confidence = row.get('confidence', 0)
        frequency = row.get('frequency', 0)
        
        if '|' in str(iv_states):
            parts = str(iv_states).split('|')
        else:
            parts = str(iv_states).split(',')
        
        decoded_parts = []
        for part in parts:
            if '=' in part:
                abbrev, val = part.split('=')
                try:
                    decoded = decode_value(abbrev.strip(), int(val.strip()), short=True)
                except:
                    decoded = val.strip()
                decoded_parts.append(decoded)
        
        lines.append(f"  ⚠️ {' + '.join(decoded_parts)}")
        lines.append(f"    ({confidence:.0f}% confident, n={frequency:.0f})")
        lines.append("")
    
    return '\n'.join(lines)


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
                print("\n" + "="*60)
                print("DECODED RULE (Full)")
                print("="*60)
                print(decode_rule_string(rule, short=False))
                print("\n" + "-"*60)
                print("DECODED RULE (Compact)")
                print("-"*60)
                print(decode_rule_string(rule, short=True))
        
        elif arg.endswith('.csv'):
            # Decode rules from CSV
            filepath = arg
            format_type = 'compact'  # Default
            if len(sys.argv) > 2:
                format_type = sys.argv[2]  # 'full', 'compact', 'table', or 'cards'
            
            if Path(filepath).exists():
                df = pd.read_csv(filepath)
                
                if format_type == 'cards':
                    # Determine stratum from filename
                    stratum = 'volcanic' if 'volcanic' in filepath.lower() else 'sedimentary'
                    output = create_practitioner_cards(df, stratum)
                else:
                    output = decode_rules_csv(filepath, format_type=format_type)
                
                print(output)
                
                # Save decoded version
                output_path = Path(filepath).stem + f'_decoded_{format_type}.txt'
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(output)
                print(f"\n✓ Saved to: {output_path}")
            else:
                print(f"File not found: {filepath}")
        
        else:
            print(f"Unknown argument: {arg}")
            print("\nUsage:")
            print("  python decode_rules_v2.py rules.csv [full|compact|table|cards]")
            print("  python decode_rules_v2.py --rule \"El=5,Tp=3,Ro=1\"")
    
    else:
        # Demo mode
        print("\n" + "="*70)
        print("RULE DECODER v2 - DEMO")
        print("="*70)
        
        examples = [
            ("Volcanic Stable", "El=5,Tp=3,Ro=1,Tt=3 -> Z=0"),
            ("Volcanic Landslide", "El=1,Tp=3,Tt=15 -> Z=1"),
            ("Sedimentary Killer Soil", "El=1,Sl=2,Tb=1,Tt=1 -> Z=1"),
            ("Sedimentary Safe Zone", "El=5,Tb=4,Tt=9 -> Z=0"),
        ]
        
        for name, rule in examples:
            print(f"\n{'─'*70}")
            print(f"EXAMPLE: {name}")
            print(f"{'─'*70}")
            print(f"Original: {rule}")
            print(f"\nCompact:  {decode_rule_string(rule, short=True)}")
            print(f"\nFull:")
            print(decode_rule_string(rule, short=False))
