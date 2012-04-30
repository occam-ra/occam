#! python
#import pdb
import os, sys
#sys.path.append("/www")
import occam
import time

from ocutils import ocUtils

if len(sys.argv) < 3:
	print 'Incorrect parameters.'
	print 'Usage: %s datafile model' % sys.argv[0]
	sys.exit()


oc = ocUtils("VB")

t1 = time.time()
oc.initFromCommandLine(sys.argv[0:2]) # initialize with the data file

oc.setFitModel(sys.argv[2])
oc.setAction("fit")
oc.setReportSeparator(3)
oc.setDDFMethod(1)
#oc.setDefaultFitModel("IV:CD")

t2 = time.time()
oc.doAction(0)
t3 = time.time()

print "start:  %8f" % (t2 - t1)
print "fit: %8f" % (t3 - t2)

