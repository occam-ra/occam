/* Copyright 2000, Portland State University Systems Science Program.  All Rights Reserved
 */

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

#undef TRACE_MEMORY

#ifdef TRACE_MEMORY
inline void* operator new (size_t inSize) {
    if (inSize > 1024) {
	void *addr = __builtin_return_address(0);
	printf ("new: [%x] size=%ld\n", addr, inSize);
    }
    return malloc(inSize);
}
#endif

#endif
