SHELL = /bin/sh

test: 
	cd .. && make 

WEB_ROOT = install/web
CL_ROOT = install/cl
PY_INCLUDE = /usr/include/python2.7

HEADERS = \
	include/attrDescs.h \
	include/_Core.h \
	include/Core.h \
	include/Input.h \
	include/ManagerBase.h \
	include/Math.h \
	include/ModelCache.h \
	include/Options.h \
	include/RelCache.h \
	include/Report.h \
	include/SBMManager.h \
	include/SearchBase.h \
	include/Search.h \
	include/VBMManager.h \
	include/Win32.h

CPP_FILES = \
	cpp/AttributeList.cpp \
	cpp/_Core.cpp \
	cpp/Input.cpp \
	cpp/Key.cpp \
	cpp/Makefile \
	cpp/ManagerBase.cpp \
	cpp/Math.cpp \
	cpp/ModelCache.cpp \
	cpp/Model.cpp \
	cpp/occ.cpp \
	cpp/Options.cpp \
	cpp/pyoccam.cpp \
	cpp/Relation.cpp \
	cpp/RelCache.cpp \
	cpp/Report.cpp \
	cpp/ReportPrintConditionalDV.cpp \
	cpp/ReportPrintResiduals.cpp \
	cpp/ReportQsort.cpp \
	cpp/SBMManager.cpp \
	cpp/SearchBase.cpp \
	cpp/Search.cpp \
	cpp/StateConstraint.cpp \
	cpp/Table.cpp \
	cpp/VariableList.cpp \
	cpp/VBMManager.cpp \

CORE_FILES = \
	cpp/occam.so \
	py/occammail.py \
	py/ocutils.py \
	script/occam3 \
	script/occambatch

CL_FILES = \
	cpp/occ \
	py/basic.py \
	py/fit.py \
	py/sbfit.py \
	py/sbsearch.py

WEB_FILES = \
	html/SBfit_cachedform.html \
	html/SBfitform.html \
	html/SBsearch_cachedform.html \
	html/SBsearchform.html \
	html/base.css \
	html/cached_data_doc.html \
	html/compareform.html \
	html/fit_cachedform.html \
	html/fitbatchform.html \
	html/fitform.html \
	html/footer.html \
	html/header.html \
	html/index.html \
	html/logform.html \
	html/search_cachedform.html \
	html/searchform.html \
	py/OpagCGI.py \
	py/jobcontrol.py \
	py/weboccam.py \
   	html/switchform.html \
    html/header.txt \
    html/weboccam.cgi

lib: $(HEADERS) $(CPP_FILES)
	cd cpp && make

install: lib $(WEB_FILES) $(CORE_FILES) $(CL_FILES)
	mkdir -p $(WEB_ROOT)
	mkdir -p $(CL_ROOT)
	cp $(WEB_FILES) $(WEB_ROOT)
	cp $(CORE_FILES) $(WEB_ROOT)
	cp $(CORE_FILES) $(CL_ROOT)
	cp $(CL_FILES) $(CL_ROOT)


