#! /usr/bin/python
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

t2 = time.time()
oc.doAction(0)
t3 = time.time()

print "start:  %8f" % (t2 - t1)
print "search: %8f" % (t3 - t2)

