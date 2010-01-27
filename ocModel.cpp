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
    attributeList = new ocAttributeList(6);
    printName = NULL;
    inverseName = NULL;
    hashNext = NULL;
    progenitor = NULL;
    ID = 0;
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
    //delete [] relations;
    //relations = new ocRelation*[1];
}


void ocModel::copyRelations(ocModel &model, int skip1, int skip2)
{
    int count = model.getRelationCount();
    for (int i = 0; i < count; i++) {
	ocRelation *rel = model.getRelation(i);
	if (skip1 != i && skip2 != i) addRelation(rel, false);
    }
}


void ocModel::setAttribute(const char *name, double value)
{
    attributeList->setAttribute(name, value);
}


double ocModel::getAttribute(const char *name)
{
    return attributeList->getAttribute(name);
}


//state space array
int * ocModel::get_indicesfromKey(ocKeySegment *key, ocVariableList *vars, int statespace,int **State_Sp_Arr, int *counter){
    int varcount=vars->getVarCount();	
    int *value_l=new int[varcount];
    //maximum number of states that can constrained by a relation
    int *indices=new int[statespace];
    for (int i = 0; i < varcount; i++) {
	ocVariable *var = vars->getVariable(i);
	ocKeySegment mask = var->mask;
	int segment = var->segment;
	int value=0;
	//printf("segment is %d nad key is %x\n",segment,key[segment]);
	ocKeySegment mask1;
	//printf("mask1 is %x and key is %x\n",mask,key[segment]);
	if((mask1=(mask & key[segment]))==mask)value_l[i]=DONT_CARE;
	else{
	    value = (key[segment] & mask) >> var->shift;
	    value_l[i]=value;
	}
	//printf("value for variable %d is %d\n",i,value_l[i]);
    }	
    *counter=0;	
    int not_a_match=-1;
    for(int i=0;i<statespace;i++){
	for(int j=0;j<varcount;j++){
	    if(value_l[j]==DONT_CARE)continue;
	    //printf("state space value %d and value_l %d\n",State_Sp_Arr[i][j],value_l[j]);
	    if(value_l[j]!=State_Sp_Arr[i][j]){
		not_a_match=1;
		break;
	    }else{
		not_a_match=0;
	    }
	}
	//printf("value for match %d\n",not_a_match);
	if(not_a_match==0){
	    //printf("counter value is %d\n",*counter);
	    indices[(*counter)]=i;
	    //printf("indice is %d\n",indices[(*counter)]);
	    (*counter)++;

	}
	not_a_match=-1;

    }
    return indices;
}
//State Based Stucture matrix generation

void ocModel::makeStructMatrix(int statespace,ocVariableList *vars ,int **State_Sp_A){

    int count = getRelationCount();
    int const_count=0;
    int i=0;
    for (i = 0; i < count; i++) {
	ocRelation *rel = getRelation(i);
	ocStateConstraint *sc=rel->getStateConstraints();
	const_count+=sc->getConstraintCount();

    }
    //printf("total no of constraints in the model %d\n",const_count);
    Total_constraints=const_count+1;
    State_Space_sz=statespace;
    structMatrix=new int *[const_count+1];
    int *State_Space_Arr1;
    /* OLD CODE
       for(i=0;i<statespace;i++){
       State_Space_Arr1=new int[statespace];
       structMatrix[i]=State_Space_Arr1;
       }
     */
    /* NEW CODE added */
    for(i=0; i <= const_count; i++){
	State_Space_Arr1 = new int[statespace];
	structMatrix[i] = State_Space_Arr1;
    }
    //printf("count is: %d\n", count);
    //printf("State_Space is: %d\n", statespace);
    //exit(1);
    for(i=0; i < statespace; i++){
	for(int j=0; j < const_count; j++){
	    structMatrix[j][i] = 0;
	}
	//the default constraint
	structMatrix[const_count][i] = 1;
    }
    const_count = 0;
    int T_const_count = 0;
    for (i = 0; i < count; i++) {
	ocRelation *rel = getRelation(i);
	if(rel == NULL){
	    printf("error happenned in file : ocModel.cpp after getRelation\n");
	    exit(1);
	}
	ocStateConstraint *sc=rel->getStateConstraints();
	if(sc == NULL){
	    printf("error happenned in file : ocModel.cpp after getStateConstraints\n");
	    exit(1);
	}
	const_count=sc->getConstraintCount();
	if(const_count <= 0){
	    printf("error happenned in file : ocModel.cpp after getConstraintCount\n");
	    exit(1);
	}
	for(int j=0; j < const_count; j++){
	    ocKeySegment* key = sc->getConstraint(j);	
	    if(key == NULL)
	    {
		printf("error happenned in file : ocModel.cpp after getConstraints\n");
		exit(1);
	    }
	    int counter;
	    int *indices = get_indicesfromKey(key,vars,statespace,State_Sp_A,&counter);			
	    //printf("number of 1s in the constraint %d\n",counter);
	    for(int k=0; k < counter; k++){	
		structMatrix[T_const_count+j][indices[k]] = 1;
	    }
	    //printf("row for %d constraint in %d relation\n",j,i);

	}
	T_const_count += const_count;
    }
}


// get/set relations
void ocModel::addRelation(ocRelation *relation, bool normalize)
{
    const int FACTOR=2;
    int i, j;

    if(relation == NULL) return;

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
	while (relationCount >= maxRelationCount) {
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

	while (relationCount >= maxRelationCount) {
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


// Returns true if this model contains the specified relation; false otherwise.
bool ocModel::containsRelation(ocRelation *relation) {
    for (int i = relationCount -1; i >= 0; --i) {
	//if (relation->compare(relations[i]) == 0)
	if (relations[i]->contains(relation))
	    return true;
    }
    return false;
}


bool ocModel::containsModel(ocModel *child) {
    for (int i = 0; i < child->getRelationCount(); i++) {
	if (!this->containsRelation(child->getRelation(i))) {
	    return false;
	}
    }
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


const char * ocModel::getPrintName(int useInverse)
{
    int i, len = 0;
    const char *name;
    bool isDirected = relations[0]->getVariableList()->isDirected();
    int indOnlyRel = -1;
    if ( (printName == NULL && useInverse == 0) || (inverseName == NULL && useInverse == 1) ) {
	for (i = 0; i < relationCount; i++) {
	    const char *name;
	    //-- for directed systems, figure out which relation is the indOnly one
	    if (isDirected && relations[i]->isIndOnly()) {
		indOnlyRel = i;
		name = "IV";
	    } else {
		name  = relations[i]->getPrintName(useInverse);
	    }
	    len += strlen(name) + 1;
	}
	if (len < 40) len = 40;	//??String allocation bug?
	char *tempName = new char[len+1];
	char *cp = tempName;
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
	    if (cp != tempName) *(cp++) = ':';
	    name = relations[i]->getPrintName(useInverse);
	    strcpy(cp, name);
	    cp += strlen(name);
	}
	*cp = '\0';
	if (useInverse == 0) printName = tempName;
	else inverseName = tempName;
    }
    if (useInverse == 0) return printName;
    else return inverseName;
}


void ocModel::printStructMatrix(){
    int statespace;
    int Total_const;
    int **str_matrix=get_structMatrix(&statespace,&Total_const);
    for(int i=0;i<Total_const;i++){
	for(int j=0;j<statespace;j++){
	    printf("%d,",str_matrix[i][j]);
	}	
	printf("\n");
    }
}	


void ocModel::dump(bool detail)
{
    printf("\tModel: %s\n", getPrintName());
    attributeList->dump();
    printf("\n");
    printf("\t\tSize: %d,\tRelCount: %d,\tMaxRel:%d", size(), getRelationCount(), maxRelationCount);
    if (detail) {
	if (fitTable)
	    printf(",\tFitTable: %d", fitTable->size());
	for (int i = 0; i < relationCount; i++) {
	    relations[i]->dump();
	}
    }
    printf("\n");

}





