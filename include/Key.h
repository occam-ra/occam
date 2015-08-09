#ifndef ___Key
#define ___Key

/*
 * static functions for manipulating keys and masks (a mask has all 0's in the
 * slot for a variable if it is included in the mask, 1's otherwise)
 */

#include "Types.h"

class Table;

class Key {
    public:
        //-- key construction and manipulation functions

        // build a key, setting don't care's for all variables except those provided,
        // and setting the appropriate values where provided. Space for the key is
        // allocated by the caller. Key points to key storage of at least keysize;
        // varindices and varvalues are the same length and
        static void buildKey(KeySegment *key, int keysize, class VariableList *vars,
                int *varindices, int *varvalues, int varcount);

        // build a key with a value for every variable.
        static void buildFullKey(KeySegment *key, int keysize, class VariableList *vars,
                int *varvalues);

        // set a single value within a key. Value can be DONT_CARE or a legal variable value.
        static void setKeyValue(KeySegment *key, int keysize, class VariableList *vars,
                int index, int value);
        // get a single value within a key. Value can be DONT_CARE or a legal variable value.
        static int getKeyValue(KeySegment *key, int keysize, class VariableList *vars,
                int index);

        // compare two keys, returning -1, 0, or 1 as the first is less than, equal to, or
        // greater than the second (lexically).
        static int compareKeys(KeySegment *key1, KeySegment *key2, int keysize);

        // copy key1 to key2
        static int copyKey(KeySegment *key1, KeySegment *key2, int keysize);

        static void buildMask(KeySegment *mask, int keysize, class VariableList *vars,
                int *varindices, int varcount);

        static void keyToString(KeySegment *key, VariableList *var, char *str);
        static void keyToUserString(KeySegment *key, VariableList *var, char *str);
        static void keyToUserString(KeySegment *key, VariableList *var, char *str,
                const char *delim);
        static void getSiblings(KeySegment *key, VariableList *vars, Table *table,
                long *i_sibs, int DV_ind, int *no_sib);

        static void dumpKey(KeySegment *key, int keysize);
};

#endif 
