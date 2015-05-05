SHELL = /bin/sh
CC = gcc
CFLAGS = -w -Wall -O3 -fPIC -std=c++11 -I ../include
LFLAGS = -shared
AR = ar
COMPILE = $(CC) $(CFLAGS)
PY_INCLUDE = /usr/include/python2.7
CL = occ
RANLIB = ranlib
LDFLAGS = -lm -lstdc++
PY = pyoccam.cpp
DYLIB = occam.so
LIB = liboccam3.a
LIBOBJECTS = \
	AttributeList.o \
	Input.o \
	Key.o \
	ManagerBase.o \
	Math.o \
	Model.o \
	ModelCache.o \
	Options.o \
	RelCache.o \
	Relation.o \
	Report.o \
	ReportPrintConditionalDV.o \
	ReportPrintResiduals.o \
	ReportQsort.o \
	SBMManager.o \
	SearchBase.o \
	Search.o \
	StateConstraint.o \
	Table.o \
	VBMManager.o \
	VariableList.o \
	_Core.o

all: $(LIB) $(DYLIB) $(CL)

.SUFFIXES:
.SUFFIXES: .cpp .o
clean:
	-test -z "$(LIB)" || rm -f $(LIB)
	-test -z "*.o core" || rm -f *.o core
	-test -z "*.bak" || rm -f *.bak
	-test -z "*.a" || rm -f *.a
	-test -z "*.so" || rm -f *.so
	-test -z "*~" || rm -f *~
	-test -z "occ" || rm -f occ

.cpp.o: 
	$(COMPILE) -c $<


# liboccam3.a depends on all the .o files
$(LIB): $(LIBOBJECTS)
	-rm -f $(LIB)			     # remove old lib
	$(AR) cru $(LIB) $(LIBOBJECTS)	     # create a new lib with all the objects
	$(RANLIB) $(LIB)		     # update the table of contents for the lib

# occam.so depends on liboccam3.a and pyoccam.cpp
$(DYLIB): $(LIB) $(PY)
	$(COMPILE) $(LFLAGS) -I $(PY_INCLUDE) -o $(DYLIB) $(PY) $(LIB) $(LDFLAGS)
$(CL): occ.cpp $(LIB)
	$(COMPILE) -o $(CL) occ.cpp $(LIBOBJECTS) $(LDFLAGS)

# Otherwise a system limit (for SysV at least) may be exceeded.
.NOEXPORT:

# output of g++ -MM *.cpp
AttributeList.o: AttributeList.cpp ../include/Core.h \
 ../include/ModelCache.h ../include/_Core.h ../include/Win32.h
_Core.o: _Core.cpp ../include/_Core.h ../include/Core.h \
 ../include/ModelCache.h
Input.o: Input.cpp ../include/Input.h ../include/Core.h \
 ../include/ModelCache.h ../include/Core.h ../include/Options.h
Key.o: Key.cpp ../include/Core.h ../include/ModelCache.h
ManagerBase.o: ManagerBase.cpp ../include/Core.h ../include/ModelCache.h \
 ../include/_Core.h ../include/ManagerBase.h ../include/Options.h \
 ../include/Math.h ../include/Core.h ../include/RelCache.h \
 ../include/ModelCache.h ../include/Options.h ../include/Input.h
Math.o: Math.cpp ../include/Math.h ../include/Core.h \
 ../include/ModelCache.h ../include/Core.h ../include/_Core.h
ModelCache.o: ModelCache.cpp ../include/Core.h ../include/ModelCache.h \
 ../include/ModelCache.h
Model.o: Model.cpp ../include/Core.h ../include/ModelCache.h \
 ../include/_Core.h ../include/Math.h ../include/Core.h \
 ../include/ModelCache.h
occ.o: occ.cpp ../include/Core.h ../include/ModelCache.h \
 ../include/VBMManager.h ../include/Core.h ../include/ManagerBase.h \
 ../include/Options.h ../include/SBMManager.h ../include/SearchBase.h \
 ../include/VBMManager.h ../include/SBMManager.h ../include/Report.h
Options.o: Options.cpp ../include/Options.h
Relation.o: Relation.cpp ../include/Core.h ../include/ModelCache.h \
 ../include/_Core.h
RelCache.o: RelCache.cpp ../include/Core.h ../include/ModelCache.h \
 ../include/RelCache.h
Report.o: Report.cpp ../include/attrDescs.h ../include/Core.h \
 ../include/ModelCache.h ../include/Core.h ../include/_Core.h \
 ../include/Report.h ../include/ManagerBase.h ../include/Options.h \
 ../include/Math.h
ReportPrintConditionalDV.o: ReportPrintConditionalDV.cpp ../include/attrDescs.h ../include/Core.h \
 ../include/ModelCache.h ../include/Core.h ../include/_Core.h \
 ../include/Report.h ../include/ManagerBase.h ../include/Options.h \
 ../include/Math.h

ReportPrintResiduals.o: ReportPrintResiduals.cpp ../include/attrDescs.h ../include/Core.h \
 ../include/ModelCache.h ../include/Core.h ../include/_Core.h \
 ../include/Report.h ../include/ManagerBase.h ../include/Options.h \
 ../include/Math.h
ReportQsort.o: ReportQsort.cpp ../include/attrDescs.h ../include/Core.h \
 ../include/ModelCache.h ../include/Core.h ../include/_Core.h \
 ../include/Report.h ../include/ManagerBase.h ../include/Options.h \
 ../include/Math.h
SBMManager.o: SBMManager.cpp ../include/Core.h ../include/ModelCache.h \
 ../include/Math.h ../include/Core.h ../include/SBMManager.h \
 ../include/ManagerBase.h ../include/Options.h ../include/ModelCache.h \
 ../include/SearchBase.h ../include/VBMManager.h ../include/SBMManager.h \
 ../include/Report.h
SearchBase.o: SearchBase.cpp ../include/SearchBase.h ../include/Core.h \
 ../include/ModelCache.h ../include/ManagerBase.h ../include/Options.h \
 ../include/VBMManager.h ../include/SBMManager.h ../include/Search.h \
 ../include/SearchBase.h
Search.o: Search.cpp ../include/Search.h ../include/SearchBase.h \
 ../include/Core.h ../include/ModelCache.h ../include/ManagerBase.h \
 ../include/Options.h ../include/VBMManager.h ../include/SBMManager.h \
 ../include/ModelCache.h ../include/_Core.h ../include/Math.h
StateConstraint.o: StateConstraint.cpp ../include/Core.h \
 ../include/ModelCache.h ../include/_Core.h
Table.o: Table.cpp ../include/Core.h ../include/ModelCache.h \
 ../include/_Core.h
VariableList.o: VariableList.cpp ../include/Core.h \
 ../include/ModelCache.h ../include/_Core.h
VBMManager.o: VBMManager.cpp ../include/Core.h ../include/ModelCache.h \
 ../include/Math.h ../include/Core.h ../include/VBMManager.h \
 ../include/ManagerBase.h ../include/Options.h ../include/ModelCache.h \
 ../include/RelCache.h ../include/SearchBase.h ../include/VBMManager.h \
 ../include/SBMManager.h ../include/Report.h
