#!/usr/bin/env python3
"""
OCCAM Fit Report Analyzer
Identifies and highlights notable patterns in fit reports

Usage:
    # As a module (recommended):
    from pyoccam.analyze_fit import FitReportAnalyzer
    analyzer = FitReportAnalyzer(fit_report_text)
    analyzer.print_summary()

    # Standalone:
    python -m pyoccam.analyze_fit my_fit_report.txt
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
    """Analyzes OCCAM fit reports and highlights interesting patterns.

    Parses the text output of generate_fit_report() and identifies:
    - Model quality (information capture, transmission, LR statistics)
    - Conditional DV patterns (high/low accuracy combos, significant rules,
      obs vs. predicted mismatches, sparse data warnings)
    - Confusion matrix performance (accuracy, sensitivity, specificity, F1,
      class balance, best/worst metrics)
    - Actionable recommendations based on all of the above

    Usage::

        # With fit report text + confusion matrix dict (recommended)
        report = manager.generate_fit_report(model_name, target_state="0")
        cm = manager.get_confusion_matrix(model_name, target_state="0")
        analyzer = FitReportAnalyzer(report, cm_dict=cm)
        analyzer.print_summary()

        # Text-only (standalone file analysis)
        analyzer = FitReportAnalyzer(report_text)
        findings = analyzer.analyze()     # structured dict for programmatic use
    """

    def __init__(self, report_text: str, cm_dict: Optional[Dict] = None):
        """
        Args:
            report_text: Full text of the fit report (from generate_fit_report)
            cm_dict: Optional confusion matrix dict from get_confusion_matrix().
                     Uses sklearn-compatible keys: train_tn, train_fp, train_fn,
                     train_tp, train_accuracy, train_sensitivity, etc.
                     When provided, this is used instead of parsing text for CM.
        """
        self.report = report_text
        self.cm_dict = cm_dict
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
        """Extract key header statistics.

        Handles both text format ('Sample size: 424') and CSV format
        ('Sample Size, 424').
        """
        metrics = {}

        # Sample size - text format: "Sample size: 424"
        match = re.search(r'Sample size:\s*(\d+)', self.report)
        if not match:
            # CSV format fallback
            match = re.search(r'Sample Size[^,]*,\s*(\d+)', self.report)
        if match:
            metrics['sample_size'] = int(match.group(1))

        # Test data present
        match = re.search(r'Test data:\s*(\w+)', self.report)
        if match:
            metrics['has_test_data'] = match.group(1).strip().lower() == 'present'

        # Variables count
        match = re.search(r'Variables:\s*(\d+)', self.report)
        if match:
            metrics['num_variables'] = int(match.group(1))

        # Entropy - text format: "Entropy(H):  9.58773"
        match = re.search(r'Entropy\(H\):\s*([\d.]+)', self.report)
        if match:
            metrics['entropy'] = float(match.group(1))

        # Information captured - text format: "Information captured (%):  13.9069"
        match = re.search(r'Information captured \(%\):\s*([\d.]+)', self.report)
        if not match:
            match = re.search(r'Information captured \(%\)[^,]*,\s*([\d.]+)', self.report)
        if match:
            metrics['info_captured_pct'] = float(match.group(1))

        # Transmission - text format: "Transmission (T):  0.859812"
        match = re.search(r'Transmission \(T\):\s*([\d.eE+-]+)', self.report)
        if not match:
            match = re.search(r'Transmission \(T\)[^,]*,\s*([\d.eE+-]+)', self.report)
        if match:
            metrics['transmission'] = float(match.group(1))

        # Loops
        match = re.search(r'Loops:\s*(\w+)', self.report)
        if match:
            metrics['has_loops'] = match.group(1).strip().upper() != 'NO'

        # Degrees of freedom
        match = re.search(r'Degrees of Freedom \(DF\):\s*([\d.eE+]+)', self.report)
        if match:
            metrics['df'] = float(match.group(1))

        return metrics

    def _extract_model_info(self) -> Dict:
        """Extract model specification from text format.

        Parses lines like:
            Model  IV:ApSxAZ (Directed System)
            IV Component:  APOE; Gender; ...  ApSxEdAg...
            Model Component:   APOE; Gender; rs1801133; CaseControl  ApSxAZ
        """
        info = {}

        # Model name - text format: "    Model  IV:ApSxAZ (Directed System)"
        match = re.search(r'^\s*Model\s+(IV:\S+|[A-Z][A-Za-z:]+)', self.report, re.MULTILINE)
        if not match:
            # CSV fallback
            match = re.search(r'Model,([^\n]+)', self.report)
        if match:
            info['model_name'] = match.group(1).strip()

        # IV Component - text format: "IV Component:  APOE; Gender; ...  AbbrCode"
        match = re.search(r'IV Component:\s*(.+?)(?:\s{2,}\S+)?\s*$', self.report, re.MULTILINE)
        if match:
            iv_text = match.group(1).strip()
            # Split on semicolons to get individual IVs
            ivs = [v.strip() for v in iv_text.split(';') if v.strip()]
            info['num_ivs'] = len(ivs)
            info['iv_list'] = '; '.join(ivs)

        # Model Component
        match = re.search(r'Model Component:\s*(.+?)(?:\s{2,}\S+)?\s*$', self.report, re.MULTILINE)
        if match:
            info['model_component'] = match.group(1).strip()

        # DV - extract from model component or look for DV line
        match = re.search(r'DV[,:\s]+(\w+)', self.report)
        if match:
            info['dv'] = match.group(1)

        return info

    def _extract_lr_stats(self) -> Dict:
        """Extract likelihood ratio and chi-square statistics.

        Handles text format:
            REFERENCE = BOTTOM
              Value  Prob. (Alpha)
            Log-Likelihood (LR)  81.6367  0
            Pearson X2  241.458
            Delta DF (dDF)  11
        """
        stats = {}

        # Reference = BOTTOM (model vs. independence)
        bottom_match = re.search(
            r'REFERENCE = BOTTOM.*?Log-Likelihood \(LR\)\s+([\d.eE+-]+)\s+([\d.eE+-]+)',
            self.report, re.DOTALL
        )
        if bottom_match:
            stats['lr_bottom'] = float(bottom_match.group(1))
            stats['lr_bottom_p'] = float(bottom_match.group(2))

        # Reference = TOP (model vs. saturated)
        top_match = re.search(
            r'REFERENCE = TOP.*?Log-Likelihood \(LR\)\s+([\d.eE+-]+)\s+([\d.eE+-]+)',
            self.report, re.DOTALL
        )
        if top_match:
            stats['lr_top'] = float(top_match.group(1))
            stats['lr_top_p'] = float(top_match.group(2))

        return stats

    def _extract_conditional_tables(self) -> List[Dict]:
        """Extract all conditional DV tables.

        Parses the pipe-separated text format:
            Ap  Sx  A  |  freq  Z=0  Z=1  |  Z=0  Z=1  rule  #correct  %correct  p(rule)  p(margin)
            0   0   0  |  15.0  86.7 13.3  |  86.7 13.3  0     13.0     86.667    0.004    0.007
        """
        tables = []

        # Find all conditional DV sections
        pattern = r'Conditional DV.*?for the (?:Model|Relation)\s+([^\n.]+)\.?\n.*?IV order:\s*([^\n.]+)\.?\n(.*?)(?=Rules marked|Confusion Matrix|Performance on Test|\Z)'

        for match in re.finditer(pattern, self.report, re.DOTALL):
            relation = match.group(1).strip()
            iv_order = match.group(2).strip()
            table_text = match.group(3)

            rows = self._parse_conditional_rows(table_text)

            if rows:
                tables.append({
                    'relation': relation,
                    'iv_order': iv_order,
                    'rows': rows
                })

        return tables

    def _parse_conditional_rows(self, table_text: str) -> List[Dict]:
        """Parse data rows from a conditional DV table."""
        rows = []

        for line in table_text.split('\n'):
            # Must contain pipe separators
            if '|' not in line:
                continue
            # Skip header lines (contain 'freq', 'obs.', 'calc.', 'DV|IV')
            if any(kw in line for kw in ['freq', 'obs.', 'calc.', 'DV|IV', 'rule', 'Test Data']):
                # But allow lines that have numbers before the first pipe (data rows
                # that happen to be in a header-like position)
                parts = line.split('|')
                if len(parts) < 3:
                    continue
                # Check if first part has the word 'freq' — that's definitely a header
                if 'freq' in parts[1] or 'obs.' in parts[1]:
                    continue

            parts = line.split('|')
            if len(parts) < 3:
                continue

            # Data section: freq, DV=0%, DV=1%
            data_vals = parts[1].split()
            if len(data_vals) < 3:
                continue

            try:
                freq = float(data_vals[0])
                if freq == 0:
                    continue

                obs_dv0 = float(data_vals[1])
                obs_dv1 = float(data_vals[2])
            except (ValueError, IndexError):
                continue

            # Model section: calc_dv0, calc_dv1, rule, #correct, %correct, p(rule), p(margin)
            model_vals = parts[2].split()
            if len(model_vals) < 5:
                continue

            try:
                row = {
                    'iv_state': parts[0].strip(),
                    'freq': freq,
                    'obs_dv0': obs_dv0,
                    'obs_dv1': obs_dv1,
                    'calc_dv0': float(model_vals[0]),
                    'calc_dv1': float(model_vals[1]),
                    'rule': int(model_vals[2]),
                    'n_correct': float(model_vals[3]),
                    'pct_correct': float(model_vals[4]),
                    'p_rule': float(model_vals[5]) if len(model_vals) > 5 else None,
                    'p_margin': float(model_vals[6]) if len(model_vals) > 6 else None,
                }
                rows.append(row)
            except (ValueError, IndexError):
                continue

        # Remove the summary row (last row typically has totals)
        # The summary row usually has freq == sum of all other freqs
        if len(rows) > 1:
            total_freq = sum(r['freq'] for r in rows[:-1])
            if rows[-1]['freq'] > 0 and abs(rows[-1]['freq'] - total_freq) < 1.0:
                rows = rows[:-1]

        return rows

    def _extract_confusion_matrices(self) -> List[Dict]:
        """Extract confusion matrix statistics.

        If cm_dict was provided (from get_confusion_matrix()), uses that directly.
        Otherwise falls back to parsing the text output.

        The cm_dict uses sklearn-compatible keys:
            train_tn, train_fp, train_fn, train_tp,
            train_accuracy, train_sensitivity, train_specificity,
            train_precision, train_npv, train_f1_score,
            test_tn, test_fp, ... (if has_test_data)
        """
        matrices = []

        # Preferred path: use the structured dict from get_confusion_matrix()
        if self.cm_dict and self.cm_dict.get('has_values', False):
            return self._cm_from_dict(self.cm_dict)

        # Fallback: parse text output
        cm_blocks = re.split(r'(?=Confusion Matrix for Fit Rule)', self.report)

        for block in cm_blocks:
            if 'Confusion Matrix for Fit Rule' not in block:
                continue

            type_match = re.search(r'Confusion Matrix for Fit Rule \((Training|Test)\)', block)
            if not type_match:
                continue
            dataset_type = type_match.group(1)

            block_start = self.report.find(block[:80])
            if block_start > 0:
                prev_text = self.report[max(0, block_start - 500):block_start]
                model_match = re.search(r'(?:Model|Relation)\s+(IV:\S+|[A-Z][A-Za-z:]+)', prev_text)
                if model_match:
                    relation = f"{model_match.group(1)} ({dataset_type})"
                else:
                    relation = f"Model ({dataset_type})"
            else:
                relation = f"Model ({dataset_type})"

            cm = self._extract_single_cm(block, relation)
            if cm:
                matrices.append(cm)

        return matrices

    def _cm_from_dict(self, cm: Dict) -> List[Dict]:
        """Build confusion matrix insights from a get_confusion_matrix() dict.

        Keys follow the sklearn-compatible pattern:
            train_tn, train_fp, train_fn, train_tp, train_accuracy, etc.
        """
        matrices = []

        # Determine model name for the label
        # Note: self.sections may not be fully built yet (called during _parse_sections)
        model_name = 'Model'
        match = re.search(r'^\s*Model\s+(IV:\S+|[A-Z][A-Za-z:]+)', self.report, re.MULTILINE)
        if match:
            model_name = match.group(1).strip()

        # Training data (always present if has_values)
        matrices.append({
            'relation': f"{model_name} (Training)",
            'TN': cm.get('train_tn', 0),
            'FP': cm.get('train_fp', 0),
            'FN': cm.get('train_fn', 0),
            'TP': cm.get('train_tp', 0),
            'pct_correct': cm.get('train_accuracy', 0),
            'sensitivity': cm.get('train_sensitivity', 0),
            'specificity': cm.get('train_specificity', 0),
            'precision': cm.get('train_precision', 0),
            'npv': cm.get('train_npv', 0),
            'f1': cm.get('train_f1_score', 0),
        })

        # Test data (if available)
        if cm.get('has_test_data', False):
            test_total = cm.get('test_tn', 0) + cm.get('test_fp', 0) + \
                         cm.get('test_fn', 0) + cm.get('test_tp', 0)
            matrices.append({
                'relation': f"{model_name} (Test)",
                'TN': cm.get('test_tn', 0),
                'FP': cm.get('test_fp', 0),
                'FN': cm.get('test_fn', 0),
                'TP': cm.get('test_tp', 0),
                'pct_correct': cm.get('test_accuracy', 0),
                'sensitivity': cm.get('test_sensitivity', 0),
                'specificity': cm.get('test_specificity', 0),
                'precision': cm.get('test_precision', 0),
                'npv': cm.get('test_npv', 0),
                'f1': cm.get('test_f1_score', 0),
            })

        return matrices

    def _extract_single_cm(self, section: str, relation: str) -> Optional[Dict]:
        """Extract metrics from a single confusion matrix block."""
        # Extract TP, TN, FP, FN - text format: "TN =     198"
        tn_match = re.search(r'TN\s*=\s*(\d+)', section)
        fp_match = re.search(r'FP\s*=\s*(\d+)', section)
        fn_match = re.search(r'FN\s*=\s*(\d+)', section)
        tp_match = re.search(r'TP\s*=\s*(\d+)', section)

        if not all([tn_match, fp_match, fn_match, tp_match]):
            return None

        tn = float(tn_match.group(1))
        fp = float(fp_match.group(1))
        fn = float(fn_match.group(1))
        tp = float(tp_match.group(1))
        total = tn + fp + fn + tp

        # Extract additional statistics
        # Format: "   Accuracy (correct/total)        0.684"
        def extract_stat(name_pattern):
            m = re.search(name_pattern + r'\s+([\d.]+)', section)
            return float(m.group(1)) if m else 0.0

        accuracy = extract_stat(r'Accuracy \(correct/total\)')
        sensitivity = extract_stat(r'Sensitivity \(Recall\)')
        specificity = extract_stat(r'Specificity')
        precision = extract_stat(r'Precision')
        npv = extract_stat(r'Negative Predictive Value')
        f1 = extract_stat(r'F1 Score')

        # Calculate pct_correct from the values if accuracy was found
        pct_correct = accuracy if accuracy > 0 else (tp + tn) / total if total > 0 else 0

        return {
            'relation': relation,
            'TN': tn,
            'FP': fp,
            'FN': fn,
            'TP': tp,
            'pct_correct': pct_correct,
            'sensitivity': sensitivity,
            'specificity': specificity,
            'precision': precision,
            'npv': npv,
            'f1': f1,
        }

    def analyze(self) -> Dict:
        """Run all analyses and return findings as a structured dict."""
        findings = {
            'overview': self._analyze_overview(),
            'model_quality': self._analyze_model_quality(),
            'conditional_patterns': self._analyze_conditional_patterns(),
            'confusion_insights': self._analyze_confusion_matrices(),
            'recommendations': []
        }
        findings['recommendations'] = self._generate_recommendations(findings)
        return findings

    def _analyze_overview(self) -> Dict:
        """Analyze overall model characteristics"""
        header = self.sections['header']
        model = self.sections['model_info']

        insights = {}

        sample_size = header.get('sample_size')
        if sample_size:
            insights['sample_info'] = f"Sample size: {sample_size}"
        if header.get('has_test_data'):
            insights['test_data'] = "Test data present for validation"

        num_ivs = model.get('num_ivs')
        if num_ivs:
            insights['complexity'] = f"{num_ivs} independent variables"

        model_name = model.get('model_name')
        if model_name:
            insights['model'] = f"Model: {model_name}"

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

        lr_bottom = lr.get('lr_bottom')
        lr_bottom_p = lr.get('lr_bottom_p')
        if lr_bottom is not None and lr_bottom_p is not None:
            if lr_bottom_p < P_HIGHLY_SIGNIFICANT:
                insights['vs_independence'] = f"Model significantly better than independence (LR={lr_bottom:.2f}, p<{P_HIGHLY_SIGNIFICANT})"
            elif lr_bottom_p < P_SIGNIFICANT:
                insights['vs_independence'] = f"Model better than independence (LR={lr_bottom:.2f}, p={lr_bottom_p:.3f})"
            else:
                insights['vs_independence'] = f"Model not significantly better than independence (LR={lr_bottom:.2f}, p={lr_bottom_p:.3f})"

        lr_top_p = lr.get('lr_top_p')
        if lr_top_p is not None:
            if lr_top_p > P_SIGNIFICANT:
                insights['vs_saturated'] = "Model fits data well (not significantly worse than saturated model)"
            else:
                insights['vs_saturated'] = f"Model fit is significantly worse than saturated (p={lr_top_p:.3f})"

        return insights

    def _analyze_conditional_patterns(self) -> List[Dict]:
        """Find interesting patterns in conditional tables"""
        patterns = []

        for table in self.sections['conditional_tables']:
            relation = table['relation']
            rows = table['rows']

            if not rows:
                continue

            high_accuracy = [r for r in rows if r['pct_correct'] >= HIGH_ACCURACY_THRESHOLD and r['freq'] >= SPARSE_DATA_THRESHOLD]
            if high_accuracy:
                patterns.append({
                    'type': 'high_accuracy',
                    'relation': relation,
                    'count': len(high_accuracy),
                    'details': f"{len(high_accuracy)} state(s) with >={HIGH_ACCURACY_THRESHOLD}% prediction accuracy",
                    'examples': [f"{r['iv_state']}: {r['pct_correct']:.1f}% correct (n={r['freq']:.0f})"
                               for r in sorted(high_accuracy, key=lambda x: -x['pct_correct'])[:10]]
                })

            low_accuracy = [r for r in rows if r['pct_correct'] < LOW_ACCURACY_THRESHOLD and r['freq'] >= MIN_FREQ_FOR_LOW_ACCURACY]
            if low_accuracy:
                patterns.append({
                    'type': 'low_accuracy',
                    'relation': relation,
                    'count': len(low_accuracy),
                    'details': f"{len(low_accuracy)} state(s) with <{LOW_ACCURACY_THRESHOLD}% accuracy (n>={MIN_FREQ_FOR_LOW_ACCURACY})",
                    'examples': [f"{r['iv_state']}: {r['pct_correct']:.1f}% correct (n={r['freq']:.0f})"
                               for r in sorted(low_accuracy, key=lambda x: x['pct_correct'])[:10]]
                })

            sparse_rows = [r for r in rows if r['freq'] < SPARSE_DATA_THRESHOLD]
            if sparse_rows:
                patterns.append({
                    'type': 'sparse_data',
                    'relation': relation,
                    'count': len(sparse_rows),
                    'details': f"{len(sparse_rows)} state(s) with <{SPARSE_DATA_THRESHOLD} samples (predictions unreliable)",
                })

            sig_rules = [r for r in rows if r.get('p_rule') is not None and r['p_rule'] < SIGNIFICANCE_THRESHOLD and r['freq'] >= MIN_FREQ_FOR_SIGNIFICANCE]
            if sig_rules:
                patterns.append({
                    'type': 'significant_rules',
                    'relation': relation,
                    'count': len(sig_rules),
                    'details': f"{len(sig_rules)} state(s) with statistically significant classification rules",
                    'examples': [f"{r['iv_state']}: p={r['p_rule']:.4f}"
                               for r in sorted(sig_rules, key=lambda x: x['p_rule'])[:10]]
                })

            large_diff = []
            for r in rows:
                if r['freq'] >= MIN_FREQ_FOR_MISMATCH:
                    diff = abs(r['obs_dv1'] - r['calc_dv1'])
                    if diff > LARGE_MISMATCH_THRESHOLD:
                        large_diff.append((r, diff))

            if large_diff:
                patterns.append({
                    'type': 'prediction_mismatch',
                    'relation': relation,
                    'count': len(large_diff),
                    'details': f"{len(large_diff)} state(s) with >{LARGE_MISMATCH_THRESHOLD}% difference between observed and predicted",
                    'examples': [f"{r['iv_state']}: obs={r['obs_dv1']:.1f}% vs pred={r['calc_dv1']:.1f}%"
                               for r, diff in sorted(large_diff, key=lambda x: -x[1])[:10]]
                })

        return patterns

    def _analyze_confusion_matrices(self) -> List[Dict]:
        """Analyze confusion matrix performance"""
        insights = []

        for cm in self.sections['confusion_matrices']:
            relation = cm['relation']

            pct = cm['pct_correct'] * 100
            if pct >= ACCURACY_EXCELLENT:
                acc_level = "Excellent"
            elif pct >= ACCURACY_GOOD:
                acc_level = "Good"
            elif pct >= ACCURACY_MODERATE:
                acc_level = "Moderate"
            else:
                acc_level = "Poor"

            insight = {
                'relation': relation,
                'accuracy': f"{acc_level} overall accuracy: {pct:.1f}%",
                'metrics': {}
            }

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

            total_positive = cm['TP'] + cm['FN']
            total_negative = cm['TN'] + cm['FP']
            total = total_positive + total_negative

            if total > 0:
                pos_pct = (total_positive / total) * 100
                neg_pct = (total_negative / total) * 100

                if abs(pos_pct - 50) > CLASS_IMBALANCE_THRESHOLD:
                    insight['balance'] = f"Imbalanced classes: {neg_pct:.1f}% negative, {pos_pct:.1f}% positive"
                else:
                    insight['balance'] = f"Balanced classes: {neg_pct:.1f}% negative, {pos_pct:.1f}% positive"

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

        overview = findings['overview']
        if 'info_capture' in overview:
            if 'Low' in overview['info_capture']:
                recs.append("Consider adding more IVs or interactions to capture more information")
            elif 'High' in overview['info_capture']:
                recs.append("Model captures substantial complexity - verify against overfitting")

        quality = findings['model_quality']
        if 'vs_independence' in quality and 'not significantly' in quality['vs_independence']:
            recs.append("Model not significantly better than independence - consider simpler model or different variables")

        # Train/test comparison
        cm_insights = findings['confusion_insights']
        train_cms = [c for c in cm_insights if 'Training' in c['relation']]
        test_cms = [c for c in cm_insights if 'Test' in c['relation']]
        if train_cms and test_cms:
            train_acc = float(re.search(r'([\d.]+)%', train_cms[0]['accuracy']).group(1))
            test_acc = float(re.search(r'([\d.]+)%', test_cms[0]['accuracy']).group(1))
            gap = train_acc - test_acc
            if gap > 15:
                recs.append(f"Large train/test accuracy gap ({gap:.1f}%) suggests overfitting - consider a simpler model")
            elif gap > 5:
                recs.append(f"Moderate train/test accuracy gap ({gap:.1f}%) - monitor for overfitting")
            elif gap <= 2:
                recs.append(f"Train/test accuracy gap is small ({gap:.1f}%) - model generalizes well")

        for cm_insight in cm_insights:
            if 'concerns' in cm_insight:
                rel = cm_insight['relation']
                for concern in cm_insight['concerns']:
                    recs.append(f"{rel}: {concern}")

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

        print("\n  OVERVIEW")
        print("-" * 80)
        for key, value in findings['overview'].items():
            print(f"  {value}")

        print("\n  MODEL QUALITY")
        print("-" * 80)
        if findings['model_quality']:
            for key, value in findings['model_quality'].items():
                print(f"  {value}")
        else:
            print("  No LR statistics extracted")

        print("\n  CONDITIONAL DV PATTERNS")
        print("-" * 80)
        if findings['conditional_patterns']:
            current_relation = None
            for pattern in findings['conditional_patterns']:
                if pattern['relation'] != current_relation:
                    current_relation = pattern['relation']
                    print(f"\n  {current_relation}:")

                print(f"    * {pattern['details']}")
                if 'examples' in pattern:
                    for ex in pattern['examples']:
                        print(f"      - {ex}")
        else:
            print("  No notable patterns found")

        print("\n  CONFUSION MATRIX PERFORMANCE")
        print("-" * 80)
        if findings['confusion_insights']:
            for insight in findings['confusion_insights']:
                print(f"\n  {insight['relation']}:")
                print(f"    * {insight['accuracy']}")
                print(f"    * {insight['best']}")
                print(f"    * {insight['worst']}")
                if 'balance' in insight:
                    print(f"    * {insight['balance']}")
                if 'concerns' in insight:
                    for concern in insight['concerns']:
                        print(f"    !  {concern}")
        else:
            print("  No confusion matrices found")

        if findings['recommendations']:
            print("\n  RECOMMENDATIONS")
            print("-" * 80)
            for i, rec in enumerate(findings['recommendations'], 1):
                print(f"  {i}. {rec}")

        print("\n" + "=" * 80)


# Standalone usage
if __name__ == "__main__":
    import sys

    input_file = FIT_REPORT_FILE

    if len(sys.argv) >= 2:
        input_file = sys.argv[1]

    if not input_file:
        print("Error: No input file specified!")
        print()
        print("Either:")
        print("  1. Edit the FIT_REPORT_FILE variable at the top of this script")
        print("  2. Run with: python -m pyoccam.analyze_fit <fit_report_file>")
        sys.exit(1)

    try:
        with open(input_file, 'r') as f:
            report = f.read()
    except FileNotFoundError:
        print(f"Error: File not found: {input_file}")
        sys.exit(1)
    except Exception as e:
        print(f"Error reading file: {e}")
        sys.exit(1)

    analyzer = FitReportAnalyzer(report)

    if OUTPUT_FILE:
        try:
            import io
            import contextlib

            string_buffer = io.StringIO()
            with contextlib.redirect_stdout(string_buffer):
                analyzer.print_summary()

            with open(OUTPUT_FILE, 'w') as f:
                f.write(string_buffer.getvalue())

            print(f"Analysis complete! Output written to: {OUTPUT_FILE}")
            print(f"Analyzed: {input_file}")
        except Exception as e:
            print(f"Error writing to output file: {e}")
            print("\nPrinting to stdout instead:\n")
            analyzer.print_summary()
    else:
        analyzer.print_summary()
