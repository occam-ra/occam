# Copyright © 1990 The Portland State University OCCAM Project Team
# [This program is licensed under the GPL version 3 or later.]
# Please see the file LICENSE in the source
# distribution of this software for license terms.

SHELL = /bin/sh

INSTALL_ROOT = install
WEB_ROOT = $(INSTALL_ROOT)/web
CL_ROOT = $(INSTALL_ROOT)/cl
PACKAGE_ROOT = $(INSTALL_ROOT)/occampy
CAPSTONE_ROOT = py/occampy

HEADERS = \
	include/attrDescs.h			\
	include/AttributeList.h		\
	include/Constants.h			\
	include/_Core.h				\
	include/Globals.h			\
	include/Input.h				\
	include/Key.h				\
	include/ManagerBase.h		\
	include/Math.h				\
	include/ModelCache.h		\
	include/Model.h				\
	include/Options.h			\
	include/Relation.h			\
	include/RelCache.h			\
	include/Report.h			\
	include/SBMManager.h		\
	include/SearchBase.h		\
	include/Search.h			\
	include/StateConstraint.h	\
	include/Table.h				\
	include/Types.h				\
	include/Variable.h			\
	include/VariableList.h		\
	include/VarIntersect.h		\
	include/VBMManager.h

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
	cpp/pyoccam3.cpp \
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

CORE_FILES_PY2 = \
	cpp/occam.so \
	py/py2/occammail.py \
	py/py2/common.py \
	py/py2/ocutils.py \
	py/py2/distanceFunctions.py \
	py/py2/ocGraph.py

CORE_FILES_PY3 = \
	cpp/occam3.so \
	py/py3/occammail.py \
	py/py3/common.py \
	py/py3/ocutils.py \
	py/py3/distanceFunctions.py \
	py/py3/ocGraph.py

SETUP_FILE = \
		py/py3/setup.py

CL_FILES_PY2 = \
	cpp/occ \
	py/py2/basic.py \
	py/py2/fit.py \
	py/py2/sbfit.py \
	py/py2/sbsearch.py

CL_FILES_PY3 = \
	cpp/occ \
	py/py3/basic.py \
	py/py3/fit.py \
	py/py3/sbfit.py \
	py/py3/sbsearch.py

WEB_FILES = \
	html/.htaccess \
	html/occam_logo.jpg \
	html/base.css \
	html/footer.html \
	html/header.html \
	html/index.html \
	py/py2/OpagCGI.py \
	py/py2/jobcontrol.py \
	py/py2/weboccam.py \
	html/switchform.html \
	html/header.txt \
	html/formheader.html \
	html/fitbatchform.html \
	html/compareform.html \
	html/logform.html \
	html/weboccam.cgi \
	html/output.template.html \
	html/cached_data.template.html \
	html/data.template.html \
	html/fit.template.html \
	html/fit.footer.html \
	html/search.template.html \
	html/search.footer.html \
	html/SBfit.template.html \
	html/SBfit.footer.html \
	html/SBsearch.template.html \
	html/SBsearch.footer.html \
	html/compare.template.html \
	html/compare.footer.html \
	html/occambatch

CAPSTONE_FILES_PY2 = \
	$(CAPSTONE_ROOT)2/*.py \
	$(CAPSTONE_ROOT)2/wrappers

CAPSTONE_FILES_PY3 = \
	$(CAPSTONE_ROOT)3/*.py \
	$(CAPSTONE_ROOT)3/wrappers

install: lib $(WEB_FILES) $(CORE_FILES_PY2) $(CL_FILES_PY2) $(CAPSTONE_FILES_PY2) $(CAPSTONE_FILES_PY3) $(SETUP_FILE)
	-rm -rf $(INSTALL_ROOT)
	mkdir -p $(INSTALL_ROOT)
	make web
	make cli
	make occampy
	cp $(SETUP_FILE) $(INSTALL_ROOT)
	touch cpp/__init__.py

web:
	mkdir -p $(WEB_ROOT)
	cp $(WEB_FILES) $(CORE_FILES_PY2) $(WEB_ROOT)
	touch $(WEB_ROOT)/__init__.py

cli:
	mkdir -p $(CL_ROOT)
	cp $(CL_FILES_PY2) $(CORE_FILES_PY2) $(CL_ROOT)
	touch $(CL_ROOT)/__init__.py

occampy:
	mkdir -p $(PACKAGE_ROOT)2 $(PACKAGE_ROOT)3
	cp -r $(CAPSTONE_FILES_PY2) $(PACKAGE_ROOT)2
	cp cpp/occam.so $(PACKAGE_ROOT)2/wrappers/occam.so
	cp -r $(CAPSTONE_FILES_PY3) $(PACKAGE_ROOT)3
	cp cpp/occam3.so $(PACKAGE_ROOT)3/wrappers/occam.so


lib: $(HEADERS) $(CPP_FILES)
	cd cpp && make

clean:
	cd cpp && make clean
	-rm -rf $(INSTALL_ROOT)
