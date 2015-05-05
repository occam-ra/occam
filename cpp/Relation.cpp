/* Copyright 2000, Portland State University Systems Science Program.  All Rights Reserved
 */

/**
 * Relation.cpp - implements the Relation class.  A Relation consists of a list
 * of variables (actually, a list of indices of variables in a VariableList).
 */

#include "Core.h"
#include "_Core.h"
#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

Relation::Relation(VariableList *list, int size, int keysz, long stateconstsz) {
    varList = list;
    maxVarCount = size;
    varCount = 0;
    vars = new int[size];
    table = NULL;
    stateConstraints = NULL;
    states = NULL;
    if (stateconstsz >= 0) {
        //needs a better keysize value........Anjali
        states = new int[size];
        stateConstraints = new StateConstraint(keysz, stateconstsz);
    }
    mask = NULL;
    hashNext = NULL;
    attributeList = new AttributeList(2);
    printName = NULL;
    inverseName = NULL;
    indepOnly = -1;
}

Relation::~Relation() {
    // delete storage.
    delete attributeList;
    if (states)
        delete states;
    if (printName)
        delete printName;
    if (inverseName)
        delete inverseName;
    if (vars)
        delete vars;
    if (stateConstraints)
        delete stateConstraints;
    if (table)
        delete table;
    if (mask)
        delete[] mask;
}

long Relation::size() {
    long size = sizeof(Relation);
    if (table)
        size += table->size();
    if (vars)
        size += maxVarCount * sizeof(int);
    return size;
}

bool Relation::isStateBased() {
    if ((stateConstraints != NULL) || (states != NULL))
        return true;
    else
        return false;
}

// adds a variable to the relation
void Relation::addVariable(int varindex, int stateind) {
    const int FACTOR = 2;
    while (varCount >= maxVarCount) {
        vars = (int*) growStorage(vars, maxVarCount*sizeof(int), FACTOR);
        if (stateind >= 0 || stateind == DONT_CARE) {
            states = (int*) growStorage(states, maxVarCount*sizeof(int), FACTOR);
        }
        maxVarCount *= FACTOR;
    }
    vars[varCount] = varindex;
    if (stateind >= 0 || stateind == DONT_CARE) {
        states[varCount] = stateind;
    }
    varCount++;
}

// returns the VariableList object
VariableList *Relation::getVariableList() {
    return varList;
}

// returns the list of variable indices. Function return value is the number of
// variables. maxVarCount is the allocated size of indices.
int Relation::copyVariables(int *indices, int maxCount, int skip) {
    int copycount = 0, i = 0;
    for (i = 0; i < varCount; i++) {
        if (copycount >= maxCount)
            break;
        if (vars[i] != skip) {
            *(indices++) = vars[i];
            copycount++;
        }
    }
    return copycount;
}

// similar but does not copy variable array.
int *Relation::getVariables() {
    return vars;
}

// returns list of state indices
int *Relation::getStateIndices() {
    return states;
}

// Used to compute the delta-DF between two models, by the method that counts relations.
// The number returned is the product of all included variable's (cardinality - 1).
long long int Relation::getDDFPortion() {
    long int total = 1;
    for (int i = 0; i < varCount; i++) {
        total = total * (varList->getVariable(vars[i])->cardinality - 1);
    }
    return total;
}

// returns the list of variable indices for variables not in the relation
// this function assumes the indices are sorted
int Relation::copyMissingVariables(int *indices, int maxCount) {
    int copycount = 0;
    int i;
    int missing = 0;
    int nextPresent;
    for (i = 0; i < varCount; i++) {
        nextPresent = vars[i];
        while (missing < nextPresent) {
            if (copycount >= maxCount)
                break;
            *(indices++) = missing++;
            copycount++;
        }
        missing = nextPresent + 1;
    }
    while (copycount <= maxCount) {
        if (missing >= varList->getVarCount())
            break;
        *(indices++) = missing++;
        copycount++;
    }
    return copycount;
}

int Relation::getIndependentVariables(int *indices, int maxCount) {
    int i, pos;
    pos = 0;
    for (i = 0; i < varCount; i++) {
        if (pos >= maxCount)
            break;
        if (!varList->getVariable(vars[i])->dv)
            indices[pos++] = vars[i];
    }
    return pos;
}

int Relation::getDependentVariables(int *indices, int maxCount) {
    int i, pos;
    pos = 0;
    for (i = 0; i < varCount; i++) {
        if (pos >= maxCount)
            break;
        if (varList->getVariable(vars[i])->dv)
            indices[pos++] = vars[i];
    }
    return pos;
}

// returns a single variable index
int Relation::getVariable(int index) {
    return (index < varCount) ? vars[index] : -1;
}

// find a variable and return its internal index
int Relation::findVariable(int varid) {
    int i;
    for (i = 0; i < varCount; i++) {
        if (getVariable(i) == varid)
            return i;
    }
    return -1;
}

// return number of variables in relation
int Relation::getVariableCount() {
    return varCount;
}

// get the size of the expansion of the relation, which is the
// product of cardinalities of missing variables times the
// number of tuples in the projection.
double Relation::getExpansionSize() {
    Table * table = getTable();
    if (table == 0)
        return 0;

    int maxCount = getVariableList()->getVarCount();
    int missing[maxCount];
    double size = table->getTupleCount();
    int missingCount = copyMissingVariables(missing, maxCount);
    for (int i = 0; i < missingCount; i++) {
        int v = missing[i];
        size *= varList->getVariable(v)->cardinality;
    }
    return size;

}
// sets a pointer to the table in the relation object
void Relation::setTable(Table *tbl) {
    table = tbl;
}

// returns a reference to the table for this relation, NULL if none computed yet.
Table *Relation::getTable() {
    return table;
}

// deletes projection table
void Relation::deleteTable() {
    if (table) {
        delete table;
        table = NULL;
    }
}

// sets/gets the state constraints for the relation
void Relation::setStateConstraints(class StateConstraint *constraints) {
    stateConstraints = constraints;
}

StateConstraint *Relation::getStateConstraints() {
    return stateConstraints;
}

// compare two relations for equality (same set of variables)
int Relation::compare(Relation *other) {
    int compare = ocCompareVariables(varCount, vars, other->varCount, other->vars);
    if ((compare == 0) && (isStateBased() || other->isStateBased())) {
        return strcmp(getPrintName(), other->getPrintName());
    } else
        return compare;
}

// see if one relation contains another. This algorithm assumes the relations are sorted
bool Relation::contains(Relation *other) {
    if (isStateBased() || other->isStateBased())
        return ocContainsStates(varCount, vars, states, other->varCount, other->vars, other->states);
        // or check if models of rel A & B are equivalent
    else
        return ocContainsVariables(varCount, vars, other->varCount, other->vars);
}

// see if all variables are independent variables. These relations are not decomposed during search
bool Relation::isIndependentOnly() {
    if (indepOnly == 0) {
        return false;
    } else if (indepOnly == 1) {
        return true;
    } else { // it hasn't been determined yet, so do it
        int i;
        int vid;
        for (i = varCount - 1; i >= 0; --i) {
            vid = getVariable(i); // position of variable in relation
            if (varList->getVariable(vid)->dv) {
                indepOnly = 0;
                return false;
            }
        }
        indepOnly = 1;
        return true;
    }
}

bool Relation::isDependentOnly() {
    for (int i = 0; i < varCount; i++) {
        if (varList->getVariable(getVariable(i))->dv == false) {
            return false;
        }
    }
    return true;
}

// get the NC (cartesian product size)
long long Relation::getNC() {
    long long nc = 1;
    int i;
    for (i = 0; i < varCount; i++) {
        nc *= varList->getVariable(vars[i])->cardinality;
    }
    return nc;
}

void Relation::makeMask(KeySegment *msk) {
    int keysize = varList->getKeySize();
    if (mask == NULL)
        buildMask();
    memcpy(msk, mask, keysize * sizeof(KeySegment));
}

KeySegment *Relation::getMask() {
    if (mask == NULL)
        buildMask();
    return mask;
}

static int sortCompare(const void *k1, const void *k2) {
    return *((int*) k1) - *((int*) k2);
}

static int *sorting_vars;
//static int sbSortCompare(void *thunk, const void *k1, const void *k2) {
static int sbSortCompare(const void *k1, const void *k2) {
    //int* vars = (int *) thunk;
    return sorting_vars[*((int *) k1)] - sorting_vars[*((int *) k2)];
}

void Relation::sort(int *vars, int varCount, int *states) {
    if (varCount <= 1) return;
    if (states == NULL) {
        qsort(vars, varCount, sizeof(int), sortCompare);
    } else {
        // when there are states, we must arrange both lists in unison, by the vars values.
        // we do this by sorting an index list based on the vars values, and then arranging
        // both vars & states using the index list afterwards.
        int* order = new int[varCount];
        for (int i = 0; i < varCount; i++)
            order[i] = i;
        // order of args must be changed for qsort_r, and its compare function, from BSD to GNU.
        // last 2 args of qsort_r must be switched, and the thunk moved to the end of compare.
        sorting_vars = vars;
        qsort(order, varCount, sizeof(int), sbSortCompare);
        int *vars_copy = new int[varCount];
        int *states_copy = new int[varCount];
        memcpy(vars_copy, vars, varCount * sizeof(int));
        memcpy(states_copy, states, varCount * sizeof(int));
        for (int i = 0; i < varCount; i++) {
            vars[i] = vars_copy[order[i]];
            states[i] = states_copy[order[i]];
        }
        delete[] states_copy;
        delete[] vars_copy;
        delete[] order;
    }
}

void Relation::sort() {
    sort(vars, varCount, states);
    //qsort(vars, varCount, sizeof(int), sortCompare);
}

void Relation::setAttribute(const char *name, double value) {
    attributeList->setAttribute(name, value);
}

double Relation::getAttribute(const char *name) {
    return attributeList->getAttribute(name);
}

const char* Relation::getPrintName(int useInverse) {
    if (useInverse == 0 || states != NULL) {
        if (printName == NULL) {
            int maxlength = 0;
            maxlength = varList->getPrintLength(varCount, vars, states);
            printName = new char[maxlength + 1];
            varList->getPrintName(printName, maxlength, varCount, vars, states);
        }
        return printName;
    } else {
        if (inverseName == NULL) {
            int *local_vars;
            int local_count;
            int maxlength = 0;
            // make int list to get missing vars
            local_vars = new int[varList->getVarCount()];
            // copy missing vars
            local_count = copyMissingVariables(local_vars, varList->getVarCount());
            maxlength = varList->getPrintLength(local_count, local_vars);
            maxlength += 2; // add 2 for brackets
            if (varList->isDirected()) {
                maxlength += strlen(varList->getVariable(varList->getDV())->abbrev);
            }
            if (maxlength < 40)
                maxlength = 40; //??String allocation bug?
            inverseName = new char[maxlength + 1];
            char *local_name = inverseName + 1;
            varList->getPrintName(local_name, maxlength, local_count, local_vars);

            char *cp = inverseName;
            *cp = '[';
            cp += strlen(inverseName);
            *cp = ']';
            cp++;
            if (varList->isDirected()) {
                const char *dv = varList->getVariable(varList->getDV())->abbrev;
                strcpy(cp, dv);
                cp += strlen(dv);
            }
            *cp = '\0';
        }
        return inverseName;
    }
}

double Relation::getMatchingTupleValue(KeySegment *key) {
    double value;
    Table *table = getTable();
    if (table == NULL)
        return 0; // so we don't crash if no projection table
    //-- get the mask, which has 0's in the positions of variables of this relation,
    //-- and 1's elsewhere.
    KeySegment *mask = getMask();

    //-- make a new empty key
    long keysize = getKeySize();
    KeySegment newKey[keysize];

    //-- fill the key with the input key, masking off variables we don't care about.
    for (int i = 0; i < keysize; i++) {
        newKey[i] = key[i] | mask[i];
    }

    //-- now look up this key in our table, and return the value if present
    int j = table->indexOf(newKey);
    if (j >= 0)
        value = table->getValue(j);
    else
        value = 0;
    return value;
}

void Relation::buildMask() {
    int keysize = varList->getKeySize();
    mask = new KeySegment[keysize];
    Key::buildMask(mask, keysize, varList, vars, varCount);
}

// dump data to stdout
void Relation::dump() {
    printf("\nRelation: %s", getPrintName());
    int keysize = varList->getKeySize();
    printf("\t\tRelation mask: ");
    Key::dumpKey(mask, keysize);
    printf("\n");
    if (states != NULL) {
        printf("\tvars  :");
        for (int i = 0; i < varCount; i++)
            printf(" %d", vars[i]);
        printf("\n");
        printf("\tstates:");
        for (int i = 0; i < varCount; i++)
            printf(" %d", states[i]);
        printf("\n");
    }
    getAttributeList()->dump();
    printf("\n");
    if (getTable()) {
        getTable()->dump(1);
    }
    varList->dump();
    //delete keystr;
}

