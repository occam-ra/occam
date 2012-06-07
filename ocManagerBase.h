/* Copyright 2000, Portland State University Systems Science Program.  All Rights Reserved
 */
#ifndef OCMANAGER_BASE_H
#define OCMANAGER_BASE_H

#include "ocOptions.h"

/**
 * ocIntersectProcessor - this is a base class for processing classes
 * used by ocManagerBase::doIntersectProcessing. This function does the
 * alternating relation intersect traversal for a model, used for computing
 * DF, H, and other functions.
 * To use this class, create an appropriate subclass, initialize it
 * properly, and pass it to doIntersectProcessing. Your process() function
 * will be called with all the relations of the model, then their first
 * order intersections, etc. For example, for model ABC:BCD:DEF, it will
 * be called with these relations/signs: ABC+, BCD+, DEF+, BC-, D-, NULL-
 * (the Null occurs because there is no intersection between ABC and DEF)
 */

class ocIntersectProcessor {
    public:
        ocIntersectProcessor() {
        }
        virtual ~ocIntersectProcessor() {
        }
        //-- this function is called for each relation. sign is true (+1) for
        //-- the first, third, etc. levels, and false (-1) for second, fourth, etc.
        virtual void process(bool sign, ocRelation *rel, int count = 1) = 0;
};

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

class ocManagerBase {
    public:
        // method to use for computing H. Auto means use IPF if there are loops and
        // algebraic method otherwise.
        enum HMethod {
            AUTO, IPF, ALGEBRAIC
        };

        // create an ocManagerBase object, supplying it with a variable list and a table
        // of input data.  Typically an application will read the input data and variable
        // definitions, and then construct the appropriate manager.
        ocManagerBase(ocVariableList *vars = 0, ocTable *input = 0);

        // initialize an ocManagerBase object, reading in standard options and data files.
        bool initFromCommandLine(int argc, char **argv);

        // delete this object
        virtual ~ocManagerBase();

        // get the relation defined by the list of variable indices and the count.
        // this will first search the cache and, if the relation is found, return it.
        // if not in the cache, a new relation is created. If instructed, the projection
        // corresponding to the relation is also created.
        virtual ocRelation *getRelation(int *varindices, int varcount, bool makeProject = false, int *stateindices = NULL);

        // get a relation just like the given relation, but with the given variable removed.
        // (skip is the variable id in the master variable list).
        virtual ocRelation *getChildRelation(ocRelation *rel, int skip, bool makeProject = false,
                int *stateindices = 0);

        // make a projection.  This creates an ocTable, and installs it as the table for the
        // given relation.  The projection is determined from the given table, and the
        // VariableList is the one associated with the given relation. False is returned on
        // any error. This function returns true immediately if the relation already has a table.
        virtual bool makeProjection(ocRelation *rel);

        // make a projection of table t1 into t2 (empty), based on the variable
        // list contained in the given relation. This is used as one step of the IPF algorithm.
        virtual bool makeProjection(ocTable *t1, ocTable *t2, ocRelation *rel);

        // make a "maxProjection" of one table into another. This creates a partial
        // probability distribution by keeping only the max values for each matching tuple.
        // rel provides the set of variables to be used in the match (generally the IV set).
        virtual bool makeMaxProjection(ocTable *t1, ocTable *t2, ocTable *inputData, ocRelation *indRel,
                ocRelation *depRel, double* missedValues);

        // make projections for all relations in a model. This just calls makeProject
        // as many times as needed.
        virtual bool makeProjections(ocModel *model);

        // delete projection tables from all relations in cache
        virtual void deleteTablesFromCache();

        // delete a model from the model cache
        virtual bool deleteModelFromCache(ocModel *model);

        // Create an array of relation intersections for an algebraic fit table.
        virtual void doFitIntersection(ocModel *model);

        // Make a fit table. This function uses the IPF algorithm. The fit table is
        // linked to the model.  If the model already has a fit table, the function
        // returns immediately. False is returned on any error.
        virtual bool makeFitTable(ocModel *model);

        // Expand a single tuple into all values of all missing variables, recursively
        void expandTuple(double tupleValue, ocKeySegment *key, int *missingVars, int missingCount, ocTable *outTable,
                int currentMissingVar);

        void makeOrthoExpansion(ocRelation *rel, ocTable *table);
        void makeSbExpansion(ocRelation *rel, ocTable *table);

        // Process relations and intersections, as need for DF and H computation
        void doIntersectionProcessing(ocModel *model, ocIntersectProcessor *proc);

        // Compute degrees of freedom of a model.  This involves computing degrees
        // of freedom of the constituent relations, minus the first order overlaps,
        // plus the second order overlaps, etc. This also computes entropy, though
        // it isn't correct if the model contains loops. For models with loops, use IPF.
        void calculateDfAndEntropy(ocModel *model);

        // Determine if the model has loops, and cache this fact for later use
        bool hasLoops(ocModel *model);

        // compute various relation and model attributes. False is returned on error
        // (e.g., no table has been computed) If computation is successful, the
        // attribute is added to the attribute list for the relation or model.
        virtual double computeDF(ocRelation *rel); // degrees of freedom
        virtual double computeDF(ocModel *model);
        virtual double computeH(ocRelation *rel); // uncertainty
        virtual double computeH(ocModel *model, HMethod method = AUTO, int SB = 0);
        virtual double computeTransmission(ocModel *model, HMethod method = AUTO, int SB = 0);
        virtual void computeStatistics(ocRelation *rel);
        virtual void computeRelWidth(ocModel *model);
        double computeLR(ocModel *model);
        virtual double computeDDF(ocModel *model);

        //-- computes the incremental alpha relative to a model's progenitor
        void computeIncrementalAlpha(ocModel *model);
        //-- compares a new progenitor to an existing one, so the best is kept
        void compareProgenitors(ocModel *model, ocModel *newProgen);

        // Sets the direction in which search is occurring, which is mostly used for information.
        // 0 = up, 1 = down.  This doesn't actually control the direction of search, but it's
        // useful for determining other things, such as DDF.
        void setSearchDirection(int dir);
        int getSearchDirection() {
            return searchDirection;
        }

        double computeDfSb(ocModel *model);

        virtual ocModel *getTopRefModel() {
            return topRef;
        }
        virtual ocModel *getBottomRefModel() {
            return bottomRef;
        }
        virtual ocModel *getRefModel() {
            return refModel;
        }
        virtual int getUseInverseNotation() {
            return useInverseNotation;
        }
        void setValuesAreFunctions(int flag);
        bool getValuesAreFunctions() {
            return valuesAreFunctions;
        }
        double getFunctionConstant() {
            return functionConstant;
        }
        double getNegativeConstant() {
            return negativeConstant;
        }
        int getKeySize() {
            return keysize;
        }
        double getSampleSz() {
            return sampleSize;
        }
        double getTestSampleSize() {
            return testSampleSize;
        }
        ocVariableList *getVariableList() {
            return varList;
        }
        class ocRelCache *getRelCache() {
            return relCache;
        }
        class ocModelCache *getModelCache() {
            return modelCache;
        }
        class ocTable *getInputData() {
            return inputData;
        }
        class ocTable *getTestData() {
            return testData;
        }
        int getDefaultDVIndex();
        int getDvOrder(int index);
        void createDvOrder();
        double getMissingCardinalityFactor(ocModel *model);
        void getPredictingVars(ocModel *model, int *varindices, int &varcount, bool includeDeps);
        ocRelation *getDepRelation();
        ocRelation *getIndRelation();

        //-- generate a model, given the name. This assumes "." as variable separator and
        //-- ":" as relation separator. Optionally the data projection can be created.
        ocModel *makeModel(const char *name, bool makeProject = true);
        ocModel *makeSbModel(const char *name, bool makeProject = true);

        //-- get and set options. The options are initialized by command line or datafile options
        bool setOptionString(ocOptionDef *def, const char *value) {
            return options->setOptionString(def, value);
        }
        bool setOptionFloat(ocOptionDef *def, double nvalue) {
            return options->setOptionFloat(def, nvalue);
        }
        bool getOptionString(const char *name, void **next, const char **value) {
            return options->getOptionString(name, next, value);
        }
        bool getOptionFloat(const char *name, void **next, double *nvalue) {
            return options->getOptionFloat(name, next, nvalue);
        }

        void printOptions(bool printHTML = false, bool skipNominal = false);

        class ocTable *getFitTable() {
            return fitTable1;
        }
        // state based Model functions
        // calculates the number of state constraints generated
        // by a particular relation
        long calcStateConstSize(int varcount, int *varindices, int *stateindices);

        // add the state constraints for a relation
        int addConstraint(int varcount, int *varindices, int *stateindices, int* stateindices_c, ocKeySegment* start,
                ocRelation *rel);
//    int** makeStateSpaceArr(int statespace = 0);

        //-- Print debug info on memory usage
        void printSizes();

        //-- print out all relations
        void dumpRelations();

    protected:
        ocModel *topRef;
        ocModel *bottomRef;
        ocModel *refModel;
        ocVariableList *varList;
        int keysize;
        double sampleSize;
        double testSampleSize;
        unsigned long long stateSpaceSize;
        ocTable *inputData;
        ocTable *testData;
        double inputH;
        class ocRelCache *relCache;
        class ocModelCache *modelCache;
        class ocOptions *options;
        ocTable *fitTable1;
        ocTable *fitTable2;
        ocTable *projTable;
        int dataLines;
        int *DVOrder;
        int useInverseNotation;
        VarIntersect *intersectArray;
        int intersectCount;
        long intersectMax;
        double functionConstant;
        double negativeConstant;
        bool valuesAreFunctions;
        int searchDirection;
};

#endif

