#! python
# Copyright © 1990 The Portland State University OCCAM Project Team
# [This program is licensed under the GPL version 3 or later.]
# Please see the file LICENSE in the source
# distribution of this software for license terms.

import pdb
import os, sys
sys.path.append("/www")
import occam
import time

from ocutils import ocUtils

if len(sys.argv) < 3:
	print 'Incorrect parameters.'
	print 'Usage: %s datafile model' % sys.argv[0]
	sys.exit()


oc = ocUtils("SB")

t1 = time.time()
oc.initFromCommandLine(sys.argv[0:2]) # initialize with the data file

oc.setFitModel(sys.argv[2])
oc.setAction("SBfit")
oc.setReportSeparator(3)
#oc.setDDFMethod(1)

t2 = time.time()
oc.doAction(0)
t3 = time.time()

print "start:  %8f" % (t2 - t1)
print "fit: %8f" % (t3 - t2)

