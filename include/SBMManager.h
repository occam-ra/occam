#ifndef OCSBM_MANAGER_H
#define OCSBM_MANAGER_H

#include "Core.h"
#include "ManagerBase.h"

/**
 * ManagerBase - implements base functionality of an ocManager.  This class is the
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
class SBMManager: public ManagerBase {
    public:
        //-- create an ManagerBase object, supplying it with a variable list and a table
        //-- of input data.  Typically an application will read the input data and variable
        //-- definitions, and then construct the appropriate manager.
        SBMManager(VariableList *vars, Table *input);
        SBMManager();

        // initialize an ManagerBase object, reading in standard options and data files.
        bool initFromCommandLine(int argc, char **argv);

        //-- delete this object
        virtual ~SBMManager();

        //-- make the top and bottom reference models, given a relation which represents
        //-- the saturated model. This function also sets the default reference model based
        //-- on whether the system is directed or undirected.
        void makeReferenceModels(Relation *top);

        void verifyStateBasedNaming();

        //-- return top, bottom, or default reference
        Model *getTopRefModel() {
            return topRef;
        }
        Model *getBottomRefModel() {
            return bottomRef;
        }
        Model *getRefModel() {
            return refModel;
        }
        // This is only a place-holder at this point.
        int getSearchDirection() {
            return 0;
        }

        //-- set ref model
        Model *setRefModel(const char *name);

        //-- compute various measures. These generally involve the top and/or bottom
        //-- reference models, so makeReferenceModels must be called before any of
        //-- these are used.
        double computeExplainedInformation(Model *model);
        double computeUnexplainedInformation(Model *model);
        double computeDDF(Model *model);

        //-- flag to indicate whether to make projections on all relations
        void setMakeProjection(bool proj) {
            projection = proj;
        }
        bool makeProjection() {
            return projection;
        }

        //-- get/set search object
        class SearchBase *getSearch() {
            return search;
        }
        void setSearch(const char *name);

        //-- compute basic informational statistics
        void computeInformationStatistics(Model *model);

        //-- compute DF and related statistics
        void computeDFStatistics(Model *model);

        //-- compute log likelihood statistics
        void computeL2Statistics(Model *model);

        //-- compute Pearson statistics
        void computePearsonStatistics(Model *model);

        //-- compute dependent variable statistics
        void computeDependentStatistics(Model *model);

        //-- compute BP-based transmission
        void computeBPStatistics(Model *model);

        //-- compute percentage correct of a model for a directed system
        void computePercentCorrect(Model *model);

        //-- Filter definitions. If a filter is set on a search object, then
        //-- generated models which do not pass the filter are not kept.
        enum RelOp {
            LESSTHAN, EQUALS, GREATERTHAN
        };
        void setFilter(const char *attrname, double attrvalue, RelOp op);
        virtual bool applyFilter(Model *model);

        //-- Sort definitions
        void setSortAttr(const char *name);
        const char *getSortAttr() {
            return sortAttr;
        }
        void setDirectionection(int dir) {
            sortDirection = dir;
        }
        int getDirectionection() {
            return sortDirection;
        }

        //-- Single model reports. For multi-model reports see Report.h
        void printFitReport(Model *model, FILE *fd);

        void printBasicStatistics();

    private:
        // data
        bool projection;
        class SearchBase *search;
        char *filterAttr;
        double filterValue;
        char *sortAttr;
        int sortDirection;
        RelOp filterOp;

};

#endif

