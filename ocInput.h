/* Copyright 2000, Portland State University Systems Science Program.  All Rights Reserved
 */

/**
 * ocInput.h - provides functions for managing input data
 */

#ifndef OCINPUT_H
#define OCINPUT_H

#include "ocCore.h"
#include <stdio.h>

/**
 * oldRead - read data from old format files. The ocTable and ocVariableList are allocated
 * in this function, and then populated with the input data and the variables, respectively
 */
 
bool ocReadFile(FILE *fd, class ocOptions *options,
	ocTable **indata, ocVariableList **vars);

#endif

