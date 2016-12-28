#ifndef ___Key
#define ___Key

/* Functions for manipulating keys and masks
 * A mask has all 0's in the slot for a variable if it is included in the mask, or 1's otherwise.
 */

#include "Types.h"

class Table;
class VariableList;

namespace Key {
    /* Build a key,
     * setting "DONTCARE" for all variables except those provided,
     * and setting the appropriate values where provided.
     * Space for the key is allocated by the caller.
     * Key points to key storage of at least keysize; 
     * varindices and varvalues are the same length
     * Values can be DONT_CARE or a legal variable value. */
    void buildKey(KeySegment *key, int keysize, VariableList *vars, int *varindices, int *varvalues, int varcount);

    /* build a key with a value for every variable. */
    void buildFullKey(KeySegment *key, int keysize, VariableList *vars, int *varvalues);

    /* Get or set a single value within a key. */
    void setKeyValue(KeySegment *key, int keysize, VariableList *vars, int index, int value);
    int getKeyValue(KeySegment *key, int keysize, VariableList *vars, int index);

    /* Compare two keys,  returning:  LT -> -1; EQ -> 0; GT -> 1 */
    int compareKeys(KeySegment *key1, KeySegment *key2, int keysize);

    /* Copy key1 to key2 */
    int copyKey(KeySegment *key1, KeySegment *key2, int keysize);

    void buildMask(KeySegment *mask, int keysize, VariableList *vars, int *varindices, int varcount);
    void keyToString(KeySegment *key, VariableList *var, char *str);
    void keyToUserString(KeySegment *key, VariableList *var, char *str);
    void keyToUserString(KeySegment *key, VariableList *var, char *str, const char *delim, bool showKey=true);
    void getSiblings(KeySegment *key, VariableList *vars, Table *table, long *i_sibs, int DV_ind, int *no_sib);
    void dumpKey(KeySegment *key, int keysize);
};

#endif 
