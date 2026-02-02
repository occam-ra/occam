#!/usr/bin/env python
"""
Simple test to verify confusion matrix appears in fit reports
"""

import pyoccam2

# Initialize and load data
manager = pyoccam2.VBMManager()
manager.init_from_command_line(["occam", "dementia05.txt"])

# Configure
manager.set_report_separator(pyoccam2.SPACESEP)
manager.set_ref_model("bottom")

# OPTION 1: Set classifier target globally
manager.set_fit_classifier_target("0")  # Use Z=0 as negative class

# Generate fit report - confusion matrix should appear
print("Testing model IV:ApZ with confusion matrix (target state = 0)")
print("=" * 80)

fit_report = manager.generate_fit_report("IV:ApZ")  # Will use global target "0"
print(fit_report)

print("\n" + "=" * 80)
print("OPTION 2: Pass target state directly")
print("=" * 80)

# OPTION 2: Pass target state directly to generate_fit_report
fit_report2 = manager.generate_fit_report("IV:ApZ:EdZ", "0")  # Pass "0" directly
print(fit_report2)