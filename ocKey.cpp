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
 
 
void ocKey::buildKey(ocKeySegment *key, int keysize, class ocVariableList *vars,
		int *varindices, int *varvalues, int varcount)
{
	int i;
	for (i = 0; i < keysize; i++) key[i] = DONT_CARE;
	for (i = 0; i < varcount; i++) {
		ocVariable *var = vars->getVariable(varindices[i]);
		ocKeySegment mask = var->mask;
		int value = varvalues[i];
		int segment = var->segment;
		assert(value == DONT_CARE || (value >= 0 && value < var->cardinality));
		key[segment] = (key[segment] & ~mask) | ((varvalues[i] << var->shift) & mask);
	}
}

/*
 * build a key with a value for every variable
 */
void ocKey::buildFullKey(ocKeySegment *key, int keysize, class ocVariableList *vars,
		int *varvalues)
{
	int i;
	int varcount = vars->getVarCount();
	for (i = 0; i < keysize; i++) key[i] = DONT_CARE;
	for (i = 0; i < varcount; i++) {
		ocVariable *var = vars->getVariable(i);
		ocKeySegment mask = var->mask;
		int value = varvalues[i];
		int segment = var->segment;
		assert(value == DONT_CARE || (value >= 0 && value < var->cardinality));
		key[segment] = (key[segment] & ~mask) | ((varvalues[i] << var->shift) & mask);
	}
}


/**	
 * setKeyValue - set a single value in a key
 */
void ocKey::setKeyValue(ocKeySegment *key, int keysize, class ocVariableList *vars,
		int index, int value)
{
	ocVariable *var = vars->getVariable(index);
	int segment = var->segment;
	ocKeySegment mask = var->mask;
	assert(value == DONT_CARE || (value >= 0 && value < var->cardinality));
	key[segment] = (key[segment] & ~mask) | ((value << var->shift) & mask);
}


/**
 * compareKeys - compare two keys
 */
int ocKey::compareKeys(ocKeySegment *key1, ocKeySegment *key2, int keysize)
{
	int i;
	for (i = 0; i < keysize; i++) {
		if (*key1 < *key2) return -1;
		if (*key1 > *key2) return 1;
		// equal so far...
		key1++; key2++;
	}
	return 0;
}


/**
 * buildMask - create a key with all 0's in included variables, 1's elsewhere
 */
void ocKey::buildMask(ocKeySegment *mask, int keysize, class ocVariableList *vars,
		int *varindices, int varcount)
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


