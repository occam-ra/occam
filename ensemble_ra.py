"""
Ensemble RA: Mining High-Confidence Prediction Rules from Specialist Models

This module implements a two-tier prediction approach for Reconstructability Analysis:

WORKFLOW:
1. Run search → Get all models with their accuracy and coverage stats
2. Select BASE MODEL → Best by BIC (balanced, high coverage)
3. Find SPECIALISTS → Models with higher accuracy but lower coverage (overfit but precise)
4. Generate fit reports for specialists (these weren't fitted because they "lost" on BIC)
5. Mine high-confidence rules from those fits
6. Two-tier prediction: if specific rule matches → use it; else → fall back to base model

KEY INSIGHT:
Models that lose on BIC/AIC often do so because they're "overfit" (complexity penalty > accuracy gain).
But that overfitting means they've memorized specific state combinations perfectly.
We extract those specific predictions while using the conservative BIC winner as fallback.

Usage:
    import pyoccam
    from ensemble_ra import EnsembleRAClassifier
    
    # Load data and run search
    data = pyoccam.load_landslides()
    manager = data.manager
    
    # Create ensemble and configure
    ensemble = EnsembleRAClassifier(manager, dv_name="Z")
    
    # Run the full workflow
    ensemble.run_ensemble_workflow(
        search_type="full-up",
        levels=7,
        width=3,
        min_specialist_accuracy=0.76,  # Must beat base model
        max_specialist_cover=80.0       # Must be selective
    )
    
    # View results
    print(ensemble.get_summary())
    ensemble.export_rules_csv("landslide_rules.csv")
    
STANDALONE USAGE (without PyOccam manager):
    from ensemble_ra import EnsembleRAClassifier
    
    ensemble = EnsembleRAClassifier(dv_name="Z")
    ensemble.configure_thresholds(min_frequency=10, min_confidence=85, min_accuracy=90, max_p_margin=0.05)
    
    # Load existing search results
    ensemble.load_search_results("search_full-up_landslides.txt")
    
    # Mine rules from existing fit report
    ensemble.mine_from_fit_file("fit_IV_ElTwZ_HbZ_LcZ_SlZ_TcZ.txt")
    
    print(ensemble.get_summary())
"""

import re
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path

# Try to import FitReportAnalyzer for parsing (works with comma-separated server output)
try:
    from analyze_fit import FitReportAnalyzer
    HAS_ANALYZER = True
except ImportError:
    HAS_ANALYZER = False


# ============================================================================
# DATA STRUCTURES
# ============================================================================

@dataclass
class SearchModel:
    """A model from the search results."""
    id: int
    name: str
    level: int
    h: float
    ddf: int
    dLR: float
    alpha: float
    pct_dh_dv: float  # %dH(DV)
    daic: float
    dbic: float
    inc_alpha: float
    pct_correct_data: float  # %C(Data)
    pct_cover: float  # %cover
    pct_correct_test: float = 0.0  # %C(Test)
    pct_miss: float = 0.0  # %miss
    is_starred: bool = False  # Has * marker (incremental path significant)
    
    def __repr__(self):
        return f"SearchModel({self.name}, acc={self.pct_correct_data:.1f}%, cover={self.pct_cover:.1f}%)"


@dataclass
class PredictionRule:
    """A single prediction rule extracted from a conditional DV table."""
    
    iv_states: Dict[str, str]  # e.g., {'El': '1', 'Hb': '2', 'Lc': '1'}
    predicted_dv: str          # e.g., '1'
    confidence: float          # calc.q(DV|IV) for predicted state (0-100)
    frequency: float           # sample count
    accuracy: float            # %correct
    p_rule: float              # p-value vs uniform
    p_margin: float            # p-value vs marginal
    source_model: str          # model name this came from
    dv_distribution: Dict[str, float] = field(default_factory=dict)
    
    def is_significant(self, alpha: float = 0.05) -> bool:
        return self.p_margin < alpha
    
    def iv_key(self) -> str:
        """Hashable key for the IV state combination."""
        return "|".join(f"{k}={v}" for k, v in sorted(self.iv_states.items()))
    
    def iv_key_short(self) -> str:
        """Short key using just values in order."""
        return ",".join(str(v) for v in self.iv_states.values())
    
    def __repr__(self):
        iv_str = ",".join(f"{k}={v}" for k, v in self.iv_states.items())
        return f"Rule({iv_str} -> {self.predicted_dv}, n={self.frequency:.0f}, conf={self.confidence:.1f}%)"


@dataclass 
class EnsembleStats:
    """Statistics for the ensemble."""
    base_model: str = ""
    base_model_accuracy: float = 0.0
    base_model_cover: float = 0.0
    n_specialists: int = 0
    specialists: List[str] = field(default_factory=list)
    n_rules_total: int = 0
    n_rules_accepted: int = 0
    total_rule_frequency: float = 0.0


# ============================================================================
# SEARCH OUTPUT PARSER
# ============================================================================

class SearchOutputParser:
    """Parse OCCAM search output to extract model statistics."""
    
    def parse(self, search_output: str) -> Tuple[List[SearchModel], Dict[str, str]]:
        """
        Parse search output.
        
        Returns:
            Tuple of (list of SearchModel, dict of best models by criterion)
        """
        models = []
        best_models = {}
        seen_models = set()  # Deduplicate
        
        lines = search_output.strip().split('\n')
        in_data_section = False
        
        for line in lines:
            line = line.strip()
            
            # Detect header line
            if line.startswith('ID') and 'MODEL' in line and 'Level' in line:
                in_data_section = True
                continue
            
            # Stop at summary section
            if 'Best Model(s)' in line:
                in_data_section = False
            
            # Parse model data line
            if in_data_section and line and (line[0].isdigit() or line[0] == '*'):
                model = self._parse_model_line(line)
                if model and model.name not in seen_models:
                    models.append(model)
                    seen_models.add(model.name)
        
        # Extract best models from summary section
        best_models = self._extract_best_models(search_output)
        
        return models, best_models
    
    def _parse_model_line(self, line: str) -> Optional[SearchModel]:
        """Parse a single model line from search output."""
        try:
            is_starred = '*' in line.split()[0] if line.split() else False
            
            parts = line.split()
            if len(parts) < 10:
                return None
            
            id_str = parts[0].replace('*', '')
            model_id = int(id_str)
            model_name = parts[1]
            numeric_parts = parts[2:]
            
            if len(numeric_parts) < 11:
                return None
            
            return SearchModel(
                id=model_id,
                name=model_name,
                level=int(numeric_parts[0]),
                h=float(numeric_parts[1]),
                ddf=int(numeric_parts[2]),
                dLR=float(numeric_parts[3]),
                alpha=float(numeric_parts[4]),
                pct_dh_dv=float(numeric_parts[5]),
                daic=float(numeric_parts[6]),
                dbic=float(numeric_parts[7]),
                inc_alpha=float(numeric_parts[8]),
                pct_correct_data=float(numeric_parts[9]),
                pct_cover=float(numeric_parts[10]),
                pct_correct_test=float(numeric_parts[11]) if len(numeric_parts) > 11 else 0.0,
                pct_miss=float(numeric_parts[12]) if len(numeric_parts) > 12 else 0.0,
                is_starred=is_starred
            )
        except (ValueError, IndexError):
            return None
    
    def _extract_best_models(self, search_output: str) -> Dict[str, str]:
        """Extract best model names from the summary section."""
        best = {}
        lines = search_output.split('\n')
        current_criterion = None
        
        for line in lines:
            if 'Best Model(s) by dBIC:' in line:
                current_criterion = 'bic'
            elif 'Best Model(s) by dAIC:' in line:
                current_criterion = 'aic'
            elif 'Best Model(s) by Information' in line:
                current_criterion = 'information'
            elif current_criterion and 'IV:' in line:
                match = re.search(r'(IV:[A-Za-z:]+)', line)
                if match:
                    best[current_criterion] = match.group(1)
                current_criterion = None
        
        return best


# ============================================================================
# CONDITIONAL DV TABLE PARSER
# ============================================================================

class ConditionalDVParser:
    """Parse the Conditional DV table from OCCAM fit reports."""
    
    def __init__(self, dv_name: str = "Z"):
        self.dv_name = dv_name
        
    def parse_fit_report(self, fit_report: str, model_name: str) -> List[PredictionRule]:
        """Extract all prediction rules from a fit report's conditional DV table."""
        
        # Try FitReportAnalyzer first (works with comma-separated format from server)
        if HAS_ANALYZER:
            rules = self._parse_with_analyzer(fit_report, model_name)
            if rules:
                return rules
        
        # Fall back to direct parsing (works with space-separated format from local runs)
        return self._parse_direct(fit_report, model_name)
    
    def _parse_with_analyzer(self, fit_report: str, model_name: str) -> List[PredictionRule]:
        """Use FitReportAnalyzer for parsing."""
        analyzer = FitReportAnalyzer(fit_report)
        rules = []
        
        for table in analyzer.sections['conditional_tables']:
            iv_names = self._extract_iv_names(fit_report, model_name)
            
            for row in table['rows']:
                iv_state_str = row.get('iv_state', '')
                iv_values = [v.strip() for v in iv_state_str.split(',') if v.strip()]
                
                if len(iv_names) != len(iv_values):
                    iv_names = [f"V{i+1}" for i in range(len(iv_values))]
                
                iv_states = dict(zip(iv_names, iv_values))
                
                rule_state = str(row.get('rule', 0))
                confidence = row.get('calc_dv0', 0.0) if rule_state == '0' else row.get('calc_dv1', 0.0)
                
                rule = PredictionRule(
                    iv_states=iv_states,
                    predicted_dv=rule_state,
                    confidence=confidence,
                    frequency=row.get('freq', 0.0),
                    accuracy=row.get('pct_correct', 0.0),
                    p_rule=row.get('p_rule', 1.0) or 1.0,
                    p_margin=row.get('p_margin', 1.0) or 1.0,
                    source_model=model_name,
                    dv_distribution={'0': row.get('calc_dv0', 0.0), '1': row.get('calc_dv1', 0.0)}
                )
                rules.append(rule)
        
        return rules
    
    def _extract_iv_names(self, fit_report: str, model_name: str) -> List[str]:
        """Extract IV variable names from fit report header."""
        for line in fit_report.split('\n'):
            if 'freq' in line and self.dv_name in line and '|' in line:
                parts = line.split('|')
                if parts:
                    iv_part = parts[0].strip()
                    iv_names = re.split(r'\s{2,}|\t', iv_part)
                    iv_names = [v.strip() for v in iv_names if v.strip()]
                    return iv_names
        return []
    
    def _parse_direct(self, fit_report: str, model_name: str) -> List[PredictionRule]:
        """Direct parsing for space-separated format (from local OCCAM runs)."""
        rules = []
        lines = fit_report.split('\n')
        
        in_conditional_table = False
        iv_names = []
        dv_states = []
        
        for line in lines:
            if "Conditional DV" in line and "Model" in line:
                in_conditional_table = True
                continue
            
            if in_conditional_table and line.startswith("IV order:"):
                continue
            
            if in_conditional_table and ("obs. p(DV|IV)" in line or "calc. q(DV|IV)" in line):
                continue
            
            # Parse column header line
            if in_conditional_table and "freq" in line and self.dv_name in line and "|" in line:
                parts = line.split("|")
                if parts:
                    iv_part = parts[0].strip()
                    iv_names = re.split(r'\s{2,}|\t', iv_part)
                    iv_names = [v.strip() for v in iv_names if v.strip()]
                
                dv_states = re.findall(rf"{self.dv_name}=([^,\s|]+)", line)
                seen = set()
                dv_states = [x for x in dv_states if not (x in seen or seen.add(x))]
                continue
            
            # End of table
            if in_conditional_table and ("Confusion Matrix" in line or 
                                         "Performance on" in line or
                                         line.startswith("-----")):
                in_conditional_table = False
                continue
            
            # Parse data row
            if in_conditional_table and iv_names and dv_states:
                rule = self._parse_data_row(line, iv_names, dv_states, model_name)
                if rule:
                    rules.append(rule)
        
        return rules
    
    def _parse_data_row(self, line: str, iv_names: List[str], 
                        dv_states: List[str], model_name: str) -> Optional[PredictionRule]:
        """Parse a single data row from the conditional DV table."""
        
        line = line.strip()
        if not line or "|" not in line:
            return None
        
        if "freq" in line.lower() or "obs." in line.lower():
            return None
        
        parts = line.split("|")
        if len(parts) < 3:
            return None
        
        try:
            # Parse IV states
            iv_part = parts[0].strip()
            iv_values = re.split(r'\s{2,}|\t', iv_part)
            iv_values = [v.strip() for v in iv_values if v.strip()]
            
            if len(iv_values) != len(iv_names):
                return None
            
            if not iv_values[0][0].isdigit() and not iv_values[0].startswith('*'):
                return None
            
            iv_states = dict(zip(iv_names, iv_values))
            
            # Parse Data section
            data_part = parts[1].strip()
            data_values = re.split(r'\s{2,}|\t|,', data_part)
            data_values = [v.strip() for v in data_values if v.strip()]
            
            if len(data_values) < 1 + len(dv_states):
                return None
            
            frequency = float(data_values[0])
            if frequency <= 0:
                return None
            
            # Parse Model section
            model_part = parts[2].strip()
            model_values = re.split(r'\s{2,}|\t|,', model_part)
            model_values = [v.strip() for v in model_values if v.strip()]
            
            if len(model_values) < len(dv_states) + 5:
                return None
            
            calc_probs = {}
            for j, state in enumerate(dv_states):
                calc_probs[state] = float(model_values[j])
            
            offset = len(dv_states)
            rule_str = model_values[offset].strip()
            pct_correct = float(model_values[offset + 2])
            p_rule = float(model_values[offset + 3])
            p_margin = float(model_values[offset + 4])
            
            predicted_dv = rule_str.lstrip('*')
            confidence = calc_probs.get(predicted_dv, 0.0)
            
            return PredictionRule(
                iv_states=iv_states,
                predicted_dv=predicted_dv,
                confidence=confidence,
                frequency=frequency,
                accuracy=pct_correct,
                p_rule=p_rule,
                p_margin=p_margin,
                source_model=model_name,
                dv_distribution=calc_probs
            )
            
        except (ValueError, IndexError):
            return None


# ============================================================================
# ENSEMBLE RA CLASSIFIER
# ============================================================================

class EnsembleRAClassifier:
    """
    Two-tier ensemble classifier that mines rules from specialist models.
    
    Workflow:
    1. Run search to get all models with accuracy/coverage stats
    2. Select base model (best BIC - balanced, high coverage)
    3. Identify specialists (high accuracy, low coverage - overfit but precise)
    4. Generate fit reports for specialists
    5. Mine high-confidence rules from those fits
    6. Prediction: specific rule match → use it; else → base model fallback
    """
    
    def __init__(self, manager=None, dv_name: str = "Z"):
        """
        Args:
            manager: PyOccam VBMManager instance
            dv_name: Name of the dependent variable
        """
        self.manager = manager
        self.dv_name = dv_name
        self.search_parser = SearchOutputParser()
        self.fit_parser = ConditionalDVParser(dv_name)
        
        # Search results
        self.search_models: List[SearchModel] = []
        self.best_models: Dict[str, str] = {}
        
        # Base model (fallback)
        self.base_model: Optional[str] = None
        self.base_model_rules: Dict[str, PredictionRule] = {}
        
        # Specialist rules (high-confidence, specific states)
        self.rules: Dict[str, PredictionRule] = {}
        
        # Configuration thresholds for rule acceptance
        self.min_frequency = 5.0
        self.min_confidence = 80.0
        self.min_accuracy = 85.0
        self.max_p_margin = 0.05
        
        # Statistics
        self.stats = EnsembleStats()
    
    def configure_thresholds(self,
                            min_frequency: float = 5.0,
                            min_confidence: float = 80.0,
                            min_accuracy: float = 85.0,
                            max_p_margin: float = 0.05):
        """Configure thresholds for accepting rules."""
        self.min_frequency = min_frequency
        self.min_confidence = min_confidence
        self.min_accuracy = min_accuracy
        self.max_p_margin = max_p_margin
    
    def run_ensemble_workflow(self,
                             search_type: str = "full-up",
                             levels: int = 7,
                             width: int = 3,
                             min_specialist_accuracy: float = 0.75,
                             max_specialist_cover: float = 80.0,
                             target_state: str = "0") -> None:
        """
        Run the complete ensemble workflow with PyOccam manager.
        
        Args:
            search_type: Type of search to run
            levels: Number of search levels
            width: Beam width
            min_specialist_accuracy: Minimum %C(Data) for a specialist model
            max_specialist_cover: Maximum %cover for a specialist model (selectivity)
            target_state: Target state for confusion matrix
        """
        if self.manager is None:
            raise ValueError("Manager required for ensemble workflow")
        
        # Step 1: Run search
        print(f"Step 1: Running {search_type} search (levels={levels}, width={width})...")
        search_output = self.manager.generate_search_report(search_type, levels, width)
        
        # Step 2: Parse search results
        print("Step 2: Parsing search results...")
        self.search_models, self.best_models = self.search_parser.parse(search_output)
        print(f"   Found {len(self.search_models)} models")
        
        # Step 3: Select base model (best BIC)
        self.base_model = self.best_models.get('bic', self.best_models.get('aic', ''))
        if not self.base_model and self.search_models:
            self.base_model = min(self.search_models, key=lambda m: m.dbic).name
        
        base_model_data = next((m for m in self.search_models if m.name == self.base_model), None)
        if base_model_data:
            self.stats.base_model = self.base_model
            self.stats.base_model_accuracy = base_model_data.pct_correct_data
            self.stats.base_model_cover = base_model_data.pct_cover
        
        print(f"Step 3: Base model = {self.base_model}")
        if base_model_data:
            print(f"   Accuracy: {base_model_data.pct_correct_data:.1f}%, Cover: {base_model_data.pct_cover:.1f}%")
        
        # Step 4: Identify specialist models
        specialists = self._find_specialists(min_specialist_accuracy, max_specialist_cover)
        self.stats.n_specialists = len(specialists)
        self.stats.specialists = [s.name for s in specialists]
        
        print(f"Step 4: Found {len(specialists)} specialist models to mine")
        for s in specialists:
            print(f"   {s.name}: acc={s.pct_correct_data:.1f}%, cover={s.pct_cover:.1f}%")
        
        # Step 5: Generate fit reports and mine rules
        print("Step 5: Mining rules from specialists...")
        total_rules = 0
        for specialist in specialists:
            try:
                fit_report = self.manager.generate_fit_report(specialist.name, target_state=target_state)
                n_rules = self._mine_rules_from_fit(fit_report, specialist.name)
                if n_rules > 0:
                    print(f"   {specialist.name}: +{n_rules} rules")
                total_rules += n_rules
            except Exception as e:
                print(f"   {specialist.name}: Error - {e}")
        
        self.stats.n_rules_total = total_rules
        self.stats.n_rules_accepted = len(self.rules)
        
        # Step 6: Load base model for fallback predictions
        print(f"Step 6: Loading base model rules for fallback...")
        try:
            base_fit = self.manager.generate_fit_report(self.base_model, target_state=target_state)
            base_rules = self.fit_parser.parse_fit_report(base_fit, self.base_model)
            self.base_model_rules = {r.iv_key(): r for r in base_rules}
            print(f"   Base model has {len(self.base_model_rules)} state combinations")
        except Exception as e:
            print(f"   Could not load base model: {e}")
        
        print("\nWorkflow complete!")
        print(f"   Total specialist rules: {len(self.rules)}")
    
    def _find_specialists(self, min_accuracy: float, max_cover: float) -> List[SearchModel]:
        """Find specialist models: high accuracy but low coverage."""
        specialists = []
        
        for model in self.search_models:
            if model.name == self.base_model:
                continue
            if model.name == 'IV:Z' or model.level == 0:
                continue
            
            if (model.pct_correct_data >= min_accuracy * 100 and 
                model.pct_cover <= max_cover):
                specialists.append(model)
        
        specialists.sort(key=lambda m: m.pct_correct_data, reverse=True)
        return specialists
    
    def _mine_rules_from_fit(self, fit_report: str, model_name: str) -> int:
        """Extract high-confidence rules from a fit report."""
        all_rules = self.fit_parser.parse_fit_report(fit_report, model_name)
        n_added = 0
        
        for rule in all_rules:
            if self._accept_rule(rule):
                key = rule.iv_key()
                if key not in self.rules or rule.confidence > self.rules[key].confidence:
                    self.rules[key] = rule
                    n_added += 1
        
        return n_added
    
    def _accept_rule(self, rule: PredictionRule) -> bool:
        """Check if a rule meets acceptance criteria."""
        return (rule.frequency >= self.min_frequency and
                rule.confidence >= self.min_confidence and
                rule.accuracy >= self.min_accuracy and
                rule.p_margin <= self.max_p_margin)
    
    def predict(self, iv_states: Dict[str, str]) -> Tuple[str, str, float]:
        """
        Make a prediction for given IV states.
        
        Returns:
            Tuple of (predicted_dv, source, confidence)
            where source is "specialist" or "base"
        """
        key = "|".join(f"{k}={v}" for k, v in sorted(iv_states.items()))
        
        if key in self.rules:
            rule = self.rules[key]
            return rule.predicted_dv, "specialist", rule.confidence
        
        if key in self.base_model_rules:
            rule = self.base_model_rules[key]
            return rule.predicted_dv, "base", rule.confidence
        
        return "?", "unknown", 0.0
    
    def get_rules(self, sort_by: str = "confidence") -> List[PredictionRule]:
        """Get all accepted specialist rules."""
        rules = list(self.rules.values())
        
        sort_keys = {
            "confidence": lambda r: r.confidence,
            "frequency": lambda r: r.frequency,
            "accuracy": lambda r: r.accuracy,
            "significance": lambda r: -r.p_margin  # Lower p is better
        }
        rules.sort(key=sort_keys.get(sort_by, sort_keys["confidence"]), reverse=True)
        return rules
    
    def get_summary(self, top_n: int = 25) -> str:
        """Generate a human-readable summary."""
        lines = [
            "=" * 80,
            "ENSEMBLE RA CLASSIFIER SUMMARY",
            "=" * 80,
            "",
            "BASE MODEL (Fallback):",
            f"  {self.stats.base_model}",
            f"  Accuracy: {self.stats.base_model_accuracy:.1f}%",
            f"  Coverage: {self.stats.base_model_cover:.1f}%",
            "",
            f"SPECIALISTS MINED: {self.stats.n_specialists}",
        ]
        for s in self.stats.specialists[:5]:
            lines.append(f"  - {s}")
        if len(self.stats.specialists) > 5:
            lines.append(f"  ... and {len(self.stats.specialists) - 5} more")
        
        lines.extend([
            "",
            "RULE THRESHOLDS:",
            f"  min_frequency: {self.min_frequency}",
            f"  min_confidence: {self.min_confidence}%",
            f"  min_accuracy: {self.min_accuracy}%",
            f"  max_p_margin: {self.max_p_margin}",
            "",
        ])
        
        total_freq = sum(r.frequency for r in self.rules.values())
        lines.append(f"RULES ACCEPTED: {len(self.rules)} (covering {total_freq:.0f} samples)")
        lines.extend([
            "",
            f"TOP {min(top_n, len(self.rules))} RULES BY FREQUENCY:",
            "-" * 80,
        ])
        
        for i, rule in enumerate(self.get_rules(sort_by="frequency")[:top_n], 1):
            iv_str = ",".join(f"{k}={v}" for k, v in rule.iv_states.items())
            lines.append(
                f"{i:3d}. {iv_str} -> {self.dv_name}={rule.predicted_dv}  "
                f"[n={rule.frequency:.0f}, conf={rule.confidence:.1f}%, "
                f"acc={rule.accuracy:.0f}%, p={rule.p_margin:.4f}]"
            )
        
        return "\n".join(lines)
    
    def export_rules_csv(self, filepath: str) -> None:
        """Export rules to CSV."""
        lines = ["iv_states,predicted_dv,confidence,frequency,accuracy,p_margin,source_model"]
        
        for rule in self.get_rules(sort_by="frequency"):
            iv_str = "|".join(f"{k}={v}" for k, v in sorted(rule.iv_states.items()))
            lines.append(
                f'"{iv_str}",{rule.predicted_dv},{rule.confidence:.2f},'
                f'{rule.frequency:.0f},{rule.accuracy:.1f},{rule.p_margin:.4f},"{rule.source_model}"'
            )
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write("\n".join(lines))
        print(f"Exported {len(self.rules)} rules to {filepath}")
    
    # =========================================================================
    # STANDALONE METHODS (work without manager, on existing files)
    # =========================================================================
    
    def load_search_results(self, filepath: str) -> None:
        """Load search results from a file."""
        with open(filepath, 'r') as f:
            search_output = f.read()
        self.search_models, self.best_models = self.search_parser.parse(search_output)
        print(f"Loaded {len(self.search_models)} models from {filepath}")
    
    def mine_from_fit_file(self, filepath: str, model_name: Optional[str] = None) -> int:
        """Mine rules from an existing fit report file."""
        with open(filepath, 'r') as f:
            fit_report = f.read()
        
        if model_name is None:
            model_name = Path(filepath).stem
        
        return self._mine_rules_from_fit(fit_report, model_name)


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

def sample_size_heuristic(n: int) -> float:
    """Calculate minimum frequency threshold based on sample size."""
    import math
    return max(5.0, math.sqrt(n))


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        filepath = sys.argv[1]
        
        if 'search' in filepath.lower():
            print(f"Parsing search results: {filepath}")
            ensemble = EnsembleRAClassifier()
            ensemble.load_search_results(filepath)
            
            print(f"\nFound {len(ensemble.search_models)} models")
            print(f"Best by BIC: {ensemble.best_models.get('bic', 'N/A')}")
            print(f"Best by AIC: {ensemble.best_models.get('aic', 'N/A')}")
            
            print("\nTop 10 models by accuracy:")
            for m in sorted(ensemble.search_models, key=lambda x: x.pct_correct_data, reverse=True)[:10]:
                print(f"  {m.name}: acc={m.pct_correct_data:.1f}%, cover={m.pct_cover:.1f}%")
        
        elif 'fit' in filepath.lower():
            print(f"Mining rules from fit report: {filepath}")
            ensemble = EnsembleRAClassifier()
            ensemble.configure_thresholds(
                min_frequency=10,
                min_confidence=80,
                min_accuracy=85,
                max_p_margin=0.05
            )
            n = ensemble.mine_from_fit_file(filepath)
            print(f"\nAccepted {n} rules")
            print(ensemble.get_summary())
    else:
        print("Ensemble RA Classifier")
        print("=" * 40)
        print("\nUsage:")
        print("  python ensemble_ra.py <search_report.txt>   # Parse search results")
        print("  python ensemble_ra.py <fit_report.txt>      # Mine rules from fit")
        print("\nOr use programmatically:")
        print("  from ensemble_ra import EnsembleRAClassifier")
        print("  ensemble = EnsembleRAClassifier(manager)")
        print("  ensemble.run_ensemble_workflow('full-up', levels=7, width=3)")
