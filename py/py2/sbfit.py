#! python
# coding=utf-8
# Copyright © 1990 The Portland State University OCCAM Project Team
# [This program is licensed under the GPL version 3 or later.]
# Please see the file LICENSE in the source
# distribution of this software for license terms.

import sys

# sys.path.append("/www")
import time

from ocutils import OCUtils

if len(sys.argv) < 3:
    print 'Incorrect parameters.'
    print 'Usage: %s datafile model' % sys.argv[0]
    sys.exit()


oc = OCUtils("SB")

t1 = time.time()
oc.init_from_command_line(sys.argv[0:2])  # initialize with the data file

oc.set_fit_model(sys.argv[2])
oc.set_action("SBfit")
oc.set_report_separator(3)
# oc.set_ddf_method(1)

t2 = time.time()
oc.do_action(0)
t3 = time.time()

print "start:  %8f" % (t2 - t1)
print "fit: %8f" % (t3 - t2)
