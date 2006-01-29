/* Copyright 2000, Portland State University Systems Science Program.  All Rights Reserved
 */

#include "ocCore.h"
#include "ocMath.h"
#include "ocVBMManager.h"
#include "ocModelCache.h"
#include "ocSearchBase.h"
#include "ocReport.h"
#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include "ocWin32.h"

ocVBMManager::ocVBMManager(ocVariableList *vars, ocTable *input):
	ocManagerBase(vars, input)
{
	topRef = bottomRef = refModel = NULL;
	projection = true;
	search = NULL;
	filterAttr = NULL;
	filterOp = EQUALS;
	filterValue = 0.0;
	sortAttr = NULL;
	sortDirection = 0;

        // by Junghan *****************
        firstCome = true;
        firstComeBP = true;
        refer_AIC = 0;
        refer_BIC = 0;
        refer_BP_AIC = 0;
        refer_BP_BIC = 0;
}

ocVBMManager::ocVBMManager():
	ocManagerBase()
{
	topRef = bottomRef = refModel = NULL;
	projection = true;
	search = NULL;
	filterAttr = NULL;
	filterOp = EQUALS;
	filterValue = 0.0;
	sortAttr = NULL;
	sortDirection = 0;

        // by Junghan *****************
        firstCome = true;
        firstComeBP = true;
        refer_AIC = 0;
        refer_BIC = 0;
        refer_BP_AIC = 0;
        refer_BP_BIC = 0;
}

ocVBMManager::~ocVBMManager()
{
	if (filterAttr) delete filterAttr;
	if (sortAttr) delete sortAttr;
}

bool ocVBMManager::initFromCommandLine(int argc, char **argv)
{
	if (!ocManagerBase::initFromCommandLine(argc, argv)) return false;
	if (varList) {
		int varCount = varList->getVarCount();
		ocRelation *top = new ocRelation(varList, varCount);
		int i;
		for (i = 0; i < varCount; i++) top->addVariable(i);	// all vars in saturated model
		top->setTable(inputData);
		makeReferenceModels(top);
	}
	return true;
}

void ocVBMManager::makeAllChildRelations(ocRelation *rel, 
	ocRelation **children, bool makeProject)
{
	//-- generate all the children, which are all relations of order one less
	//-- than the given relation, each with one variable removed.  Thus the
	//-- number of these is the order of the given relation.
	//-- By generating them in reverse order of the ommitted variable, the
	//-- relations are in sorted order
	int order = rel->getVariableCount();
	int *varindices = new int[order];
	for (int r = order-1; r >= 0; r--) {
		children[r] = getChildRelation(rel, r, makeProject);
	}
	delete varindices;
}

ocModel *ocVBMManager::makeChildModel(ocModel *model, int remove, bool *fromCache, bool makeProject)
{
	ocModel *newModel = new ocModel(varList->getVarCount());
	int count = model->getRelationCount();
	if (remove >= count) return NULL;	// bad argument
	for (int i = 0; i < count; i++) {
		ocRelation *rel = model->getRelation(i);
		if (i == remove) {
			int varCount = rel->getVariableCount();
			ocRelation **children = new ocRelation*[varCount];
			makeAllChildRelations(rel, children, makeProject);
			for (int j = 0; j < varCount; j++) {
				newModel->addRelation(children[j]);
			}
			delete children;
		}
		else {
			newModel->addRelation(rel);
		}
	}
	//-- return one from cache if possible
	if (!modelCache->addModel(newModel)) {
		const char *name = newModel->getPrintName();
		ocModel *cacheModel = modelCache->findModel(name);
		delete newModel;
		newModel = cacheModel;
		if (fromCache) *fromCache = true;
	}
	else {
		if (fromCache) *fromCache = false;
	}
	return newModel;
}

void ocVBMManager::makeReferenceModels(ocRelation *top)
{
	ocModel *model = new ocModel(1);
	model->addRelation(top);
	modelCache->addModel(model);
	topRef = model;
	
	//-- Generate bottom reference model. If system is neutral.
	//-- this has a relation per variable. Otherwise it has a
	//-- relation per dependent variable, and one containing all
	//-- the independent variables.
	int varCount = varList->getVarCount();
	int* varindices = new int[varCount];
	ocRelation *rel;
	int i;
	if (varList->isDirected()) {
		//-- first, make a relation with all the independent variables
		model = new ocModel(2);	// typical case: one dep variable
		int pos = 0;
		ocVariable *var;
		for (i = 0; i < varCount; i++) {
			var = varList->getVariable(i);
			if (!var->dv) varindices[pos++] = i;
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
	}
	else {
		model = new ocModel(varCount);
		for (i = 0; i < varCount; i++) {
			//-- build a list of all variables but r
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
	refModel = varList->isDirected() ? bottomRef : topRef;
	delete [] varindices;
}

ocModel *ocVBMManager::setRefModel(const char *name)
{
	if (strcasecmp(name, "top") == 0) {
		refModel = topRef;
	}
	else if (strcasecmp(name, "bottom") == 0) {
		refModel = bottomRef;
	}
	else {
		refModel = makeModel(name, true);
	}
	return refModel;
}

double ocVBMManager::computeExplainedInformation(ocModel *model)
{
	ocAttributeList *attrs = model->getAttributeList();
	double topH = topRef->getAttributeList()->getAttribute(ATTRIBUTE_H);
	double botH = bottomRef->getAttributeList()->getAttribute(ATTRIBUTE_H);
	double modelT = computeTransmission(model);
	double info = (botH - topH - modelT) / (botH - topH);
	// info is normalized but may not quite be between zero and 1 due to
	// roundoff. Fix this here.
	if (info <= 0.0) info = 0.0;
	if (info >= 1.0) info = 1.0;
	attrs->setAttribute(ATTRIBUTE_EXPLAINED_I, info);
	return info;
}

double ocVBMManager::computeUnexplainedInformation(ocModel *model)
{
	ocAttributeList *attrs = model->getAttributeList();
	double topH = topRef->getAttributeList()->getAttribute(ATTRIBUTE_H);
	double botH = bottomRef->getAttributeList()->getAttribute(ATTRIBUTE_H);
	double modelT = computeTransmission(model);
	double info = modelT / (botH - topH);
	// info is normalized but may not quite be between zero and 1 due to
	// roundoff. Fix this here.
	if (info <= 0.0) info = 0.0;
	if (info >= 1.0) info = 1.0;
	attrs->setAttribute(ATTRIBUTE_UNEXPLAINED_I, info);
	return info;
}

double ocVBMManager::computeDDF(ocModel *model)
{
	ocAttributeList *attrs = model->getAttributeList();
	double refDF = getRefModel()->getAttributeList()->getAttribute(ATTRIBUTE_DF);
	double modelDF = attrs->getAttribute(ATTRIBUTE_DF);
	double df = refDF - modelDF;
	//-- for bottom reference the sign will be wrong
	df = fabs(df);
	attrs->setAttribute(ATTRIBUTE_DDF, df);
	return df;
}

void ocVBMManager::setSearch(const char *name)
{
	if (search) {
		delete search;
		search = NULL;
	}
	search = ocSearchFactory::getSearchMethod(this, name, makeProjection());
}

void ocVBMManager::computeDFStatistics(ocModel *model)
{
	computeDF(model);
	computeDDF(model);
}

void ocVBMManager::computeInformationStatistics(ocModel *model)
{
	computeH(model);
	computeTransmission(model);
	computeExplainedInformation(model);
	computeUnexplainedInformation(model);
}

/****************************************************************

        calculateAIC() & calculateBIC() by Junghan

        This function will calculate delta-AIC with H and DF

        * AIC = -2 * samplesize * sigma p log p + 2 * df
        * BIC = -2 * samplesize * sigma p log p + log (samplesize) * df

        AIC = 2 * N * H + 2 * df
        BIC = 2 * N * H + log(N) * df

        input  : ocModel *model
        output : .

****************************************************************/
void ocVBMManager::calculateAicBic(ocModel *model,ocAttributeList *attrs)
{
        double sampleSize = getSampleSz();
        double deltaH_Aic = computeH(model);
	deltaH_Aic *= log(2.0);  		// convert h to ln rather than log base 2 again
	double deltaH_Bic = deltaH_Aic;
	double modelDF = computeDF(model);	// get DF of the model

	//******************************
	// delta - AIC & BIC
	if(firstCome){
	    double reDeltaH_Aic = computeH(refModel);
	    double refDF = computeDF(refModel);	// get DF of the ref model
	    reDeltaH_Aic *= log(2.0);
            firstCome = false;
            refer_AIC = (2*sampleSize)*reDeltaH_Aic + 2*refDF;
            refer_BIC = (2*sampleSize)*reDeltaH_Aic + (log(sampleSize)*refDF);
	}
        deltaH_Aic = (2*sampleSize)*deltaH_Aic + 2*modelDF;
        deltaH_Bic = (2*sampleSize)*deltaH_Bic + (log(sampleSize)*modelDF);

	//******************************
	deltaH_Aic = refer_AIC-deltaH_Aic;	// calculate delta AIC and BIC
	deltaH_Bic = refer_BIC-deltaH_Bic;
        attrs->setAttribute(ATTRIBUTE_AIC, deltaH_Aic);
        attrs->setAttribute(ATTRIBUTE_BIC, deltaH_Bic);
}

void ocVBMManager::calculateBP_AicBic(ocModel *model, ocAttributeList *attrs)
{
        double sampleSize = getSampleSz();
        double deltaH_Aic = computeH(model);
        deltaH_Aic *= log(2.0);  // convert h to ln rather than log base 2 again
        double deltaH_Bic = deltaH_Aic;
	double modelDF = computeDF(model);	// get DF of the model

	//******************************
	// delta - AIC & BIC
	if(firstCome){
	    double reDeltaH_Aic = computeH(refModel);
	    double refDF = computeDF(refModel);	// get DF of the ref model
	    reDeltaH_Aic *= log(2.0);
            firstCome = false;
            refer_BP_AIC = (2*sampleSize)*reDeltaH_Aic + 2*refDF;
            refer_BP_BIC = (2*sampleSize)*reDeltaH_Aic + (log(sampleSize)*refDF);
	}
        deltaH_Aic = (2*sampleSize)*deltaH_Aic + 2*modelDF;
        deltaH_Bic = (2*sampleSize)*deltaH_Bic + (log(sampleSize)*modelDF);

	//******************************
        deltaH_Aic = refer_BP_AIC - deltaH_Aic;	// calculate AIC and BIC
        deltaH_Bic = refer_BP_BIC - deltaH_Bic;
        attrs->setAttribute(ATTRIBUTE_BP_AIC, deltaH_Aic);
        attrs->setAttribute(ATTRIBUTE_BP_BIC, deltaH_Bic);
}

//***************************************************************************************

void ocVBMManager::computeL2Statistics(ocModel *model)
{
	//-- make sure we have the fittted table (needed for some statistics)
	//-- this will return immediately if the table was already created.
	ocAttributeList *attrs = model->getAttributeList();

	//-- make sure the other attributes are there
	computeDFStatistics(model);
	computeInformationStatistics(model);
	//-- compute chi-squared statistics and related statistics. L2 = 2*n*sum(p(ln p/q))
	//-- which is 2*n*ln(2)*T
	int errcode;
	double modelT = computeTransmission(model);
	double modelL2 = 2.0 * M_LN2 * sampleSize * modelT;
	double refT = computeTransmission(refModel);
	double refL2 = 2.0 * M_LN2 * sampleSize * refT;
	double refModelL2 = refL2 - modelL2;
	double modelDF = computeDF(model);
	double refDF = computeDF(refModel);
	double refDDF = modelDF - refDF;

	//-- depending on the relative position of the reference model and the
	//-- current model in the hierarchy, refDDF may be positive or negative
	//-- as may refModel2. But the signs should be the same. If they aren't,
	//-- the csa computation will fail.
	if (refDDF < 0) {
		refDDF = -refDDF;
		refModelL2 = - refModelL2;
	}

	//-- eliminate negative value due to small roundoff
	if (refModelL2 <= 0.0) refModelL2 = 0.0;

	double refL2Prob = csa(refModelL2, refDDF);

	double critX2=0, refL2Power=0;

	errcode = 0;
	double alpha;
	if (!getOptionFloat("palpha", NULL, &alpha)) alpha = 0.0;
	if (alpha > 0) critX2 = ppchi(alpha, refDDF, &errcode);
	else critX2 = refModelL2;
	if (errcode) printf("ppchi: errcode=%d\n", errcode);
	refL2Power = 1.0 - chin2(critX2, refDDF, refModelL2, &errcode);

        /***************************************
                calculate AIC by Junghan
        ***************************************/
        calculateAicBic(model,attrs);

	//?? do something with these returned errors
	attrs->setAttribute(ATTRIBUTE_DDF, refDDF);
	attrs->setAttribute(ATTRIBUTE_LR, refModelL2);
	attrs->setAttribute(ATTRIBUTE_ALPHA, refL2Prob);
	attrs->setAttribute(ATTRIBUTE_BETA, refL2Power);
}

void ocVBMManager::computePearsonStatistics(ocModel *model)
{
	//-- these statistics require a full contingency table, so make
	//-- sure one has been created.
	if (model == NULL || bottomRef == NULL) return;
	makeFitTable(model);
	ocTable *modelFitTable = new ocTable(keysize, fitTable1->getTupleCount());
	modelFitTable->copy(fitTable1);
	makeFitTable(bottomRef);
	double modelP2 = ocPearsonChiSquared(inputData, modelFitTable, sampleSize);
	double refP2 = ocPearsonChiSquared(inputData, fitTable1, sampleSize);
	ocAttributeList *attrs = model->getAttributeList();

	int errcode;
	double modelDF = computeDF(model);
	double refDF = computeDF(refModel);
	double refDDF = modelDF - refDF;
	double refModelP2 = refP2 - modelP2;
	double refP2Prob = csa(refModelP2, refDDF);

	double critX2, refP2Power;


	errcode = 0;
	double alpha;
	if (!getOptionFloat("palpha", NULL, &alpha)) alpha = 0.0;
	if (alpha > 0) critX2 = ppchi(alpha, refDDF, &errcode);
	else critX2 = modelP2;
	if (errcode) printf("ppchi: errcode=%d\n", errcode);
	refP2Power = 1.0 - chin2(critX2, refDDF, modelP2, &errcode);

	//if (errcode) printf("chin2: errcode=%d\n", errcode);
	//?? do something with these returned errors

	attrs->setAttribute(ATTRIBUTE_P2, modelP2);
	attrs->setAttribute(ATTRIBUTE_P2_ALPHA, refP2Prob);
	attrs->setAttribute(ATTRIBUTE_P2_BETA, refP2Power);
}
	
ocRelation *ocVBMManager::getIndRelation()
{
	if (!getVariableList()->isDirected()) return NULL;	// can only do this for directed models
	int i;
	for (i = 0; i < bottomRef->getRelationCount(); i++) {
		ocRelation *indRel = bottomRef->getRelation(i);
		if (indRel->isIndOnly()) return indRel;	// this is the one.
	}
	return NULL;
}

ocRelation *ocVBMManager::getDepRelation()
{
  //-- this function takes advantage of the fact that the bottom model has only two relations;
  //-- one is the IV relation, the other is the DV
	if (!getVariableList()->isDirected()) return NULL;	// can only do this for directed models
	int i;
	for (i = 0; i < bottomRef->getRelationCount(); i++) {
		ocRelation *indRel = bottomRef->getRelation(i);
		if (!indRel->isIndOnly()) return indRel;	// this is the one.
	}
	return NULL;
}

void ocVBMManager::computeDependentStatistics(ocModel *model)
{
	//-- the basic metric is the conditional uncertainty u(Z|ABC...), which is
	//-- u(model) - u(ABC...), where ABC... are the independent variables
	//-- first, compute the relation stats for the bottom reference model, which
	//-- will give us the u(ABC...).
	if (!getVariableList()->isDirected()) return;	// can only do this for directed models
	double depH = topRef->getRelation(0)->getAttributeList()->getAttribute(ATTRIBUTE_DEP_H);
	ocRelation *indRel = getIndRelation();
	ocAttributeList *indAttrs = indRel->getAttributeList();
	ocAttributeList *attrs = model->getAttributeList();
	double indH = indAttrs->getAttribute(ATTRIBUTE_H);
	double refH = computeH(bottomRef);
	double refCondH = refH - indH;

	double h = computeH(model);
	double condH = h - indH;
	attrs->setAttribute(ATTRIBUTE_COND_H, condH);
	attrs->setAttribute(ATTRIBUTE_COND_DH, refH - h);
	attrs->setAttribute(ATTRIBUTE_COND_PCT_DH, 100 * (refH - h) / depH);
}

double ocVBMManager::computeBPT(ocModel *model)
{
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

	class BPIntersectProcessor : public ocIntersectProcessor
	{
	public:
		BPIntersectProcessor(ocTable *inData, double fullDim)
	        {
			inputData = inData;
			keysize = inputData->getKeySize();
			qData = new ocTable(keysize, inputData->getTupleCount());
			fullDimension = fullDim;
		}

	        void reset(int rels)
		{
		        qData->reset(keysize);

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
		}

 		virtual ~BPIntersectProcessor()
		{
			delete qData;
		}


		virtual void process(int sign, ocRelation *rel)
		{
			ocKeySegment key[keysize];
			double qi, q;
			//-- get the orthogonal dimension of the relation (the number of states
			//-- projected into one substate)
			double relDimension = fullDimension / 
				(ocDegreesOfFreedom(rel) + 1);
			//-- add the scaled contribution to each q
			for (int i = 0; i < qData->getTupleCount(); i++) {
				qData->copyKey(i, key);
				q = qData->getValue(i);
				ocKeySegment *mask = rel->getMask();
				for (int k = 0; k < keysize; k++) key[k] |= mask[k];
				int j = rel->getTable()->indexOf(key);
				if (j >= 0) {
					qi = sign * (rel->getTable()->getValue(j) / relDimension);
					qData->setValue(i, qi + q);
				}
			}
			originTerms += sign;
		}

		double getTransmission()
		{
			correctOriginTerms();

			double t, p, q;
			t = 0;
			for (long i = 0; i < inputData->getTupleCount(); i++) {
				long j = qData->indexOf(inputData->getKey(i));
				p = inputData->getValue(i);
				q = qData->getValue(j);
				if (p > 0 && q > 0)
					t += p * log (p/q);
			}
			t/= log(2.0);
			return t;
		}

		void correctOriginTerms()
		{
			double q;
			double originTerm = ((double)(originTerms-1)) / fullDimension;
			for (long i = 0; i < qData->getTupleCount(); i++) {
				q = qData->getValue(i);
				q -= originTerm;
				qData->setValue(i, q);
			}
		}

		ocTable *qData, *inputData;
		double fullDimension;
		int keysize;
		int relCount;
		int originTerms;
	};

	static BPIntersectProcessor *processor = NULL;

	ocAttributeList *attrs = model->getAttributeList();

	//-- see if we did this already.
	double modelT = attrs->getAttribute(ATTRIBUTE_BP_T);
	if (modelT >= 0) return modelT;

	double fullDimension = ocDegreesOfFreedom(topRef->getRelation(0)) + 1;

	//-- because we clear the cache periodically, we have to force
	//-- creation of all projections here
	long relCount = model->getRelationCount();
	long r;
	class ocRelation *rel;
	for (r = 0; r < relCount; r++) {
	  rel = model->getRelation(r);
	  ocManagerBase::makeProjection(rel);
	}

	if (processor == NULL) processor = new BPIntersectProcessor(inputData, fullDimension);
	processor->reset(relCount);
	doIntersectionProcessing(model, processor);
	modelT = processor->getTransmission();
	attrs->setAttribute(ATTRIBUTE_BP_T, modelT);
	return modelT;
}

void ocVBMManager::computeBPStatistics(ocModel *model)
{
	ocAttributeList *attrs = model->getAttributeList();
	double modelT = computeBPT(model);
	double topH = computeH(topRef);
	//-- we need both BP and standard T for the bottom model
	double botBPT = computeBPT(bottomRef);
	double botStdT = computeTransmission(bottomRef);
	//-- estimate H by scaling the standard T of the bottom model, proportionately
	//-- with the BP_T of the model and the bottom model
	double modelH = topH + modelT * botStdT / botBPT;

	attrs->setAttribute(ATTRIBUTE_BP_H, modelH);

	double info = modelT / botBPT;
	// info is normalized but may not quite be between zero and 1 due to
	// roundoff. Fix this here.
	if (info <= 0.0) info = 0.0;
	if (info >= 1.0) info = 1.0;
	attrs->setAttribute(ATTRIBUTE_BP_EXPLAINED_I, 1.0 - info);
	attrs->setAttribute(ATTRIBUTE_BP_UNEXPLAINED_I, info);

	//-- make sure the other attributes are there
	computeDFStatistics(model);
	//-- compute chi-squared statistics and related statistics. L2 = 2*n*sum(p(ln p/q))
	//-- which is 2*n*ln(2)*T
	int errcode;
	double modelL2 = 2.0 * M_LN2 * sampleSize * modelT;
	double refT = computeBPT(refModel);
	double refL2 = 2.0 * M_LN2 * sampleSize * refT;
	double refModelL2 = refL2 - modelL2;
	double modelDF = computeDF(model);
	double refDF = computeDF(refModel);
	double refDDF = modelDF - refDF;

	//-- depending on the relative position of the reference model and the
	//-- current model in the hierarchy, refDDF may be positive or negative
	//-- as may refModel2. But the signs should be the same. If they aren't,
	//-- the csa computation will fail.
	if (refDDF < 0) {
		refDDF = -refDDF;
		refModelL2 = - refModelL2;
	}

	//-- eliminate negative value due to small roundoff
	if (refModelL2 <= 0.0) refModelL2 = 0.0;

	double refL2Prob = csa(refModelL2, refDDF);

	double critX2=0, refL2Power=0;

	errcode = 0;
	double alpha;
	if (!getOptionFloat("palpha", NULL, &alpha)) alpha = 0.0;
	if (alpha > 0) critX2 = ppchi(alpha, refDDF, &errcode);
	else critX2 = refModelL2;
	if (errcode) printf("ppchi: errcode=%d\n", errcode);
	refL2Power = 1.0 - chin2(critX2, refDDF, refModelL2, &errcode);


	//?? do something with these returned errors
	attrs->setAttribute(ATTRIBUTE_DDF, refDDF);
	attrs->setAttribute(ATTRIBUTE_BP_LR, refModelL2);
	attrs->setAttribute(ATTRIBUTE_BP_ALPHA, refL2Prob);
	attrs->setAttribute(ATTRIBUTE_BP_BETA, refL2Power);

	//-- dependent statistics
	if (!getVariableList()->isDirected()) return;	// can only do this for directed models
	double depH = topRef->getRelation(0)->getAttributeList()->getAttribute(ATTRIBUTE_DEP_H);
	double indH = topRef->getRelation(0)->getAttributeList()->getAttribute(ATTRIBUTE_IND_H);
	// for these computations, we need an estimated H which is compatible
	// with the Info-theoretic measures.
	double refH = computeH(bottomRef);
	double refCondH = refH - indH;

	double condH = modelH - indH;

        /************************************************
                calculate BP_AIC & BIC by Junghan
        ************************************************/
        calculateBP_AicBic(model, attrs);

	//	printf("h=%lg, topH=%lg, refH=%lg, modelT=%lg, botT=%lg<br>\n",
	//       h, topH, refH, modelT, botT);
	attrs->setAttribute(ATTRIBUTE_BP_COND_H, condH);
	attrs->setAttribute(ATTRIBUTE_BP_COND_DH, refH - modelH);
	attrs->setAttribute(ATTRIBUTE_BP_COND_PCT_DH, 100 * (refH - modelH) / depH);
}

void ocVBMManager::computePercentCorrect(ocModel *model)
{
	double total;
	long count, i;
	ocRelation *indRel = getIndRelation();
	ocRelation *depRel = getDepRelation();

	//-- if either of these is empty, then we don't have a directed system
	if (indRel == 0 || depRel == 0) return;

	((ocManagerBase*)this)->makeProjection(depRel);

	//-- get default DV probability, which is the largest of the values in the dependent relation
	makeFitTable(model);
	ocTable *modelTable = fitTable1;
	ocTable *maxTable = new ocTable(keysize, modelTable->getTupleCount());
	maxTable = new ocTable(keysize, modelTable->getTupleCount());
	makeMaxProjection(modelTable, maxTable, inputData, indRel, depRel);
	total = 0.0;
	count = maxTable->getTupleCount();
	for (i = 0; i < count; i++) {
	  total += maxTable->getValue(i);
	}
	model->getAttributeList()->setAttribute(ATTRIBUTE_PCT_CORRECT_DATA, 100 * total);

	if (testData) {
	  //-- for test data, use projections involving only the predicting variables
	  int maxCount = varList->getVarCount();
	  int varindices[maxCount], varcount;
	  getPredictingVars(model, varindices, varcount, false);
	  ocRelation *predRelNoDV = getRelation(varindices, varcount);
	  getPredictingVars(model, varindices, varcount, true);
	  ocRelation *predRelWithDV = getRelation(varindices, varcount);
	  ocTable *predModelTable = new ocTable(keysize, modelTable->getTupleCount());
	  ocTable *predTestTable = new ocTable(keysize, modelTable->getTupleCount());
	  ocManagerBase::makeProjection(modelTable, predModelTable, predRelWithDV);
	  ocManagerBase::makeProjection(testData, predTestTable, predRelWithDV);
	  maxTable->reset(keysize);
	  makeMaxProjection(predModelTable, maxTable, predTestTable, predRelNoDV, depRel);
	  total = 0.0;
	  // printf("MODEL: %s\n", model->getPrintName());
	  // maxTable->dump(true);
	  count = maxTable->getTupleCount();
	  for (i = 0; i < count; i++) {
	    total += maxTable->getValue(i);
	  }
	  model->getAttributeList()->setAttribute(ATTRIBUTE_PCT_CORRECT_TEST, 100 * total);
	}
	delete maxTable;
}

void ocVBMManager::setFilter(const char *attrname, double attrvalue, RelOp op)
{
	if (filterAttr) delete filterAttr;
	filterAttr = new char[strlen(attrname) + 1];
	strcpy(filterAttr, attrname);
	filterValue = attrvalue;
	filterOp = op;
}

bool ocVBMManager::applyFilter(ocModel *model)
{
	//-- if no filter defined, then it passes
	if (filterAttr == NULL) return true;
	
	//-- make sure require attributes were computed
	computeRelWidth(model);
	computeL2Statistics(model);
	computeDependentStatistics(model);
	
	//-- now apply the test
	double val = model->getAttributeList()->getAttribute(filterAttr);
	switch (filterOp) {
	case LESSTHAN:
		return val < filterValue;
	case EQUALS:
		return fabs(val - filterValue) < OC_COMPARE_EPSILON;
	case GREATERTHAN:
		return val > filterValue;
	default:
		return false;
	}
}

void ocVBMManager::setSortAttr(const char *name)
{
	if (sortAttr) delete sortAttr;
	sortAttr = new char[strlen(name) + 1];
	strcpy(sortAttr, name);
}

static void printRefTable(ocAttributeList *attrs, FILE *fd, const char *ref,
	const char **strings, int rows)
{
	//-- Print general report for a single model, similar to Fit in Occam2
	const char *header, *beginLine, *endLine, *separator, *footer, *headerSep;
	if (ocReport::isHTMLMode()) {
		header = "<table><tr><td>&nbsp;</td></tr>\n";
		beginLine = "<tr><td>";
		separator = "</td><td>";
		endLine = "</td></tr>\n";
		footer = "</table>";
		headerSep = "<tr><td colspan=10><hr></td></tr>\n";
	}
	else {
		header = "\n";
		beginLine = "    ";
		separator = ",";
		endLine = "\n";
		footer = "\n";
		headerSep = 
		"-------------------------------------------------------------------------\n";
	}
	int cols = 3;
	int labelwidth = 20;
	int colwidth = 18;
	int row, col, rowlabel;
	const char *label;
	
	fprintf(fd, header);
	fprintf(fd,"-------------------------------------------------------------------------\n\n");
	fprintf(fd, "\n%sREFERENCE = %s%s", beginLine, ref, endLine);
	label = "Value";
	fprintf(fd, "%s%s%s%s", beginLine, separator, label, separator);
	label = "Prob. (Alpha)";
	fprintf(fd, "%s%s", label, endLine);
	//label = "Power (Beta)";
	//fprintf(fd, "%s%s", label, endLine);
	
	fprintf(fd, headerSep);
	for (row = 0; row < rows; row++) {
		rowlabel = row * cols; 
		fprintf(fd, "%s%s", beginLine, strings[rowlabel]);
		for (col = 1; col < cols; col++) {
			double value = attrs->getAttribute(strings[rowlabel + col]);
			if (value >= 0)
				fprintf(fd, "%s%g", separator, value);
			else
				fprintf(fd, "%s", separator);
		}
		fprintf(fd, endLine);
	}
	fprintf(fd, footer);
	
}
void ocVBMManager::printFitReport(ocModel *model, FILE *fd)
{
	//-- Print general report for a single model, similar to Fit in Occam2
	const char *header, *beginLine, *endLine, *separator, *footer;
	if (ocReport::isHTMLMode()) {
		header = "<table>\n";
		beginLine = "<tr><td>";
		separator = "</td><td>";
		endLine = "</td></tr>\n";
		footer = "</table>";
	}
	else {
		header = "";
		beginLine = "    ";
		separator = ",";
		endLine = "\n";
		footer = "\n";
	}
	bool directed = getVariableList()->isDirected();
	fprintf(fd, header);
	fprintf(fd, "%sModel%s%s%s", beginLine, separator, 
		model->getPrintName(), separator);
	if (directed)
		fprintf(fd, "Directed System%s", endLine);
	else
		fprintf(fd, "Neutral System%s", endLine);
	
	//-- Print relations using long names
	int i, j;
	for (i = 0; i < model->getRelationCount(); i++) {
		fprintf(fd, beginLine);
		ocRelation *rel = model->getRelation(i);
		for (j = 0; j <rel->getVariableCount(); j++) {
			const char *varname = getVariableList()->getVariable(rel->getVariable(j))->name;
			if (j > 0) fprintf(fd, ", ");
			fprintf(fd, varname);
		}
		fprintf(fd, endLine);
	}
	
	//-- Print some general stuff
	int cwid = 40;
	const char *label;
	double value;

	label = "Sample size:";
	fprintf(fd, "%s%s%s%d%s", beginLine, label, separator, sampleSize, endLine);
	label = "Number of cells:";
	value = topRef->getAttributeList()->getAttribute("df") + 1;
	fprintf(fd, "%s%s%s%g%s", beginLine, label, separator, value, endLine);
	label = "Degrees of Freedom (DF):";
	value = model->getAttributeList()->getAttribute("df");
	fprintf(fd, "%s%s%s%g%s", beginLine, label, separator, value, endLine);
	label = "Loops:";
	value = model->getAttributeList()->getAttribute("h");
	fprintf(fd, "%s%s%s%s%s", beginLine, label, separator,
		value > 0 ? "YES" : "NO", endLine);
	label = "Entropy(H):";
	value = model->getAttributeList()->getAttribute("h");
	fprintf(fd, "%s%s%s%g%s", beginLine, label, separator, value, endLine);
	label = "Information captured (%):";
	value = model->getAttributeList()->getAttribute("information") * 100.0;
	fprintf(fd, "%s%s%s%g%s", beginLine, label, separator, value, endLine);
	label = "Transmission (T):";
	value = model->getAttributeList()->getAttribute("t");
	fprintf(fd, "%s%s%s%g%s", beginLine, label, separator, value, endLine);
	fprintf(fd, footer);
	//-- print top and bottom reference tables
	const char *topFields[] = {
		"Log-Likelihood (LR)", ATTRIBUTE_LR, ATTRIBUTE_ALPHA, ATTRIBUTE_BETA,
		"Pearson X2", ATTRIBUTE_P2, ATTRIBUTE_P2_ALPHA, ATTRIBUTE_P2_BETA,
		"Delta DF (dDF)", ATTRIBUTE_DDF, "", "",
	};
	const char *bottomFields[] = {
		"Log-Likelihood (LR)", ATTRIBUTE_LR, ATTRIBUTE_ALPHA, ATTRIBUTE_BETA,
		"Pearson X2", ATTRIBUTE_P2, ATTRIBUTE_P2_ALPHA, ATTRIBUTE_P2_BETA,
		"Delta DF (dDF)", ATTRIBUTE_DDF, "", "",
	};
	const char *topFields1[] = {
		"Log-Likelihood (LR)", ATTRIBUTE_LR, ATTRIBUTE_ALPHA, 
		"Pearson X2", ATTRIBUTE_P2, ATTRIBUTE_P2_ALPHA, 
		"Delta DF (dDF)", ATTRIBUTE_DDF, "", 
	};
	const char *bottomFields1[] = {
		"Log-Likelihood (LR)", ATTRIBUTE_LR, ATTRIBUTE_ALPHA, 
		"Pearson X2", ATTRIBUTE_P2, ATTRIBUTE_P2_ALPHA, 
		"Delta DF (dDF)", ATTRIBUTE_DDF, "",
	};
	//-- compute attributes for top and bottom references
	model->getAttributeList()->reset();
	setRefModel("top");
	computeInformationStatistics(model);
	computeDependentStatistics(model);
	computeL2Statistics(model);
	computePearsonStatistics(model);

	printRefTable(model->getAttributeList(), fd, "TOP", topFields1, 3);
	model->getAttributeList()->reset();
	setRefModel("bottom");
	computeInformationStatistics(model);
	computeDependentStatistics(model);
	computeL2Statistics(model);
	computePearsonStatistics(model);
	printRefTable(model->getAttributeList(), fd, "BOTTOM", bottomFields1, 3);
	fprintf(fd,"-------------------------------------------------------------------------\n\n");
}

void ocVBMManager::printBasicStatistics()
{
	const char *header, *beginLine, *endLine, *separator, *footer;
	double h;
	if (ocReport::isHTMLMode()) {
		header = "<table width=\"30%\">\n";
		beginLine = "<tr><td>";
		separator = "</td><td>";
		endLine = "</td></tr>\n";
		footer = "</table>";
	}
	else {
		header = "";
		beginLine = "    ";
		separator = ",";
		endLine = "";
		footer = "\n";
	}
	bool directed = getVariableList()->isDirected();
	printf("%s\n", header);
	double topH = computeH(topRef);
	printf("%s%s%s%lg%s\n", beginLine, "H(data)", separator, topH, endLine);
	double stateSpace = computeDF(getTopRefModel())+1;
        double sampleSz1 = getSampleSz();
	printf("%s%s%s%lg%s\n", beginLine, "State Space Size", separator, stateSpace, endLine);
	printf("%s%s%s%lg%s\n", beginLine, "Sample Size", separator, sampleSz1, endLine);
	if (directed) {
		double depH = topRef->getRelation(0)->getAttributeList()->getAttribute(ATTRIBUTE_DEP_H);
		double indH = topRef->getRelation(0)->getAttributeList()->getAttribute(ATTRIBUTE_IND_H);
		printf("%s%s%s%lg%s\n", beginLine, "H(IV)", separator, indH, endLine);
		printf("%s%s%s%lg%s\n", beginLine, "H(DV)", separator, depH, endLine);
	}
	printf("%s\n", footer);
}

void ocVBMManager::getPredictingVars(ocModel *model,
				      int *varindices, 
				      int &varcount,
				      bool includeDeps)
{
  ocRelation *indRel = getIndRelation();
  ocVariableList *vars = getVariableList();
  varcount = 0;
  for (int r = 0; r < model->getRelationCount(); r++) {
    ocRelation *rel = model->getRelation(r);
    if (rel != indRel) {
      for (int iv = 0; iv < rel->getVariableCount(); iv++) {
	int varid = rel->getVariable(iv);
	if (vars->getVariable(varid)->dv && !includeDeps) continue;
	for (int jv = 0; jv < varcount; jv++) {
	  if (varid == varindices[jv]) {
	    varid = -1;
	    break;
	  }
	}
	if (varid >= 0) varindices[varcount++] = varid;
      }
    }
  }
}
