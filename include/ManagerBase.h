/*
 * Copyright © 1990 The Portland State University OCCAM Project Team
 * [This program is licensed under the GPL version 3 or later.]
 * Please see the file LICENSE in the source
 * distribution of this software for license terms.
 */

#ifndef ___ManagerBase
#define ___ManagerBase

#include "Model.h"
#include "Options.h"
#include "VarIntersect.h"
#include <map>

/**
 * ocIntersectProcessor - this is a base class for processing classes
 * used by ManagerBase::doIntersectProcessing. This function does the
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
        virtual void process(bool sign, Relation *rel, int count = 1) = 0;
};

/**
 * ManagerBase - implements base functionality of an ocManager.  This class is the
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

using std::map;
typedef map<Relation*, long long> FitIntersectMap;

class ManagerBase {
    public:
        // method to use for computing H. Auto means use IPF if there are loops and
        // algebraic method otherwise.
        enum HMethod {
            AUTO, IPF, ALGEBRAIC
        };


        // create an ManagerBase object, supplying it with a variable list and a table
        // of input data.  Typically an application will read the input data and variable
        // definitions, and then construct the appropriate manager.
        ManagerBase(VariableList *vars = 0, Table *input = 0);

        // initialize an ManagerBase object, reading in standard options and data files.
        bool initFromCommandLine(int argc, char **argv);

	void setAlphaThreshold(double thresh);

        // delete this object
        virtual ~ManagerBase();

        // get the relation defined by the list of variable indices and the count.
        // this will first search the cache and, if the relation is found, return it.
        // if not in the cache, a new relation is created. If instructed, the projection
        // corresponding to the relation is also created.
        virtual Relation *getRelation(int *varindices, int varcount, bool makeProject = false, int *stateindices = NULL);

        // get a relation just like the given relation, but with the given variable removed.
        // (skip is the variable id in the master variable list).
        virtual Relation *getChildRelation(Relation *rel, int skip, bool makeProject = false,
                int *stateindices = 0);

        // make a projection.  This creates an Table, and installs it as the table for the
        // given relation.  The projection is determined from the given table, and the
        // VariableList is the one associated with the given relation. False is returned on
        // any error. This function returns true immediately if the relation already has a table.
        virtual bool makeProjection(Relation *rel);

        // make a projection of table t1 into t2 (empty), based on the variable
        // list contained in the given relation. This is used as one step of the IPF algorithm.
        virtual bool makeProjection(Table *t1, Table *t2, Relation *rel);

        // make a "maxProjection" of one table into another. This creates a partial
        // probability distribution by keeping only the max values for each matching tuple.
        // rel provides the set of variables to be used in the match (generally the IV set).
        virtual bool makeMaxProjection(Table *t1, Table *t2, Table *inputData, Relation *indRel,
                Relation *depRel, double* missedValues);

        // make projections for all relations in a model. This just calls makeProject
        // as many times as needed.
        virtual bool makeProjections(Model *model);

        // delete projection tables from all relations in cache
        virtual void deleteTablesFromCache();

        // delete a model from the model cache
        virtual bool deleteModelFromCache(Model *model);


        // Make a fit table. This function uses the IPF algorithm. The fit table is
        // linked to the model.  If the model already has a fit table, the function
        // returns immediately. False is returned on any error.
        virtual void fitTestAlgebraic(Model *model, Table* algTable, double missingCard, const FitIntersectMap& map);
        virtual bool makeFitTable(Model *model);
        virtual bool makeFitTableIPF(Model *model);
        virtual bool makeFitTableAlgebraic(Model *model);

        // Expand a single tuple into all values of all missing variables, recursively
        void expandTuple(double tupleValue, KeySegment *key, int *missingVars, int missingCount, Table *outTable,
                int currentMissingVar);

        void makeOrthoExpansion(Relation *rel, Table *table);
        void makeSbExpansion(Relation *rel, Table *table);

        // Process relations and intersections, as need for DF and H computation
        void doIntersectionProcessing(Model *model, ocIntersectProcessor *proc);

        // Compute degrees of freedom of a model.  This involves computing degrees
        // of freedom of the constituent relations, minus the first order overlaps,
        // plus the second order overlaps, etc. This also computes entropy, though
        // it isn't correct if the model contains loops. For models with loops, use IPF.
        void calculateDfAndEntropy(Model *model);

        // Determine if the model has loops, and cache this fact for later use
        bool hasLoops(Model *model);

        // compute various relation and model attributes. False is returned on error
        // (e.g., no table has been computed) If computation is successful, the
        // attribute is added to the attribute list for the relation or model.
        virtual double computeDF(Relation *rel); // degrees of freedom
        virtual double computeDF(Model *model);
        virtual double computeH(Relation *rel); // uncertainty
        virtual double computeH(Model *model, HMethod method = AUTO, int SB = 0);
        virtual double computeTransmission(Model *model, HMethod method = AUTO, int SB = 0);
        virtual void computeStatistics(Relation *rel);
        virtual void computeRelWidth(Model *model);
        double computeLR(Model *model);
        virtual double computeDDF(Model *model);

        //-- computes the incremental alpha relative to a model's progenitor
        void computeIncrementalAlpha(Model *model);
        //-- compares a new progenitor to an existing one, so the best is kept
        void compareProgenitors(Model *model, Model *newProgen);

        // Sets the direction in which search is occurring, which is mostly used for information.
        // 0 = up, 1 = down.  This doesn't actually control the direction of search, but it's
        // useful for determining other things, such as DDF.
        void setSearchDirection(Direction dir);
        Direction getSearchDirection() { return searchDirection; }

        double computeDfSb(Model *model);

        virtual Model *getTopRefModel() {
            return topRef;
        }
        virtual Model *getBottomRefModel() {
            return bottomRef;
        }
        virtual Model *getRefModel() {
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
        VariableList *getVariableList() {
            return varList;
        }
        class RelCache *getRelCache() {
            return relCache;
        }
        class ModelCache *getModelCache() {
            return modelCache;
        }
        class Table *getInputData() {
            return inputData;
        }
        class Table *getTestData() {
            return testData;
        }
        int getDefaultDVIndex();
        int getDvOrder(int index);
        void createDvOrder();
        double getMissingCardinalityFactor(Model *model);
        void getPredictingVars(Model *model, int *varindices, int &varcount, bool includeDeps);
        void getRelevantVars(Model *model, int *varindices, int &varcount, bool includeDeps);
        Relation *getDepRelation();
        Relation *getIndRelation();

        //-- generate a model, given the name. This assumes "." as variable separator and
        //-- ":" as relation separator. Optionally the data projection can be created.
        Model *makeModel(const char *name, bool makeProject = true);
        Model *makeSbModel(const char *name, bool makeProject = true);

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

        class Table *getFitTable() {
            return fitTable1;
        }
        // state based Model functions
        // calculates the number of state constraints generated
        // by a particular relation
        long calcStateConstSize(int varcount, int *varindices, int *stateindices);

        // add the state constraints for a relation
        int addConstraint(int varcount, int *varindices, int *stateindices, int* stateindices_c, KeySegment* start,
                Relation *rel);
//    int** makeStateSpaceArr(int statespace = 0);

        //-- Print debug info on memory usage
        void printSizes();

        //-- print out all relations
        void dumpRelations();
        double alpha_threshold = 0.05;

        // Create an array of relation intersections for an algebraic fit table.
        FitIntersectMap computeIntersectLevels(Model* model);

        Table* getIndepTable();
        Table* disownTable();

        Table* projectedFit(Relation* projectTo, Model* fitModel);

        Model* projectedModel(Relation* projectTo, Model* model);

    protected:
        Model *topRef;
        Model *bottomRef;
        Model *refModel;
        VariableList *varList;
        int keysize;
        double sampleSize;
        double testSampleSize;
        unsigned long long stateSpaceSize;
        Table *inputData;
        Table *testData;
        double inputH;
        class RelCache *relCache;
        class ModelCache *modelCache;
        class Options *options;
        Table *fitTable1;
        Table *fitTable2;
        Table *projTable;
        int dataLines;
        int *DVOrder;
        int useInverseNotation;
        VarIntersect *intersectArray;
        int intersectCount;
        int intersectMax;
        double functionConstant;
        double negativeConstant;
        bool valuesAreFunctions;
        Direction searchDirection;


};

#endif

