import pyoccam
import sys

manager = pyoccam.VBMManager()
manager.init_from_command_line(["occam", "dementia05.txt"])

print("Testing IV:ApZ:EdZ step by step...", flush=True)

print("Step 1: Generate fit report (no target)...", flush=True)
report = manager.generate_fit_report("IV:ApZ:EdZ", "")
print(f"  OK - {len(report)} chars", flush=True)

print("Step 2: Generate fit report (with target)...", flush=True)
sys.stdout.flush()
report = manager.generate_fit_report("IV:ApZ:EdZ", "0")
print(f"  OK - {len(report)} chars", flush=True)

print("Step 3: Get confusion matrix...", flush=True)
sys.stdout.flush()
cm = manager.get_confusion_matrix("IV:ApZ:EdZ", "0")
print(f"  OK - acc={cm['accuracy']:.3f}", flush=True)

print("ALL DONE!")