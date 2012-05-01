SHELL = /bin/sh

CC = gcc
CFLAGS = -w -Wall -O2 -fPIC
LFLAGS = -shared

# -arch x86_64 to force 64-bit intel compile
# -arch i386 to force 32-bit intel compile
# -g for debugging
# -pg for gprof (profiler)

arch = $(shell uname)
# `uname` gives "Linux" or "Darwin" for linux or OSX, respectively
# `uname -n` gives hostname
# OIT: nag.research.pdx.edu
# dmm: dmm
# ra: ra

INCLUDES = ocCore.h _ocCore.h
WEB_ROOT = ../html						# root for the web install
CL_ROOT = install						# root for the command-line install
PY_INCLUDE = /usr/include/python2.6		# location of python include files
CL = occ								# command-line executable
DEFS = -I.		  						# include the current directory

ifeq ($(arch), Darwin)
#    CFLAGS = -w -Wall -O1 -arch x86_64 -g -flat_namespace -undefined suppress
    CFLAGS = -w -Wall -O2 -arch x86_64 -flat_namespace -undefined suppress
    LFLAGS = -bundle
	DEFS = -I. -DSWAP_QSORT_R				# fixes problem with qsort_r argument order on different platforms
    WEB_ROOT = ~/Sites/occam
    CL_ROOT = ~/Documents/Research/Occam/install
    PY_INCLUDE = /Library/Frameworks/Python.framework/Versions/2.7/include/python2.7 
endif

RANLIB = ranlib		  # tool to add or update the table of contents of archive libraries
LDFLAGS = -lm -lstdc++	  # link libm and libstdc++ libs

PY_WRAPPER = pyoccam.cpp
PY_OCCAM = occam.so

LIB = liboccam3.a
LIBOBJECTS = \
	_ocCore.o \
	ocKey.o \
	ocTable.o \
	ocVariableList.o \
	ocInput.o \
	ocRelation.o \
	ocModel.o \
	ocAttributeList.o \
	ocStateConstraint.o \
	ocManagerBase.o \
	ocRelCache.o \
	ocReport.o \
	ocModelCache.o \
	ocMath.o \
	ocOptions.o \
	ocVBMManager.o \
	ocSBMManager.o \
	ocSearchBase.o \
	ocSearch.o

CORE_FILES = occam.so ocutils.py occam3 occambatch occammail.py

CL_FILES = basic.py fit.py sbfit.py sbsearch.py $(CL)

WEB_FILES = weboccam.py header.html switchform.html searchform.html fitform.html logform.html base.css \
    header.txt footer.html index.html jobcontrol.py SBsearchform.html SBfitform.html fitbatchform.html \
    weboccam.cgi OpagCGI.py

AR = ar
COMPILE = $(CC) $(DEFS) $(CFLAGS)		 # = gcc -I. -w
#CCLD = $(CC)
#LINK = $(CCLD) $(CFLAGS) $(LDFLAGS) -o $@

install: all export
all: $(LIB) $(PY_OCCAM) $(CL)

export:
	cp $(WEB_FILES) $(WEB_ROOT)
	cp $(CORE_FILES) $(WEB_ROOT)
	cp $(CORE_FILES) $(CL_ROOT)
	cp $(CL_FILES) $(CL_ROOT)

.SUFFIXES:
.SUFFIXES: .cpp .o
clean:
	-test -z "$(LIB)" || rm -f $(LIB)
	-test -z "*.o core" || rm -f *.o core
	-test -z "*.bak" || rm -f *.bak
	-test -z "*.a" || rm -f *.a
	-test -z "*.so" || rm -f *.so
	-test -z "*~" || rm -f *~

.cpp.o: $(INCLUDES)
	$(COMPILE) -c $<

# output of g++ -MM *.cpp
_ocCore.o: _ocCore.cpp _ocCore.h ocCore.h ocModelCache.h
occ.o: occ.cpp ocCore.h ocModelCache.h ocVBMManager.h ocManagerBase.h \
  ocOptions.h ocSBMManager.h ocSearchBase.h ocReport.h
ocAttributeList.o: ocAttributeList.cpp ocCore.h ocModelCache.h _ocCore.h \
  ocWin32.h
ocInput.o: ocInput.cpp ocInput.h ocCore.h ocModelCache.h ocOptions.h
ocKey.o: ocKey.cpp ocCore.h ocModelCache.h
ocManagerBase.o: ocManagerBase.cpp ocCore.h ocModelCache.h _ocCore.h \
  ocManagerBase.h ocOptions.h ocMath.h ocRelCache.h ocInput.h
ocMath.o: ocMath.cpp ocMath.h ocCore.h ocModelCache.h _ocCore.h
ocModel.o: ocModel.cpp ocCore.h ocModelCache.h _ocCore.h ocMath.h
ocModelCache.o: ocModelCache.cpp ocCore.h ocModelCache.h
ocOptions.o: ocOptions.cpp ocOptions.h
ocRelCache.o: ocRelCache.cpp ocCore.h ocModelCache.h ocRelCache.h
ocRelation.o: ocRelation.cpp ocCore.h ocModelCache.h _ocCore.h
ocReport.o: ocReport.cpp ocCore.h ocModelCache.h _ocCore.h ocReport.h \
  ocManagerBase.h ocOptions.h ocMath.h
ocSBMManager.o: ocSBMManager.cpp ocCore.h ocModelCache.h ocMath.h \
  ocSBMManager.h ocManagerBase.h ocOptions.h ocSearchBase.h \
  ocVBMManager.h ocReport.h
ocSearch.o: ocSearch.cpp ocSearch.h ocSearchBase.h ocCore.h \
  ocModelCache.h ocManagerBase.h ocOptions.h ocVBMManager.h \
  ocSBMManager.h _ocCore.h ocMath.h
ocSearchBase.o: ocSearchBase.cpp ocSearchBase.h ocCore.h ocModelCache.h \
  ocManagerBase.h ocOptions.h ocVBMManager.h ocSBMManager.h ocSearch.h
ocStateConstraint.o: ocStateConstraint.cpp ocCore.h ocModelCache.h \
  _ocCore.h
ocTable.o: ocTable.cpp ocCore.h ocModelCache.h _ocCore.h
ocVBMManager.o: ocVBMManager.cpp ocCore.h ocModelCache.h ocMath.h \
  ocVBMManager.h ocManagerBase.h ocOptions.h ocRelCache.h ocSearchBase.h \
  ocSBMManager.h ocReport.h
ocVariableList.o: ocVariableList.cpp ocCore.h ocModelCache.h _ocCore.h

clean-compile: clean all

# liboccam3.a depends on all the .o files
$(LIB): $(LIBOBJECTS)
	-rm -f $(LIB)			     # remove old lib
	$(AR) cru $(LIB) $(LIBOBJECTS)	     # create a new lib with all the objects
	$(RANLIB) $(LIB)		     # update the table of contents for the lib

# occam.so depends on liboccam3.a and pyoccam.cpp
#	(gcc -I. -w) -shared -I (python dir) -o (occam.so) (pyoccam.cpp) (liboccam3.a) (-lm -lstdc++)
$(PY_OCCAM): $(LIB) $(PY_WRAPPER)
	$(COMPILE) $(LFLAGS) -I $(PY_INCLUDE) -o $(PY_OCCAM) $(PY_WRAPPER) $(LIB) $(LDFLAGS)
$(CL): occ.cpp $(LIB)
	$(COMPILE) -o $(CL) occ.cpp $(LIBOBJECTS) $(LDFLAGS)
#$(COMPILE) -shared -I $(PY_INCLUDE) -o $(PY_OCCAM) $(PY_WRAPPER) $(LIB) $(LDFLAGS)


# Otherwise a system limit (for SysV at least) may be exceeded.
.NOEXPORT:
