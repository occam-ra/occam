#!/usr/bin/env python3
"""
Timing diagnostic - see exactly where it hangs or gets slow
"""
import pyoccam
import sys
import time

sys.stderr = sys.stdout

def timed_step(description, func):
    """Run a function and print how long it took"""
    print(f"\n[{description}]", end='', flush=True)
    start = time.time()
    try:
        result = func()
        elapsed = time.time() - start
        print(f" OK ({elapsed:.2f}s)", flush=True)
        return result
    except Exception as e:
        elapsed = time.time() - start
        print(f" FAILED after {elapsed:.2f}s: {e}", flush=True)
        raise

print("="*80)
print("TIMING DIAGNOSTIC FOR COMPLEX MODEL")
print("="*80)

# Initialize
manager = timed_step("Initialize manager", pyoccam.VBMManager)

# Load data
def load_data():
    success = manager.init_from_command_line(["occam", "dementia05.txt"])
    if not success:
        raise RuntimeError("Failed to load data")
    return success

timed_step("Load data", load_data)

# Try SIMPLE model first (2 components)
print("\n" + "="*80)
print("TESTING SIMPLE MODEL (IV:ApZ)")
print("="*80)

simple_model = "IV:ApZ"
target = "0"

def gen_fit_simple():
    return manager.generate_fit_report(simple_model, target)

fit_report_simple = timed_step("Generate fit report (simple)", gen_fit_simple)
print(f"    Report length: {len(fit_report_simple)} chars")

def get_cm_simple():
    return manager.get_confusion_matrix()

cm_simple = timed_step("Get confusion matrix (simple)", get_cm_simple)
print(f"    Values: TN={cm_simple.get('TN', 0):.0f}, TP={cm_simple.get('TP', 0):.0f}")

# Now try COMPLEX model (4 components)
print("\n" + "="*80)
print("TESTING COMPLEX MODEL (IV:ApZ:EdZ:CZ)")
print("="*80)
print("NOTE: If this hangs, we'll see exactly where...")
print("="*80)

complex_model = "IV:ApZ:EdZ:CZ"

def gen_fit_complex():
    return manager.generate_fit_report(complex_model, target)

print("\nStarting fit report generation for complex model...")
print("If it hangs here, press Ctrl+C and let me know it hung during fit report")
print()

fit_report_complex = timed_step("Generate fit report (complex)", gen_fit_complex)

print(f"    Report length: {len(fit_report_complex)} chars")
if "Component" in fit_report_complex:
    print("    ✓ Report contains component relations")

def get_cm_complex():
    return manager.get_confusion_matrix()

cm_complex = timed_step("Get confusion matrix (complex)", get_cm_complex)

if cm_complex.get('has_values'):
    tn, fp, fn, tp = cm_complex['TN'], cm_complex['FP'], cm_complex['FN'], cm_complex['TP']
    print(f"    Values: TN={tn:.0f}, FP={fp:.0f}, FN={fn:.0f}, TP={tp:.0f}")
    print(f"    Accuracy: {cm_complex['accuracy']:.3f}")
    
    # Check against server
    if tn == 352 and fp == 90 and fn == 168 and tp == 238:
        print("    ✓✓✓ MATCHES SERVER OUTPUT!")
else:
    print("    ✗ No confusion matrix values")

print("\n" + "="*80)
print("TEST COMPLETE - ALL TIMINGS SHOWN ABOVE")
print("="*80)
