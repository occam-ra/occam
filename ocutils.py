#! /usr/bin/python
##--
# ocutils - utility scripts for common operations,
# such as processing old format occam files

import os, sys, re, occam, random
totalgen=0
totalkept=0
# don't exceed 500 MB
maxMemoryToUse = 500000000

class ocUtils:

	#-- separator styles for reporting
	TABSEP=1
	COMMASEP=2
	SPACESEP=3
	HTMLFORMAT=4

	#
	#-- Initialize instance
	#
	def __init__(self):
		self.__manager = occam.ocVBMManager()
		self.__report = self.__manager.ocReport()
		self.__sortName = "ddf"
		self.__reportSortName = ""
		self.__sortDir = "ascending"
		self.__searchSortDir = "ascending"
		self.__searchWidth = 20
		self.__searchLevels = 12
		self.__searchDir = "default"
		self.__searchFilter = "all"
		self.__startModel = "default"
		self.__refModel = "default"
		self.__fitModels = []
		self.__reportFile = ""
		self.__dataFile = ""
		self.__report.setSeparator(ocUtils.SPACESEP)	# align columns using spaces
		self.__HTMLFormat = 0
		self.__BPStatistics = 0
		self.__PercentCorrect = 0
		self.__NoIPF = 0

	#
	#-- Read command line args and process input file
	#
	def initFromCommandLine(self, argv):
		self.__manager.initFromCommandLine(argv)
		self.occam2Settings()

	#
	#-- Set up report variables
	#
	def setReportVariables(self, reportAttributes):
		self.__report.setAttributes(reportAttributes)
		if re.search('bp_t', reportAttributes):
			self.__BPStatistics = 1
		if re.search('pct_correct', reportAttributes):
			self.__PercentCorrect = 1

	def setReportSeparator(self, format):
		occam.setHTMLMode(format == ocUtils.HTMLFORMAT)
		self.__report.setSeparator(format)
		self.__HTMLFormat = (format == ocUtils.HTMLFORMAT)
	#
	#-- Set control attributes
	#
	def setSortName(self, sortName):
		self.__sortName = sortName

	def setReportSortName(self, sortName):
		self.__reportSortName = sortName

	def setSortDir(self, sortDir):
		if sortDir == "": sortDir = "descending"
		if sortDir != "ascending" and sortDir != "descending":
			raise AttributeError, "setSortDir"
		self.__sortDir = sortDir

	def setSearchSortDir(self, sortDir):
		if sortDir == "": sortDir = "descending"
		if sortDir != "ascending" and sortDir != "descending":
			raise AttributeError, "setSearchSortDir"
		self.__searchSortDir = sortDir

	def setSearchWidth(self, searchWidth):
		width = int(searchWidth)
		if width <= 0:
			raise AttributeError, "SearchWidth"
		self.__searchWidth = width

	def setSearchLevels(self, searchLevels):
		levels = int(searchLevels)
		if levels < 0:	# zero is OK here
			raise AttributeError, "SearchLevels"
		self.__searchLevels = levels

	def setSearchDir(self, searchDir):
		self.__searchDir = searchDir

	def setSearchFilter(self, searchFilter):
		self.__searchFilter = searchFilter

	def setRefModel(self, refModel):
		self.__refModel = refModel

	def setStartModel(self, startModel):
		self.__startModel = startModel

	def getStartModel(self):
		return self.__startModel

	def setFitModel(self, fitModel):
		self.__fitModels = [fitModel]

	def setReportFile(self, reportFile):
		self.__reportFile = reportFile

	def setAction(self, action):
		self.__action = action

	def setDataFile(self, dataFile):
		self.__dataFile = dataFile

	def setNoIPF(self, state):
		self.__NoIPF = state

	def isDirected(self):
		return self.__manager.isDirected()

	def setOption(self, opt):
		return self.__manager.setOption(opt)

	def hasTestData(self):
		return self.__manager.hasTestData()

	#
	#-- Search operations
	#

	# compare function for sorting models. The python list sort function uses this
	# the name of the attribute to sort on is given above, as well as ascending or descending
	def __compareModels(self, m1, m2):
		result = 0
		a1 = m1.get(self.__sortName)
		a2 = m2.get(self.__sortName)
		if self.__searchSortDir == "ascending":
			if (a1 > a2): result = 1
			if (a1 < a2): result = -1
		else:
			if (a1 > a2): result = -1
			if (a1 < a2): result = 1
		return result

	# this function decides which statistic to computed, based
	# on how search is sorting the models. We want to avoid any
	# extra expensive computations
	def computeSortStatistic(self, model):
		if self.__sortName == "h" or self.__sortName == "information" or self.__sortName == "unexplained" or self.__sortName == "alg_t"	:
			self.__manager.computeInformationStatistics(model)
		elif self.__sortName == "df" or self.__sortName == "ddf" :
			self.__manager.computeDFStatistics(model)
		elif self.__sortName == "bp_t" or self.__sortName == "bp_information" or self.__sortName == "bp_alpha" :
			self.__manager.computeBPStatistics(model)
		elif self.__sortName == "pct_correct":
			self.__manager.computePercentCorrect(model)
		# anything else, just compute everything we might need
		elif self.__sortName != "random":
			self.__manager.computeL2Statistics(model)
			self.__manager.computeDependentStatistics(model)

	#
	# this function generates the parents/children of the given model, and for
	# any which haven't been seen before puts them into the newModel list
	# this function also computes the LR statistics (H, LR, DF, etc.) as well
	# as the dependent statistics (dH, %dH, etc.)
	#

	def processModel(self, level, newModels, model):
		addCount = 0;
		generatedModels = self.__manager.searchOneLevel(model)
		for newModel in generatedModels :
			if newModel.get("processed") <= 0.0 :
				newModel.processed = 1.0
				newModel.random = random.random()
				newModel.level = level
				self.computeSortStatistic(newModel)
				pos = 0;
				while pos < len(newModels) and pos < self.__searchWidth:
					if self.__compareModels(newModel, newModels[pos]) <= 0: break
					pos = pos + 1;
				if pos < len(newModels):
					newModels.insert(pos, newModel)
				elif self.__searchWidth > 0 and len(newModels) < self.__searchWidth:
					newModels.append(newModel)
				addCount = addCount + 1;
				newModel.deleteFitTable()	#recover fit table memory
				newModel.deleteRelationLinks()	#recover relation link memory
		return addCount

			
	#
	# this function processes models from one level, and return models for the next level
	# for each level, it prints the best model at that level as a progress indicator
	#

	def processLevel(self, level, oldModels):
		global totalgen
                global totalkept
		newModels = []
		fullCount = 0;
		for model in oldModels:
			print '.',	# progress indicator
			fullCount = fullCount + self.processModel(level, newModels, model)
		#newModels.sort(self.__compareModels)
		#fullCount = len(newModels)
		if self.__searchWidth != 0:
			newModels = newModels[0:self.__searchWidth]
		self.__manager.deleteTablesFromCache()
		truncCount = len(newModels)
		totalgen = fullCount+totalgen
                totalkept = truncCount+totalkept
		memUsed = self.__manager.getMemUsage();
		print " ,%ld models generated, %ld kept,%ld total models generated,%ld total models kept, %ld bytes memory used" % (fullCount, truncCount, totalgen+1 ,totalkept+1, memUsed)
		# print self.__manager.printSizes();
		return newModels

	#
	# this function returns the name of the search strategy to use based on
	# the searchMode and loopless settings above
	#

	def searchType(self):
		if self.__searchDir == "up":
			if self.__searchFilter == "loopless":
				searchMode = "loopless-up"
			elif self.__searchFilter == "disjoint":
				searchMode = "disjoint-up"
			elif self.__searchFilter == "chain":
				searchMode = "chain-up"
			else:
				searchMode = "full-up"
		else:
			if self.__searchFilter == "loopless":
				searchMode = "loopless-down"
			elif self.__searchFilter == "disjoint":
				searchMode = "disjoint-up"
			elif self.__searchFilter == "chain":
				searchMode = "chain-up"
			else:
				searchMode = "full-down"
		return searchMode

	def doSearch(self, printOptions):
		if self.__startModel == "":
			self.__startModel = "default"

		if self.__manager.isDirected() and self.__searchDir == "default":
			self.__searchDir = "up"
		
		if not self.__manager.isDirected() and self.__searchDir == "default":
			self.__searchDir = "down"

		# set start model. For chain search, ignore any specific starting model
		# otherwise, if not set, set the start model based on search direction
		if (self.__searchFilter == "chain" or self.__startModel == "default") and self.__searchDir == "down":
			self.__startModel = "top"
		elif (self.__searchFilter == "chain" or self.__startModel == "default") and self.__searchDir == "up":
			self.__startModel = "bottom"

		if self.__startModel == "top":
			start = self.__manager.getTopRefModel()
		elif self.__startModel == "bottom":
			start = self.__manager.getBottomRefModel()
		else:
			start = self.__manager.makeModel(self.__startModel, 1)

		self.__manager.setRefModel(self.__refModel)

		if printOptions: self.printOptions()
		self.__manager.printBasicStatistics()
		self.__manager.computeL2Statistics(start)
		self.__manager.computeDependentStatistics(start)
		if self.__BPStatistics:
			self.__manager.computeBPStatistics(start)
		if self.__PercentCorrect:
			self.__manager.computePercentCorrect(start)
		start.level = 0
		self.__report.addModel(start)
		oldModels = [start]

		self.__manager.setSearchType(self.searchType())

		#
		# process each level, up to the number of levels indicated. Each of the best models
		# is added to the report generator for later output
		#
		StateSpace=self.__manager.computeDF(self.__manager.getTopRefModel())+1
                SampleSz1=self.__manager.getSampleSz()
                print "Sample Size:, %ld ," %(SampleSz1)
                print "State Space:, %lg ," %(StateSpace)
		print "Searching levels:",
		for i in xrange(1,self.__searchLevels+1):
			if self.__manager.getMemUsage() > maxMemoryToUse:
				print "Memory limit exceeded: stopping search"
				break

			print i,' ',	# progress indicator
			newModels = self.processLevel(i, oldModels)
			for model in newModels:
				# make sure all statistics are calculated. This
				# won't do anything if we did it already
				if not self.__NoIPF:
					self.__manager.computeL2Statistics(model)
					self.__manager.computeDependentStatistics(model)
				if self.__BPStatistics:
					self.__manager.computeBPStatistics(model)
				if self.__PercentCorrect:
					self.__manager.computePercentCorrect(model)

				self.__report.addModel(model)
			oldModels = newModels

			# if the list is empty, stop. Also, only do one step for chain search
			if self.__searchFilter == "chain" or len(oldModels) == 0:
				break

	def printReport(self):
		#
		# sort the report as requested, and print it.
		#
		if self.__reportSortName != "":
			sortName = self.__reportSortName
		else:
			sortName = self.__sortName
		self.__report.sort(sortName, self.__sortDir)
		if self.__reportFile != "":
			self.__report.writeReport(self.__reportFile)
		else:
			self.__report.printReport()

	def doFit(self,printOptions):
		self.__manager.printBasicStatistics()
		if printOptions: self.printOptions();
		for modelName in self.__fitModels:
			print "Model: ", modelName
			self.__manager.setRefModel(self.__refModel)
			model = self.__manager.makeModel(modelName, 1)
			self.__manager.computeL2Statistics(model)
			self.__manager.computeDependentStatistics(model)
			self.__report.addModel(model)
			self.__manager.printFitReport(model)
			sys.stdout.flush()
			if self.__manager.getOption("res-table"):
				self.__manager.makeFitTable(model)
				self.__report.printResiduals(model)
				sys.stdout.flush()
			print
			print

	def occam2Settings(self):
		option = self.__manager.getOption("action")
		if option != "":
			self.__action = option
		option = self.__manager.getOption("search-levels")
		if option != "":
			self.__searchLevels = int(float(option))
		option = self.__manager.getOption("optimize-search-width")
		if option != "":
			self.__searchWidth = int(float(option))
		option = self.__manager.getOption("reference-model")
		if option != "":
			self.__refModel = option
		option = self.__manager.getOption("search-direction")
		if option != "":
			self.__searchDir = option
		option = self.__manager.getOptionList("short-model")
		# for search, only one specified model allowed
		if len(option) > 0:
			self.__startModel = option[0]
			self.__fitModels = option


	def doAction(self, printOptions):
		# set reporting variables based on ref model
		if self.__manager.isDirected() and self.__refModel == "default":
			self.__refModel = "bottom"

		if not self.__manager.isDirected() and self.__refModel == "default":
			self.__refModel = "top"

		option = self.__action
		if option == "search":
			self.doSearch(printOptions)
			self.printReport()

		elif option == "fit":
			self.doFit(printOptions)

		else:
			print "Error: unknown operation", self.__action

	def printOption(self,label, value):
		if self.__HTMLFormat:
			print "<TR><TD>" + label + "</TD><TD>" + str(value) + "</TD></TR>"
		else:
			print label + "," + str(value)

	def printOptions(self):
		if self.__HTMLFormat:
			print "<table>"
		self.__manager.printOptions(self.__HTMLFormat)
		self.printOption("Input data file", self.__dataFile)
		self.printOption("Starting model", self.__startModel)
		self.printOption("Search direction", self.__searchDir)
		self.printOption("Ref model", self.__refModel)
		self.printOption("Models to consider", self.__searchFilter)
		self.printOption("Search width", self.__searchWidth)
		self.printOption("Search levels", self.__searchLevels)
		self.printOption("Sort by", self.__sortName)
		if self.__HTMLFormat:
			print "</table>"



# End class ocUtils


