/* Copyright 2000, Portland State University Systems Science Program.  All Rights Reserved
 */
#ifndef OCSBM_MANAGER_H
#define OCSBM_MANAGER_H

#include "ocCore.h"
#include "ocManagerBase.h"

/**
 * ocManagerBase - implements base functionality of an ocManager.  This class is the
 * provider for algorithms which manipulate core objects.  The class is extensible,
 * to allow new managers to be developed for different analysis approaches.
 *
 * The base manager has default implementations for commonly required operations, such as:
 * - generation of descendant models from an existing model
 * - creation of a table for a model, by projection from an input table
 * - creation of a fit table for a model using IPF
 * - calculation of various parameters for a table or model
 * - determination if a model contains loops
 */
class ocSBMManager: public ocManagerBase {
    public:
        //-- create an ocManagerBase object, supplying it with a variable list and a table
        //-- of input data.  Typically an application will read the input data and variable
        //-- definitions, and then construct the appropriate manager.
        ocSBMManager(ocVariableList *vars, ocTable *input);
        ocSBMManager();

        // initialize an ocManagerBase object, reading in standard options and data files.
        bool initFromCommandLine(int argc, char **argv);

        //-- delete this object
        virtual ~ocSBMManager();

        //-- make the top and bottom reference models, given a relation which represents
        //-- the saturated model. This function also sets the default reference model based
        //-- on whether the system is directed or undirected.
        void makeReferenceModels(ocRelation *top);

        void verifyStateBasedNaming();

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
        // This is only a place-holder at this point.
        int getSearchDirection() {
            return 0;
        }

        //-- set ref model
        ocModel *setRefModel(const char *name);

        //-- compute various measures. These generally involve the top and/or bottom
        //-- reference models, so makeReferenceModels must be called before any of
        //-- these are used.
        double computeExplainedInformation(ocModel *model);
        double computeUnexplainedInformation(ocModel *model);
        double computeDDF(ocModel *model);

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
        void computeBPStatistics(ocModel *model);

        //-- compute percentage correct of a model for a directed system
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

    private:
        // data
        bool projection;
        class ocSearchBase *search;
        char *filterAttr;
        double filterValue;
        char *sortAttr;
        int sortDirection;
        RelOp filterOp;

};

#endif

