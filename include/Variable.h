#ifndef ___Variable
#define ___Variable

#include "Constants.h"
#include "Types.h"

struct ocVariable { // internal use only - see VariableList
        int cardinality; // number of values of the variable
        int segment; // which KeySegment of the key this variable is in
        int shift; // starting rightmost bit position of value in segment
        int size; // number of bits (log2 of (cardinality+1))
        bool dv; // is it a dependent variable?
        KeySegment mask; // a bitmask of 1's in the bit positions for this variable
        char name[MAXNAMELEN + 1]; // long name of variable (max 32 chars)
        char abbrev[MAXABBREVLEN + 1]; // abbreviated name for variable
        char* valmap[MAXCARDINALITY]; // maps input file values to nominal values
        bool rebin; //is rebinning required for this variable
        char * oldnew[2][MAXCARDINALITY];
        int old_card;
        char *exclude;
};

#endif
