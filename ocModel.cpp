/* Copyright 2000, Portland State University Systems Science Program.  All Rights Reserved
 */

 #include "ocCore.h"
 #include "_ocCore.h"
 #include <assert.h>
 #include <stdio.h>
 #include <stdlib.h>
 #include <string.h>

/**
 * ocModel.cpp - implements the ocModel class.  This represents a model, which is a
 * set of relations (and optionally the set of tables implementing those relations).
 * The model can also store a computed table, which is the fitted table to the source
 * data (e.g., computed via IPF).
 */	

// initialize the model, and allocate storage for the relation pointers.
ocModel::ocModel(int size)
{
	maxRelationCount = size;
	relationCount = 0;
	relations = new ocRelation*[size];
	fitTable = NULL;
	attributeList = new ocAttributeList(8);
	printName = NULL;
	hashNext = NULL;
}
	
ocModel::~ocModel()
{
	// delete storage; this does not cascade to deleting the relations,
	// but does delete the table if any
	if (relations) delete [] relations;
	if (fitTable) delete fitTable;
	if (attributeList) delete attributeList;
}

long ocModel::size()
{
  long size = sizeof(ocModel) + maxRelationCount * sizeof(ocRelation*);
  if (fitTable) size += fitTable->size();
  if (attributeList) size += attributeList->size();
  return size;
}

void ocModel::deleteRelationLinks()
{
  //  delete relations;
  //  relations = NULL;
}

void ocModel::copyRelations(ocModel &model, int skip1, int skip2)
{
	int count = model.getRelationCount();
	for (int i = 0; i < count; i++) {
		ocRelation *rel = model.getRelation(i);
		if (skip1 != i && skip2 != i) addRelation(rel, false);
	}
}

	// get/set relations
void ocModel::addRelation(ocRelation *relation, bool normalize)
{
	const int FACTOR=2;
	int i, j;
	
	//-- if normalize, compare this relation to existing relations
	if (normalize) {
		for (i = 0; i < relationCount; i++) {
			if (relations[i]->contains(relation)) {
				// don't need this one. Assuming caching
				// we don't explicitly delete it since it
				// may be referenced elsewhere.
				return;
			}
			else if (relation->contains(relations[i])) {
				// remove this relation from model
				for (j = i; j < relationCount-1; j++) {
					relations[j] = relations[j+1];
				}
				relationCount--;
				i--; //fix up loop counter since we deleted one
			}
		}
		//-- grow storage if needed
		if (relationCount >= maxRelationCount) {
			relations = (ocRelation**) growStorage(relations, maxRelationCount*sizeof(ocRelation*), FACTOR);
			maxRelationCount *= FACTOR;
		}
		//-- now find the spot for this relation and add it in
		for (i = 0; i < relationCount; i++) {
			if (relation->compare(relations[i]) < 0) break;
		}
		for(j = relationCount; j > i; j--) {
			relations[j] = relations[j-1];
		}
		relations[i] = relation;
		relationCount++;
	}
	else {
		//-- if we know a priori the relations are normalized and in order,
		//-- we can skip all this stuff.
				
		if (relationCount >= maxRelationCount) {
			relations = (ocRelation**) growStorage(relations, maxRelationCount*sizeof(ocRelation*), FACTOR);
			maxRelationCount *= FACTOR;
		}
		relations[relationCount++] = relation;
	}
}


int ocModel::getRelations(ocRelation **rels, int maxRelations)
{
	int count = (relationCount < maxRelations) ? relationCount : maxRelations;
	memcpy(rels, relations, count*sizeof(ocRelation*));
	return count;	
}


ocRelation *ocModel::getRelation(int index)
{
	return (index < relationCount) ? relations[index] : NULL;
}


int ocModel::getRelationCount()
{
	return relationCount;
}


ocTable *ocModel::getFitTable()
{
	return fitTable;
}


void ocModel::setFitTable(ocTable *tbl)
{
	fitTable = tbl;
}

void ocModel::deleteFitTable()
{
	if (fitTable) {
		delete fitTable;
		fitTable = NULL;
	}
}

const char * ocModel::getPrintName()
{
	int i, len = 0;
	const char *name;
	bool isDirected = relations[0]->getVariableList()->isDirected();
	int indOnlyRel = -1;
	if (printName == NULL) {
		for (i = 0; i < relationCount; i++) {
			const char *name;
			//-- for directed systems, figure out which relation is the indOnly one
			if (isDirected && relations[i]->isIndOnly()) {
				indOnlyRel = i;
				name = "IV";
			}
			else {
				name  = relations[i]->getPrintName();
			}
			len += strlen(name) + 1;
		}
		if (len < 40) len = 40;	//??String allocation bug?
		printName = new char[len+1];
		char *cp = printName;
		*cp = '\0';
		
		//-- format the name. For directed systems put the string IV: first, 
		//-- and skip the independent only relation
		if (indOnlyRel >= 0) {
			strcpy(cp, "IV");
			cp += strlen(cp);
		}
		for (i = 0; i < relationCount; i++) {	
			if (i == indOnlyRel) continue;
			// if the string isn't empty, put in a colon separator
			if (cp != printName) *(cp++) = ':';
			name = relations[i]->getPrintName();
			strcpy(cp, name);
			cp += strlen(name);
		}
		*cp = '\0';
	}
	return printName;
}

void ocModel::dump()
{
	printf("Model: %s\n", getPrintName());
	attributeList->dump();
	printf("\n");
}

