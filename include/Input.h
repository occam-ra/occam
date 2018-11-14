/*
 * Copyright © 1990 The Portland State University OCCAM Project Team
 * [This program is licensed under the GPL version 3 or later.]
 * Please see the file LICENSE in the source
 * distribution of this software for license terms.
 */

#ifndef ___Input
#define ___Input

#include "Table.h"

#include <stdio.h>

/**
 * oldRead - read data from old format files. The Table and VariableList are allocated
 * in this function, and then populated with the input data and the variables, respectively
 * The return value is the number of data lines read.
 */

int ocReadFile(FILE *fd, class Options *options,
	Table **indata, Table **testdata, VariableList **vars);

#endif

