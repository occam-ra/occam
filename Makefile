# Copyright © 1990 The Portland State University OCCAM Project Team
# [This program is licensed under the GPL version 3 or later.]
# Please see the file LICENSE in the source
# distribution of this software for license terms.

SHELL = /bin/sh

INSTALL_ROOT = install
WEB_ROOT = $(INSTALL_ROOT)/web
CL_ROOT = $(INSTALL_ROOT)/cl
PACKAGE_ROOT = $(INSTALL_ROOT)/occampy

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

CORE_FILES = \
	cpp/occam.so \
	cpp/occam3.so \
	py/occammail.py \
	py/common.py \
	py/ocutils.py \
	py/distanceFunctions.py \
	py/ocGraph.py

SETUP_FILE = \
		py/occam_base/setup.py

CAPSTONE_FILES = \
	py/occam_base/variable_list.py \
	py/occam_base/vbm_manager.py \
	py/occam_base/model.py \
	py/occam_base/__init__.py

CL_FILES = \
	cpp/occ \
	py/basic.py \
	py/fit.py \
	py/sbfit.py \
	py/sbsearch.py

WEB_FILES = \
	html/.htaccess \
	html/occam_logo.jpg \
	html/base.css \
	html/footer.html \
	html/header.html \
	html/index.html \
	py/OpagCGI.py \
	py/jobcontrol.py \
	py/weboccam.py \
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

install: lib $(WEB_FILES) $(CORE_FILES) $(CL_FILES) $(CAPSTONE_FILES) $(SETUP_FILE)
	-rm -rf $(INSTALL_ROOT)
	mkdir -p $(INSTALL_ROOT)
	mkdir -p $(WEB_ROOT)
	mkdir -p $(CL_ROOT)
	mkdir -p $(PACKAGE_ROOT)
	cp $(CL_FILES) $(CL_ROOT)
	cp $(WEB_FILES) $(WEB_ROOT)
	cp $(CORE_FILES) $(CAPSTONE_FILES) $(CL_ROOT)
	cp $(CORE_FILES) $(CAPSTONE_FILES) $(WEB_ROOT)
	cp $(CORE_FILES) $(CAPSTONE_FILES) $(PACKAGE_ROOT)
	cp $(SETUP_FILE) $(INSTALL_ROOT)
	touch $(CL_ROOT)/__init__.py $(WEB_ROOT)/__init__.py cpp/__init__.py

web:
	cp $(WEB_FILES) $(WEB_ROOT)
	cp $(CORE_FILES) $(CAPSTONE_FILES) $(WEB_ROOT)

cli:
	cp $(CORE_FILES) $(CAPSTONE_FILES) $(CL_ROOT)
	cp $(CL_FILES) $(CL_ROOT)

occampy:
	cp $(CORE_FILES) $(CAPSTONE_FILES) $(PACKAGE_ROOT)


lib: $(HEADERS) $(CPP_FILES)
	cd cpp && make

clean:
	cd cpp && make clean
	-rm -rf $(INSTALL_ROOT)
