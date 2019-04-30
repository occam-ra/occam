/*
 * Copyright © 1990 The Portland State University OCCAM Project Team
 * [This program is licensed under the GPL version 3 or later.]
 * Please see the file LICENSE in the source
 * distribution of this software for license terms.
 */

#include "AttributeList.h"
#include "Math.h"
#include "Report.h"
#include "SBMManager.h"
#include "SearchBase.h"
#include "VBMManager.h"
#include "VariableList.h"
#include "Variable.h"
#include <limits>
#include <unistd.h>
#include <Python.h>


/***** MACROS *****/
//-- Exit function on error
#define onError(message) {PyErr_SetString(ErrorObject, message); return NULL; }

//-- Define the struct for a PyObject type. This carries a pointer to an
//-- instance of the actual type.
#define DefinePyObject(type) extern PyTypeObject T##type; struct P##type { PyObject_HEAD; type *obj; }

//-- Define the standard python function header.
#define DefinePyFunction(type, fn) static PyObject *type##_##fn(PyObject *self, PyObject *args)

//-- Create a method definition line
#define PyMethodDef(type, fn) { #fn, type##_##fn, 1 }

//-- Creates a reference to a variable of the python wrapper type.
#define ObjRef(var, type) (((P##type*)var)->obj)

//-- Creates a new instance of a python wrapper type.
#define ObjNew(type) ((P##type*)PyObject_NEW(P##type, &T##type))

// Define the struct for a PyObject type which carries a pointer to an instance
// of the actual type and indexes used by iterators
#define DefineIterablePyObject(type) \
extern PyTypeObject T##type;   \
struct P##type                  \
{                               \
    PyObject_HEAD          \
    type *obj;             \
    int current_it_index;       \
    int max_it_index;           \
};

//-- Trace output
#ifdef TRACE_ON
#define TRACE printf
#define TRACE_FN(name, line, obj) {TRACE("Trace: %s (%ld), %0lx\n", name, line, obj); fflush(stdout);}
#else
void notrace(...) {
}
#define TRACE notrace
#define TRACE_FN notrace
#endif

static PyObject *ErrorObject; /* local exception */

/****** Occam object types *****/
DefinePyObject(VBMManager);
DefinePyObject(SBMManager);

DefinePyObject(Relation);
DefinePyObject(Model);
DefinePyObject(Report);
DefinePyObject(Variable);

DefineIterablePyObject(VariableList)


/**************************/
/****** VBMManager ******/
/**************************/

/****** Methods ******/

static PyObject *
VBMManager_new(PyObject *self, PyObject *args)
{
    if (!PyArg_ParseTuple(args, ""))
        return NULL;

    PVBMManager *newobj = ObjNew(VBMManager);
    newobj->obj = new VBMManager();
    Py_INCREF(newobj);
    return (PyObject*) newobj;
}

static void
VBMManager_dealloc(PVBMManager *self)
{
    if (self->obj)
        delete self->obj;
    delete self;
}

// Constructor
DefinePyFunction(VBMManager, initFromCommandLine) {
    PyObject *Pargv;
    PyArg_ParseTuple(args, "O!", &PyList_Type, &Pargv);
    int argc = PyList_Size(Pargv);
    char **argv = new char*[argc];
    int i;
    for (i = 0; i < argc; i++) {
        PyObject *PString = PyList_GetItem(Pargv, i);
        int size = PyUnicode_GetLength(PString);
        argv[i] = new char[size + 1];
        strcpy(argv[i], PyUnicode_AsUTF8(PString));
    }
    bool ret;
    ret = ObjRef(self, VBMManager)->initFromCommandLine(argc, argv);
    for (i = 0; i < argc; i++)
        delete[] argv[i];
    delete[] argv;
    if (!ret) {
        onError("VBMManager: initialization failed");
    }
    Py_INCREF(Py_None);
    return Py_None;
}

// Relation **makeAllChildRelations(Relation *, bool makeProject)
DefinePyFunction(VBMManager, makeAllChildRelations) {
    PRelation *rel;
    int makeProject;
    bool bMakeProject;
    PyArg_ParseTuple(args, "O!i)", &TRelation, &rel, &makeProject);
    bMakeProject = (makeProject != 0);
    int count = rel->obj->getVariableCount();
    Relation **rels = new Relation*[count];
    ObjRef(self, VBMManager)->makeAllChildRelations(rel->obj, rels, bMakeProject);
    PyObject *list = PyList_New(count);
    int i;
    for (i = 0; i < count; i++) {
        rel = ObjNew(Relation);
        rel->obj = rels[i]; // move relation to the python object
        rels[i] = NULL;
        PyList_SetItem(list, i, (PyObject*) rel);
    }
    delete rels;
    Py_INCREF(list);
    return list;
}

DefinePyFunction(VBMManager, getDvName) {
    VBMManager* mgr = ObjRef(self, VBMManager);
    VariableList* varlist = mgr->getVariableList();

    if(!varlist)
    {
        Py_INCREF(Py_None);
        return Py_None;
    }

    const char* abbrev = varlist->getVariable(varlist->getDV())->abbrev;
    PyObject* name = PyUnicode_FromString(abbrev);
    return name;
}

// Model **searchOneLevel(Model *)
DefinePyFunction(VBMManager, searchOneLevel) {
    PModel *start;
    PModel *pmodel;
    PyArg_ParseTuple(args, "O!", &TModel, &start);
    Model **models;
    VBMManager *mgr = ObjRef(self, VBMManager);
    if (mgr->getSearch() == NULL) {
        onError("No search method defined");
    }
    if (start->obj == NULL)
        onError("Model is NULL!");
    models = mgr->getSearch()->search(start->obj);

    Model **model;
    long count = 0;
    //-- count the models
    if (models)
        for (model = models; *model; model++)
            count++;
    //-- sort them if sort was requested
    if (mgr->getSortAttr()) {
        Report::sort(models, count, mgr->getSortAttr(), (Direction) mgr->getDirectionection());
    }
    //-- make a PyList
    PyObject *list = PyList_New(count);
    int i;
    for (i = 0; i < count; i++) {
        pmodel = ObjNew(Model);
        pmodel->obj = models[i];
        PyList_SetItem(list, i, (PyObject*) pmodel);
    }
    delete[] models;
    Py_INCREF(list);
    return list;
}

// void setSearchType(const char *name)
DefinePyFunction(VBMManager, setSearchType) {
    char *name;
    PyArg_ParseTuple(args, "s", &name);
    VBMManager *mgr = ObjRef(self, VBMManager);
    mgr->setSearch(name);
    if (mgr->getSearch() == NULL) { // invalid search method name
        onError("undefined search type");
    }
    Py_INCREF(Py_None);
    return Py_None;
}

// Model *makeChildModel(Model *, int relation, bool makeProjection)
DefinePyFunction(VBMManager, makeChildModel) {
    PModel *Pmodel;
    int makeProject, relation;
    bool bMakeProject;
    bool cache;
    PyArg_ParseTuple(args, "O!ii", TModel, &Pmodel, &relation, &makeProject);
    bMakeProject = makeProject != 0;
    Model *model = Pmodel->obj;
    if (model == NULL)
        onError("Model is NULL!");
    //-- if this relation is trivial, return None
    if (model->getRelation(relation)->getVariableCount() <= 1) {
        Py_INCREF(Py_None);
        return Py_None;
    }
    Model *ret = ObjRef(self, VBMManager)->makeChildModel(Pmodel->obj, relation, &cache, bMakeProject);
    if (ret == NULL)
        onError("invalid arguments");
    PModel *newModel = ObjNew(Model);
    newModel->obj = ret;
    return Py_BuildValue("O", newModel);
}

// Model *getTopRefModel()
DefinePyFunction(VBMManager, getTopRefModel) {
    //TRACE("getTopRefModel\n");
    PModel *model;
    PyArg_ParseTuple(args, "");
    model = ObjNew(Model);
    model->obj = ObjRef(self, VBMManager)->getTopRefModel();
    Py_INCREF((PyObject*)model);
    return (PyObject*) model;
}

// Model *getBottomRefModel()
DefinePyFunction(VBMManager, getBottomRefModel) {
    //TRACE("getBottomRefModel\n");
    PModel *model;
    PyArg_ParseTuple(args, "");
    model = ObjNew(Model);
    model->obj = ObjRef(self, VBMManager)->getBottomRefModel();
    Py_INCREF((PyObject*)model);
    return (PyObject*) model;
}

// Model *getRefModel()
DefinePyFunction(VBMManager, getRefModel) {
    //TRACE("getRefModel\n");
    PModel *model;
    PyArg_ParseTuple(args, "");
    model = ObjNew(Model);
    model->obj = ObjRef(self, VBMManager)->getRefModel();
    Py_INCREF((PyObject*)model);
    return (PyObject*) model;
}

// Model *setRefModel()
DefinePyFunction(VBMManager, setRefModel) {
    char *name;
    PyArg_ParseTuple(args, "s", &name);
    Model *ret = ObjRef(self, VBMManager)->setRefModel(name);
    if (ret == NULL)
        onError("invalid model name");
    PModel *newModel = ObjNew(Model);
    newModel->obj = ret;
    return Py_BuildValue("O", newModel);
}

// long computeDF(Model *model)
DefinePyFunction(VBMManager, computeDF) {
    PyObject *Pmodel;
    PyArg_ParseTuple(args, "O!", &TModel, &Pmodel);
    Model *model = ObjRef(Pmodel, Model);
    double df = ObjRef(self, VBMManager)->computeDF(model);
    return Py_BuildValue("d", df);
}

// double computeH(Model *model)
DefinePyFunction(VBMManager, computeH) {
    PyObject *Pmodel;
    PyArg_ParseTuple(args, "O!", &TModel, &Pmodel);
    Model *model = ObjRef(Pmodel, Model);
    if (model == NULL)
        onError("Model is NULL!");
    double h = ObjRef(self, VBMManager)->computeH(model);
    return Py_BuildValue("d", h);
}

// double computeT(Model *model)
DefinePyFunction(VBMManager, computeT) {
    PyObject *Pmodel;
    PyArg_ParseTuple(args, "O!", &TModel, &Pmodel);
    Model *model = ObjRef(Pmodel, Model);
    if (model == NULL)
        onError("Model is NULL!");
    double t = ObjRef(self, VBMManager)->computeTransmission(model, VBMManager::ALGEBRAIC);
    return Py_BuildValue("d", t);
}

// void computeInformationStatistics(Model *model)
DefinePyFunction(VBMManager, computeInformationStatistics) {
    PyObject *Pmodel;
    PyArg_ParseTuple(args, "O!", &TModel, &Pmodel);
    Model *model = ObjRef(Pmodel, Model);
    if (model == NULL)
        onError("Model is NULL!");
    ObjRef(self, VBMManager)->computeInformationStatistics(model);
    Py_INCREF(Py_None);
    return Py_None;
}

// void computeDFStatistics(Model *model)
DefinePyFunction(VBMManager, computeDFStatistics) {
    PyObject *Pmodel;
    PyArg_ParseTuple(args, "O!", &TModel, &Pmodel);
    Model *model = ObjRef(Pmodel, Model);
    if (model == NULL)
        onError("Model is NULL!");
    ObjRef(self, VBMManager)->computeDFStatistics(model);
    Py_INCREF(Py_None);
    return Py_None;
}

// void computeL2Statistics(Model *model)
DefinePyFunction(VBMManager, computeL2Statistics) {
    PyObject *Pmodel;
    PyArg_ParseTuple(args, "O!", &TModel, &Pmodel);
    Model *model = ObjRef(Pmodel, Model);
    if (model == NULL)
        onError("Model is NULL!");
    ObjRef(self, VBMManager)->computeL2Statistics(model);
    Py_INCREF(Py_None);
    return Py_None;
}

// void computePearsonStatistics(Model *model)
DefinePyFunction(VBMManager, computePearsonStatistics) {
    PyObject *Pmodel;
    PyArg_ParseTuple(args, "O!", &TModel, &Pmodel);
    Model *model = ObjRef(Pmodel, Model);
    if (model == NULL)
        onError("Model is NULL!");
    ObjRef(self, VBMManager)->computePearsonStatistics(model);
    Py_INCREF(Py_None);
    return Py_None;
}

// void computeDependentStatistics(Model *model)
DefinePyFunction(VBMManager, computeDependentStatistics) {
    PyObject *Pmodel;
    PyArg_ParseTuple(args, "O!", &TModel, &Pmodel);
    Model *model = ObjRef(Pmodel, Model);
    if (model == NULL)
        onError("Model is NULL!");
    ObjRef(self, VBMManager)->computeDependentStatistics(model);
    Py_INCREF(Py_None);
    return Py_None;
}

// void computeBPStatistics(Model *model)
DefinePyFunction(VBMManager, computeBPStatistics) {
    PyObject *Pmodel;
    PyArg_ParseTuple(args, "O!", &TModel, &Pmodel);
    Model *model = ObjRef(Pmodel, Model);
    if (model == NULL)
        onError("Model is NULL!");
    ObjRef(self, VBMManager)->computeBPStatistics(model);
    Py_INCREF(Py_None);
    return Py_None;
}

// void computeIncrementalAlpha(Model *model)
DefinePyFunction(VBMManager, computeIncrementalAlpha) {
    PyObject *Pmodel;
    PyArg_ParseTuple(args, "O!", &TModel, &Pmodel);
    Model *model = ObjRef(Pmodel, Model);
    if (model == NULL)
        onError("Model is NULL!");
    ObjRef(self, VBMManager)->computeIncrementalAlpha(model);
    Py_INCREF(Py_None);
    return Py_None;
}

// void compareProgenitors(Model *model, Model *newProgen)
DefinePyFunction(VBMManager, compareProgenitors) {
    PyObject *Pmodel, *Pprogen;
    PyArg_ParseTuple(args, "O!O!", &TModel, &Pmodel, &TModel, &Pprogen);
    Model *model = ObjRef(Pmodel, Model);
    Model *progen = ObjRef(Pprogen, Model);
    if (model == NULL)
        onError("Model is NULL.");
    if (progen == NULL)
        onError("Progen is NULL.");
    ObjRef(self, VBMManager)->compareProgenitors(model, progen);
    Py_INCREF(Py_None);
    return Py_None;
}

// Model *makeModel(String name, bool makeProject)
DefinePyFunction(VBMManager, makeModel) {
    char *name;
    int makeProject;
    bool bMakeProject;
    PyArg_ParseTuple(args, "si", &name, &makeProject);
    bMakeProject = makeProject != 0;
    Model *ret = ObjRef(self, VBMManager)->makeModel(name, bMakeProject);
    if (ret == NULL) {
        onError("invalid model name");
        exit(1);
    }
    PModel *newModel = ObjNew(Model);
    newModel->obj = ret;
    return Py_BuildValue("O", newModel);
}

// void setFilter(String attrName, String op, double value)
DefinePyFunction(VBMManager, setFilter) {
    char *attrName;
    const char *relOp;
    double attrValue;
    VBMManager::RelOp op;
    PyArg_ParseTuple(args, "ssd", &attrName, &relOp, &attrValue);
    if (strcmp(relOp, "<") == 0 || strcasecmp(relOp, "lt") == 0)
        op = VBMManager::LESSTHAN;
    else if (strcmp(relOp, "=") == 0 || strcasecmp(relOp, "eq") == 0)
        op = VBMManager::EQUALS;
    else if (strcmp(relOp, ">") == 0 || strcasecmp(relOp, "gt") == 0)
        op = VBMManager::GREATERTHAN;
    else {
        onError("Invalid comparison operator");
    }
    ObjRef(self, VBMManager)->setFilter(attrName, attrValue, op);
    Py_INCREF(Py_None);
    return Py_None;
}

/* commented out because it is currently unused
 // void setSort(String attrName, String dir)
 DefinePyFunction(VBMManager, setSort)
 {
 char *attrName;
 const char *dir;
 PyArg_ParseTuple(args, "ss", &attrName, &dir);
 VBMManager *mgr = ObjRef(self, VBMManager);
 mgr->setSortAttr(attrName);
 if (strcasecmp(dir, "ascending") == 0)
 mgr->setDirectionection(Direction::Ascending);
 else if (strcasecmp(dir, "descending") == 0)
 mgr->setDirectionection(Direction::Descending);
 else {
 onError("Invalid sort direction");
 }
 Py_INCREF(Py_None);
 return Py_None;
 }
 */

// void setDDFMethod(int method)
DefinePyFunction(VBMManager, setDDFMethod) {
    int meth;
    PyArg_ParseTuple(args, "i", &meth);
    ObjRef(self, VBMManager)->setDDFMethod(meth);
    Py_INCREF(Py_None);
    return Py_None;
}

// void setAlphaThreshold(double thresh)
DefinePyFunction(VBMManager, setAlphaThreshold) {
	double thresh;
    PyArg_ParseTuple(args, "d", &thresh);
    ObjRef(self, VBMManager)->setAlphaThreshold(thresh);
    Py_INCREF(Py_None);
	return Py_None;
}


// void setUseInverseNotation(int method)
DefinePyFunction(VBMManager, setUseInverseNotation) {
    int flag;
    PyArg_ParseTuple(args, "i", &flag);
    ObjRef(self, VBMManager)->setUseInverseNotation(flag);
    Py_INCREF(Py_None);
    return Py_None;
}

// void setValuesAreFunctions(int method)
DefinePyFunction(VBMManager, setValuesAreFunctions) {
    int flag;
    PyArg_ParseTuple(args, "i", &flag);
    ObjRef(self, VBMManager)->setValuesAreFunctions(flag);
    Py_INCREF(Py_None);
    return Py_None;
}

// void setSearchDirection(int dir)
// 0 = up, 1 = down
DefinePyFunction(VBMManager, setSearchDirection) {
    int dir_raw;
    PyArg_ParseTuple(args, "i", &dir_raw);
    Direction dir = (dir_raw ==  1) ? Direction::Descending : Direction::Ascending;
    ObjRef(self, VBMManager)->setSearchDirection(dir);
    Py_INCREF(Py_None);
    return Py_None;
}

// void printFitReport(Model *model)
DefinePyFunction(VBMManager, printFitReport) {
    PyObject *Pmodel;
    PyArg_ParseTuple(args, "O!", &TModel, &Pmodel);
    Model *model = ObjRef(Pmodel, Model);
    if (model == NULL)
        onError("Model is NULL!");
    ObjRef(self, VBMManager)->printFitReport(model, stdout);
    Py_INCREF(Py_None);
    return Py_None;
}

// void getOption(const char *name)
DefinePyFunction(VBMManager, getOption) {
    char *attrName;
    PyArg_ParseTuple(args, "s", &attrName);
    const char *value;
    void *nextp = NULL;
    if (!ObjRef(self, VBMManager)->getOptionString(attrName, &nextp, &value)) {
        value = "";
    }
    return Py_BuildValue("s", value);
}

DefinePyFunction(VBMManager, getOptionList) {
    char *attrName;
    PyArg_ParseTuple(args, "s", &attrName);
    const char *value;
    void *nextp = NULL;
    PyObject *list = PyList_New(0);
    while (ObjRef(self, VBMManager)->getOptionString(attrName, &nextp, &value) && nextp != NULL) {
        PyObject *valstr = Py_BuildValue("s", value);
        PyList_Append(list, valstr);
    }
    Py_INCREF(list);
    return list;
}

// Model *Report()
DefinePyFunction(VBMManager, Report) {
    PyArg_ParseTuple(args, "");
    PReport *report = ObjNew(Report);
    report->obj = new Report(ObjRef(self, VBMManager));
    return Py_BuildValue("O", report);
}

// void makeFitTable(Model *model)
DefinePyFunction(VBMManager, makeFitTable) {
    PyObject *Pmodel;
    PyArg_ParseTuple(args, "O!", &TModel, &Pmodel);
    Model *model = ObjRef(Pmodel, Model);
    if (model == NULL)
        onError("Model is NULL!");
    ObjRef(self, VBMManager)->makeFitTable(model);
    Py_INCREF(Py_None);
    return Py_None;
}

// bool isDirected()
DefinePyFunction(VBMManager, isDirected) {
    PyArg_ParseTuple(args, "");
    bool directed = ObjRef(self, VBMManager)->getVariableList()->isDirected();
    return Py_BuildValue("i", directed ? 1 : 0);
}

// void printOptions()
DefinePyFunction(VBMManager, printOptions) {
    int printHTML;
    int skipNominal;
    PyArg_ParseTuple(args, "ii", &printHTML, &skipNominal);
    ObjRef(self, VBMManager)->printOptions(printHTML != 0, skipNominal != 0);
    Py_INCREF(Py_None);
    return Py_None;
}

// void deleteTablesFromCache()
DefinePyFunction(VBMManager, deleteTablesFromCache) {
    ObjRef(self, VBMManager)->deleteTablesFromCache();
    Py_INCREF(Py_None);
    return Py_None;
}

// bool deleteModelFromCache(Model *model)
DefinePyFunction(VBMManager, deleteModelFromCache) {
    PyObject *Pmodel;
    PyArg_ParseTuple(args, "O!", &TModel, &Pmodel);
    Model *model = ObjRef(Pmodel, Model);
    if (model == NULL)
        onError("Model is NULL!");
    bool success = ObjRef(self, VBMManager)->deleteModelFromCache(model);
    return Py_BuildValue("i", success ? 1 : 0);
}

//double getSampleSz()
DefinePyFunction(VBMManager, getSampleSz) {
    PyArg_ParseTuple(args, "");
    double ss = ObjRef(self, VBMManager)->getSampleSz();
    return Py_BuildValue("d", ss);
}

//long printSizes()
DefinePyFunction(VBMManager, printSizes) {
    PyArg_ParseTuple(args, "");
    VBMManager *mgr = ObjRef(self, VBMManager);
    mgr->printSizes();
    Py_INCREF(Py_None);
    return Py_None;
}

//long printBasicStatistics()
DefinePyFunction(VBMManager, printBasicStatistics) {
    PyArg_ParseTuple(args, "");
    VBMManager *mgr = ObjRef(self, VBMManager);
    mgr->printBasicStatistics();
    Py_INCREF(Py_None);
    fflush(stdout);
    return Py_None;
}

//long computePercentCorrect(Model)
DefinePyFunction(VBMManager, computePercentCorrect) {
    PyObject *Pmodel;
    PyArg_ParseTuple(args, "O!", &TModel, &Pmodel);
    Model *model = ObjRef(Pmodel, Model);
    if (model == NULL)
        onError("Model is NULL!");
    ObjRef(self, VBMManager)->computePercentCorrect(model);
    Py_INCREF(Py_None);
    return Py_None;
}

//long getMemUsage()
// This memory usage function doesn't work on Mac OS X, and perhaps other platforms.
DefinePyFunction(VBMManager, getMemUsage) {
    static char *oldBrk = 0;
    PyArg_ParseTuple(args, "");
    if (oldBrk == 0)
        oldBrk = (char*) sbrk(0);
    double used = ((char*) sbrk(0)) - oldBrk;
    return Py_BuildValue("d", used);
}

//int hasTestData()
DefinePyFunction(VBMManager, hasTestData) {
    PyArg_ParseTuple(args, "");
    VBMManager *mgr = ObjRef(self, VBMManager);
    int result = (mgr->getTestData() != NULL);
    return Py_BuildValue("i", result);
}

//int dumpRelations
DefinePyFunction(VBMManager, dumpRelations) {
    PyArg_ParseTuple(args, "");
    VBMManager *mgr = ObjRef(self, VBMManager);
    mgr->dumpRelations();
    return Py_BuildValue("i", 0);
}

DefinePyFunction(VBMManager, getVariableList)
{
    VBMManager* manager = ObjRef(self, VBMManager);
    VariableList *variable_list = manager->getVariableList();

    //Variable list is NULL
    if(!variable_list)
    {
       Py_INCREF(Py_None);
       return Py_None;
    }

    PVariableList *py_variable_list = ObjNew(VariableList);
    py_variable_list->obj = variable_list;
    Py_INCREF(py_variable_list);

    return (PyObject*) py_variable_list;
}


static struct PyMethodDef VBMManager_methods[] = {
        PyMethodDef(VBMManager, compareProgenitors),
        PyMethodDef(VBMManager, computeBPStatistics),
        PyMethodDef(VBMManager, computeDependentStatistics),
        PyMethodDef(VBMManager, computeDF),
        PyMethodDef(VBMManager, computeDFStatistics),
        PyMethodDef(VBMManager, computeH),
        PyMethodDef(VBMManager, computeIncrementalAlpha),
        PyMethodDef(VBMManager, computeInformationStatistics),
        PyMethodDef(VBMManager, computeL2Statistics),
        PyMethodDef(VBMManager, computePearsonStatistics),
        PyMethodDef(VBMManager, computePercentCorrect),
        PyMethodDef(VBMManager, computeT),
        PyMethodDef(VBMManager, deleteModelFromCache),
        PyMethodDef(VBMManager, deleteTablesFromCache),
        PyMethodDef(VBMManager, dumpRelations),
        PyMethodDef(VBMManager, getBottomRefModel),
        PyMethodDef(VBMManager, getDvName),
        PyMethodDef(VBMManager, getMemUsage),
        PyMethodDef(VBMManager, getOption),
        PyMethodDef(VBMManager, getOptionList),
        PyMethodDef(VBMManager, getRefModel),
        PyMethodDef(VBMManager, getSampleSz),
        PyMethodDef(VBMManager, getTopRefModel),
        PyMethodDef(VBMManager, getVariableList),
        PyMethodDef(VBMManager, hasTestData),
        PyMethodDef(VBMManager, initFromCommandLine),
        PyMethodDef(VBMManager, isDirected),
        PyMethodDef(VBMManager, makeAllChildRelations),
        PyMethodDef(VBMManager, makeChildModel),
        PyMethodDef(VBMManager, makeFitTable),
        PyMethodDef(VBMManager, makeModel),
        PyMethodDef(VBMManager, printBasicStatistics),
        PyMethodDef(VBMManager, printFitReport),
        PyMethodDef(VBMManager, printOptions),
        PyMethodDef(VBMManager, printSizes),
        PyMethodDef(VBMManager, Report),
        PyMethodDef(VBMManager, searchOneLevel),
        PyMethodDef(VBMManager, setAlphaThreshold),
        PyMethodDef(VBMManager, setDDFMethod),
        PyMethodDef(VBMManager, setFilter),
        PyMethodDef(VBMManager, setRefModel),
        PyMethodDef(VBMManager, setSearchDirection),
        PyMethodDef(VBMManager, setSearchType),
        PyMethodDef(VBMManager, setUseInverseNotation),
        PyMethodDef(VBMManager, setValuesAreFunctions),
        { nullptr }
};


/****** Type Definition ******/
PyTypeObject TVBMManager = {
    PyVarObject_HEAD_INIT(&PyType_Type, 0)
    .tp_name            = "VBMManager_cpp",
    .tp_basicsize       = sizeof(PVBMManager),
    .tp_itemsize        = NULL,
    .tp_dealloc         = (destructor) VBMManager_dealloc,
    .tp_print           = nullptr,
    .tp_getattr         = nullptr,
    .tp_setattr         = nullptr,
    .tp_as_async        = nullptr,
    .tp_repr            = nullptr,
    .tp_as_number       = nullptr,
    .tp_as_sequence     = nullptr,
    .tp_as_mapping      = nullptr,
    .tp_hash            = nullptr,
    .tp_call            = nullptr,
    .tp_str             = nullptr,
    .tp_getattro        = nullptr,
    .tp_setattro        = nullptr,
    .tp_as_buffer       = nullptr,
    .tp_flags           = Py_TPFLAGS_DEFAULT,
    .tp_doc             = nullptr,
    .tp_traverse        = nullptr,
    .tp_clear           = nullptr,
    .tp_richcompare     = nullptr,
    .tp_weaklistoffset  = NULL,
    .tp_iter            = nullptr,
    .tp_iternext        = nullptr,
    .tp_methods         = VBMManager_methods,
};

/**************************/
/****** SBMManager ******/
/**************************/

/****** Methods ******/

static PyObject *
SBMManager_new(PyObject *self, PyObject *args)
{
    if (!PyArg_ParseTuple(args, ""))
        return NULL;

    PSBMManager *newobj = ObjNew(SBMManager);
    newobj->obj = new SBMManager();
    Py_INCREF(newobj);
    return (PyObject*) newobj;
};

static void
SBMManager_dealloc(PVBMManager *self)
{
    if (self->obj)
        delete self->obj;
    delete self;
}

// Constructor
DefinePyFunction(SBMManager, initFromCommandLine) {
    PyObject *Pargv;
    PyArg_ParseTuple(args, "O!", &PyList_Type, &Pargv);
    int argc = PyList_Size(Pargv);
    char **argv = new char*[argc];
    int i;
    for (i = 0; i < argc; i++) {
        PyObject *PString = PyList_GetItem(Pargv, i);
        int size = PyUnicode_GetLength(PString);
        argv[i] = new char[size + 1];
        strcpy(argv[i], PyUnicode_AsUTF8(PString));
    }
    bool ret;
    ret = ObjRef(self, SBMManager)->initFromCommandLine(argc, argv);
    for (i = 0; i < argc; i++)
        delete[] argv[i];
    delete[] argv;
    if (!ret) {
        onError("SBMManager: initialization failed");
    }
    Py_INCREF(Py_None);
    return Py_None;
}

// Model **searchOneLevel(Model *)
DefinePyFunction(SBMManager, searchOneLevel) {
    PModel *start;
    PModel *pmodel;
    PyArg_ParseTuple(args, "O!", &TModel, &start);
    Model **models;
    SBMManager *mgr = ObjRef(self, SBMManager);
    if (mgr->getSearch() == NULL) {
        onError("No search method defined");
    }
    if (start->obj == NULL)
        onError("Model is NULL!");
    models = mgr->getSearch()->search(start->obj);
    Model **model;
    long count = 0;
    //-- count the models
    if (models)
        for (model = models; *model; model++)
            count++;
    //-- sort them if sort was requested
    if (mgr->getSortAttr()) {
        Report::sort(models, count, mgr->getSortAttr(), (Direction) mgr->getDirectionection());
    }
    //-- make a PyList
    PyObject *list = PyList_New(count);
    int i;
    for (i = 0; i < count; i++) {
        pmodel = ObjNew(Model);
        pmodel->obj = models[i];
        PyList_SetItem(list, i, (PyObject*) pmodel);
    }
    delete[] models;
    Py_INCREF(list);
    return list;
}

// void setSearchType(const char *name)
DefinePyFunction(SBMManager, setSearchType) {
    char *name;
    PyArg_ParseTuple(args, "s", &name);
    SBMManager *mgr = ObjRef(self, SBMManager);
    mgr->setSearch(name);
    if (mgr->getSearch() == NULL) { // invalid search method name
        onError("undefined search type");
    }
    Py_INCREF(Py_None);
    return Py_None;
}

// Model *getTopRefModel()
DefinePyFunction(SBMManager, getTopRefModel) {
    //TRACE("getTopRefModel\n");
    PModel *model;
    PyArg_ParseTuple(args, "");
    model = ObjNew(Model);
    model->obj = ObjRef(self, SBMManager)->getTopRefModel();
    Py_INCREF((PyObject*)model);
    return (PyObject*) model;
}

// Model *getBottomRefModel()
DefinePyFunction(SBMManager, getBottomRefModel) {
    //TRACE("getBottomRefModel\n");
    PModel *model;
    PyArg_ParseTuple(args, "");
    model = ObjNew(Model);
    model->obj = ObjRef(self, SBMManager)->getBottomRefModel();
    Py_INCREF((PyObject*)model);
    return (PyObject*) model;
}

// Model *getRefModel()
DefinePyFunction(SBMManager, getRefModel) {
    //TRACE("getRefModel\n");
    PModel *model;
    PyArg_ParseTuple(args, "");
    model = ObjNew(Model);
    model->obj = ObjRef(self, SBMManager)->getRefModel();
    Py_INCREF((PyObject*)model);
    return (PyObject*) model;
}

// Model *setRefModel()
DefinePyFunction(SBMManager, setRefModel) {
    char *name;
    PyArg_ParseTuple(args, "s", &name);
    Model *ret = ObjRef(self, SBMManager)->setRefModel(name);
    if (ret == NULL)
        onError("invalid model name");
    PModel *newModel = ObjNew(Model);
    newModel->obj = ret;
    return Py_BuildValue("O", newModel);
}

// long computeDF(Model *model)
DefinePyFunction(SBMManager, computeDF) {
    PyObject *Pmodel;
    PyArg_ParseTuple(args, "O!", &TModel, &Pmodel);
    Model *model = ObjRef(Pmodel, Model);
    double df = ObjRef(self, SBMManager)->computeDfSb(model);
    return Py_BuildValue("d", df);
}

// double computeH(Model *model)
DefinePyFunction(SBMManager, computeH) {
    PyObject *Pmodel;
    PyArg_ParseTuple(args, "O!", &TModel, &Pmodel);
    Model *model = ObjRef(Pmodel, Model);
    if (model == NULL)
        onError("Model is NULL!");
    double h = ObjRef(self,SBMManager)->computeH(model, SBMManager::IPF);
    return Py_BuildValue("d", h);
}

// double computeT(Model *model)
DefinePyFunction(SBMManager, computeT) {
    PyObject *Pmodel;
    PyArg_ParseTuple(args, "O!", &TModel, &Pmodel);
    Model *model = ObjRef(Pmodel, Model);
    if (model == NULL)
        onError("Model is NULL!");
    double t = ObjRef(self, SBMManager)->computeTransmission(model, SBMManager::IPF);
    return Py_BuildValue("d", t);
}

// void computeInformationStatistics(Model *model)
DefinePyFunction(SBMManager, computeInformationStatistics) {
    PyObject *Pmodel;
    PyArg_ParseTuple(args, "O!", &TModel, &Pmodel);
    Model *model = ObjRef(Pmodel, Model);
    if (model == NULL)
        onError("Model is NULL!");
    ObjRef(self, SBMManager)->computeInformationStatistics(model);
    Py_INCREF(Py_None);
    return Py_None;
}

// void computeDFStatistics(Model *model)
DefinePyFunction(SBMManager, computeDFStatistics) {
    PyObject *Pmodel;
    PyArg_ParseTuple(args, "O!", &TModel, &Pmodel);
    Model *model = ObjRef(Pmodel, Model);
    if (model == NULL)
        onError("Model is NULL!");
    ObjRef(self, SBMManager)->computeDFStatistics(model);
    Py_INCREF(Py_None);
    return Py_None;
}

// void computeL2Statistics(Model *model)
DefinePyFunction(SBMManager, computeL2Statistics) {
    PyObject *Pmodel;
    PyArg_ParseTuple(args, "O!", &TModel, &Pmodel);
    Model *model = ObjRef(Pmodel, Model);
    if (model == NULL)
        onError("Model is NULL!");
    ObjRef(self, SBMManager)->computeL2Statistics(model);
    Py_INCREF(Py_None);
    return Py_None;
}

// void computePearsonStatistics(Model *model)
DefinePyFunction(SBMManager, computePearsonStatistics) {
    PyObject *Pmodel;
    PyArg_ParseTuple(args, "O!", &TModel, &Pmodel);
    Model *model = ObjRef(Pmodel, Model);
    if (model == NULL)
        onError("Model is NULL!");
    ObjRef(self, SBMManager)->computePearsonStatistics(model);
    Py_INCREF(Py_None);
    return Py_None;
}

// void computeDependentStatistics(Model *model)
DefinePyFunction(SBMManager, computeDependentStatistics) {
    PyObject *Pmodel;
    PyArg_ParseTuple(args, "O!", &TModel, &Pmodel);
    Model *model = ObjRef(Pmodel, Model);
    if (model == NULL)
        onError("Model is NULL!");
    ObjRef(self, SBMManager)->computeDependentStatistics(model);
    Py_INCREF(Py_None);
    return Py_None;
}

// void computeBPStatistics(Model *model)
DefinePyFunction(SBMManager, computeBPStatistics) {
    PyObject *Pmodel;
    PyArg_ParseTuple(args, "O!", &TModel, &Pmodel);
    Model *model = ObjRef(Pmodel, Model);
    if (model == NULL)
        onError("Model is NULL!");
    ObjRef(self, SBMManager)->computeBPStatistics(model);
    Py_INCREF(Py_None);
    return Py_None;
}

// void computeIncrementalAlpha(Model *model)
DefinePyFunction(SBMManager, computeIncrementalAlpha) {
    PyObject *Pmodel;
    PyArg_ParseTuple(args, "O!", &TModel, &Pmodel);
    Model *model = ObjRef(Pmodel, Model);
    if (model == NULL)
        onError("Model is NULL!");
    ObjRef(self, SBMManager)->computeIncrementalAlpha(model);
    Py_INCREF(Py_None);
    return Py_None;
}

// void compareProgenitors(Model *model, Model *newProgen)
DefinePyFunction(SBMManager, compareProgenitors) {
    PyObject *Pmodel, *Pprogen;
    PyArg_ParseTuple(args, "O!O!", &TModel, &Pmodel, &TModel, &Pprogen);
    Model *model = ObjRef(Pmodel, Model);
    Model *progen = ObjRef(Pprogen, Model);
    if (model == NULL)
        onError("Model is NULL.");
    if (progen == NULL)
        onError("Progen is NULL.");
    ObjRef(self, SBMManager)->compareProgenitors(model, progen);
    Py_INCREF(Py_None);
    return Py_None;
}

// Model *makeSbModel(String name, bool makeProject)
DefinePyFunction(SBMManager, makeSbModel) {
    char *name;
    const char *name2;
    //name2=new char[100];
    int makeProject;
    bool bMakeProject;
    PyArg_ParseTuple(args, "si", &name, &makeProject);
    bMakeProject = makeProject != 0;
    Model *ret = ObjRef(self, SBMManager)->makeSbModel(name, bMakeProject);
    if (ret == NULL) {
        onError("invalid model name");
        exit(1);
    }
    name2 = ret->getPrintName();
    //printf("model name is %s\n",name2);
    PModel *newModel = ObjNew(Model);
    newModel->obj = ret;
    return Py_BuildValue("O", newModel);
}

// void setFilter(String attrName, String op, double value)
DefinePyFunction(SBMManager, setFilter) {
    char *attrName;
    const char *relOp;
    double attrValue;
    SBMManager::RelOp op;
    PyArg_ParseTuple(args, "ssd", &attrName, &relOp, &attrValue);
    if (strcmp(relOp, "<") == 0 || strcasecmp(relOp, "lt") == 0)
        op = SBMManager::LESSTHAN;
    else if (strcmp(relOp, "=") == 0 || strcasecmp(relOp, "eq") == 0)
        op = SBMManager::EQUALS;
    else if (strcmp(relOp, ">") == 0 || strcasecmp(relOp, "gt") == 0)
        op = SBMManager::GREATERTHAN;
    else {
        onError("Invalid comparison operator");
    }
    ObjRef(self, SBMManager)->setFilter(attrName, attrValue, op);
    Py_INCREF(Py_None);
    return Py_None;
}

/* commented out because it is currently unused
 // void setSort(String attrName, String dir)
 DefinePyFunction(SBMManager, setSort)
 {
 char *attrName;
 const char *dir;
 PyArg_ParseTuple(args, "ss", &attrName, &dir);
 SBMManager *mgr = ObjRef(self, SBMManager);
 mgr->setSortAttr(attrName);
 if (strcasecmp(dir, "ascending") == 0)
 mgr->setDirectionection(Direction::Ascending);
 else if (strcasecmp(dir, "descending") == 0)
 mgr->setDirectionection(Direction::Descending);
 else {
 onError("Invalid sort direction");
 }
 Py_INCREF(Py_None);
 return Py_None;
 }
 */

// void setSearchDirection(int dir)
// 0 = up, 1 = down
DefinePyFunction(SBMManager, setSearchDirection) {
    int dir_raw;
    PyArg_ParseTuple(args, "i", &dir_raw);
    Direction dir = (dir_raw ==  1) ? Direction::Descending : Direction::Ascending;
    ObjRef(self, SBMManager)->setSearchDirection(dir);
    Py_INCREF(Py_None);
    return Py_None;
}

// void printFitReport(Model *model)
DefinePyFunction(SBMManager, printFitReport) {
    PyObject *Pmodel;
    PyArg_ParseTuple(args, "O!", &TModel, &Pmodel);
    Model *model = ObjRef(Pmodel, Model);
    if (model == NULL)
        onError("Model is NULL!");
    ObjRef(self, SBMManager)->printFitReport(model, stdout);
    Py_INCREF(Py_None);
    return Py_None;
}

// void getOption(const char *name)
DefinePyFunction(SBMManager, getOption) {
    char *attrName;
    PyArg_ParseTuple(args, "s", &attrName);
    const char *value;
    void *nextp = NULL;
    if (!ObjRef(self, SBMManager)->getOptionString(attrName, &nextp, &value)) {
        value = "";
    }
    return Py_BuildValue("s", value);
}

DefinePyFunction(SBMManager, getOptionList) {
    char *attrName;
    PyArg_ParseTuple(args, "s", &attrName);
    const char *value;
    void *nextp = NULL;
    PyObject *list = PyList_New(0);
    while (ObjRef(self, SBMManager)->getOptionString(attrName, &nextp, &value) && nextp != NULL) {
        PyObject *valstr = Py_BuildValue("s", value);
        PyList_Append(list, valstr);
    }
    Py_INCREF(list);
    return list;
}

// Model *Report()
DefinePyFunction(SBMManager, Report) {
    PyArg_ParseTuple(args, "");
    PReport *report = ObjNew(Report);
    report->obj = new Report(ObjRef(self, SBMManager));
    return Py_BuildValue("O", report);
}

// void makeFitTable(Model *model)
DefinePyFunction(SBMManager, makeFitTable) {
    PyObject *Pmodel;
    PyArg_ParseTuple(args, "O!", &TModel, &Pmodel);
    Model *model = ObjRef(Pmodel, Model);
    if (model == NULL)
        onError("Model is NULL!");
    ObjRef(self, SBMManager)->makeFitTable(model);
    Py_INCREF(Py_None);
    return Py_None;
}

// bool isDirected()
DefinePyFunction(SBMManager, isDirected) {
    PyArg_ParseTuple(args, "");
    bool directed = ObjRef(self,SBMManager)->getVariableList()->isDirected();
    return Py_BuildValue("i", directed ? 1 : 0);
}

// void printOptions()
DefinePyFunction(SBMManager, printOptions) {
    int printHTML;
    int skipNominal;
    PyArg_ParseTuple(args, "ii", &printHTML, &skipNominal);
    ObjRef(self, SBMManager)->printOptions(printHTML != 0, skipNominal != 0);
    Py_INCREF(Py_None);
    return Py_None;
}

// bool deleteModelFromCache(Model *model)
DefinePyFunction(SBMManager, deleteModelFromCache) {
    PyObject *Pmodel;
    PyArg_ParseTuple(args, "O!", &TModel, &Pmodel);
    Model *model = ObjRef(Pmodel, Model);
    if (model == NULL)
        onError("Model is NULL!");
    bool success = ObjRef(self, SBMManager)->deleteModelFromCache(model);
    return Py_BuildValue("i", success ? 1 : 0);
}

// void deleteTablesFromCache()
DefinePyFunction(SBMManager, deleteTablesFromCache) {
    ObjRef(self, SBMManager)->deleteTablesFromCache();
    Py_INCREF(Py_None);
    return Py_None;
}

//double getSampleSz()
DefinePyFunction(SBMManager, getSampleSz) {
    PyArg_ParseTuple(args, "");
    double ss = ObjRef(self, SBMManager)->getSampleSz();
    return Py_BuildValue("d", ss);
}

//long computePercentCorrect(Model)
DefinePyFunction(SBMManager, computePercentCorrect) {
    PyObject *Pmodel;
    PyArg_ParseTuple(args, "O!", &TModel, &Pmodel);
    Model *model = ObjRef(Pmodel, Model);
    if (model == NULL)
        onError("Model is NULL!");
    ObjRef(self, SBMManager)->computePercentCorrect(model);
    Py_INCREF(Py_None);
    return Py_None;
}

//long getMemUsage()
// This memory usage function doesn't work on Mac OS X, and perhaps other platforms.
DefinePyFunction(SBMManager, getMemUsage) {
    static char *oldBrk = 0;
    PyArg_ParseTuple(args, "");
    if (oldBrk == 0)
        oldBrk = (char*) sbrk(0);
    double used = ((char*) sbrk(0)) - oldBrk;
    return Py_BuildValue("d", used);
}

//long printBasicStatistics()
DefinePyFunction(SBMManager, printBasicStatistics) {
    PyArg_ParseTuple(args, "");
    SBMManager *mgr = ObjRef(self, SBMManager);
    mgr->printBasicStatistics();
    Py_INCREF(Py_None);
    fflush(stdout);
    return Py_None;
}

//int hasTestData()
DefinePyFunction(SBMManager, hasTestData) {
    PyArg_ParseTuple(args, "");
    SBMManager *mgr = ObjRef(self, SBMManager);
    int result = (mgr->getTestData() != NULL);
    return Py_BuildValue("i", result);
}

static struct PyMethodDef SBMManager_methods[] = {
        PyMethodDef(SBMManager, compareProgenitors),
        PyMethodDef(SBMManager, computeBPStatistics),
        PyMethodDef(SBMManager, computeDependentStatistics),
        PyMethodDef(SBMManager, computeDF),
        PyMethodDef(SBMManager, computeDFStatistics),
        PyMethodDef(SBMManager, computeH),
        PyMethodDef(SBMManager, computeIncrementalAlpha),
        PyMethodDef(SBMManager, computeInformationStatistics),
        PyMethodDef(SBMManager, computeL2Statistics),
        PyMethodDef(SBMManager, computePearsonStatistics),
        PyMethodDef(SBMManager, computePercentCorrect),
        PyMethodDef(SBMManager, computeT),
        PyMethodDef(SBMManager, deleteModelFromCache),
        PyMethodDef(SBMManager, deleteTablesFromCache),
        PyMethodDef(SBMManager, getBottomRefModel),
        PyMethodDef(SBMManager, getMemUsage),
        PyMethodDef(SBMManager, getOption),
        PyMethodDef(SBMManager, getOptionList),
        PyMethodDef(SBMManager, getRefModel),
        PyMethodDef(SBMManager, getSampleSz),
        PyMethodDef(SBMManager, getTopRefModel),
        PyMethodDef(SBMManager, hasTestData),
        PyMethodDef(SBMManager, initFromCommandLine),
        PyMethodDef(SBMManager, isDirected),
        PyMethodDef(SBMManager, makeFitTable),
        PyMethodDef(SBMManager, makeSbModel),
        PyMethodDef(SBMManager, printBasicStatistics),
        PyMethodDef(SBMManager, printFitReport),
        PyMethodDef(SBMManager, printOptions),
        PyMethodDef(SBMManager, Report),
        PyMethodDef(SBMManager, searchOneLevel),
        PyMethodDef(SBMManager, setFilter),
        PyMethodDef(SBMManager, setRefModel),
        PyMethodDef(SBMManager, setSearchDirection),
        PyMethodDef(SBMManager, setSearchType),
        { nullptr }
};


/****** Type Definition ******/
PyTypeObject TSBMManager = {
    PyVarObject_HEAD_INIT(&PyType_Type, 0)
    .tp_name            = "SBMManager_cpp",
    .tp_basicsize       = sizeof(PSBMManager),
    .tp_itemsize        = NULL,
    .tp_dealloc         = (destructor) SBMManager_dealloc,
    .tp_print           = nullptr,
    .tp_getattr         = nullptr,
    .tp_setattr         = nullptr,
    .tp_as_async        = nullptr,
    .tp_repr            = nullptr,
    .tp_as_number       = nullptr,
    .tp_as_sequence     = nullptr,
    .tp_as_mapping      = nullptr,
    .tp_hash            = nullptr,
    .tp_call            = nullptr,
    .tp_str             = nullptr,
    .tp_getattro        = nullptr,
    .tp_setattro        = nullptr,
    .tp_as_buffer       = nullptr,
    .tp_flags           = Py_TPFLAGS_DEFAULT,
    .tp_doc             = nullptr,
    .tp_traverse        = nullptr,
    .tp_clear           = nullptr,
    .tp_richcompare     = nullptr,
    .tp_weaklistoffset  = NULL,
    .tp_iter            = nullptr,
    .tp_iternext        = nullptr,
    .tp_methods         = SBMManager_methods,
};

/************************/
/****** Relation ******/
/************************/
static PyObject *
Relation_new(PyObject *self, PyObject *args)
{
    if (!PyArg_ParseTuple(args, ""))
        return NULL;

    PRelation *newobj = ObjNew(Relation);
    newobj->obj = new Relation();
    Py_INCREF(newobj);
    return (PyObject*) newobj;
}

// Object* get(char *name)
DefinePyFunction(Relation, get) {
    Relation *relation = ObjRef(self, Relation);
    char *name;
    PyArg_ParseTuple(args, "s", &name);
    //-- Other attributes
    if (strcmp(name, "name") == 0) {
        const char *printName = relation->getPrintName();
        return PyUnicode_FromString(printName);
    }

    if (strcmp(name, "varcount") == 0) {
        long varcount = relation->getVariableCount();
        return PyLong_FromLong(varcount);
    }

    int attindex = relation->getAttributeList()->getAttributeIndex(name);
    double value;
    if (attindex < 0)
        value = -1;
    else
        value = relation->getAttributeList()->getAttributeByIndex(attindex);
    return PyFloat_FromDouble(value);
}

static struct PyMethodDef Relation_methods[] = {
        PyMethodDef(Relation, get),
        { nullptr }
};

PyTypeObject TRelation = {
    PyVarObject_HEAD_INIT(&PyType_Type, 0)
    .tp_name            = "Relation_cpp",
    .tp_basicsize       = sizeof(PRelation),
    .tp_itemsize        = NULL,
    .tp_dealloc         = nullptr,
    .tp_print           = nullptr,
    .tp_getattr         = nullptr,
    .tp_setattr         = nullptr,
    .tp_as_async        = nullptr,
    .tp_repr            = nullptr,
    .tp_as_number       = nullptr,
    .tp_as_sequence     = nullptr,
    .tp_as_mapping      = nullptr,
    .tp_hash            = nullptr,
    .tp_call            = nullptr,
    .tp_str             = nullptr,
    .tp_getattro        = nullptr,
    .tp_setattro        = nullptr,
    .tp_as_buffer       = nullptr,
    .tp_flags           = Py_TPFLAGS_DEFAULT,
    .tp_doc             = nullptr,
    .tp_traverse        = nullptr,
    .tp_clear           = nullptr,
    .tp_richcompare     = nullptr,
    .tp_weaklistoffset  = NULL,
    .tp_iter            = nullptr,
    .tp_iternext        = nullptr,
    .tp_methods         = Relation_methods,
};

/****** Basic Type Operations ******/

/* commented out because it is currently unused
 static PRelation *
 newPRelation()
 {
 PRelation *self = new PRelation();
 self->obj = new Relation();
 return self;
 }
 */

/* commented out because it is currently unused
 static void
 Relation_dealloc(PRelation *self)
 {
 //-- this doesn't delete the Relation, because these
 //-- are generally borrowed from the cache
 delete self;
 }
 */

/************************/
/****** Model ******/
/************************/

static PyObject *
Model_new(PyObject *self, PyObject *args)
{
    if (!PyArg_ParseTuple(args, ""))
        return NULL;

    PModel *newobj = ObjNew(Model);
    newobj->obj = new Model();
    Py_INCREF(newobj);
    return (PyObject*) newobj;
}

int Model_setattr(PyObject *self, char *name, PyObject *value) {
    double dvalue;
    if (PyFloat_Check(value))
        dvalue = PyFloat_AsDouble(value);
    else if (PyLong_Check(value))
        dvalue = PyLong_AsDouble(value);
    else if (PyLong_Check(value))
        dvalue = (double) PyLong_AsLong(value);
    else
        dvalue = -1;
    ObjRef(self, Model)->setAttribute(name, dvalue);
    return 0;
}

// Relation* getRelation(int index)
DefinePyFunction(Model, getRelation) {
    int index;
    PyArg_ParseTuple(args, "i", &index);
    Model *model = ObjRef(self, Model);
    PRelation *newRelation = ObjNew(Relation);
    newRelation->obj = model->getRelation(index);
    return Py_BuildValue("O", newRelation);
}

// Object* get(char *name)
DefinePyFunction(Model, get) {
    Model *model = ObjRef(self, Model);
    char *name;
    PyArg_ParseTuple(args, "s", &name);
    //-- Other attributes
    if (strcmp(name, "name") == 0) {
        const char *printName = model->getPrintName();
        return PyUnicode_FromString(printName);
    }

    if (strcmp(name, "relcount") == 0) {
        long relcount = model->getRelationCount();
        return PyLong_FromLong(relcount);
    }

    int attindex = model->getAttributeList()->getAttributeIndex(name);
    double value;
    if (attindex < 0)
        value = -1;
    else
        value = model->getAttributeList()->getAttributeByIndex(attindex);
    return PyFloat_FromDouble(value);
}

// void deleteFitTable()
DefinePyFunction(Model, deleteFitTable) {
    Model *model = ObjRef(self, Model);
    model->deleteFitTable();
    Py_INCREF(Py_None);
    return Py_None;
}

// void deleteRelationLinks()
DefinePyFunction(Model, deleteRelationLinks) {
    Model *model = ObjRef(self, Model);
    model->deleteRelationLinks();
    Py_INCREF(Py_None);
    return Py_None;
}

// void setProgenitor(Model* )
DefinePyFunction(Model, setProgenitor) {
    PyObject *Pmodel;
    PyArg_ParseTuple(args, "O!", &TModel, &Pmodel);
    Model *progen = ObjRef(Pmodel, Model);
    Model *model = ObjRef(self, Model);
    model->setProgenitor(progen);
    Py_INCREF(Py_None);
    return Py_None;
}

// Model *getProgenitor()
DefinePyFunction(Model, getProgenitor) {
    PModel *model;
    PyArg_ParseTuple(args, "");
    model = ObjNew(Model);
    model->obj = ObjRef(self, Model)->getProgenitor();
    Py_INCREF((PyObject*)model);
    return (PyObject*) model;
}

// void setID()
DefinePyFunction(Model, setID) {
    int ID;
    PyArg_ParseTuple(args, "i", &ID);
    Model *model = ObjRef(self, Model);
    model->setID(ID);
    Py_INCREF(Py_None);
    return Py_None;
}

// bool isEquivalentTo(Model*)
DefinePyFunction(Model, isEquivalentTo) {
    PyObject *Pmodel;
    PyArg_ParseTuple(args, "O!", &TModel, &Pmodel);
    Model *other = ObjRef(Pmodel, Model);
    Model *model = ObjRef(self, Model);
    bool equivTest = model->isEquivalentTo(other);
    return Py_BuildValue("i", equivTest ? 1 : 0);
}

// void dump()
DefinePyFunction(Model, dump) {
    Model *model = ObjRef(self, Model);
    model->dump();
    Py_INCREF(Py_None);
    return Py_None;
}

DefinePyFunction(Model, getPrintName)
{
    Model *model = ObjRef(self, Model);

    if(!model)
    {
        Py_INCREF(Py_None);
        return Py_None;
    }

    return PyUnicode_FromString(model->getPrintName());
}

static struct PyMethodDef Model_methods[] = {
    PyMethodDef(Model, deleteFitTable),
    PyMethodDef(Model, deleteRelationLinks),
    PyMethodDef(Model, dump),
    PyMethodDef(Model, get),
    PyMethodDef(Model, getProgenitor),
    PyMethodDef(Model, getRelation),
    PyMethodDef(Model, isEquivalentTo),
    PyMethodDef(Model, setID),
    PyMethodDef(Model, setProgenitor),
    PyMethodDef(Model, getPrintName),
    { nullptr }
};

/****** Type Definition ******/
PyTypeObject TModel = {
    PyVarObject_HEAD_INIT(&PyType_Type, 0)
    .tp_name            = "Model_cpp",
    .tp_basicsize       = sizeof(PModel),
    .tp_itemsize        = NULL,
    .tp_dealloc         = nullptr,
    .tp_print           = nullptr,
    .tp_getattr         = nullptr,
    .tp_setattr         = nullptr,
    .tp_as_async        = nullptr,
    .tp_repr            = nullptr,
    .tp_as_number       = nullptr,
    .tp_as_sequence     = nullptr,
    .tp_as_mapping      = nullptr,
    .tp_hash            = nullptr,
    .tp_call            = nullptr,
    .tp_str             = nullptr,
    .tp_getattro        = nullptr,
    .tp_setattro        = (setattrofunc) Model_setattr,
    .tp_as_buffer       = nullptr,
    .tp_flags           = Py_TPFLAGS_DEFAULT,
    .tp_doc             = nullptr,
    .tp_traverse        = nullptr,
    .tp_clear           = nullptr,
    .tp_richcompare     = nullptr,
    .tp_weaklistoffset  = NULL,
    .tp_iter            = nullptr,
    .tp_iternext        = nullptr,
    .tp_methods         = Model_methods,
};

/************************/
/****** Report ******/
/************************/

// Object* get(char *name)
DefinePyFunction(Report, get) {
    Report *report = ObjRef(self, Report);
    TRACE_FN("Report::get", __LINE__, report);
    char *name;
    PyArg_ParseTuple(args, "s", &name);
    //-- none defined
    TRACE_FN("Report::get", __LINE__, 0);
    return NULL;
}

// void addModel(Model *model)
DefinePyFunction(Report, addModel) {
    Report *report = ObjRef(self, Report);
    TRACE_FN("Report::addModel", __LINE__, report);
    PModel *pmodel;
    Model *model;
    PyArg_ParseTuple(args, "O", &pmodel);
    model = pmodel->obj;
    report->addModel(model);
    Py_INCREF(Py_None);
    TRACE_FN("Report::addModel", __LINE__, 0);
    return Py_None;
}

// void setDefaultFitModel(Model *model)
DefinePyFunction(Report, setDefaultFitModel) {
    Report *report = ObjRef(self, Report);
    TRACE_FN("Report::setDefaultFitModel", __LINE__, report);
    PModel *pmodel;
    Model *model;
    PyArg_ParseTuple(args, "O", &pmodel);
    model = pmodel->obj;
    report->setDefaultFitModel(model);
    Py_INCREF(Py_None);
    TRACE_FN("Report::setDefaultFitModel", __LINE__, 0);
    return Py_None;
}

// void setAttributes(char *attrList)
DefinePyFunction(Report, setAttributes) {
    Report *report = ObjRef(self, Report);
    TRACE_FN("Report::setAttributes", __LINE__, report);
    char *attrList;
    PyArg_ParseTuple(args, "s", &attrList);
    report->setAttributes(attrList);
    Py_INCREF(Py_None);
    TRACE_FN("Report::setAttributes", __LINE__, 0);
    return Py_None;
}

// void sort(char *attr, char *direction) "ascending" or "descending"
DefinePyFunction(Report, sort) {
    Report *report = ObjRef(self, Report);
    TRACE_FN("Report::sort", __LINE__, report);
    char *attr;
    char *direction;
    PyArg_ParseTuple(args, "ss", &attr, &direction);
    if (strcasecmp(direction, "ascending") == 0) {
        report->sort(attr, Direction::Ascending);
    } else if (strcasecmp(direction, "descending") == 0) {
        report->sort(attr, Direction::Descending);
    } else {
        onError("Invalid sort direction");
    }
    Py_INCREF(Py_None);
    TRACE_FN("Report::sort", __LINE__, 0);
    return Py_None;
}

// void setSeparator(int sep) 1=tab, 2=comma, 3=space filled, 4=HTML
DefinePyFunction(Report, setSeparator) {
    Report *report = ObjRef(self, Report);
    TRACE_FN("Report::setSeparator", __LINE__, report);
    int sep;
    PyArg_ParseTuple(args, "i", &sep);
    report->setSeparator(sep < 4 ? sep : 1);
    report->setHTMLMode(sep == 4);
    Py_INCREF(Py_None);
    TRACE_FN("Report::setSeparator", __LINE__, 0);
    return Py_None;
}

// void printReport()
DefinePyFunction(Report, printReport) {
    Report *report = ObjRef(self, Report);
    TRACE_FN("Report::printReport", __LINE__, report);
    PyArg_ParseTuple(args, "");
    report->print(stdout);
    Py_INCREF(Py_None);
    TRACE_FN("Report::printReport", __LINE__, 0);
    return Py_None;
}

// void writeReport(const char *name)
DefinePyFunction(Report, writeReport) {
    Report *report = ObjRef(self, Report);
    const char *file;
    TRACE_FN("Report::printReport", __LINE__, report);
    PyArg_ParseTuple(args, "s", &file);
    FILE *fd = fopen(file, "w");
    if (fd == NULL)
        onError("cannot open file");
    report->print(fd);
    fclose(fd);
    Py_INCREF(Py_None);
    TRACE_FN("Report::printReport", __LINE__, 0);
    return Py_None;
}

// void printResiduals(Model *model)
DefinePyFunction(Report, printResiduals) {
    PyObject *Pmodel;
    int skipTrainedTable;
    int skipIVItables;
    PyArg_ParseTuple(args, "O!ii", &TModel, &Pmodel, &skipTrainedTable, &skipIVItables);
    Model *model = ObjRef(Pmodel, Model);

    ObjRef(self, Report)->printResiduals(stdout, model, skipTrainedTable, skipIVItables);
    Py_INCREF(Py_None);
    return Py_None;
}

// void printConditional_DV(Model *model)
DefinePyFunction(Report, printConditional_DV) {
    PyObject *Pmodel;
    int calcExpectedDV;
    char* classTarget;
    bool bCalcExpectedDV = false;
    PyArg_ParseTuple(args, "O!is", &TModel, &Pmodel, &calcExpectedDV, &classTarget);
    if (calcExpectedDV != 0)
        bCalcExpectedDV = true;
    Model *model = ObjRef(Pmodel, Model);
    ObjRef(self, Report)->printConditional_DV(stdout, model, bCalcExpectedDV, classTarget);
    Py_INCREF(Py_None);
    return Py_None;
}


DefinePyFunction(Report, bestModelName) {
    Report* report = ObjRef(self, Report);
    const char* ret = report->bestModelName();
    return Py_BuildValue("s", ret);
}

DefinePyFunction(Report, dvName) {
    Report* report = ObjRef(self, Report);
    VBMManager* mgr = dynamic_cast<VBMManager*>(report->manager);
    VariableList* varlist = mgr->getVariableList();
    const char* abbrev = varlist->getVariable(varlist->getDV())->abbrev;
    PyObject* name = PyUnicode_FromString(abbrev);
    return name;
}

DefinePyFunction(Report, variableList) {
    Report* report = ObjRef(self, Report);
    VBMManager* mgr = dynamic_cast<VBMManager*>(report->manager);
    VariableList* varlist = mgr->getVariableList();
    long var_count = varlist->getVarCount();

    PyObject* ret = PyList_New(var_count);
    for (long i = 0; i < var_count; ++i) {

        const char* printName = varlist->getVariable(i)->name;
        const char* abbrevName = varlist->getVariable(i)->abbrev;
        PyObject* name = PyUnicode_FromString(printName);
        PyObject* abbrev = PyUnicode_FromString(abbrevName);
        PyObject* names = PyTuple_Pack(2,name,abbrev);
        PyList_SetItem(ret, i, names);
    }

    return ret;
}

DefinePyFunction(Report, bestModelData) {
    // Get the report and the manager


    // RESUME

    Report* report = ObjRef(self, Report);
    VBMManager* mgr = dynamic_cast<VBMManager*>(report->manager);

    // Get the best model name
    const char* bestModelName = report->bestModelName();

    // Get the overall data
    Table* input = mgr->getInputData();
    VariableList* varlist = mgr->getVariableList();
    long var_count = varlist->getVarCount();
    Model* mod = mgr->makeModel(bestModelName, true);
    mgr->computeL2Statistics(mod);
    mgr->computeDFStatistics(mod);
    mgr->computeDependentStatistics(mod);
    mgr->makeFitTable(mod);
    Table* fit = mgr->getFitTable();
    fit->normalize();

    // DEBUG: print out the model using an iterator
    // Do a string/double KV iteration over the fit table
    //auto printer = [](char* key, double value) {
    //    printf("%s: %g, \n", key, value);
    //};
    //tableKVIteration(fit, varlist, var_count, printer);

    // Get statistics for the best model

    Model* data = mgr->getTopRefModel();

    mgr->computeH(mod);
    mgr->computeL2Statistics(mod);
    mgr->computeH(data);
    mgr->computeL2Statistics(data);

    double h_model = mod->getAttribute(ATTRIBUTE_H);
    double df_model = mod->getAttribute(ATTRIBUTE_DF);
    double aic_model = mod->getAttribute(ATTRIBUTE_AIC);
    double bic_model = mod->getAttribute(ATTRIBUTE_BIC);
    double h_data = data->getAttribute(ATTRIBUTE_H);
    double df_data = data->getAttribute(ATTRIBUTE_DF);
    double aic_data = data->getAttribute(ATTRIBUTE_AIC);
    double bic_data = data->getAttribute(ATTRIBUTE_BIC);

    // Make Python dictionary holding fit table for the best model
    // (as a sparse dictionary of (key, probability))

    PyObject *sparseTable = PyDict_New();
    auto dictPopulator = [&sparseTable](char* key, double value) {
        PyObject *keyP = Py_BuildValue("s", key);
        PyObject *valueP = Py_BuildValue("d", value);
        PyDict_SetItem(sparseTable, keyP, valueP);
    };
    tableKVIteration(fit, varlist, var_count, dictPopulator);

    // Make a Python object to hold everything
    PyObject *ret = Py_BuildValue(
        "{s:s,s:O,s:d,s:d,s:d,s:d,s:d,s:d,s:d,s:d}",
            "name", bestModelName,
            "sparse_table", sparseTable,
            "H(model)",  h_model,
            "DF(model)", df_model,
            "dAIC(model)", aic_model,
            "dBIC(model)", bic_model,
            "H(data)", h_data,
            "DF(data)", df_data,
            "dAIC(data)", aic_data,
            "dBIC(data)", bic_data
            );

    return ret;
}


static struct PyMethodDef Report_methods[] = {
    PyMethodDef(Report, addModel),
    PyMethodDef(Report, bestModelData),
    PyMethodDef(Report, bestModelName),
    PyMethodDef(Report, dvName),
    PyMethodDef(Report, get),
    PyMethodDef(Report, printConditional_DV),
    PyMethodDef(Report, printReport),
    PyMethodDef(Report, printResiduals),
    PyMethodDef(Report, setAttributes),
    PyMethodDef(Report, setDefaultFitModel),
    PyMethodDef(Report, setSeparator),
    PyMethodDef(Report, sort),
    PyMethodDef(Report, variableList),
    PyMethodDef(Report, writeReport),
    { nullptr }
};

/****** Type Definition ******/
PyTypeObject TReport = {
    PyVarObject_HEAD_INIT(&PyType_Type, 0)
    .tp_name            = "Report_cpp",
    .tp_basicsize       = sizeof(PReport),
    .tp_itemsize        = NULL,
    .tp_dealloc         = nullptr,
    .tp_print           = nullptr,
    .tp_getattr         = nullptr,
    .tp_setattr         = nullptr,
    .tp_as_async        = nullptr,
    .tp_repr            = nullptr,
    .tp_as_number       = nullptr,
    .tp_as_sequence     = nullptr,
    .tp_as_mapping      = nullptr,
    .tp_hash            = nullptr,
    .tp_call            = nullptr,
    .tp_str             = nullptr,
    .tp_getattro        = nullptr,
    .tp_setattro        = nullptr,
    .tp_as_buffer       = nullptr,
    .tp_flags           = Py_TPFLAGS_DEFAULT,
    .tp_doc             = nullptr,
    .tp_traverse        = nullptr,
    .tp_clear           = nullptr,
    .tp_richcompare     = nullptr,
    .tp_weaklistoffset  = NULL,
    .tp_iter            = nullptr,
    .tp_iternext        = nullptr,
    .tp_methods         = Report_methods,
};


/*
    VariableList definition
*/

/*
*   Called when an iterator is requested
*   Similar to __iter__ function in python
*/
PyObject* variable_list_iter(PyObject *self)
{
    PVariableList *py_variable_list = (PVariableList *)self;

    // Set the starting and ending indexes used by the iterator
    py_variable_list->current_it_index = 0;
    py_variable_list->max_it_index = py_variable_list->obj->getVarCount();

    Py_INCREF(self);

    return self;
}

/*
*   Called when the next item from the iterator is requested
*   Similar to __next__ function in python
*/
PyObject* variable_list_iternext(PyObject *self)
{
    PVariableList *py_variable_list = (PVariableList *)self;

    // Iterator reached the end
    if (py_variable_list->current_it_index >= py_variable_list->max_it_index)
    {
        // Raising of standard StopIteration exception with empty value.
        PyErr_SetNone(PyExc_StopIteration);
        return NULL;
    }

    // Create a new Variable object and return it
    PVariable *py_variable = ObjNew(Variable);
    VariableList *variable_list = py_variable_list->obj;

    py_variable->obj = variable_list->getVariable(py_variable_list->current_it_index);
    py_variable_list->current_it_index++;

    Py_INCREF(py_variable);

    return (PyObject *)py_variable;
}

DefinePyFunction(VariableList, getVarCount)
{
    VariableList *variable_list = ObjRef(self, VariableList);

    return PyLong_FromLong(variable_list->getVarCount());
}

DefinePyFunction(VariableList, getVariable)
{
    int index;
    PyArg_ParseTuple(args, "i", &index);

    VariableList *variable_list = ObjRef(self, VariableList);

    // Create a new Variable object and return it
    PVariable *py_variable = ObjNew(Variable);
    py_variable->obj = variable_list->getVariable(index);

    Py_INCREF(py_variable);

    return (PyObject *)py_variable;
}

DefinePyFunction(VariableList, isDirected)
{
    VariableList *variable_list = ObjRef(self, VariableList);

    if(variable_list->isDirected())
    {
        Py_INCREF(Py_True);
        return Py_True;
    }

    Py_INCREF(Py_False);
    return Py_False;
}

static struct PyMethodDef VariableList_methods[] = 
{
    PyMethodDef(VariableList, getVarCount),
    PyMethodDef(VariableList, getVariable),
    PyMethodDef(VariableList, isDirected),
    { nullptr }
};


PyTypeObject TVariableList = {
    PyVarObject_HEAD_INIT(&PyType_Type, 0)
    .tp_name            = "VariableList_cpp",
    .tp_basicsize       = sizeof(PVariableList),
    .tp_itemsize        = NULL,
    .tp_dealloc         = nullptr,
    .tp_print           = nullptr,
    .tp_getattr         = nullptr,
    .tp_setattr         = nullptr,
    .tp_as_async        = nullptr,
    .tp_repr            = nullptr,
    .tp_as_number       = nullptr,
    .tp_as_sequence     = nullptr,
    .tp_as_mapping      = nullptr,
    .tp_hash            = nullptr,
    .tp_call            = nullptr,
    .tp_str             = nullptr,
    .tp_getattro        = nullptr,
    .tp_setattro        = nullptr,
    .tp_as_buffer       = nullptr,
    .tp_flags           = Py_TPFLAGS_DEFAULT,
    .tp_doc             = nullptr,
    .tp_traverse        = nullptr,
    .tp_clear           = nullptr,
    .tp_richcompare     = nullptr,
    .tp_weaklistoffset  = NULL,
    .tp_iter            = variable_list_iter,
    .tp_iternext        = variable_list_iternext,
    .tp_methods         = VariableList_methods
};

/*
    Variable definition
*/

DefinePyFunction(Variable, getAbbrev)
{
    Variable *variable = ObjRef(self, Variable);

    return PyUnicode_FromString(variable->getAbbrev());
}

static struct PyMethodDef Variable_methods[] =
{
    PyMethodDef(Variable, getAbbrev),
    { nullptr }
};

PyTypeObject TVariable = {
    PyVarObject_HEAD_INIT(&PyType_Type, 0)
    .tp_name            = "Variable_cpp",
    .tp_basicsize       = sizeof(PVariable),
    .tp_itemsize        = NULL,
    .tp_dealloc         = nullptr,
    .tp_print           = nullptr,
    .tp_getattr         = nullptr,
    .tp_setattr         = nullptr,
    .tp_as_async        = nullptr,
    .tp_repr            = nullptr,
    .tp_as_number       = nullptr,
    .tp_as_sequence     = nullptr,
    .tp_as_mapping      = nullptr,
    .tp_hash            = nullptr,
    .tp_call            = nullptr,
    .tp_str             = nullptr,
    .tp_getattro        = nullptr,
    .tp_setattro        = nullptr,
    .tp_as_buffer       = nullptr,
    .tp_flags           = Py_TPFLAGS_DEFAULT,
    .tp_doc             = nullptr,
    .tp_traverse        = nullptr,
    .tp_clear           = nullptr,
    .tp_richcompare     = nullptr,
    .tp_weaklistoffset  = NULL,
    .tp_iter            = nullptr,
    .tp_iternext        = nullptr,
    .tp_methods         = Variable_methods,
};

/**************************/
/****** MODULE LOGIC ******/
/**************************/

static PyObject *setHTMLMode(PyObject *self, PyObject *args) {
    int mode;
    if (!PyArg_ParseTuple(args, "i", &mode))
        return NULL;
    Report::setHTMLMode(mode != 0);
    Py_INCREF(Py_None);
    return Py_None;
}

static struct PyMethodDef occam_methods[] = {
    { "Relation",    (PyCFunction) Relation_new,    METH_VARARGS},
    { "Model",       (PyCFunction) Model_new,       METH_VARARGS},
    { "VBMManager",  (PyCFunction) VBMManager_new,  METH_VARARGS},
    { "SBMManager",  (PyCFunction) SBMManager_new,  METH_VARARGS},
    { "setHTMLMode", (PyCFunction) setHTMLMode,     METH_VARARGS},
    {nullptr}
};

static struct PyModuleDef occam =
{
    PyModuleDef_HEAD_INIT,
    "occam3",     /* name of module */
    "",          /* module documentation, may be NULL */
    -1,          /* size of per-interpreter state of the module, or -1 if the module keeps state in global variables. */
    occam_methods
};

PyMODINIT_FUNC PyInit_occam(void)
{
    Py_Initialize();
    PyObject *m = PyModule_Create(&occam);

    if (PyType_Ready(&TRelation) < 0)
        return NULL;
    if (PyType_Ready(&TModel) < 0)
        return NULL;
    if (PyType_Ready(&TVBMManager) < 0)
        return NULL;
    if (PyType_Ready(&TSBMManager) < 0)
        return NULL;
    if (PyType_Ready(&TReport) < 0)
        return NULL;
    if (PyType_Ready(&TVariableList) < 0)
        return NULL;
    if (PyType_Ready(&TVariable) < 0)
        return NULL;

    return m;
}