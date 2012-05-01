/* Copyright 2000, Portland State University Systems Science Program.  All Rights Reserved
 */

#include "ocCore.h"
#include "_ocCore.h"
#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

/**
 * ocStateConstraint.cpp - implements a state constraint object, which is
 * a list of variable keys which define certain cells to be constrained.
 * This is used in state-based modeling, to specify in a relation which
 * of the cells have fixed values.
 *
 */

#define keyAddr(index) (constraints + (keysize * index))

ocStateConstraint::ocStateConstraint(int keysz, int size)
{
    keysize = keysz;
    maxConstraintCount = size;
    constraintCount = 0;
    constraints = new ocKeySegment[keysize * maxConstraintCount];
}


ocStateConstraint::~ocStateConstraint()
{
    // delete storage
    delete[] constraints;
}


// add a constraint.
void ocStateConstraint::addConstraint(ocKeySegment *key)
{
    const int FACTOR = 2;
    while (constraintCount >= maxConstraintCount) {
        constraints = (ocKeySegment*) growStorage(constraints, keysize*maxConstraintCount*sizeof(ocKeySegment), FACTOR);
        maxConstraintCount *= FACTOR;
    }
    ocKeySegment *addr = keyAddr(constraintCount);	// get the address of the next key
    memcpy(addr, key, keysize*sizeof(ocKeySegment)); // and copy the new one
    constraintCount++;
}


// get the number of constraints in the list
long ocStateConstraint::getConstraintCount()
{
    return constraintCount;
}


// retrieve a constraint, given the index (0 .. constraintCount-1)
ocKeySegment *ocStateConstraint::getConstraint(int index)
{
    return (index < constraintCount) ? keyAddr(index) : NULL;
}


// get the key size for this constraint table
int ocStateConstraint::getKeySize()
{
    return keysize;
}


