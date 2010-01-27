/* Copyright 2000, Portland State University Systems Science Program.  All Rights Reserved
 */

/**
 * ocKey.cpp - implements the Key class. The class contains only static functions,
 * for key manipulation.
 */
 
#include "ocCore.h"
#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>


void ocKey::buildKey(ocKeySegment *key, int keysize, class ocVariableList *vars,
	int *varindices, int *varvalues, int varcount)
{
    int i;
    for (i = 0; i < keysize; i++) key[i] = DONT_CARE;
    for (i = 0; i < varcount; i++) {
	ocVariable *var = vars->getVariable(varindices[i]);
	ocKeySegment mask = var->mask;
	int segment = var->segment;
	key[segment] = (key[segment] & ~mask) | ((varvalues[i] << var->shift) & mask);
    }
}


/*
 * build a key with a value for every variable
 */
void ocKey::buildFullKey(ocKeySegment *key, int keysize, class ocVariableList *vars, int *varvalues)
{
    int i;
    int varcount = vars->getVarCount();
    for (i = 0; i < keysize; i++) key[i] = DONT_CARE;
    for (i = 0; i < varcount; i++) {
	ocVariable *var = vars->getVariable(i);
	ocKeySegment mask = var->mask;
	int segment = var->segment;
	key[segment] = (key[segment] & ~mask) | ((varvalues[i] << var->shift) & mask);
    }
}


/**	
 * setKeyValue - set a single value in a key
 */
void ocKey::setKeyValue(ocKeySegment *key, int keysize, class ocVariableList *vars, int index, int value)
{
    ocVariable *var = vars->getVariable(index);
    int segment = var->segment;
    ocKeySegment mask = var->mask;
    key[segment] = (key[segment] & ~mask) | ((value << var->shift) & mask);
}


/**	
 * getKeyValue - get a single value in a key
 */
int ocKey::getKeyValue(ocKeySegment *key, int keysize, class ocVariableList *vars, int index)
{
    ocKeySegment temp = 0;
    ocVariable *var = vars->getVariable(index);
    int segment = var->segment;
    temp = (key[segment] & var->mask); 
    int value = temp >> var->shift;
    return value;
}


/**
 * compareKeys - compare two keys
 */
int ocKey::compareKeys(ocKeySegment *key1, ocKeySegment *key2, int keysize)
{
    int i;
    for (i = 0; i < keysize; i++) {
	if (*key1 == *key2) {
	    key1++;
	    key2++;
	} else if (*key1 < *key2) {
	    return -1;
	} else { //(*key1 > *key2)
	    return 1;
	}
    }
    return 0;
}


/**
 * copy a key
 */
int ocKey::copyKey(ocKeySegment *key1, ocKeySegment *key2, int keysize)
{
    int i;
    for (i = 0; i < keysize; i++) {
	*(key2++) = *(key1++);
    }
    return 0;   // not sure what this return value was meant to do?
}


/**
 * buildMask - create a key with all 0's in included variables, 1's elsewhere
 */
void ocKey::buildMask(ocKeySegment *mask, int keysize, class ocVariableList *vars, int *varindices, int varcount)
{
    //-- start with all DONT_CARE values
    int i;
    for (i = 0; i < keysize; i++) mask[i] = DONT_CARE;

    //-- now set zero's in the slots for this relation

    int count = varcount;
    int var;
    for (i = 0; i < count; i++) {
	var = varindices[i];	// var is index in variableList
	ocKey::setKeyValue(mask, keysize, vars, var, 0);
    }
}
/**
 * buildMask - create a key with values as specified in states for included variables, 1's elsewhere
 */
/*
   void ocKey::buildMask(ocKeySegment *mask, int keysize, class ocVariableList *vars,
   int *varindices, int varcount, int * states)
   {
//-- start with all DONT_CARE values
int i;
for (i = 0; i < keysize; i++) mask[i] = DONT_CARE;

//-- now set zero's in the slots for this relation

int count = varcount;
int var;
for (i = 0; i < count; i++) {
var = varindices[i];	// var is index in variableList
ocKey::setKeyValue(mask, keysize, vars, var, 0);
}
}
 */
/**
 * keyToString - generate printable form
 */
void ocKey::keyToString(ocKeySegment *key, ocVariableList *vars, char *str)
{
    const char *valchars = "0123456789ABCDEF";
    int i;
    int varcount = vars->getVarCount();
    char *cp = str;
    for (i = 0; i < varcount; i++) {
	ocVariable *var = vars->getVariable(i);
	ocKeySegment mask = var->mask;
	int segment = var->segment;
	int value = (key[segment] & mask) >> var->shift;
	assert(value >= 0 && value < 16);
	*(cp++) = valchars[value];
    }
    *cp = '\0';
}


void ocKey::keyToUserString(ocKeySegment *key, ocVariableList *vars, char *str)
{
    int i;
    int varcount = vars->getVarCount();
    char *cp = str;
    for (i = 0; i < varcount; i++) {
	ocVariable *var = vars->getVariable(i);
	char **map = var->valmap;
	ocKeySegment mask = var->mask;
	int segment = var->segment;
	int value = (key[segment] & mask) >> var->shift;
	if(value < (var->cardinality)) {
	    assert(value >= 0 && value < 16);
	    int len1 = strlen(map[value]);
	    strncpy(cp, map[value], len1);
	    cp += len1;
	}
    }
    *cp = '\0';
}


void ocKey::getSiblings(ocKeySegment *key, ocVariableList *vars, ocTable *table, long *i_sibs, int DV_ind, int *no_sib)
{
    int keySize = vars->getKeySize();	
    ocKeySegment *temp_key = new ocKeySegment[keySize];
    memcpy((int *)temp_key, (int *)key, keySize * sizeof(long));	
    int j=0;
    ocVariable *var = vars->getVariable(DV_ind);
    int card = var->cardinality;

    setKeyValue(temp_key, keySize, vars, DV_ind, 0);
    for(int i=0; i < card; i++) {
	long index = table->indexOf(temp_key);
	if(index > -1) {
	    i_sibs[j++] = index;
	}	
	setKeyValue(temp_key, keySize, vars, DV_ind, i+1);
    }
    delete [] temp_key;
    *no_sib = j;
}
