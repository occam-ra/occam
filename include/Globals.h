#ifndef ___Globals
#define ___Globals

#include "Types.h"

extern class VariableList* sort_var_list;
extern int sort_count;
extern int* sort_vars;
extern KeySegment** sort_keys;
extern class Table* sort_table;

int sortKeys(const void*, const void*);

#endif
