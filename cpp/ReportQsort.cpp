#include "Report.h"
#include <cstring>
//-- support routines for quicksort. The static variables
//-- are used to communicate between the sort and compare routines
// The "levelPref" variable is used to sub-sort during a search,
// preferring to keep the models sorted in the order of the search.
int sortCompare(const void *k1, const void *k2) {
    Model *m1 = *((Model**) k1);
    Model *m2 = *((Model**) k2);
    double a1 = m1->getAttribute(Report::sortAttr);
    double a2 = m2->getAttribute(Report::sortAttr);
    double l1 = m1->getAttribute("Level");
    double l2 = m2->getAttribute("Level");
    int levelPref = 0;
    if (Report::searchDir == 0) {
        levelPref = (l1 > l2) ? -1 : (l1 < l2) ? 1 : 0;
    } else if (Report::searchDir == 1) {
        levelPref = (l1 < l2) ? -1 : (l1 > l2) ? 1 : 0;
    }
    if (Report::sortDir == Report::DESCENDING) {
        return (a1 > a2) ? -1 : (a1 < a2) ? 1 : levelPref;
    } else {
        return (a1 < a2) ? -1 : (a1 > a2) ? 1 : levelPref;
    }
}
int sortKeys(const void *d1, const void *d2) {
    int keysize = Report::sort_var_list->getKeySize();
    KeySegment *k1, *k2;
    if (Report::sort_keys == NULL) {
        k1 = Report::sort_table->getKey((long long)*(int*) d1);
        k2 = Report::sort_table->getKey((long long)*(int*) d2);
    } else {
        k1 = Report::sort_keys[*(int*) d1];
        k2 = Report::sort_keys[*(int*) d2];
    }
    const char *s1, *s2;
    int test;
    int v;
    for (int j = 0; j < Report::sort_count; j++) {
        if (Report::sort_vars == NULL) {
            v = j;
        } else {
            v = Report::sort_vars[j];
        }
        s1 = Report::sort_var_list->getVarValue(v, Key::getKeyValue(k1, keysize, Report::sort_var_list, v));
        s2 = Report::sort_var_list->getVarValue(v, Key::getKeyValue(k2, keysize, Report::sort_var_list, v));
        test = strcmp(s1, s2);
        if (test != 0)
            return test;
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
