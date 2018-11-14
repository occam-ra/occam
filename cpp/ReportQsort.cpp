#include "Key.h"
#include "Model.h"
#include <cctype>
#include <cstring>
//-- support routines for quicksort. The static variables
//-- are used to communicate between the sort and compare routines
// The "levelPref" variable is used to sub-sort during a search,
// preferring to keep the models sorted in the order of the search.

VariableList *sort_var_list;
int sort_count;
int *sort_vars;
KeySegment **sort_keys;
Table *sort_table;
const char *sortAttr;
Direction sortDir;
Direction searchDir;


int allNumeric(const char* s) {
    bool ret = true;
    for (const char* r = s; *r != '\0'; ++r) {
        ret &= isdigit(r[0]);
    }
    return ret;
}
int strcmpAccountingForNumbers(const char* s1, const char* s2) {
    if (allNumeric(s1) && allNumeric(s2)) {
        int d1 = atoi(s1);
        int d2 = atoi(s2);
        return (d1 < d2) ? -1 : (d1 == d2) ? 0 : 1;
    } else {
        return strcmp(s1, s2);
    }
}
int sortCompare(const void *k1, const void *k2) {
    Model *m1 = *((Model**) k1);
    Model *m2 = *((Model**) k2);
    double a1 = m1->getAttribute(sortAttr);
    double a2 = m2->getAttribute(sortAttr);
    double l1 = m1->getAttribute("Level");
    double l2 = m2->getAttribute("Level");
    int levelPref = 0;
    if      (searchDir == Direction::Ascending)  { levelPref = (l1 > l2) ? -1 : (l1 < l2) ? 1 : 0; } 
    else if (searchDir == Direction::Descending) { levelPref = (l1 < l2) ? -1 : (l1 > l2) ? 1 : 0; }
    if (sortDir == Direction::Descending) { return (a1 > a2) ? -1 : (a1 < a2) ? 1 : levelPref; }
    else                       { return (a1 < a2) ? -1 : (a1 > a2) ? 1 : levelPref; }
}
int sortKeys(const void *d1, const void *d2) {
    int keysize = sort_var_list->getKeySize();
    KeySegment *k1, *k2;
    if (sort_keys == NULL) {
        k1 = sort_table->getKey((long long)*(int*) d1);
        k2 = sort_table->getKey((long long)*(int*) d2);
    } else {
        k1 = sort_keys[*(int*) d1];
        k2 = sort_keys[*(int*) d2];
    }
    const char *s1, *s2;
    int test;
    int v;
    for (int j = 0; j < sort_count; j++) {
        if (sort_vars == NULL) {
            v = j;
        } else {
            v = sort_vars[j];
        }
        s1 = sort_var_list->getVarValue(v, Key::getKeyValue(k1, keysize, sort_var_list, v));
        s2 = sort_var_list->getVarValue(v, Key::getKeyValue(k2, keysize, sort_var_list, v));
        test = strcmpAccountingForNumbers(s1, s2);
        if (test != 0) {
            return test;
        }
    }
    return 0;
}




void orderIndices(const char **stringArray, int len, int *order) {
    // Find the last value in the order list, to initialize the other searches with
    int last = 0;
    for (int i = 0; i < len; i++) {
        if (strcmp(stringArray[last], stringArray[i]) < 0) {
            last = i;
        }
    }
    // Loop through order, finding the lowest value for each spot that is bigger than the previous values
    for (int j = 0; j < len; j++) {
        // Set initial values all to the last value
        order[j] = last;
        // Loop through all the values looking for a lower one
        for (int i = 0; i < len; i++) {
            if (strcmp(stringArray[order[j]], stringArray[i]) > 0) {
                // If a lower value is found for the first slot, use it
                if (j == 0) {
                    order[j] = i;
                    // If it's not the first slot, make sure it's bigger than the previous slot before using it
                } else if (strcmp(stringArray[order[j - 1]], stringArray[i]) < 0) {
                    order[j] = i;
                }
            }
        }
    }
}
