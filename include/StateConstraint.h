#ifndef ___StateConstraint
#define ___StateConstraint

#include "Types.h"

/**
 * StateConstraint - defines the set of states (variable combinations) within a relation
 * whose values are fixed.
 */
class StateConstraint {
    public:
        // initialize a set of constraints.  Size is a hint of the number needed
        StateConstraint(int keysize, long size);
        ~StateConstraint();

        // add a constraint.
        void addConstraint(KeySegment *key);

        // get the number of constraints in the list
        long getConstraintCount();

        // retrieve a constraint, given the index (0 .. constraintCount-1)
        KeySegment *getConstraint(long index);

        // get the key size for this constraint table
        int getKeySize();

    private:
        KeySegment *constraints;
        long constraintCount;
        long maxConstraintCount;
        int keysize;
};

#endif
