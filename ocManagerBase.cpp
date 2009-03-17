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
void logProjection(const char *name)
{
}
#endif


ocManagerBase::ocManagerBase(ocVariableList *vars, ocTable *input)
	: varList(vars), inputData(input), keysize(vars ? vars->getKeySize() : 0)
{
	topRef = bottomRef = refModel = NULL;
	relCache = new ocRelCache;
	modelCache = new ocModelCache;
	sampleSize = 0;
	testSampleSize = 0;
	options = new ocOptions();
	inputH = -1;
	stateSpaceSize = 0;
	fitTable1 = fitTable2 = projTable = NULL;
	inputData = testData = NULL;
	DVOrder = NULL;
	useInverseNotation = 0;
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
		else if ((dataLines = ocReadFile(fd, options, &input, &test, &vars)) == 0) {
			printf("ERROR: ocReadFile() failed for %s\n", fname);
			return false;
		}
	}
	sampleSize = input->normalize();
	if (test) testSampleSize = test->normalize();
	//-- DEBUG
	// options->write(stdout);
	// vars->dump();
	//input->dump(true);
	//test->dump(true);
	
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

//Anjali.. 
//this function calculates the number of state constraints imposed by a particular relation which
//has variables as are present in the varindices list and state constraints as present in the
// stateindices list, a state value of -1 implies a dontcare value 

int ocManagerBase::calc_StateConst_sz(int varcount,int *varindices, int *stateindices){
	int size=1;
	ocVariable *var;
	int card=0;
	if(varindices ==NULL || stateindices==NULL)return -1;
	for(int i=0;i<varcount;i++){
		if(stateindices[i]==DONT_CARE){
			var=varList->getVariable(varindices[i]);
			card=var->cardinality;
			size=size*card;
		}
	}
	return size;
}

//--add the constraints for a relation 
int ocManagerBase::addConstraint(int varcount,int *varindices,int *stateindices,int* stateindices_c,ocKeySegment* start1,ocRelation *rel){
	ocVariable *var;
	int keysize = getKeySize();
	int count=varcount-1;
	int card=0;
	//get card
	while(stateindices[count]!=DONT_CARE){	
		count--;	
		if(count<0)return 0;
	}
start:
	var=varList->getVariable(varindices[count]);
	card=var->cardinality;
	if(stateindices_c[count]==(card-1)){
		stateindices_c[count]=0x00;
		count--;
		while(stateindices[count]!=DONT_CARE){	
			count--;	
			if(count<0)return 0;
		}
		goto start;
	}else{
		stateindices_c[count]++;
		ocKey::buildKey(start1,keysize,varList,varindices,stateindices_c,varcount);
		rel->getStateConstraint()->addConstraint(start1);
		addConstraint(varcount,varindices,stateindices,stateindices_c,start1,rel);  
		return 0;
	}
		
}

//-- look in relCache and, if not found, make a new relation and store in relCache
ocRelation *ocManagerBase::getRelation(int *varindices, int varcount, bool makeProject, int *stateindices)
{
	int stateconstsz=0;
	if(stateindices==NULL)
		ocRelation::sort(varindices, varcount);
	int keysize = getKeySize();
	ocRelation *rel=NULL;
	int *stateindices1=new int[varcount];
	ocKeySegment *mask = new ocKeySegment[keysize];
	ocKeySegment *start = new ocKeySegment[keysize];
	ocKey::buildMask(mask, keysize, varList, varindices, varcount);
	ocKey::buildMask(start, keysize, varList, varindices, varcount);
	if(stateindices==NULL) {
		rel = relCache->findRelation(mask, keysize);
	}
	if (rel == NULL) {
		if(stateindices!=0) {
			stateconstsz=calc_StateConst_sz(varcount, varindices, stateindices);
			rel = new ocRelation(varList, defaultRelSize, keysize, stateconstsz);
			for (int i = 0; i < varcount; i++) {
				rel->addVariable(varindices[i],stateindices[i]);
			}
		} else {
			rel = new ocRelation(varList, defaultRelSize);
			for (int i = 0; i < varcount; i++) {
				rel->addVariable(varindices[i]);
			}
		}
		if(stateindices!=0) {
			//make starting constraint
			for(int i = 0; i < varcount; i++) {
				if(stateindices[i] == DONT_CARE) {
					stateindices1[i] = 0x00;
				} else {
					stateindices1[i] = stateindices[i];	
				}
			}
			//build the first constraint and then loop
			ocKey::buildKey(start,keysize,varList,varindices,stateindices1,varcount);
			rel->getStateConstraint()->addConstraint(start);
			addConstraint(varcount,varindices,stateindices,stateindices1, start,rel);
			int c_count = rel->getStateConstraint()->getConstraintCount();
		}		
		if(stateindices == 0) {
			relCache->addRelation(rel);
		}
	}
	if (makeProject) {
		if(stateindices != 0)
			makeProjection(rel, 1);
		else
			makeProjection(rel, 0);
	}
	return rel;
}

// "skip" is the index of the variable in the varList
ocRelation *ocManagerBase::getChildRelation(ocRelation *rel, int skip, bool makeProject)
{
	int order = rel->getVariableCount();
	int *varindices = new int[order];
	int slot = 0;
	ocRelation *newRel = NULL;
	for (int i = 0; i < order; i++) {
		//-- build a list of all variables but skip
		if (rel->getVariable(i) != skip) varindices[slot++] = rel->getVariable(i);
		//if (i != skip) varindices[slot++] = rel->getVariable(i);
	}
	//-- build and cache the relation
	newRel = getRelation(varindices, order-1, makeProject);
	delete varindices;
	return newRel;
}

bool ocManagerBase::makeProjection(ocRelation *rel, int SB)
{
	//-- create the projection data for a given relation. Go through
	//-- the inputData, and for each tuple, sum it into the table for the relation.
	const long START_SIZE = 256;
	double totalP = 0;

	if (rel->getTable()) return true;	// table already computed
	logProjection(rel->getPrintName());
	ocTable *table = new ocTable(keysize, START_SIZE);
	rel->setTable(table);
	long long count = inputData->getTupleCount();
	ocKeySegment *key = new ocKeySegment[keysize];
	ocKeySegment *mask = rel->getMask();
	long long i, k;
	for (i = 0; i < count; i++) {
		int is_match=1;
		inputData->copyKey(i, key);
		double value = inputData->getValue(i);
		//-- set all the variables in the key to don't care if they don't exist in the relation
		if(SB==0){
			for (k = 0; k < keysize; k++) key[k] |= mask[k];
			table->sumTuple(key, value);
			totalP += value;
		}else{
			ocKeySegment *dont_care_k=new ocKeySegment[keysize];	
			for (k = 0; k < keysize; k++) dont_care_k[k] = DONT_CARE;
			// state based, so if the key matches one of the constraints
			// then leave it otherwise make it all dont_care
			for (k = 0; k < keysize; k++) key[k] |= mask[k];
			int c_count=rel->getStateConstraint()->getConstraintCount();
		        for(int j=0;j<c_count;j++){
				is_match=1;
				ocKeySegment *const_k=rel->getStateConstraint()->getConstraint(j);
				for (k = 0; k < keysize; k++){
					if(key[k]!=const_k[k]){		
						is_match=-1;
						break;
					}
				}
				if(is_match==1)break;
			}		
			if(is_match==-1){
				//make a key with all dont care bits to sum up the rest fo the tuples.
				table->sumTuple(dont_care_k, value);
					
			}else if(is_match==1){
				table->sumTuple(key, value);
			}
			totalP += value;
			delete dont_care_k;
		}
	}
	table->sort();
	table->normalize();  // in case of roundoff problems, 
	delete [] key;
	return true;
}


bool ocManagerBase::makeProjection(ocTable *t1, ocTable *t2, ocRelation *rel, int SB)
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
		int is_match=1;
		t1->copyKey(i, key);
		double value = t1->getValue(i);
		//-- set all the variables in the key to don't care if they don't
		//-- exist in the relation
		if(SB==0) {
			for (k = 0; k < keysize; k++) key[k] |= mask[k];
			t2->sumTuple(key, value);
			totalP += value;
		} else {
			ocKeySegment *dont_care_k=new ocKeySegment[keysize];	
			for (k = 0; k < keysize; k++) dont_care_k[k] = DONT_CARE;
			//state based, so if the key matches one of the constraints
			// then leave it otherwise make it all dont_care
			for (k = 0; k < keysize; k++) key[k] |= mask[k];
			int c_count=rel->getStateConstraint()->getConstraintCount();
		        for(int j=0;j<c_count;j++){
				is_match=1;
				ocKeySegment *const_k=rel->getStateConstraint()->getConstraint(j);
				for (k = 0; k < keysize; k++){
					if(key[k]!=const_k[k]){		
						is_match=-1;
						break;
					}
				}
				if(is_match==1)break;
			}		
			if(is_match==-1){
				//make a key with all dont care bits to sum up the rest fo the tuples.
				t2->sumTuple(dont_care_k, value);
					
			}else if(is_match==1){
				t2->sumTuple(key, value);
			}
			totalP += value;
			delete dont_care_k;
		}
	}
	t2->sort();
	delete [] key;
	return true;
}

bool ocManagerBase::makeMaxProjection(ocTable *qt, ocTable *maxpt, ocTable *inputData, ocRelation *indRel, ocRelation *depRel)
{
	//-- create the max projection data for the IV relation, used for computing percent correct.
	//-- Two new tables are created. maxqt contains a tuple for each distinct IV state,
	//-- and the q value from the qt table. maxpt contains a corresponding tuple for each distinct
	//-- IV state, and the p value (from the input data).
	//-- A pass is made through the the qt table, and for each tuple, it is checked against the
	//-- maxqt table. If it has not been added yet, or if its q value is greater than the value
	//-- already present on the matching tuple in maxqt, then both the maxqt tuple and the maxpt
	//-- tuples are updated. At the end, maxpt has a tuple for each IV state, and the p value
	//-- for the specific IV,DV state which corresponds to the greatest q value across the DV
	//-- states for that IV state.
	if (qt == NULL || maxpt == NULL || indRel == NULL || depRel == NULL) return false;
	long long count = qt->getTupleCount();
	ocTable *maxqt = new ocTable(keysize, count);
	ocTable *dvt = new ocTable(keysize, count);
	maxpt->reset(keysize);	// reset the output table
	ocKeySegment *key = new ocKeySegment[keysize];
	ocKeySegment *mask = indRel->getMask();
	long long i, pindex, maxqindex, maxpindex, dvindex;
	int k;
	double totalP, qvalue, pvalue, maxqvalue;
	int qdv, pdv, maxdv;
	int defaultDV = getDefaultDVIndex();
	for (i = 0; i < count; i++) {
		qt->copyKey(i, key);
		qvalue = qt->getValue(i);
		pindex = inputData->indexOf(key);
		pvalue = 0.0;
		if (pindex >= 0) pvalue = inputData->getValue(pindex);
		qdv = ocKey::getKeyValue(key, keysize, varList, varList->getDV());
		//-- set up key to match just IVs
		for (k = 0; k < keysize; k++) key[k] |= mask[k];
		maxqindex = maxqt->indexOf(key);
		maxpindex = maxpt->indexOf(key);
		dvindex = dvt->indexOf(key);
		if (maxqindex >= 0 && maxpindex >= 0) {
			//-- we already saw this IV state; see if the q value is greater
			maxqvalue = maxqt->getValue(maxqindex);
			if (fabs(maxqvalue - qvalue) < DBL_EPSILON) {
				// Break any ties by checking the order of the DV values
				maxdv = (int)dvt->getValue(dvindex);
				if (getDVOrder(qdv) < getDVOrder(maxdv)) {
					maxqt->setValue(maxqindex, qvalue);
					maxpt->setValue(maxpindex, pvalue);
					dvt->setValue(dvindex, (double)qdv);
				}
			} else if (maxqvalue < qvalue) {
				maxqt->setValue(maxqindex, qvalue);
				maxpt->setValue(maxpindex, pvalue);
				dvt->setValue(dvindex, (double)qdv);
			}
		} else {
			//-- new IV state; add to both tables
			//-- we have to call indexOf again to get the position, then do the insert
			maxqt->insertTuple(key, qvalue, maxqt->indexOf(key, false));
			maxpt->insertTuple(key, pvalue, maxpt->indexOf(key, false));
			dvt->insertTuple(key, (double)qdv, dvt->indexOf(key, false));
		}
	}

	//-- Add in entries for the default rule (i.e., if the model doesn't predict
	//-- a DV value for a particular IV, then just use the most likely DV value).
	//-- To do this we go through the inputData and find tuples for which (a) the IV
	//-- state does not exist in maxpt, and (b) where the DV value is the most likely value.
	//-- These are the inputData tuples which are predicted correctly by the default rule.
	//-- Their probabilities need to be accounted for.

	count = inputData->getTupleCount();
	long long index;
	double value;
	for (i = 0; i < count; i++) {
		pdv = ocKey::getKeyValue(inputData->getKey(i), keysize, varList, varList->getDV());
		if (pdv != defaultDV) continue;
		
		inputData->copyKey(i, key);
		for (k = 0; k < keysize; k++) key[k] |= mask[k];
		if (maxpt->indexOf(key) >= 0) continue; //-- model predicts this; don't need default

		//-- add this entry to maxpt; default rule applies
		value = inputData->getValue(i);
		if (value > 0) {
			index = maxpt->indexOf(key, false);
			maxpt->insertTuple(key, value, index);
		}
	}
	maxpt->sort();
	delete [] key;
	delete maxqt;
	return true;
}


int ocManagerBase::getDefaultDVIndex() {
        if (!varList->isDirected()) return NULL;      // can only do this for directed models
	if (DVOrder == NULL) createDVOrder();
	return DVOrder[0];
}


int ocManagerBase::getDVOrder(int index) {
	if (!varList->isDirected()) return NULL;
	if (DVOrder == NULL) createDVOrder();
	int dv_card = varList->getVariable(varList->getDV())->cardinality;
	for (int i=0; i < dv_card; ++i) {
		if(DVOrder[i] == index) return i;
	}
	return NULL;
}


static double *sort_freq;
static ocVariable *sort_dv_var;
int sortDV(const void *d1, const void *d2) {
	int a = *(int*)d1;
	int b = *(int*)d2;
	// Would prefer to use DBL_EPSILON here, but the frequencies we get for DV values (from the bottom reference)
	// are not precise enough for some reason.
	if (fabs(sort_freq[a] - sort_freq[b]) < 1e-10) { return strcmp(sort_dv_var->valmap[a], sort_dv_var->valmap[b]); }
	if (sort_freq[a] > sort_freq[b]) { return -1; }
	if (sort_freq[a] < sort_freq[b]) { return 1; }
	// Put this again, just in case.
	return strcmp(sort_dv_var->valmap[a], sort_dv_var->valmap[b]);
}



void ocManagerBase::createDVOrder() {
	if (!varList->isDirected()) return;
	if (DVOrder != NULL) return;

	sort_dv_var = varList->getVariable(varList->getDV());
	int dv_card = sort_dv_var->cardinality;
	DVOrder = new int[dv_card];
	
	// Build an array of frequencies, taken from the dependent relation (from the bottom reference)
	long long k;
	ocTable *depTable;
	for (k = 0; k < bottomRef->getRelationCount(); ++k) {
		if (!bottomRef->getRelation(k)->isIndOnly()) {
			depTable = bottomRef->getRelation(k)->getTable();
			break;
		}
	}
	sort_freq = new double[dv_card];
	for (k = 0; k < depTable->getTupleCount(); ++k) {
		sort_freq[ocKey::getKeyValue(depTable->getKey(k), keysize, varList, varList->getDV())] = depTable->getValue(k);
	}
	for (int i = 0; i < dv_card; ++i) DVOrder[i] = i;
	qsort(DVOrder, dv_card, sizeof(int), sortDV);
}


void ocManagerBase::getPredictingVars(ocModel *model, int *varindices, int &varcount, bool includeDeps)
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


ocRelation *ocManagerBase::getIndRelation()
{
	if (!getVariableList()->isDirected()) return NULL;      // can only do this for directed models
	int i;
	for (i = 0; i < bottomRef->getRelationCount(); i++) {
		ocRelation *indRel = bottomRef->getRelation(i);
		if (indRel->isIndOnly()) return indRel; // this is the one.
	}
	return NULL;
}


ocRelation *ocManagerBase::getDepRelation()
{
	// This function takes advantage of the fact that the bottom model has only two relations;
	// one is the IV relation, the other is the DV.
	if (!getVariableList()->isDirected()) return NULL;      // can only do this for directed models
	int i;
	for (i = 0; i < bottomRef->getRelationCount(); i++) {
		ocRelation *indRel = bottomRef->getRelation(i);
		if (!indRel->isIndOnly()) return indRel;        // this is the one.
	}
	return NULL;
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

bool ocManagerBase::deleteModelFromCache(ocModel *model)
{
	return modelCache->deleteModel(model);
}

static bool nextTuple(ocVariableList *varList, int *varvalues)
{
	int varcount = varList->getVarCount();
	// bump the last variable by one; if it overflows, carry to the
	// previous one, etc. Return false if we overflow the whole variable list
	int i = varcount - 1;
	varvalues[i]++;
	while (varvalues[i] >= varList->getVariable(i)->cardinality) {
		if (i == 0) return false;	// overflow
		varvalues[i--] = 0;
		varvalues[i]++;
	}
	return true;
}


bool ocManagerBase::makeFitTable(ocModel *model, int SB)
{
	if (model == NULL) return false;
	if (!fitTable1) {
		stateSpaceSize = (unsigned long long) ocDegreesOfFreedom(varList) + 1;
		//-- for large state spaces, start with less space and let it grow.
		if (stateSpaceSize > 1000000) stateSpaceSize = 1000000;
		fitTable1 = new ocTable(keysize, stateSpaceSize);
	}
	if (!fitTable2) {
		if (stateSpaceSize > 1000000) stateSpaceSize = 1000000;
		fitTable2 = new ocTable(keysize, stateSpaceSize);
	}
	if (!projTable) {
		if (stateSpaceSize > 1000000) stateSpaceSize = 1000000;
		projTable = new ocTable(keysize, stateSpaceSize);
	}
	fitTable1->reset(keysize);
	fitTable2->reset(keysize);
	projTable->reset(keysize);
	ocKeySegment *key = new ocKeySegment[keysize];
	int i, j, k;
	double error = 0, totalP = 0.0;

	// for state-based modelling
	ocKeySegment *dont_care_k = new ocKeySegment[keysize];	
	for (k = 0; k < keysize; k++) dont_care_k[k] = DONT_CARE;

	//-- make sure we have projections for all relations
	for (int r = 0; r < model->getRelationCount(); r++) {
		makeProjection(model->getRelation(r),SB);
	}

	//-- compute the number of nonzero tuples in the expansion
	//-- of each relation, and start with the one where this is
	//-- smallest (to minimize memory usage)
	int startRel = 0;
	double expsize = model->getRelation(0)->getExpansionSize();
	for (int r = 1; r < model->getRelationCount(); r++) {
		double newexpsize = model->getRelation(r)->getExpansionSize();
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
	if (!getOptionFloat("ipf-maxdev", NULL, &delta2)) delta2 = .20;
	if (this->sampleSize > 0) delta2 /= sampleSize;
	else delta2 /= 1000;

	double maxiter;
	if (!getOptionFloat("ipf-maxit", NULL, &maxiter)) maxiter = 266;
	int iter;
	for (iter = 0; iter < maxiter; iter++) {
		error = 0.0;		// abs difference between original proj and computed values
		for (int r = 0; r < model->getRelationCount(); r++) {
		  ocRelation *rel = model->getRelation(r);
		  ocTable *relp = rel->getTable();
		  ocKeySegment *mask = rel->getMask();
		  // create a projection of the computed data, based on the variables in the relation
		  projTable->reset(keysize);
		  makeProjection(fitTable1, projTable, rel, SB);
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
		    } else {
		      //printf("came to the else case Sb is %d ****\n",SB);
		      if(SB==1){
			//then probably its the remainder probabilty
			j = relp->indexOf(dont_care_k);
			double relvalue = relp->getValue(j);
			if (relvalue > 0.0) {
			  j = projTable->indexOf(dont_care_k);
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
	delete dont_care_k;
	return true;
}

/**
 * compute the orthogonal expansion of a projection. This means taking every tuple in the projection, and
 * apportioning it evenly across all the states which map into the substate of that projection.
 */
void ocManagerBase::expandTuple(double tupleValue, ocKeySegment *key, int *missingVars, int missingCount, ocTable *outTable, int currentMissingVar)
{
  if (missingCount == 0) {
	outTable->addTuple(key, tupleValue);
  }
  else {
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
      }
      else {
	expandTuple(tupleValue, newKey, missingVars, missingCount, outTable, currentMissingVar);
      }
    }
  }
}


void ocManagerBase::makeOrthoExpansion(ocRelation *rel, ocTable *outTable)
{
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

double ocManagerBase::compute_SB_DF(ocModel *model)
{
	double df = model->getAttributeList()->getAttribute(ATTRIBUTE_DF);
	if (df < 0.0) {	//-- not set yet
		df = ::ocSB_DF(model);
		model->getAttributeList()->setAttribute(ATTRIBUTE_DF,df);
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
	double h = rel->getAttributeList()->getAttribute(ATTRIBUTE_H);
	if (h < 0) {	//-- not set yet
		ocTable *table = rel->getTable();
		if (table == NULL) {
			makeProjection(rel);
			table = rel->getTable();
		}
		h = ocEntropy(table);
		rel->getAttributeList()->setAttribute(ATTRIBUTE_H, h);
	}
	return h;
}


double ocManagerBase::computeH(ocModel *model, HMethod method, int SB)
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
			if(SB)
				makeFitTable(model,SB);
			else
				makeFitTable(model);
			h = ocEntropy(fitTable1);
			attrs->setAttribute(ATTRIBUTE_FIT_H, h);
			attrs->setAttribute(ATTRIBUTE_H, h);
		}
	} else {
		h = attrs->getAttribute(ATTRIBUTE_ALG_H);
		if (h < 0) {	//-- not set yet
			DFAndEntropy(model);
			h = attrs->getAttribute(ATTRIBUTE_ALG_H);
		}
		attrs->setAttribute(ATTRIBUTE_H, h);
	}
	return h;
}


double ocManagerBase::computeTransmission(ocModel *model, HMethod method, int SB)
{
	//-- compute analytically. Krippendorf claims that you
	//-- can't do this for models with loops, but experimental
	//-- comparison indicates that loops don't matter in computing this.
	double t;
	ocAttributeList *attrs = model->getAttributeList();

	t = attrs->getAttribute(ATTRIBUTE_ALG_T);
	if (t < 0) {	//-- not set yet
		double h = 0;

		if (SB) {
			h = computeH(model, IPF, SB);
		} else {
			h = computeH(model);
		}
		t = h - inputH;
		attrs->setAttribute(ATTRIBUTE_ALG_T, t);
		attrs->setAttribute(ATTRIBUTE_T, t);
	}
	return t;
}

//-- intersect two variable lists, producing a third. returns true if intersection
//-- is not empty, and returns the list and count of common variables
static bool intersect(ocRelation *rel1, ocRelation *rel2, int* &var, int &count)
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
	if ((model->getAttributeList()->getAttribute(ATTRIBUTE_DF) < 0) || (model->getAttributeList()->getAttribute(ATTRIBUTE_ALG_H) < 0)) {
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
		while (intersectCount >= intersectMax) {
			intersectArray = (VarIntersect*) growStorage(intersectArray, sizeof(VarIntersect)*intersectMax, 2);
			intersectMax *= 2;
		}
		VarIntersect *intersect = intersectArray + (intersectCount++);
		intersect->rel = rel;
		intersect->startIndex = i;
		proc->process(1, rel);
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
					while (intersectCount >= intersectMax) {
						intersectArray = (VarIntersect*) growStorage(intersectArray, sizeof(VarIntersect)*intersectMax, 2);
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

void ocManagerBase::computeRelWidth(ocModel *model) {
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

ocModel *ocManagerBase::makeModel(const char *name, bool makeProject) {
	ocModel *model = new ocModel(10);
	char *relname = new char[(1 + varList->getMaxAbbrevLen()) * varList->getVarCount()];
	int varcount;
	int *vars = new int[varList->getVarCount()];
	const char *cp = name, *cp2;
	bool atStart = true;
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
		if (varList->isDirected() && (atStart == true) && (strcmp(relname,"IV")==0) ) {
			rel = getChildRelation(getTopRefModel()->getRelation(0), varList->getDV());
		} else {
			varcount = varList->getVariableList(relname, vars);
			if (varcount == 0) {
				delete model;
				delete relname;
				delete vars;
				return NULL;	// error in name
			}
			rel = getRelation(vars, varcount, makeProject);
		}
		if (rel == NULL) {
			delete model;
			delete relname;
			delete vars;
			return NULL;	// error in name
		}
		model->addRelation(rel, makeProject);
		atStart = false;
	}
	delete vars;
	delete relname;

	//-- put it in the cache; return the cached one if present
	//ocModelCache *cache = getModelCache();
	if (!modelCache->addModel(model)) {
		//-- already exists in cache; return that one
		ocModel *cachedModel = modelCache->findModel(model->getPrintName());
		delete model;
		model = cachedModel;
	}

	return model;
}

#define MAXSTATENAME 10
ocModel *ocManagerBase::makeSBModel(const char *name, bool makeProject)
{
        ocModel *model = new ocModel(10);
        char *relname = new char[(1 + varList->getMaxAbbrevLen()) * varList->getVarCount()*2*MAXSTATENAME];
        int varcount;
        int *vars = new int[varList->getVarCount()];
        int *states = new int[varList->getVarCount()];
        const char *cp = name, *cp2;
	bool atStart = true;
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
		//printf("relname is %s\n",relname);
//debug start
		//printf("varcount %d\n",varcount);
		//for(int i=0;i<varcount;i++)
		//printf("varaibel index %d and state index %d\n",vars[i],states[i]);
                if (varList->isDirected() && (atStart == true) && (strcmp(relname,"IV")==0) ) {
                        rel = getChildRelation(getTopRefModel()->getRelation(0), varList->getDV());
			printf("found IV\n");
                } else {
			varcount = varList->getVar_StateList(relname, vars, states);
			if (varcount == 0) {
				delete model;
				delete relname;
				delete vars;
				return NULL;    // error in name
			}
			rel = getRelation(vars, varcount, makeProject, states);
		}
                if (rel == NULL) {
                        delete model;
                        delete relname;
                        delete vars;
                        return NULL;    // error in name
                }
		
                model->addRelation(rel,false);
		atStart = false;
        }
	int StateSpace = (long) ocDegreesOfFreedom(varList) + 1;
	//printf("state space is %d\n",StateSpace);

	make_SS(StateSpace);
	int var_count=varList->getVarCount();
	/*for (int i=0;i<StateSpace;i++){
		for(int j=0;j<var_count;j++){
		printf("%d,",State_Space_Arr[i][j]);
		}
		printf("\n");
	}*/
	model->makeStructMatrix(StateSpace,varList,State_Space_Arr );
	//printf("structure matrix :\n");
	//model->printStructMatrix();
	
        delete vars;
        delete relname;

        return model;
}

void ocManagerBase::make_SS(int statespace){
	int var_count=varList->getVarCount();
	//printf("varcount is %d\n",var_count);
	State_Space_Arr=new int *[statespace];
	int *State_Space_Arr1;
	for(int i=0;i<statespace;i++){
		State_Space_Arr1=new int[var_count];
		State_Space_Arr[i]=State_Space_Arr1;
	}

	for (int i=0;i<statespace;i++){
		for(int j=0;j<var_count;j++){
			State_Space_Arr[i][j]=0;
		}
	}
	for(int k=0;k<var_count;k++){
		State_Space_Arr[0][k]=0;
	}	
	int l=var_count-1;
	int i=0;
	int loop1=0;
	while(i<statespace-1) {
		//first copy from previous state
		for(int j=0;j<var_count;j++){
			State_Space_Arr[i+1][j]=State_Space_Arr[i][j];
		}
rap:
		if(i+1==statespace)break;
		ocVariable *var=varList->getVariable(l);
		int card=var->cardinality;
		if(State_Space_Arr[i][l]==(card-1)) {
			//printf("card is reached \n");
			State_Space_Arr[i+1][l]=0;
			l--;
			if(l<0)break;
			goto rap;
		} else {
			State_Space_Arr[i+1][l]++;
			l=var_count-1;
		}
		i++;
	}
	
}


void ocManagerBase::printOptions(bool printHTML=false) 
{
	options->write(NULL, printHTML);
	if (printHTML) {
		printf("<tr><td>Data Lines Read</td><td>%ld</td></tr>\n", dataLines);
	} else {
		printf("Data Lines Read\t%ld\n", dataLines);
	}
}

void ocManagerBase::printSizes()
{
	long size;
	size = relCache->size();
	printf("Rel-cache: %ld; ", size); 
	size = modelCache->size();
	printf("Model cache: %ld; ", size); 
//	relCache->dump();
	modelCache->dump();
}

void ocManagerBase::dumpRelations()
{
	relCache->dump();
}



