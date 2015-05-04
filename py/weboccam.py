#! /usr/bin/env python

import os, cgi, sys, occam, time, string, pickle, zipfile, datetime, tempfile, cgitb, urllib2, platform, traceback

from time import clock
from ocutils import ocUtils
from OpagCGI import OpagCGI
from jobcontrol import JobControl

cgitb.enable(display=1)
VERSION = "3.3.11"

# TODO: eliminate the need for this kludgy definition.
false = 0; true = 1

# TODO: check that the 'datadir' directory exists.
# This requires a manual installation step.
# If it does not exist with correct permissions, OCCAM will not run.
datadir = "data"

def apply_if(predicate, func, val):
    return func(val) if predicate else val

def getDataFileName(formFields, trim=false, key='datafilename'):
    """
    Get the original name of the data file.
    * formFields:   the form data from the user
    * trim:         trim the extension from the filename.
    """
    return '_'.join(apply_if(trim, lambda d : os.path.splitext(d)[0], os.path.split(formFields[key])[1]).split())

def printHeaders(formFields, textFormat):
    if textFormat:
        print "Content-type: application/octet-stream"
        print "Content-disposition: attachment; filename=" + getDataFileName(formFields, true) + ".csv"
    else:
        print "Content-type: text/html"
    print ""

def printTop(template, textFormat):
    if textFormat:
        template.set_template('header.txt')
    else:
        template.set_template('header.html')
    args = {'version':VERSION,'date':datetime.datetime.now().strftime("%c")}
    template.out(args)

def printTime(textFormat):
    now = time.time()
    elapsed_t = now - startt
    if elapsed_t > 0:
        if textFormat:
            print "Run time: %f seconds\n" % elapsed_t
        else:
            print "<br>Run time: %f seconds</br>" % elapsed_t

#
#---- printBottom ---- Print bottom HTML part
#
def printBottom():
    template.set_template('footer.html')
    args = {}
    template.out(args)

#
#---- printForm ---- Print the data input form
#
def printForm(formFields):
    template = OpagCGI()
    action = formFields.get("action", "")

    formatText = ""
    if formFields.has_key("formatText"): formFields['formatText'] = "checked"
    template.set_template('switchform.html')
    template.out(formFields)

    if action in ["fit", "search", "SBsearch", "SBfit", "fitbatch", "log", "compare"]:
        cached = formFields.get("cached", "")
        if cached=="true" and action in ["fit", "search", "SBsearch", "SBfit"]:
            action = action + "_cached"
        template.set_template(action + 'form.html')
        template.out(formFields)

    if action == "jobcontrol":
        jc = JobControl()
        jc.showJobs(formFields)

#
#---- actionForm ---- put up the input form
#
def actionForm(form, errorText):
    if errorText:
        print "<H2>Error: %s</H2><BR>" % errorText
    printForm(form)

#
#---- getDataFile ---- get the posted data and store to temp file
#
def getDataFileAlloc(formFields, key='datafilename'):
    if getDataFileName(formFields, key=key) == "":
        print "ERROR: No data file specified."
        sys.exit()
    datafile = getUniqueFilename(os.path.join(datadir, getDataFileName(formFields)))
    try:
        outf = open(datafile, "w", 0660)
        data = formFields["data"]
        outf.write(data)
        outf.close()
    except:
        if getDataFileName(formFields) == "":
            print "ERROR: No data file specified."
        else:
            print "ERROR: Problems reading data file %s." % datafile
        sys.exit()
    return datafile

def getDataFileAllocByName(fn, data):
    if fn == "":
        print "ERROR: No data file specified."
        sys.exit()
    datafile = getTimestampedFilename(os.path.join(datadir, fn))
    try:
        outf = open(datafile, "w", 0660)
        outf.write(data)
        outf.close()
    except:
        print "ERROR: Problems reading data file %s." % datafile
        sys.exit()
    return datafile

def getDataFile(formFields):
    
    if formFields.get("cached") != "true":
        return unzipDataFile(getDataFileAlloc(formFields))
    else:
        return prepareCachedData(formFields)

def prepareCachedData(formFields):
    # Get relevant data from the form
    declsFileName = formFields.get("declsfilename") 
    declsFile = formFields.get("decls") 
    dataFileName  = formFields.get("datafilename")
    dataFile  = formFields.get("data")
    testFileName  = formFields.get("testfilename")
    testFile  = formFields.get("test")
    dataRefrName  = formFields.get("refr")
    testRefrName  = formFields.get("testrefr")
  
    # Check that a vars file was submitted
    if declsFileName == "":
        print "ERROR: No variable declarations file submitted."
        sys.exit(1)

    # Check that exactly 1 of datafile, refr were chosen
    if (dataFileName == "" and dataRefrName == "") or (dataFileName != "" and dataRefrName != ""):
        print "ERROR: Exactly 1 of 'Data File' and 'Cached Data Name' must be filled out."
        sys.exit(1)

    # Check that at most 1 of testfile, testrefr were chosen
    if testFileName != "" and testRefrName != "":
        print "ERROR: At most 1 of 'Test File' and 'Cached Test Name' must be filled out."
        sys.exit(1)
    
    def unpackToString(fn, data):
        rn = unzipDataFile(getDataFileAllocByName(fn, data))
        return open(rn).read(), rn

    decls, declsRn = unpackToString(declsFileName, declsFile)
    
    data = ""
    if dataFileName == "": # search for the Cached Data Name and combine.
        drn = os.path.join(datadir, dataRefrName)
        if not os.path.isfile(drn):
            print "ERROR: Data file corresponding to Cached Data Name, '" + dataRefrName + "', does not exist"
            sys.exit(1)
        data = open(drn).read()

    else:
        data, dataRefrName = unpackToString(dataFileName, dataFile)

    test = ""
    if testFileName == "" and testRefrName != "": 
        trn = os.path.join(datadir, testRefrName)
        print trn
        if not os.path.isfile(trn):
            print "ERROR: Test file corresponding to Cached Test Name, '" + testRefrName + "', does not exist"
            sys.exit(1)
        test = open(trn).read()
   
    elif testFileName != "":
        test, testRefrName = unpackToString(testFileName, testFile)
    
    dataRefrTag = os.path.split(dataRefrName)[1] 
    testRefrTag = os.path.split(testRefrName)[1]

    finalDataFile = decls + "\n" + data + "\n" + test

    finalDataFileName = declsFileName + "." + dataRefrTag
    finalDataFileName = finalDataFileName + ".txt"
    finalDataFileName = os.path.join(datadir,finalDataFileName)

    with open(finalDataFileName, "w") as f:
        f.write(finalDataFile)
    
    formFields['datafilename'] = finalDataFileName

    # Print out the (fresh or reference) cached data name to the report.
    r = ""
    if not textFormat: r += "<TABLE><TR><TD><B>"
    r += "Cached Data Name:"
    if textFormat: r += "\t"
    else: r += "</B></TD><TD>"
    r += dataRefrTag
    if textFormat: r += "\n"
    else: r += "</TD></TR><TR><TD><B>"
    if testRefrName != "": r += "Cached Test Name: "
    if textFormat: r += "\t"
    else: r += "</B></TD><TD>"
    r += testRefrTag 
    if not textFormat: r += "</TD></TR></TABLE>"
    print r
    # Return the new datafile.
    return finalDataFileName

def unzipDataFile(datafile):
    # If it appears to be a zipfile, unzip it
    if os.path.splitext(datafile)[1] == ".zip":
        oldfile = datafile
        zipdata = zipfile.ZipFile(datafile)
        # ignore any directories, or files in them, such as those OSX likes to make
        ilist = [item for item in zipdata.infolist() if item.filename.find("/") == -1]
        # make sure there is only one file left
        if len(ilist) != 1:
            print "ERROR: Zip file can only contain one data file. (It appears to contain %d.)" % len(ilist)
            sys.exit()
        # try to extract the file
        try:
            datafile = os.path.join(datadir, ilist[0].filename)
            datafile = getTimestampedFilename(datafile)
            outf = open(datafile, "w")
            outf.write(zipdata.read(ilist[0].filename))
            outf.close()
            os.remove(oldfile)
        except:
            print "ERROR: Extracting zip file failed."
            sys.exit()
    return datafile

def processFit(fn, model, negativeDVforConfusion, oc):
    global datafile, textFormat, printOptions

    if textFormat:
        oc.setReportSeparator(ocUtils.COMMASEP)
    else:
        print '<div class="data">'
        oc.setReportSeparator(ocUtils.HTMLFORMAT)

    if model <> "":
        oc.setFitModel(model)
    
    oc.setFitClassifierTarget(negativeDVforConfusion)
    oc.setAction("fit")
    oc.doAction(printOptions)

    if not textFormat:
        print "</span>"

#
#---- processSBFit ---- Do state based fit operation
#
def processSBFit(fn, model, negativeDVforConfusion, oc):
    global datafile, textFormat, printOptions
    if textFormat:
        oc.setReportSeparator(ocUtils.COMMASEP)
    else:
        print '<div class="data">'
        oc.setReportSeparator(ocUtils.HTMLFORMAT)

    if model <> "":
        oc.setFitModel(model)
    
    oc.setFitClassifierTarget(negativeDVforConfusion)
    oc.setAction("SBfit")
    oc.doAction(printOptions)

#
#---- actionFit ---- Report on Fit
#
def actionFit(formFields):
    global textFormat

    fn = getDataFile(formFields)
    oc = ocUtils("VB")
    if not textFormat:
        print '<pre>'
    oc.initFromCommandLine(["",fn])
    if not textFormat:
        print '</pre>'
    oc.setDataFile(formFields["datafilename"])
    if formFields.has_key("calcExpectedDV"):
        oc.setCalcExpectedDV(1)
    oc.setDDFMethod(1)
    skipNominalFlag = formFields.get("skipnominal", "")
    if skipNominalFlag:
        oc.setSkipNominal(1)
    if formFields.has_key("defaultmodel"):
        oc.setDefaultFitModel(formFields["defaultmodel"])
#functionFlag = formFields.get("functionvalues", "")
#if functionFlag:
#oc.setValuesAreFunctions(1)
    
    target = formFields["negativeDVforConfusion"] if formFields.has_key("negativeDVforConfusion") else ""
        
    if not formFields.has_key("data") or not formFields.has_key("model") :
        actionNone(formFields, "Missing form fields")
        return
    processFit(fn, formFields["model"], target, oc) 
    os.remove(fn)
#
#---- actionFitBatch ---- Report on several Fit models
#
def actionFitBatch(formFields):
    global batchEmail
    models = formFields["model"].split()
    formFields["model"] = models[0]
    actionFit(formFields)
    if len(models) > 1:
        formFields["model"] = "\n".join(models[1:])
        formFields["batchOutput"] = batchEmail
        startBatch(formFields)

#
#---- actionSBFit ---- Report on SB Fit model
#
def actionSBFit(formFields):
    global textFormat

    fn = getDataFile(formFields)
    oc = ocUtils("SB")
    if not textFormat:
        print '<pre>'
    oc.initFromCommandLine(["",fn])
    if not textFormat:
        print '</pre>'
    oc.setDataFile(formFields["datafilename"])
#functionFlag = formFields.get("functionvalues", "")
#if functionFlag:
#oc.setValuesAreFunctions(1)
    if not formFields.has_key("data") or not formFields.has_key("model") :
        actionNone(formFields, "Missing form fields")
        return
    skipNominalFlag = formFields.get("skipnominal", "")
    if skipNominalFlag:
        oc.setSkipNominal(1)
    target = formFields["negativeDVforConfusion"] if formFields.has_key("negativeDVforConfusion") else ""
    processSBFit(fn, formFields["model"], target, oc) 
    os.remove(fn)


#
#---- processSearch ---- Do search operation
#
def actionSearch(formFields):
    global textFormat
    fn = getDataFile(formFields)
    man="VB"
    oc = ocUtils(man)
    if not textFormat:
        print '<pre>'
    oc.initFromCommandLine(["",fn])
    if not textFormat:
        print '</pre>'
    oc.setDataFile(formFields["datafilename"])
    # unused error? this should get caught by getDataFile() above
    if not formFields.has_key("data") :
        actionForm(form, "Missing form fields")
        print "missing data"
        return
    #textFormat = formFields.get("format", "")
    if textFormat:
        oc.setReportSeparator(ocUtils.COMMASEP)
    else:
        oc.setReportSeparator(ocUtils.HTMLFORMAT)
    oc.setSortDir(formFields.get("sortdir", ""))
    levels = formFields.get("searchlevels")
    if levels and levels > 0:
        oc.setSearchLevels(levels)
    width = formFields.get("searchwidth")
    if width and width > 0:
        oc.setSearchWidth(width)
    reportSort = formFields.get("sortreportby", "")
    searchSort = formFields.get("sortby", "")
    inverseFlag = formFields.get("inversenotation", "")
    if inverseFlag:
        oc.setUseInverseNotation(1)
    skipNominalFlag = formFields.get("skipnominal", "")
    if skipNominalFlag:
        oc.setSkipNominal(1)
    functionFlag = formFields.get("functionvalues", "")
    if functionFlag:
        oc.setValuesAreFunctions(1)
    oc.setStartModel(formFields.get("model", "default"))
    refModel = formFields.get("refmodel", "default")
    #specificRefModel = ""
    #if refModel == "specific" and formFields.has_key("specificrefmodel"):
    #    refModel = formFields["specificrefmodel"]
        #specificRefModel = refModel
    if refModel == "starting":
        refModel = oc.getStartModel()
    oc.setRefModel(refModel)
    oc.searchDir = formFields.get("searchdir", "default")
    oc.setSearchSortDir(formFields.get("searchsortdir", ""))
    oc.setSearchFilter(formFields.get("searchtype", "all"))
    oc.setAlphaThreshold(formFields.get("alpha-threshold", "0.05"))
    oc.setAction("search")
    if formFields["evalmode"] == "bp":
        reportvars = "Level$I, bp_t, bp_h, ddf, bp_lr, bp_alpha, bp_information"
        oc.setNoIPF(true)
        if reportSort == "information": reportSort = "bp_information"
        elif reportSort == "alpha": reportSort = "bp_alpha"
        if searchSort == "information": searchSort = "bp_information"
        elif searchSort == "alpha": searchSort = "bp_alpha"
        if oc.isDirected():
            reportvars += ", bp_cond_pct_dh"
        reportvars += ", bp_aic, bp_bic"
    else:
        reportvars = "Level$I"
        if formFields.get("show_h", ""):
            reportvars += ", h"
        reportvars += ", ddf"
        if formFields.get("show_dlr", ""):
            reportvars += ", lr"
        if formFields.get("show_alpha", "") or searchSort == "alpha" or reportSort == "alpha":
            reportvars += ", alpha"
        reportvars += ", information"
        if oc.isDirected():
            if formFields.get("show_pct_dh", ""):
                reportvars += ", cond_pct_dh"
        if formFields.get("show_aic", "") or searchSort == "aic" or reportSort == "aic":
            reportvars += ", aic"
        if formFields.get("show_bic", "") or searchSort == "bic" or reportSort == "bic":
            reportvars += ", bic"
    if formFields.get("show_incr_a", ""):
        reportvars += ", incr_alpha, prog_id"
    if formFields.get("show_bp", "") and formFields["evalmode"] <> "bp":
        reportvars += ", bp_t"
    if oc.isDirected():
        if formFields.get("show_pct", "") or formFields.get("show_pct_cover", "") or searchSort == "pct_correct_data" or reportSort == "pct_correct_data":
            reportvars += ", pct_correct_data"
            if formFields.get("show_pct_cover", ""):
                reportvars += ", pct_coverage"
            if oc.hasTestData():
                reportvars += ", pct_correct_test"
                if formFields.get("show_pct_miss", ""):
                    reportvars += ", pct_missed_test"
    oc.setReportSortName(reportSort)
    oc.sortName = searchSort
    oc.setReportVariables(reportvars)
    if textFormat:
        oc.doAction(printOptions)
    else:
        print "<hr><p>"
        print '<div class="data">'
        oc.doAction(printOptions)
        print "</div>"
    os.remove(fn)


def actionBatchCompare(formFields):
    # Get data from the form

    # Get Occam search parameters
    search_assoc_list = []
    search_fields = ["type", "direction", "levels", "width", "sort by", "selection function"]

    for key in search_fields:
        search_assoc_list.append((key, formFields.get(key)))
    
    search = dict(search_assoc_list)
 
    # Get Occam report parameters
    report_1 = []
    report_2 = []
    report_fields_1 = ["DF(data)", "H(data)", "dBIC(model)", "dAIC(model)", "DF(model)", "H(model)"]
    report_fields_2 = ["Absolute dist", "Information dist", "Kullback-Leibler dist", "Euclidean dist", "Maximum dist", "Hellinger dist"]
    
    d = {"max(DF)":"DF(model)", "min(H)":"H(model)",
         "min(dAIC)":"dAIC(model)", "min(dBIC)":"dBIC(model)"}

    for r, rf in [(report_1, report_fields_1), (report_2, report_fields_2)]:
        for key in sorted(rf):
            if formFields.get(key, "") == "yes" or d[search["selection function"]] == key:
                r.append(key)


    # Check if the datafile field has a file in it.
    fn = getDataFileAlloc(formFields)
   
    # Validate the datafile as a zip file containing the proper named pairs.
    if not zipfile.is_zipfile(fn):
        print "ERROR: " + fn + " is not a zipped archive."
        sys.exit()

    def makePairs(zip_data):
        pairs = []
        sorted_data = sorted(zip_data, key = lambda s: s.filename)
        
        if len(sorted_data) == 0:
            print "ERROR: Empty zip archive."
            sys.exit()

        if len(sorted_data) % 2 != 0:
            print "ERROR: Expected an even number of datafiles inside the zip archive."
            sys.exit()
        for ix in range(len(sorted_data) / 2):
            g = lambda i : os.path.splitext(sorted_data[i].filename)[0]
            a = g(2*ix)
            b = g(2*ix + 1)
            if not (a[:-1] == b[:-1]):
                print "ERROR: Expected matching paired data, but got<br></br>"
                print "&emsp;&emsp;'" + sorted_data[2*ix].filename + "',<br></br>"
                print "&emsp;&emsp;'" + sorted_data[2*ix+1].filename + "'.<br></br>"
                print "For each pair in the zipfile, the 2 filenames must be the same"
                print "except for exactly 1 character immediately before the extension which differs<br></br>"
                print "&emsp;&emsp;(e.g. 'fileA.txt', 'fileB.txt')."
                sys.exit()
            pairs.append((a[:-1], sorted_data[2*ix], sorted_data[2*ix+1]))
        return pairs

    zip_data = zipfile.ZipFile(fn)
    pairs = makePairs([i for i in zip_data.infolist() if i.filename.find("/") == -1])
    
    # Define the analysis.
    # Steps: 
    # * Read out one pair at a time into the directory, and analyze it:
    #   * Search to find the best model for each file
    #   * Compare the two best models
    #   * Save a data row

    def extract(x):
        try:
            d = getUniqueFilename(os.path.join(datadir, x.filename))
            outf = open(d, "w")
            outf.write(zip_data.read(x.filename))
            outf.close()
            return d
        except:
            print "ERROR: Extracting zip file failed."
            sys.exit()

    # Figure out what statistics to include (and in what reporting order)
    def getStatHeaders():
        headers = []
        candidate = ["H(data)", "H(model)", "DF(data)", "DF(model)", 
                     "dAIC(model)", "dBIC(model)"]
        for i in report_1 + report_2:
            if i in candidate:
                headers.append(i[:-1] + "(A))")
                headers.append(i[:-1] + "(B))")
            if i in report_fields_2:
                headers.append(i + "(model(A), model(B))")
        return headers

    global textFormat, printOptions
   
    # Definitions used in the report
    def bracket(s, hl, hr, tl, tr):
        if textFormat:
            return tl + s + tr
        else:
            return hl + s + hr
    

    line = lambda s: bracket(s, "<br>", "</br>", "", "")
    tab_row = lambda s: bracket(s, "<tr>", "</tr>", "", "")
    tab_col = lambda s: bracket(s, "<td>", "</td>", "\t", ",")
    tab_head = lambda s: bracket(s, "<th align=left>", "</th>", "\t", ",")

    table_start = "<br><table border=0 cellpadding=0 cellspacing=0>"
    table_end = "</table>"


    def computeBestModel(filename): 
        oc = ocUtils("VB")
        oc.initFromCommandLine(["occam", filename])
        oc.setDataFile(filename)
        oc.setAction("search")
        
        # Hardcoded settings (for now):
        oc.setSortDir("descending")
        oc.setSearchSortDir("descending") # try to maximize dBIC or dAIC. 
        oc.setRefModel("bottom") # Always uses bottom as reference. 

        # Parameters from the web form 
        oc.sortName = search["sort by"]
        oc.setSearchLevels(int(search["levels"]))
        oc.setSearchWidth(int(search["width"]))
        oc.setSearchFilter(search["type"])

        [i, d] = search["direction"].split(" ")
        oc.searchDir = d
        oc.setStartModel(i)

        return oc.findBestModel()

    def selectBest(stats):
        sel = search["selection function"]
        d = 0
        s = ""
        if sel == "min(H)":
            d = -1
            s = "H(model)"
        elif sel == "max(DF)":
            d = 1
            s = "DF(model)"
        elif sel == "min(dBIC)":
            d = -1
            s = "dBIC(model)"
        elif sel == "min(dAIC)":
            d = -1
            s = "dAIC(model)"
        return d, s


    def computeModelStats(file_A, model_A, file_B, model_B):
        stats_1 = dict([(k,[0,0]) for k in report_1])
        stats_2 = {}

        for (f, m, i) in [(file_A, model_A, 0), (file_B, model_B, 1)]:
            oc = ocUtils("VB")
            oc.initFromCommandLine(["occam,", f])
            for k in report_1:
                stat, rest = k.split("(")
                mod = rest.strip(")")
                stats_1[k][i] = oc.computeUnaryStatistic(m, stat, mod) 

        # Find the best model based on the single-model stats
        best_d, best_s = selectBest(stats_1)
       
        a, b  = stats_1[best_s]
        best = ""
        if best_d == -1:
            best = "A" if a <= b else "B"
        elif best_d == 1:
            best = "A" if a >= b else "B"
        comp_order = [file_A, model_A, file_B, model_B] if best == "A" else [file_B, model_B, file_A, model_A]

        oc = ocUtils("VB")
        for k in report_2:
            stats_2[k] = oc.computeBinaryStatistic(comp_order, k)

        return best, stats_1, stats_2


    def runAnalysis(pair_name, file_A, file_B): 
        model_A = computeBestModel(file_A)
        model_B = computeBestModel(file_B)

        best, stats_1, stats_2 = computeModelStats(file_A, model_A, file_B, model_B)

        return ([pair_name, model_A, model_B, best], stats_1, stats_2)

    
    # Print out the report
    # * Print out options if requested
    # * Print out the file name
    # * Print out the header
    # * For each data row, pretty print it
    # * Print out the header again as a footer


    def ppOptions():
        for (k, v) in search_assoc_list:
            if v != '': 
                print tab_row(tab_col(k + ": ") + tab_col(v))
       
    def ppColumnList():
        print tab_row(tab_col("columns in report: ") + tab_col(", ".join(report_1 + report_2)))

    def ppAnalysis(row):
        return "".join(map(tab_col, row))

    def ppStats(stats_1, stats_2):
        s = ""
        fmt = "%.6g"
        for (k,v) in sorted(stats_1.items()):
            for i in [0, 1]:
                if (k[:2] == "DF"):
                    s += tab_col("%.0f" % v[i])
                else: 
                    s += tab_col(fmt % v[i])
        for (k,v) in sorted(stats_2.items()):
            s += tab_col(fmt % v)
        return s 

    def ppHeader():
        col_headers = ["pair name", "model(A)", "model(B)", search["selection function"]] + getStatHeaders()
        return "".join(map(tab_head, col_headers))

    
    # Layout the document
    if not textFormat: 
        print "<hr><p>"
        print '<div class="data">'
    if not textFormat: print table_start
    print tab_row(tab_head("Input archive: ") + tab_col(getDataFileName(formFields)))
    if printOptions:
        print tab_row(tab_head("Options:"))
        ppOptions()
        ppColumnList()
    if not textFormat:
        print table_end

    if not textFormat:
        print table_start
    print tab_row(tab_head("Results:"))
    print tab_row(ppHeader())

    # Perform and print the analysis on each pair in the zip file.
    for pair_name, A, B in pairs:
        file_A = extract(A)
        file_B = extract(B)
        l, s1, s2 = runAnalysis(pair_name, file_A, file_B)
        print tab_row(ppAnalysis(l) + ppStats(s1, s2))
        os.remove(file_A)
        os.remove(file_B)


    # If there was more than one pair, print a footer
    if len(pairs) > 1:
        print tab_row(ppHeader())
        if not textFormat:
            print table_end
            print "</div>"
    
    # Remove the zip file
    os.remove(fn)


def actionSBSearch(formFields):
    global textFormat
    fn = getDataFile(formFields)
    man="SB"
    oc = ocUtils(man)
    if not textFormat:
        print '<pre>'
    oc.initFromCommandLine(["",fn])
    if not textFormat:
        print '</pre>'
    oc.setDataFile(formFields["datafilename"])
    # unused error? this should get caught by getDataFile() above
    if not formFields.has_key("data") :
        actionForm(formFields, "Missing form fields")
        print "missing data"
        return
    #textFormat = formFields.get("format", "")
    if textFormat:
        oc.setReportSeparator(ocUtils.COMMASEP)
    else:
        oc.setReportSeparator(ocUtils.HTMLFORMAT)
    oc.setSortDir(formFields.get("sortdir", ""))
    levels = formFields.get("searchlevels")
    if levels and levels > 0:
        oc.setSearchLevels(levels)
    width = formFields.get("searchwidth")
    if width and width > 0:
        oc.setSearchWidth(width)
    reportSort = formFields.get("sortreportby", "")
    searchSort = formFields.get("sortby", "")
    inverseFlag = formFields.get("inversenotation", "")
    if inverseFlag:
        oc.setUseInverseNotation(1)
    skipNominalFlag = formFields.get("skipnominal", "")
    if skipNominalFlag:
        oc.setSkipNominal(1)
    functionFlag = formFields.get("functionvalues", "")
    if functionFlag:
        oc.setValuesAreFunctions(1)
    oc.setStartModel(formFields.get("model", "default"))
    refModel = formFields.get("refmodel", "default")
    #specificRefModel = ""
    if refModel == "specific" and formFields.has_key("specificrefmodel"):
        refModel = formFields["specificrefmodel"]
        #specificRefModel = refModel
    elif refModel == "starting":
        refModel = oc.getStartModel()
    oc.setRefModel(refModel)
    oc.searchDir =  formFields.get("searchdir", "default")
    oc.setSearchSortDir(formFields.get("searchsortdir", ""))
    oc.setSearchFilter(formFields.get("searchtype", "all"))
    oc.setAction("SBsearch")
    if formFields["evalmode"] == "bp":
        reportvars = "Level$I, bp_t, bp_h, ddf, bp_lr, bp_alpha, bp_information"
        oc.setNoIPF(true)
        if reportSort == "information": reportSort = "bp_information"
        elif reportSort == "alpha": reportSort = "bp_alpha"
        if searchSort == "information": searchSort = "bp_information"
        elif searchSort == "alpha": searchSort = "bp_alpha"
        if oc.isDirected():
            reportvars += ", bp_cond_pct_dh"
        reportvars += ", bp_aic, bp_bic"
    else:
        reportvars = "Level$I"
        if formFields.get("show_h", ""):
            reportvars += ", h"
        reportvars += ", ddf"
        if formFields.get("show_dlr", ""):
            reportvars += ", lr"
        if formFields.get("show_alpha", "") or searchSort == "alpha" or reportSort == "alpha":
            reportvars += ", alpha"
        reportvars += ", information"
        if oc.isDirected():
            if formFields.get("show_pct_dh", ""):
                reportvars += ", cond_pct_dh"
        if formFields.get("show_aic", "") or searchSort == "aic" or reportSort == "aic":
            reportvars += ", aic"
        if formFields.get("show_bic", "") or searchSort == "bic" or reportSort == "bic":
            reportvars += ", bic"
    if formFields.get("show_incr_a", ""):
        reportvars += ", incr_alpha, prog_id"
    if formFields.get("show_bp", "") and formFields["evalmode"] <> "bp":
        reportvars += ", bp_t"
    if oc.isDirected():
        if formFields.get("show_pct", "") or formFields.get("show_pct_cover", "") or searchSort == "pct_correct_data" or reportSort == "pct_correct_data":
            reportvars += ", pct_correct_data"
            if formFields.get("show_pct_cover", ""):
                reportvars += ", pct_coverage"
            if oc.hasTestData():
                reportvars += ", pct_correct_test"
                if formFields.get("show_pct_miss", ""):
                    reportvars += ", pct_missed_test"
    oc.setReportSortName(reportSort)
    oc.sortName = searchSort
    oc.setReportVariables(reportvars)
    if textFormat:
        oc.doAction(printOptions)
    else:
        print "<hr><p>"
        print '<div class="data">'
        oc.doAction(printOptions)
        print "</div>"
    os.remove(fn)

#
#---- actionShowLog ---- show job log given email
def actionShowLog(formFields):
    email = formFields.get("email", "").lower()
    if email:
        printBatchLog(email)

#---- actionError ---- print error on unknown action
#
def actionError():
    if textFormat:
        print "Error: unknown action"
    else:
        print "<H1>Error: unknown action</H1>"

#---- getFormFields ----
def getFormFields(form):
    formFields = {}
    keys = form.keys()
    for key in keys:
        if key in ['data', 'decls', 'test']:
            formFields[key+'filename'] = form[key].filename
            formFields[key] = form[key].value
        else:
            formFields[key] = form.getfirst(key)
    return formFields


def getUniqueFilename(file_name):
    dirname, filename = os.path.split(file_name)
    prefix, suffix = os.path.splitext(filename)
    prefix = '_'.join(prefix.split())
    fd, filename = tempfile.mkstemp(suffix, prefix+"__", dirname)
    os.chmod(filename, 0660)
    return filename

def getTimestampedFilename(file_name):
    dirname, filename = os.path.split(file_name)
    prefix, suffix = os.path.splitext(filename)
    prefix = '_'.join(prefix.split())
    timestamp = datetime.datetime.now().strftime("%Y_%m_%d-%H_%M_%S")
    filename = os.path.join(dirname, prefix+"_"+timestamp+suffix)
    return filename

#
#---- startBatch ----
#
# Output all the form arguments to a file, and then run the
# script as a command line job
#
def startBatch(formFields):
    if getDataFileName(formFields) == "":
        print "ERROR: No data file specified."
        sys.exit()
    ctlfilename = os.path.join(datadir, getDataFileName(formFields, true) + '.ctl')
    ctlfilename = getUniqueFilename(ctlfilename)
    csvname = getDataFileName(formFields, true) + '.csv'
    datafilename = getDataFileName(formFields)
    toaddress =  formFields["batchOutput"].lower()
    emailSubject = formFields["emailSubject"]
    f = open(ctlfilename, 'w', 0660)
    pickle.dump(formFields, f)
    f.close()
    appname = os.path.dirname(sys.argv[0])
    if not appname: appname = "."
    appname = os.path.join(appname, "occambatch")

    print "Process ID:", os.getpid(), "<p>"

    cmd = 'nohup "%s" "%s" "%s" "%s" "%s" "%s" &' % (appname, sys.argv[0], ctlfilename, toaddress, csvname, emailSubject.encode("hex"))
    os.system(cmd)
    print "<hr>Batch job started -- data file: %s, results will be sent to %s\n" % (datafilename, toaddress)


#
#---- getWebControls ----
#
def getWebControls():
    formFields = getFormFields(cgi.FieldStorage())
    return formFields

#
#---- getBatchControls ----
#
def getBatchControls():
    ctlfile = sys.argv[1]
    f = open(ctlfile, "r")
    formFields = pickle.load(f)
    f.close()
    os.remove(ctlfile)
    # set text mode
    formFields["format"] = "text"
    return formFields

#
#---- printBatchLog ----
#
def printBatchLog(email):
    email = email.lower()
    print "<P>"
    # perhaps we should do some check that this directory exists?
    file = os.path.join("batchlogs", email.lower())
    try:
        f = open(file)
        logcontents = f.readlines()
        theLog = '<BR>'.join(logcontents)
        f.close()
        print theLog
    except:
        print "no log file found for %s<br>" % email

#---- main script ----
#

template = OpagCGI()
datafile = ""
textFormat = ""
printOptions = ""
#thispage = os.environ.get('SCRIPT_NAME', '')
startt = time.time()

# See if this is a batch run or a web server run
argc = len(sys.argv)
if argc > 1:
    formFields = getBatchControls()
    batchEmail = formFields["batchOutput"]
    formFields["batchOutput"] = ""
else:
    formFields = getWebControls()

textFormat = formFields.get("format", "") != ""
if formFields.has_key("batchOutput") and formFields["batchOutput"]:
    textFormat = 0

printHeaders(formFields, textFormat)

if formFields.has_key("printoptions"):
    printOptions = "true"

printTop(template, textFormat)
sys.stdout.flush()
#print sys.executable + "<br>" + platform.python_version() + "<br>"

# If this is not an output page, or reporting a batch job, then print the header form
if not formFields.has_key("data") and not formFields.has_key("email"):
    actionForm(formFields, None)

# If there is an action, and either data or an email address, proceed
if formFields.has_key("action"):
    
    # If this is running from web server, and batch mode requested, then start a background task
    if formFields.has_key("batchOutput") and formFields["batchOutput"]:
        startBatch(formFields)
    else:

        # if any subject line was supplied, print it
        if formFields.has_key("emailSubject") and formFields["emailSubject"]:
            print "Subject line:," + formFields["emailSubject"]

        try:
            if formFields["action"] == "fit" :
                actionFit(formFields)
            elif formFields["action"] == "SBsearch":
                actionSBSearch(formFields)
            elif formFields["action"] == "SBfit":
                actionSBFit(formFields)
            elif formFields["action"] == "fitbatch":
                actionFitBatch(formFields)
            elif formFields["action"] == "search" or formFields["action"] == "advanced":
                actionSearch(formFields)
            elif formFields["action"] == "log":
                actionShowLog(formFields)
            elif formFields["action"] == "compare":
                actionBatchCompare(formFields)
            else:
                actionError()
            printTime(textFormat)
        except:
            pass

if not textFormat:
    printBottom()
    sys.stdout.flush()
    sys.stdout.close()

