import sys, re, occam, time, heapq

totalgen=0
totalkept=0
maxMemoryToUse = 8 * 2**30

class ocUtils:
    # Separator styles for reporting
    TABSEP=1
    COMMASEP=2
    SPACESEP=3
    HTMLFORMAT=4

    def __init__(self,man):
        if man == "VB":
            self.__manager = occam.VBMManager()
        else:           
            self.__manager = occam.SBMManager()
        self.__hide_intermediate_output = False
        self.__report = self.__manager.Report()
        self.__DDFMethod = 0
        self.sortName = "ddf"
        self.__reportSortName = ""
        self.__sortDir = "ascending"
        self.__searchSortDir = "ascending"
	self.__alphaThreshold = 0.05
        self.__searchWidth = 3
        self.__searchLevels = 7
        self.searchDir = "default"
        self.__searchFilter = "loopless"
        self.__startModel = "default"
        self.__refModel = "default"
        self.__fitModels = []
        self.__reportFile = ""
        self.__dataFile = ""
        self.__calcExpectedDV = 0
        self.__defaultFitModel = ""
        self.__report.setSeparator(ocUtils.SPACESEP)    # align columns using spaces
        self.__HTMLFormat = 0
        self.__skipNominal = 0
        self.__useInverseNotation = 0
        self.__valuesAreFunctions = 0
        self.__BPStatistics = 0
        self.__PercentCorrect = 0
        self.__IncrementalAlpha = 0
        self.__NoIPF = 0
        self.totalgen = 0
        self.totalkept = 0
        self.__nextID = 0

    #-- Read command line args and process input file
    def initFromCommandLine(self, argv):
        self.__manager.initFromCommandLine(argv)
        self.occam2Settings()

    #-- Set up report variables
    def setReportVariables(self, reportAttributes):
        # if the data uses function values, we want to skip the attributes that require a sample size
        option = self.__manager.getOption("function-values")
        if option != "" or self.__valuesAreFunctions != 0:
            reportAttributes = re.sub(r",\salpha", '', reportAttributes)
            reportAttributes = re.sub(r",\sincr_alpha", '', reportAttributes)
            reportAttributes = re.sub(r",\slr", '', reportAttributes)
            reportAttributes = re.sub(r",\saic", '', reportAttributes)
            reportAttributes = re.sub(r",\sbic", '', reportAttributes)
            pass
        self.__report.setAttributes(reportAttributes)
        if re.search('bp_t', reportAttributes):
            self.__BPStatistics = 1
        if re.search('pct_correct', reportAttributes):
            self.__PercentCorrect = 1
        if re.search('incr_alpha', reportAttributes):
            self.__IncrementalAlpha = 1

    def setReportSeparator(self, format):
        occam.setHTMLMode(format == ocUtils.HTMLFORMAT)
        self.__report.setSeparator(format)
        self.__HTMLFormat = (format == ocUtils.HTMLFORMAT)

    def setSkipNominal(self, useFlag):
        flag = int(useFlag)
        if flag != 1:
            flag = 0
        self.__skipNominal = flag

    def setUseInverseNotation(self, useFlag):
        flag = int(useFlag)
        if flag != 1:
            flag = 0
        self.__useInverseNotation = flag

    def setValuesAreFunctions(self, useFlag):
        flag = int(useFlag)
        if flag != 1:
            flag = 0
        self.__valuesAreFunctions = flag

    #-- Set control attributes
    def setDDFMethod(self, DDFMethod):
        method = int(DDFMethod)
        if method != 1:
            method = 0
        self.__DDFMethod = method

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
        width = int(round(float(searchWidth)))
        if width <= 0:
            width = 1
        self.__searchWidth = width

    def setSearchLevels(self, searchLevels):
        levels = int(round(float(searchLevels)))
        if levels < 0:  # zero is OK here
            levels = 0
        self.__searchLevels = levels

    def setReportSortName(self, sortName):
        self.__reportSortName = sortName

    def setSearchFilter(self, searchFilter):
        self.__searchFilter = searchFilter

    def setAlphaThreshold(self, alphaThreshold):
 	self.__alphaThreshold = float(alphaThreshold)

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

    def setCalcExpectedDV(self, calcExpectedDV):
        self.__calcExpectedDV = calcExpectedDV

    def setDefaultFitModel(self, model):
        self.__defaultFitModel = model

    def setNoIPF(self, state):
        self.__NoIPF = state

    def isDirected(self):
        return self.__manager.isDirected()

    def hasTestData(self):
        return self.__manager.hasTestData()

    #-- Search operations
    # compare function for sorting models. The python list sort function uses this
    # the name of the attribute to sort on is given above, as well as ascending or descending
    def __compareModels(self, m1, m2):
        result = 0
        a1 = m1.get(self.sortName)
        a2 = m2.get(self.sortName)
        if self.__searchSortDir == "ascending":
            if a1 > a2: result = 1
            if a1 < a2: result = -1
        else:
            if a1 > a2: result = -1
            if a1 < a2: result = 1
        return result

    # this function decides which statistic to computed, based
    # on how search is sorting the models. We want to avoid any
    # extra expensive computations
    def computeSortStatistic(self, model):
        if self.sortName == "h" or self.sortName == "information" or self.sortName == "unexplained" or self.sortName == "alg_t" :
            self.__manager.computeInformationStatistics(model)
        elif self.sortName == "df" or self.sortName == "ddf" :
            self.__manager.computeDFStatistics(model)
        elif self.sortName == "bp_t" or self.sortName == "bp_information" or self.sortName == "bp_alpha" :
            self.__manager.computeBPStatistics(model)
        elif self.sortName == "pct_correct_data":
            self.__manager.computePercentCorrect(model)
        # anything else, just compute everything we might need
        else:
            self.__manager.computeL2Statistics(model)
            self.__manager.computeDependentStatistics(model)
 
    # this function generates the parents/children of the given model, and for
    # any which haven't been seen before puts them into the newModel list
    # this function also computes the LR statistics (H, LR, DF, etc.) as well
    # as the dependent statistics (dH, %dH, etc.)
    def processModel(self, level, newModelsHeap, model):
        addCount = 0
        generatedModels = self.__manager.searchOneLevel(model)
        for newModel in generatedModels:
            if newModel.get("processed") <= 0.0 :
                newModel.processed = 1.0
                newModel.level = level
                newModel.setProgenitor(model)
                self.computeSortStatistic(newModel)
    # need a fix here (or somewhere) to check for (and remove) models that have the same DF as the progenitor
                # decorate model with a key for sorting, & push onto heap
                key = newModel.get(self.sortName)
                if self.__searchSortDir == "descending":
                    key = -key
                heapq.heappush(newModelsHeap, ([key, newModel.get("name")] , newModel))     # appending the model name makes sort alphabet-consistent
                addCount += 1
            else:
                if self.__IncrementalAlpha:
                    # this model has been made already, but this progenitor might lead to a better Incr.Alpha
                    # so we ask the manager to check on that, and save the best progenitor
                    self.__manager.compareProgenitors(newModel, model)
        return addCount

            
    # This function processes models from one level, and return models for the next level.
    def processLevel(self, level, oldModels, clear_cache_flag):
        # start a new heap
        newModelsHeap = []
        fullCount = 0
        for model in oldModels:
            fullCount += self.processModel(level, newModelsHeap, model)
        # if searchWidth < heapsize, pop off searchWidth and add to bestModels
        bestModels = []
        lastKey = ['','']
        while len(newModelsHeap) > 0:
            # make sure that we're adding unique models to the list (mostly for state-based)
            key, candidate = heapq.heappop(newModelsHeap)
            if (len(bestModels) < self.__searchWidth): # or key[0] == lastKey[0]:      # comparing keys allows us to select more than <width> models,
                if True not in [n.isEquivalentTo(candidate) for n in bestModels]:   # in the case of ties
                    bestModels.append(candidate)
                    lastKey = key
            else:
                break
        truncCount = len(bestModels)
        self.totalgen  = fullCount + self.totalgen
        self.totalkept = truncCount + self.totalkept
        memUsed = self.__manager.getMemUsage()
        if not self.__hide_intermediate_output:
            print '%d new models, %ld kept; %ld total models, %ld total kept; %ld kb memory used; ' % (fullCount, truncCount, self.totalgen+1, self.totalkept+1, memUsed/1024),
        sys.stdout.flush()
        if clear_cache_flag:
            for item in newModelsHeap:
                self.__manager.deleteModelFromCache(item[1])
        return bestModels


    # This function returns the name of the search strategy to use based on
    # the searchMode and loopless settings above
    def searchType(self):
        if self.searchDir == "up":
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
                # This mode is not implemented
                searchMode = "disjoint-down"
            elif self.__searchFilter == "chain":
                # This mode is not implemented
                searchMode = "chain-down"
            else:
                searchMode = "full-down"
        return searchMode

    def sbSearchType(self):
        if self.searchDir == "up":
            if self.__searchFilter == "loopless":
                searchMode = "sb-loopless-up"
            elif self.__searchFilter == "disjoint":
                searchMode = "sb-disjoint-up"
            elif self.__searchFilter == "chain":
                searchMode = "sb-chain-up"
            else:
                searchMode = "sb-full-up"
        else:
            if self.__searchFilter == "loopless":
                searchMode = "sb-loopless-down"
            elif self.__searchFilter == "disjoint":
                # This mode is not implemented
                searchMode = "sb-disjoint-down"
            elif self.__searchFilter == "chain":
                # This mode is not implemented
                searchMode = "sb-chain-down"
            else:
                searchMode = "sb-full-down"
        return searchMode

    def doSearch(self, printOptions):
        if self.__manager.isDirected():
            if self.searchDir == "down":
                if self.__searchFilter == "disjoint":
		            pass
                elif self.__searchFilter == "chain":
                    print 'ERROR: Directed Down Chain Search not yet implemented.'
                    raise sys.exit()
        else:
            if self.searchDir == "up":
                pass
            else:
                if self.__searchFilter == "disjoint":
                    pass
                elif self.__searchFilter == "chain":
                    print 'ERROR: Neutral Down Chain Search not yet implemented.'
                    raise sys.exit()

        if self.__startModel == "":
            self.__startModel = "default"
        if self.__manager.isDirected() and self.searchDir == "default":
            self.searchDir = "up"
        if not self.__manager.isDirected() and self.searchDir == "default":
            self.searchDir = "up"
        # set start model. For chain search, ignore any specific starting model
        # otherwise, if not set, set the start model based on search direction
        if (self.__searchFilter == "chain" or self.__startModel == "default") and self.searchDir == "down":
            self.__startModel = "top"
        elif (self.__searchFilter == "chain" or self.__startModel == "default") and self.searchDir == "up":
            self.__startModel = "bottom"
        if self.__startModel == "top":
            start = self.__manager.getTopRefModel()
        elif self.__startModel == "bottom":
            start = self.__manager.getBottomRefModel()
        else:
            start = self.__manager.makeModel(self.__startModel, 1)
        self.__manager.setRefModel(self.__refModel)
        self.__manager.setUseInverseNotation(self.__useInverseNotation)
        self.__manager.setValuesAreFunctions(self.__valuesAreFunctions)
	self.__manager.setAlphaThreshold(self.__alphaThreshold)
        if self.searchDir == "down":
            self.__manager.setSearchDirection(1)
        else:
            self.__manager.setSearchDirection(0)
        if printOptions: self.printOptions(1)
        self.__manager.printBasicStatistics()
        self.__manager.computeL2Statistics(start)
        self.__manager.computeDependentStatistics(start)
        if self.__BPStatistics:
            self.__manager.computeBPStatistics(start)
        if self.__PercentCorrect and self.__manager.isDirected():
            self.__manager.computePercentCorrect(start)
        if self.__IncrementalAlpha:
            self.__manager.computeIncrementalAlpha(start)
        start.level = 0
        self.__report.addModel(start)
        self.__nextID = 1
        start.setID(self.__nextID)
        start.setProgenitor(start)
        oldModels = [start]
        try:
            self.__manager.setSearchType(self.searchType())
        except:
            print "ERROR: UNDEFINED SEARCH TYPE " + self.searchType()
            return
        # process each level, up to the number of levels indicated. Each of the best models
        # is added to the report generator for later output
        if self.__HTMLFormat: print '<pre>'
        print "Searching levels:"
        start_time = time.time()
        last_time = start_time
        for i in xrange(1,self.__searchLevels+1):
            if self.__manager.getMemUsage() > maxMemoryToUse:
                print "Memory limit exceeded: stopping search"
                break
            print i,':',    # progress indicator
            newModels = self.processLevel(i, oldModels, i != self.__searchLevels)
            current_time = time.time()
            print '%.1f seconds, %.1f total' % (current_time - last_time, current_time - start_time)
            sys.stdout.flush()
            last_time = current_time
            for model in newModels:
                # Make sure all statistics are calculated. This won't do anything if we did it already.
                if not self.__NoIPF:
                    self.__manager.computeL2Statistics(model)
                    self.__manager.computeDependentStatistics(model)
                if self.__BPStatistics:
                    self.__manager.computeBPStatistics(model)
                if self.__PercentCorrect:
                    self.__manager.computePercentCorrect(model)
                if self.__IncrementalAlpha:
                    self.__manager.computeIncrementalAlpha(model)
                self.__nextID += 1
                model.setID(self.__nextID)
                #model.deleteFitTable()  #recover fit table memory
                self.__report.addModel(model)
            oldModels = newModels
            # if the list is empty, stop. Also, only do one step for chain search
            if self.__searchFilter == "chain" or len(oldModels) == 0:
                break
        if self.__HTMLFormat: print '</pre><br>'
        else: print ""

    def doSbSearch(self,printOptions):
        if self.__startModel == "":
            self.__startModel = "default"
        if self.__manager.isDirected() and self.searchDir == "default":
            self.searchDir = "up"
        if not self.__manager.isDirected() and self.searchDir == "default":
            self.searchDir = "up"
        if (self.__searchFilter == "chain" or self.__startModel == "default") and self.searchDir == "down":
            self.__startModel = "top"
        elif (self.__searchFilter == "chain" or self.__startModel == "default") and self.searchDir == "up":
            self.__startModel = "bottom"
        if self.__startModel == "top":
            start = self.__manager.getTopRefModel()
        elif self.__startModel == "bottom":
            start = self.__manager.getBottomRefModel()
        else:
            start = self.__manager.makeSbModel(self.__startModel, 1)
        self.__manager.setRefModel(self.__refModel)
        if self.searchDir == "down":
            self.__manager.setSearchDirection(1)
        else:
            self.__manager.setSearchDirection(0)
        if printOptions: self.printOptions(1)
        self.__manager.printBasicStatistics()
        self.__manager.computeL2Statistics(start)
        self.__manager.computeDependentStatistics(start)
        if self.__PercentCorrect and self.__manager.isDirected():
            self.__manager.computePercentCorrect(start)
        if self.__IncrementalAlpha:
            self.__manager.computeIncrementalAlpha(start)
        start.level = 0
        self.__report.addModel(start)
        self.__nextID = 1
        start.setID(self.__nextID)
        start.setProgenitor(start)
        oldModels = [start]
        try:
            self.__manager.setSearchType(self.sbSearchType())
        except:
            print "ERROR: UNDEFINED SEARCH TYPE " + self.sbSearchType()
            return
        if self.__HTMLFormat: print '<pre>'
        print "Searching levels:"
        start_time = time.time()
        last_time = start_time
        for i in xrange(1,self.__searchLevels+1):
            if self.__manager.getMemUsage() > maxMemoryToUse:
                print "Memory limit exceeded: stopping search"
                break
            print i,':',    # progress indicator
            newModels = self.processLevel(i, oldModels, i != self.__searchLevels)
            current_time = time.time()
            print '%.1f seconds, %.1f total' % (current_time - last_time, current_time - start_time)
            last_time = current_time
            for model in newModels:
                # Make sure all statistics are calculated. This won't do anything if we did it already.
                if not self.__NoIPF:
                    self.__manager.computeL2Statistics(model)
                    self.__manager.computeDependentStatistics(model)
                if self.__BPStatistics:
                    self.__manager.computeBPStatistics(model)
                if self.__PercentCorrect:
                    self.__manager.computePercentCorrect(model)
                if self.__IncrementalAlpha:
                    self.__manager.computeIncrementalAlpha(model)
                self.__nextID += 1
                model.setID(self.__nextID)
                model.deleteFitTable()  #recover fit table memory
                self.__report.addModel(model)
            oldModels = newModels
            # if the list is empty, stop. Also, only do one step for chain search
            if self.__searchFilter == "chain" or len(oldModels) == 0:
                break
        if self.__HTMLFormat: print '</pre><br>'
        else: print ""

    def printSearchReport(self):
        # sort the report as requested, and print it.
        if self.__reportSortName != "":
            sortName = self.__reportSortName
        else:
            sortName = self.sortName
        self.__report.sort(sortName, self.__sortDir)
        if self.__reportFile != "":
            self.__report.writeReport(self.__reportFile)
        else:
            self.__report.printReport()
        #-- self.__manager.dumpRelations()

    def doFit(self,printOptions):
        #self.__manager.setValuesAreFunctions(self.__valuesAreFunctions)
        if printOptions: self.printOptions(0)
        self.__manager.printBasicStatistics()
        for modelName in self.__fitModels:
            self.__manager.setRefModel(self.__refModel)
            model = self.__manager.makeModel(modelName, 1)
            self.doAllComputations(model)
            if self.__defaultFitModel != "":
                try:
                    defaultModel = self.__manager.makeModel(self.__defaultFitModel, 1)
                except:
                    print "\nERROR: Unable to create model " + self.__defaultFitModel
                    sys.exit(0)
                self.__report.setDefaultFitModel(defaultModel)
            self.__report.printConditional_DV(model, self.__calcExpectedDV)
            print
            print

    def doAllComputations(self, model):
        self.__manager.computeL2Statistics(model)
        self.__manager.computeDFStatistics(model)
        self.__manager.computeDependentStatistics(model)
        self.__report.addModel(model)
        self.__manager.printFitReport(model)
        self.__manager.makeFitTable(model)
        self.__report.printResiduals(model)

    def doSbFit(self,printOptions):
        #self.__manager.setValuesAreFunctions(self.__valuesAreFunctions)
        if printOptions: self.printOptions(0);
        self.__manager.printBasicStatistics()
        for modelName in self.__fitModels:
            self.__manager.setRefModel(self.__refModel)
            model = self.__manager.makeSbModel(modelName, 1)
            self.doAllComputations(model)
            if self.__defaultFitModel != "":
                try:
                    defaultModel = self.__manager.makeSbModel(self.__defaultFitModel, 1)
                except:
                    print "\nERROR: Unable to create model " + self.__defaultFitModel
                    sys.exit(0)
                self.__report.setDefaultFitModel(defaultModel)
            self.__report.printConditional_DV(model, self.__calcExpectedDV)
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
            self.searchDir = option
        option = self.__manager.getOptionList("short-model")
        # for search, only one specified model allowed
        if len(option) > 0:
            self.__startModel = option[0]
            self.__fitModels = option

    def doAction(self, printOptions):
        # set reporting variables based on ref model
        if self.__manager.isDirected() and self.__refModel == "default":
            if self.searchDir == "down":
                self.__refModel = "top"
            else:
                self.__refModel = "bottom"
        if not self.__manager.isDirected() and self.__refModel == "default":
            if self.searchDir == "down":
                self.__refModel = "top"
            else:
                self.__refModel = "bottom"
        option = self.__action
        if option == "search":
            self.__manager.setDDFMethod(self.__DDFMethod)
            self.doSearch(printOptions)
            self.printSearchReport()
        elif option == "fit":
            self.__manager.setDDFMethod(self.__DDFMethod)
            self.doFit(printOptions)
        elif option == "SBsearch":
            #self.__manager.setDDFMethod(self.__DDFMethod)
            self.doSbSearch(printOptions)
            self.printSearchReport()
        elif option == "SBfit":
            self.doSbFit(printOptions)
        else:
            print "Error: unknown operation", self.__action

    def printOption(self,label, value):
        if self.__HTMLFormat:
            print "<tr><td>" + label + "</td><td>" + str(value) + "</td></tr>"
        else:
            print label + "," + str(value)

    def printOptions(self,r_type):
        if self.__HTMLFormat:
            print "<br><table border=0 cellpadding=0 cellspacing=0>"
        self.__manager.printOptions(self.__HTMLFormat, self.__skipNominal)
        self.printOption("Input data file", self.__dataFile)
        if r_type==1:   
            self.printOption("Starting model", self.__startModel)
            self.printOption("Search direction", self.searchDir)
            self.printOption("Ref model", self.__refModel)
            self.printOption("Models to consider", self.__searchFilter)
            self.printOption("Search width", self.__searchWidth)
            self.printOption("Search levels", self.__searchLevels)
            self.printOption("Search sort by", self.sortName)
            self.printOption("Search preference", self.__searchSortDir)
            self.printOption("Report sort by", self.__reportSortName)
            self.printOption("Report preference", self.__sortDir)
        if self.__HTMLFormat:
            print "</table>"
        sys.stdout.flush()

    def findBestModel(self):
        self.__hide_intermediate_output = True

        # Initialize a manager and the starting model
        self.__manager.setRefModel(self.__refModel)
        self.__manager.setSearchDirection(1 if (self.searchDir == "down") else 0)
        self.__manager.setSearchType(self.searchType())
       
        # Set up the starting model
        start = self.__manager.getTopRefModel() if (self.searchDir == "down") else self.__manager.getBottomRefModel()
        start.level = 0
        self.__manager.computeL2Statistics(start)
        self.__manager.computeDependentStatistics(start)
        self.__report.addModel(start)
        self.__nextID = 1
        start.setID(self.__nextID)
        start.setProgenitor(start)
        
        # Perform the search to find the best model
        oldModels = [start]
        for i in xrange(1, self.__searchLevels + 1):
            newModels = self.processLevel(i, oldModels, i != self.__searchLevels)
            for model in newModels:
                self.__manager.computeL2Statistics(model)
                self.__manager.computeDependentStatistics(model)
                self.__nextID += 1
                model.setID(self.__nextID)
                self.__report.addModel(model)
            oldModels = newModels

        self.__report.sort(self.sortName, self.__sortDir)
        best = self.__report.bestModelName()
        self.__hide_intermediate_output = False
        return best

    def computeUnaryStatistic(self, model, key, modname):
        return self.__manager.computeUnaryStatistic(model, key, modname)

    def computeBinaryStatistic(self, compare_order, key):
        file_Ref, model_Ref, file_Comp, model_Comp = compare_order
        return self.__manager.computeBinaryStatistic(file_Ref, model_Ref, file_Comp, model_Comp, key)
