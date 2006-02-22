#! /pkg/python/bin/python

import os, sys, cgi, sys, occam,time, string, traceback, pickle
from ocutils import ocUtils
from time import clock
from OpagCGI import OpagCGI
from jobcontrol import JobControl

VERSION = "3.2.19"

false = 0; true = 1
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
	if trim:
		datafile = os.path.splitext(datafile)[0]
	return datafile

#
#---- printHeaders ---- Print HTTP Headers
#
def printHeaders(formFields, textFormat):
	if textFormat:
		datafile = getDataFileName(formFields, true)
		datafile = datafile + ".csv"
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
	args = {'version':VERSION}
	template.out(args)
#
#---- printTime ---- Print elapsed time
#
def printTime(startTime, textFormat):
	now=time.time();
	elapsed_t=now-startt
	#elapsed = clock() - startTime;
	if textFormat:
		 if elapsed_t>0:
                        print "Run time: %f seconds\n" % elapsed_t
	else:
		if elapsed_t>0:
                        print "<br>Run time: %f seconds</br>" % elapsed_t


#
#---- printBottom ---- Print bottom HTML part
#
def printBottom():
	print """
	</body>
	</html>
	"""

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

	#---- This form section for fit only
	if action == "fit":
		template.set_template('fitform.html')
		template.out(formFields)

	#---- This section for search only
	elif action == "search" or action == "advanced" :
		template.set_template('searchform.html')
		template.out(formFields)
	
	elif action == "SBfit":
		template.set_template('SBfitform.html')
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
	datafile = datadir + "/" + getDataFileName(formFields, false)
	try:
		outf = open(datafile, "w")
		data = formFields["data"]
		outf.write(data)
		outf.close()
	except:
		print "Error: problems reading data file %s" % datafile
		traceback.print_exc(file=sys.stdout)
	return datafile

#
#---- processFit ---- Do fit operation
#
def processFit(fn, model, oc):
	global datafile, textFormat, printOptions


	if textFormat:
		oc.setReportSeparator(ocUtils.COMMASEP)
	else:
		oc.setReportSeparator(ocUtils.HTMLFORMAT)

	if model <> "":
		oc.setFitModel(model)
	oc.setAction("fit")
	oc.doAction(printOptions)

#
#---- processSBFit ---- Do state based fit operation
#
def processSBFit(fn, model, oc):
	global datafile, textFormat, printOptions


	if textFormat:
		oc.setReportSeparator(ocUtils.COMMASEP)
	else:
		oc.setReportSeparator(ocUtils.HTMLFORMAT)

	if model <> "":
		oc.setFitModel(model)
	oc.setAction("SBfit")
	oc.doAction(printOptions)
#
#---- actionFit ---- Report on Fit
#
def actionFit(formFields):
	global textFormat, calcExpectedDV

	fn = getDataFile(formFields)
	man="VB"
	oc = ocUtils(man)
	oc.initFromCommandLine(["",fn])
	oc.setDataFile(formFields["datafilename"])
	oc.setCalcExpectedDV(calcExpectedDV)

	if not formFields.has_key("data") or not formFields.has_key("model") :
		actionNone(formFields, "Missing form fields")
		return
	model = formFields["model"]

	if textFormat:
		processFit(fn, model, oc)
	else:
		print "<span class=mono>"
		processFit(fn, model, oc)
		print "</span>"

#
#---- actionSBFit ---- Report on Fit
#
def actionSBFit(formFields):
	global textFormat

	fn = getDataFile(formFields)
	man="SB"
	oc = ocUtils(man)
	oc.initFromCommandLine(["",fn])
	oc.setDataFile(formFields["datafilename"])

	if not formFields.has_key("data") or not formFields.has_key("model") :
		actionNone(formFields, "Missing form fields")
		return
	model = formFields["model"]

	if textFormat:
		processSBFit(fn, model,oc)
	else:
		print "<span class=mono>"
		processSBFit(fn, model, oc)
		print "</span>"
#
#---- processSearch ---- Do search operation
#
def actionSearch(formFields):

	fn = getDataFile(formFields)
	man="VB"
	oc = ocUtils(man)
	oc.initFromCommandLine(["",fn])
	oc.setDataFile(formFields["datafilename"])

	if not formFields.has_key("data") :
		actionForm(form, "Missing form fields")
		print "missing data"
		return
	textFormat = formFields.get("format", "")
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

	oc.setStartModel(formFields.get("model", "default"))

	refModel = formFields.get("refmodel", "default")
	specificRefModel = ""
	if refModel == "specific" and form.has_key("specificrefmodel"):
		refModel = formFields["specificrefmodel"]
		specificRefModel = refModel
	elif refModel == "starting":
		refModel = oc.getStartModel()
	oc.setRefModel(refModel)

	oc.setSearchDir(formFields.get("searchdir", "default"))
	oc.setSearchSortDir(formFields.get("searchsortdir", ""))

	oc.setSearchFilter(formFields.get("searchtype", "all"))
	oc.setAction("search")

	if formFields["evalmode"] == "bp":
		reportvars = "Level$I, bp_t, bp_h, ddf, bp_lr, bp_alpha, bp_information"
                #********** Junghan
                #**********  new bp_aic & bp_bic
                reportvars = "Level$I, bp_t, bp_h, ddf, bp_lr, bp_alpha, bp_information"
		oc.setNoIPF(true)
 		if reportSort == "information": reportSort = "bp_information"
		elif reportSort == "alpha": reportSort = "bp_alpha"
 		if searchSort == "information": searchSort = "bp_information"
		elif searchSort == "alpha": searchSort = "bp_alpha"
		if oc.isDirected():
			reportvars = reportvars + ", bp_cond_pct_dh"
		reportvars = reportvars + ", bp_aic, bp_bic"	#********** Junghan : attach aic & bic
	else:
		reportvars = "Level$I, h, ddf, lr, alpha, information"
		if oc.isDirected():
			reportvars = reportvars + ", cond_pct_dh"
		reportvars = reportvars + ", aic, bic"	#********** Junghan : attach aic & bic
			
	if formFields.get("showbp", "") and formFields["evalmode"] <> "bp":
		reportvars = reportvars + ", bp_t"

	if formFields.get("showpct", ""):
		reportvars = reportvars + ", pct_correct_data"
		if oc.hasTestData(): reportvars = reportvars + ", pct_correct_test"

	oc.setReportSortName(reportSort)
 	oc.setSortName(searchSort)
	oc.setReportVariables(reportvars)

	if textFormat:
		oc.doAction(printOptions)
	else:
		print "<table>"
		print "</table><hr><p>"
		print "<div class=data>"
		oc.doAction(printOptions)
		print "</div>"

#
#---- actionShowLog ---- show job log given email
def actionShowLog(formFields):
	email = formFields.get("email", "")
	if email:
		printBatchLog(email)
#
#---- actionError ---- print error on unknown action
#
def actionError():
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
			formFields[key] = form[key].value
	return formFields
		
#
#---- startBatch ----
#
# Output all the form arguments to a file, and then run the
# script as a command line job
#
def startBatch(formFields):
	ctlfilename = datadir + '/' + getDataFileName(formFields, true) + '.ctl'
	csvname = getDataFileName(formFields, true) + '.csv'
	datafilename = getDataFileName(formFields, false)
	toaddress =  formFields["batchOutput"]
	f = open(ctlfilename, 'w', 0777)
	pickle.dump(formFields, f)
	f.close()
	dirname = os.path.dirname(sys.argv[0])
	if not dirname: dirname = "."

	print "Process ID: ", os.getpid(), "<p>"

	cmd = "nohup %s/occambatch %s %s %s %s &" % (dirname, sys.argv[0], ctlfilename, toaddress, csvname)
	print "<hr>Batch job started -- data file: %s, results will be sent to %s\n" % (datafilename, toaddress)
	result = os.system(cmd)


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
	# set text mode, clear batch mode (so we don't recurse)
	formFields["format"] = "text"
	formFields["batchOutput"] = ""
	f.close()
	return formFields

#
#---- printBatchLog ----
#
def printBatchLog(email):
	print "<P>"
	file = "batchlogs/" + email
	try:
		f = open(file)
		logcontents = f.readlines()
		theLog = string.join(logcontents, '<BR>')
		f.close
		print theLog
	except:
		print "no log file found for %s<br>" % email

#---- main script ----
#

template = OpagCGI()
datafile = ""
textFormat = ""
printOptions = ""
calcExpectedDV = 0
thispage = os.environ.get('SCRIPT_NAME', '')
startTime = clock()
startt=time.time()

# See if this is a batch run or a web server run
argc = len(sys.argv)
if argc > 1:
	formFields = getBatchControls()
else:
	formFields = getWebControls()

textFormat = formFields.get("format", "") != ""

printHeaders(formFields, textFormat)

if formFields.has_key("printoptions"):
	printOptions = "true"

if formFields.has_key("calcExpectedDV"):
	calcExpectedDV = 1

printTop(template, textFormat)

if not formFields.has_key("data") and not formFields.has_key("email"):
	actionForm(formFields, None)

if formFields.has_key("action") and ( formFields.has_key("data") or formFields.has_key("email") ) :
	
# If this is running from web server, and batch mode requested, then
# start a background task
	if formFields.has_key("batchOutput") and formFields["batchOutput"]:
		startBatch(formFields)
	else:
		try:
			if formFields["action"] == "fit" :
				actionFit(formFields)
			elif formFields["action"] == "SBfit":
				actionSBFit(formFields)
			elif formFields["action"] == "search" or formFields["action"] == "advanced":
				actionSearch(formFields)
			elif formFields["action"] == "showlog":
				actionShowLog(formFields)
			else:
				actionError()
		except:
			print "ERROR99"
			traceback.print_exc(file=sys.stdout)
	#		xfile = open('/tmp/except.log', 'w')
	#		traceback.print_exc(file=xfile)
	#		os.close(xfile)
		printTime(startTime, textFormat)

if not textFormat:
	printBottom()

