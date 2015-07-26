/* Copyright 2000, Portland State University Systems Science Program.  All Rights Reserved
 */

#include "Core.h"
#include "Math.h"
#include "VBMManager.h"
#include "ModelCache.h"
#include "RelCache.h"
#include "SearchBase.h"
#include "Report.h"
#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <time.h>
//#include "Win32.h"

VBMManager::VBMManager(VariableList *vars, Table *input) :
        ManagerBase(vars, input) {
    topRef = bottomRef = refModel = NULL;
    projection = true;
    search = NULL;
    filterAttr = NULL;
    filterOp = EQUALS;
    filterValue = 0.0;
    sortAttr = NULL;
    sortDirection = 0;
    useInverseNotation = 0;
    DDFMethod = 0;

    firstCome = true;
    firstComeBP = true;
    refer_AIC = 0;
    refer_BIC = 0;
    refer_BP_AIC = 0;
    refer_BP_BIC = 0;
}

VBMManager::VBMManager() :
        ManagerBase() {
    topRef = bottomRef = refModel = NULL;
    projection = true;
    search = NULL;
    filterAttr = NULL;
    filterOp = EQUALS;
    filterValue = 0.0;
    sortAttr = NULL;
    sortDirection = 0;
    useInverseNotation = 0;
    DDFMethod = 0;

    firstCome = true;
    firstComeBP = true;
    refer_AIC = 0;
    refer_BIC = 0;
    refer_BP_AIC = 0;
    refer_BP_BIC = 0;
}

VBMManager::~VBMManager() {
    if (filterAttr)
        delete filterAttr;
    if (sortAttr)
        delete sortAttr;
    if (search)
        delete search;
}

bool VBMManager::initFromCommandLine(int argc, char **argv) {
    if (!ManagerBase::initFromCommandLine(argc, argv))
        return false;
    if (varList) {
        int varCount = varList->getVarCount();
        Relation *top = new Relation(varList, varCount);
        int i;
        for (i = 0; i < varCount; i++)
            top->addVariable(i); // all vars in saturated model
        getRelCache()->addRelation(top);
        top->setTable(inputData);
        makeReferenceModels(top);
    }
    return true;
}

void VBMManager::makeAllChildRelations(Relation *rel, Relation **children, bool makeProject) {
    //-- generate all the children, which are all relations of order one less
    //-- than the given relation, each with one variable removed.  Thus the
    //-- number of these is the order of the given relation.
    //-- By generating them in reverse order of the omitted variable, the
    //-- relations are in sorted order
    int order = rel->getVariableCount();
    int *varindices = new int[order];
    for (int r = order - 1; r >= 0; r--) {
        children[r] = getChildRelation(rel, rel->getVariable(r), makeProject);
    }
    delete varindices;
}

Model *VBMManager::makeChildModel(Model *model, int remove, bool *fromCache, bool makeProject) {
    Model *newModel = new Model(varList->getVarCount());
    int count = model->getRelationCount();
    if (remove >= count)
        return NULL; // bad argument
    for (int i = 0; i < count; i++) {
        Relation *rel = model->getRelation(i);
        if (i == remove) {
            int varCount = rel->getVariableCount();
            Relation **children = new Relation*[varCount];
            makeAllChildRelations(rel, children, makeProject);
            for (int j = 0; j < varCount; j++) {
                newModel->addRelation(children[j]);
            }
            delete children;
        } else {
            newModel->addRelation(rel);
        }
    }
    //-- return one from cache if possible
    if (!modelCache->addModel(newModel)) {
        const char *name = newModel->getPrintName();
        Model *cacheModel = modelCache->findModel(name);
        delete newModel;
        newModel = cacheModel;
        if (fromCache)
            *fromCache = true;
    } else {
        if (fromCache)
            *fromCache = false;
    }
    return newModel;
}

void VBMManager::makeReferenceModels(Relation *top) {
    Model *model = new Model(1);
    model->addRelation(top);
    modelCache->addModel(model);
    topRef = model;

    //-- Generate bottom reference model. If system is neutral.
    //-- this has a relation per variable. Otherwise it has a
    //-- relation per dependent variable, and one containing all
    //-- the independent variables.
    int varCount = varList->getVarCount();
    int* varindices = new int[varCount];
    Relation *rel;
    int i;
    if (varList->isDirected()) {
        //-- first, make a relation with all the independent variables
        model = new Model(2); // typical case: one dep variable
        int pos = 0;
        ocVariable *var;
        for (i = 0; i < varCount; i++) {
            var = varList->getVariable(i);
            if (!var->dv)
                varindices[pos++] = i;
        }
        rel = getRelation(varindices, pos, true);
        model->addRelation(rel);

        //-- now add a unary relation for each dependent variable
        for (i = 0; i < varCount; i++) {
            var = varList->getVariable(i);
            if (var->dv) {
                varindices[0] = i;
                rel = getRelation(varindices, 1, true);
                model->addRelation(rel);
            }
        }
    } else {
        model = new Model(varCount);
        for (i = 0; i < varCount; i++) {
            varindices[0] = i;
            rel = getRelation(varindices, 1, true);
            model->addRelation(rel);
        }
    }
    modelCache->addModel(model);
    bottomRef = model;
    computeDF(topRef);
    computeH(topRef);
    computeDF(bottomRef);
    computeH(bottomRef);
    //-- compute relation statistics for the top relation
    computeStatistics(topRef->getRelation(0));

    //-- set default reference model depending on whether
    //-- the system is directed or neutral
    refModel = varList->isDirected() ? bottomRef : bottomRef;
    delete[] varindices;
}

Model *VBMManager::setRefModel(const char *name) {
    if (strcasecmp(name, "top") == 0) {
        refModel = topRef;
    } else if (strcasecmp(name, "bottom") == 0) {
        refModel = bottomRef;
    } else {
        refModel = makeModel(name, true);
    }
    return refModel;
}

double VBMManager::computeExplainedInformation(Model *model) {
    double info = model->getAttribute(ATTRIBUTE_EXPLAINED_I);
    if (info >= 0)
        return info;
    double topH = topRef->getAttribute(ATTRIBUTE_H);
    double botH = bottomRef->getAttribute(ATTRIBUTE_H);
    double modelT = computeTransmission(model);
    info = (botH - topH - modelT) / (botH - topH);
    // info is normalized but may not quite be between zero and 1 due to roundoff. Fix this here.
    if (info <= 0.0)
        info = 0.0;
    if (info >= 1.0)
        info = 1.0;
    model->setAttribute(ATTRIBUTE_EXPLAINED_I, info);
    return info;
}

double VBMManager::computeUnexplainedInformation(Model *model) {
    double info = model->getAttribute(ATTRIBUTE_UNEXPLAINED_I);
    if (info >= 0)
        return info;
    double topH = topRef->getAttribute(ATTRIBUTE_H);
    double botH = bottomRef->getAttribute(ATTRIBUTE_H);
    double modelT = computeTransmission(model);
    info = modelT / (botH - topH);
    // info is normalized but may not quite be between zero and 1 due to
    // roundoff. Fix this here.
    if (info <= 0.0)
        info = 0.0;
    if (info >= 1.0)
        info = 1.0;
    model->setAttribute(ATTRIBUTE_UNEXPLAINED_I, info);
    return info;
}

void VBMManager::buildDDF(Relation *rel, Model *loModel, Model *diffModel, bool directed) {
    // If this is a directed model, only consider relations that contain the DV
    if (directed && rel->isIndependentOnly()) {
        return;
    }
    // If the loModel contains the relation, return
    if (loModel->containsRelation(rel)) {
        return;
    }

    // If the difference list contains *exactly* this relation, return.
    // These must be checked by comparing all relations, rather than with containsRelation(), because the model is not normalized.
    // That is, the relations in diffModel may be child relations of other relations in the list/model.
    int dcount = diffModel->getRelationCount();
    for (int i = 0; i < dcount; ++i) {
        if (rel->compare(diffModel->getRelation(i)) == 0) {
            return;
        }
    }
    // So, the relation is not in the loModel. It's also not in diffModel, so we add it.
    // The "false" flag says not to normalize: that is, don't combine this with any existing child/parent relations.
    diffModel->addRelation(rel, false);
    int vcount = rel->getVariableCount();
    Relation *subRel;
    for (int i = 0; i < vcount; ++i) {
        subRel = getChildRelation(rel, rel->getVariable(i), false);
        buildDDF(subRel, loModel, diffModel, directed);
    }
    return;
}

double VBMManager::computeDDF(Model *model) {
    double ddf = model->getAttribute(ATTRIBUTE_DDF);
    if (ddf >= 0)
        return ddf;
    if (model == refModel) {
        model->setAttribute(ATTRIBUTE_DDF, 0);
        return 0;
    }
    if (!hasLoops(model)) {
        calculateDfAndEntropy(model);
    }

    // This is the old method of computing delta-DF.
    // It looks simple here, but it is inaccurate with large statespaces.
    if ((DDFMethod == 1) || (model->getAttribute(ATTRIBUTE_DF) >= 0)) {
        int modExp, refExp, ddfExp;
        frexp(computeDF(model), &modExp);
        frexp(computeDF(refModel), &refExp);
        ddf = fabs(computeDF(refModel) - computeDF(model));
        frexp(ddf, &ddfExp);
        int digit_diff = (modExp > refExp ? modExp : refExp) - ddfExp;
        // if we have a good value for dDF now, we're done
        if ((round(ddf) >= 1.0) && (digit_diff < DBL_DIG)) {
            model->setAttribute(ATTRIBUTE_DDF, ddf);
            return ddf;
        }
        // else if ref - mod ~= 0, try the incremental method
    }

    // Alternate method for computing dDF, by adding up the DFs of the unshared relations.
    Model *progen = model->getProgenitor();
    double prog_ddf = -1;
    int signFlip = 1;
    if (progen != NULL) {
        prog_ddf = progen->getAttribute(ATTRIBUTE_DDF);
    }

    Model *hiModel, *loModel;
    // If we know the progenitor, and its dDF, then we only need to compute the small step between them.
    if (prog_ddf >= 0) {
        // If search is up, the model is higher than its progenitor.
        if (searchDirection == Direction::Ascending) { // up
            hiModel = model;
            loModel = progen;
            // However, if the ref is the top, then DDF(model) is DDF(progen) minus the space between them.
            if (refModel == topRef)
                signFlip = -1;
            // If search is down, the model is always lower than its progenitor.
        } else { // down
            hiModel = progen;
            loModel = model;
            // In this case, if the ref is the bottom, the difference will need to be subtracted instead of added.
            if (refModel == bottomRef)
                signFlip = -1;
        }
    } else {
        // Since we're not using the progenitor, set its dDF to zero.
        prog_ddf = 0;
        // Compare model and refModel, to find which is higher up the lattice.
        if (refModel == topRef) {
            hiModel = refModel;
            loModel = model;
        } else if (refModel == bottomRef) {
            hiModel = model;
            loModel = refModel;
        } else {
            // If ref is not the top or bottom, it must be a custom starting model.
            // In this case, we can use the search direction to tell which is higher on the model.
            if (searchDirection == Direction::Ascending) { // up
                hiModel = model;
                loModel = refModel;
            } else { // down
                hiModel = refModel;
                loModel = model;
            }
        }
    }
    // Find all relations in the higher model not in the lower.
    // Do this by considering each of the relations in the high model in turn.
    // We check every relation and child relation against the low model (recursively),
    // to find all those that are in the higher but not the lower.
    int hiCount = hiModel->getRelationCount();
    bool directed = varList->isDirected();
    Model *diffModel = new Model(varList->getVarCount());
    for (int i = 0; i < hiCount; i++) {
        Relation *hiRel = hiModel->getRelation(i);
        buildDDF(hiRel, loModel, diffModel, directed);
    }
    // With the list of individual relations by which the two models differ,
    // we can now find the delta-DF.  Each relation contributes the product
    // of all its variables' (cardinality - 1).
    long long int ddf2 = 0;
    int rcount = diffModel->getRelationCount();
    for (int i = 0; i < rcount; i++) {
        ddf2 += diffModel->getRelation(i)->getDDFPortion();
    }
    delete diffModel;

    // If ddf was figured from the progenitor, now add/subtract this to the ddf of the progenitor itself.
    // If this was not from the progenitor, this has no effect.
    ddf2 = ddf2 * signFlip + (long long int) prog_ddf;

    model->setAttribute(ATTRIBUTE_DDF, (double) ddf2);
    return (double) ddf2;
}

void VBMManager::setDDFMethod(int method) {
    if ((method == 0) || (method == 1))
        DDFMethod = method;
    else
        DDFMethod = 0;
}

void VBMManager::setUseInverseNotation(int flag) {
    if (flag == 1)
        useInverseNotation = 1;
    else
        useInverseNotation = 0;
}

void VBMManager::setSearch(const char *name) {
    if (search) {
        delete search;
        search = NULL;
    }
    search = SearchFactory::getSearchMethod(this, name, makeProjection());
}

void VBMManager::computeDFStatistics(Model *model) {
    computeDF(model);
    computeDDF(model);
}

void VBMManager::computeInformationStatistics(Model *model) {
    computeH(model);
    computeTransmission(model);
    computeExplainedInformation(model);
    computeUnexplainedInformation(model);
}

void VBMManager::calculateBP_AicBic(Model *model) {
    double sampleSize = getSampleSz();
    double deltaH_Aic = computeH(model);
    deltaH_Aic *= log(2.0); // convert h to ln rather than log base 2 again
    double deltaH_Bic = deltaH_Aic;
    double modelDF = computeDF(model); // get DF of the model

    // delta - AIC & BIC
    if (firstCome) {
        double reDeltaH_Aic = computeH(refModel);
        double refDF = computeDF(refModel); // get DF of the ref model
        reDeltaH_Aic *= log(2.0);
        firstCome = false;
        refer_BP_AIC = (2 * sampleSize) * reDeltaH_Aic + 2 * refDF;
        refer_BP_BIC = (2 * sampleSize) * reDeltaH_Aic + (log(sampleSize) * refDF);
    }
    deltaH_Aic = (2 * sampleSize) * deltaH_Aic + 2 * modelDF;
    deltaH_Bic = (2 * sampleSize) * deltaH_Bic + (log(sampleSize) * modelDF);

    deltaH_Aic = refer_BP_AIC - deltaH_Aic; // calculate AIC and BIC
    deltaH_Bic = refer_BP_BIC - deltaH_Bic;
    model->setAttribute(ATTRIBUTE_BP_AIC, deltaH_Aic);
    model->setAttribute(ATTRIBUTE_BP_BIC, deltaH_Bic);
}

void VBMManager::computeL2Statistics(Model *model) {
    //-- make sure the other attributes are there
    computeInformationStatistics(model);
    //-- compute chi-squared statistics and related statistics. L2 = 2*n*sum(p(ln p/q)) = 2*n*ln(2)*T
    // L2 (or dLR) is computed to always be positive
    // The values that depend on it (BIC and AIC) have their signs corrected below
    double refL2 = computeLR(model);
    double refDDF = computeDDF(model);

    double refL2Prob = model->getAttribute(ATTRIBUTE_ALPHA);
    if (refL2Prob < 0) {
        refL2Prob = csa(refL2, refDDF);
        model->setAttribute(ATTRIBUTE_ALPHA, refL2Prob);
    }

    double refL2Power = model->getAttribute(ATTRIBUTE_BETA);
    if (refL2Power < 0) {
        refL2Power = 0;
        double critX2 = 0;
        int errcode = 0;
        double alpha;
        if (!getOptionFloat("palpha", NULL, &alpha))
            alpha = 0.0;
        if (alpha > 0)
            critX2 = ppchi(alpha, refDDF, &errcode);
        else
            critX2 = refL2;
        if (errcode)
            printf("ppchi: errcode=%d\n", errcode);
        refL2Power = 1.0 - chin2(critX2, refDDF, refL2, &errcode);
        model->setAttribute(ATTRIBUTE_BETA, refL2Power);
    }

    double dAIC = refL2 - 2.0 * computeDDF(model);
    double dBIC = refL2 - log(sampleSize) * computeDDF(model);

    // If the top model is the reference, or if there is a custom start model and we're searching down,
    // we flip the signs of dAIC and dBIC.  (A custom start occurs when ref is neither top nor bottom.)
    // (That is, flip signs in cases when the reference is above the model in the lattice.)
    if ((refModel == topRef) || ((refModel != bottomRef) && (searchDirection == Direction::Descending))) {
        dAIC = -dAIC;
        dBIC = -dBIC;
    }
    model->setAttribute(ATTRIBUTE_AIC, dAIC);
    model->setAttribute(ATTRIBUTE_BIC, dBIC);
}

void VBMManager::computePearsonStatistics(Model *model) {
    //-- these statistics require a full contingency table, so make
    //-- sure one has been created.
    if (model == NULL || bottomRef == NULL)
        return;
    makeFitTable(model);
    Table *modelFitTable = new Table(keysize, fitTable1->getTupleCount());
    modelFitTable->copy(fitTable1);
    makeFitTable(bottomRef);
    double modelP2 = ocPearsonChiSquared(inputData, modelFitTable, (long) round(sampleSize));
    double refP2 = ocPearsonChiSquared(inputData, fitTable1, (long) round(sampleSize));

    int errcode;
    double refDDF = computeDDF(model);
    double refModelP2 = refP2 - modelP2;
    double refP2Prob = csa(refModelP2, refDDF);

    double critX2, refP2Power;

    errcode = 0;
    double alpha;
    if (!getOptionFloat("palpha", NULL, &alpha))
        alpha = 0.0;
    if (alpha > 0)
        critX2 = ppchi(alpha, refDDF, &errcode);
    else
        critX2 = modelP2;
    if (errcode)
        printf("ppchi: errcode=%d\n", errcode);
    refP2Power = 1.0 - chin2(critX2, refDDF, modelP2, &errcode);

    //if (errcode) printf("chin2: errcode=%d\n", errcode);
    //?? do something with these returned errors

    model->setAttribute(ATTRIBUTE_P2, modelP2);
    model->setAttribute(ATTRIBUTE_P2_ALPHA, refP2Prob);
    model->setAttribute(ATTRIBUTE_P2_BETA, refP2Power);
    delete modelFitTable;
}

void VBMManager::computeDependentStatistics(Model *model) {
    //-- the basic metric is the conditional uncertainty u(Z|ABC...), which is
    //-- u(model) - u(ABC...), where ABC... are the independent variables
    //-- first, compute the relation stats for the bottom reference model, which
    //-- will give us the u(ABC...).
    if (!getVariableList()->isDirected())
        return; // can only do this for directed models
    double depH = topRef->getRelation(0)->getAttribute(ATTRIBUTE_DEP_H);
    Relation *indRel = getIndRelation();
    double indH = indRel->getAttribute(ATTRIBUTE_H);
    double refH = computeH(bottomRef);
    //double refCondH = refH - indH;

    double h = computeH(model);
    double condH = h - indH;
    model->setAttribute(ATTRIBUTE_COND_H, condH);
    model->setAttribute(ATTRIBUTE_COND_DH, refH - h);
    model->setAttribute(ATTRIBUTE_COND_PCT_DH, 100 * (refH - h) / depH);
}

double VBMManager::computeBPT(Model *model) {
    // this function computes transmission using the Fourier BP method.
    // Individual q values are computed as the mean value from each projection,
    // q(x) = sum (R(x)/|R|) - (nR - 1), where R(x) is the projected value
    // which contains state x in relation R; |R| is the number of states collapsed
    // into each state of relation R; and nR is the number of relations in the model.
    //
    // Since the transmission terms are p(x) log (p(x)/q(x)), these computations
    // are only done for nonzero p and q values.
    // Subtracting for overlaps may leave the result un-normalized because of
    // Null overlaps (for example, AB:CD has no overlaps, but p(AB)+p(CD) = 2, not 1)
    // The count of origin terms which much still be deducted for normalization
    // is maintained, and the q values corrected at the end.

    class BPIntersectProcessor: public ocIntersectProcessor {
        public:
            BPIntersectProcessor(Table *inData, double fullDim) {
                inputData = inData;
                keysize = inputData->getKeySize();
                qData = new Table(keysize, inputData->getTupleCount());
                fullDimension = fullDim;
                originTerms = 0;
                relCount = 0;
            }

            void reset(int rels) {
                qData->reset(keysize);

                //-- seed the computed table with the tuples from the input data,
                //-- but with zero values. These are the only tuples we care about.
                for (int i = 0; i < inputData->getTupleCount(); i++) {
                    KeySegment *key = inputData->getKey(i);
                    qData->addTuple(key, 0);
                }

                //-- keep track of the total probability so we can deduct
                //-- the appropriate number of origin terms.
                originTerms = 0;

                relCount = rels;
            }

            virtual ~BPIntersectProcessor() {
                delete qData;
            }

            virtual void process(bool sign, Relation *rel, int count) {
                for (int counter = 0; counter < count; counter++) {
                    KeySegment key[keysize];
                    double qi, q;
                    //-- get the orthogonal dimension of the relation (the number of states projected into one substate)
                    double relDimension = fullDimension / (ocDegreesOfFreedom(rel) + 1);
                    //-- add the scaled contribution to each q
                    for (int i = 0; i < qData->getTupleCount(); i++) {
                        qData->copyKey(i, key);
                        q = qData->getValue(i);
                        KeySegment *mask = rel->getMask();
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

            Table *qData, *inputData;
            double fullDimension;
            int keysize;
            int relCount;
            int originTerms;
    };

    static BPIntersectProcessor *processor = NULL;

    //-- see if we did this already.
    double modelT = model->getAttribute(ATTRIBUTE_BP_T);
    if (modelT >= 0)
        return modelT;

    double fullDimension = ocDegreesOfFreedom(topRef->getRelation(0)) + 1;

    //-- because we clear the cache periodically, we have to force
    //-- creation of all projections here
    int relCount = model->getRelationCount();
    int r;
    class Relation *rel;
    for (r = 0; r < relCount; r++) {
        rel = model->getRelation(r);
        ManagerBase::makeProjection(rel);
    }

    if (processor == NULL)
        processor = new BPIntersectProcessor(inputData, fullDimension);
    processor->reset(relCount);
    if (intersectArray != NULL) {
        delete[] intersectArray;
        intersectCount = 0;
        intersectMax = model->getRelationCount();
        ;
        intersectArray = NULL;
    }

    doIntersectionProcessing(model, processor);
    modelT = processor->getTransmission();
    model->setAttribute(ATTRIBUTE_BP_T, modelT);
    return modelT;
}

void VBMManager::computeBPStatistics(Model *model) {
    double modelT = computeBPT(model);
    double topH = computeH(topRef);
    //-- we need both BP and standard T for the bottom model
    double botBPT = computeBPT(bottomRef);
    double botStdT = computeTransmission(bottomRef);
    //-- estimate H by scaling the standard T of the bottom model, proportionately
    //-- with the BP_T of the model and the bottom model
    double modelH = topH + modelT * botStdT / botBPT;

    model->setAttribute(ATTRIBUTE_BP_H, modelH);

    double info = modelT / botBPT;
    // info is normalized but may not quite be between zero and 1 due to
    // roundoff. Fix this here.
    if (info <= 0.0)
        info = 0.0;
    if (info >= 1.0)
        info = 1.0;
    model->setAttribute(ATTRIBUTE_BP_EXPLAINED_I, 1.0 - info);
    model->setAttribute(ATTRIBUTE_BP_UNEXPLAINED_I, info);

    //-- make sure the other attributes are there
    //computeDFStatistics(model);
    //-- compute chi-squared statistics and related statistics. L2 = 2*n*sum(p(ln p/q))
    //-- which is 2*n*ln(2)*T
    int errcode;
    double modelL2 = 2.0 * M_LN2 * sampleSize * modelT;
    double refT = computeBPT(refModel);
    double refL2 = 2.0 * M_LN2 * sampleSize * refT;
    double refModelL2 = refL2 - modelL2;
    double refDDF = computeDDF(model);

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
    if (!getOptionFloat("palpha", NULL, &alpha))
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
    model->setAttribute(ATTRIBUTE_BP_LR, refModelL2);
    model->setAttribute(ATTRIBUTE_BP_ALPHA, refL2Prob);
    model->setAttribute(ATTRIBUTE_BP_BETA, refL2Power);

    //-- dependent statistics
    if (!getVariableList()->isDirected())
        return; // can only do this for directed models
    double depH = topRef->getRelation(0)->getAttribute(ATTRIBUTE_DEP_H);
    double indH = topRef->getRelation(0)->getAttribute(ATTRIBUTE_IND_H);
    // for these computations, we need an estimated H which is compatible
    // with the Info-theoretic measures.
    double refH = computeH(bottomRef);
    //double refCondH = refH - indH;

    double condH = modelH - indH;

    //        calculate BP_AIC & BIC by Junghan
    calculateBP_AicBic(model);

    model->setAttribute(ATTRIBUTE_BP_COND_H, condH);
    model->setAttribute(ATTRIBUTE_BP_COND_DH, refH - modelH);
    model->setAttribute(ATTRIBUTE_BP_COND_PCT_DH, 100 * (refH - modelH) / depH);
}

void VBMManager::computePercentCorrect(Model *model) {
    double total;
    long long count, i;
    Relation *indRel = getIndRelation();
    Relation *depRel = getDepRelation();

    //-- if either of these is empty, then we don't have a directed system
    if (indRel == 0 || depRel == 0)
        return;

    ((ManagerBase*) this)->makeProjection(depRel);

    if (!makeFitTable(model))
        printf("ERROR\n");
    Table *modelTable = fitTable1;
    Table *maxTable = new Table(modelTable->getKeySize(), modelTable->getTupleCount());

    int maxCount = varList->getVarCount();
    int varindices[maxCount], varcount;
    getPredictingVars(model, varindices, varcount, false);
    Relation *predRelNoDV = getRelation(varindices, varcount);
    getPredictingVars(model, varindices, varcount, true);
    Relation *predRelWithDV = getRelation(varindices, varcount);
    Table *predModelTable = new Table(keysize, modelTable->getTupleCount());

    Table *predInputTable = new Table(keysize, modelTable->getTupleCount());
    ManagerBase::makeProjection(modelTable, predModelTable, predRelWithDV);
    ManagerBase::makeProjection(inputData, predInputTable, predRelWithDV);

    Table *inputsOnly = new Table(keysize, modelTable->getTupleCount());
    ManagerBase::makeProjection(inputData, inputsOnly, predRelNoDV);
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
        Table *predTestTable = new Table(keysize, testData->getTupleCount());
        ManagerBase::makeProjection(testData, predTestTable, predRelWithDV);
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

void VBMManager::setFilter(const char *attrname, double attrvalue, RelOp op) {
    if (filterAttr)
        delete filterAttr;
    filterAttr = new char[strlen(attrname) + 1];
    strcpy(filterAttr, attrname);
    filterValue = attrvalue;
    filterOp = op;
}

bool VBMManager::applyFilter(Model *model) {
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

void VBMManager::setSortAttr(const char *name) {
    if (sortAttr)
        delete sortAttr;
    sortAttr = new char[strlen(name) + 1];
    strcpy(sortAttr, name);
}

static void printRefTable(Model *model, FILE *fd, const char *ref, const char **strings, int rows) {
    //-- Print general report for a single model, similar to Fit in Occam2
    const char *line_sep, *header, *beginLine, *endLine, *separator, *footer, *headerSep;
    if (Report::isHTMLMode()) {
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

void VBMManager::printFitReport(Model *model, FILE *fd) {
    //-- Print general report for a single model, similar to Fit in Occam2
    const char *line_sep, *header, *beginLine, *endLine, *separator, *footer;
    if (Report::isHTMLMode()) {
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
        Relation *rel = model->getRelation(i);
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
    const char *topFields1[] = { "Log-Likelihood (LR)", ATTRIBUTE_LR, ATTRIBUTE_ALPHA, "Pearson X2", ATTRIBUTE_P2,
            ATTRIBUTE_P2_ALPHA, "Delta DF (dDF)", ATTRIBUTE_DDF, "", };
    const char *bottomFields1[] = { "Log-Likelihood (LR)", ATTRIBUTE_LR, ATTRIBUTE_ALPHA, "Pearson X2", ATTRIBUTE_P2,
            ATTRIBUTE_P2_ALPHA, "Delta DF (dDF)", ATTRIBUTE_DDF, "", };
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

void VBMManager::printBasicStatistics() {
    const char *header, *beginLine, *endLine, *separator, *footer;
    //double h;
    if (Report::isHTMLMode()) {
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
    
    bool no_freq = false;
    const char *option;
    if (getOptionString("no-frequency", NULL, &option)) {
        no_freq = true;
    }
    
    if (!getValuesAreFunctions()) {
        printf("%s%s%s%8lg%s\n", beginLine, "Sample Size", separator, sampleSz1, endLine);
        if (no_freq && sampleSz1 != dataLines)
        {
            printf("%s%s%g%s%d%s\n", beginLine, 
                   "Warning: option 'no-frequency' is set and sample size (", 
                   sampleSz1, ") does not equal number of lines read (", dataLines,
                   "); this may be due to lines being excluded due to missing values,"
                   " or the selection of specific variable states for analysis,"
                   " or the presence of a frequency column"
                   " (which may be due to a missing variable declaration)");
        }

        if (testSampleSize > 0) {
            printf("%s%s%s%8lg%s\n", beginLine, "Sample Size (test)", separator, testSampleSize, endLine);
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
        printf("%sDV%s%s%s\n", beginLine, separator, getVariableList()->getVariable(getVariableList()->getDV())->abbrev,
                endLine);
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

