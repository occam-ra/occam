/* Copyright 2000, Portland State University Systems Science Program.  All Rights Reserved
 */

#include <math.h>
#include "ocCore.h"
#include "_ocCore.h"
#include "ocManagerBase.h"
#include "ocMath.h"
#include "ocRelCache.h"
#include "ocModelCache.h"
#include "ocOptions.h"
#include "ocInput.h"
#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
//#include "ocWin32.h"

const int defaultRelSize = 10;

//#define LOG_PROJECTIONS
#ifdef LOG_PROJECTIONS
static FILE *projfd = NULL;
void logProjection(const char *name)
{
    if (projfd == NULL) projfd = fopen("projections.log", "w");
    if (projfd == NULL) return;
    fprintf(projfd, "%s\n", name);
    fflush(projfd);
}
#else
void logProjection(const char *name) {
}
#endif

ocManagerBase::ocManagerBase(ocVariableList *vars, ocTable *input) :
        varList(vars), inputData(input), keysize(vars ? vars->getKeySize() : 0) {
    topRef = bottomRef = refModel = NULL;
    relCache = new ocRelCache;
    modelCache = new ocModelCache;
    sampleSize = 0;
    testSampleSize = 0;
    options = new ocOptions();
    inputH = -1;
    stateSpaceSize = 0;
    fitTable1 = NULL;
    fitTable2 = NULL;
    projTable = NULL;
    inputData = testData = NULL;
    DVOrder = NULL;
    searchDirection = 0;
    useInverseNotation = 0;
    valuesAreFunctions = false;
    intersectArray = NULL;
    intersectCount = 0;
    intersectMax = 1;
    functionConstant = 0;
    negativeConstant = 0;
}

bool ocManagerBase::initFromCommandLine(int argc, char **argv) {
    ocTable *input = NULL, *test = NULL;
    ocVariableList *vars;
    //-- get all command line options.  Datafile arguments show up as "datafile" option.
    options->setOptions(argc, argv);

    //-- now read datafiles (which may also contain options)
    void *next = NULL;
    const char *fname;
    while (options->getOptionString("datafile", &next, &fname)) {
        FILE *fd = fopen(fname, "r");
        if (fd == NULL) {
            printf("ERROR: couldn't open %s\n", fname);
            return false;
        } else if ((dataLines = ocReadFile(fd, options, &input, &test, &vars)) == 0) {
            printf("ERROR: ocReadFile() failed for %s\n", fname);
            return false;
        }
    }
    varList = vars;

    if (!varList->isDirected()) {
        if (getOptionFloat("function-constant", NULL, &functionConstant)) {
            input->addConstant(functionConstant);
            if (test)
                test->addConstant(functionConstant);
            setValuesAreFunctions(1);
        } else {
            functionConstant = 0;
        }
    }

    const char *option;
    if (getOptionString("function-values", NULL, &option)) {
        setValuesAreFunctions(1);
    }

    // check for negative values in the data
    negativeConstant = input->getLowestValue();
    if (test) {
        double testLowest = test->getLowestValue();
        if (testLowest < negativeConstant)
            negativeConstant = testLowest;
    }
    if (negativeConstant < 0) {
        if (varList->isDirected()) {
            printf("ERROR: Negative frequency values are not permitted in directed systems.\n");
            return false;
        }
        setValuesAreFunctions(1);
        negativeConstant *= -1;
        input->addConstant(negativeConstant);
        if (test)
            test->addConstant(negativeConstant);
    } else {
        negativeConstant = 0;
    }

    sampleSize = input->normalize();
    if (test)
        testSampleSize = test->normalize();

    // if sampleSize is equal to 1, this is probability data, and we should treat it as a function
    if (fabs(sampleSize - 1) < DBL_EPSILON) {
        setValuesAreFunctions(1);
    }

    inputData = input;
    testData = test;
    inputH = ocEntropy(inputData);
    keysize = vars->getKeySize();
    return true;
}

ocManagerBase::~ocManagerBase() {
    if (testData) delete testData;
    if (fitTable1) delete fitTable1;
    if (fitTable2) delete fitTable2;
    if (projTable) delete projTable;
    if (intersectArray) delete[] intersectArray;
    if (DVOrder) delete[] DVOrder;
    delete options;
    delete modelCache;
    delete relCache;
    if (varList) delete varList;
}

// Anjali..
// this function calculates the number of state constraints imposed by a particular relation which
// has variables as are present in the varindices list and state constraints as present in the
// stateindices list, a state value of -1 implies a dont_care value
int ocManagerBase::calcStateConstSize(int varcount, int *varindices, int *stateindices) {
    int size = 1;
    ocVariable *var;
    int card = 0;
    if (varindices == NULL || stateindices == NULL)
        return -1;
    for (int i = 0; i < varcount; i++) {
        if (stateindices[i] == DONT_CARE) {
            var = varList->getVariable(varindices[i]);
            card = var->cardinality;
            size = size * card;
        }
    }
    return size;
}

//--add the constraints for a relation
int ocManagerBase::addConstraint(int varcount, int *varindices, int *stateindices, int* stateindices_c,
        ocKeySegment* start1, ocRelation *rel) {
    ocVariable *var;
    int keysize = getKeySize();
    int count = varcount - 1;
    int card = 0;
    //get card
    while (stateindices[count] != DONT_CARE) {
        count--;
        if (count < 0)
            return 0;
    }
    start: var = varList->getVariable(varindices[count]);
    card = var->cardinality;
    if (stateindices_c[count] == (card - 1)) {
        stateindices_c[count] = 0x00;
        count--;
        if (count >= 0) {
            while (stateindices[count] != DONT_CARE) {
                count--;
                if (count < 0)
                    return 0;
            }
            goto start;
        } else {
            return 0;
        }
    } else {
        stateindices_c[count]++;
        ocKey::buildKey(start1, keysize, varList, varindices, stateindices_c, varcount);
        rel->getStateConstraints()->addConstraint(start1);
        addConstraint(varcount, varindices, stateindices, stateindices_c, start1, rel);
        return 0;
    }
}

//-- look in relCache and, if not found, make a new relation and store in relCache
// *** warning: this function sorts varindices in place ***
ocRelation *ocManagerBase::getRelation(int *input_vars, int varcount, bool make_project, int *input_states) {
    int* varindices = new int[varcount];
    memcpy(varindices, input_vars, varcount * sizeof(int));
    int* stateindices = NULL;
    if (input_states != NULL) {
        stateindices = new int[varcount];
        memcpy(stateindices, input_states, varcount * sizeof(int));
    }
    int stateconstsz = 0;
    ocRelation::sort(varindices, varcount, stateindices);
    int keysize = getKeySize();
    ocRelation *rel;
    if (stateindices != NULL) {
        int *stateindices1 = new int[varcount];
        ocKeySegment* mask = new ocKeySegment[keysize];
        ocKeySegment* start1 = new ocKeySegment[keysize];
        memset(stateindices1, 0, varcount * sizeof(int));
        memset(mask, 0, keysize * sizeof(ocKeySegment));
        memset(start1, 0, keysize * sizeof(ocKeySegment));
        ocKey::buildMask(mask, keysize, varList, varindices, varcount);
        ocKey::buildMask(start1, keysize, varList, varindices, varcount);
        stateconstsz = calcStateConstSize(varcount, varindices, stateindices);
        rel = new ocRelation(varList, varList->getVarCount(), keysize, stateconstsz);
        for (int i = 0; i < varcount; i++) {
            rel->addVariable(varindices[i], stateindices[i]);
        }
        if (!relCache->addRelation(rel)) {
            ocRelation *cached_rel = relCache->findRelation(rel->getPrintName());
            delete rel;
            rel = cached_rel;
        } else {
            //make starting constraint
            for (int i = 0; i < varcount; i++) {
                if (stateindices[i] == DONT_CARE) {
                    stateindices1[i] = 0x00;
                } else {
                    stateindices1[i] = stateindices[i];
                }
            }
            //build the first constraint and then loop
            ocKey::buildKey(start1, keysize, varList, varindices, stateindices1, varcount);
            rel->getStateConstraints()->addConstraint(start1);
            addConstraint(varcount, varindices, stateindices, stateindices1, start1, rel);
        }
        delete[] start1;
        delete[] mask;
        delete[] stateindices1;
        delete[] stateindices;
    } else {
        rel = new ocRelation(varList, varList->getVarCount());
        for (int i = 0; i < varcount; i++) {
            rel->addVariable(varindices[i]);
        }
        if (!relCache->addRelation(rel)) {
            ocRelation *cached_rel = relCache->findRelation(rel->getPrintName());
            delete rel;
            rel = cached_rel;
        }
    }
    if (make_project) {
        makeProjection(rel);
    }
    delete[] varindices;
    return rel;
}

// "skip" is the index of the variable in the varList
ocRelation *ocManagerBase::getChildRelation(ocRelation *rel, int skip, bool makeProject, int *stateindices) {
    int order = rel->getVariableCount();
    int *varindices = new int[order];
    int slot = 0;
    ocRelation *newRel = NULL;
    for (int i = 0; i < order; i++) {
        //-- build a list of all variables but skip
        if (rel->getVariable(i) != skip)
            varindices[slot++] = rel->getVariable(i);
    }
    //-- build and cache the relation
    newRel = getRelation(varindices, order - 1, makeProject, stateindices);
    delete varindices;
    return newRel;
}

// This function is a special case of the other makeProjection(), further below.
// It projects the input data into the table for a relation.
bool ocManagerBase::makeProjection(ocRelation *rel) {
    if (rel->getTable())
        return true; // table already computed

    //-- create the projection data for a given relation. Go through
    //-- the inputData, and for each tuple, sum it into the table for the relation.
    long long start_size = rel->getNC();
    if ((inputData->getTupleCount() < start_size) || (start_size <= 0)) {
        start_size = inputData->getTupleCount();
    }
    //logProjection(rel->getPrintName());
    ocTable *table = new ocTable(keysize, start_size);
    rel->setTable(table);
    makeProjection(inputData, table, rel);
    return true;
}

// This function projects the data in table t1 into (empty) table t2, based on the relation.
bool ocManagerBase::makeProjection(ocTable *t1, ocTable *t2, ocRelation *rel) {
    //-- create the projection data for a given relation. Go through
    //-- the inputData, and for each tuple, sum it into the table for the relation.
    long long count = t1->getTupleCount();
    t2->reset(keysize); // reset the output table
    ocKeySegment *key = new ocKeySegment[keysize];
    ocKeySegment *mask = rel->getMask();
    long i, j, k;
    double value;

    bool is_match = false;  // for state-based
    double remainder = 0;   // for state-based
    int c_count;            // for state-based
    ocKeySegment *const_k;  // for state-based
    if (rel->isStateBased()) { // for state-based
        c_count = rel->getStateConstraints()->getConstraintCount();
        makeSbExpansion(rel, t2);
    }
    for (i = 0; i < count; i++) {
        t1->copyKey(i, key);
        value = t1->getValue(i);
        //-- set all the variables in the key to dont_care if they don't exist in the relation
        for (k = 0; k < keysize; k++) {
            key[k] |= mask[k];
        }
        if (!rel->isStateBased()) {
            t2->sumTuple(key, value);
        } else {
            // state based, so if the key matches one of the constraints we keep it,
            // otherwise add it to the remainder to be split up later
            for (j = 0; j < c_count; j++) {
                is_match = false;
                const_k = rel->getStateConstraints()->getConstraint(j);
                if (ocKey::compareKeys(key, const_k, keysize) == 0) {
                    is_match = true;
                    break;
                }
            }
            if (is_match) {
                t2->sumTuple(key, value);
            } else {
                remainder += value;
            }
        }
    }
    if (rel->isStateBased()) {
        // now, for SB relations, spread remainder through unused cells
        count = t2->getTupleCount();
        for (i = 0; i < count; i++) {
            is_match = false;
            for (j = 0; j < c_count; j++) {
                const_k = rel->getStateConstraints()->getConstraint(j);
                if (ocKey::compareKeys(t2->getKey(i), const_k, keysize) == 0) {
                    is_match = true;
                    break;
                }
            }
            if (is_match == false) {
                t2->setValue(i, remainder / (count - c_count));
            }
        }
    }
    t2->sort();
    delete[] key;
    return true;
}

bool ocManagerBase::makeMaxProjection(ocTable *qt, ocTable *maxpt, ocTable *inputData, ocRelation *indRel,
        ocRelation *depRel, double *missedValues) {
    //-- create the max projection data for the IV relation, used for computing percent correct.
    //-- Two new tables are created. maxqt contains a tuple for each distinct IV state,
    //-- and the q value from the qt table. maxpt contains a corresponding tuple for each distinct
    //-- IV state, and the p value (from the input data).
    //-- A pass is made through the qt table, and for each tuple, it is checked against the
    //-- maxqt table. If it has not been added yet, or if its q value is greater than the value
    //-- already present on the matching tuple in maxqt, then both the maxqt tuple and the maxpt
    //-- tuples are updated. At the end, maxpt has a tuple for each IV state, and the p value
    //-- for the specific IV,DV state which corresponds to the greatest q value across the DV
    //-- states for that IV state.
    if (qt == NULL || maxpt == NULL || indRel == NULL || depRel == NULL)
        return false;
    long long count = qt->getTupleCount();
    ocTable *maxqt = new ocTable(keysize, count);
    ocTable *dvt = new ocTable(keysize, count);
    maxpt->reset(keysize); // reset the output table
    ocKeySegment *key = new ocKeySegment[keysize];
    ocKeySegment *mask = indRel->getMask();
    long long i, pindex, maxqindex, maxpindex, dvindex;
    int k;
    double qvalue, pvalue, maxqvalue;
    int qdv, pdv, maxdv;
    int defaultDV = getDefaultDVIndex();
    for (i = 0; i < count; i++) {
        qt->copyKey(i, key);
        qvalue = qt->getValue(i);
        pindex = inputData->indexOf(key);
        pvalue = 0.0;
        if (pindex >= 0)
            pvalue = inputData->getValue(pindex);
        qdv = ocKey::getKeyValue(key, keysize, varList, varList->getDV());
        //-- set up key to match just IVs
        for (k = 0; k < keysize; k++)
            key[k] |= mask[k];
        maxqindex = maxqt->indexOf(key);
        maxpindex = maxpt->indexOf(key);
        dvindex = dvt->indexOf(key);
        if (maxqindex >= 0 && maxpindex >= 0) {
            //-- we already saw this IV state; see if the q value is greater
            maxqvalue = maxqt->getValue(maxqindex);
            if (fabs(maxqvalue - qvalue) < DBL_EPSILON) {
                // Break any ties by checking the order of the DV values
                maxdv = (int) dvt->getValue(dvindex);
                if (getDvOrder(qdv) < getDvOrder(maxdv)) {
                    maxqt->setValue(maxqindex, qvalue);
                    maxpt->setValue(maxpindex, pvalue);
                    dvt->setValue(dvindex, (double) qdv);
                }
            } else if (maxqvalue < qvalue) {
                maxqt->setValue(maxqindex, qvalue);
                maxpt->setValue(maxpindex, pvalue);
                dvt->setValue(dvindex, (double) qdv);
            }
        } else {
            //-- new IV state; add to both tables
            //-- we have to call indexOf again to get the position, then do the insert
            maxqt->insertTuple(key, qvalue, maxqt->indexOf(key, false));
            maxpt->insertTuple(key, pvalue, maxpt->indexOf(key, false));
            dvt->insertTuple(key, (double) qdv, dvt->indexOf(key, false));
        }
    }

    //-- Add in entries for the default rule (i.e., if the model doesn't predict
    //-- a DV value for a particular IV, then just use the most likely DV value).
    //-- To do this we go through the inputData and find tuples for which (a) the IV
    //-- state does not exist in maxpt, and (b) where the DV value is the most likely value.
    //-- These are the inputData tuples which are predicted correctly by the default rule.
    //-- Their probabilities need to be accounted for.
    if (missedValues != NULL) {
        long long index;
        double value;
        count = inputData->getTupleCount();
        (*missedValues) = 0;
        for (i = 0; i < count; i++) {
            inputData->copyKey(i, key);
            for (k = 0; k < keysize; k++)
                key[k] |= mask[k];
            if (maxpt->indexOf(key) >= 0) {
                continue; //-- model predicts this; don't need default
            } else {
                value = inputData->getValue(i);
                (*missedValues) += value;
                pdv = ocKey::getKeyValue(inputData->getKey(i), keysize, varList, varList->getDV());
                if (pdv != defaultDV)
                    continue;

                //-- add this entry to maxpt; default rule applies
                if (value > 0) {
                    index = maxpt->indexOf(key, false);
                    maxpt->insertTuple(key, value, index);
                }
            }
        }
    }
    maxpt->sort();
    delete[] key;
    delete maxqt;
    return true;
}

int ocManagerBase::getDefaultDVIndex() {
    if (!varList->isDirected())
        return NULL; // can only do this for directed models
    if (DVOrder == NULL)
        createDvOrder();
    return DVOrder[0];
}

int ocManagerBase::getDvOrder(int index) {
    if (!varList->isDirected())
        return NULL;
    if (DVOrder == NULL)
        createDvOrder();
    int dv_card = varList->getVariable(varList->getDV())->cardinality;
    for (int i = 0; i < dv_card; ++i) {
        if (DVOrder[i] == index)
            return i;
    }
    return NULL;
}

static double *sort_freq;
static ocVariable *sort_dv_var;
int sortDV(const void *d1, const void *d2) {
    int a = *(int*) d1;
    int b = *(int*) d2;
    // Would prefer to use DBL_EPSILON here, but the frequencies we get for DV values (from the bottom reference)
    // are not precise enough for some reason.
    if (fabs(sort_freq[a] - sort_freq[b]) < 1e-10) {
        return strcmp(sort_dv_var->valmap[a], sort_dv_var->valmap[b]);
    }
    if (sort_freq[a] > sort_freq[b]) {
        return -1;
    }
    if (sort_freq[a] < sort_freq[b]) {
        return 1;
    }
    // Put this again, just in case.
    return strcmp(sort_dv_var->valmap[a], sort_dv_var->valmap[b]);
}

void ocManagerBase::createDvOrder() {
    if (!varList->isDirected())
        return;
    if (DVOrder != NULL)
        return;
    sort_dv_var = varList->getVariable(varList->getDV());
    int dv_card = sort_dv_var->cardinality;
    DVOrder = new int[dv_card];
    // Build an array of frequencies, taken from the dependent relation (from the bottom reference)
    long long k;
    ocTable *depTable;
    for (k = 0; k < bottomRef->getRelationCount(); ++k) {
        if (!bottomRef->getRelation(k)->isIndependentOnly()) {
            depTable = bottomRef->getRelation(k)->getTable();
            break;
        }
    }
    sort_freq = new double[dv_card];
    for (k = 0; k < depTable->getTupleCount(); ++k) {
        sort_freq[ocKey::getKeyValue(depTable->getKey(k), keysize, varList, varList->getDV())] = depTable->getValue(k);
    }
    for (int i = 0; i < dv_card; ++i)
        DVOrder[i] = i;
    qsort(DVOrder, dv_card, sizeof(int), sortDV);
}

// Creates a product of the cardinalities of any variables missing from the model
// (but present in the data).  Used for adjusting calculated values when fitting
// a loopless model algorithmically.
double ocManagerBase::getMissingCardinalityFactor(ocModel *model) {
    ocVariableList *vars = getVariableList();
    int vcount = vars->getVarCount();
    int rcount = model->getRelationCount();
    int vi, ri;
    int card;
    double missingCards = 1;
    for (vi = 0; vi < vcount; vi++) {
        card = vars->getVariable(vi)->cardinality;
        for (ri = 0; ri < rcount; ri++) {
            if (model->getRelation(ri)->findVariable(vi) >= 0) {
                card = 1;
                break;
            }
        }
        missingCards *= card;
    }
    return missingCards;
}

void ocManagerBase::getPredictingVars(ocModel *model, int *varindices, int &varcount, bool includeDeps) {
    ocVariableList *vars = getVariableList();
    varcount = 0;
    for (int r = 0; r < model->getRelationCount(); r++) {
        ocRelation *rel = model->getRelation(r);
        if (rel->isIndependentOnly())
            continue;
        for (int iv = 0; iv < rel->getVariableCount(); iv++) {
            int varid = rel->getVariable(iv);
            if (vars->getVariable(varid)->dv && !includeDeps)
                continue;
            for (int jv = 0; jv < varcount; jv++) {
                if (varid == varindices[jv]) {
                    varid = -1;
                    break;
                }
            }
            if (varid >= 0)
                varindices[varcount++] = varid;
        }
    }
}

ocRelation *ocManagerBase::getIndRelation() {
    if (!getVariableList()->isDirected())
        return NULL; // can only do this for directed models
    for (int i = 0; i < bottomRef->getRelationCount(); i++) {
        ocRelation *indRel = bottomRef->getRelation(i);
        if (indRel->isIndependentOnly())
            return indRel; // this is the one.
    }
    return NULL;
}

ocRelation *ocManagerBase::getDepRelation() {
    // This function takes advantage of the fact that the bottom model has only two relations;
    // one is the IV relation, the other is the DV.
    if (!getVariableList()->isDirected())
        return NULL; // can only do this for directed models
    for (int i = 0; i < bottomRef->getRelationCount(); i++) {
        ocRelation *dep_rel = bottomRef->getRelation(i);
        if (!dep_rel->isIndependentOnly())
            return dep_rel; // this is the one.
    }
    return NULL;
}

bool ocManagerBase::makeProjections(ocModel *model) {
    //-- create projections for all relations in model
    int count = model->getRelationCount();
    for (int i = 0; i < count; i++) {
        if (!makeProjection(model->getRelation(i)))
            return false;
    }
    return true;
}

void ocManagerBase::deleteTablesFromCache() {
    relCache->deleteTables();
}

bool ocManagerBase::deleteModelFromCache(ocModel *model) {
    return modelCache->deleteModel(model);
}

//static bool nextTuple(ocVariableList *varList, int *varvalues) {
//    int varcount = varList->getVarCount();
//    // bump the last variable by one; if it overflows, carry to the
//    // previous one, etc. Return false if we overflow the whole variable list
//    int i = varcount - 1;
//    varvalues[i]++;
//    while (varvalues[i] >= varList->getVariable(i)->cardinality) {
//        if (i == 0)
//            return false; // overflow
//        varvalues[i--] = 0;
//        varvalues[i]++;
//    }
//    return true;
//}

//-- intersect two variable lists, producing a third. returns true if intersection
//-- is not empty, and returns the list and count of common variables
static bool intersect(ocRelation *rel1, ocRelation *rel2, int* &var, int &count) {
    int *var1, *var2;
    int count1, count2;
    count1 = rel1->getVariableCount();
    var1 = rel1->getVariables();
    count2 = rel2->getVariableCount();
    var2 = rel2->getVariables();

    var = NULL;
    count = 0;
    for (int i = 0; i < count1; i++) {
        for (int j = 0; j < count2; j++) {
            if (var1[i] == var2[j]) {
                if (var == NULL)
                    var = new int[count1]; //this is sure to be large enough
                var[count++] = var1[i];
            }
        }
    }
    return var != NULL;
}

static VarIntersect *fitIntersectArray = NULL;
static int fitIntersectCount = 0;
static long fitIntersectMax = 1;

void ocManagerBase::doFitIntersection(ocModel *model) {
    if (model == NULL)
        return;
    if (fitIntersectArray != NULL) {
        delete[] fitIntersectArray;
    }
    fitIntersectCount = 0;
    fitIntersectMax = model->getRelationCount();
    fitIntersectArray = new VarIntersect[fitIntersectMax];

    ocVariableList *varList = model->getRelation(0)->getVariableList();
    ocRelation *rel;

    int i, j;
    for (i = 0; i < fitIntersectMax; i++) {
        rel = model->getRelation(i);
        VarIntersect *intersect = fitIntersectArray + (fitIntersectCount++);
        intersect->rel = rel;
        intersect->startIndex = i;
        intersect->sign = true;
    }
    int levelstart = 0;
    int levelend = fitIntersectCount;
    int level0end = fitIntersectCount;
    bool sign = true;
    int *newvars, newcount;
    VarIntersect *ip, *jp, *newp;

    while (levelend > levelstart) {
        sign = !sign;
        for (i = levelstart; i < levelend; i++) {
            for (j = fitIntersectArray[i].startIndex + 1; j < level0end; j++) {
                ip = fitIntersectArray + i;
                jp = fitIntersectArray + j;
                if (intersect(ip->rel, jp->rel, newvars, newcount)) {
                    rel = getRelation(newvars, newcount, true);
                    //-- add this intersection term to the DF, and append to list
                    while (fitIntersectCount >= fitIntersectMax) {
                        fitIntersectArray =
                                (VarIntersect*) growStorage(fitIntersectArray, sizeof(VarIntersect)*fitIntersectMax, 2);
                        fitIntersectMax *= 2;
                    }
                    newp = fitIntersectArray + (fitIntersectCount++);
                    newp->rel = rel;
                    newp->startIndex = j;
                    newp->sign = sign;
                    delete[] newvars;
                }
            }
        }
        levelstart = levelend;
        levelend = fitIntersectCount;
    }
}

bool ocManagerBase::makeFitTable(ocModel *model) {
    if (model == NULL)
        return false;
    // Check for models that can be fit algorithmically. If so, solve that way.
    if (!hasLoops(model) && !model->isStateBased() && !getVariableList()->isDirected()) {
        doFitIntersection(model);
        double missingCard = getMissingCardinalityFactor(model);
        for (int ri = 0; ri < fitIntersectCount; ri++) {        // check that all relations in intersectArray have projections
            makeProjection(fitIntersectArray[ri].rel);
        }
        //inputData->normalize();
        long long inSize = inputData->getTupleCount();
        ocTable *algTable = new ocTable(keysize, inSize);

        double value, outValue;
        ocKeySegment *tupleKey;
        long long ti;
        int ri;
        for (ti = 0; ti < inSize; ti++) {
            tupleKey = inputData->getKey(ti);
            outValue = 1;       // start outvalue at 1
            for (ri = 0; ri < fitIntersectCount; ri++) {        // for each item in intersectArray
                value = fitIntersectArray[ri].rel->getMatchingTupleValue(tupleKey);     // get value from relation for masked key
                if (fabs(value) < DBL_EPSILON) {                // if value is ever zero, set outValue to zero and end for-loop
                    outValue = 0;
                    break;
                }
                if (fitIntersectArray[ri].sign) {               // mult/div value into outValue
                    outValue *= value;
                } else {
                    outValue /= value;
                }
            }
            algTable->sumTuple(tupleKey, outValue / missingCard);       // put outvalue into fitted table
        }
        if (testData) {
            inSize = testData->getTupleCount();
            for (ti = 0; ti < inSize; ti++) {                           // for every tuple in test
                tupleKey = testData->getKey(ti);
                if (inputData->indexOf(tupleKey) == -1) {               // if this tuple wasn't in inputData
                    outValue = 1;
                    for (ri = 0; ri < fitIntersectCount; ri++) {        // for each item in intersectArray
                        // get value from relation for masked key
                        value = fitIntersectArray[ri].rel->getMatchingTupleValue(tupleKey);
                        if (fabs(value) < DBL_EPSILON) {                // if value is ever zero, set outValue to zero and end for-loop
                            outValue = 0;
                            break;
                        }
                        if (fitIntersectArray[ri].sign) {               // mult/div value into outValue
                            outValue *= value;
                        } else {
                            outValue /= value;
                        }
                    }
                    algTable->sumTuple(tupleKey, outValue / missingCard);       // put outvalue into fitted table
                }
            }
        }
        algTable->sort();
        if (fitTable1) delete fitTable1;
        fitTable1 = algTable;
        return true;
    }

    // For looped & SB models, proceed to solve with IPF.
    stateSpaceSize = (unsigned long long) ocDegreesOfFreedom(varList) + 1;
    if (!fitTable1) {
        //-- for large state spaces, start with less space and let it grow.
        if (stateSpaceSize > 1000000)
            stateSpaceSize = 1000000;
        fitTable1 = new ocTable(keysize, stateSpaceSize);
    }
    if (!fitTable2) {
        if (stateSpaceSize > 1000000)
            stateSpaceSize = 1000000;
        fitTable2 = new ocTable(keysize, stateSpaceSize);
    }
    if (!projTable) {
        if (stateSpaceSize > 1000000)
            stateSpaceSize = 1000000;
        projTable = new ocTable(keysize, stateSpaceSize);
    }
    fitTable1->reset(keysize);
    fitTable2->reset(keysize);
    projTable->reset(keysize);
    ocKeySegment *key = new ocKeySegment[keysize];
    int k;
    double error = 0;

    makeProjections(model);

    //-- compute the number of nonzero tuples in the expansion
    //-- of each relation, and start with the one where this is
    //-- smallest (to minimize memory usage)
    int startRel = 0;
    double expsize = model->getRelation(0)->getExpansionSize();
    double newexpsize;
    for (int r = 1; r < model->getRelationCount(); r++) {
        newexpsize = model->getRelation(r)->getExpansionSize();
        if (newexpsize < expsize) {
            startRel = r;
            expsize = newexpsize;
        }
    }
    makeOrthoExpansion(model->getRelation(startRel), fitTable1);

    //-- configurable fitting parameters
    //-- convergence error. This is approximately in units of samples.
    //-- if initial data was probabilities, an artificial scale of 1000 is used
    double delta2;
    if (!getOptionFloat("ipf-maxdev", NULL, &delta2))
        delta2 = .20;
    if (this->sampleSize > 0) {
        delta2 /= sampleSize;
    } else {
        delta2 /= 1000;
    }

    double maxiter;
    if (hasLoops(model) || (model->isStateBased() && (model->getRelationCount() > 1))) {
        if (!getOptionFloat("ipf-maxit", NULL, &maxiter))
            maxiter = 266;
    } else {
        maxiter = 1;
    }
    int iter, r;
    long long i, j;
    long long tupleCount;
    for (iter = 0; iter < maxiter; iter++) {
        error = 0.0; // abs difference between original proj and computed values
        for (r = 0; r < model->getRelationCount(); r++) {
            ocRelation *rel = model->getRelation(r);
            ocTable *relp = rel->getTable();
            ocKeySegment *mask = rel->getMask();
            // create a projection of the computed data, based on the variables in the relation
            projTable->reset(keysize);
            makeProjection(fitTable1, projTable, rel);
            // for each tuple in fitTable1, create a scaled tuple in fitTable2, scaled by the
            // ratio of the projection from the input data, and the computed projection
            // from the previous iteration.  In any cases where the input marginal is
            // zero, or where the computed marginal is zero, skip this tuple (equivalent
            // to setting it to zero, but conserves space).
            tupleCount = fitTable1->getTupleCount();
            fitTable2->reset(keysize);
            for (i = 0; i < tupleCount; i++) {
                double newValue = 0.0;
                fitTable1->copyKey(i, key);
                double value = fitTable1->getValue(i);
                for (k = 0; k < keysize; k++)
                    key[k] |= mask[k];
                j = relp->indexOf(key);
                if (j >= 0) {
                    double relvalue = relp->getValue(j);
                    if (relvalue > 0.0) {
                        j = projTable->indexOf(key);
                        if (j >= 0) {
                            double projvalue = projTable->getValue(j);
                            if (projvalue > 0.0) {
                                newValue = value * relvalue / projvalue;
                            }
                            error = fmax(error, fabs(relvalue - projvalue));
                        } else {
                            error = fmax(error, relvalue);
                        }
                    }
                }
                if (newValue > 0) {
                    fitTable1->copyKey(i, key);
                    fitTable2->addTuple(key, newValue);
                }
            }
            // swap fitTable1 and fitTable2 for next pass
            ocTable *ftswap = fitTable1;
            fitTable1 = fitTable2;
            fitTable2 = ftswap;
        }
        // check convergence
        if (error < delta2)
            break;
    }
    fitTable1->sort();
    model->setAttribute(ATTRIBUTE_IPF_ITERATIONS, (double) iter);
    model->setAttribute(ATTRIBUTE_IPF_ERROR, error);
    delete[] key;
    return true;
}

/**
 * compute the orthogonal expansion of a projection. This means taking every tuple in the projection, and
 * apportioning it evenly across all the states which map into the substate of that projection.
 */
void ocManagerBase::expandTuple(double tupleValue, ocKeySegment *key, int *missingVars, int missingCount,
        ocTable *outTable, int currentMissingVar) {
    if (missingCount == 0) {
        outTable->addTuple(key, tupleValue);
    } else {
        int var = missingVars[currentMissingVar++];
        //-- make a copy of the key, with the current variable replaced
        //-- by each legal value in turn.
        ocKeySegment newKey[keysize];
        int varvalue;
        int cardinality = getVariableList()->getVariable(var)->cardinality;
        for (varvalue = 0; varvalue < cardinality; varvalue++) {
            ocKey::copyKey(key, newKey, keysize);
            ocKey::setKeyValue(newKey, keysize, getVariableList(), var, varvalue);
            //-- If we have set all the values, then add this tuple. Otherwise recurse
            if (currentMissingVar >= missingCount) {
                outTable->addTuple(newKey, tupleValue);
            } else {
                expandTuple(tupleValue, newKey, missingVars, missingCount, outTable, currentMissingVar);
            }
        }
    }
}

void ocManagerBase::makeOrthoExpansion(ocRelation *rel, ocTable *outTable) {
    //-- get an array of the variable indices which don't occur in the relation.
    int varCount = rel->getVariableList()->getVarCount();
    int missingVars[varCount];
    int missingCount = rel->copyMissingVariables(missingVars, varCount);
    ocTable *relTable = rel->getTable();

    long long tupleCount = relTable->getTupleCount();
    outTable->reset(keysize);
    for (long long i = 0; i < tupleCount; i++) {
        ocKeySegment key[keysize];
        relTable->copyKey(i, key);
        double value = relTable->getValue(i);
        expandTuple(value, key, missingVars, missingCount, outTable, 0);
    }
    outTable->sort();
    outTable->normalize();
}

void ocManagerBase::makeSbExpansion(ocRelation *rel, ocTable *table) {
    int varCount = rel->getVariableCount();
    int vars[varCount];
    varCount = rel->copyVariables(vars, varCount);

    ocKeySegment *dont_care_key = new ocKeySegment[keysize];
    for (int k = 0; k < keysize; k++) {
        dont_care_key[k] = DONT_CARE;
    }
    expandTuple(0, dont_care_key, vars, varCount, table, 0);
    delete dont_care_key;
    //table->sort();
    //table->normalize();
}

bool ocManagerBase::hasLoops(ocModel *model) {
    bool loops;
    double dloops = model->getAttribute(ATTRIBUTE_LOOPS);
    if (dloops < 0) { // -1 = not set, 1 = true, 0 = false
        loops = ocHasLoops(model);
        model->setAttribute(ATTRIBUTE_LOOPS, loops ? 1 : 0);
    } else {
        loops = (dloops > 0);
    }
    return loops;
}

// For information purposes, tells us the direction of the search.
// 0 = up, 1 = down
void ocManagerBase::setSearchDirection(int dir) {
    if ((dir == 0) || (dir == 1))
        searchDirection = dir;
    else
        searchDirection = 0;
}

double ocManagerBase::computeDF(ocRelation *rel) { // degrees of freedom
    double df = rel->getAttribute(ATTRIBUTE_DF);
    if (df < 0.0) { //-- not set yet
        df = ::ocDegreesOfFreedom(rel);
        rel->setAttribute(ATTRIBUTE_DF, df);
    }
    return df;
}

double ocManagerBase::computeDfSb(ocModel *model) {
    double df = model->getAttribute(ATTRIBUTE_DF);
    if (df < 0.0) { //-- not set yet
        df = ::ocDegreesOfFreedomStateBased(model);
        model->setAttribute(ATTRIBUTE_DF, df);
    }
    return df;
}

double ocManagerBase::computeDF(ocModel *model) {
    double df = model->getAttribute(ATTRIBUTE_DF);
    if (df < 0.0) { //-- not set yet
        if (model->isStateBased()) {
            df = computeDfSb(model);
        } else {
            calculateDfAndEntropy(model);
            df = model->getAttribute(ATTRIBUTE_DF);
        }
    }
    return df;
}

double ocManagerBase::computeH(ocRelation *rel) // uncertainty
        {
    double h = rel->getAttribute(ATTRIBUTE_H);
    if (h < 0) { //-- not set yet
        ocTable *table = rel->getTable();
        if (table == NULL) {
            makeProjection(rel);
            table = rel->getTable();
        }
        h = ocEntropy(table);
        rel->setAttribute(ATTRIBUTE_H, h);
    }
    return h;
}

double ocManagerBase::computeH(ocModel *model, HMethod method, int SB) {
    double h;
    bool loops;

    if (method == ALGEBRAIC)
        loops = false;
    else if (method == IPF)
        loops = true;
    else
        loops = hasLoops(model);

    //-- for models with loops, compute fitted H value.  There may be
    //-- an H value as well, but this is ignored for models with loops.
    if (loops) {
        h = model->getAttribute(ATTRIBUTE_FIT_H);
        if (h < 0) {
            makeFitTable(model);
            h = ocEntropy(fitTable1);
            model->setAttribute(ATTRIBUTE_FIT_H, h);
            model->setAttribute(ATTRIBUTE_H, h);
        }
    } else {
        h = model->getAttribute(ATTRIBUTE_ALG_H);
        if (h < 0) { //-- not set yet
            calculateDfAndEntropy(model);
            h = model->getAttribute(ATTRIBUTE_ALG_H);
        }
        model->setAttribute(ATTRIBUTE_H, h);
    }
    return h;
}

double ocManagerBase::computeTransmission(ocModel *model, HMethod method, int SB) {
    //-- compute analytically. Krippendorf claims that you
    //-- can't do this for models with loops, but experimental
    //-- comparison indicates that loops don't matter in computing this.
    double t;

    t = model->getAttribute(ATTRIBUTE_ALG_T);
    if (t < 0) { //-- not set yet
        double h = 0;

        if (SB) {
            h = computeH(model, IPF, SB);
        } else {
            h = computeH(model);
        }
        t = h - inputH;
        model->setAttribute(ATTRIBUTE_ALG_T, t);
        model->setAttribute(ATTRIBUTE_T, t);
    }
    return t;
}

struct DFAndHProc: public ocIntersectProcessor {
        double df;
        double h;
        ocManagerBase *manager;
        DFAndHProc(ocManagerBase *mgr) {
            df = 0;
            h = 0;
            manager = mgr;
        }
        void process(bool sign, ocRelation *rel, int count) {
            if (rel) {
                df += (sign ? 1 : -1) * manager->computeDF(rel) * count;
                h += (sign ? 1 : -1) * manager->computeH(rel) * count;
            }
        }
};

void ocManagerBase::calculateDfAndEntropy(ocModel *model) {
    if ((model->getAttribute(ATTRIBUTE_DF) < 0) || (model->getAttribute(ATTRIBUTE_ALG_H) < 0)) {
        DFAndHProc processor(this);
        if (intersectArray != NULL) {
            delete[] intersectArray;
            intersectCount = 0;
            intersectMax = model->getRelationCount();
            ;
            intersectArray = NULL;
        }
        doIntersectionProcessing(model, &processor);
        model->setAttribute(ATTRIBUTE_DF, processor.df);
        model->setAttribute(ATTRIBUTE_ALG_H, processor.h);
    }
}

void ocManagerBase::doIntersectionProcessing(ocModel *model, ocIntersectProcessor *proc) {
    //-- allocate intersect storage; this grows later if needed
    if (intersectArray == NULL) {
        intersectMax = model->getRelationCount();
        intersectArray = new VarIntersect[intersectMax];
    }

    int count = model->getRelationCount();
    ocVariableList *varList = model->getRelation(0)->getVariableList();

    ocRelation *rel;
    int i, j, k;
    //-- go through the relations in the model and create VarIntersect entries
    for (i = 0; i < count; i++) {
        rel = model->getRelation(i);
        while (intersectCount >= intersectMax) {
            intersectArray = (VarIntersect*) growStorage(intersectArray, sizeof(VarIntersect)*intersectMax, 2);
            intersectMax *= 2;
        }
        VarIntersect *intersect = intersectArray + (intersectCount++);
        intersect->rel = rel;
        intersect->startIndex = i;
        intersect->sign = true;
        intersect->count = 1;
        proc->process(intersect->sign, intersect->rel, intersect->count);
    }
    int level0end = intersectCount;
    bool sign = true;
    bool match;

    //-- given the previous level of intersection terms, construct the next level from
    //-- all intersections among the previous level. When an intersection is found, we
    //-- need to check the new intersections. If there is a match, we update its
    //-- include count; if there is no match, we create a new one. This process
    //-- terminates when no new terms have been added.
    VarIntersect *ip, *jp, *newp;
    VarIntersect *currentArray, *nextArray;
    int currentCount, nextCount;
    long nextMax;
    int *newvars, newcount;
    currentArray = intersectArray;
    currentCount = intersectCount;
    while (currentCount > 0) {
        sign = !sign;
        nextArray = new VarIntersect[intersectMax];
        nextCount = 0;
        nextMax = intersectMax;
        for (i = 0; i < currentCount; i++) {
            for (j = currentArray[i].startIndex + 1; j < level0end; j++) {
                ip = currentArray + i;
                jp = intersectArray + j;
                if (intersect(ip->rel, jp->rel, newvars, newcount)) {
                    rel = getRelation(newvars, newcount, true);
                    proc->process(sign, rel, ip->count);
                    // only add the relation to the intersect array if it has any potential for overlap.
                    // (when j==(level0end-1), that relation can be part of no further overlaps)
                    if (j < (level0end - 1)) {
                        match = false;
                        for (k = 0; k < nextCount; k++) {
                            if ((nextArray[k].rel == rel) && (nextArray[k].startIndex == j)) {
                                match = true;
                                nextArray[k].count += ip->count;
                                break;
                            }
                        }
                        if (!match) {
                            while (nextCount >= nextMax) {
                                nextArray = (VarIntersect*) growStorage(nextArray, sizeof(VarIntersect)*nextMax, 2);
                                nextMax *= 2;
                            }
                            newp = nextArray + (nextCount++);
                            newp->rel = rel;
                            newp->startIndex = j;
                            newp->sign = sign;
                            newp->count = ip->count;
                        }
                    }
                    delete[] newvars;
                }
            }
        }
        if (currentArray != intersectArray) {
            delete[] currentArray;
        }
        currentArray = nextArray;
        nextArray = NULL;
        currentCount = nextCount;
    }
    if (currentArray != intersectArray) {
        delete[] currentArray;
    }
}

// !!! This function computes dependent stats whether or not this is a directed system. !!!
// Perhaps this should be fixed. [jsf]
void ocManagerBase::computeStatistics(ocRelation *rel) {
    int varcount;
    int maxVars = rel->getVariableCount();
    int *varindices = new int[maxVars];
    int tupleCount = inputData->getTupleCount();

    //-- Get a pointer to the independent-only relation
    varcount = rel->getIndependentVariables(varindices, maxVars);
    ocRelation *indRel = getRelation(varindices, varcount, true);

    //-- now the dependent-only
    varcount = rel->getDependentVariables(varindices, maxVars);
    ocRelation *depRel = getRelation(varindices, varcount, true);
    //-- get the various uncertainties and compute basic combinations
    double h = computeH(rel);
    double hDep = computeH(depRel);
    double hInd = computeH(indRel);
    double hCond = h - hInd;
    rel->setAttribute(ATTRIBUTE_COND_H, hCond);
    rel->setAttribute(ATTRIBUTE_COND_DH, hDep != 0.0 ? (hDep - h) / hDep : 0.0);
    rel->setAttribute(ATTRIBUTE_COND_PCT_DH, hInd != 0.0 ? 100 * (hDep - h) / hInd : 0.0);
    rel->setAttribute(ATTRIBUTE_IND_H, hInd);
    rel->setAttribute(ATTRIBUTE_DEP_H, hDep);

    //-- get the NC (cartesian product) measures
    //double hc = (double)rel->getNC();
    long long depNC = depRel->getNC();
    long long indNC = indRel->getNC();

    //-- get the df measures.
    long long df = (depNC - 1) * indNC;
    long long ddf = depNC * indNC - (depNC + indNC) - 1;
    double totalLR = ocLR(tupleCount, depNC * indNC, h);
    double indLR = ocLR(tupleCount, indNC, hInd);
    double condLR = totalLR - indLR;
    rel->setAttribute(ATTRIBUTE_COND_DF, df);
    rel->setAttribute(ATTRIBUTE_COND_DDF, ddf);
    rel->setAttribute(ATTRIBUTE_TOTAL_LR, totalLR);
    rel->setAttribute(ATTRIBUTE_IND_LR, indLR);
    rel->setAttribute(ATTRIBUTE_COND_LR, condLR);

    double l2 = 2.0 * M_LN2 * tupleCount * (hDep - hCond);
    double hCondProb = chic(condLR, df);
    rel->setAttribute(ATTRIBUTE_COND_H_PROB, hCondProb);
    delete[] varindices;
}

void ocManagerBase::computeRelWidth(ocModel *model) {
    //-- relation widths are the min and max number of variables among the relations
    //-- in the model. For directed systems the all-independent relation is not included
    //-- in this. These values are used primarily for filtering and sorting models
    if (model->getAttribute(ATTRIBUTE_MAX_REL_WIDTH) > 0)
        return; // already did this
    long minwidth = 0, maxwidth = 0;
    bool directed = getVariableList()->isDirected();
    long i, relCount = model->getRelationCount();
    for (i = 0; i < relCount; i++) {
        ocRelation *rel = model->getRelation(i);
        if (directed && rel->isIndependentOnly())
            continue; // skip all-ind relation
        int width = rel->getVariableCount();
        if (maxwidth == 0) { // first time
            minwidth = maxwidth = width;
        } else {
            minwidth = minwidth < width ? minwidth : width;
            maxwidth = maxwidth > width ? maxwidth : width;
        }
    }
    model->setAttribute(ATTRIBUTE_MIN_REL_WIDTH, (double) minwidth);
    model->setAttribute(ATTRIBUTE_MAX_REL_WIDTH, (double) maxwidth);
}

double ocManagerBase::computeLR(ocModel *model) {
    double lr = model->getAttribute(ATTRIBUTE_LR);
    if (lr < 0) {
        lr = fabs(2.0 * M_LN2 * sampleSize * (computeTransmission(model) - computeTransmission(refModel)));
        model->setAttribute(ATTRIBUTE_LR, lr);
    }
    return lr;
}

double ocManagerBase::computeDDF(ocModel *model) {
    // This is not an accurate method of computing DDF, in many cases.
    // The VB & SB managers do a better job of it.
    double ddf = model->getAttribute(ATTRIBUTE_DDF);
    if (ddf >= 0)
        return ddf;
    if (model == refModel) {
        model->setAttribute(ATTRIBUTE_DDF, 0);
        return 0;
    }
    model->setAttribute(ATTRIBUTE_DDF, ddf);
    return ddf;
}

void ocManagerBase::computeIncrementalAlpha(ocModel *model) {
    if (model == NULL)
        return;
    double incr_alpha = model->getAttribute(ATTRIBUTE_INCR_ALPHA);
    if (incr_alpha < 0) {
        double refL2 = computeLR(model);
        double refDDF = computeDDF(model);
        double prog_id;
        double ia_reachable; // To test if all steps to a model have had incr_alpha < 0.05
        ocModel *progen = model->getProgenitor();
        if (progen == NULL) {
            prog_id = 0;
            incr_alpha = 0;
            ia_reachable = 1;
        } else {
            prog_id = (double) progen->getID();
            double prog_ddf = computeDDF(progen);
            double prog_lr = computeLR(progen);
            incr_alpha = csa(fabs(prog_lr - refL2), fabs(prog_ddf - refDDF));
            if ((incr_alpha < 0.05) && (progen->getAttribute(ATTRIBUTE_INCR_ALPHA_REACHABLE) == 1)) {
                ia_reachable = 1;
            } else {
                ia_reachable = 0;
            }
        }
        model->setAttribute(ATTRIBUTE_INCR_ALPHA, incr_alpha);
        model->setAttribute(ATTRIBUTE_PROG_ID, prog_id);
        model->setAttribute(ATTRIBUTE_INCR_ALPHA_REACHABLE, ia_reachable);
    }
}

void ocManagerBase::compareProgenitors(ocModel *model, ocModel *newProgen) {
    if ((model == NULL) || (newProgen == NULL))
        return;
    ocModel *oldProgen = model->getProgenitor();
    if (oldProgen == NULL) {
        model->setProgenitor(newProgen);
        return;
    }
    // compute and save old IA, then new IA
    computeIncrementalAlpha(model);
    double old_IA = model->getAttribute(ATTRIBUTE_INCR_ALPHA);
    double old_IA_reach = model->getAttribute(ATTRIBUTE_INCR_ALPHA_REACHABLE);

    model->setProgenitor(newProgen);
    model->setAttribute(ATTRIBUTE_INCR_ALPHA, -1);
    model->setAttribute(ATTRIBUTE_PROG_ID, -1);
    model->setAttribute(ATTRIBUTE_INCR_ALPHA_REACHABLE, -1);
    computeIncrementalAlpha(model);
    double new_IA = model->getAttribute(ATTRIBUTE_INCR_ALPHA);
    double new_IA_reach = model->getAttribute(ATTRIBUTE_INCR_ALPHA_REACHABLE);

    // The new progen is now in place. If it's better than (or good as) the old, keep it and return.
    // Otherwise, put the old one back.
    // searchDirection: 0=up, 1=down.  When searching up, prefer small incr.alpha;  when down, large.
    // Also, when searching up, we first prefer models that are reachable, i.e., every step has IA <= 0.05.
    // If the reference is the top (or is a custom start model above these ones), then prefer large alpha.
    if ((refModel == topRef) || ((refModel != bottomRef) && (searchDirection == 1))) {
        if (old_IA <= new_IA)
            return;
    } else {
        if ((old_IA >= new_IA) && (old_IA_reach == new_IA_reach))
            return;
        if ((old_IA_reach != 1) && (new_IA_reach == 1))
            return;
    }
    model->setProgenitor(oldProgen);
    model->setAttribute(ATTRIBUTE_INCR_ALPHA, -1);
    model->setAttribute(ATTRIBUTE_PROG_ID, -1);
    model->setAttribute(ATTRIBUTE_INCR_ALPHA_REACHABLE, -1);
    computeIncrementalAlpha(model);
}

void ocManagerBase::setValuesAreFunctions(int flag) {
    if (flag == 0)
        valuesAreFunctions = false;
    else {
        valuesAreFunctions = true;
        ocOptionDef *optDef = options->findOptionByName("function-values");
        if (optDef)
            setOptionString(optDef, "Y");
    }
}

ocModel *ocManagerBase::makeModel(const char *name, bool makeProject) {
    const char *cp = name, *cp2, *cp3;
    // Count how many relations are in the name, for initializing the ocModel object.
    int relCount = 0;
    while (cp != NULL) {
        cp = strchr(cp, ':');
        relCount++;
        if (cp != NULL)
            cp++;
    }
    cp = name;
    ocModel *model = new ocModel(relCount);
    char *relname = new char[(1 + varList->getMaxAbbrevLen()) * varList->getVarCount()];
    int varcount, notCount;
    int *vars = new int[varList->getVarCount()];
    bool atStart = true;
    int i, j;
    bool varFound;
    ocRelation *rel;
    while (cp) {
        cp2 = strchr(cp, ':');
        if (cp2 != NULL) {
            int len = cp2 - cp;
            strncpy(relname, cp, len);
            relname[len] = '\0';
            cp = cp2 + 1;
        } else {
            strcpy(relname, cp);
            cp = NULL;
        }
        // if relname is "IV", is at the start of the string, and this is directed
        // replace "IV" with the abbrevs of all the IVs
        if (varList->isDirected() && (atStart == true) && (strcmp(relname, "IV") == 0)) {
            rel = getChildRelation(getTopRefModel()->getRelation(0), varList->getDV());
        // if relname is "IVI" at the start of a neutral model, add all single-variable relations
        } else if (!varList->isDirected() && (atStart == true) && (strcmp(relname, "IVI") == 0)) {
            for (i=0; i < varList->getVarCount(); i++) {
                vars[0] = i;
                rel = getRelation(vars, 1, makeProject);
                model->addRelation(rel, true);
            }
            atStart = false;
            continue;
        } else if (strchr(relname, '[') != NULL) {
            cp2 = strchr(relname, '[');
            cp2++;
            cp3 = strchr(cp2, ']');
            if (cp3 == NULL) {
                delete model;
                delete relname;
                delete vars;
                return NULL; // error in name
            }
            relname[cp3 - relname] = '\0';
            int *notVars = new int[varList->getVarCount()];
            notCount = varList->getVariableList(cp2, notVars);
            varcount = 0;
            // Now add in every variable in the full varList that is not in the notVars list.
            for (i = 0; i < varList->getVarCount(); i++) {
                varFound = false;
                for (j = 0; j < notCount; j++) {
                    if (notVars[j] == i) {
                        varFound = true;
                        break;
                    }
                }
                if (!varFound) {
                    vars[varcount] = i;
                    varcount++;
                }
            }
            delete notVars;
            if (varcount == 0) {
                delete model;
                delete relname;
                delete vars;
                return NULL; // error in name
            }
            rel = getRelation(vars, varcount, makeProject);
        } else {
            varcount = varList->getVariableList(relname, vars);
            if (varcount == 0) {
                delete model;
                delete relname;
                delete vars;
                return NULL; // error in name
            }
            rel = getRelation(vars, varcount, makeProject);
        }
        if (rel == NULL) {
            delete model;
            delete relname;
            delete vars;
            return NULL; // error in name
        }
        model->addRelation(rel, true);
        atStart = false;
    }
    delete[] vars;
    delete[] relname;

    //-- put it in the cache; return the cached one if present
    if (!modelCache->addModel(model)) {
        //-- already exists in cache; return that one
        ocModel *cachedModel = modelCache->findModel(model->getPrintName());
        delete model;
        model = cachedModel;
    }
    return model;
}

#define MAXSTATENAME 10
ocModel *ocManagerBase::makeSbModel(const char *name, bool makeProject) {
    const char *cp = name, *cp2;
    // Count how many relations are in the name, for initializing the ocModel object.
    int relCount = 0;
    while (cp != NULL) {
        cp = strchr(cp, ':');
        relCount++;
        if (cp != NULL)
            cp++;
    }
    cp = name;
    ocModel *model = new ocModel(relCount);
    // This estimate for maximum relation name length is questionable [jsf]
    char *relName = new char[(1 + varList->getMaxAbbrevLen()) * varList->getVarCount() * 2 * MAXSTATENAME];
    int varCount;
    int *vars = new int[varList->getVarCount()];
    int *states = new int[varList->getVarCount()];
    bool atStart = true;
    ocRelation *rel;
    while (cp) {
        cp2 = strchr(cp, ':');
        if (cp2 != NULL) {
            int len = cp2 - cp;
            strncpy(relName, cp, len);
            relName[len] = '\0';
            cp = cp2 + 1;
        } else {
            strcpy(relName, cp);
            cp = NULL;
        }
        // if relname is "IV", is at the start of the string, and this is directed,
        // replace "IV" with the abbreviations of all the IVs
        if (varList->isDirected() && (atStart == true) && (strcmp(relName, "IV") == 0)) {
            const char *indName = getIndRelation()->getPrintName();
            varCount = varList->getVarStateList(indName, vars, states);
            if (varCount == 0) {
                delete model, relName, vars;
                return NULL; // error in name
            }
            rel = getRelation(vars, varCount, makeProject, states);
        } else {
            varCount = varList->getVarStateList(relName, vars, states);
            if (varCount == 0) {
                delete model, relName, vars;
                return NULL; // error in name
            }
            rel = getRelation(vars, varCount, makeProject, states);
        }
        if (rel == NULL) {
            delete model, relName, vars;
            return NULL; // error in name
        }
        model->addRelation(rel, true, getModelCache());
        atStart = false;
    }
    model->completeSbModel();

    //-- put it in the cache; return the cached one if present
    if (!modelCache->addModel(model)) {
        //-- already exists in cache; return that one
        ocModel *cachedModel = modelCache->findModel(model->getPrintName());
        delete model;
        model = cachedModel;
    }
    delete[] vars;
    delete[] states;
    delete[] relName;
    return model;
}

void ocManagerBase::printOptions(bool printHTML, bool skipNominal) {
    options->write(NULL, printHTML, skipNominal);
    if (printHTML) {
        printf("<tr><td>Data Lines Read</td><td>%d</td></tr>\n", dataLines);
    } else {
        printf("Data Lines Read\t%d\n", dataLines);
    }
}

void ocManagerBase::printSizes() {
    long size;
    size = relCache->size();
    printf("Rel-cache: %ld; ", size);
    size = modelCache->size();
    printf("Model cache: %ld; ", size);
    //	relCache->dump();
    modelCache->dump();
}

void ocManagerBase::dumpRelations() {
    relCache->dump();
}

