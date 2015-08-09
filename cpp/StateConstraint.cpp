#include "StateConstraint.h"
#include "_Core.h"
#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

/**
 * StateConstraint.cpp - implements a state constraint object, which is
 * a list of variable keys which define certain cells to be constrained.
 * This is used in state-based modeling, to specify in a relation which
 * of the cells have fixed values.
 *
 */

#define keyAddr(index) (constraints + (keysize * index))

StateConstraint::StateConstraint(int keysz, long size)
{
    keysize = keysz;
    maxConstraintCount = size;
    if (maxConstraintCount == 0) maxConstraintCount = 1;
    constraintCount = 0;
    constraints = new KeySegment[keysize * maxConstraintCount];
}


StateConstraint::~StateConstraint()
{
    // delete storage
    delete[] constraints;
}


// add a constraint.
void StateConstraint::addConstraint(KeySegment *key)
{
    const int FACTOR = 2;
    while (constraintCount >= maxConstraintCount) {
        constraints = (KeySegment*) growStorage(constraints, keysize*maxConstraintCount*sizeof(KeySegment), FACTOR);
        maxConstraintCount *= FACTOR;
    }
    KeySegment *addr = keyAddr(constraintCount);	// get the address of the next key
    memcpy(addr, key, keysize*sizeof(KeySegment)); // and copy the new one
    constraintCount++;
}


// get the number of constraints in the list
long StateConstraint::getConstraintCount()
{
    return constraintCount;
}


// retrieve a constraint, given the index (0 .. constraintCount-1)
KeySegment *StateConstraint::getConstraint(long index)
{
    return (index < constraintCount) ? keyAddr(index) : NULL;
}


// get the key size for this constraint table
int StateConstraint::getKeySize()
{
    return keysize;
}


