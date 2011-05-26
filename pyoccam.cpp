/*
 * pyoccam.cpp - defines wrapper functions to map C classes to Python
 */

//-- Hack to get around Python platform checking
#include "Python.h"
#include "ocCore.h"
#include "ocVBMManager.h"
#include "ocSearchBase.h"
#include "ocReport.h"
#include "ocWin32.h"
#include "unistd.h"
#include "ocSBMManager.h"


#if defined(_WIN32) || defined(__WIN32__)
#	if defined(STATIC_LINKED)
#       define SWIGEXPORT(a) a
#   else
#       define SWIGEXPORT(a) __declspec(dllexport) a
#   endif
#else
#  define SWIGEXPORT(a) a
#endif

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


//-- Trace output
#ifdef TRACE_ON
#define TRACE printf
#define TRACE_FN(name, line, obj) {TRACE("Trace: %s (%ld), %0lx\n", name, line, obj); fflush(stdout);}
#else
void notrace(...) {}
#define TRACE notrace
#define TRACE_FN notrace
#endif


static PyObject *ErrorObject;	/* local exception */


/****** Occam object types *****/
DefinePyObject(ocVBMManager);
DefinePyObject(ocSBMManager);

DefinePyObject(ocRelation);
DefinePyObject(ocModel);
DefinePyObject(ocReport);

/**************************/
/****** ocVBMManager ******/
/**************************/

/****** Methods ******/

// Constructor
DefinePyFunction(ocVBMManager, initFromCommandLine)
{
    PyObject *Pargv;
    PyArg_ParseTuple(args, "O!", &PyList_Type, &Pargv);
    int argc = PyList_Size(Pargv);
    char **argv = new char*[argc];
    int i;
    for (i = 0; i < argc; i++) {
        PyObject *PString = PyList_GetItem(Pargv, i);
        int size = PyString_Size(PString);
        argv[i] = new char[size+1];
        strcpy(argv[i], PyString_AsString(PString));
    }
    bool ret;
    ret = ObjRef(self, ocVBMManager)->initFromCommandLine(argc, argv);
    for (i = 0; i < argc; i++) delete [] argv[i];
    delete [] argv;
    if (!ret)
    {
        onError("ocVBMManager: initialization failed");
    }
    Py_INCREF(Py_None);
    return Py_None;
}


// ocRelation **makeAllChildRelations(ocRelation *, bool makeProject)
DefinePyFunction(ocVBMManager, makeAllChildRelations)
{
    PocRelation *rel;
    int makeProject;
    bool bMakeProject;
    PyArg_ParseTuple(args, "O!i)", &TocRelation, &rel, &makeProject);
    bMakeProject = (makeProject != 0);
    int count = rel->obj->getVariableCount();
    ocRelation **rels = new ocRelation*[count];
    ObjRef(self, ocVBMManager)->makeAllChildRelations(
            rel->obj, rels, bMakeProject);
    PyObject *list = PyList_New(count);
    int i;
    for (i = 0; i < count; i++) {
        rel = ObjNew(ocRelation);
        rel->obj = rels[i];	// move relation to the python object
        rels[i] = NULL;
        PyList_SetItem(list, i, (PyObject*)rel);
    }
    delete rels;
    Py_INCREF(list);
    return list;
}


// ocModel **searchOneLevel(ocModel *)
DefinePyFunction(ocVBMManager, searchOneLevel)
{
    PocModel *start;
    PocModel *pmodel;
    PyArg_ParseTuple(args, "O!", &TocModel, &start);
    ocModel **models;
    ocVBMManager *mgr = ObjRef(self, ocVBMManager);
    if (mgr->getSearch() == NULL) {
        onError("No search method defined");
    }
    if (start->obj == NULL) onError("Model is NULL!");
    models = mgr->getSearch()->search(start->obj);

    ocModel **model;
    long count = 0;
    //-- count the models
    if (models) for (model = models; *model; model++) count++;

    //-- sort them if sort was requested
    if (mgr->getSortAttr()) {
        ocReport::sort(models, count, mgr->getSortAttr(), (ocReport::SortDir) mgr->getSortDirection());
    }

    //-- make a PyList
    PyObject *list = PyList_New(count);
    int i;
    for (i = 0; i < count; i++) {
        pmodel = ObjNew(ocModel);
        pmodel->obj = models[i];
        PyList_SetItem(list, i, (PyObject*)pmodel);
    }
    delete [] models;
    Py_INCREF(list);
    return list;
}


// void setSearchType(const char *name)
DefinePyFunction(ocVBMManager, setSearchType)
{
    char *name;
    PyArg_ParseTuple(args, "s", &name);
    ocVBMManager *mgr = ObjRef(self, ocVBMManager);
    mgr->setSearch(name);
    if (mgr->getSearch() == NULL) { // invalid search method name
        onError("undefined search type");
    } else {
        Py_INCREF(Py_None);
        return Py_None;
    }
}


// ocModel *makeChildModel(ocModel *, int relation, bool makeProjection)
DefinePyFunction(ocVBMManager, makeChildModel)
{
    PocModel *Pmodel;
    int makeProject, relation;
    bool bMakeProject;
    bool cache;
    PyArg_ParseTuple(args, "O!ii", TocModel, &Pmodel, &relation, &makeProject);
    bMakeProject = makeProject != 0;
    ocModel *model = Pmodel->obj;
    if (model == NULL) onError("Model is NULL!");
    //-- if this relation is trivial, return None
    if (model->getRelation(relation)->getVariableCount() <= 1) {
        Py_INCREF(Py_None);
        return Py_None;
    }
    ocModel *ret = ObjRef(self, ocVBMManager)->makeChildModel(
            Pmodel->obj, relation, &cache, bMakeProject);
    if (ret == NULL) onError("invalid arguments");
    PocModel *newModel = ObjNew(ocModel);
    newModel->obj = ret;
    return Py_BuildValue("O", newModel);
}


// ocModel *getTopRefModel()
DefinePyFunction(ocVBMManager, getTopRefModel)
{
    //TRACE("getTopRefModel\n");
    PocModel *model;
    PyArg_ParseTuple(args, "");
    model = ObjNew(ocModel);
    model->obj = ObjRef(self, ocVBMManager)->getTopRefModel();
    Py_INCREF((PyObject*)model);
    return (PyObject*) model;
}


// ocModel *getBottomRefModel()
DefinePyFunction(ocVBMManager, getBottomRefModel)
{
    //TRACE("getBottomRefModel\n");
    PocModel *model;
    PyArg_ParseTuple(args, "");
    model = ObjNew(ocModel);
    model->obj = ObjRef(self, ocVBMManager)->getBottomRefModel();
    Py_INCREF((PyObject*)model);
    return (PyObject*) model;
}


// ocModel *getRefModel()
DefinePyFunction(ocVBMManager, getRefModel)
{
    //TRACE("getRefModel\n");
    PocModel *model;
    PyArg_ParseTuple(args, "");
    model = ObjNew(ocModel);
    model->obj = ObjRef(self, ocVBMManager)->getRefModel();
    Py_INCREF((PyObject*)model);
    return (PyObject*) model;
}


// ocModel *setRefModel()
DefinePyFunction(ocVBMManager, setRefModel)
{
    char *name;
    PyArg_ParseTuple(args, "s", &name);
    ocModel *ret = ObjRef(self, ocVBMManager)->setRefModel(name);
    if (ret == NULL) onError("invalid model name");
    PocModel *newModel = ObjNew(ocModel);
    newModel->obj = ret;
    return Py_BuildValue("O", newModel);
}


// long computeDF(ocModel *model)
DefinePyFunction(ocVBMManager, computeDF)
{
    PyObject *Pmodel;
    PyArg_ParseTuple(args, "O!", &TocModel, &Pmodel);
    ocModel *model = ObjRef(Pmodel, ocModel);
    double df = ObjRef(self, ocVBMManager)->computeDF(model);
    return Py_BuildValue("d", df);
}



// double computeH(ocModel *model)
DefinePyFunction(ocVBMManager, computeH)
{
    PyObject *Pmodel;
    PyArg_ParseTuple(args, "O!", &TocModel, &Pmodel);
    ocModel *model = ObjRef(Pmodel, ocModel);
    if (model == NULL) onError("Model is NULL!");
    double h = ObjRef(self, ocVBMManager)->computeH(model);
    return Py_BuildValue("d", h);
}


// double computeT(ocModel *model)
DefinePyFunction(ocVBMManager, computeT)
{
    PyObject *Pmodel;
    PyArg_ParseTuple(args, "O!", &TocModel, &Pmodel);
    ocModel *model = ObjRef(Pmodel, ocModel);
    if (model == NULL) onError("Model is NULL!");
    double t = ObjRef(self, ocVBMManager)->computeTransmission(model, ocVBMManager::ALGEBRAIC);
    return Py_BuildValue("d", t);
}


// void computeInformationStatistics(ocModel *model)
DefinePyFunction(ocVBMManager, computeInformationStatistics)
{
    PyObject *Pmodel;
    PyArg_ParseTuple(args, "O!", &TocModel, &Pmodel);
    ocModel *model = ObjRef(Pmodel, ocModel);
    if (model == NULL) onError("Model is NULL!");
    ObjRef(self, ocVBMManager)->computeInformationStatistics(model);
    Py_INCREF(Py_None);
    return Py_None;
}


// void computeDFStatistics(ocModel *model)
DefinePyFunction(ocVBMManager, computeDFStatistics)
{
    PyObject *Pmodel;
    PyArg_ParseTuple(args, "O!", &TocModel, &Pmodel);
    ocModel *model = ObjRef(Pmodel, ocModel);
    if (model == NULL) onError("Model is NULL!");
    ObjRef(self, ocVBMManager)->computeDFStatistics(model);
    Py_INCREF(Py_None);
    return Py_None;
}


// void computeL2Statistics(ocModel *model)
DefinePyFunction(ocVBMManager, computeL2Statistics)
{
    PyObject *Pmodel;
    PyArg_ParseTuple(args, "O!", &TocModel, &Pmodel);
    ocModel *model = ObjRef(Pmodel, ocModel);
    if (model == NULL) onError("Model is NULL!");
    ObjRef(self, ocVBMManager)->computeL2Statistics(model);
    Py_INCREF(Py_None);
    return Py_None;
}


// void computePearsonStatistics(ocModel *model)
DefinePyFunction(ocVBMManager, computePearsonStatistics)
{
    PyObject *Pmodel;
    PyArg_ParseTuple(args, "O!", &TocModel, &Pmodel);
    ocModel *model = ObjRef(Pmodel, ocModel);
    if (model == NULL) onError("Model is NULL!");
    ObjRef(self, ocVBMManager)->computePearsonStatistics(model);
    Py_INCREF(Py_None);
    return Py_None;
}


// void computeDependentStatistics(ocModel *model)
DefinePyFunction(ocVBMManager, computeDependentStatistics)
{
    PyObject *Pmodel;
    PyArg_ParseTuple(args, "O!", &TocModel, &Pmodel);
    ocModel *model = ObjRef(Pmodel, ocModel);
    if (model == NULL) onError("Model is NULL!");
    ObjRef(self, ocVBMManager)->computeDependentStatistics(model);
    Py_INCREF(Py_None);
    return Py_None;
}


// void computeBPStatistics(ocModel *model)
DefinePyFunction(ocVBMManager, computeBPStatistics)
{
    PyObject *Pmodel;
    PyArg_ParseTuple(args, "O!", &TocModel, &Pmodel);
    ocModel *model = ObjRef(Pmodel, ocModel);
    if (model == NULL) onError("Model is NULL!");
    ObjRef(self, ocVBMManager)->computeBPStatistics(model);
    Py_INCREF(Py_None);
    return Py_None;
}


// void computeIncrementalAlpha(ocModel *model)
DefinePyFunction(ocVBMManager, computeIncrementalAlpha)
{
    PyObject *Pmodel;
    PyArg_ParseTuple(args, "O!", &TocModel, &Pmodel);
    ocModel *model = ObjRef(Pmodel, ocModel);
    if (model == NULL) onError("Model is NULL!");
    ObjRef(self, ocVBMManager)->computeIncrementalAlpha(model);
    Py_INCREF(Py_None);
    return Py_None;
}


// void compareProgenitors(ocModel *model, ocModel *newProgen)
DefinePyFunction(ocVBMManager, compareProgenitors)
{
    PyObject *Pmodel, *Pprogen;
    PyArg_ParseTuple(args, "O!O!", &TocModel, &Pmodel, &TocModel, &Pprogen);
    ocModel *model = ObjRef(Pmodel, ocModel);
    ocModel *progen = ObjRef(Pprogen, ocModel);
    if (model == NULL) onError("Model is NULL.");
    if (progen == NULL) onError("Progen is NULL.");
    ObjRef(self, ocVBMManager)->compareProgenitors(model, progen);
    Py_INCREF(Py_None);
    return Py_None;
}


// ocModel *makeModel(String name, bool makeProject)
DefinePyFunction(ocVBMManager, makeModel)
{
    char *name;
    int makeProject;
    bool bMakeProject;
    PyArg_ParseTuple(args, "si", &name, &makeProject);
    bMakeProject = makeProject != 0;
    ocModel *ret = ObjRef(self, ocVBMManager)->makeModel(name, bMakeProject);
    if (ret == NULL) {
        onError("invalid model name");
        exit(1);
    }
    PocModel *newModel = ObjNew(ocModel);
    newModel->obj = ret;
    return Py_BuildValue("O", newModel);
}


// void setFilter(String attrName, String op, double value)
DefinePyFunction(ocVBMManager, setFilter)
{
    char *attrName;
    const char *relOp;
    double attrValue;
    ocVBMManager::RelOp op;
    PyArg_ParseTuple(args, "ssd", &attrName, &relOp, &attrValue);
    if (strcmp(relOp, "<") == 0 || strcasecmp(relOp, "lt") == 0)
        op = ocVBMManager::LESSTHAN;
    else if (strcmp(relOp, "=") == 0 || strcasecmp(relOp, "eq") == 0)
        op = ocVBMManager::EQUALS;
    else if (strcmp(relOp, ">") == 0 || strcasecmp(relOp, "gt") == 0)
        op = ocVBMManager::GREATERTHAN;
    else {
        onError("Invalid comparison operator");
    }
    ObjRef(self, ocVBMManager)->setFilter(attrName, attrValue, op);
    Py_INCREF(Py_None);
    return Py_None;
}


/* commented out because it is currently unused
// void setSort(String attrName, String dir)
DefinePyFunction(ocVBMManager, setSort)
{
char *attrName;
const char *dir;
PyArg_ParseTuple(args, "ss", &attrName, &dir);
ocVBMManager *mgr = ObjRef(self, ocVBMManager);
mgr->setSortAttr(attrName);
if (strcasecmp(dir, "ascending") == 0)
mgr->setSortDirection(ocReport::ASCENDING);
else if (strcasecmp(dir, "descending") == 0)
mgr->setSortDirection(ocReport::DESCENDING);
else {
onError("Invalid sort direction");
}
Py_INCREF(Py_None);
return Py_None;
}
 */


// void setDDFMethod(int method)
DefinePyFunction(ocVBMManager, setDDFMethod)
{
    int meth;
    PyArg_ParseTuple(args, "i", &meth);
    ObjRef(self, ocVBMManager)->setDDFMethod(meth);
    Py_INCREF(Py_None);
    return Py_None;
}


// void setUseInverseNotation(int method)
DefinePyFunction(ocVBMManager, setUseInverseNotation)
{
    int flag;
    PyArg_ParseTuple(args, "i", &flag);
    ObjRef(self, ocVBMManager)->setUseInverseNotation(flag);
    Py_INCREF(Py_None);
    return Py_None;
}


// void setSearchDirection(int dir)
// 0 = up, 1 = down
DefinePyFunction(ocVBMManager, setSearchDirection)
{
    int dir;
    PyArg_ParseTuple(args, "i", &dir);
    ObjRef(self, ocVBMManager)->setSearchDirection(dir);
    Py_INCREF(Py_None);
    return Py_None;
}


// void printFitReport(ocModel *model)
DefinePyFunction(ocVBMManager, printFitReport)
{
    PyObject *Pmodel;
    PyArg_ParseTuple(args, "O!", &TocModel, &Pmodel);
    ocModel *model = ObjRef(Pmodel, ocModel);
    if (model == NULL) onError("Model is NULL!");
    ObjRef(self, ocVBMManager)->printFitReport(model, stdout);
    Py_INCREF(Py_None);
    return Py_None;
}


// void getOption(const char *name)
DefinePyFunction(ocVBMManager, getOption)
{
    char *attrName;
    PyArg_ParseTuple(args, "s", &attrName);
    const char *value;
    void *nextp = NULL;
    if (!ObjRef(self, ocVBMManager)->getOptionString(attrName, &nextp, &value))
    {
        value = "";
    }
    return Py_BuildValue("s", value);
}


DefinePyFunction(ocVBMManager, getOptionList)
{
    char *attrName;
    PyArg_ParseTuple(args, "s", &attrName);
    const char *value;
    void *nextp = NULL;
    PyObject *list = PyList_New(0);
    while(ObjRef(self, ocVBMManager)->getOptionString(attrName, &nextp, &value) &&
            nextp != NULL)
    {
        PyObject *valstr = Py_BuildValue("s", value);
        PyList_Append(list, valstr);
    }
    Py_INCREF(list);
    return list;
}


// ocModel *ocReport()
DefinePyFunction(ocVBMManager, ocReport)
{
    PyArg_ParseTuple(args, "");
    PocReport *report = ObjNew(ocReport);
    report->obj = new ocReport(ObjRef(self, ocVBMManager));
    return Py_BuildValue("O", report);
}


// void makeFitTable(ocModel *model)
DefinePyFunction(ocVBMManager, makeFitTable)
{
    PyObject *Pmodel;
    PyArg_ParseTuple(args, "O!", &TocModel, &Pmodel);
    ocModel *model = ObjRef(Pmodel, ocModel);
    if (model == NULL) onError("Model is NULL!");
    ObjRef(self, ocVBMManager)->makeFitTable(model);
    Py_INCREF(Py_None);
    return Py_None;
}

// bool isDirected()
DefinePyFunction(ocVBMManager, isDirected)
{
    PyArg_ParseTuple(args, "");
    bool directed = ObjRef(self, ocVBMManager)->getVariableList()->isDirected();
    return Py_BuildValue("i", directed ? 1 : 0);
}


// void printOptions()
DefinePyFunction(ocVBMManager, printOptions)
{
    int printHTML;
    PyArg_ParseTuple(args, "i", &printHTML);
    ObjRef(self, ocVBMManager)->printOptions(printHTML != 0);
    Py_INCREF(Py_None);
    return Py_None;
}


// void deleteTablesFromCache()
DefinePyFunction(ocVBMManager, deleteTablesFromCache)
{
    ObjRef(self, ocVBMManager)->deleteTablesFromCache();
    Py_INCREF(Py_None);
    return Py_None;
}


// bool deleteModelFromCache(ocModel *model)
DefinePyFunction(ocVBMManager, deleteModelFromCache)
{
    PyObject *Pmodel;
    PyArg_ParseTuple(args, "O!", &TocModel, &Pmodel);
    ocModel *model = ObjRef(Pmodel, ocModel);
    if (model == NULL) onError("Model is NULL!");
    bool success = ObjRef(self, ocVBMManager)->deleteModelFromCache(model);
    return Py_BuildValue("i", success ? 1: 0);
}


//double getSampleSz()
DefinePyFunction(ocVBMManager, getSampleSz)
{
    PyArg_ParseTuple(args, "");
    double ss=ObjRef(self, ocVBMManager)->getSampleSz();
    return Py_BuildValue("d",ss);
}


//long printSizes()
DefinePyFunction(ocVBMManager, printSizes)
{
    PyArg_ParseTuple(args, "");
    ocVBMManager *mgr = ObjRef(self, ocVBMManager);
    mgr->printSizes();
    return Py_None;
}


//long printBasicStatistics()
DefinePyFunction(ocVBMManager, printBasicStatistics)
{
    PyArg_ParseTuple(args, "");
    ocVBMManager *mgr = ObjRef(self, ocVBMManager);
    mgr->printBasicStatistics();
    return Py_None;
}


//long computePercentCorrect(ocModel)
DefinePyFunction(ocVBMManager, computePercentCorrect)
{
    PyObject *Pmodel;
    PyArg_ParseTuple(args, "O!", &TocModel, &Pmodel);
    ocModel *model = ObjRef(Pmodel, ocModel);
    if (model == NULL) onError("Model is NULL!");
    ObjRef(self, ocVBMManager)->computePercentCorrect(model);
    Py_INCREF(Py_None);
    return Py_None;
}


//long getMemUsage()
// This memory usage function doesn't work on Mac OS X, and perhaps other platforms.
DefinePyFunction(ocVBMManager, getMemUsage)
{
    static char *oldBrk = 0;
    PyArg_ParseTuple(args, "");
    if (oldBrk == 0) oldBrk = (char*) sbrk(0);
    double used = ((char*) sbrk(0)) - oldBrk;
    return Py_BuildValue("d",used);
}


//int hasTestData()
DefinePyFunction(ocVBMManager, hasTestData)
{
    PyArg_ParseTuple(args, "");
    ocVBMManager *mgr = ObjRef(self, ocVBMManager);
    int result = (mgr->getTestData() != NULL);
    return Py_BuildValue("i",result);
}

//int dumpRelations
DefinePyFunction(ocVBMManager, dumpRelations)
{
    PyArg_ParseTuple(args, "");
    ocVBMManager *mgr = ObjRef(self, ocVBMManager);
    mgr->dumpRelations();
    return Py_BuildValue("i",0);
}


static struct PyMethodDef ocVBMManager_methods[] = {
    PyMethodDef(ocVBMManager, initFromCommandLine),
    PyMethodDef(ocVBMManager, makeAllChildRelations),
    PyMethodDef(ocVBMManager, makeChildModel),
    PyMethodDef(ocVBMManager, makeModel),
    PyMethodDef(ocVBMManager, setFilter),
    PyMethodDef(ocVBMManager, searchOneLevel),
    PyMethodDef(ocVBMManager, setSearchType),
    PyMethodDef(ocVBMManager, getTopRefModel),
    PyMethodDef(ocVBMManager, getBottomRefModel),
    PyMethodDef(ocVBMManager, getRefModel),
    PyMethodDef(ocVBMManager, setRefModel),
    PyMethodDef(ocVBMManager, computeDF),
    PyMethodDef(ocVBMManager, computeH),
    PyMethodDef(ocVBMManager, computeT),
    PyMethodDef(ocVBMManager, computeInformationStatistics),
    PyMethodDef(ocVBMManager, computeDFStatistics),
    PyMethodDef(ocVBMManager, computeL2Statistics),
    PyMethodDef(ocVBMManager, computePearsonStatistics),
    PyMethodDef(ocVBMManager, computeDependentStatistics),
    PyMethodDef(ocVBMManager, computeBPStatistics),
    PyMethodDef(ocVBMManager, computeIncrementalAlpha),
    PyMethodDef(ocVBMManager, compareProgenitors),
    PyMethodDef(ocVBMManager, setDDFMethod),
    PyMethodDef(ocVBMManager, setUseInverseNotation),
    PyMethodDef(ocVBMManager, setSearchDirection),
    PyMethodDef(ocVBMManager, printFitReport),
    PyMethodDef(ocVBMManager, getOption),
    PyMethodDef(ocVBMManager, getOptionList),
    PyMethodDef(ocVBMManager, ocReport),
    PyMethodDef(ocVBMManager, makeFitTable),
    PyMethodDef(ocVBMManager, isDirected),
    PyMethodDef(ocVBMManager, printOptions),
    PyMethodDef(ocVBMManager, deleteTablesFromCache),
    PyMethodDef(ocVBMManager, deleteModelFromCache),
    PyMethodDef(ocVBMManager, getSampleSz),
    PyMethodDef(ocVBMManager, printBasicStatistics),
    PyMethodDef(ocVBMManager, computePercentCorrect),
    PyMethodDef(ocVBMManager, printSizes),
    PyMethodDef(ocVBMManager, getMemUsage),
    PyMethodDef(ocVBMManager, hasTestData),
    PyMethodDef(ocVBMManager, dumpRelations),
    {NULL, NULL, 0}
};


/****** Basic Type Operations ******/

static void ocVBMManager_dealloc(PocVBMManager *self)
{
    if (self->obj) delete self->obj;
    delete self;
}


PyObject * ocVBMManager_getattr(PyObject *self, char *name)
{
    PyObject *method = Py_FindMethod(ocVBMManager_methods, self, name);
    return method;
}


/****** Type Definition ******/
    PyTypeObject TocVBMManager = {
        PyObject_HEAD_INIT(&PyType_Type)
            0,
        "ocVBMManager",
        sizeof(PocVBMManager),
        0,
        //-- standard methods
        (destructor) ocVBMManager_dealloc,
        (printfunc) 0,
        (getattrfunc) ocVBMManager_getattr,
        (setattrfunc) 0,
        (cmpfunc) 0,
        (reprfunc) 0,

        //-- type categories
        0,
        0,
        0,

        //-- more methods
        (hashfunc) 0,
        (ternaryfunc) 0,
        (reprfunc) 0,
        (getattrofunc) 0,
        (setattrofunc) 0,
    };


DefinePyFunction(ocVBMManager, new)
{
    if (!PyArg_ParseTuple(args, ""))
        return NULL;
    PocVBMManager *newobj = ObjNew(ocVBMManager);
    newobj->obj = new ocVBMManager();
    Py_INCREF(newobj);
    return (PyObject*) newobj;
}


/**************************/
/****** ocSBMManager ******/
/**************************/

/****** Methods ******/

// Constructor
DefinePyFunction(ocSBMManager, initFromCommandLine)
{
    PyObject *Pargv;
    PyArg_ParseTuple(args, "O!", &PyList_Type, &Pargv);
    int argc = PyList_Size(Pargv);
    char **argv = new char*[argc];
    int i;
    for (i = 0; i < argc; i++) {
        PyObject *PString = PyList_GetItem(Pargv, i);
        int size = PyString_Size(PString);
        argv[i] = new char[size+1];
        strcpy(argv[i], PyString_AsString(PString));
    }
    bool ret;
    ret = ObjRef(self, ocSBMManager)->initFromCommandLine(argc, argv);
    for (i = 0; i < argc; i++) delete [] argv[i];
    delete [] argv;
    if (!ret) {
        onError("ocSBMManager: initialization failed");
    }
    Py_INCREF(Py_None);
    return Py_None;
}


// ocModel *getTopRefModel()
DefinePyFunction(ocSBMManager, getTopRefModel)
{
    //TRACE("getTopRefModel\n");
    PocModel *model;
    PyArg_ParseTuple(args, "");
    model = ObjNew(ocModel);
    model->obj = ObjRef(self, ocSBMManager)->getTopRefModel();
    Py_INCREF((PyObject*)model);
    return (PyObject*) model;
}


// ocModel *getBottomRefModel()
DefinePyFunction(ocSBMManager, getBottomRefModel)
{
    //TRACE("getBottomRefModel\n");
    PocModel *model;
    PyArg_ParseTuple(args, "");
    model = ObjNew(ocModel);
    model->obj = ObjRef(self, ocSBMManager)->getBottomRefModel();
    Py_INCREF((PyObject*)model);
    return (PyObject*) model;
}


// ocModel *getRefModel()
DefinePyFunction(ocSBMManager, getRefModel)
{
    //TRACE("getRefModel\n");
    PocModel *model;
    PyArg_ParseTuple(args, "");
    model = ObjNew(ocModel);
    model->obj = ObjRef(self, ocSBMManager)->getRefModel();
    Py_INCREF((PyObject*)model);
    return (PyObject*) model;
}


// ocModel *setRefModel()
DefinePyFunction(ocSBMManager, setRefModel)
{
    char *name;
    PyArg_ParseTuple(args, "s", &name);
    ocModel *ret = ObjRef(self, ocSBMManager)->setRefModel(name);
    if (ret == NULL) onError("invalid model name");
    PocModel *newModel = ObjNew(ocModel);
    newModel->obj = ret;
    return Py_BuildValue("O", newModel);
}


// long computeDF(ocModel *model)
DefinePyFunction(ocSBMManager, compute_SB_DF)
{
    PyObject *Pmodel;
    PyArg_ParseTuple(args, "O!", &TocModel, &Pmodel);
    ocModel *model = ObjRef(Pmodel, ocModel);
    double df = ObjRef(self, ocSBMManager)->compute_SB_DF(model);
    return Py_BuildValue("d", df);
}


// double computeH(ocModel *model)
DefinePyFunction(ocSBMManager, computeH)
{
    PyObject *Pmodel;
    PyArg_ParseTuple(args, "O!", &TocModel, &Pmodel);
    ocModel *model = ObjRef(Pmodel, ocModel);
    if (model == NULL) onError("Model is NULL!");
    double h = ObjRef(self,ocSBMManager)->computeH(model,ocSBMManager::IPF);
    return Py_BuildValue("d", h);
}


// double computeT(ocModel *model)
DefinePyFunction(ocSBMManager, computeT)
{
    PyObject *Pmodel;
    PyArg_ParseTuple(args, "O!", &TocModel, &Pmodel);
    ocModel *model = ObjRef(Pmodel, ocModel);
    if (model == NULL) onError("Model is NULL!");
    double t = ObjRef(self, ocSBMManager)->computeTransmission(model,ocSBMManager::IPF);
    return Py_BuildValue("d", t);
}


// void computeInformationStatistics(ocModel *model)
DefinePyFunction(ocSBMManager, computeInformationStatistics)
{
    PyObject *Pmodel;
    PyArg_ParseTuple(args, "O!", &TocModel, &Pmodel);
    ocModel *model = ObjRef(Pmodel, ocModel);
    if (model == NULL) onError("Model is NULL!");
    ObjRef(self, ocSBMManager)->computeInformationStatistics(model);
    Py_INCREF(Py_None);
    return Py_None;
}


// void computeDFStatistics(ocModel *model)
DefinePyFunction(ocSBMManager, computeDFStatistics)
{
    PyObject *Pmodel;
    PyArg_ParseTuple(args, "O!", &TocModel, &Pmodel);
    ocModel *model = ObjRef(Pmodel, ocModel);
    if (model == NULL) onError("Model is NULL!");
    ObjRef(self, ocSBMManager)->computeDFStatistics(model);
    Py_INCREF(Py_None);
    return Py_None;
}


// void computeL2Statistics(ocModel *model)
DefinePyFunction(ocSBMManager, computeL2Statistics)
{
    PyObject *Pmodel;
    PyArg_ParseTuple(args, "O!", &TocModel, &Pmodel);
    ocModel *model = ObjRef(Pmodel, ocModel);
    if (model == NULL) onError("Model is NULL!");
    ObjRef(self, ocSBMManager)->computeL2Statistics(model);
    Py_INCREF(Py_None);
    return Py_None;
}


// void computePearsonStatistics(ocModel *model)
DefinePyFunction(ocSBMManager, computePearsonStatistics)
{
    PyObject *Pmodel;
    PyArg_ParseTuple(args, "O!", &TocModel, &Pmodel);
    ocModel *model = ObjRef(Pmodel, ocModel);
    if (model == NULL) onError("Model is NULL!");
    ObjRef(self, ocSBMManager)->computePearsonStatistics(model);
    Py_INCREF(Py_None);
    return Py_None;
}


// void computeDependentStatistics(ocModel *model)
DefinePyFunction(ocSBMManager, computeDependentStatistics)
{
    PyObject *Pmodel;
    PyArg_ParseTuple(args, "O!", &TocModel, &Pmodel);
    ocModel *model = ObjRef(Pmodel, ocModel);
    if (model == NULL) onError("Model is NULL!");
    ObjRef(self, ocSBMManager)->computeDependentStatistics(model);
    Py_INCREF(Py_None);
    return Py_None;
}


// void computeBPStatistics(ocModel *model)
DefinePyFunction(ocSBMManager, computeBPStatistics)
{
    PyObject *Pmodel;
    PyArg_ParseTuple(args, "O!", &TocModel, &Pmodel);
    ocModel *model = ObjRef(Pmodel, ocModel);
    if (model == NULL) onError("Model is NULL!");
    ObjRef(self, ocSBMManager)->computeBPStatistics(model);
    Py_INCREF(Py_None);
    return Py_None;
}


// ocModel *makeSBModel(String name, bool makeProject)
DefinePyFunction(ocSBMManager, makeSBModel)
{
    char *name;
    const char *name2;
    //name2=new char[100];
    int makeProject;
    bool bMakeProject;
    PyArg_ParseTuple(args, "si", &name, &makeProject);
    bMakeProject = makeProject != 0;
    ocModel *ret = ObjRef(self, ocSBMManager)->makeSBModel(name, bMakeProject);
    if (ret == NULL){
        onError("invalid model name");
        exit(1);
    }
    name2=ret->getPrintName();
    //printf("model name is %s\n",name2);
    PocModel *newModel = ObjNew(ocModel);
    newModel->obj = ret;
    return Py_BuildValue("O", newModel);
}


// void setFilter(String attrName, String op, double value)
DefinePyFunction(ocSBMManager, setFilter)
{
    char *attrName;
    const char *relOp;
    double attrValue;
    ocSBMManager::RelOp op;
    PyArg_ParseTuple(args, "ssd", &attrName, &relOp, &attrValue);
    if (strcmp(relOp, "<") == 0 || strcasecmp(relOp, "lt") == 0)
        op = ocSBMManager::LESSTHAN;
    else if (strcmp(relOp, "=") == 0 || strcasecmp(relOp, "eq") == 0)
        op = ocSBMManager::EQUALS;
    else if (strcmp(relOp, ">") == 0 || strcasecmp(relOp, "gt") == 0)
        op = ocSBMManager::GREATERTHAN;
    else {
        onError("Invalid comparison operator");
    }
    ObjRef(self, ocSBMManager)->setFilter(attrName, attrValue, op);
    Py_INCREF(Py_None);
    return Py_None;
}


/* commented out because it is currently unused
// void setSort(String attrName, String dir)
DefinePyFunction(ocSBMManager, setSort)
{
char *attrName;
const char *dir;
PyArg_ParseTuple(args, "ss", &attrName, &dir);
ocSBMManager *mgr = ObjRef(self, ocSBMManager);
mgr->setSortAttr(attrName);
if (strcasecmp(dir, "ascending") == 0)
mgr->setSortDirection(ocReport::ASCENDING);
else if (strcasecmp(dir, "descending") == 0)
mgr->setSortDirection(ocReport::DESCENDING);
else {
onError("Invalid sort direction");
}
Py_INCREF(Py_None);
return Py_None;
}
 */


// void printFitReport(ocModel *model)
DefinePyFunction(ocSBMManager, printFitReport)
{
    PyObject *Pmodel;
    PyArg_ParseTuple(args, "O!", &TocModel, &Pmodel);
    ocModel *model = ObjRef(Pmodel, ocModel);
    if (model == NULL) onError("Model is NULL!");
    ObjRef(self, ocSBMManager)->printFitReport(model, stdout);
    Py_INCREF(Py_None);
    return Py_None;
}


// void getOption(const char *name)
DefinePyFunction(ocSBMManager, getOption)
{
    char *attrName;
    PyArg_ParseTuple(args, "s", &attrName);
    const char *value;
    void *nextp = NULL;
    if (!ObjRef(self, ocSBMManager)->getOptionString(attrName, &nextp,&value))
    {
        value = "";
    }
    return Py_BuildValue("s", value);
}


DefinePyFunction(ocSBMManager, getOptionList)
{
    char *attrName;
    PyArg_ParseTuple(args, "s", &attrName);
    const char *value;
    void *nextp = NULL;
    PyObject *list = PyList_New(0);
    while(ObjRef(self, ocSBMManager)->getOptionString(attrName,&nextp, &value) &&
            nextp != NULL)
    {
        PyObject *valstr = Py_BuildValue("s", value);
        PyList_Append(list, valstr);
    }
    Py_INCREF(list);
    return list;
}


// ocModel *ocReport()
DefinePyFunction(ocSBMManager, ocReport)
{
    PyArg_ParseTuple(args, "");
    PocReport *report = ObjNew(ocReport);
    report->obj = new ocReport(ObjRef(self, ocSBMManager));
    return Py_BuildValue("O", report);
}


// void makeFitTable(ocModel *model)
DefinePyFunction(ocSBMManager, makeFitTable)
{
    PyObject *Pmodel;
    PyArg_ParseTuple(args, "O!", &TocModel, &Pmodel);
    ocModel *model = ObjRef(Pmodel, ocModel);
    if (model == NULL) onError("Model is NULL!");
    ObjRef(self, ocSBMManager)->makeFitTable(model);
    Py_INCREF(Py_None);
    return Py_None;
}


// bool isDirected()
DefinePyFunction(ocSBMManager, isDirected)
{
    PyArg_ParseTuple(args, "");
    bool directed = ObjRef(self,ocSBMManager)->getVariableList()->isDirected();
    return Py_BuildValue("i", directed ? 1 : 0);
}


// void printOptions()
DefinePyFunction(ocSBMManager, printOptions)
{
    int printHTML;
    PyArg_ParseTuple(args, "i", &printHTML);
    ObjRef(self, ocSBMManager)->printOptions(printHTML != 0);
    Py_INCREF(Py_None);
    return Py_None;
}


// void deleteTablesFromCache()
DefinePyFunction(ocSBMManager, deleteTablesFromCache)
{
    ObjRef(self, ocSBMManager)->deleteTablesFromCache();
    Py_INCREF(Py_None);
    return Py_None;
}


//double getSampleSz()
DefinePyFunction(ocSBMManager, getSampleSz)
{
    PyArg_ParseTuple(args, "");
    double ss=ObjRef(self, ocSBMManager)->getSampleSz();
    return Py_BuildValue("d",ss);
}

//long printBasicStatistics()
DefinePyFunction(ocSBMManager, printBasicStatistics)
{
    PyArg_ParseTuple(args, "");
    ocSBMManager *mgr = ObjRef(self, ocSBMManager);
    mgr->printBasicStatistics();
    return Py_None;
}



static struct PyMethodDef ocSBMManager_methods[] = {
    PyMethodDef(ocSBMManager, initFromCommandLine),
    PyMethodDef(ocSBMManager, makeSBModel),
    PyMethodDef(ocSBMManager, setFilter),
    PyMethodDef(ocSBMManager, getTopRefModel),
    PyMethodDef(ocSBMManager, getBottomRefModel),
    PyMethodDef(ocSBMManager, getRefModel),
    PyMethodDef(ocSBMManager, setRefModel),
    PyMethodDef(ocSBMManager, compute_SB_DF),
    PyMethodDef(ocSBMManager, computeH),
    PyMethodDef(ocSBMManager, computeT),
    PyMethodDef(ocSBMManager, computeInformationStatistics),
    PyMethodDef(ocSBMManager, computeDFStatistics),
    PyMethodDef(ocSBMManager, computeL2Statistics),
    PyMethodDef(ocSBMManager, computePearsonStatistics),
    PyMethodDef(ocSBMManager, computeDependentStatistics),
    PyMethodDef(ocSBMManager, computeBPStatistics),
    PyMethodDef(ocSBMManager, printFitReport),
    PyMethodDef(ocSBMManager, getOption),
    PyMethodDef(ocSBMManager, getOptionList),
    PyMethodDef(ocSBMManager, ocReport),
    PyMethodDef(ocSBMManager, makeFitTable),
    PyMethodDef(ocSBMManager, isDirected),
    PyMethodDef(ocSBMManager, printOptions),
    PyMethodDef(ocSBMManager, deleteTablesFromCache),
    PyMethodDef(ocSBMManager, getSampleSz),
    PyMethodDef(ocSBMManager, printBasicStatistics),
    {NULL, NULL, 0}
};


/****** Basic Type Operations ******/
static void ocSBMManager_dealloc(PocSBMManager *self)
{
    if (self->obj) delete self->obj;
    delete self;
}


PyObject * ocSBMManager_getattr(PyObject *self, char *name)
{
    PyObject *method = Py_FindMethod(ocSBMManager_methods, self,name);
    return method;
}


/****** Type Definition ******/
    PyTypeObject TocSBMManager = {
        PyObject_HEAD_INIT(&PyType_Type)
            0,
        "ocSBMManager",
        sizeof(PocSBMManager),
        0,
        //-- standard methods
        (destructor) ocSBMManager_dealloc,
        (printfunc) 0,
        (getattrfunc) ocSBMManager_getattr,
        (setattrfunc) 0,
        (cmpfunc) 0,
        (reprfunc) 0,

        //-- type categories
        0,
        0,
        0,

        //-- more methods
        (hashfunc) 0,
        (ternaryfunc) 0,
        (reprfunc) 0,
        (getattrofunc) 0,
        (setattrofunc) 0,
    };


DefinePyFunction(ocSBMManager, new)
{
    if (!PyArg_ParseTuple(args, ""))
        return NULL;
    PocSBMManager *newobj = ObjNew(ocSBMManager);
    newobj->obj = new ocSBMManager();
    Py_INCREF(newobj);
    return (PyObject*) newobj;
}


/************************/
/****** ocRelation ******/
/************************/

// Object* get(char *name)
DefinePyFunction(ocRelation, get)
{
    ocRelation *relation = ObjRef(self, ocRelation);
    char *name;
    PyArg_ParseTuple(args, "s", &name);
    //-- Other attributes
    if (strcmp(name, "name") == 0) {
        const char *printName = relation->getPrintName();
        return PyString_FromString(printName);
    }

    if (strcmp(name, "varcount") == 0) {
        long varcount = relation->getVariableCount();
        return PyInt_FromLong(varcount);
    }

    int attindex = relation->getAttributeList()->getAttributeIndex(name);
    double value;
    if (attindex < 0) value = -1;
    else value = relation->getAttributeList()->getAttributeByIndex(attindex);
    return PyFloat_FromDouble(value);
}


static struct PyMethodDef ocRelation_methods[] = {
    PyMethodDef(ocRelation, get),
    {NULL, NULL, 0}
};


/****** Basic Type Operations ******/

/* commented out because it is currently unused
   static PocRelation *
   newPocRelation()
   {
   PocRelation *self = new PocRelation();
   self->obj = new ocRelation();
   return self;
   }
 */

/* commented out because it is currently unused
   static void
   ocRelation_dealloc(PocRelation *self)
   {
//-- this doesn't delete the ocRelation, because these
//-- are generally borrowed from the cache
delete self;
}
 */

    PyObject *
ocRelation_getattr(PyObject *self, char *name)
{
    PyObject *method = Py_FindMethod(ocRelation_methods, self, name);
    if (method) return method;

    ocRelation *rel = ObjRef(self, ocRelation);

    //-- Other attributes
    if (strcmp(name, "name") == 0) {
        const char *printName = rel->getPrintName();
        return Py_BuildValue("s", printName);
    }

    if (strcmp(name, "varcount") == 0) {
        long varcount = rel->getVariableCount();
        return Py_BuildValue("l", varcount);
    }

    int attindex = rel->getAttributeList()->getAttributeIndex(name);
    double value;
    if (attindex < 0) value = -1;
    else value = rel->getAttributeList()->getAttributeByIndex(attindex);
    return Py_BuildValue("d", value);
}


/****** Type Definition ******/
    PyTypeObject TocRelation = {
        PyObject_HEAD_INIT(&PyType_Type)
            0,
        "ocRelation",
        sizeof(PocRelation),
        0,
        //-- standard methods
        (destructor) 0,
        (printfunc) 0,
        (getattrfunc) ocRelation_getattr,
        (setattrfunc) 0,
        (cmpfunc) 0,
        (reprfunc) 0,

        //-- type categories
        0,
        0,
        0,

        //-- more methods
        (hashfunc) 0,
        (ternaryfunc) 0,
        (reprfunc) 0,
        (getattrofunc) 0,
        (setattrofunc) 0,
    };


DefinePyFunction(ocRelation, new)
{
    if (!PyArg_ParseTuple(args, ""))
        return NULL;
    PocRelation *newobj = ObjNew(ocRelation);
    newobj->obj = new ocRelation();
    Py_INCREF(newobj);
    return (PyObject*) newobj;
}


/************************/
/****** ocModel ******/
/************************/

// ocRelation* getRelation(int index)
DefinePyFunction(ocModel, getRelation)
{
    int index;
    PyArg_ParseTuple(args, "i", &index);
    ocModel *model = ObjRef(self, ocModel);
    PocRelation *newRelation = ObjNew(ocRelation);
    newRelation->obj = model->getRelation(index);
    return Py_BuildValue("O", newRelation);
}


// Object* get(char *name)
DefinePyFunction(ocModel, get)
{
    ocModel *model = ObjRef(self, ocModel);
    char *name;
    PyArg_ParseTuple(args, "s", &name);
    //-- Other attributes
    if (strcmp(name, "name") == 0) {
        const char *printName = model->getPrintName();
        return PyString_FromString(printName);
    }

    if (strcmp(name, "relcount") == 0) {
        long relcount = model->getRelationCount();
        return PyInt_FromLong(relcount);
    }

    int attindex = model->getAttributeList()->getAttributeIndex(name);
    double value;
    if (attindex < 0) value = -1;
    else value = model->getAttributeList()->getAttributeByIndex(attindex);
    return PyFloat_FromDouble(value);
}


// void deleteFitTable()
DefinePyFunction(ocModel, deleteFitTable)
{
    ocModel *model = ObjRef(self, ocModel);
    model->deleteFitTable();
    Py_INCREF(Py_None);
    return Py_None;
}


// void deleteRelationLinks()
DefinePyFunction(ocModel, deleteRelationLinks)
{
    ocModel *model = ObjRef(self, ocModel);
    model->deleteRelationLinks();
    Py_INCREF(Py_None);
    return Py_None;
}


// void setProgenitor(ocModel* )
DefinePyFunction(ocModel, setProgenitor)
{
    PyObject *Pmodel;
    PyArg_ParseTuple(args, "O!", &TocModel, &Pmodel);
    ocModel *progen = ObjRef(Pmodel, ocModel);
    ocModel *model = ObjRef(self, ocModel);
    model->setProgenitor(progen);
    Py_INCREF(Py_None);
    return Py_None;
}


// ocModel *getProgenitor()
DefinePyFunction(ocModel, getProgenitor)
{
    PocModel *model;
    PyArg_ParseTuple(args, "");
    model = ObjNew(ocModel);
    model->obj = ObjRef(self, ocModel)->getProgenitor();
    Py_INCREF((PyObject*)model);
    return (PyObject*) model;
}


// void setID()
DefinePyFunction(ocModel, setID)
{
    int ID;
    PyArg_ParseTuple(args, "i", &ID);
    ocModel *model = ObjRef(self, ocModel);
    model->setID(ID);
    Py_INCREF(Py_None);
    return Py_None;
}


// void dump()
DefinePyFunction(ocModel, dump)
{
    ocModel *model = ObjRef(self, ocModel);
    model->dump();
    Py_INCREF(Py_None);
    return Py_None;
}


static struct PyMethodDef ocModel_methods[] = {
    PyMethodDef(ocModel, getRelation),
    PyMethodDef(ocModel, get),
    PyMethodDef(ocModel, deleteFitTable),
    PyMethodDef(ocModel, deleteRelationLinks),
    PyMethodDef(ocModel, setProgenitor),
    PyMethodDef(ocModel, getProgenitor),
    PyMethodDef(ocModel, setID),
    PyMethodDef(ocModel, dump),
    {NULL, NULL, 0}
};


/****** Basic Type Operations ******/

/* commented out because it is currently unused
   static PocModel *
   newPocModel()
   {
   PocModel *self = new PocModel();
   self->obj = new ocModel();
   return self;
   }
 */

/* commented out because it is currently unused
   static void
   ocModel_dealloc(PocModel *self)
   {
//-- models are cached also
delete self;
}
 */

PyObject * ocModel_getattr(PyObject *self, char *name)
{
    PyObject *method = Py_FindMethod(ocModel_methods, self, name);
    if (method) return method;

    ocModel *model = ObjRef(self, ocModel);
    //-- Other attributes
    if (strcmp(name, "name") == 0) {
        const char *printName = model->getPrintName();
        return PyString_FromString(printName);
    }

    if (strcmp(name, "relcount") == 0) {
        long relcount = model->getRelationCount();
        return PyInt_FromLong(relcount);
    }

    int attindex = model->getAttributeList()->getAttributeIndex(name);
    double value;
    if (attindex < 0) value = -1;
    else value = model->getAttributeList()->getAttributeByIndex(attindex);
    return PyFloat_FromDouble(value);
}


int ocModel_setattr(PyObject *self, char *name, PyObject *value)
{
    double dvalue;
    if (PyFloat_Check(value))
        dvalue = PyFloat_AsDouble(value);
    else if (PyLong_Check(value))
        dvalue = PyLong_AsDouble(value);
    else if (PyInt_Check(value))
        dvalue = (double) PyInt_AsLong(value);
    else dvalue = -1;
    ObjRef(self, ocModel)->setAttribute(name, dvalue);
    return 0;
}

/****** Type Definition ******/

    PyTypeObject TocModel = {
        PyObject_HEAD_INIT(&PyType_Type)
            0,
        "ocModel",
        sizeof(PocModel),
        0,
        //-- standard methods
        (destructor) 0,
        (printfunc) 0,
        (getattrfunc) ocModel_getattr,
        (setattrfunc) ocModel_setattr,
        (cmpfunc) 0,
        (reprfunc) 0,

        //-- type categories
        0,
        0,
        0,

        //-- more methods
        (hashfunc) 0,
        (ternaryfunc) 0,
        (reprfunc) 0,
        (getattrofunc) 0,
        (setattrofunc) 0,
    };


DefinePyFunction(ocModel, new)
{
    if (!PyArg_ParseTuple(args, ""))
        return NULL;
    PocModel *newobj = ObjNew(ocModel);
    newobj->obj = new ocModel();
    Py_INCREF(newobj);
    return (PyObject*) newobj;
}


/************************/
/****** ocReport ******/
/************************/

// Object* get(char *name)
DefinePyFunction(ocReport, get)
{
    ocReport *report = ObjRef(self, ocReport);
    TRACE_FN("ocReport::get", __LINE__, report);
    char *name;
    PyArg_ParseTuple(args, "s", &name);
    //-- none defined
    TRACE_FN("ocReport::get", __LINE__, 0);
    return NULL;
}


// void addModel(ocModel *model)
DefinePyFunction(ocReport, addModel)
{
    ocReport *report = ObjRef(self, ocReport);
    TRACE_FN("ocReport::addModel", __LINE__, report);
    PocModel *pmodel;
    ocModel *model;
    PyArg_ParseTuple(args, "O", &pmodel);
    model = pmodel->obj;
    report->addModel(model);
    Py_INCREF(Py_None);
    TRACE_FN("ocReport::addModel", __LINE__, 0);
    return Py_None;
}


// void setDefaultFitModel(ocModel *model)
DefinePyFunction(ocReport, setDefaultFitModel)
{
    ocReport *report = ObjRef(self, ocReport);
    TRACE_FN("ocReport::setDefaultFitModel", __LINE__, report);
    PocModel *pmodel;
    ocModel *model;
    PyArg_ParseTuple(args, "O", &pmodel);
    model = pmodel->obj;
    report->setDefaultFitModel(model);
    Py_INCREF(Py_None);
    TRACE_FN("ocReport::setDefaultFitModel", __LINE__, 0);
    return Py_None;
}


// void setAttributes(char *attrList)
DefinePyFunction(ocReport, setAttributes)
{
    ocReport *report = ObjRef(self, ocReport);
    TRACE_FN("ocReport::setAttributes", __LINE__, report);
    char *attrList;
    PyArg_ParseTuple(args, "s", &attrList);
    report->setAttributes(attrList);
    Py_INCREF(Py_None);
    TRACE_FN("ocReport::setAttributes", __LINE__, 0);
    return Py_None;
}


// void sort(char *attr, char *direction) "ascending" or "descending"
DefinePyFunction(ocReport, sort)
{
    ocReport *report = ObjRef(self, ocReport);
    TRACE_FN("ocReport::sort", __LINE__, report);
    char *attr;
    char *direction;
    PyArg_ParseTuple(args, "ss", &attr, &direction);
    if (strcasecmp(direction, "ascending") == 0) {
        report->sort(attr, ocReport::ASCENDING);
    }
    else if (strcasecmp(direction, "descending") == 0) {
        report->sort(attr, ocReport::DESCENDING);
    }
    else {
        onError("Invalid sort direction");
    }
    Py_INCREF(Py_None);
    TRACE_FN("ocReport::sort", __LINE__, 0);
    return Py_None;
}


// void setSeparator(int sep) 1=tab, 2=comma, 3=space filled, 4=HTML
DefinePyFunction(ocReport, setSeparator)
{
    ocReport *report = ObjRef(self, ocReport);
    TRACE_FN("ocReport::setSeparator", __LINE__, report);
    int sep;
    PyArg_ParseTuple(args, "i", &sep);
    report->setSeparator(sep < 4 ? sep : 1);
    report->setHTMLMode(sep == 4);
    Py_INCREF(Py_None);
    TRACE_FN("ocReport::setSeparator", __LINE__,0);
    return Py_None;
}


// void printReport()
DefinePyFunction(ocReport, printReport)
{
    ocReport *report = ObjRef(self, ocReport);
    TRACE_FN("ocReport::printReport", __LINE__, report);
    PyArg_ParseTuple(args, "");
    report->print(stdout);
    Py_INCREF(Py_None);
    TRACE_FN("ocReport::printReport", __LINE__,0);
    return Py_None;
}


// void writeReport(const char *name)
DefinePyFunction(ocReport, writeReport)
{
    ocReport *report = ObjRef(self, ocReport);
    const char *file;
    TRACE_FN("ocReport::printReport", __LINE__, report);
    PyArg_ParseTuple(args, "s", &file);
    FILE *fd = fopen(file, "w");
    if (fd == NULL) onError("cannot open file");
    report->print(fd);
    fclose(fd);
    Py_INCREF(Py_None);
    TRACE_FN("ocReport::printReport", __LINE__,0);
    return Py_None;
}


// void printResiduals(ocModel *model)
DefinePyFunction(ocReport, printResiduals)
{
    PyObject *Pmodel;
    PyArg_ParseTuple(args, "O!", &TocModel, &Pmodel);
    ocModel *model = ObjRef(Pmodel, ocModel);
    ObjRef(self, ocReport)->printResiduals(stdout, model);
    Py_INCREF(Py_None);
    return Py_None;
}


// void printConditional_DV(ocModel *model)
DefinePyFunction(ocReport, printConditional_DV)
{
    PyObject *Pmodel;
    int calcExpectedDV;
    bool bCalcExpectedDV = false;
    PyArg_ParseTuple(args, "O!i", &TocModel, &Pmodel, &calcExpectedDV);
    if (calcExpectedDV != 0) bCalcExpectedDV = true;
    ocModel *model = ObjRef(Pmodel, ocModel);
    ObjRef(self, ocReport)->printConditional_DV(stdout, model, bCalcExpectedDV);
    Py_INCREF(Py_None);
    return Py_None;
}


static struct PyMethodDef ocReport_methods[] = {
    PyMethodDef(ocReport, get),
    PyMethodDef(ocReport, addModel),
    PyMethodDef(ocReport, setDefaultFitModel),
    PyMethodDef(ocReport, setAttributes),
    PyMethodDef(ocReport, sort),
    PyMethodDef(ocReport, printReport),
    PyMethodDef(ocReport, writeReport),
    PyMethodDef(ocReport, setSeparator),
    PyMethodDef(ocReport, printResiduals),
    PyMethodDef(ocReport, printConditional_DV),
    {NULL, NULL, 0}
};


/****** Basic Type Operations ******/

/* commented out because it is currently unused
   static void
   ocReport_dealloc(PocReport *self)
   {
   ocReport *report = ObjRef(self, ocReport);
   TRACE_FN("ocReport::dealloc", __LINE__, report);
   delete report;
   delete self;
   TRACE_FN("ocReport::dealloc", __LINE__, 0);
   }
 */


PyObject * ocReport_getattr(PyObject *self, char *name)
{
    //	TRACE_FN("ocReport::getattr", __LINE__);
    PyObject *method = Py_FindMethod(ocReport_methods, self, name);
    if (method) return method;

    //ocReport *report = ObjRef(self, ocReport);
    //-- none defined
    //	TRACE_FN("ocReport::getattr", __LINE__);
    return NULL;
}


/****** Type Definition ******/
    PyTypeObject TocReport = {
        PyObject_HEAD_INIT(&PyType_Type)
            0,
        "ocReport",
        sizeof(PocReport),
        0,
        //-- standard methods
        (destructor) 0,
        (printfunc) 0,
        (getattrfunc) ocReport_getattr,
        (setattrfunc) 0,
        (cmpfunc) 0,
        (reprfunc) 0,

        //-- type categories
        0,
        0,
        0,

        //-- more methods
        (hashfunc) 0,
        (ternaryfunc) 0,
        (reprfunc) 0,
        (getattrofunc) 0,
        (setattrofunc) 0,
    };


/**************************/
/****** MODULE LOGIC ******/
/**************************/

static PyObject *setHTMLMode(PyObject *self, PyObject *args)
{
    int mode;
    if (!PyArg_ParseTuple(args, "i", &mode))
        return NULL;
    ocReport::setHTMLMode(mode != 0);
    Py_INCREF(Py_None);
    return Py_None;
}


static struct PyMethodDef occam_methods[] = {
    {"ocRelation", ocRelation_new, 1},
    {"ocModel", ocModel_new, 1},
    {"ocVBMManager", ocVBMManager_new, 1},
    {"ocSBMManager", ocSBMManager_new, 1},
    {"setHTMLMode", setHTMLMode, 1},
    {NULL, NULL}
};


extern "C" {
    SWIGEXPORT(void) initoccam();
};


void initoccam()
{
    PyObject *m, *d;
    m = Py_InitModule("occam", occam_methods);
    d = PyModule_GetDict(m);
    ErrorObject = Py_BuildValue("s", "occam.error");
    PyDict_SetItemString(d, "error", ErrorObject);
    if (PyErr_Occurred())
        Py_FatalError("cannot initialize module occam");
}

