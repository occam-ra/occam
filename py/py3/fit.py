#! python
# coding=utf-8
# Copyright © 1990 The Portland State University OCCAM Project Team
# [This program is licensed under the GPL version 3 or later.]
# Please see the file LICENSE in the source
# distribution of this software for license terms.

import sys
import time

from ocutils import OCUtils

# sys.path.append("/www")

if len(sys.argv) < 3:
    print('Incorrect parameters.')
    print(f'Usage: {sys.argv[0]} datafile model')
    sys.exit()


oc = OCUtils("VB")

t1 = time.time()
oc.init_from_command_line(sys.argv[0:2])  # initialize with the data file

oc.set_fit_model(sys.argv[2])
oc.set_action("fit")
oc.set_report_separator(3)
oc.set_skip_nominal(1)
oc.set_ddf_method(1)
# oc.set_default_fit_model("IV:CD")

t2 = time.time()
oc.do_action(1)
t3 = time.time()

print(f"start:  {(t2 - t1):8f}")
print(f"fit: {(t3 - t2):8f}")
