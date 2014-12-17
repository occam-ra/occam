/* Copyright 2000, Portland State University Systems Science Program.  All Rights Reserved
 */

#include "_ocCore.h"
#include "ocCore.h"
#include "string.h"
#include "stdio.h"
#include "limits.h"

#undef LOG_MEMORY

#ifdef LOG_MEMORY

const char *memlog = "memusage.log";
static FILE *mlogfd = fopen(memlog, "w");

void logMemory(void *old, unsigned long long oldSize, long factor, const char *file, long line)
{
    if (mlogfd == NULL) return;
    fprintf(mlogfd, "%s [%ld]: %lld %ld\n", file, line, oldSize, factor);
    fflush(mlogfd);
}

#else

void logMemory(void *old, unsigned long long oldSize, long factor, const char *file, long line)
{
}

#endif

void *_growStorage(void *old, unsigned long long oldSize, long factor, const char *file, long line)
{
    logMemory(old, oldSize, factor, file, line);
    if (oldSize == 0) oldSize = 1;
    if ( ((double)oldSize * (double)factor) > ULONG_MAX ) {
        printf("Memory allocation error.  %s[%ld], memory requested: %f\n", file, line, (double)oldSize * (double)factor);
        fflush(stdout);
        exit(1);
    }
    unsigned long long newSize = oldSize * factor;
    if (newSize == 0) newSize = 1;

    char *newp = new char[newSize];
    if (newp == NULL) {
        printf("Out of memory!\n");
        return NULL;
    }
    memset(newp, 0, newSize);
    memcpy(newp, old, oldSize);
    delete [] ((char*)old);
    return newp;
}


//-- check variable lists to see if they are the same
int ocCompareVariables(int varCount1, int *var1, int varCount2, int *var2)
{
    // this assumes the indices in the relation are sorted.  Two relations
    // are equal if they have the same set of variables.  If there are state
    // constraints, these must also equal.
    int count = (varCount1 < varCount2) ? varCount1 : varCount2;	// minimum
    for (int i = 0; i < count; i++) {
        if (var1[i] < var2[i]) return -1;
        else if (var1[i] > var2[i]) return 1;
    }

    // equal so far
    if (varCount1 > count) return 1;		// this list is longer
    else if (varCount2 > count) return -1;		// other list is longer
    else return 0;
}


//-- check variable lists to see if the first contains the second
bool ocContainsVariables(int varCount1, int *var1, int varCount2, int *var2)
{
    //-- since variable lists are sorted by construction, we move along the first list,
    //-- looking for the next entry in the second. When we are done, we should have
    //-- traversed the entire second list.
    int j = 0;
    for (int i = 0; i < varCount1; i++) {
        if (j >= varCount2) break;
        if (var1[i] == var2[j]) j++;
    }
    return (j >= varCount2);
}




bool ocContainsStates(int var_count1, int *var1, int *states1, int var_count2, int *var2, int *states2)
{
    bool found;
    int s1, s2;
    for (int i = 0; i < var_count2; i++) {
        found = false;
        for (int j = 0; j < var_count1; j++) {
            if (var2[i] == var1[j]) {
                s1 = (states1 == NULL) ? -1 : states1[j];
                s2 = (states2 == NULL) ? -1 : states2[i];
                if ((s1 != DONT_CARE) && (s2 != s1)) {
                    return false;
                } else {
                    found = true;
                    break;
                }
            }
        }
        if (found == false)
            return false;
    }
    return true;
}



