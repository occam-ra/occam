# Copyright © 1990 The Portland State University OCCAM Project Team
# [This program is licensed under the GPL version 3 or later.]
# Please see the file LICENSE in the source
# distribution of this software for license terms.

SHELL = /bin/sh

INSTALL_ROOT = install
WEB_ROOT = $(INSTALL_ROOT)/web
CL_ROOT = $(INSTALL_ROOT)/cl

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
	py/common.py \
	py/ocutils.py \
	py/distanceFunctions.py \
	py/ocGraph.py

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

install: $(WEB_FILES) $(CORE_FILES) $(CL_FILES)
	-@ [ -d $(WEB_ROOT) ] && echo "warning: existing web installation"
	-@ [ -d $(CL_ROOT) ] && echo "warning: existing cli installation"
	mkdir -p $(INSTALL_ROOT) && \
	mkdir -p $(WEB_ROOT) && \
	mkdir -p $(CL_ROOT) && \
	cp $(WEB_FILES) $(WEB_ROOT) && \
	cp $(CORE_FILES) $(WEB_ROOT) && \
	cp $(CORE_FILES) $(CL_ROOT) && \
	cp $(CL_FILES) $(CL_ROOT) && \
	mkdir -p $(WEB_ROOT)/data

web:
	cp $(WEB_FILES) $(WEB_ROOT) && \
	cp $(CORE_FILES) $(WEB_ROOT)

cli:
	cp $(CORE_FILES) $(CL_ROOT) && \
	cp $(CL_FILES) $(CL_ROOT)

cpp/occam.so: $(HEADERS) $(CPP_FILES)
	cd cpp && $(MAKE)

GTEST_DIR = tests/googletest/googletest
GTEST_INCLUDE_DIR = $(GTEST_DIR)/include
GTEST_LIB_DIR = $(GTEST_DIR)/lib

$(GTEST_DIR):
	git submodule init
	git submodule update

$(GTEST_LIB_DIR)/libgtest.a: $(GTEST_DIR)
	g++ -std=c++14 -isystem $(GTEST_INCLUDE_DIR) -I$(GTEST_DIR) -pthread -c $(GTEST_DIR)/src/gtest-all.cc && \
	mkdir -p $(GTEST_LIB_DIR)
	ar -rv $(GTEST_LIB_DIR)/libgtest.a gtest-all.o

tests/test_ocReadFile: cpp/occam.so tests/test_ocReadFile.cpp $(GTEST_LIB_DIR)/libgtest.a
	g++ -std=c++14 -isystem $(GTEST_INCLUDE_DIR) -pthread tests/test_ocReadFile.cpp -L./cpp -loccam3 $(GTEST_LIB_DIR)/libgtest.a -o tests/test_ocReadFile

tests/test_csa: cpp/occam.so tests/test_csa.cpp $(GTEST_LIB_DIR)/libgtest.a
	g++ -std=c++14 -isystem $(GTEST_INCLUDE_DIR) -pthread tests/test_csa.cpp -L./cpp -loccam3 $(GTEST_LIB_DIR)/libgtest.a -o tests/test_csa

tests: tests/test_ocReadFile tests/test_csa
	./tests/test_ocReadFile
	./tests/test_csa

clean:
	cd cpp && $(MAKE) clean
	-rm -rf $(INSTALL_ROOT)
	-rm -rf $(GTEST_LIB_DIR)
	-rm -f tests/test_ocReadFile
	$(CXX) $(CXXFLAGS) -c $< -o $@
