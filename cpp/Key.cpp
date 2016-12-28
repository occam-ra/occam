#include "Constants.h"
#include "Key.h"
#include "VariableList.h"
#include "Table.h"
#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>


void Key::buildKey(KeySegment *key, int keysize, class VariableList *vars,
        int *varindices, int *varvalues, int varcount)
{
    int i;
    for (i = 0; i < keysize; i++) key[i] = DONT_CARE;
    for (i = 0; i < varcount; i++) {
        Variable *var = vars->getVariable(varindices[i]);
        KeySegment mask = var->mask;
        int segment = var->segment;
        key[segment] = (key[segment] & ~mask) | ((varvalues[i] << var->shift) & mask);
    }
}


/*
 * build a key with a value for every variable
 */
void Key::buildFullKey(KeySegment *key, int keysize, class VariableList *vars, int *varvalues)
{
    int i;
    int varcount = vars->getVarCount();
    for (i = 0; i < keysize; i++) key[i] = DONT_CARE;
    for (i = 0; i < varcount; i++) {
        Variable *var = vars->getVariable(i);
        KeySegment mask = var->mask;
        int segment = var->segment;
        key[segment] = (key[segment] & ~mask) | ((varvalues[i] << var->shift) & mask);
    }
}


/**	
 * setKeyValue - set a single value in a key
 */
void Key::setKeyValue(KeySegment *key, int keysize, class VariableList *vars, int index, int value)
{
    Variable *var = vars->getVariable(index);
    int segment = var->segment;
    KeySegment mask = var->mask;
    key[segment] = (key[segment] & ~mask) | ((value << var->shift) & mask);
}


/**	
 * getKeyValue - get a single value in a key
 */
int Key::getKeyValue(KeySegment *key, int keysize, class VariableList *vars, int index)
{
    KeySegment temp = 0;
    Variable *var = vars->getVariable(index);
    int segment = var->segment;
    temp = (key[segment] & var->mask); 
    int value = temp >> var->shift;
    return value;
}


/**
 * compareKeys - compare two keys
 */
int Key::compareKeys(KeySegment *key1, KeySegment *key2, int keysize)
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
int Key::copyKey(KeySegment *key1, KeySegment *key2, int keysize)
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
void Key::buildMask(KeySegment *mask, int keysize, class VariableList *vars, int *varindices, int varcount)
{
    //-- start with all DONT_CARE values
    int i;
    for (i = 0; i < keysize; i++) mask[i] = DONT_CARE;

    //-- now set zero's in the slots for this relation

    int count = varcount;
    int var;
    for (i = 0; i < count; i++) {
        var = varindices[i];	// var is index in variableList
        Key::setKeyValue(mask, keysize, vars, var, 0);
    }
}
/**
 * buildMask - create a key with values as specified in states for included variables, 1's elsewhere
 */
/*
   void Key::buildMask(KeySegment *mask, int keysize, class VariableList *vars,
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
Key::setKeyValue(mask, keysize, vars, var, 0);
}
}
 */
/**
 * keyToString - generate printable form
 */
void Key::keyToString(KeySegment *key, VariableList *vars, char *str)
{
    const char *valchars = "0123456789ABCDEF";
    int i;
    int varcount = vars->getVarCount();
    char *cp = str;
    for (i = 0; i < varcount; i++) {
        Variable *var = vars->getVariable(i);
        KeySegment mask = var->mask;
        int segment = var->segment;
        int value = (key[segment] & mask) >> var->shift;
        assert(value >= 0 && value < 16);
        *(cp++) = valchars[value];
    }
    *cp = '\0';
}


void Key::keyToUserString(KeySegment *key, VariableList *vars, char *str)
{
    Key::keyToUserString(key, vars, str, "");
}


void Key::keyToUserString(KeySegment *key, VariableList *vars, char *str, const char *delim, bool showKey)
{
    int i;
    int varcount = vars->getVarCount();
    char *cp = str;
    int dlen = strlen(delim);
    for (i = 0; i < varcount; i++) {
        Variable *var = vars->getVariable(i);
        char **map = var->valmap;
        KeySegment mask = var->mask;
        int segment = var->segment;
        int value = (key[segment] & mask) >> var->shift;
        if(value < (var->cardinality)) {
            //assert(value >= 0 && value < 16);
            if (showKey) {
                int len1 = strlen(map[value]);
                strncpy(cp, map[value], len1);
                cp += len1;
            }
            if (dlen > 0) {
                strncpy(cp, delim, dlen);
                cp += dlen;
            }
        }
    }
    *cp = '\0';
}


void Key::getSiblings(KeySegment *key, VariableList *vars, Table *table, long *i_sibs, int DV_ind, int *no_sib)
{
    int keySize = vars->getKeySize();	
    KeySegment *temp_key = new KeySegment[keySize];
    memcpy((int *)temp_key, (int *)key, keySize * sizeof(long));	
    int j=0;
    Variable *var = vars->getVariable(DV_ind);
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


void Key::dumpKey(KeySegment *key, int keysize)
{
    for (int k = 0; k < keysize; k++) {
        printf("%08lx ", key[k]);
    }
}



