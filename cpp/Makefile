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
	$(AR) crU $(LIB) $(LIBOBJECTS)	     # create a new lib with all the objects
	$(RANLIB) $(LIB)		     # update the table of contents for the lib

# occam.so depends on liboccam3.a and pyoccam.cpp
$(DYLIB): $(LIB) $(PY)
	$(COMPILE) $(LFLAGS) -I $(PY_INCLUDE) -o $(DYLIB) $(PY) $(LIB) $(LDFLAGS)
$(CL): occ.cpp $(LIB)
	$(COMPILE) -o $(CL) occ.cpp $(LIBOBJECTS) $(LDFLAGS)

# Otherwise a system limit (for SysV at least) may be exceeded.
.NOEXPORT:

# output of g++ -MM *.cpp

AttributeList.o: AttributeList.cpp ../include/AttributeList.h \
 ../include/_Core.h
_Core.o: _Core.cpp ../include/_Core.h
Input.o: Input.cpp ../include/Input.h ../include/Options.h \
 ../include/VariableList.h ../include/Variable.h ../include/Constants.h \
 ../include/Types.h
Key.o: Key.cpp ../include/Constants.h ../include/Key.h ../include/Types.h \
 ../include/VariableList.h ../include/Variable.h ../include/Constants.h \
 ../include/Table.h ../include/Globals.h
ManagerBase.o: ManagerBase.cpp ../include/Input.h \
 ../include/ManagerBase.h ../include/Model.h ../include/ModelCache.h \
 ../include/Relation.h ../include/Table.h ../include/Globals.h \
 ../include/Types.h ../include/VariableList.h ../include/Variable.h \
 ../include/Constants.h ../include/Options.h ../include/VarIntersect.h \
 ../include/Math.h ../include/VBMManager.h ../include/ManagerBase.h \
 ../include/FlatTable.h ../include/Model.h ../include/ModelCache.h \
 ../include/Options.h ../include/RelCache.h ../include/Relation.h \
 ../include/StateConstraint.h ../include/VariableList.h \
 ../include/_Core.h
Math.o: Math.cpp ../include/Math.h ../include/VBMManager.h \
 ../include/ManagerBase.h ../include/Model.h ../include/ModelCache.h \
 ../include/Relation.h ../include/Table.h ../include/Globals.h \
 ../include/Types.h ../include/VariableList.h ../include/Variable.h \
 ../include/Constants.h ../include/Options.h ../include/VarIntersect.h \
 ../include/FlatTable.h ../include/Model.h ../include/Relation.h \
 ../include/_Core.h
ModelCache.o: ModelCache.cpp ../include/Model.h ../include/ModelCache.h \
 ../include/Relation.h ../include/Table.h ../include/Globals.h \
 ../include/Types.h ../include/VariableList.h ../include/Variable.h \
 ../include/Constants.h ../include/ModelCache.h
Model.o: Model.cpp ../include/AttributeList.h ../include/Math.h \
 ../include/VBMManager.h ../include/ManagerBase.h ../include/Model.h \
 ../include/ModelCache.h ../include/Relation.h ../include/Table.h \
 ../include/Globals.h ../include/Types.h ../include/VariableList.h \
 ../include/Variable.h ../include/Constants.h ../include/Options.h \
 ../include/VarIntersect.h ../include/FlatTable.h ../include/Model.h \
 ../include/ModelCache.h ../include/Relation.h \
 ../include/StateConstraint.h ../include/_Core.h
occ.o: occ.cpp ../include/VBMManager.h ../include/ManagerBase.h \
 ../include/Model.h ../include/ModelCache.h ../include/Relation.h \
 ../include/Table.h ../include/Globals.h ../include/Types.h \
 ../include/VariableList.h ../include/Variable.h ../include/Constants.h \
 ../include/Options.h ../include/VarIntersect.h ../include/SBMManager.h \
 ../include/SearchBase.h ../include/VBMManager.h ../include/SBMManager.h \
 ../include/Report.h
Options.o: Options.cpp ../include/Options.h
pyoccam.o: pyoccam.cpp ../include/AttributeList.h ../include/FlatTable.h \
 ../include/Math.h ../include/VBMManager.h ../include/ManagerBase.h \
 ../include/Model.h ../include/ModelCache.h ../include/Relation.h \
 ../include/Table.h ../include/Globals.h ../include/Types.h \
 ../include/VariableList.h ../include/Variable.h ../include/Constants.h \
 ../include/Options.h ../include/VarIntersect.h ../include/FlatTable.h \
 ../include/Report.h ../include/SBMManager.h ../include/SearchBase.h \
 ../include/SBMManager.h ../include/VBMManager.h
Relation.o: Relation.cpp ../include/AttributeList.h ../include/Key.h \
 ../include/Types.h ../include/Relation.h ../include/Table.h \
 ../include/Globals.h ../include/VariableList.h ../include/Variable.h \
 ../include/Constants.h ../include/StateConstraint.h ../include/_Core.h
RelCache.o: RelCache.cpp ../include/Relation.h ../include/Table.h \
 ../include/Globals.h ../include/Types.h ../include/VariableList.h \
 ../include/Variable.h ../include/Constants.h ../include/RelCache.h
Report.o: Report.cpp ../include/attrDescs.h ../include/_Core.h \
 ../include/Report.h ../include/Model.h ../include/ModelCache.h \
 ../include/Relation.h ../include/Table.h ../include/Globals.h \
 ../include/Types.h ../include/VariableList.h ../include/Variable.h \
 ../include/Constants.h ../include/ManagerBase.h ../include/Options.h \
 ../include/VarIntersect.h ../include/Math.h ../include/VBMManager.h \
 ../include/ManagerBase.h ../include/FlatTable.h
ReportPrintConditionalDV.o: ReportPrintConditionalDV.cpp \
 ../include/Report.h ../include/Model.h ../include/ModelCache.h \
 ../include/Relation.h ../include/Table.h ../include/Globals.h \
 ../include/Types.h ../include/VariableList.h ../include/Variable.h \
 ../include/Constants.h ../include/ManagerBase.h ../include/Options.h \
 ../include/VarIntersect.h ../include/Math.h ../include/VBMManager.h \
 ../include/ManagerBase.h ../include/FlatTable.h
ReportPrintResiduals.o: ReportPrintResiduals.cpp ../include/Key.h \
 ../include/Types.h ../include/ManagerBase.h ../include/Model.h \
 ../include/ModelCache.h ../include/Relation.h ../include/Table.h \
 ../include/Globals.h ../include/VariableList.h ../include/Variable.h \
 ../include/Constants.h ../include/Options.h ../include/VarIntersect.h \
 ../include/Report.h
ReportQsort.o: ReportQsort.cpp ../include/Key.h ../include/Types.h \
 ../include/Model.h ../include/ModelCache.h ../include/Relation.h \
 ../include/Table.h ../include/Globals.h ../include/VariableList.h \
 ../include/Variable.h ../include/Constants.h
SBMManager.o: SBMManager.cpp ../include/AttributeList.h ../include/Math.h \
 ../include/VBMManager.h ../include/ManagerBase.h ../include/Model.h \
 ../include/ModelCache.h ../include/Relation.h ../include/Table.h \
 ../include/Globals.h ../include/Types.h ../include/VariableList.h \
 ../include/Variable.h ../include/Constants.h ../include/Options.h \
 ../include/VarIntersect.h ../include/FlatTable.h ../include/ModelCache.h \
 ../include/Report.h ../include/SBMManager.h ../include/SearchBase.h \
 ../include/SBMManager.h
SearchBase.o: SearchBase.cpp ../include/SearchBase.h \
 ../include/ManagerBase.h ../include/Model.h ../include/ModelCache.h \
 ../include/Relation.h ../include/Table.h ../include/Globals.h \
 ../include/Types.h ../include/VariableList.h ../include/Variable.h \
 ../include/Constants.h ../include/Options.h ../include/VarIntersect.h \
 ../include/VBMManager.h ../include/SBMManager.h ../include/Search.h \
 ../include/SearchBase.h
Search.o: Search.cpp ../include/Search.h ../include/SearchBase.h \
 ../include/ManagerBase.h ../include/Model.h ../include/ModelCache.h \
 ../include/Relation.h ../include/Table.h ../include/Globals.h \
 ../include/Types.h ../include/VariableList.h ../include/Variable.h \
 ../include/Constants.h ../include/Options.h ../include/VarIntersect.h \
 ../include/VBMManager.h ../include/SBMManager.h ../include/ModelCache.h \
 ../include/_Core.h ../include/Math.h ../include/FlatTable.h
StateConstraint.o: StateConstraint.cpp ../include/StateConstraint.h \
 ../include/Types.h ../include/_Core.h
Table.o: Table.cpp ../include/_Core.h
VariableList.o: VariableList.cpp ../include/VariableList.h \
 ../include/Variable.h ../include/Constants.h ../include/Types.h \
 ../include/_Core.h
VBMManager.o: VBMManager.cpp ../include/AttributeList.h ../include/Math.h \
 ../include/VBMManager.h ../include/ManagerBase.h ../include/Model.h \
 ../include/ModelCache.h ../include/Relation.h ../include/Table.h \
 ../include/Globals.h ../include/Types.h ../include/VariableList.h \
 ../include/Variable.h ../include/Constants.h ../include/Options.h \
 ../include/VarIntersect.h ../include/FlatTable.h ../include/ModelCache.h \
 ../include/RelCache.h ../include/Report.h ../include/SearchBase.h \
 ../include/SBMManager.h ../include/VBMManager.h
