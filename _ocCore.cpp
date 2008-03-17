/* Copyright 2000, Portland State University Systems Science Program.  All Rights Reserved
 */

#include "_ocCore.h"
#include "string.h"
#include "stdio.h"

#undef LOG_MEMORY

#ifdef LOG_MEMORY

const char *memlog = "memusage.log";
static FILE *mlogfd = fopen(memlog, "w");

void logMemory(void *old, unsigned long long oldSize, long factor, const char *file, long line)
{
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
	char *newp = new char[oldSize * factor];
	if (newp == NULL) {
		printf("out of memory!\n");
		return NULL;
	}
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



