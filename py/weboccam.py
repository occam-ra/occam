#! /usr/bin/env python
# coding=utf-8
# Copyright © 1990 The Portland State University OCCAM Project Team
# [This program is licensed under the GPL version 3 or later.]
# Please see the file LICENSE in the source
# distribution of this software for license terms.


import os, cgi, sys, occam, time, string, pickle, zipfile, datetime, tempfile, cgitb, urllib2, platform, traceback, distanceFunctions

from time import clock
from ocutils import ocUtils
from OpagCGI import OpagCGI
from jobcontrol import JobControl
from common import *
import ocGraph


cgitb.enable(display=1)
VERSION = "3.4.0"
stdout_save = None
# TODO: eliminate the need for this kludgy definition.
false = 0; true = 1

# TODO: check that the 'datadir' directory exists.
# This requires a manual installation step.
# If it does not exist with correct permissions, OCCAM will not run.
datadir = "data"


globalOcInstance = None

def apply_if(predicate, func, val):
    return func(val) if predicate else val

def getDataFileName(formFields, trim=false, key='datafilename'):
    """
    Get the original name of the data file.
    * formFields:   the form data from the user
    * trim:         trim the extension from the filename.
    """
    return '_'.join(apply_if(trim, lambda d : os.path.splitext(d)[0], os.path.split(formFields[key])[1]).split())


def useGfx(formFields):
    return formFields.has_key("onlyGfx") or formFields.has_key("gfx") or formFields.has_key("gephi")

csvname = ""

def printHeaders(formFields, textFormat):
    if textFormat:
        global csvname
        origcsvname = getDataFileName(formFields, true) + ".csv"
        csvname = getUniqueFilename("data/"+origcsvname)
        if useGfx(formFields):
            # REDIRECT OUTPUT FOR NOW (it will be printed in outputZipfile())
            print "Content-type: application/octet-stream"
            print "Content-disposition: attachment; filename=" + getDataFileName(formFields, true) + ".zip"
            print ""
            sys.stdout.flush()
            
            global stdout_save
            stdout_save = os.dup(1)
            csv = os.open(csvname, os.O_WRONLY)
            os.dup2(csv, 1)
            os.close(csv)

        else:
            print "Content-type: application/octet-stream"
            print "Content-disposition: attachment; filename=" + origcsvname
        

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

def attemptParseInt(string, default, msg, verbose):
    # for now: the fields aren't even displayed...
    verbose = False

    try:
        return int(string)

    except ValueError:
        if verbose:
            print ("WARNING: expected " + msg + " to be an integer value, but got: \"" + string + "\"; using the default value, " + str(default) + "\n")
            if not textFormat:
                print "<br>"
        
        return default

def graphWidth():
    return attemptParseInt(formFields.get("graphWidth", ""), 640, "hypergraph image width", formFields.has_key("gfx"))
    


def graphHeight():
    return attemptParseInt(formFields.get("graphHeight", ""), 480, "hypergraph image height", formFields.has_key("gfx"))

def graphFontSize():
    return attemptParseInt(formFields.get("graphFontSize", ""), 12, "hypergraph font size", formFields.has_key("gfx"))

def graphNodeSize():
    return attemptParseInt(formFields.get("graphNodeSize", ""), 24, "hypergraph node size", formFields.has_key("gfx"))

# Take the captured standard output,
# and the generated graphs, and roll them into a ZIP file.
def outputToZip(oc):
    global stdout_save
    global csvname

    # Make an empty zip file
    zipname = "data/" + getDataFileName(formFields, true) + ".zip"
    z = zipfile.ZipFile(zipname, "w")
    

    sys.stdout.flush()
    # Write out each graph to a PDF; include a brief note in the CSV.
    for modelname,graph in oc.graphs.items():
        modelname = modelname.replace(":","_")

        if formFields.has_key("gfx"):
            filename = modelname + ".pdf"
            print "Writing graph to " + filename
            graphFile = ocGraph.printPDF(modelname, graph, formFields["layout"], graphWidth(), graphHeight(), graphFontSize(), graphNodeSize())
            z.write(graphFile, filename)
            sys.stdout.flush()
 
 
        if formFields.has_key("gephi"):
            nodename = modelname + ".nodes_table.csv"
            print "Writing Gephi Node table file to " + nodename
            nodetext = ocGraph.gephiNodes(graph)
            nodefile = getUniqueFilename("data/"+nodename)
            with open(nodefile, "w") as nf:
                nf.write(nodetext)
            z.write(nodefile, nodename)
 
            edgename = modelname + ".edges_table.csv"
            print "Writing Gephi Edges table file to " + edgename
            edgetext = ocGraph.gephiEdges(graph)
            edgefile = getUniqueFilename("data/"+edgename)
            with open(edgefile, "w") as ef:
                ef.write(edgetext)
            z.write(edgefile, edgename)           
            sys.stdout.flush()

    # Restore the STDOUT handle 
    sys.stdout = os.fdopen(stdout_save, 'w')

    # Write the CSV to the ZIP
    z.write(csvname, getDataFileName(formFields, true) + ".csv")
    z.close() 

    # print out the zipfile
    handle = open(zipname)
    contents = handle.read()
    print contents
    sys.stdout.flush()

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

    # define sets of legitimate actions
    common_actions = {"fit", "search", "SBsearch", "SBfit"}
    form_actions = {"compare", "log", "fitbatch"}
    jobcontrol_action = {"jobcontrol"}  # excessive but consistent

    # the union of these sets is the allowable list of actions
    valid_actions = common_actions | form_actions | jobcontrol_action

    # the user provided action is untrustable
    untrusted_action = formFields.get("action", "")

    # validate the action by checking for it's presence in the allowlist
    if untrusted_action not in valid_actions:
        action = untrusted_action
    else:
        # exit if the action is invalid
        actionError()
        return

    formatText = ""
    if formFields.has_key("formatText"): formFields['formatText'] = "checked"
    template.set_template('switchform.html')
    template.out(formFields)

    
    if action in common_actions:

        template.set_template("formheader.html")
        template.out(formFields)

        cached = formFields.get("cached", "")
        
        if cached == "true":
            template.set_template("cached_data.template.html")
            template.out(formFields)
        else:
            template.set_template("data.template.html")
            template.out(formFields)
       
        template.set_template(action+".template.html")
        template.out(formFields)
        template.set_template("output.template.html")
        template.out(formFields)
        
        template.set_template(action+".footer.html")
        template.out(formFields)

    elif action in form_actions:
        template.set_template(action+"form.html")
        template.out(formFields)

    if action == "jobcontrol":
        JobControl().showJobs(formFields)

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
        print "NOTE: Exactly 1 of 'Data File' and 'Cached Data Name' must be filled out."
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

def processFit(fn, model, negativeDVforConfusion, oc, onlyGfx):
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
    oc.doAction(printOptions, onlyGfx)

    if not textFormat:
        print "</span>"

#
#---- processSBFit ---- Do state based fit operation
#
def processSBFit(fn, model, negativeDVforConfusion, oc, onlyGfx):
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
    oc.doAction(printOptions, onlyGfx)

def maybeSkipResiduals(formFields, oc):
    skipResidualsFlag = formFields.get("skipresiduals", "")
    if skipResidualsFlag:
        oc.setSkipTrainedModelTable(1)
    else:
        oc.setSkipTrainedModelTable(0)
 
def maybeSkipIVIs(formFields, oc):
    skipResidualsFlag = formFields.get("skipivitables", "")
    if skipResidualsFlag:
        oc.setSkipIVITables(1)
    else:
        oc.setSkipIVITables(0)

#
#---- actionFit ---- Report on Fit
#
def handleGraphOptions(oc, formFields):
    if useGfx(formFields):
        lo = formFields["layout"]
        oc.setGfx(formFields.has_key("gfx"),layout=lo,gephi=formFields.has_key("gephi"),hideIV=formFields.has_key("hideIsolated"),hideDV=formFields.has_key("hideDV"), fullVarNames=formFields.has_key("fullVarNames"), width=graphWidth(), height=graphHeight(), fontSize=graphFontSize(), nodeSize=graphNodeSize())


def actionFit(formFields):
    global textFormat

    fn = getDataFile(formFields)
    oc = ocUtils("VB")
    global globalOcInstance
    globalOcInstance = oc
    if not textFormat:
        print '<pre>'
    oc.initFromCommandLine(["",fn])
    if not textFormat:
        print '</pre>'
    oc.setDataFile(formFields["datafilename"])
    handleGraphOptions(oc, formFields)
    

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

    maybeSkipResiduals(formFields, oc)
    maybeSkipIVIs(formFields, oc)
   
    if not formFields.has_key("data") or not formFields.has_key("model") :
        actionNone(formFields, "Missing form fields")
        return
    onlyGfx = formFields.has_key("onlyGfx")
    processFit(fn, formFields["model"], target, oc, onlyGfx) 
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
    global globalOcInstance
    globalOcInstance = oc
    if not textFormat:
        print '<pre>'
    oc.initFromCommandLine(["",fn])
    if not textFormat:
        print '</pre>'
    oc.setDataFile(formFields["datafilename"])
    handleGraphOptions(oc, formFields)
#functionFlag = formFields.get("functionvalues", "")
#if functionFlag:
#oc.setValuesAreFunctions(1)
    if not formFields.has_key("data") or not formFields.has_key("model") :
        actionNone(formFields, "Missing form fields")
        os.remove(fn)
        return
    skipNominalFlag = formFields.get("skipnominal", "")
    if skipNominalFlag:
        oc.setSkipNominal(1)
    
    maybeSkipResiduals(formFields, oc)
    maybeSkipIVIs(formFields, oc)

    target = formFields["negativeDVforConfusion"] if formFields.has_key("negativeDVforConfusion") else ""


    onlyGfx = formFields.has_key("onlyGfx")
    processSBFit(fn, formFields["model"], target, oc, onlyGfx) 
    os.remove(fn)


#
#---- processSearch ---- Do search operation
#
def actionSearch(formFields):
    global textFormat
    fn = getDataFile(formFields)
    man="VB"
    oc = ocUtils(man)
    global globalOcInstance
    globalOcInstance = oc
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

## INTENTIONALLY COMMENTED OUT CODE IN THIS MULTILINE STRING!!!
## This code handles the backpropagation-based evaluation,
## but it is not currently used (and the HTML forms do not define "evalmode"
## so it will crash!!)
    disabledBPCode = """
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
    """
    if False: pass
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

## INTENTIONALLY COMMENTED OUT CODE IN THIS MULTILINE STRING!!!
## This code handles the backpropagation-based evaluation,
## but it is not currently used (and the HTML forms do not define "evalmode"
## so it will crash!!)
    disabledBPCode = """
    if formFields.get("show_bp", "") and formFields["evalmode"] <> "bp":
        reportvars += ", bp_t"
    """

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
                headers.append(i + "(model(A) : model(B))")
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
    tab_col = lambda s: bracket(s, "<td>", "</td>", " ", ",")
    tab_head = lambda s: bracket(s, "<th align=left>", "</th>", " ", ",")

    table_start = "<br><table border=0 cellpadding=0 cellspacing=0>"
    table_end = "</table>"


    def computeBestModel(filename): 
        oc = ocUtils("VB")
        global globalOcInstance
        globalOcInstance = oc
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

    def computeBinaryStatistics(report_items, comp_order):
        stats = dict([(k, distanceFunctions.computeDistanceMetric(k, comp_order)) for k in report_items])
        return stats


    def computeModelStats(model_A, model_B):
        stats_1 = dict([(k,[model_A[k],model_B[k]]) for k in report_1])
        best = "unknown"

#        # Find the best model based on the single-model stats
        best_d, best_s = selectBest(stats_1)       
        a, b  = stats_1[best_s]
        best = ""
        if best_d == -1:
            best = "A" if a <= b else "B"
        elif best_d == 1:
            best = "A" if a >= b else "B"
        comp_order = [model_A, model_B] if best == "A" else [model_B, model_A]
        stats_2 = computeBinaryStatistics(report_2, comp_order)

        return best, stats_1, stats_2


    def runAnalysis(pair_name, file_A, file_B): 
        model_A = computeBestModel(file_A)
        model_B = computeBestModel(file_B)
        model_A["filename"] = pair_name + "A.txt"
        model_B["filename"] = pair_name + "B.txt"

        best, stats_1, stats_2 = computeModelStats(model_A, model_B)
        return ([pair_name, model_A["name"], model_B["name"], best], stats_1, stats_2)

    
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

    # Perform and print the analysis on each pair in the zip file.
    sys.stdout.write("Running searches")
    results = []
    for pair_name, A, B in pairs:
        file_A = extract(A)
        file_B = extract(B)
        l, s1, s2 = runAnalysis(pair_name, file_A, file_B)
        results.append([l, s1, s2])
        os.remove(file_A)
        os.remove(file_B)
    print
    print "Searches completed. "
    
    if not textFormat:
        print table_start
    print tab_row(tab_head("Comparison Results:"))
    print tab_row(ppHeader())
    
    for res in results:
        print tab_row(ppAnalysis(res[0]) + ppStats(res[1], res[2]))

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
    global globalOcInstance
    globalOcInstance = oc
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

## INTENTIONALLY COMMENTED OUT CODE IN THIS MULTILINE STRING!!!
## This code handles the backpropagation-based evaluation,
## but it is not currently used (and the HTML forms do not define "evalmode"
## so it will crash!!)
    disabledBPCode = """
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
    """
    if False: pass
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


## INTENTIONALLY COMMENTED OUT CODE IN THIS MULTILINE STRING!!!
## This code handles the backpropagation-based evaluation,
## but it is not currently used (and the HTML forms do not define "evalmode"
## so it will crash!!)
    disabledBPCode = """
    if formFields.get("show_bp", "") and formFields["evalmode"] <> "bp":
        reportvars += ", bp_t"
    """

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

    print "<hr>Batch job started for data file '%s'.<br>Results will be sent to '%s'" % (datafilename, toaddress)

    if len(emailSubject) > 0:
        print " with email subject line including '%s'." % emailSubject
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

def startNormal(formFields):
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
        elif formFields["action"] == "jobcontrol":
            pass
        else:
            actionError()

        printTime(textFormat)
    except Exception as e:
        if isinstance(e, KeyError) and str(e) == "'datafilename'":
            pass
        else:
            if not textFormat:
                print "<br><hr>"
            print "FATAL ERROR: " + str(e)
            if not textFormat:
                print "<br>"
            print "This error was not expected by the programmer. "
            print "For help, please contact h.forrest.alexander@gmail.com, and include the output so far "
            ex_type, ex, tb = sys.exc_info()
            traceback.print_tb(tb)
            print "(end error message)."


def finalizeGfx():
    global globalOcInstance
    if useGfx(formFields) and textFormat:
        outputToZip(globalOcInstance)
        sys.stdout.flush()

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

if formFields.has_key("batchOutput") and formFields["batchOutput"]:
    textFormat = 0

    r1 = formFields.pop('gfx', None)
    r2 = formFields.pop('gephi', None)
    t = (r1 != None) or (r2 != None)
    if t:
        print "Note: Occam's email server interacts with graph output in a way that currently results in an error; graph functionality is temporarily disabled. The programmer is working on a fix...<br><hr>"

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
        startNormal(formFields)

finalizeGfx()

if not textFormat:
    printBottom()
    sys.stdout.flush()
    sys.stdout.close()

