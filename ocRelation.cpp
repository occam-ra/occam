/* Copyright 2000, Portland State University Systems Science Program.  All Rights Reserved
 */

/**
 * ocRelation.cpp - implements the Relation class.  A Relation consists of a list
 * of variables (actually, a list of indices of variables in a VariableList).
 */
 
 #include "ocCore.h"
 #include "_ocCore.h"
 #include <assert.h>
 #include <stdio.h>
 #include <stdlib.h>
 #include <string.h>
 
 
ocRelation::ocRelation(ocVariableList *list, int size ,int keysz,int stateconstsz)
{
	varList = list;
	maxVarCount = size;
	varCount = 0;
	vars = new int[size];
	table = NULL;
	if(stateconstsz<=0){
		stateConstraints = NULL;
		states=NULL;
	}else{
		//needs a better keysize value........Anjali
		states=new int[size];
		stateConstraints=new ocStateConstraint(keysz,stateconstsz);
	}
	mask = NULL;
	hashNext = NULL;
	attributeList = new ocAttributeList(8);
	printName = NULL;
}

ocRelation::~ocRelation()
{
	// delete storage.
	if (vars) delete vars;
	if (stateConstraints) delete stateConstraints;
	if (table) delete table;
}

long ocRelation::size()
{
  long size = sizeof(ocRelation);
  if (table) size += table->size();
  if (vars) size += maxVarCount * sizeof(int);
  return size;
}

// adds a variable to the relation
void ocRelation::addVariable(int varindex,int stateind)
{
	const int FACTOR = 2;
	if (varCount >= maxVarCount) {
		vars = (int*) growStorage(vars, maxVarCount*sizeof(int), FACTOR);
		if(stateind>=0 || stateind==DONT_CARE){
			states = (int*) growStorage(states, maxVarCount*sizeof(int), FACTOR);
		}
		maxVarCount *= FACTOR;
	}
	vars[varCount] = varindex;
	if(stateind>=0 || stateind==DONT_CARE){
		states[varCount]=stateind;
	}
	varCount++;
}


// returns the ocVariableList object
ocVariableList *ocRelation::getVariableList()
{
	return varList;
}

// returns the list of variable indices. Function return value is the number of
// variables. maxVarCount is the allocated size of indices.
int ocRelation::copyVariables(int *indices, int maxCount, int skip)
{
	int copycount = 0, i = 0;
	for (i = 0; i < varCount; i++) {
		if (copycount >= maxCount) break;
		if (vars[i] != skip) {
			*(indices++) = vars[i];
			copycount++;
		}
	}
	return copycount;
}

// similar but does not copy variable array.
int *ocRelation::getVariables()
{
	return vars;
}

// returns the list of variable indices for variables not in the relation
// this function assumes the indices are sorted
int ocRelation::copyMissingVariables(int *indices, int maxCount)
{
  int copycount = 0;
  int i, j;
  int missing = 0;
  for (i = 0; i < varCount; i++) {
    int nextPresent = vars[i];
    while (missing < nextPresent) {
      if (copycount >= maxCount) break;
      *(indices++) = missing++;
      copycount++;
    }
    missing = nextPresent + 1;
  }
  return copycount;
}

int ocRelation::getIndependentVariables(int *indices, int maxCount)
{
	int i, pos;
	pos = 0;
	for (i = 0; i < varCount; i++) {
		if (pos >= maxCount) break;
		if (!varList->getVariable(i)->dv) indices[pos++] = i;
	}
	return pos;
}

int ocRelation::getDependentVariables(int *indices, int maxCount)
{
	int i, pos;
	pos = 0;
	for (i = 0; i < varCount; i++) {
		if (pos >= maxCount) break;
		if (varList->getVariable(i)->dv) indices[pos++] = i;
	}
	return pos;
}

// returns a single variable index
int ocRelation::getVariable(int index)
{
	return (index < varCount) ? vars[index] : -1;
}

// find a variable and return its index
int ocRelation::findVariable(int varid)
{
	int i;
	for (i = 0; i < varCount; i++) {
		if (getVariable(i) == varid) return i;
	}
	return -1;
}

// return number of variables in relation
int ocRelation::getVariableCount()
{
	return varCount;
}

// get the size of the expansion of the relation, which is the
// product of cardinalities of missing variables times the
// number of tuples in the projection.
double ocRelation::getExpansionSize()
{
  ocTable * table = getTable();
  if (table == 0) return 0;

  int missing[varCount];
  double size = table->getTupleCount();
  int missingCount = copyMissingVariables(missing, varCount);
  for (int i = 0; i < missingCount; i++) {
    int v = missing[i];
    size *= varList->getVariable(v)->cardinality;
  }
  return size;
    
}	
// sets a pointer to the table in the relation object
void ocRelation::setTable(ocTable *tbl)
{
	table = tbl;
}

// returns a reference to the table for this relation, NULL if none computed yet.
ocTable *ocRelation::getTable()
{
	return table;
}

// deletes projection table
void ocRelation::deleteTable()
{	if (table) {
		delete table;
		table = NULL;
	}
}

// sets/gets the state constraints for the relation
void ocRelation::setStateConstraints(class ocStateConstraint *constraints)
{
	stateConstraints = constraints;
}

ocStateConstraint *ocRelation::getStateConstraints()
{
	return stateConstraints;
}
	
// compare two relations for equality (same set of variables)
int ocRelation::compare(const ocRelation *other)
{
	return ocCompareVariables(varCount, vars, other->varCount, other->vars);
}


// see if one relation contains another. This algorithm assumes the relations
// are sorted
bool ocRelation::contains(const ocRelation *other)
{
	return ocContainsVariables(varCount, vars, other->varCount, other->vars);
}


// see if all variables are independent variables. These relations are not
// decomposed during search
bool ocRelation::isIndOnly()
{
	int i;
	for (i = 0; i < varCount; i++) {
		int vid = getVariable(i);	// position of variable in relation
		if (varList->getVariable(vid)->dv) return false;
	}
	return true;
}

long ocRelation::getNC()
{
	long nc = 1;
	int i;
	for (i = 0; i < varCount; i++) nc *= varList->getVariable(i)->cardinality;
	return nc;
}

void ocRelation::makeMask(ocKeySegment *msk)
{
	int keysize = varList->getKeySize();
	if (mask == NULL) buildMask();
	memcpy(msk, mask, keysize*sizeof(ocKeySegment));
}

ocKeySegment *ocRelation::getMask()
{
	if (mask == NULL) buildMask();
	return mask;
}

static int sortCompare(const void *k1, const void *k2)
{
	return *((int*)k1) - *((int*)k2);
}

void ocRelation::sort(int *vars, int varCount)
{
	qsort(vars, varCount, sizeof(int), sortCompare);
}

void ocRelation::sort()
{
	qsort(vars, varCount, sizeof(int), sortCompare);
}

const char* ocRelation::getPrintName()
{
	if (printName == NULL) {
		int maxlength=0;
		if(stateConstraints!=NULL)
			maxlength = varList->getPrintLength(varCount, vars,true);
		else
				
			maxlength = varList->getPrintLength(varCount, vars);
		if (maxlength < 40) maxlength = 40;	//??String allocation bug?
		printName = new char[maxlength+1];
		if(states==NULL)
			varList->getPrintName(printName, maxlength, varCount, vars);
		else
			varList->getPrintName(printName, maxlength, varCount, vars,states);
	}
	return printName;
}
	
double ocRelation::getMatchingTupleValue(ocKeySegment *key)
{
	double value;
	ocTable *table = getTable();
	if (table == NULL) return 0;	// so we don't crash if no projection table
	//-- get the mask, which has 0's in the positions of variables of this relation,
	//-- and 1's elsewhere.
	ocKeySegment *mask = getMask();
	
	//-- make a new empty key
	long keysize = getKeySize();
	ocKeySegment newKey[keysize];
	
	//-- fill the key with the input key, masking off variables we don't care about.
	for (int i = 0; i < keysize; i++) {
		newKey[i] = key[i] | mask[i];
	}
	
	//-- now look up this key in our table, and return the value if present
	int j = table->indexOf(newKey);
	if (j >= 0) value = table->getValue(j);
	else value = 0;
	return value;
}

void ocRelation::buildMask()
{
	int keysize = varList->getKeySize();
	mask = new ocKeySegment[keysize];
	ocKey::buildMask(mask, keysize, varList, vars, varCount);	
}

// dump data to stdout
void ocRelation::dump()
{
	printf("Relation: %s\n", getPrintName());
	if (getTable()) {
		getTable()->dump(false);
	}
	getAttributeList()->dump();
}


