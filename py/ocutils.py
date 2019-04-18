# coding=utf-8
# Copyright © 1990 The Portland State University OCCAM Project Team
# [This program is licensed under the GPL version 3 or later.]
# Please see the file LICENSE in the source
# distribution of this software for license terms.

# coding=utf8
import sys, re, occam, time, heapq, ocGraph

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
        self.__fitClassifierTarget = ""
        self.__skipTrainedModelTable = 1
        self.__skipIVITables = 1
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
        
        self.graphs = {}
        self.__graphWidth = 500
        self.__graphHeight = 500
        self.__graphFontSize = 12
        self.__graphNodeSize = 36
        self.__generateGraph = False
        self.__generateGephi = False
        self.__hideIsolated = True
        self.__graphHideDV = False
        self.__fullVarNames = False
        self.__layoutStyle = None
#        self.__showEdgeWeights = True
#        self.__weightFn = "Mutual Information"


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

    def setFitClassifierTarget(self, target):
        self.__fitClassifierTarget = target

    def setSkipTrainedModelTable(self, b):
        self.__skipTrainedModelTable = b

    def setSkipIVITables(self, b):
        self.__skipIVITables = b
    
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
        if not (startModel in ["top", "bottom", "default", ""]):
            self.checkModelName(startModel)
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


    def printSearchGraphs(self):

        if not (self.__generateGraph or  self.__generateGephi):
            return

        # in HTML mode, note that the graphs are being printed.
        if self.__HTMLFormat:
            print('<hr>')

        # Get the varlist (used for all graphs)


        # Graphs for each kind of best model:
        # Generate the graph (but don't print anything yet).
        # BIC [1 or more]

        # AIC [1 or more]

        # Incr Alpha [0 or more]

        # For each of the graphs (and headers) above,
        # if HTML mode, print out a brief note and graph/gephi (if enabled)


    def newl(self):
        if self.__HTMLFormat: print "<br>"
    
    def splitCaps(self,s): 
        return re.findall('[A-Z][^A-Z]*', s)

    def splitModel(self,modelName):
        comps = modelName.split(":")
        model = map(lambda s: [s] if (s == "IV" if self.isDirected() else s == "IVI") else self.splitCaps(s), comps)
        return model

    def checkModelName(self, modelName):
        varlist = [v.getAbbrev() for v in self.__manager.getVariableList()]
        model = self.splitModel(modelName)
        isDirected = self.isDirected()
        haveIVs = False
        sawMaybeWrongIV = False

        # IV can be present if directed system; IVI otherwise
        if isDirected:
            if ["I","V","I"] in model:
                sawMaybeWrongIV = True
            if ["IV"] in model:
                haveIVs = True
        else:
            if ["I","V"] in model:
                sawMaybeWrongIV = True               
            if ["IVI"] in model:
                haveIVs = True     

        # all variables in varlist are in model (possibly as IV or IVI)
        modelvars = [var for rel in model for var in rel]
        
        varset = set(varlist)
        modset = set(modelvars)
        if isDirected:
            modset.discard("IV")
        else:
            modset.discard("IVI")

        if not haveIVs:
            if not varset.issubset(modset):
                if self.__HTMLFormat:
                    print "<br>"
                print "\nERROR: Not all declared variables are present in the model, '" + modelName + "'."
                if self.__HTMLFormat:
                    print "<br>"
                if sawMaybeWrongIV:
                    print "\nDid you mean '" + ("IV" if isDirected else "IVI") + "' instead of '" + ("IVI" if isDirected else "IV") + "'?"
                else:
                    print "\n Did you forget the " + ("IV" if isDirected else "IVI") + " component?"
                if self.__HTMLFormat:
                    print "<br>"
                print "\n Not in model: "
                print ", ".join(["'" + i + "'" for i in varset.difference(modset)])
                sys.exit(1)
        
        # all variables in model are in varlist
        if not modset.issubset(varset):
            if self.__HTMLFormat:
                print "<br>"
            print "\nERROR: Not all variables in the model '" + modelName + "' are declared in the variable list."
            if self.__HTMLFormat:
                print "<br>"
            diffset = modset.difference(varset)
            if sawMaybeWrongIV or diffset == set(["I", "V"]):
                print "\nDid you mean '" + ("IV" if isDirected else "IVI") + "' instead of '" + ("IVI" if isDirected else "IV") + "'?"
            else:
                print "\n Not declared: "
                print ", ".join(["'" + i + "'" for i in diffset])
              
            sys.exit(1)

        # dv must be in all components (except IV) if directed
        if isDirected:
            dv = self.__manager.getDvName()
            for rel in model:
                if not (rel == ["IVI"] or rel == ["IV"]) and dv not in rel:
                    if self.__HTMLFormat:
                        print "<br>"
                    print "\nERROR: In the model '" + modelName + "', model component '" + "".join(rel) + "' is missing the DV, '" + dv + "'."
                    sys.exit(1)
    
    def printGraph(self,modelName, only):
        if (only and not self.__generateGephi):
            self.__generateGraph = True
        if (self.__generateGraph or self.__generateGephi) and (self.__hideIsolated and (modelName == "IVI" or modelName == "IV")):
            msg = "Note: no " 
            if self.__generateGraph:
                msg = msg + "hypergraph image "
            if self.__generateGraph and self.__generateGephi:
                msg = msg + "or "
            if self.__generateGephi:
                msg = msg + "Gephi input "

            msg = msg + "was generated, since the model contains only "
            msg = msg + modelName
            msg = msg + " components, which were requested to be hidden in the graph."

            if self.__HTMLFormat:
                print "<br>"
            print msg
            if self.__HTMLFormat:
                print "<br>"

        else:
            self.maybePrintGraphSVG(modelName, True)
            self.maybePrintGraphGephi(modelName, True)
        print
        print




    def doFit(self,printOptions, onlyGfx):
        #self.__manager.setValuesAreFunctions(self.__valuesAreFunctions)


        if printOptions and not onlyGfx: self.printOptions(0)

        if not onlyGfx: self.__manager.printBasicStatistics()
       

        for modelName in self.__fitModels:
            self.checkModelName(modelName)
            self.__manager.setRefModel(self.__refModel)
            model = self.__manager.makeModel(modelName, 1)
 
            if onlyGfx:
                self.printGraph(modelName, onlyGfx)
                continue

            self.doAllComputations(model)


            if self.__defaultFitModel != "":
                try:
                    defaultModel = self.__manager.makeModel(self.__defaultFitModel, 1)
                except:
                    print "\nERROR: Unable to create model " + self.__defaultFitModel
                    sys.exit(0)
                self.__report.setDefaultFitModel(defaultModel)
            self.__report.printConditional_DV(model, self.__calcExpectedDV, self.__fitClassifierTarget)

            self.printGraph(modelName, onlyGfx)

    def maybePrintGraphSVG(self, model, header):

        if self.__generateGraph:
            self.generateGraph(model)
            if self.__HTMLFormat:
                if header: 
                    print "Hypergraph model visualization for the Model " + model + " (using the " + self.__layoutStyle + " layout algorithm)<br>"
                ocGraph.printSVG(self.graphs[model], self.__layoutStyle, self.__graphWidth, self.__graphHeight, self.__graphFontSize, self.__graphNodeSize)
                print "<hr>"

    def maybePrintGraphGephi(self, model, header):
        
        if self.__generateGephi:
            self.generateGraph(model)

            if self.__HTMLFormat:
                if header:
                    print "Hypergraph model Gephi input for the Model " + model + "<br>"
                print ocGraph.printGephi(self.graphs[model])
                print "<hr>"


    def generateGraph(self, model):
        varlist = self.__report.variableList()
        hideIV = self.__hideIsolated
        hideDV = self.__graphHideDV
        fullVarNames = self.__fullVarNames
        dvName = ""
        allHigherOrder = (self.__layoutStyle == "bipartite")
        if self.isDirected():
            dvName = self.__report.dvName()

        if self.graphs.has_key(model):
            pass
        else:
            self.graphs[model] = ocGraph.generate(model, varlist, hideIV, hideDV, dvName, fullVarNames, allHigherOrder)

    def setGfx(self, useGfx, layout=None, gephi=False, hideIV=True, hideDV=True, fullVarNames=False, width=640, height=480, fontSize=12, nodeSize=24):
       self.__generateGraph = useGfx
       self.__generateGephi = gephi
       self.__layoutStyle = layout
       self.__hideIsolated = hideIV
       self.__graphHideDV = hideDV
       self.__fullVarNames = fullVarNames
       self.__graphWidth = width
       self.__graphHeight = height
       self.__graphFontSize = fontSize
       self.__graphNodeSize = nodeSize
    

    def doAllComputations(self, model):
        self.__manager.computeL2Statistics(model)
        self.__manager.computeDFStatistics(model)
        self.__manager.computeDependentStatistics(model)
        self.__report.addModel(model)
        self.__manager.printFitReport(model)
        self.__manager.makeFitTable(model)
        self.__report.printResiduals(model, self.__skipTrainedModelTable, self.__skipIVITables)

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
            self.__report.printConditional_DV(model, self.__calcExpectedDV, self.__fitClassifierTarget)
            
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

    def doAction(self, printOptions, onlyGfx=False):
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
            self.doFit(printOptions, onlyGfx)
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

        if self.__fitClassifierTarget != "":
            self.printOption("Default ('negative') state for confusion matrices", self.__fitClassifierTarget)
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


        if r_type==0:
            self.printOption("Generate hypergraph images", "Y" if self.__generateGraph else "N")
            self.printOption("Generate Gephi files", "Y" if self.__generateGephi else "N")

        if self.__generateGraph:
            self.printOption("Hypergraph layout style", str(self.__layoutStyle))
            self.printOption("Hypergraph image width", str(self.__graphWidth))
            self.printOption("Hypergraph image height", str(self.__graphHeight))
            self.printOption("Hypergraph font size", str(self.__graphFontSize))
            self.printOption("Hypergraph node size", str(self.__graphNodeSize))

        if(self.__generateGephi or self.__generateGraph):
            self.printOption("Hide " + ("IV" if self.isDirected() else "IVI")  + " components in hypergraph", "Y" if self.__hideIsolated else "N")
            
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
            sys.stdout.write('.')
            newModels = self.processLevel(i, oldModels, i != self.__searchLevels)
            for model in newModels:
                self.__manager.computeL2Statistics(model)
                self.__manager.computeDependentStatistics(model)
                self.__nextID += 1
                model.setID(self.__nextID)
                self.__report.addModel(model)
            oldModels = newModels

        self.__report.sort(self.sortName, self.__sortDir)
        best = self.__report.bestModelData()
        self.__hide_intermediate_output = False
        return best

    def computeUnaryStatistic(self, model, key, modname):
        return self.__manager.computeUnaryStatistic(model, key, modname)

    def computeBinaryStatistic(self, compare_order, key):
        file_Ref, model_Ref, file_Comp, model_Comp = compare_order
        return self.__manager.computeBinaryStatistic(file_Ref, model_Ref, file_Comp, model_Comp, key)
