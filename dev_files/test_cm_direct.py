import pyoccam

print("Testing confusion matrix extraction with file redirection...")

manager = pyoccam.VBMManager()
manager.init_from_command_line(["occam", "dementia05.txt"])

# Test models from the server PDF
test_models = [
    ("IV:ApZ", 179, 42, 98, 105, 0.670),  # ApZ or ApSxZ
    ("IV:EdZ", 216, 5, 180, 23, 0.564),  # EdZ
    ("IV:CZ", 111, 110, 68, 135, 0.580),  # CZ
    ("IV:KZ", 69, 152, 32, 171, 0.566),  # KZ
]

print("\nModel Testing Results:")
print("-" * 60)

for model, exp_tn, exp_fp, exp_fn, exp_tp, exp_acc in test_models:
    cm = manager.get_confusion_matrix(model, "0")

    if "error" in cm:
        print(f"{model}: ERROR - {cm['error']}")
    elif "warning" in cm:
        print(f"{model}: WARNING - {cm['warning']}")
        if "debug_cm_section" in cm:
            print(f"  Debug: {cm['debug_cm_section'][:200]}")
    else:
        tn_match = abs(cm['TN'] - exp_tn) < 1
        fp_match = abs(cm['FP'] - exp_fp) < 1
        fn_match = abs(cm['FN'] - exp_fn) < 1
        tp_match = abs(cm['TP'] - exp_tp) < 1
        acc_match = abs(cm['accuracy'] - exp_acc) < 0.01

        all_match = tn_match and fp_match and fn_match and tp_match and acc_match

        status = "✓ PASS" if all_match else "✗ FAIL"
        print(f"{model}: {status}")
        print(f"  TN={cm['TN']:.0f} (exp:{exp_tn}), FP={cm['FP']:.0f} (exp:{exp_fp})")
        print(f"  FN={cm['FN']:.0f} (exp:{exp_fn}), TP={cm['TP']:.0f} (exp:{exp_tp})")
        print(f"  Accuracy={cm['accuracy']:.3f} (exp:{exp_acc:.3f})")

print("\n" + "=" * 60)
print("File-based stdout capture test complete!")