/*
 * Copyright © 1990 The Portland State University OCCAM Project Team
 * [This program is licensed under the GPL version 3 or later.]
 * Please see the file LICENSE in the source
 * distribution of this software for license terms.
 */

#ifndef ___Relation
#define ___Relation

#include "Table.h"
#include "VariableList.h"

/*
 * Relation - defines a list of variables, and optionally a table which has been
 * constructed based on that relation. A relation can also contain a StateConstraint
 * object, which specifies certain states as being constrained in the relation. If
 * there is no StateConstraint object, then all states are constrained (the normal
 * variable-based modeling case).
 * The variables in a relation are always kept in sorted order.
 */
class Relation {
    public:
        // initializes an empty relation object. The size argument is a hint as to the
        // number of variables to allocate space for (but relations can grow dynamically
        // if needed).
        Relation(VariableList *list = 0, int size = 0, int keysz = 0, long stateconstsz = -1);
        ~Relation();
        long size();

        // returns true if the relation has state constraints, false otherwise
        bool isStateBased();

        // adds a variable to the relation
        // what does this -5 mean??? [jsf]
        void addVariable(int varindex, int stateind = -5);

        // returns the VariableList for this relation
        VariableList *getVariableList();

        // returns the list of variable indices. Function return value is the number of
        // variables. maxVarCount is the allocated size of indices.
        int copyVariables(int *indices, int maxCount, int skip = -1);
        int *getVariables();
        int *getStateIndices();
        long long int getDDFPortion();
        int getIndependentVariables(int *indices, int maxCount);
        int getDependentVariables(int *indices, int maxCount);
        int copyMissingVariables(int *indices, int maxCount);

        // get a single variable from its index
        int getVariable(int index);

        // find a variable and return its index
        int findVariable(int varid);

        // return number of variables in relation
        int getVariableCount();

        // get the size of the orthogonal expansion of the projection
        double getExpansionSize();

        // sets a pointer to the table in the relation object
        void setTable(Table *tbl);

        // returns a reference to the table for this relation, NULL if none computed yet.
        Table *getTable();
        // deletes the projection table to recover storage
        void deleteTable();

        // sets/gets the state constraints for the relation
        void setStateConstraints(class StateConstraint *constraints);
        StateConstraint *getStateConstraints();

        // compare two relations; returns 0 if they are equal (have the same set
        // of variables); otherwise returns -1 or 1 based on lexical comparison
        // of the variable lists
        int compare(Relation *other);
        // int compare(const Relation *other) {return compare(*other);}

        // see if one relation contains another
        bool contains(Relation *other);

        // see if all variables are independent or all dependent
        bool isIndependentOnly();
        bool isDependentOnly();

        // get the NC (cartesian product size)
        long long getNC();

        // create a mask with 1's in the don't care slots, and zeros elsewhere
        // this can be OR'd with a key to set all the don't care slots to DONT_CARE
        // one form of this function copies the key, the other just returns a pointer
        void makeMask(KeySegment *msk);
        KeySegment *getMask();

        // get the key size; a convenience function for getting it from the variable list
        int getKeySize() {
            return varList->getKeySize();
        }

        // sort the variable indices
        void sort();
        static void sort(int *vars, int varcount, int *states = nullptr);

        // set, get hash chain linkages
        Relation *getHashNext() {
            return hashNext;
        }
        void setHashNext(Relation *next) {
            hashNext = next;
        }

        // get the attribute list for the relation
        class AttributeList *getAttributeList() {
            return attributeList;
        }
        void setAttribute(const char *name, double value);
        double getAttribute(const char *name);

        // get a printable name for the relation, using the variable abbreviations
        const char *getPrintName(int useInverse = 0);

        // get a tuple value from the projection table, which matches the key passed in.
        // the key may contain don't cares but must have actual values for all the variables
        // of this relation (otherwise zero is returned).
        double getMatchingTupleValue(KeySegment *key);

        // dump data to stdout
        void dump();

    private:
        void buildMask(); // build the variable mask from the list of variables

        VariableList *varList; // variable list associated with this relation
        int *vars; // array of variable indices
        int *states; //ARRAY OF STATES associated with each
        // variable in the rel,DONT_CARE if no state specified
        int varCount; // number of vars in relation
        int maxVarCount; // size of vars array
        class Table *table;
        class StateConstraint *stateConstraints; // state constraints
        Relation *hashNext; // linkage for storing relations in a hash table
        KeySegment *mask; // mask has zero for variables in this rel, 1's elsewhere
        class AttributeList *attributeList;
        char *printName;
        char *inverseName;
        int indepOnly; // remembers if relation is independent only
};

#endif
