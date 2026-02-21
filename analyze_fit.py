#!/usr/bin/env python3
"""
OCCAM Fit Report Analyzer
Identifies and highlights notable patterns in fit reports
"""

import re
from typing import Dict, List, Tuple, Optional

# ============================================================================
# CONFIGURATION - Edit these settings
# ============================================================================

# Path to the fit report file to analyze
# Leave as None to use command-line argument
FIT_REPORT_FILE = None  # e.g., 'dementia05_fit_IV_ApZ_EdZ_CZ.csv'

# Optional: Path to save the analysis output
# Leave as None to print to stdout
OUTPUT_FILE = None  # e.g., 'analysis_output.txt'

# ============================================================================
# CONDITIONAL DV PATTERN THRESHOLDS
# ============================================================================

# Accuracy thresholds
HIGH_ACCURACY_THRESHOLD = 90   # % correct for "high accuracy" states
LOW_ACCURACY_THRESHOLD = 60    # % correct for "low accuracy" states

# Sample size thresholds
SPARSE_DATA_THRESHOLD = 5      # minimum samples for reliable predictions
MIN_FREQ_FOR_LOW_ACCURACY = 10 # minimum samples to flag low accuracy
MIN_FREQ_FOR_SIGNIFICANCE = 10 # minimum samples to report significant rules
MIN_FREQ_FOR_MISMATCH = 10     # minimum samples to report obs/pred mismatches

# Statistical thresholds
SIGNIFICANCE_THRESHOLD = 0.05  # p-value threshold for significance
LARGE_MISMATCH_THRESHOLD = 20  # % difference between observed and predicted

# ============================================================================
# OVERVIEW ASSESSMENT THRESHOLDS
# ============================================================================

# Information capture levels (%)
INFO_CAPTURE_LOW = 10       # Below this = "Low information capture"
INFO_CAPTURE_MODERATE = 30  # Below this = "Moderate", else check high threshold
INFO_CAPTURE_HIGH = 60      # Above this = "High information capture"

# Transmission (T) strength
TRANSMISSION_WEAK = 0.3     # Below this = "weak relationship"
TRANSMISSION_STRONG = 0.7   # Above this = "strong relationship"

# ============================================================================
# MODEL QUALITY THRESHOLDS
# ============================================================================

# p-value significance levels
P_HIGHLY_SIGNIFICANT = 0.001  # p < this = "highly significant"
P_SIGNIFICANT = 0.05          # p < this = "significant"

# ============================================================================
# CONFUSION MATRIX THRESHOLDS
# ============================================================================

# Overall accuracy assessment levels (%)
ACCURACY_EXCELLENT = 80  # >= this = "Excellent"
ACCURACY_GOOD = 70       # >= this = "Good"
ACCURACY_MODERATE = 60   # >= this = "Moderate", else "Poor"

# Performance metric thresholds
LOW_SENSITIVITY_THRESHOLD = 0.5   # Below this = "Low sensitivity"
LOW_SPECIFICITY_THRESHOLD = 0.5   # Below this = "Low specificity"
LOW_F1_THRESHOLD = 0.5            # Below this = "Low F1"

# Class balance
CLASS_IMBALANCE_THRESHOLD = 20  # % deviation from 50% = "imbalanced"

# ============================================================================


class FitReportAnalyzer:
    """Analyzes OCCAM fit reports and highlights interesting patterns"""
    
    def __init__(self, report_text: str):
        """
        Args:
            report_text: Full text of the fit report (from file or stdout)
        """
        self.report = report_text
        self.sections = self._parse_sections()
        
    def _parse_sections(self) -> Dict:
        """Parse the report into logical sections"""
        sections = {
            'header': self._extract_header_metrics(),
            'model_info': self._extract_model_info(),
            'lr_stats': self._extract_lr_stats(),
            'conditional_tables': self._extract_conditional_tables(),
            'confusion_matrices': self._extract_confusion_matrices()
        }
        return sections
    
    def _extract_header_metrics(self) -> Dict:
        """Extract key header statistics"""
        metrics = {}
        
        # Sample size
        match = re.search(r'Sample Size[^,]*,\s*(\d+)', self.report)
        if match:
            metrics['sample_size'] = int(match.group(1))
        
        # Test sample size
        match = re.search(r'Sample Size \(test\)[^,]*,\s*(\d+)', self.report)
        if match:
            metrics['test_sample_size'] = int(match.group(1))
            
        # Entropy measures
        for metric_name in ['H(data)', 'H(IV)', 'H(DV)', 'T(IV:DV)']:
            pattern = re.escape(metric_name) + r'[,\s]+([\d.]+)'
            match = re.search(pattern, self.report)
            if match:
                metrics[metric_name] = float(match.group(1))
        
        # Information captured
        match = re.search(r'Information captured \(%\)[^,]*,\s*([\d.]+)', self.report)
        if match:
            metrics['info_captured_pct'] = float(match.group(1))
        
        # Transmission
        match = re.search(r'Transmission \(T\)[^,]*,\s*([\d.]+)', self.report)
        if match:
            metrics['transmission'] = float(match.group(1))
            
        return metrics
    
    def _extract_model_info(self) -> Dict:
        """Extract model specification"""
        info = {}
        
        # Model name
        match = re.search(r'Model,([^\n]+)', self.report)
        if match:
            info['model_name'] = match.group(1).strip()
        
        # IVs in use
        match = re.search(r'IVs in use \((\d+)\), ([^\n]+)', self.report)
        if match:
            info['num_ivs'] = int(match.group(1))
            info['iv_list'] = match.group(2).strip()
        
        # DV
        match = re.search(r'DV,(\w+)', self.report)
        if match:
            info['dv'] = match.group(1)
            
        return info
    
    def _extract_lr_stats(self) -> Dict:
        """Extract likelihood ratio and chi-square statistics"""
        stats = {}
        
        # Reference = BOTTOM (model vs. independence)
        bottom_section = re.search(
            r'REFERENCE = BOTTOM.*?Log-Likelihood \(LR\),\s*([\d.]+),\s*([\d.]+)',
            self.report, re.DOTALL
        )
        if bottom_section:
            stats['lr_bottom'] = float(bottom_section.group(1))
            stats['lr_bottom_p'] = float(bottom_section.group(2))
        
        # Reference = TOP (model vs. saturated)
        top_section = re.search(
            r'REFERENCE = TOP.*?Log-Likelihood \(LR\),\s*([\d.]+),\s*([\d.]+)',
            self.report, re.DOTALL
        )
        if top_section:
            stats['lr_top'] = float(top_section.group(1))
            stats['lr_top_p'] = float(top_section.group(2))
        
        return stats
    
    def _extract_conditional_tables(self) -> List[Dict]:
        """Extract all conditional DV tables"""
        tables = []
        
        # Find all conditional DV sections
        pattern = r'Conditional DV.*?for the (?:Model|Relation) ([^\n]+)\n.*?IV order: ([^\n]+).*?\n(.*?)(?=\n\nRules marked|Confusion Matrix|\Z)'
        
        for match in re.finditer(pattern, self.report, re.DOTALL):
            relation = match.group(1).strip()
            iv_order = match.group(2).strip()
            table_text = match.group(3)
            
            # Parse rows
            rows = []
            for line in table_text.split('\n'):
                # Skip header and separator lines
                if '|' not in line or 'freq' in line or line.strip().startswith('|'):
                    continue
                
                parts = [p.strip() for p in line.split('|')]
                if len(parts) < 2:
                    continue
                
                # Parse data section
                data_cols = [c.strip() for c in parts[1].split(',') if c.strip()]
                if len(data_cols) < 3:  # Need at least freq, Z=0, Z=1
                    continue
                
                try:
                    freq = float(data_cols[0])
                    if freq == 0:
                        continue  # Skip zero-frequency rows
                    
                    # Check if we have model columns
                    if len(parts) > 2:
                        model_cols = [c.strip() for c in parts[2].split(',') if c.strip()]
                        if len(model_cols) >= 7:  # Full model output
                            row = {
                                'iv_state': parts[0].strip(),
                                'freq': freq,
                                'obs_dv0': float(data_cols[1]),
                                'obs_dv1': float(data_cols[2]),
                                'calc_dv0': float(model_cols[0]),
                                'calc_dv1': float(model_cols[1]),
                                'rule': int(model_cols[2]),
                                'n_correct': float(model_cols[3]),
                                'pct_correct': float(model_cols[4]),
                                'p_rule': float(model_cols[5]) if len(model_cols) > 5 else None,
                                'p_margin': float(model_cols[6]) if len(model_cols) > 6 else None,
                            }
                            rows.append(row)
                except (ValueError, IndexError) as e:
                    continue  # Skip malformed rows
            
            if rows:
                tables.append({
                    'relation': relation,
                    'iv_order': iv_order,
                    'rows': rows
                })
        
        return tables
    
    def _extract_confusion_matrices(self) -> List[Dict]:
        """Extract confusion matrix statistics"""
        matrices = []
        
        # Find all confusion matrix sections
        # First try with Model/Relation names
        cm_sections = re.split(r'Confusion Matrix for the (?:Model|Relation) ', self.report)[1:]
        
        # If that didn't find any, try without Model/Relation (just "Confusion Matrix for Fit Rule")
        if not cm_sections or len(cm_sections) <= 1:
            # For reports that don't have explicit relation names, find all CM sections
            # Use finditer instead of split to avoid capturing group issues
            pattern = r'Confusion Matrix for Fit Rule \((Training|Test)\)(.*?)(?=Confusion Matrix for Fit Rule|Conditional DV|\Z)'
            
            for match in re.finditer(pattern, self.report, re.DOTALL):
                dataset_type = match.group(1)  # Training or Test
                section = match.group(2)  # The confusion matrix content
                
                # Try to find relation name from preceding text
                start_pos = match.start()
                prev_text = self.report[max(0, start_pos-500):start_pos]
                
                # Look for relation names
                relation_match = None
                for pattern in [
                    r'for the Relation ([^\n]+)',
                    r'for the Model ([^\n]+)',
                    r'Conditional DV.*?for the (?:Model|Relation) ([^\n]+)',
                ]:
                    relation_match = re.search(pattern, prev_text)
                    if relation_match:
                        break
                
                if relation_match:
                    relation = f"{relation_match.group(1).strip()} ({dataset_type})"
                else:
                    relation = f"Full Model ({dataset_type})"
                
                self._extract_single_cm(section, relation, matrices)
            
            return matrices
        
        # Process Model/Relation format
        for section in cm_sections:
            # Extract relation name (first line)
            relation_match = re.match(r'([^\n]+)', section)
            if not relation_match:
                continue
            relation = relation_match.group(1).strip()
            
            self._extract_single_cm(section, relation, matrices)
        
        return matrices
    
    def _extract_single_cm(self, section: str, relation: str, matrices: List[Dict]):
        """Extract a single confusion matrix from a section"""
        # Extract values - note that metrics have format: "metric,definition,value"
        tn_match = re.search(r'TN=,?\s*([\d.]+)', section)
        fp_match = re.search(r'FP=,?\s*([\d.]+)', section)
        fn_match = re.search(r'FN=,?\s*([\d.]+)', section)
        tp_match = re.search(r'TP=,?\s*([\d.]+)', section)
        
        # These have format: metric,definition,value
        pct_match = re.search(r'%correct,[^,]*,([\d.]+)', section)
        sens_match = re.search(r'Sensitivity[^,]*,[^,]*,([\d.]+)', section)
        spec_match = re.search(r'Specificity,[^,]*,([\d.]+)', section)
        prec_match = re.search(r'Precision,[^,]*,([\d.]+)', section)
        npv_match = re.search(r'Negative Predictive Value,[^,]*,([\d.]+)', section)
        f1_match = re.search(r'F1 score,[^,]*,([\d.]+)', section)
        
        # Only add if we have the core values
        if all([tn_match, fp_match, fn_match, tp_match, pct_match, sens_match]):
            matrices.append({
                'relation': relation,
                'TN': float(tn_match.group(1)),
                'FP': float(fp_match.group(1)),
                'FN': float(fn_match.group(1)),
                'TP': float(tp_match.group(1)),
                'pct_correct': float(pct_match.group(1)),
                'sensitivity': float(sens_match.group(1)),
                'specificity': float(spec_match.group(1)) if spec_match else 0.0,
                'precision': float(prec_match.group(1)) if prec_match else 0.0,
                'npv': float(npv_match.group(1)) if npv_match else 0.0,
                'f1': float(f1_match.group(1)) if f1_match else 0.0,
            })
    
    def analyze(self) -> Dict:
        """Run all analyses and return findings"""
        findings = {
            'overview': self._analyze_overview(),
            'model_quality': self._analyze_model_quality(),
            'conditional_patterns': self._analyze_conditional_patterns(),
            'confusion_insights': self._analyze_confusion_matrices(),
            'recommendations': []
        }
        
        # Generate recommendations based on findings
        findings['recommendations'] = self._generate_recommendations(findings)
        
        return findings
    
    def _analyze_overview(self) -> Dict:
        """Analyze overall model characteristics"""
        header = self.sections['header']
        model = self.sections['model_info']
        
        insights = {
            'sample_info': f"Sample size: {header.get('sample_size', 'N/A')}",
            'complexity': f"{model.get('num_ivs', 'N/A')} independent variables",
            'model': model.get('model_name', 'N/A')
        }
        
        # Information capture assessment
        info_pct = header.get('info_captured_pct')
        if info_pct is not None:
            if info_pct < INFO_CAPTURE_LOW:
                insights['info_capture'] = f"Low information capture ({info_pct:.1f}%) - model may be too simple"
            elif info_pct < INFO_CAPTURE_MODERATE:
                insights['info_capture'] = f"Moderate information capture ({info_pct:.1f}%)"
            elif info_pct < INFO_CAPTURE_HIGH:
                insights['info_capture'] = f"Good information capture ({info_pct:.1f}%)"
            else:
                insights['info_capture'] = f"High information capture ({info_pct:.1f}%) - model captures substantial complexity"
        
        # Transmission assessment
        transmission = header.get('transmission')
        if transmission is not None:
            insights['transmission'] = f"T(IV:DV) = {transmission:.3f}"
            if transmission < TRANSMISSION_WEAK:
                insights['transmission'] += " (weak relationship)"
            elif transmission < TRANSMISSION_STRONG:
                insights['transmission'] += " (moderate relationship)"
            else:
                insights['transmission'] += " (strong relationship)"
        
        return insights
    
    def _analyze_model_quality(self) -> Dict:
        """Assess model fit quality"""
        lr = self.sections['lr_stats']
        
        insights = {}
        
        # LR vs. independence (BOTTOM)
        lr_bottom = lr.get('lr_bottom')
        lr_bottom_p = lr.get('lr_bottom_p')
        if lr_bottom is not None and lr_bottom_p is not None:
            if lr_bottom_p < P_HIGHLY_SIGNIFICANT:
                insights['vs_independence'] = f"Model significantly better than independence (LR={lr_bottom:.2f}, p<{P_HIGHLY_SIGNIFICANT})"
            elif lr_bottom_p < P_SIGNIFICANT:
                insights['vs_independence'] = f"Model better than independence (LR={lr_bottom:.2f}, p={lr_bottom_p:.3f})"
            else:
                insights['vs_independence'] = f"⚠️ Model not significantly better than independence (LR={lr_bottom:.2f}, p={lr_bottom_p:.3f})"
        
        # LR vs. saturated (TOP)
        lr_top_p = lr.get('lr_top_p')
        if lr_top_p is not None:
            if lr_top_p > P_SIGNIFICANT:
                insights['vs_saturated'] = f"Model fits data well (LR p={lr_top_p:.3f}, not significantly worse than saturated)"
            else:
                insights['vs_saturated'] = f"⚠️ Model fit is significantly worse than saturated (p={lr_top_p:.3f})"
        
        return insights
    
    def _analyze_conditional_patterns(self) -> List[Dict]:
        """Find interesting patterns in conditional tables"""
        patterns = []
        
        for table in self.sections['conditional_tables']:
            relation = table['relation']
            rows = table['rows']
            
            if not rows:
                continue
            
            # Find rows with extreme prediction accuracy
            high_accuracy = [r for r in rows if r['pct_correct'] >= HIGH_ACCURACY_THRESHOLD and r['freq'] >= SPARSE_DATA_THRESHOLD]
            if high_accuracy:
                patterns.append({
                    'type': 'high_accuracy',
                    'relation': relation,
                    'count': len(high_accuracy),
                    'details': f"{len(high_accuracy)} state(s) with ≥{HIGH_ACCURACY_THRESHOLD}% prediction accuracy",
                    'examples': [f"{r['iv_state']}: {r['pct_correct']:.1f}% correct (n={r['freq']:.0f})" 
                               for r in sorted(high_accuracy, key=lambda x: -x['pct_correct'])[:10]]
                })
            
            # Find rows with low accuracy (potential problem areas)
            low_accuracy = [r for r in rows if r['pct_correct'] < LOW_ACCURACY_THRESHOLD and r['freq'] >= MIN_FREQ_FOR_LOW_ACCURACY]
            if low_accuracy:
                patterns.append({
                    'type': 'low_accuracy',
                    'relation': relation,
                    'count': len(low_accuracy),
                    'details': f"⚠️ {len(low_accuracy)} state(s) with <{LOW_ACCURACY_THRESHOLD}% accuracy (n≥{MIN_FREQ_FOR_LOW_ACCURACY})",
                    'examples': [f"{r['iv_state']}: {r['pct_correct']:.1f}% correct (n={r['freq']:.0f})" 
                               for r in sorted(low_accuracy, key=lambda x: x['pct_correct'])[:10]]
                })
            
            # Find sparse data rows (low frequency)
            sparse_rows = [r for r in rows if r['freq'] < SPARSE_DATA_THRESHOLD]
            if sparse_rows:
                patterns.append({
                    'type': 'sparse_data',
                    'relation': relation,
                    'count': len(sparse_rows),
                    'details': f"ℹ️ {len(sparse_rows)} state(s) with <{SPARSE_DATA_THRESHOLD} samples (predictions unreliable)",
                })
            
            # Find significant rules (low p-values)
            sig_rules = [r for r in rows if r.get('p_rule') is not None and r['p_rule'] < SIGNIFICANCE_THRESHOLD and r['freq'] >= MIN_FREQ_FOR_SIGNIFICANCE]
            if sig_rules:
                patterns.append({
                    'type': 'significant_rules',
                    'relation': relation,
                    'count': len(sig_rules),
                    'details': f"✓ {len(sig_rules)} state(s) with statistically significant classification rules",
                    'examples': [f"{r['iv_state']}: p={r['p_rule']:.4f}" 
                               for r in sorted(sig_rules, key=lambda x: x['p_rule'])[:10]]
                })
            
            # Find large obs vs calc discrepancies
            large_diff = []
            for r in rows:
                if r['freq'] >= MIN_FREQ_FOR_MISMATCH:
                    diff = abs(r['obs_dv1'] - r['calc_dv1'])
                    if diff > LARGE_MISMATCH_THRESHOLD:  # Configurable threshold
                        large_diff.append((r, diff))
            
            if large_diff:
                patterns.append({
                    'type': 'prediction_mismatch',
                    'relation': relation,
                    'count': len(large_diff),
                    'details': f"⚠️ {len(large_diff)} state(s) with >{LARGE_MISMATCH_THRESHOLD}% difference between observed and predicted",
                    'examples': [f"{r['iv_state']}: obs={r['obs_dv1']:.1f}% vs pred={r['calc_dv1']:.1f}%" 
                               for r, diff in sorted(large_diff, key=lambda x: -x[1])[:10]]
                })
        
        return patterns
    
    def _analyze_confusion_matrices(self) -> List[Dict]:
        """Analyze confusion matrix performance"""
        insights = []
        
        for cm in self.sections['confusion_matrices']:
            relation = cm['relation']
            
            # Overall accuracy assessment
            pct = cm['pct_correct'] * 100
            if pct >= ACCURACY_EXCELLENT:
                acc_level = "Excellent"
            elif pct >= ACCURACY_GOOD:
                acc_level = "Good"
            elif pct >= ACCURACY_MODERATE:
                acc_level = "Moderate"
            else:
                acc_level = "⚠️ Poor"
            
            insight = {
                'relation': relation,
                'accuracy': f"{acc_level} overall accuracy: {pct:.1f}%",
                'metrics': {}
            }
            
            # Identify strongest and weakest metrics
            metrics = {
                'Sensitivity': cm['sensitivity'],
                'Specificity': cm['specificity'],
                'Precision': cm['precision'],
                'NPV': cm['npv'],
                'F1': cm['f1']
            }
            
            best_metric = max(metrics.items(), key=lambda x: x[1])
            worst_metric = min(metrics.items(), key=lambda x: x[1])
            
            insight['best'] = f"Strongest: {best_metric[0]} = {best_metric[1]:.3f}"
            insight['worst'] = f"Weakest: {worst_metric[0]} = {worst_metric[1]:.3f}"
            
            # Class balance
            total_positive = cm['TP'] + cm['FN']
            total_negative = cm['TN'] + cm['FP']
            total = total_positive + total_negative
            
            pos_pct = (total_positive / total) * 100
            neg_pct = (total_negative / total) * 100
            
            if abs(pos_pct - 50) > CLASS_IMBALANCE_THRESHOLD:
                insight['balance'] = f"⚠️ Imbalanced classes: {neg_pct:.1f}% negative, {pos_pct:.1f}% positive"
            else:
                insight['balance'] = f"Balanced classes: {neg_pct:.1f}% negative, {pos_pct:.1f}% positive"
            
            # Performance notes
            notes = []
            if cm['sensitivity'] < LOW_SENSITIVITY_THRESHOLD:
                notes.append("Low sensitivity - many false negatives")
            if cm['specificity'] < LOW_SPECIFICITY_THRESHOLD:
                notes.append("Low specificity - many false positives")
            if cm['f1'] < LOW_F1_THRESHOLD:
                notes.append("Low F1 score - poor overall classification")
            
            if notes:
                insight['concerns'] = notes
            
            insights.append(insight)
        
        return insights
    
    def _generate_recommendations(self, findings: Dict) -> List[str]:
        """Generate actionable recommendations"""
        recs = []
        
        # Based on information capture
        overview = findings['overview']
        if 'info_capture' in overview:
            if 'Low' in overview['info_capture']:
                recs.append("Consider adding more IVs or interactions to capture more information")
            elif 'High' in overview['info_capture']:
                recs.append("Model captures substantial complexity - verify against overfitting")
        
        # Based on model quality
        quality = findings['model_quality']
        if 'vs_independence' in quality and '⚠️' in quality['vs_independence']:
            recs.append("Model not significantly better than independence - consider simpler model or different variables")
        
        # Based on confusion matrices
        for cm_insight in findings['confusion_insights']:
            if 'concerns' in cm_insight:
                rel = cm_insight['relation']
                for concern in cm_insight['concerns']:
                    recs.append(f"{rel}: {concern}")
        
        # Based on conditional patterns
        for pattern in findings['conditional_patterns']:
            if pattern['type'] == 'low_accuracy':
                recs.append(f"{pattern['relation']}: Investigate low-accuracy states for potential confounds")
            elif pattern['type'] == 'prediction_mismatch':
                recs.append(f"{pattern['relation']}: Large observed vs predicted differences suggest model misspecification")
        
        return recs
    
    def print_summary(self):
        """Print a human-readable summary of findings"""
        findings = self.analyze()
        
        print("=" * 80)
        print("FIT REPORT ANALYSIS SUMMARY")
        print("=" * 80)
        
        print("\n📊 OVERVIEW")
        print("-" * 80)
        for key, value in findings['overview'].items():
            print(f"  {value}")
        
        print("\n📈 MODEL QUALITY")
        print("-" * 80)
        for key, value in findings['model_quality'].items():
            print(f"  {value}")
        
        print("\n🎯 CONDITIONAL DV PATTERNS")
        print("-" * 80)
        if findings['conditional_patterns']:
            current_relation = None
            for pattern in findings['conditional_patterns']:
                if pattern['relation'] != current_relation:
                    current_relation = pattern['relation']
                    print(f"\n  {current_relation}:")
                
                print(f"    • {pattern['details']}")
                if 'examples' in pattern:
                    for ex in pattern['examples']:
                        print(f"      - {ex}")
        else:
            print("  No notable patterns found")
        
        print("\n🎲 CONFUSION MATRIX PERFORMANCE")
        print("-" * 80)
        for insight in findings['confusion_insights']:
            print(f"\n  {insight['relation']}:")
            print(f"    • {insight['accuracy']}")
            print(f"    • {insight['best']}")
            print(f"    • {insight['worst']}")
            print(f"    • {insight['balance']}")
            if 'concerns' in insight:
                for concern in insight['concerns']:
                    print(f"    ⚠️  {concern}")
        
        if findings['recommendations']:
            print("\n💡 RECOMMENDATIONS")
            print("-" * 80)
            for i, rec in enumerate(findings['recommendations'], 1):
                print(f"  {i}. {rec}")
        
        print("\n" + "=" * 80)


# Standalone usage
if __name__ == "__main__":
    import sys
    
    # Determine which file to analyze
    input_file = FIT_REPORT_FILE
    
    # Command-line argument overrides config
    if len(sys.argv) >= 2:
        input_file = sys.argv[1]
    
    if not input_file:
        print("Error: No input file specified!")
        print()
        print("Either:")
        print("  1. Edit the FIT_REPORT_FILE variable at the top of this script")
        print("  2. Run with: python analyze_fit.py <fit_report_file>")
        sys.exit(1)
    
    # Load the report
    try:
        with open(input_file, 'r') as f:
            report = f.read()
    except FileNotFoundError:
        print(f"Error: File not found: {input_file}")
        sys.exit(1)
    except Exception as e:
        print(f"Error reading file: {e}")
        sys.exit(1)
    
    # Analyze
    analyzer = FitReportAnalyzer(report)
    
    # Determine output destination
    if OUTPUT_FILE:
        try:
            with open(OUTPUT_FILE, 'w') as f:
                import io
                import contextlib
                
                # Capture print output
                string_buffer = io.StringIO()
                with contextlib.redirect_stdout(string_buffer):
                    analyzer.print_summary()
                
                # Write to file
                output = string_buffer.getvalue()
                f.write(output)
                
            print(f"Analysis complete! Output written to: {OUTPUT_FILE}")
            print(f"Analyzed: {input_file}")
        except Exception as e:
            print(f"Error writing to output file: {e}")
            print("\nPrinting to stdout instead:\n")
            analyzer.print_summary()
    else:
        # Print to stdout
        analyzer.print_summary()
