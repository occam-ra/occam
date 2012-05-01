/* Copyright 2000, Portland State University Systems Science Program.  All Rights Reserved
 */
#ifndef OCVBM_MANAGER_H
#define OCVBM_MANAGER_H

#include "ocCore.h"
#include "ocManagerBase.h"

/**
 * ocManagerBase - implements base functionality of an ocManager.  This class is the
 * provider for algorithms which manipulate core objects.  The class is extensible,
 * to allow new managers to be developed for different analysis approaches.
 *
 * The base manager has default implementions for commonly required operations, such as:
 * - generation of descendent models from an existing model
 * - creation of a table for a model, by projection from an input table
 * - creation of a fit table for a model using IPF
 * - calculation of various parameters for a table or model
 * - determination if a model contains loops
 */
class ocVBMManager: public ocManagerBase {
public:
    //-- create an ocManagerBase object, supplying it with a variable list and a table
    //-- of input data.  Typically an application will read the input data and variable
    //-- definitions, and then construct the appropriate manager.
    ocVBMManager(ocVariableList *vars, ocTable *input);
    ocVBMManager();

    // initialize an ocManagerBase object, reading in standard options and data files.
    bool initFromCommandLine(int argc, char **argv);

    //-- delete this object
    virtual ~ocVBMManager();

    //-- return all the child relations of the given relation.  The children array
    //-- must have been preallocated, of size at least the number of variables in
    //-- the relation (this is the number of children). Projections are created, if
    //-- indicated
    void makeAllChildRelations(ocRelation *rel, ocRelation **children, bool makeProject = false);

    //-- make a child model of a given model, by removing a relation and then adding back
    //-- in all its children
    ocModel *makeChildModel(ocModel *model, int remove, bool* fromCache = 0, bool makeProject =
            false);

    //-- make the top and bottom reference models, given a relation which represents
    //-- the saturated model. This function also sets the default reference model based
    //-- on whether the system is directed or undirected.
    void makeReferenceModels(ocRelation *top);

    //-- return top, bottom, or default reference
    ocModel *getTopRefModel() {
        return topRef;
    }
    ocModel *getBottomRefModel() {
        return bottomRef;
    }
    ocModel *getRefModel() {
        return refModel;
    }

    //-- set ref model
    ocModel *setRefModel(const char *name);

    //-- compute various measures. These generally involve the top and/or bottom
    //-- reference models, so makeReferenceModels must be called before any of
    //-- these are used.
    double computeExplainedInformation(ocModel *model);
    double computeUnexplainedInformation(ocModel *model);
    double computeDDF(ocModel *model);
    void setDDFMethod(int method);

    void setUseInverseNotation(int flag);
    int getUseInverseNotation() {
        return useInverseNotation;
    }

    //-- flag to indicate whether to make projections on all relations
    void setMakeProjection(bool proj) {
        projection = proj;
    }
    bool makeProjection() {
        return projection;
    }

    //-- get/set search object
    class ocSearchBase *getSearch() {
        return search;
    }
    void setSearch(const char *name);

    //-- compute basic informational statistics
    void computeInformationStatistics(ocModel *model);

    //-- compute DF and related statistics
    void computeDFStatistics(ocModel *model);

    //-- compute log likelihood statistics
    void computeL2Statistics(ocModel *model);

    //-- compute Pearson statistics
    void computePearsonStatistics(ocModel *model);

    //-- compute dependent variable statistics
    void computeDependentStatistics(ocModel *model);

    //-- compute BP-based transmission
    //void doBPIntersection(ocModel *model);
    double computeBPT(ocModel *model);

    //-- compute all statistics based on BP_T
    void computeBPStatistics(ocModel *model);

    //-- compute percentage correct of a model for adirected system
    void computePercentCorrect(ocModel *model);

    //-- Filter definitions. If a filter is set on a search object, then
    //-- generated models which do not pass the filter are not kept.
    enum RelOp {
        LESSTHAN, EQUALS, GREATERTHAN
    };
    void setFilter(const char *attrname, double attrvalue, RelOp op);
    virtual bool applyFilter(ocModel *model);

    //-- Sort definitions
    void setSortAttr(const char *name);
    const char *getSortAttr() {
        return sortAttr;
    }
    void setSortDirection(int dir) {
        sortDirection = dir;
    }
    int getSortDirection() {
        return sortDirection;
    }

    //-- Single model reports. For multi-model reports see ocReport.h
    void printFitReport(ocModel *model, FILE *fd);

    void printBasicStatistics();

    //-- Get predicting variables, for a model of adependent system.
    //-- The predicting variables are those in any relation other than
    //-- the IV relation. Optionally the dependent variables can be included in this.
    //-- the varindices arg is filled with the variable indices;
    //-- it needs to have been allocated large enough.

    void calculateBP_AicBic(ocModel *model);

private:
    // data
    bool projection;
    class ocSearchBase *search;
    char *filterAttr;
    double filterValue;
    char *sortAttr;
    int sortDirection;
    RelOp filterOp;
    int useInverseNotation;

    bool firstCome;
    bool firstComeBP;
    double refer_AIC;
    double refer_BIC;
    double refer_BP_AIC;
    double refer_BP_BIC;

    // Called by computeDDF to build a list of the relations that differ between two models.
    void buildDDF(ocRelation *rel, ocModel *loModel, ocModel *diffModel, bool directed);
    int DDFMethod; // method to use for computing DDF. 0=new (default); 1=old
};

#endif

