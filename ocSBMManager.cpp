/* Copyright 2000, Portland State University Systems Science Program.  All Rights Reserved
 */

#include "ocCore.h"
#include "ocMath.h"
#include "ocSBMManager.h"
#include "ocModelCache.h"
#include "ocSearchBase.h"
#include "ocReport.h"
#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
//#include "ocWin32.h"

ocSBMManager::ocSBMManager(ocVariableList *vars, ocTable *input) :
        ocManagerBase(vars, input) {
    topRef = bottomRef = refModel = NULL;
    projection = true;
    filterAttr = NULL;
    filterOp = EQUALS;
    filterValue = 0.0;
    sortAttr = NULL;
    search = NULL;
    sortDirection = 0;
}

ocSBMManager::ocSBMManager() :
        ocManagerBase() {
    topRef = bottomRef = refModel = NULL;
    projection = true;
    filterAttr = NULL;
    filterOp = EQUALS;
    filterValue = 0.0;
    sortAttr = NULL;
    search = NULL;
    sortDirection = 0;
}

ocSBMManager::~ocSBMManager() {
    if (filterAttr)
        delete filterAttr;
    if (sortAttr)
        delete sortAttr;
    if (search)
        delete search;
}

bool ocSBMManager::initFromCommandLine(int argc, char **argv) {
    if (!ocManagerBase::initFromCommandLine(argc, argv))
        return false;
    // Check that variable & state names are appropriate for state-based
    verifyStateBasedNaming();
    if (varList) {
        int var_count = varList->getVarCount();
        int* var_indices = new int[var_count];
        int* state_indices = new int[var_count];
        for (int i = 0; i < var_count; i++) {
            var_indices[i] = i;
            state_indices[i] = DONT_CARE;
        }
        ocRelation *top = getRelation(var_indices, var_count, false, state_indices);
        top->setTable(inputData);
        makeReferenceModels(top);
        delete[] var_indices;
        delete[] state_indices;
    }
    return true;
}

// Verifies that variable abbreviations are letters-only, and that state names are numbers-only.
// It finds & prints all errors before exiting.
void ocSBMManager::verifyStateBasedNaming() {
    bool errorFound = false;
    char temp[MAXLINE];
    int test = 0;
    if (varList) {
        int var_count = varList->getVarCount();
        for (int i=0; i < var_count; i++) {
            test = sscanf(varList->getVariable(i)->abbrev, "%[A-Za-z]", temp);
            if ((test != 1) || (strcmp(temp, varList->getVariable(i)->abbrev) != 0)) {
                printf("Error: Invalid state-based variable abbreviation: \"%s\". Abbreviations must use only letters.\n", varList->getVariable(i)->abbrev);
                errorFound = true;
            }
            for (int j=0; j < varList->getVariable(i)->cardinality; j++) {
                test = sscanf(varList->getVariable(i)->valmap[j], "%[0-9.]", temp);
                if ((test != 1) || (strcmp(temp, varList->getVariable(i)->valmap[j]) != 0)) {
                    printf("Error: Invalid state-based state value: \"%s\" Values must use only numbers.\n", varList->getVariable(i)->valmap[j]);
                    errorFound = true;
                }
            }
        }
    }
    if (errorFound)
        exit(1);
}

void ocSBMManager::makeReferenceModels(ocRelation *top) {
    ocModel *model = new ocModel(1);
    model->addRelation(top, false);
    model->completeSbModel();
    topRef = model;
    //-- Generate bottom reference model. If system is neutral.
    //-- this has a relation per variable. Otherwise it has a
    //-- relation per dependent variable, and one containing all
    //-- the independent variables.
    int varCount = varList->getVarCount();
    int* varindices = new int[varCount];
    int* state_indices = new int[varCount];
    ocRelation *rel;
    int i;
    if (varList->isDirected()) {
        //-- first, make a relation with all the independent variables
        model = new ocModel(2); // typical case: one dep variable
        int pos = 0;
        ocVariable *var;
        for (i = 0; i < varCount; i++) {
            var = varList->getVariable(i);
            if (!var->dv) {
                varindices[pos] = i;
                state_indices[pos] = DONT_CARE;
                pos++;
            }
        }
        rel = getRelation(varindices, pos, true, state_indices);
        model->addRelation(rel, true, getModelCache());
        //-- now add a unary relation for each dependent variable
        for (i = 0; i < varCount; i++) {
            var = varList->getVariable(i);
            if (var->dv) {
                varindices[0] = i;
                rel = getRelation(varindices, 1, true, state_indices);
                model->addRelation(rel, true, getModelCache());
            }
        }
        model->completeSbModel();
    } else {
        //this needs to change since in SB the bottom reference is uniform model and
        //not independence model
        model = new ocModel(varCount);
        int *state = new int[1];
        state[0] = DONT_CARE;
        for (i = 0; i < varCount; i++) {
            varindices[0] = i;
            rel = getRelation(varindices, 1, true, state);
            model->addRelation(rel, true, getModelCache());
            /*
             int inputCells = 1;
             int varcount = varList->getVarCount();
             for (i = 0; i < varcount; i++) {
             inputCells *= varList->getVariable(i)->cardinality;
             }
             double cellWeight = 1.0 / inputCells;
             int *varvalues = new int[varcount];

             for (i = 0; i < varcount; i++) {
             varvalues[i] = 0;
             }
             ocKeySegment *key = new ocKeySegment[keysize];
             long cellCount = 0;
             for(;;) {
             ocKey::buildFullKey(key, keysize, varList, varvalues);
             fitTable1->addTuple(key, cellWeight);
             cellCount++;
             if (!nextTuple(varList, varvalues)) break;
             }
             delete [] varvalues;

             */
        }
        delete[] state;
        model->completeSbModel();
    }
    bottomRef = model;
    if (!modelCache->addModel(bottomRef)) {
        ocModel *cached_model = modelCache->findModel(bottomRef->getPrintName());
        delete bottomRef;
        bottomRef = cached_model;
    }
    modelCache->addModel(topRef);
    computeDF(topRef);
    computeH(topRef);
    computeDF(bottomRef);
    computeH(bottomRef);
    //-- compute relation statistics for the top relation
    computeStatistics(topRef->getRelation(0));

    //-- set default reference model depending on whether
    //-- the system is directed or neutral
    refModel = varList->isDirected() ? bottomRef : bottomRef;
    delete[] state_indices;
    delete[] varindices;
}

ocModel *ocSBMManager::setRefModel(const char *name) {
    if (strcasecmp(name, "top") == 0) {
        refModel = topRef;
    } else if (strcasecmp(name, "bottom") == 0) {
        refModel = bottomRef;
    } else {
        refModel = makeSbModel(name, true);
    }
    return refModel;
}

double ocSBMManager::computeExplainedInformation(ocModel *model) {
    double info = model->getAttribute(ATTRIBUTE_EXPLAINED_I);
    if (info >= 0)
        return info;
    double topH = topRef->getAttribute(ATTRIBUTE_H);
    double botH = bottomRef->getAttribute(ATTRIBUTE_H);
    double modelT = computeTransmission(model, IPF);
    info = (botH - topH - modelT) / (botH - topH);
    // info is normalized but may not quite be between zero and 1 due to roundoff. Fix this here.
    if (info <= 0.0)
        info = 0.0;
    if (info >= 1.0)
        info = 1.0;
    model->setAttribute(ATTRIBUTE_EXPLAINED_I, info);
    return info;
}

double ocSBMManager::computeUnexplainedInformation(ocModel *model) {
    double topH = topRef->getAttribute(ATTRIBUTE_H);
    double botH = bottomRef->getAttribute(ATTRIBUTE_H);
    double modelT = computeTransmission(model, IPF);
    double info = modelT / (botH - topH);
    // info is normalized but may not quite be between zero and 1 due to roundoff. Fix this here.
    if (info <= 0.0)
        info = 0.0;
    if (info >= 1.0)
        info = 1.0;
    model->setAttribute(ATTRIBUTE_UNEXPLAINED_I, info);
    return info;
}

double ocSBMManager::computeDDF(ocModel *model) {
    double ddf = model->getAttribute(ATTRIBUTE_DDF);
    if (ddf >= 0)
        return ddf;
    if (model == refModel) {
        model->setAttribute(ATTRIBUTE_DDF, 0);
        return 0;
    }

    double refDF = computeDF(refModel);
    double modelDF = computeDF(model);
    double df = refDF - modelDF;
    //-- for bottom reference the sign will be wrong
    df = fabs(df);
    model->setAttribute(ATTRIBUTE_DDF, df);
    return df;
}

void ocSBMManager::setSearch(const char *name) {
    if (search) {
        delete search;
        search = NULL;
    }
    search = ocSearchFactory::getSearchMethod(this, name, makeProjection());
}

void ocSBMManager::computeDFStatistics(ocModel *model) {
    computeDfSb(model);
    computeDDF(model);
}

void ocSBMManager::computeInformationStatistics(ocModel *model) {
    if (model == topRef || model == bottomRef) {
        computeH(model, ALGEBRAIC, 1);
        computeTransmission(model, ALGEBRAIC, 1);
    } else {
        computeH(model, IPF, 1);
        computeTransmission(model, IPF, 1);
    }
    computeExplainedInformation(model);
    computeUnexplainedInformation(model);
}

void ocSBMManager::computeL2Statistics(ocModel *model) {
    //-- make sure we have the fitted table (needed for some statistics)
    //-- this will return immediately if the table was already created.
    //-- make sure the other attributes are there
    computeDFStatistics(model);
    computeInformationStatistics(model);
    //-- compute chi-squared statistics and related statistics. L2 = 2*n*sum(p(ln p/q))
    //-- which is 2*n*ln(2)*T
    int errcode;
    double modelT = computeTransmission(model, IPF);
    double modelL2 = 2.0 * M_LN2 * sampleSize * modelT;
    double refT = computeTransmission(refModel);
    double refL2 = 2.0 * M_LN2 * sampleSize * refT;
    double refModelL2 = refL2 - modelL2;
    double modelDF = computeDfSb(model);
    double refDF = computeDF(refModel);
    double refDDF = modelDF - refDF;

    //-- depending on the relative position of the reference model and the
    //-- current model in the hierarchy, refDDF may be positive or negative
    //-- as may refModel2. But the signs should be the same. If they aren't,
    //-- the csa computation will fail.
    if (refDDF < 0) {
        refDDF = -refDDF;
        refModelL2 = -refModelL2;
    }

    //-- eliminate negative value due to small roundoff
    if (refModelL2 <= 0.0)
        refModelL2 = 0.0;

    double refL2Prob = csa(refModelL2, refDDF);

    double critX2 = 0, refL2Power = 0;

    errcode = 0;
    double alpha;
    if (!getOptionFloat("alpha", NULL, &alpha))
        alpha = 0.0;
    if (alpha > 0)
        critX2 = ppchi(alpha, refDDF, &errcode);
    else
        critX2 = refModelL2;
    if (errcode)
        printf("ppchi: errcode=%d\n", errcode);
    refL2Power = 1.0 - chin2(critX2, refDDF, refModelL2, &errcode);

    //?? do something with these returned errors
    model->setAttribute(ATTRIBUTE_DDF, refDDF);
    model->setAttribute(ATTRIBUTE_LR, refModelL2);
    model->setAttribute(ATTRIBUTE_ALPHA, refL2Prob);
    model->setAttribute(ATTRIBUTE_BETA, refL2Power);

    double dAIC = refModelL2 - 2.0 * computeDDF(model);
    double dBIC = refModelL2 - log(sampleSize) * computeDDF(model);

    // If the top model is the reference, or if there is a custom start model and we're searching down,
    // we flip the signs of dAIC and dBIC.  (A custom start occurs when ref is neither top nor bottom.)
    // (That is, flip signs in cases when the reference is above the model in the lattice.)
    if ((refModel == topRef) || ((refModel != bottomRef) && (searchDirection == 1))) {
        dAIC = -dAIC;
        dBIC = -dBIC;
    }
    model->setAttribute(ATTRIBUTE_AIC, dAIC);
    model->setAttribute(ATTRIBUTE_BIC, dBIC);

}

void ocSBMManager::computePearsonStatistics(ocModel *model) {
    //-- these statistics require a full contingency table, so make
    //-- sure one has been created.
    if (model == NULL || bottomRef == NULL)
        return;
    makeFitTable(model);

    ocTable *modelFitTable = new ocTable(keysize, fitTable1->getTupleCount());

    modelFitTable->copy(fitTable1);
    makeFitTable(bottomRef);
    double modelP2 = ocPearsonChiSquared(inputData, modelFitTable, (long) round(sampleSize));
    double refP2 = ocPearsonChiSquared(inputData, fitTable1, (long) round(sampleSize));

    int errcode;
    double modelDF = computeDfSb(model);
    double refDF = computeDF(refModel);
    double refDDF = fabs(modelDF - refDF);
    double refModelP2 = refP2 - modelP2;
    double refP2Prob = csa(refModelP2, refDDF);

    double critX2, refP2Power;
    errcode = 0;
    double alpha;

    if (!getOptionFloat("alpha", NULL, &alpha))
        alpha = 0.0;
    if (alpha > 0)
        critX2 = ppchi(alpha, refDDF, &errcode);
    else
        critX2 = modelP2;
    if (errcode)
        printf("ppchi: errcode=%d\n", errcode);
    refP2Power = 1.0 - chin2(critX2, refDDF, modelP2, &errcode);
    if (errcode)
        printf("chin2: errcode=%d, %.2f, %.2f\n", errcode, refDDF, modelP2);
    //?? do something with these returned errors

    model->setAttribute(ATTRIBUTE_P2, modelP2);
    model->setAttribute(ATTRIBUTE_P2_ALPHA, refP2Prob);
    model->setAttribute(ATTRIBUTE_P2_BETA, refP2Power);
    delete modelFitTable;
}

void ocSBMManager::computeDependentStatistics(ocModel *model) {
    //-- the basic metric is the conditional uncertainty u(Z|ABC...), which is
    //-- u(model) - u(ABC...), where ABC... are the independent variables
    //-- first, compute the relation stats for the bottom reference model, which
    //-- will give us the u(ABC...).
    if (!getVariableList()->isDirected())
        return; // can only do this for directed models
    double depH = topRef->getRelation(0)->getAttribute(ATTRIBUTE_DEP_H);
    ocRelation *indRel;
    int i;
    for (i = 0; i < bottomRef->getRelationCount(); i++) {
        indRel = bottomRef->getRelation(i);
        if (indRel->isIndependentOnly())
            break; // this is the one.
    }
    double indH = indRel->getAttribute(ATTRIBUTE_H);
    double refH = computeH(bottomRef);
    double refCondH = refH - indH;

    //printf("compute H in SB computeDependStat\n");
    double h = computeH(model, IPF);
    double condH = h - indH;
    model->setAttribute(ATTRIBUTE_COND_H, condH);
    model->setAttribute(ATTRIBUTE_COND_DH, refH - h);
    model->setAttribute(ATTRIBUTE_COND_PCT_DH, 100 * (refH - h) / depH);
}

void ocSBMManager::computeBPStatistics(ocModel *model) {
    // this function computes transmission using the Fourier BP method.
    // Individual q values are computed as the mean value from each projection,
    // q(x) = sum (R(x)/|R|) - (nR - 1), where R(x) is the projected value
    // which contains state x in relation R; |R| is the number of states collapsed
    // into each state of relation R; and nR is the number of relations in the model.
    //
    // Since the transmission terms are p(x) log (p(x)/q(x)), these computations
    // are only done for nonzero p and q values.
    // Subtracting for overlaps may leave the result un-normalized because of
    // null overlaps (for example, AB:CD has no overlaps, but p(AB)+p(CD) = 2, not 1)
    // The count of origin terms which much still be deducted for normalization
    // is maintained, and the q values corrected at the end.

    class BPIntersectProcessor: public ocIntersectProcessor {
        public:
            BPIntersectProcessor(ocTable *inData, int rels, long fullDim) {
                inputData = inData;
                keysize = inputData->getKeySize();
                qData = new ocTable(keysize, inputData->getTupleCount());
                //-- seed the computed table with the tuples from the input data,
                //-- but with zero values. These are the only tuples we care about.
                for (int i = 0; i < inputData->getTupleCount(); i++) {
                    ocKeySegment *key = inputData->getKey(i);
                    qData->addTuple(key, 0);
                }

                //-- keep track of the total probability so we can deduct
                //-- the appropriate number of origin terms.
                originTerms = 0;

                relCount = rels;

                fullDimension = fullDim;
            }

            void process(bool sign, ocRelation *rel, int count) {
                for (int counter = 0; counter < count; counter++) {
                    ocKeySegment *key = new ocKeySegment[keysize];
                    double qi, q;
                    //-- get the orthogonal dimension of the relation (the number of states
                    //-- projected into one substate)
                    long relDimension = fullDimension / ((long) ocDegreesOfFreedom(rel) + 1);
                    //-- add the scaled contribution to each q
                    for (int i = 0; i < qData->getTupleCount(); i++) {
                        qData->copyKey(i, key);
                        q = qData->getValue(i);
                        ocKeySegment *mask = rel->getMask();
                        for (int k = 0; k < keysize; k++)
                            key[k] |= mask[k];
                        int j = rel->getTable()->indexOf(key);
                        if (j >= 0) {
                            qi = (sign ? 1 : -1) * (rel->getTable()->getValue(j) / relDimension);
                            qData->setValue(i, qi + q);
                        }
                    }
                    originTerms += (sign ? 1 : -1);
                }
            }

            double getTransmission() {
                correctOriginTerms();

                double t, p, q;
                t = 0;
                for (long i = 0; i < inputData->getTupleCount(); i++) {
                    long j = qData->indexOf(inputData->getKey(i));
                    p = inputData->getValue(i);
                    q = qData->getValue(j);
                    if (p > 0 && q > 0)
                        t += p * log(p / q);
                }
                t /= log(2.0);
                return t;
            }

            void correctOriginTerms() {
                double q;
                double originTerm = ((double) (originTerms - 1)) / fullDimension;
                for (long i = 0; i < qData->getTupleCount(); i++) {
                    q = qData->getValue(i);
                    q -= originTerm;
                    qData->setValue(i, q);
                }
            }

            ocTable *qData, *inputData;
            long fullDimension;
            int keysize;
            int relCount;
            int originTerms;
    };

    long fullDimension = (long) ocDegreesOfFreedom(topRef->getRelation(0)) + 1;

    BPIntersectProcessor processor(inputData, model->getRelationCount(), fullDimension);
    if (intersectArray != NULL) {
        delete[] intersectArray;
        intersectCount = 0;
        intersectMax = model->getRelationCount();
        ;
        intersectArray = NULL;
    }

    doIntersectionProcessing(model, &processor);
    double t = processor.getTransmission();
    model->setAttribute(ATTRIBUTE_BP_T, t);
}

void ocSBMManager::computePercentCorrect(ocModel *model) {
    double total;
    long long count, i;
    ocRelation *indRel = getIndRelation();
    ocRelation *depRel = getDepRelation();
    //-- if either of these is empty, then we don't have a directed system
    if (indRel == 0 || depRel == 0)
        return;
    ((ocManagerBase*) this)->makeProjection(depRel);
    if (!makeFitTable(model))
        printf("ERROR\n");
    ocTable *modelTable = fitTable1;
    ocTable *maxTable = new ocTable(modelTable->getKeySize(), modelTable->getTupleCount());

    int maxCount = varList->getVarCount();
    int varindices[maxCount], varcount;
    int stateindices[maxCount];
    getPredictingVars(model, varindices, varcount, false);
    for (int i = 0; i < varcount; i++)
        stateindices[i] = DONT_CARE;
    ocRelation *predRelNoDV = getRelation(varindices, varcount, false, stateindices);
    getPredictingVars(model, varindices, varcount, true);
    for (int i = 0; i < varcount; i++)
        stateindices[i] = DONT_CARE;
    ocRelation *predRelWithDV = getRelation(varindices, varcount, false, stateindices);
    ocTable *predModelTable = new ocTable(keysize, modelTable->getTupleCount());

    ocTable *predInputTable = new ocTable(keysize, modelTable->getTupleCount());
    ocManagerBase::makeProjection(modelTable, predModelTable, predRelWithDV);
    ocManagerBase::makeProjection(inputData, predInputTable, predRelWithDV);

    ocTable *inputsOnly = new ocTable(keysize, modelTable->getTupleCount());
    ocManagerBase::makeProjection(inputData, inputsOnly, predRelNoDV);
    model->setAttribute(ATTRIBUTE_PCT_COVERAGE,
            (double) inputsOnly->getTupleCount() / (double) predRelNoDV->getNC() * 100.0);
    delete inputsOnly;

    // "missedValues" is passed as NULL, to signify that this is inputData.  In this case,
    // there is no need to check for missed values, so that step can be skipped.
    makeMaxProjection(predModelTable, maxTable, predInputTable, predRelNoDV, depRel, NULL);

    total = 0.0;
    count = maxTable->getTupleCount();
    for (i = 0; i < count; i++) {
        total += maxTable->getValue(i);
    }
    model->setAttribute(ATTRIBUTE_PCT_CORRECT_DATA, 100 * total);

    if (testData) {
        //-- for test data, use projections involving only the predicting variables
        ocTable *predTestTable = new ocTable(keysize, testData->getTupleCount());
        ocManagerBase::makeProjection(testData, predTestTable, predRelWithDV);
        maxTable->reset(keysize);
        double missedTest = 0;
        makeMaxProjection(predModelTable, maxTable, predTestTable, predRelNoDV, depRel, &missedTest);
        total = 0.0;
        count = maxTable->getTupleCount();
        for (i = 0; i < count; i++) {
            total += maxTable->getValue(i);
        }
        model->setAttribute(ATTRIBUTE_PCT_CORRECT_TEST, 100 * total);
        model->setAttribute(ATTRIBUTE_PCT_MISSED_TEST, 100 * missedTest);
        delete predTestTable;
    }
    delete maxTable;
    delete predModelTable, predInputTable;
}

void ocSBMManager::setFilter(const char *attrname, double attrvalue, RelOp op) {
    if (filterAttr)
        delete filterAttr;
    filterAttr = new char[strlen(attrname) + 1];
    strcpy(filterAttr, attrname);
    filterValue = attrvalue;
    filterOp = op;
}

bool ocSBMManager::applyFilter(ocModel *model) {
    //-- if no filter defined, then it passes
    if (filterAttr == NULL)
        return true;

    //-- make sure require attributes were computed
    computeRelWidth(model);
    computeL2Statistics(model);
    computeDependentStatistics(model);

    //-- now apply the test
    double val = model->getAttribute(filterAttr);
    switch (filterOp) {
        case LESSTHAN:
            return val < filterValue;
        case EQUALS:
            return fabs(val - filterValue) < DBL_EPSILON;
        case GREATERTHAN:
            return val > filterValue;
        default:
            return false;
    }
}

void ocSBMManager::setSortAttr(const char *name) {
    if (sortAttr)
        delete sortAttr;
    sortAttr = new char[strlen(name) + 1];
    strcpy(sortAttr, name);
}

static void printRefTable(ocModel *model, FILE *fd, const char *ref, const char **strings,
        int rows) {
    //-- Print general report for a single model, similar to Fit in Occam2
    const char *line_sep, *header, *beginLine, *endLine, *separator, *footer, *headerSep;
    if (ocReport::isHTMLMode()) {       // does this check a particular ocReport object, or the class?  seems odd.
        line_sep = "<hr>\n";
        header = "<table border=0 cellpadding=0 cellspacing=0><tr><td>&nbsp;</td></tr>\n";
        beginLine = "<tr><td>";
        separator = "</td><td>";
        endLine = "</td></tr>\n";
        footer = "</table><br><br>\n";
        headerSep = "<tr><td colspan=10><hr></td></tr>\n";
    } else {
        line_sep = "-------------------------------------------------------------------------\n";
        header = "";
        beginLine = "    ";
        separator = ",";
        endLine = "\n";
        footer = "\n";
        //headerSep = "    -----------------------------------------------\n";
        headerSep = "";
    }
    int cols = 3;
    int row, col, rowlabel;
    const char *label;

    fprintf(fd, line_sep);
    fprintf(fd, header);
    fprintf(fd, "\n%sREFERENCE = %s%s", beginLine, ref, endLine);
    label = "Value";
    fprintf(fd, "%s%s%s%s", beginLine, separator, label, separator);
    label = "Prob. (Alpha)";
    fprintf(fd, "%s%s", label, endLine);

    fprintf(fd, headerSep);
    for (row = 0; row < rows; row++) {
        rowlabel = row * cols;
        fprintf(fd, "%s%s", beginLine, strings[rowlabel]);
        for (col = 1; col < cols; col++) {
            double value = model->getAttribute(strings[rowlabel + col]);
            if (value >= 0)
                fprintf(fd, "%s%g", separator, value);
            else
                fprintf(fd, "%s", separator);
        }
        fprintf(fd, endLine);
    }
    fprintf(fd, footer);

}

void ocSBMManager::printFitReport(ocModel *model, FILE *fd) {
    //-- Print general report for a single model, similar to Fit in Occam2
    const char *line_sep, *header, *beginLine, *endLine, *separator, *footer;
    if (ocReport::isHTMLMode()) {
        line_sep = "<hr>\n";
        header = "<table border=0 cellspacing=0 cellpadding=0>\n";
        beginLine = "<tr><td>";
        separator = "</td><td>";
        endLine = "</td></tr>\n";
        footer = "</table><br>";
        fprintf(fd, "<br>\n");
    } else {
        line_sep = "-------------------------------------------------------------------------\n";
        header = "";
        beginLine = "    ";
        separator = ",";
        endLine = "\n";
        footer = "\n";
    }
    bool directed = getVariableList()->isDirected();
    fprintf(fd, header);
    fprintf(fd, "%sModel%s%s", beginLine, separator, model->getPrintName());
    if (directed)
        fprintf(fd, " (Directed System)%s", endLine);
    else
        fprintf(fd, " (Neutral System)%s", endLine);

    //-- Print relations using long names
    int i, j;
    for (i = 0; i < model->getRelationCount(); i++) {
        fprintf(fd, beginLine);
        ocRelation *rel = model->getRelation(i);
        if (directed) {
            if (rel->isIndependentOnly())
                fprintf(fd, "IV Component:");
            else
                fprintf(fd, "Model Component: ");
            fprintf(fd, separator);
        }
        for (j = 0; j < rel->getVariableCount(); j++) {
            const char *varname = getVariableList()->getVariable(rel->getVariable(j))->name;
            if (j > 0)
                fprintf(fd, "; ");
            fprintf(fd, varname);
        }
        fprintf(fd, separator);
        fprintf(fd, rel->getPrintName());
        fprintf(fd, endLine);
    }

    //-- Print some general stuff
    const char *label;
    double value;

    label = "Degrees of Freedom (DF):";
    value = model->getAttribute("df");
    fprintf(fd, "%s%s%s%g%s", beginLine, label, separator, value, endLine);
    label = "Loops:";
    value = model->getAttribute("loops");
    fprintf(fd, "%s%s%s%s%s", beginLine, label, separator, value > 0 ? "YES" : "NO", endLine);
    label = "Entropy(H):";
    value = model->getAttribute("h");
    fprintf(fd, "%s%s%s%g%s", beginLine, label, separator, value, endLine);
    label = "Information captured (%):";
    value = model->getAttribute("information") * 100.0;
    fprintf(fd, "%s%s%s%g%s", beginLine, label, separator, value, endLine);
    label = "Transmission (T):";
    value = model->getAttribute("t");
    fprintf(fd, "%s%s%s%g%s", beginLine, label, separator, value, endLine);
    fprintf(fd, footer);
    //-- print top and bottom reference tables
    const char *topFields1[] = { "Log-Likelihood (LR)", ATTRIBUTE_LR, ATTRIBUTE_ALPHA, "Pearson X2",
            ATTRIBUTE_P2, ATTRIBUTE_P2_ALPHA, "Delta DF (dDF)", ATTRIBUTE_DDF, "", };
    const char *bottomFields1[] = { "Log-Likelihood (LR)", ATTRIBUTE_LR, ATTRIBUTE_ALPHA,
            "Pearson X2", ATTRIBUTE_P2, ATTRIBUTE_P2_ALPHA, "Delta DF (dDF)", ATTRIBUTE_DDF, "", };
    //-- compute attributes for top and bottom references
    double h1 = model->getAttribute(ATTRIBUTE_ALG_H);
    double h2 = model->getAttribute(ATTRIBUTE_H);
    model->getAttributeList()->reset();
    model->setAttribute(ATTRIBUTE_ALG_H, h1);
    model->setAttribute(ATTRIBUTE_H, h2);
    setRefModel("top");
    computeInformationStatistics(model);
    computeDependentStatistics(model);
    computeL2Statistics(model);
    computePearsonStatistics(model);
    printRefTable(model, fd, "TOP", topFields1, 3);

    model->getAttributeList()->reset();
    model->setAttribute(ATTRIBUTE_ALG_H, h1);
    model->setAttribute(ATTRIBUTE_H, h2);
    setRefModel("bottom");
    computeInformationStatistics(model);
    computeDependentStatistics(model);
    computeL2Statistics(model);
    computePearsonStatistics(model);
    printRefTable(model, fd, "BOTTOM", bottomFields1, 3);
    fprintf(fd, line_sep);
}

void ocSBMManager::printBasicStatistics() {
    const char *header, *beginLine, *endLine, *separator, *footer;
    //double h;
    if (ocReport::isHTMLMode()) {
        header = "<br><br><table border=0 cellpadding=0 cellspacing=0>\n";
        beginLine = "<tr><td width=170 valign=\"top\">";
        separator = "</td><td>";
        endLine = "</td></tr>\n";
        footer = "</table>";
    } else {
        header = "";
        beginLine = "    ";
        separator = ",";
        endLine = "";
        footer = "";
    }
    bool directed = getVariableList()->isDirected();
    printf("%s\n", header);
    double topH = computeH(topRef);
    double stateSpace = computeDF(getTopRefModel()) + 1;
    double sampleSz1 = getSampleSz();
    double testSampleSize = getTestSampleSize();
    printf("%s%s%s%8lg%s\n", beginLine, "State Space Size", separator, stateSpace, endLine);
    if (!getValuesAreFunctions()) {
        printf("%s%s%s%8lg%s\n", beginLine, "Sample Size", separator, sampleSz1, endLine);
        if (testSampleSize > 0) {
            printf("%s%s%s%8lg%s\n", beginLine, "Sample Size (test)", separator, testSampleSize,
                    endLine);
        }
    }
    printf("%s%s%s%8lg%s\n", beginLine, "H(data)", separator, topH, endLine);
    int varLineBreaks = 0;
    if (directed) {
        double depH = topRef->getRelation(0)->getAttribute(ATTRIBUTE_DEP_H);
        double indH = topRef->getRelation(0)->getAttribute(ATTRIBUTE_IND_H);
        printf("%s%s%s%8lg%s\n", beginLine, "H(IV)", separator, indH, endLine);
        printf("%s%s%s%8lg%s\n", beginLine, "H(DV)", separator, depH, endLine);
        printf("%s%s%s%8lg%s\n", beginLine, "T(IV:DV)", separator, indH + depH - topH, endLine);
        printf("%sIVs in use (%d)%s", beginLine, getVariableList()->getVarCount() - 1, separator);
        for (int i = 0; i < getVariableList()->getVarCount(); i++) {
            if (!getVariableList()->getVariable(i)->dv) {
                if (i / 30 > varLineBreaks) {
                    varLineBreaks++;
                    printf("%s\n", endLine);
                    printf("%s%s", beginLine, separator);
                }
                printf(" %s", getVariableList()->getVariable(i)->abbrev);
            }
        }
        printf("%s\n", endLine);
        printf("%sDV%s%s%s\n", beginLine, separator,
                getVariableList()->getVariable(getVariableList()->getDV())->abbrev, endLine);
        // DV: Z
    } else {
        printf("%sVariables in use (%d)%s", beginLine, getVariableList()->getVarCount(), separator);
        for (int i = 0; i < getVariableList()->getVarCount(); i++) {
            if (i / 30 > varLineBreaks) {
                varLineBreaks++;
                printf("%s\n", endLine);
                printf("%s%s", beginLine, separator);
            }
            printf(" %s", getVariableList()->getVariable(i)->abbrev);
        }
        printf("%s\n", endLine);
    }
    printf("%s\n", footer);
}

