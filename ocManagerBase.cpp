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
#include "ocWin32.h"

const int defaultRelSize = 10;

#define LOG_PROJECTIONS
#ifdef LOG_PROJECTIONS

static FILE *projfd = NULL;
void logProjection(const char *name)
{
  if (projfd == NULL) projfd = fopen("projections.log", "w");
  fprintf(projfd, "%s\n", name);
  fflush(projfd);
}

#else

void logProjection(const char *name)
{
}

#endif

ocManagerBase::ocManagerBase(ocVariableList *vars, ocTable *input)
	: varList(vars), inputData(input), keysize(vars ? vars->getKeySize() : 0)
{
	relCache = new ocRelCache;
	modelCache = new ocModelCache;
	sampleSize = 0;
	options = new ocOptions();
	inputH = -1;
	stateSpaceSize = 0;
	fitTable1 = fitTable2 = projTable = NULL;
	inputData = testData = NULL;
}

bool ocManagerBase::initFromCommandLine(int argc, char **argv)
{
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
		}
		else if (!ocReadFile(fd, options, &input, &test, &vars)) {
			printf("ERROR: ocReadFile() failed for %s\n", fname);
			return false;
		}
	}
	sampleSize = input->normalize();
	if (test) test->normalize();
	//-- DEBUG
	// options->write(stdout);
	// vars->dump();
	// input->dump();
	
	varList = vars;
	inputData = input;
	testData = test;
	inputH = ocEntropy(inputData);
	keysize = vars->getKeySize();
	return true;
}

ocManagerBase::~ocManagerBase()
{
//	if (varList) delete varList;
//	if (inputData) delete inputData;
}

//-- look in relCache and, if not found, make a new relation and store in relCache
ocRelation *ocManagerBase::getRelation(int *varindices, int varcount, bool makeProject)
{
	ocRelation::sort(varindices, varcount);
	int keysize = getKeySize();
	ocKeySegment *mask = new ocKeySegment[keysize];
	ocKey::buildMask(mask, keysize, varList, varindices, varcount);
	ocRelation *rel = relCache->findRelation(mask, keysize);
	if (rel == NULL) {
		rel = new ocRelation(varList, defaultRelSize);
		for (int i = 0; i < varcount; i++) {
			rel->addVariable(varindices[i]);
		}
		relCache->addRelation(rel);
	}
	if (makeProject) makeProjection(rel);
	delete mask;
	return rel;
}


ocRelation *ocManagerBase::getChildRelation(ocRelation *rel, int skip, bool makeProject)
{
	int order = rel->getVariableCount();
	int *varindices = new int[order];
	int slot = 0;
	ocRelation *newRel = NULL;
	for (int i = 0; i < order; i++) {
		//-- build a list of all variables but skip
		if (i != skip) varindices[slot++] = rel->getVariable(i);
	}
	//-- build and cache the relation
	newRel = getRelation(varindices, order-1, makeProject);
	delete varindices;
	return newRel;
}

bool ocManagerBase::makeProjection(ocRelation *rel)
{
	//-- create the projection data for a given relation. Go through
	//-- the inputData, and for each tuple, sum it into the table for
	//-- the relation.
	const long START_SIZE = 256;
	double totalP = 0;

	if (rel->getTable()) return true;	// table already computed
	logProjection(rel->getPrintName());
	ocTable *table = new ocTable(keysize, START_SIZE);
	rel->setTable(table);
	long count = inputData->getTupleCount();
	ocKeySegment *key = new ocKeySegment[keysize];
	ocKeySegment *mask = rel->getMask();
	long i, k;
	for (i = 0; i < count; i++) {
		inputData->copyKey(i, key);
		double value = inputData->getValue(i);
		//-- set all the variables in the key to don't care if they don't
		//-- exist in the relation
		for (k = 0; k < keysize; k++) key[k] |= mask[k];
		table->sumTuple(key, value);
		totalP += value;
	}
	table->sort();
	delete [] key;
	return true;
}


bool ocManagerBase::makeProjection(ocTable *t1, ocTable *t2, ocRelation *rel)
{
	//-- create the projection data for a given relation. Go through
	//-- the inputData, and for each tuple, sum it into the table for
	//-- the relation.
	long count = t1->getTupleCount();
	t2->reset(keysize);	// reset the output table
	ocKeySegment *key = new ocKeySegment[keysize];
	ocKeySegment *mask = rel->getMask();
	long i, k;
	double totalP;
	for (i = 0; i < count; i++) {
		t1->copyKey(i, key);
		double value = t1->getValue(i);
		//-- set all the variables in the key to don't care if they don't
		//-- exist in the relation
		for (k = 0; k < keysize; k++) key[k] |= mask[k];
		t2->sumTuple(key, value);
		totalP += value;
	}
	t2->sort();
	delete [] key;
	return true;
}

bool ocManagerBase::makeMaxProjection(ocTable *qt, ocTable *maxpt, ocTable *inputData, ocRelation *rel)
{
	//-- create the max projection data for the IV relation, used for computing percent correct.
	//-- Two new tables are created. maxpqt contains a tuple for each distinct IV state,
	//-- and the q value from the qt table. maxpt contains a corresponding tuple for each distinct
	//-- IV state, and the p value (from the input data).
	//-- A pass is made through the the qt table, and for each tuple, it is checked against the
	//-- maxqt table. If it has not been added yet, or if its q value is greater than the value
	//-- already present on the matching tuple in maxqt, then both the maxqt tuple and the maxpt
	//-- tuples are updated. At the end, maxpt has a tuple for each IV state, and the p value
	//-- for the specific IV,DV state which corresponds to the greatest q value across the DV
	//-- states for that IV state.
	if (qt == NULL || maxpt == NULL || rel == NULL) return false;
	long count = qt->getTupleCount();
	ocTable *maxqt = new ocTable(keysize, count);
	maxpt->reset(keysize);	// reset the output table
	ocKeySegment *key = new ocKeySegment[keysize];
	ocKeySegment *mask = rel->getMask();
	long i, k;
	double totalP;
	for (i = 0; i < count; i++) {
		qt->copyKey(i, key);
		double qvalue = qt->getValue(i);
		long pindex = inputData->indexOf(key);
		double pvalue = 0.0;
		if (pindex >= 0) pvalue = inputData->getValue(pindex);
		//-- set up key to match just IVs
		for (k = 0; k < keysize; k++) key[k] |= mask[k];
		long maxqindex = maxqt->indexOf(key);
		long maxpindex = maxpt->indexOf(key);
		if (maxqindex >= 0 && maxpindex >= 0) {
			//-- we already saw this IV state; see if the q value is greater
			double maxqvalue = maxqt->getValue(maxqindex);
			if (maxqvalue < qvalue) {
				maxqt->setValue(maxqindex, qvalue);
				maxpt->setValue(maxpindex, pvalue);
			}
		}
		else {
			//-- new IV state; add to both tables
			//-- we have to call indexOf again to get the position, then
			//-- do the insert
			maxqindex = maxqt->indexOf(key, false);
			maxqt->insertTuple(key, qvalue, maxqindex);
			maxpindex = maxpt->indexOf(key, false);
			maxpt->insertTuple(key, pvalue, maxpindex);
		}
	}
	maxpt->sort();
	delete [] key;
	delete maxqt;
	return true;
}

bool ocManagerBase::makeProjections(ocModel *model)
{
	//-- create projections for all relations in model
	int count = model->getRelationCount();
	for (int i = 0; i < count; i++) {
		if (!makeProjection(model->getRelation(i))) return false;
	}
	return true;
}

void ocManagerBase::deleteTablesFromCache()
{
	relCache->deleteTables();
}

static bool nextTuple(ocVariableList *varList, int *varvalues)
{
	int varcount = varList->getVarCount();
	// bump the last variable by one; if it overflows, carry to the
	// previous one, etc. Return false if we overflow the whole
	// variable list
	int i = varcount - 1;
	varvalues[i]++;
	while (varvalues[i] >= varList->getVariable(i)->cardinality) {
		if (i == 0) return false;	// overflow
		varvalues[i--] = 0;
		varvalues[i]++;
	}
	return true;
}


bool ocManagerBase::makeFitTable(ocModel *model)
{
	if (model == NULL) return false;
	if (!fitTable1) {
		stateSpaceSize = (long) ocDegreesOfFreedom(varList) + 1;
		fitTable1 = new ocTable(keysize, stateSpaceSize);
	}
	if (!fitTable2) {
		fitTable2 = new ocTable(keysize, stateSpaceSize);
	}
	if (!projTable) {
		projTable = new ocTable(keysize, stateSpaceSize);
	}
	fitTable1->reset(keysize);
	fitTable2->reset(keysize);
	projTable->reset(keysize);
	ocKeySegment *key = new ocKeySegment[keysize];
	int i, j, k;
	double error = 0, totalP = 0.0;

	//-- make sure we have projections for all relations
	for (int r = 0; r < model->getRelationCount(); r++) {
		makeProjection(model->getRelation(r));
	}


	//-- configurable fitting parameters
	//-- convergence error. This is approximately in units of samples.
	//-- if initial data was probabilities, an artificial scale of 1000 is used
	double delta2;
	if (!getOptionFloat("ipf-maxdev", NULL, &delta2)) delta2 = .25;
	if (this->sampleSize > 0) delta2 /= sampleSize;
	else delta2 /= 1000;

	double maxiter;
	if (!getOptionFloat("ipf-maxit", NULL, &maxiter)) maxiter = 266;
	int iter;
	for (iter = 0; iter < maxiter; iter++) {
		error = 0.0;		// abs difference between original proj and computed values
		for (int r = 0; r < model->getRelationCount(); r++) {
			ocRelation *rel = model->getRelation(r);
			ocKeySegment *mask = rel->getMask();
			//-- First time special case, to get things started
			if (iter == 0 && r == 0) {
				//-- find out how many cells are projected together by this
				//-- relation; i.e., cells in the input space / cells in the
				//-- projection. This is used in place of the projection sum
				//-- for the first pass.
			#if 1
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
			#else
				fitTable1->copy(inputData);
				int inputCells = fitTable1->getTupleCount();
				double cellWeight = 1.0 / inputCells;
				for(i = 0; i < inputCells; i++) {
					fitTable1->setValue(i, cellWeight);
				}
			#endif
			}
			// create a projection of the computed data, based on the
			// variables in the relation
			projTable->reset(keysize);
			makeProjection(fitTable1, projTable, rel);
			ocTable *relp = rel->getTable();
			// for each tuple in fitTable1, create a scaled tuple in fitTable2, scaled by the
			// ratio of the projection from the input data, and the computed projection
			// from the previous iteration.  In any cases where the input marginal is
			// zero, or where the computed marginal is 0, skip this tuple (equivalent
			// to setting it to zero, but conserves space).
			long tupleCount = fitTable1->getTupleCount();
			fitTable2->reset(keysize);
			totalP = 0.0;
			for (i = 0; i < tupleCount; i++) {
				double newValue = 0.0;
				fitTable1->copyKey(i, key);
				double value = fitTable1->getValue(i);
				for (k = 0; k < keysize; k++) key[k] |= mask[k];
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
						}
						else error = fmax(error, relvalue);
					}
				}
				else {
				}
				if (newValue > 0) {
					fitTable1->copyKey(i, key);
					fitTable2->addTuple(key, newValue);
					totalP += newValue;
				}
			}
			// swap fitTable1 and fitTable2 for next pass
			ocTable *ftswap = fitTable1;
			fitTable1 = fitTable2;
			fitTable2 = ftswap;
		}
		// check convergence
		if (error < delta2) break;
	}
	fitTable1->sort();
	model->getAttributeList()->setAttribute(ATTRIBUTE_IPF_ITERATIONS, (double) iter);
	model->getAttributeList()->setAttribute(ATTRIBUTE_IPF_ERROR, error);
		// printf("model %s, iterations=%d, error=%lg, delta2=%lg\n", model->getPrintName(),
		// iter, error, delta2);
	return true;
}

bool ocManagerBase::hasLoops(ocModel *model)
{	
	bool loops;
	ocAttributeList *attrs = model->getAttributeList();
	double dloops = attrs->getAttribute(ATTRIBUTE_LOOPS);
	if (dloops < 0) {	// -1 = not set, 1 = true, 0 = false
		loops = ocHasLoops(model);
		attrs->setAttribute(ATTRIBUTE_LOOPS, loops ? 1 : 0);
	}
	else {
		loops = (dloops > 0);
	}
	return loops;
}

double ocManagerBase::computeDF(ocRelation *rel)	// degrees of freedom
{
	double df = -1;
	df = rel->getAttributeList()->getAttribute(ATTRIBUTE_DF);
	if (df < 0.0) {	//-- not set yet
	  df = ::ocDegreesOfFreedom(rel);
	  rel->getAttributeList()->setAttribute(ATTRIBUTE_DF, df);
	}
	return df;
}


double ocManagerBase::computeDF(ocModel *model)
{
	double df = model->getAttributeList()->getAttribute(ATTRIBUTE_DF);
	if (df < 0.0) {	//-- not set yet
	  DFAndEntropy(model);
	  df = model->getAttributeList()->getAttribute(ATTRIBUTE_DF);
	}
	return df;
}


double ocManagerBase::computeH(ocRelation *rel)	// uncertainty
{
	ocTable *table = rel->getTable();
	if (table == NULL) {
		makeProjection(rel);
		table = rel->getTable();
	}
	double h = rel->getAttributeList()->getAttribute(ATTRIBUTE_H);
	if (h < 0) {	//-- not set yet
		h = ocEntropy(table);
		rel->getAttributeList()->setAttribute(ATTRIBUTE_H, h);
	}
	return h;
}


double ocManagerBase::computeH(ocModel *model, HMethod method)
{
	double h;
	bool loops;
	ocAttributeList *attrs = model->getAttributeList();

	if (method == ALGEBRAIC) loops = false;
	else if (method == IPF) loops = true;
	else loops = hasLoops(model);

	//-- for models with loops, compute fitted H value.  There may be
	//-- an H value as well, but this is ignored for models with loops.
	if (loops) {
		h = attrs->getAttribute(ATTRIBUTE_FIT_H);
		if (h < 0) {
			makeFitTable(model);
			h = ocEntropy(fitTable1);
			attrs->setAttribute(ATTRIBUTE_FIT_H, h);
			attrs->setAttribute(ATTRIBUTE_H, h);
		}
	}
	else {
		h = attrs->getAttribute(ATTRIBUTE_ALG_H);
		if (h < 0) {	//-- not set yet
			DFAndEntropy(model);
			h = attrs->getAttribute(ATTRIBUTE_ALG_H);
		}
		attrs->setAttribute(ATTRIBUTE_H, h);
	}
	return h;
}


double ocManagerBase::computeTransmission(ocModel *model, HMethod method)
{
	//-- compute analytically. Krippendorf claims that you
	//-- can't do this for models with loops, but experimental
	//-- comparison indicates that loops don't matter in computing
	//-- this.
	double t;
	bool loops;
	ocAttributeList *attrs = model->getAttributeList();

	if (method == ALGEBRAIC) loops = false;
	else if (method == IPF) loops = true;
	else loops = hasLoops(model);

	//-- for models with loops, compute fitted T = sum(p log(p/q)) value.
//	if (loops) {
//		t = attrs->getAttribute(ATTRIBUTE_FIT_T);
//		if (t < 0) {
//			makeFitTable(model);
//			t = ocTransmission(inputData, fitTable1);
//			attrs->setAttribute(ATTRIBUTE_FIT_T, t);
//			attrs->setAttribute(ATTRIBUTE_T, t);
//		}
//	}
//	else {
		t = attrs->getAttribute(ATTRIBUTE_ALG_T);
		if (t < 0) {	//-- not set yet
			double h = computeH(model);
			t = h - inputH;
			attrs->setAttribute(ATTRIBUTE_ALG_T, t);
			attrs->setAttribute(ATTRIBUTE_T, t);
		}
//	}
	return t;
}

//-- intersect two variable lists, producing a third. returns true if intersection
//-- is not empty, and returns the list and count of common variables
static bool intersect(ocRelation *rel1, ocRelation *rel2,
	int* &var, int &count)
{
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
				if (var == NULL) var = new int[count1];	//this is sure to be large enough
				var[count++] = var1[i];
			}
		}
	}
	return var != NULL;
}

void ocManagerBase::DFAndEntropy(ocModel *model)
{
	struct DFAndHProc : public ocIntersectProcessor {
		double df;
		double h;
		ocManagerBase *manager;
		DFAndHProc(ocManagerBase *mgr) {df = 0; h = 0; manager = mgr; }
		virtual void process(int sign, ocRelation *rel)
		{
			if (rel) {
			  df += sign * manager->computeDF(rel);
			  h += sign * manager->computeH(rel);
			}
		}
	};

	DFAndHProc processor(this);
	doIntersectionProcessing(model, &processor);
	model->getAttributeList()->setAttribute(ATTRIBUTE_DF, processor.df);
	model->getAttributeList()->setAttribute(ATTRIBUTE_ALG_H, processor.h);

}

struct VarIntersect {
	int startIndex; // the highest numbered relation index this intersection term represents
	ocRelation *rel;
	VarIntersect():startIndex(0), rel(NULL) {}
};
static VarIntersect *intersectArray = NULL;
static long intersectMax = 2000;
void ocManagerBase::doIntersectionProcessing(ocModel *model, ocIntersectProcessor *proc)
{
	int intersectCount = 0;

	//-- allocate intersect storage; this grows later if needed
	if (intersectArray == NULL)
		intersectArray = new VarIntersect[intersectMax];
	
	int count = model->getRelationCount();
	ocVariableList *varList = model->getRelation(0)->getVariableList();
	
	ocRelation *rel;
	//-- go through the relations in the model and create VarIntersect entries
	for (int i = 0; i < count; i++) {
		rel = model->getRelation(i);
		if (intersectCount >= intersectMax) {
			intersectArray = (VarIntersect*) growStorage(intersectArray, 
				sizeof(VarIntersect)*intersectMax, 2);
			intersectMax *= 2;
		}
		VarIntersect *intersect = intersectArray + (intersectCount++);
		intersect->rel = rel;
		intersect->startIndex = i;
		proc->process(1, rel);
		//printf("rel=%s, DF=%14.0g, H=%14.8g\n", rel->getPrintName(), computeDF(rel),
		//	computeH(rel));
		//rel->getTable()->dump(strlen(rel->getPrintName()) < 10);
	}
	int levelstart = 0;
	int levelend = intersectCount;
	int level0end = intersectCount;
	int sign = 1;
	
	//-- given the previous level of intersection terms, construct the next level from
	//-- all intersections among the previous level. When an intersection is found, we
	//-- need to check the new intersections. If there is a match, we update its
	//-- include count; if there is no match, we create a new one. This process
	//-- terminates when no new terms have been added.
	while (levelend > levelstart) {
		sign = -sign;
		for (int i = levelstart; i < levelend; i++) {
			for (int j = intersectArray[i].startIndex+1; j < level0end; j++) {
				int *newvars, newcount;
				VarIntersect *ip = intersectArray + i;
				VarIntersect *jp = intersectArray + j;
				if(intersect(ip->rel, jp->rel, newvars, newcount))
				{
					//-- add this intersection term to the DF, and append to list
					if (intersectCount >= intersectMax) {
						intersectArray = (VarIntersect*) growStorage(intersectArray, 
							sizeof(VarIntersect)*intersectMax, 2);
						intersectMax *= 2;
					}
					VarIntersect *newp = intersectArray + (intersectCount++);
					newp->rel = getRelation(newvars, newcount, true);
					newp->startIndex = j;
					proc->process(sign, newp->rel);
					delete [] newvars;
				}
			}
		}
		levelstart = levelend;
		levelend = intersectCount;
	}
}

void ocManagerBase::computeStatistics(ocRelation *rel)
{
	ocAttributeList *attrs = rel->getAttributeList();
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
	attrs->setAttribute(ATTRIBUTE_COND_H, hCond);
	attrs->setAttribute(ATTRIBUTE_COND_DH, hDep != 0.0 ? (hDep - h) / hDep : 0.0);
	attrs->setAttribute(ATTRIBUTE_COND_PCT_DH, hInd != 0.0 ? 100 * (hDep - h) / hInd : 0.0);
	attrs->setAttribute(ATTRIBUTE_IND_H, hInd);
	attrs->setAttribute(ATTRIBUTE_DEP_H, hDep);
	
	//-- get the NC (cartesian product) measures
	double hc = rel->getNC();
	long depNC = depRel->getNC();
	long indNC = indRel->getNC();
	
	//-- get the df measures.
	long df = (depNC - 1) * indNC;
	long ddf = depNC * indNC - (depNC + indNC) - 1;
	double totalLR = ocLR(tupleCount, depNC * indNC, h);
	double indLR = ocLR(tupleCount, indNC, hInd);
	double condLR = totalLR - indLR;
	attrs->setAttribute(ATTRIBUTE_COND_DF, df);
	attrs->setAttribute(ATTRIBUTE_COND_DDF, ddf);
	attrs->setAttribute(ATTRIBUTE_TOTAL_LR, totalLR);
	attrs->setAttribute(ATTRIBUTE_IND_LR, indLR);
	attrs->setAttribute(ATTRIBUTE_COND_LR, condLR);
	
	double l2 = 2.0 * M_LN2 * tupleCount * (hDep - hCond);
	double hCondProb = chic (condLR, df);
	attrs->setAttribute(ATTRIBUTE_COND_H_PROB, hCondProb);
		
}

void ocManagerBase::computeRelWidth(ocModel *model)
{
	//-- relation widths are the min and max number of variables among the relations
	//-- in the model. For directed systems the all-independent relation is not included
	//-- in this. These values are used primarily for filtering and sorting models
	ocAttributeList *attrs = model->getAttributeList();
	if (attrs->getAttribute(ATTRIBUTE_MAX_REL_WIDTH) > 0) return;	// already did this
	long minwidth = 0, maxwidth = 0;
	bool directed = getVariableList()->isDirected();
	long i, relCount = model->getRelationCount();
	for (i = 0; i < relCount; i++) {
		ocRelation *rel = model->getRelation(i);
		if (directed && rel->isIndOnly()) continue;	// skip all-ind relation
		int width = rel->getVariableCount();
		if (maxwidth == 0) {	// first time
			minwidth = maxwidth = width;
		}
		else {
			minwidth = minwidth < width ? minwidth : width;
			maxwidth = maxwidth > width ? maxwidth : width;
		}
	}
	attrs->setAttribute(ATTRIBUTE_MIN_REL_WIDTH, (double) minwidth);
	attrs->setAttribute(ATTRIBUTE_MAX_REL_WIDTH, (double) maxwidth);
}

ocModel *ocManagerBase::makeModel(const char *name, bool makeProject)
{
	ocModel *model = new ocModel(10);
	char *relname = new char[(1 + varList->getMaxAbbrevLen()) * varList->getVarCount()];
	int varcount;
	int *vars = new int[varList->getVarCount()];
	const char *cp = name, *cp2;
	while (cp) {
		cp2 = strchr(cp, ':');
		if (cp2 != NULL) {
			int len = cp2 - cp;
			strncpy(relname, cp, len);
			relname[len] = '\0';
			cp = cp2 + 1;
		}
		else {
			strcpy(relname, cp);
			cp = NULL;
		}
		varcount = varList->getVariableList(relname, vars);
		if (varcount == 0) {
			delete model;
			delete relname;
			delete vars;
			return NULL;	// error in name
		}
		ocRelation *rel = getRelation(vars, varcount, makeProject);
		if (rel == NULL) {
			delete model;
			delete relname;
			delete vars;
			return NULL;	// error in name
		}
		model->addRelation(rel, makeProject);
	}
	delete vars;
	delete relname;

	//-- put it in the cache; return the cached one if present
	ocModelCache *cache = getModelCache();
	if (!cache->addModel(model)) {
		//-- already exists in cache; return that one
		ocModel *cachedModel = cache->findModel(model->getPrintName());
		delete model;
		model = cachedModel;
	}

	return model;
}


void ocManagerBase::printOptions(bool printHTML=false) 
{
	options->write(NULL, printHTML);
}

void ocManagerBase::printSizes()
{
  long size;
  size = relCache->size();
  printf("Size of all Relations in cache: %ld  \n", size); 
  size = modelCache->size();
  printf("Size of all Models in cache: %ld  \n", size); 
}


