#! python

import os, cgi, sys, occam, time, string, pickle, zipfile, datetime, tempfile
import cgitb; cgitb.enable(display=1)

from ocutils import ocUtils
#from time import clock
from OpagCGI import OpagCGI
from jobcontrol import JobControl
#import urllib2
#import platform, traceback

VERSION = "3.3.6"

false = 0; true = 1
# perhaps we should do some check that this directory exists?
datadir = "data"

#
#---- getDataFileName -- get the original name of the data file
#
def getDataFileName(formFields, trim=false):
    # extract the file name (minus directory) and seed the download dialog with it
    # we have to handle both forward and backward slashes here.
    datafile = formFields['datafilename']
    if string.find(datafile, "\\") >= 0:
        datapath = string.split(datafile, "\\")
    else:
        datapath = string.split(datafile, "/")
    datafile = datapath[len(datapath)-1]
    #datafile = os.path.basename(formFields['datafilename'])
    if trim:
        datafile = os.path.splitext(datafile)[0]
    return datafile

#
#---- printHeaders ---- Print HTTP Headers
#
def printHeaders(formFields, textFormat):
    if textFormat:
        datafile = getDataFileName(formFields, true)
        datafile += ".csv"
        print "Content-type: application/octet-stream"
        print "Content-disposition: attachment; filename=" + datafile
    else:
        print "Content-type: text/html"
    print ""

#
#---- printTop ---- Print top HTML part
#
def printTop(template, textFormat):
    if textFormat:
        template.set_template('header.txt')
    else:
        template.set_template('header.html')
    args = {'version':VERSION,'date':datetime.datetime.now().strftime("%c")}
    template.out(args)

#
#---- printTime ---- Print elapsed time
#
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
    datafile = formFields.get("datafile", "")
    model = formFields.get("model", "")
    specificRefModel = formFields.get("specificrefmodel")

    formatText = ""
    if formFields.has_key("formatText"): formFields['formatText'] = "checked"
    template.set_template('switchform.html')
    template.out(formFields)

    if action == "fit":
        template.set_template('fitform.html')
        template.out(formFields)

    elif action == "search" or action == "advanced" :
        template.set_template('searchform.html')
        template.out(formFields)
    
    elif action == "SBsearch":
        template.set_template('SBsearchform.html')
        template.out(formFields)
        
    elif action == "SBfit":
        template.set_template('SBfitform.html')
        template.out(formFields)
        
    elif action == "fitbatch":
        template.set_template('fitbatchform.html')
        template.out(formFields)
        
    elif action == "showlog":
        template.set_template('logform.html')
        template.out(formFields)

    elif action == "jobcontrol":
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
def getDataFile(formFields):
    datafile = os.path.join(datadir, getDataFileName(formFields))
    try:
        outf = open(datafile, "w", 0777)
        data = formFields["data"]
        outf.write(data)
        outf.close()
    except:
        if getDataFileName(formFields) == "":
            print "ERROR: No data file specified."
        else:
            print "ERROR: Problems reading data file %s." % datafile
        sys.exit()
    # If it appears to be a zipfile, unzip it
    if os.path.splitext(datafile)[1] == ".zip":
        zipdata = zipfile.ZipFile(datafile)
        # ignore any directories or files in them, such as those OSX likes to make
        ilist = [item for item in zipdata.infolist() if item.filename.find("/") == -1]
        # make sure there is only one file left
        if len(ilist) != 1:
            print "ERROR: Zip file can only contain one data file. (It appears to contain %d.)" % len(ilist)
            sys.exit()
        # try to extract the file
        try:
            datafile = os.path.join(datadir, ilist[0].filename)
            outf = open(datafile, "w")
            outf.write(zipdata.read(ilist[0].filename))
            outf.close()
        except:
            print "ERROR: Extracting zip file failed."
            sys.exit()
    return datafile

#
#---- processFit ---- Do fit operation
#
def processFit(fn, model, oc):
    global datafile, textFormat, printOptions

    if textFormat:
        oc.setReportSeparator(ocUtils.COMMASEP)
    else:
        print '<div class="data">'
        oc.setReportSeparator(ocUtils.HTMLFORMAT)

    if model <> "":
        oc.setFitModel(model)
    oc.setAction("fit")
    oc.doAction(printOptions)

    if not textFormat:
        print "</span>"

#
#---- processSBFit ---- Do state based fit operation
#
def processSBFit(fn, model, oc):
    global datafile, textFormat, printOptions


    if textFormat:
        oc.setReportSeparator(ocUtils.COMMASEP)
    else:
        print '<div class="data">'
        oc.setReportSeparator(ocUtils.HTMLFORMAT)

    if model <> "":
        oc.setFitModel(model)
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

    if not formFields.has_key("data") or not formFields.has_key("model") :
        actionNone(formFields, "Missing form fields")
        return
    processFit(fn, formFields["model"], oc)

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
#model = formFields["model"]
#   if textFormat:
    processSBFit(fn, formFields["model"], oc)
#else:
#       print "<span class=mono>"
#       processSBFit(fn, model, oc)
#       print "</span>"

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
    if formFields["datafilename"] != os.path.split(fn)[1]:
        oc.setDataFile(os.path.split(fn)[1] + " (from: \"" + formFields["datafilename"] + "\")")
    else:
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
    if refModel == "specific" and formFields.has_key("specificrefmodel"):
        refModel = formFields["specificrefmodel"]
        #specificRefModel = refModel
    elif refModel == "starting":
        refModel = oc.getStartModel()
    oc.setRefModel(refModel)
    oc.setSearchDir(formFields.get("searchdir", "default"))
    oc.setSearchSortDir(formFields.get("searchsortdir", ""))
    oc.setSearchFilter(formFields.get("searchtype", "all"))
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
    if formFields.get("show_pct", "") or formFields.get("show_pct_cover", "") or searchSort == "pct_correct_data" or reportSort == "pct_correct_data":
        reportvars += ", pct_correct_data"
        if formFields.get("show_pct_cover", ""):
            reportvars += ", pct_coverage"
        if oc.hasTestData():
            reportvars += ", pct_correct_test"
            if formFields.get("show_pct_miss", ""):
                reportvars += ", pct_missed_test"
    oc.setReportSortName(reportSort)
    oc.setSortName(searchSort)
    oc.setReportVariables(reportvars)
    if textFormat:
        oc.doAction(printOptions)
    else:
        print "<hr><p>"
        print '<div class="data">'
        oc.doAction(printOptions)
        print "</div>"

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
    if formFields["datafilename"] != os.path.split(fn)[1]:
        oc.setDataFile(os.path.split(fn)[1] + " (from: \"" + formFields["datafilename"] + "\")")
    else:
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
    oc.setSearchDir(formFields.get("searchdir", "default"))
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
    if formFields.get("show_pct", "") or formFields.get("show_pct_cover", "") or searchSort == "pct_correct_data" or reportSort == "pct_correct_data":
        reportvars += ", pct_correct_data"
        if formFields.get("show_pct_cover", ""):
            reportvars += ", pct_coverage"
        if oc.hasTestData():
            reportvars += ", pct_correct_test"
            if formFields.get("show_pct_miss", ""):
                reportvars += ", pct_missed_test"
    oc.setReportSortName(reportSort)
    oc.setSortName(searchSort)
    oc.setReportVariables(reportvars)
    if textFormat:
        oc.doAction(printOptions)
    else:
        print "<hr><p>"
        print '<div class="data">'
        oc.doAction(printOptions)
        print "</div>"
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
        if key == 'data':
            formFields['datafilename'] = form[key].filename
            formFields['data'] = form[key].value
        else:
            formFields[key] = form.getfirst(key)
    return formFields


def getUniqueFilename(file_name):
    dirname, filename = os.path.split(file_name)
    prefix, suffix = os.path.splitext(filename)

    fd, filename = tempfile.mkstemp(suffix, prefix+"_", dirname)
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
    f = open(ctlfilename, 'w', 0777)
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
        theLog = string.join(logcontents, '<BR>')
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

#print sys.executable + "<br>" + platform.python_version() + "<br>"

# If this is not an output page, or reporting a batch job, then print the header form
if not formFields.has_key("data") and not formFields.has_key("email"):
    actionForm(formFields, None)

# If there is an action, and either data or an email address, proceed
if formFields.has_key("action") and ( formFields.has_key("data") or formFields.has_key("email") ) :
    
    # If this is running from web server, and batch mode requested, then start a background task
    if formFields.has_key("batchOutput") and formFields["batchOutput"]:
        startBatch(formFields)
    else:
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
            elif formFields["action"] == "showlog":
                actionShowLog(formFields)
            else:
                actionError()
            printTime(textFormat)
        except:
            pass

if not textFormat:
    printBottom()

