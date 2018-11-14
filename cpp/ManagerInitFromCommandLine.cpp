/*
 * Copyright © 1990 The Portland State University OCCAM Project Team
 * [This program is licensed under the GPL version 3 or later.]
 * Please see the file LICENSE in the source
 * distribution of this software for license terms.
 */

#include <math.h>
#include "Input.h"
#include "Key.h"
#include "ManagerBase.h"
#include "Math.h"
#include "Model.h"
#include "ModelCache.h"
#include "Options.h"
#include "RelCache.h"
#include "Relation.h"
#include "StateConstraint.h"
#include "VariableList.h"
#include "_Core.h"
#include <assert.h>
#include <cxxabi.h>
#include <execinfo.h>
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

bool ManagerBase::initFromCommandLine(int argc, char **argv) {
    Table *input = NULL, *test = NULL;
    VariableList *vars;
    //-- get all command line options.  Datafile arguments show up as "datafile" option.
    options->setOptions(argc, argv);

    //-- now read datafiles (which may also contain options)
    void *next = NULL;
    const char *fname;
    while (options->getOptionString("datafile", &next, &fname)) {
        FILE *fd = fopen(fname, "r");
        if (fd == NULL) {
            printf("ERROR: couldn't open %s\n", fname);
            return false;
        } else if ((dataLines = ocReadFile(fd, options, &input, &test, &vars)) == 0) {
            printf("ERROR: ocReadFile() failed for %s\n", fname);
            return false;
        }
    }
    varList = vars;

    if (!getOptionFloat("alpha-threshold", NULL, &alpha_threshold))
    {
        alpha_threshold = 0.05;
    };

    if (!varList->isDirected()) {
        if (getOptionFloat("function-constant", NULL, &functionConstant)) {
            input->addConstant(functionConstant);
            if (test)
                test->addConstant(functionConstant);
            setValuesAreFunctions(1);
        } else {
            functionConstant = 0;
        }
    }


    const char *option;
    if (getOptionString("function-values", NULL, &option)) {
        setValuesAreFunctions(1);
    }

    // check for negative values in the data
    negativeConstant = input->getLowestValue();
    if (test) {
        double testLowest = test->getLowestValue();
        if (testLowest < negativeConstant)
            negativeConstant = testLowest;
    }
    if (negativeConstant < 0) {
        if (varList->isDirected()) {
            printf("ERROR: Negative frequency values are not permitted in directed systems.\n");
            return false;
        }
        setValuesAreFunctions(1);
        negativeConstant *= -1;
        input->addConstant(negativeConstant);
        if (test)
            test->addConstant(negativeConstant);
    } else {
        negativeConstant = 0;
    }

    sampleSize = input->normalize();
    if (test)
        testSampleSize = test->normalize();

    // if sampleSize is equal to 1, this is probability data, and we should treat it as a function
    if (fabs(sampleSize - 1) < DBL_EPSILON) {
        setValuesAreFunctions(1);
    }

    //-- configurable fitting parameters
    //-- convergence error. This is approximately in units of samples.
    //-- if initial data was probabilities, an artificial scale of 1000 is used
    double value;
    ocOptionDef *currentOptDef;
    if (!getOptionFloat("ipf-maxdev", NULL, &value)) {
        currentOptDef = options->findOptionByName("ipf-maxdev");
        setOptionFloat(currentOptDef, .20);
    }
    if (!getOptionFloat("ipf-maxit", NULL, &value)) {
        currentOptDef = options->findOptionByName("ipf-maxit");
        setOptionFloat(currentOptDef, 266);
    }

    inputData = input;
    testData = test;
    inputH = ocEntropy(inputData);
    keysize = vars->getKeySize();
    return true;
}
