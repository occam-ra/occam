#ifndef _OCCORE_H
#define _OCCORE_H

#include "stdlib.h"
#include "stdio.h"

#define fmax(a, b) ((a) > (b) ? (a) : (b))

#define growStorage(old, osize, factor) (_growStorage((old), (unsigned long long) (osize), (factor), __FILE__, __LINE__))

/**
 * growStorage - increase the storage for a block by the given factor, copying the
 * old data into the new block. This function is called via the macro above, so
 * that memory usage can be tracked.
 */
extern void *_growStorage(void *old, unsigned long long oldSize, long factor, const char *file, long line);

/**
 * Determine if two variable lists are the same
 */
int ocCompareVariables(int varCount1, int *var1, int varCount2, int *var2);

/**
 * Determine if one variable list contains another
 */
bool ocContainsVariables(int varCount1, int *var1, int varCount2, int *var2);
bool ocContainsStates(int var_count1, int *var1, int *states1, int var_count2, int *var2, int *states2);

#endif
