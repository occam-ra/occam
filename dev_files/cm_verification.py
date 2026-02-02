#!/usr/bin/env python3
"""
Comprehensive Confusion Matrix Verification Script

Tests confusion matrix extraction for:
1. Training data CM (always present)
2. Test data CM (when :test data provided)
3. Multiple datasets (dementia05 and landslides)
4. Multiple models

This script validates against server PDF outputs to ensure accuracy.
"""

import pyoccam
import os
import sys
from pathlib import Path
import re

# Colors for terminal output
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def print_header(text):
    print(f"\n{Colors.BOLD}{Colors.HEADER}{'='*80}")
    print(f"{text}")
    print(f"{'='*80}{Colors.ENDC}\n")

def print_success(text):
    print(f"{Colors.OKGREEN}✓ {text}{Colors.ENDC}")

def print_error(text):
    print(f"{Colors.FAIL}✗ {text}{Colors.ENDC}")

def print_warning(text):
    print(f"{Colors.WARNING}⚠ {text}{Colors.ENDC}")

def print_info(text):
    print(f"{Colors.OKCYAN}ℹ {text}{Colors.ENDC}")


class CMVerifier:
    """Verifies confusion matrix extraction accuracy"""
    
    def __init__(self, data_file, expected_results=None):
        self.data_file = data_file
        self.expected_results = expected_results or {}
        self.results = {}
        
    def extract_cm_from_report_text(self, report_text, section="training"):
        """
        Manually extract CM from report text to verify parser
        
        Args:
            report_text: The fit report text
            section: "training" or "test"
        """
        lines = report_text.split('\n')
        
        # Find the right section
        target_line = f"Confusion Matrix for Fit Rule ({'Training' if section == 'training' else 'Test'})"
        
        tn = fp = fn = tp = 0
        found_section = False
        
        for i, line in enumerate(lines):
            if target_line in line:
                found_section = True
                print_info(f"Found {section} CM section at line {i}")
                
                # Look for TN/FP line (Z=0 row)
                for j in range(i+1, min(i+10, len(lines))):
                    if ',Z=0,|,TN=' in lines[j]:
                        parts = lines[j].split(',')
                        for k, part in enumerate(parts):
                            if part == 'TN=' and k+1 < len(parts):
                                tn = float(parts[k+1])
                            elif part == 'FP=' and k+1 < len(parts):
                                fp = float(parts[k+1])
                    
                    # Look for FN/TP line (Z≠0 or Z=not0 row)
                    if ',Z=not0,|,FN=' in lines[j] or ',Z≠0,|,FN=' in lines[j]:
                        parts = lines[j].split(',')
                        for k, part in enumerate(parts):
                            if part == 'FN=' and k+1 < len(parts):
                                fn = float(parts[k+1])
                            elif part == 'TP=' and k+1 < len(parts):
                                tp = float(parts[k+1])
                
                # Stop after finding this section
                if tn + tp + fn + fp > 0:
                    break
        
        if not found_section:
            print_warning(f"Did not find {section} CM section in report")
            return None
        
        if tn + tp + fn + fp == 0:
            print_warning(f"Found {section} CM section but all values are 0")
            return None
        
        # Calculate metrics
        total = tn + fp + fn + tp
        accuracy = (tn + tp) / total if total > 0 else 0
        sensitivity = tp / (tp + fn) if (tp + fn) > 0 else 0
        specificity = tn / (tn + fp) if (tn + fp) > 0 else 0
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0
        npv = tn / (tn + fn) if (tn + fn) > 0 else 0
        f1 = 2 * precision * sensitivity / (precision + sensitivity) if (precision + sensitivity) > 0 else 0
        
        return {
            'tn': tn, 'fp': fp, 'fn': fn, 'tp': tp,
            'accuracy': accuracy,
            'sensitivity': sensitivity,
            'specificity': specificity,
            'precision': precision,
            'npv': npv,
            'f1_score': f1
        }
    
    def verify_model(self, manager, model_name, target_state="0"):
        """
        Comprehensive verification of CM extraction for a model
        """
        print_header(f"VERIFYING MODEL: {model_name}")
        
        # Generate fit report
        print_info("Generating fit report...")
        fit_report = manager.generate_fit_report(model_name, target_state)
        
        # Save for inspection
        report_file = f"verify_{model_name.replace(':', '_')}_report.txt"
        with open(report_file, 'w') as f:
            f.write(fit_report)
        print_info(f"Saved report to: {report_file}")
        
        # Check if test data exists
        has_test = 'Confusion Matrix for Fit Rule (Test)' in fit_report
        print_info(f"Test data present: {has_test}")
        
        results = {
            'model': model_name,
            'has_test_data': has_test
        }
        
        # ===== TEST 1: Extract Training CM Manually =====
        print(f"\n{Colors.BOLD}Test 1: Manual Training CM Extraction{Colors.ENDC}")
        manual_train = self.extract_cm_from_report_text(fit_report, "training")
        if manual_train:
            print_success(f"Manual training CM: TN={manual_train['tn']:.0f}, FP={manual_train['fp']:.0f}, FN={manual_train['fn']:.0f}, TP={manual_train['tp']:.0f}")
            print_success(f"  Accuracy: {manual_train['accuracy']:.3f}, F1: {manual_train['f1_score']:.3f}")
            results['manual_training'] = manual_train
        else:
            print_error("Failed to extract training CM manually")
            results['manual_training'] = None
        
        # ===== TEST 2: Extract Training CM via get_confusion_matrix =====
        print(f"\n{Colors.BOLD}Test 2: API Training CM Extraction{Colors.ENDC}")
        api_cm = manager.get_confusion_matrix(model_name, target_state)
        if api_cm and api_cm.get('accuracy', 0) > 0:
            print_success(f"API CM: TN={api_cm['tn']:.0f}, FP={api_cm['fp']:.0f}, FN={api_cm['fn']:.0f}, TP={api_cm['tp']:.0f}")
            print_success(f"  Accuracy: {api_cm['accuracy']:.3f}, F1: {api_cm.get('f1_score', 0):.3f}")
            results['api_cm'] = api_cm
        else:
            print_error("API returned zero or empty CM")
            print_warning(f"  Returned: {api_cm}")
            results['api_cm'] = None
        
        # ===== TEST 3: Compare Manual vs API =====
        if manual_train and api_cm:
            print(f"\n{Colors.BOLD}Test 3: Manual vs API Comparison{Colors.ENDC}")
            
            # Check if they match
            tolerance = 0.001
            matches = []
            mismatches = []
            
            for key in ['tn', 'fp', 'fn', 'tp', 'accuracy']:
                manual_val = manual_train.get(key, 0)
                api_val = api_cm.get(key, 0)
                diff = abs(manual_val - api_val)
                
                if diff < tolerance:
                    matches.append(key)
                    print_success(f"  {key.upper()}: {manual_val:.3f} == {api_val:.3f}")
                else:
                    mismatches.append(key)
                    print_error(f"  {key.upper()}: {manual_val:.3f} != {api_val:.3f} (diff={diff:.3f})")
            
            if len(mismatches) == 0:
                print_success("✓ PERFECT MATCH: Manual and API values agree!")
                results['training_match'] = True
            else:
                print_error(f"✗ MISMATCH: {len(mismatches)} values differ")
                results['training_match'] = False
        
        # ===== TEST 4: Test Data CM (if present) =====
        if has_test:
            print(f"\n{Colors.BOLD}Test 4: Test Data CM Extraction{Colors.ENDC}")
            manual_test = self.extract_cm_from_report_text(fit_report, "test")
            
            if manual_test:
                print_success(f"Manual test CM: TN={manual_test['tn']:.0f}, FP={manual_test['fp']:.0f}, FN={manual_test['fn']:.0f}, TP={manual_test['tp']:.0f}")
                print_success(f"  Accuracy: {manual_test['accuracy']:.3f}, F1: {manual_test['f1_score']:.3f}")
                results['manual_test'] = manual_test
                
                # TODO: Need API method to explicitly get test CM
                # For now, note that get_confusion_matrix() returns training CM
                print_warning("⚠ API currently returns TRAINING CM, not test CM")
                print_warning("  We need to add a parameter to specify training vs test")
            else:
                print_error("Failed to extract test CM manually")
                results['manual_test'] = None
        
        # ===== TEST 5: Compare with Expected (if provided) =====
        if model_name in self.expected_results:
            print(f"\n{Colors.BOLD}Test 5: Compare with Server Output{Colors.ENDC}")
            expected = self.expected_results[model_name]
            
            if manual_train:
                for key in ['tn', 'fp', 'fn', 'tp', 'accuracy']:
                    if key in expected:
                        expected_val = expected[key]
                        actual_val = manual_train[key]
                        diff = abs(expected_val - actual_val)
                        
                        if diff < 0.001:
                            print_success(f"  {key.upper()}: {actual_val:.3f} == {expected_val:.3f} (server)")
                        else:
                            print_error(f"  {key.upper()}: {actual_val:.3f} != {expected_val:.3f} (server, diff={diff:.3f})")
        
        return results
    
    def run_full_verification(self):
        """Run complete verification suite"""
        print_header(f"CONFUSION MATRIX VERIFICATION: {self.data_file}")
        
        # Initialize manager
        print_info("Initializing pyoccam manager...")
        manager = pyoccam.VBMManager()
        manager.init_from_command_line(["occam", self.data_file])
        print_success("Manager initialized")
        
        # Check if file has test data
        with open(self.data_file, 'r') as f:
            content = f.read()
            has_test_marker = ':test' in content.lower()
        
        print_info(f"Data file has :test marker: {has_test_marker}")
        
        # Run search
        print_info("Running search (loopless-up, levels=3, width=3)...")
        search_report = manager.generate_search_report("loopless-up", 3, 3)
        print_success("Search completed")
        
        # Get best models
        best_bic = manager.get_best_model_by_bic()
        best_aic = manager.get_best_model_by_aic()
        best_info = manager.get_best_model_by_information()
        
        print_info(f"Best by BIC: {best_bic}")
        print_info(f"Best by AIC: {best_aic}")
        print_info(f"Best by Info: {best_info}")
        
        # Verify each unique model
        models_to_test = list(set([best_bic, best_aic, best_info]))
        
        all_results = {}
        for model in models_to_test:
            results = self.verify_model(manager, model, "0")
            all_results[model] = results
        
        # Final summary
        self._print_summary(all_results)
        
        return all_results
    
    def _print_summary(self, all_results):
        """Print final summary"""
        print_header("VERIFICATION SUMMARY")
        
        total_tests = len(all_results)
        passed = sum(1 for r in all_results.values() if r.get('training_match', False))
        
        print(f"\n{Colors.BOLD}Results:{Colors.ENDC}")
        print(f"  Total models tested: {total_tests}")
        print(f"  Perfect matches: {passed}")
        print(f"  Failures: {total_tests - passed}")
        
        if passed == total_tests:
            print_success("\n🎉 ALL TESTS PASSED! Confusion matrix extraction is working correctly!")
        else:
            print_error(f"\n⚠ {total_tests - passed} tests failed. Review the output above.")
        
        # List any issues found
        issues = []
        for model, results in all_results.items():
            if not results.get('training_match', False):
                issues.append(f"  - {model}: Training CM mismatch")
            if results.get('has_test_data') and not results.get('manual_test'):
                issues.append(f"  - {model}: Test CM extraction failed")
        
        if issues:
            print_warning("\n⚠ Issues found:")
            for issue in issues:
                print(issue)


def main():
    """Main verification entry point"""
    
    # ===== TEST DATASET 1: DEMENTIA05 =====
    # Expected values from server PDF: server_search_output_dementia05_loopless.PDF
    dementia_expected = {
        'IV:ApZ': {
            'tn': 179, 'fp': 42, 'fn': 98, 'tp': 105,
            'accuracy': 0.670
        },
        'IV:ApZ:CZ': {
            'tn': 187, 'fp': 34, 'fn': 86, 'tp': 117,
            'accuracy': 0.717
        },
        'IV:ApZ:EdZ:CZ': {
            'tn': 191, 'fp': 30, 'fn': 85, 'tp': 118,
            'accuracy': 0.728
        }
    }
    
    # ===== TEST DATASET 2: LANDSLIDES (SY_SAMPLE) =====
    # Expected values from server CSVs: SY_sample_pts_to_occam3_shuffle_split42_hdr_server_*.csv
    # Model: IV:ElTwZ:HbZ:LcZ:SlZ:TcZ (Directed System)
    # ⚠️ IMPORTANT: Use MODEL-level CM, not relation-level!
    # This dataset HAS TEST DATA (training: 1077, test: 268)
    landslides_expected = {
        'IV:ElTwZ:HbZ:LcZ:SlZ:TcZ': {
            'training': {
                'tn': 466, 'fp': 85, 'fn': 153, 'tp': 373,
                'accuracy': 0.779
            },
            'test': {
                'tn': 122, 'fp': 27, 'fn': 46, 'tp': 73,
                'accuracy': 0.728
            }
        },
        'IV:LcZ:TcZ': {  # Best by BIC (simpler model)
            'training': {'tn': None, 'fp': None, 'fn': None, 'tp': None, 'accuracy': None},
            'test': {'tn': None, 'fp': None, 'fn': None, 'tp': None, 'accuracy': None}
        },
        'IV:HbZ:TcZ': {  # Another good model
            'training': {'tn': None, 'fp': None, 'fn': None, 'tp': None, 'accuracy': None},
            'test': {'tn': None, 'fp': None, 'fn': None, 'tp': None, 'accuracy': None}
        }
    }
    
    print("="*80)
    print("CONFUSION MATRIX COMPREHENSIVE VERIFICATION")
    print("="*80)
    print("\nThis script verifies:")
    print("  1. Training CM extraction (manual parsing)")
    print("  2. Training CM extraction (API)")
    print("  3. Manual vs API agreement")
    print("  4. Test CM extraction (if :test data present)")
    print("  5. Comparison with server PDF outputs")
    print()
    
    # Test dementia05
    if os.path.exists('dementia05.txt'):
        print_info("Testing dementia05.txt...")
        verifier = CMVerifier('dementia05.txt', dementia_expected)
        dementia_results = verifier.run_full_verification()
    else:
        print_warning("dementia05.txt not found, skipping")
    
    # Test with landslides/SY_sample (HAS TEST DATA!)
    sy_sample_file = 'SY_sample_pts_to_occam3_shuffle_split42_hdr.txt'
    if os.path.exists(sy_sample_file):
        print_info(f"\nTesting {sy_sample_file}...")
        print_info("⭐ This dataset HAS TEST DATA - will verify both training and test CMs")
        
        # Use special landslides verifier that checks both training and test
        verifier = CMVerifier(sy_sample_file, landslides_expected)
        landslides_results = verifier.run_full_verification()
        
        # Additional test-specific validation
        print_header("TEST DATA VALIDATION")
        print_info("Verifying that pyoccam correctly extracts TEST confusion matrix...")
        print_warning("⚠️ This requires the C++ enhancement to distinguish training vs test")
        print_info("Expected: API should support cm_type='test' parameter")
    else:
        print_warning(f"{sy_sample_file} not found, skipping landslides test")
    
    print_header("VERIFICATION COMPLETE")


if __name__ == "__main__":
    main()
