#! /usr/local/bin/python
import os, sys, occam
theModels = ( \
	"A.B.C.D", \
	"A.B.D:A.C.D:B.C.D" \
)

# process(model)
# print info about the model


def process(model):
	mgr.computeL2Statistics(model)
	mgr.computePearsonStatistics(model)
	mgr.computeDependentStatistics(model)
	mgr.printFitReport(model)
	return
#end def
		


# BEGINNING of main script

# create a variable based modeling manager, and initialize
# it from the command line arguments (which contain the input file)
mgr = occam.ocVBMManager()
mgr.initFromCommandLine(sys.argv)
for modelName in theModels:
	model = mgr.makeModel(modelName, 1)
	process(model)

