/*
 * ocReport.cpp - implements model reports
 */

#include <math.h>
#include "ocCore.h"
#include "_ocCore.h"
#include "ocReport.h"
#include "ocManagerBase.h"
#include "ocMath.h"
#include <string.h>
#include <ctype.h>
#include <stdlib.h>
//#include "ocWin32.h"

struct attrDesc {
        const char *name;
        const char *title;
        const char *fmt;
};

static attrDesc attrDescriptions[] = { { ATTRIBUTE_LEVEL, "Level", "%14.0f" }, { ATTRIBUTE_H, "H", "%12.4f" }, {
        ATTRIBUTE_T, "T", "%12.4f" }, { ATTRIBUTE_DF, "DF", "%14.0f" }, { ATTRIBUTE_DDF, "dDF", "%14.0f" }, {
        ATTRIBUTE_FIT_H, "H(IPF)", "%12.4f" }, { ATTRIBUTE_ALG_H, "H(ALG)", "%12.4f" }, { ATTRIBUTE_FIT_T, "T(IPF)",
        "%12.4f" }, { ATTRIBUTE_ALG_T, "T(ALG)", "%12.4f" }, { ATTRIBUTE_LOOPS, "Loops", "%2.0f" }, {
        ATTRIBUTE_EXPLAINED_I, "Inf", "%1.8f" }, { ATTRIBUTE_AIC, "dAIC", "%12.4f" },
        { ATTRIBUTE_BIC, "dBIC", "%12.4f" }, { ATTRIBUTE_BP_AIC, "dAIC(BP)", "%12.4f" }, { ATTRIBUTE_BP_BIC, "dBIC(BP)",
                "%12.4f" }, { ATTRIBUTE_PCT_CORRECT_DATA, "%C(Data)", "%12.4f" }, { ATTRIBUTE_PCT_COVERAGE, "%cover",
                "%12.4f" }, { ATTRIBUTE_PCT_CORRECT_TEST, "%C(Test)", "%12.4f" }, { ATTRIBUTE_PCT_MISSED_TEST, "%miss",
                "%12.4f" }, { ATTRIBUTE_BP_EXPLAINED_I, "Inf(BP)", "%12f" },
        //*******************************************************************************
        { ATTRIBUTE_UNEXPLAINED_I, "Unexp Info", "%12.4f" }, { ATTRIBUTE_T_FROM_H, "T(H)", "%12.4f" }, {
                ATTRIBUTE_IPF_ITERATIONS, "IPF Iter", "%7.0f" }, { ATTRIBUTE_IPF_ERROR, "IPF Err", "%12.8g" }, {
                ATTRIBUTE_PROCESSED, "Proc", "%2.0" }, { ATTRIBUTE_IND_H, "H(Ind)", "%12.4f" }, { ATTRIBUTE_DEP_H,
                "H(Dep)", "%12.4f" }, { ATTRIBUTE_COND_H, "H|Model", "%12.4f" }, { ATTRIBUTE_COND_DH, "dH|Model",
                "%12.4f" }, { ATTRIBUTE_COND_PCT_DH, "%dH(DV)", "%12.4f" }, { ATTRIBUTE_COND_DF, "DF(Cond)", "%14.0f" },
        { ATTRIBUTE_COND_DDF, "dDF(Cond)", "%14.0f" }, { ATTRIBUTE_TOTAL_LR, "LR Total", "%12.4f" }, { ATTRIBUTE_IND_LR,
                "LR Ind", "%12.4f" }, { ATTRIBUTE_COND_LR, "LR|Model", "%12.4f" }, { ATTRIBUTE_COND_H_PROB, "H|Model",
                "%12.4f" }, { ATTRIBUTE_P2, "P2", "%12.4f" }, { ATTRIBUTE_P2_ALPHA, "P2 Alpha", "%12.4f" }, {
                ATTRIBUTE_P2_BETA, "P2 Beta", "%12.4f" }, { ATTRIBUTE_LR, "dLR", "%12.4f" }, { ATTRIBUTE_INCR_ALPHA,
                "Inc.Alpha", "%12.4f" }, { ATTRIBUTE_INCR_ALPHA_REACHABLE, "Inc.A.<0.05", "%1.0f" }, {
                ATTRIBUTE_PROG_ID, "Prog.", "%14.0f" }, { ATTRIBUTE_ALPHA, "Alpha", "%12.4f" }, { ATTRIBUTE_BETA,
                "Beta", "%12.4f" }, { ATTRIBUTE_BP_T, "T(BP)", "%12.4f" }, { ATTRIBUTE_BP_H, "est. H(BP)", "%12.4f" }, {
                ATTRIBUTE_BP_UNEXPLAINED_I, "est. Unexplained(BP)", "%12.4f" }, { ATTRIBUTE_BP_ALPHA, "Alpha(BP)",
                "%12.4f" }, { ATTRIBUTE_BP_BETA, "Beta(BP)", "%12.4f" }, { ATTRIBUTE_BP_LR, "LR(BP)", "%12.4f" }, {
                ATTRIBUTE_BP_COND_H, "H|Model(BP)", "%12.4f" }, { ATTRIBUTE_BP_COND_DH, "dH|Model(BP)", "%12.4f" }, {
                ATTRIBUTE_BP_COND_PCT_DH, "est. %dH(DV)(BP)", "%12.4f" }, };

bool ocReport::htmlMode = false;

int attrDescCount = sizeof(attrDescriptions) / sizeof(attrDesc);
static int searchDir;

static void deleteStringTable(char **table, long stringCount) {
    int i;
    for (i = 0; i < stringCount; i++)
        delete table[i];
    delete table;
}

ocReport::ocReport(class ocManagerBase *mgr) {
    manager = mgr;
    searchDir = -1;
    maxModelCount = 10;
    models = new ocModel*[maxModelCount];
    memset(models, 0, maxModelCount * sizeof(ocModel*));
    defaultFitModel = NULL;
    attrs = 0;
    modelCount = 0;
    attrCount = 0;
    separator = 3;
}

ocReport::~ocReport() {
    //-- models don't belong to us, so don't delete them; just the pointer block.
    delete models;
    deleteStringTable(attrs, attrCount);
}

void ocReport::addModel(class ocModel *model) {
    const int FACTOR = 2;
    while (modelCount >= maxModelCount) {
        models = (ocModel**) growStorage(models, maxModelCount*sizeof(ocModel*), FACTOR);
        maxModelCount *= FACTOR;
    }
    models[modelCount++] = model;
}

void ocReport::setDefaultFitModel(class ocModel *model) {
    defaultFitModel = model;
}

void ocReport::setAttributes(const char *attrlist) {
    int listCount = 1;
    const char *cp;
    //-- count the attributes in list (commas + 1)
    for (cp = attrlist; *cp; cp++)
        if (*cp == ',')
            listCount++;

    //-- delete old list and create new one
    if (attrs)
        deleteStringTable(attrs, attrCount);
    attrs = new char *[listCount];
    attrCount = 0;
    cp = attrlist;
    const char *cpcomma, *cpend;
    for (;;) {
        while (isspace(*cp))
            cp++;
        cpcomma = strchr(cp, ',');
        if (cpcomma == NULL)
            cpcomma = cp + strlen(cp); // cpcomma points to null byte
        cpend = cpcomma - 1;
        while (isspace(*cpend))
            cpend--;
        char *newAttr = new char[cpend - cp + 2]; //allow for null
        strncpy(newAttr, cp, cpend - cp + 1);
        newAttr[cpend - cp + 1] = '\0';
        attrs[attrCount++] = newAttr;
        if (*cpcomma == '\0')
            break;
        cp = cpcomma + 1;
    }
}

//-- support routines for quicksort. The static variables
//-- are used to communicate between the sort and compare routines
// The "levelPref" variable is used to sub-sort during a search,
// preferring to keep the models sorted in the order of the search.
static const char *sortAttr;
static ocReport::SortDir sortDir;
static int sortCompare(const void *k1, const void *k2) {
    ocModel *m1 = *((ocModel**) k1);
    ocModel *m2 = *((ocModel**) k2);
    double a1 = m1->getAttribute(sortAttr);
    double a2 = m2->getAttribute(sortAttr);
    double l1 = m1->getAttribute("Level");
    double l2 = m2->getAttribute("Level");
    int levelPref = 0;
    if (searchDir == 0) {
        levelPref = (l1 > l2) ? -1 : (l1 < l2) ? 1 : 0;
    } else if (searchDir == 1) {
        levelPref = (l1 < l2) ? -1 : (l1 > l2) ? 1 : 0;
    }
    if (sortDir == ocReport::DESCENDING) {
        return (a1 > a2) ? -1 : (a1 < a2) ? 1 : levelPref;
    } else {
        return (a1 < a2) ? -1 : (a1 > a2) ? 1 : levelPref;
    }
}

void ocReport::sort(const char *attr, SortDir dir) {
    sortAttr = attr;
    sortDir = dir;
    searchDir = manager->getSearchDirection();
    qsort(models, modelCount, sizeof(ocModel*), sortCompare);
}

void ocReport::sort(class ocModel** models, long modelCount, const char *attr, SortDir dir) {
    sortAttr = attr;
    sortDir = dir;
    qsort(models, modelCount, sizeof(ocModel*), sortCompare);
}

static int maxNameLength;
// Print a report of the search results
void ocReport::print(FILE *fd) {
    // To speed things up, we make a list of the indices of the attribute descriptions
    int *attrID = new int[attrCount];
    for (int a = 0; a < attrCount; a++) {
        attrID[a] = -1;
        const char *attrp = attrs[a];
        // Find the attribute
        for (int d = 0; d < attrDescCount; d++) {
            if (strcasecmp(attrp, attrDescriptions[d].name) == 0) {
                attrID[a] = d;
                break;
            }
        }
    }
    maxNameLength = 1;
    for (int m = 0; m < modelCount; m++) {
        if (strlen(models[m]->getPrintName()) > maxNameLength)
            maxNameLength = strlen(models[m]->getPrintName());
    }

    // Create a mapping for IDs so they are listed in order.
    int idOrder[modelCount + 1];
    idOrder[0] = 0;
    if (manager->getSearchDirection() == 1) {
        for (int m = 0; m < modelCount; m++) {
            idOrder[models[m]->getID()] = m + 1;
            models[m]->setID(m + 1);
        }
    } else {
        for (int m = 0; m < modelCount; m++) {
            idOrder[models[m]->getID()] = modelCount - m;
            models[m]->setID(modelCount - m);
        }
    }
    // If progenitors are being tracked, map the progenitor values too.
    if (models[0]->getProgenitor() != NULL) {
        for (int m = 0; m < modelCount; m++) {
            models[m]->setAttribute(ATTRIBUTE_PROG_ID,
                    (double) idOrder[(int) models[m]->getAttribute(ATTRIBUTE_PROG_ID)]);
        }
    }

    // Print out the search results for each model, with the header before and after
    if (htmlMode)
        fprintf(fd, "<table border=0 cellpadding=0 cellspacing=0>\n");
    printSearchHeader(fd, attrID);
    for (int m = 0; m < modelCount; m++) {
        printSearchRow(fd, models[m], attrID, m % 2);
    }
    printSearchHeader(fd, attrID);

    // Loop through the models to find the best values for each measure of model quality
    double bestBIC, bestAIC, bestInfoAlpha, bestInfoIncr, bestTest;
    double tempBIC, tempAIC, tempInf, tempTest;
    bestInfoAlpha = bestInfoIncr = bestTest = -1.0e38;
    bestBIC = models[0]->getAttribute(ATTRIBUTE_BIC);
    bestAIC = models[0]->getAttribute(ATTRIBUTE_AIC);

    // Only show best info/alpha values when searching from the bottom.
    bool checkAlpha = false;
    bool showAlpha = false;
//    if ((manager->getRefModel() == manager->getBottomRefModel())
//            || ((manager->getRefModel() != manager->getTopRefModel()) && manager->getSearchDirection() == 0)) {
//        checkAlpha = true;
//    }
    bool checkIncr = false;
    bool showIncr = false;
    if ((manager->getSearchDirection() == 0) && (models[0]->getAttribute(ATTRIBUTE_INCR_ALPHA) != -1)) {
        checkIncr = true;
    }

    // Only show percent correct on test data when it's present.
    bool showPercentCorrect = false;
    if ((models[0]->getAttribute(ATTRIBUTE_PCT_CORRECT_TEST) != -1.0) && manager->getTestSampleSize() > 0.0)
        showPercentCorrect = true;

    for (int m = 0; m < modelCount; m++) {
        tempBIC = models[m]->getAttribute(ATTRIBUTE_BIC);
        if (tempBIC > bestBIC)
            bestBIC = tempBIC;
        tempAIC = models[m]->getAttribute(ATTRIBUTE_AIC);
        if (tempAIC > bestAIC)
            bestAIC = tempAIC;
        tempInf = models[m]->getAttribute(ATTRIBUTE_EXPLAINED_I);
        if (checkAlpha) {
            if (models[m]->getAttribute(ATTRIBUTE_ALPHA) < 0.05) {
                showAlpha = true;
                if (tempInf > bestInfoAlpha)
                    bestInfoAlpha = tempInf;
            }
        }
        if (checkIncr) {
            showIncr = true;
            if (models[m]->getAttribute(ATTRIBUTE_INCR_ALPHA_REACHABLE) == 1) {
                if (tempInf > bestInfoIncr)
                    bestInfoIncr = tempInf;
            }
        }
        if (showPercentCorrect) {
            tempTest = models[m]->getAttribute(ATTRIBUTE_PCT_CORRECT_TEST);
            if (tempTest > bestTest)
                bestTest = tempTest;
        }
    }

    // Now print out the best models for each of the various measures
    if (!htmlMode)
        fprintf(fd, "\n\nBest Model(s) by dBIC:\n");
    else
        fprintf(fd, "<tr><td colspan=8><br><br><b>Best Model(s) by dBIC:</b></td></tr>\n");
    for (int m = 0; m < modelCount; m++) {
        if (models[m]->getAttribute(ATTRIBUTE_BIC) != bestBIC)
            continue;
        printSearchRow(fd, models[m], attrID, 0);
    }

    if (!htmlMode)
        fprintf(fd, "Best Model(s) by dAIC:\n");
    else
        fprintf(fd, "<tr><td colspan=8><b>Best Model(s) by dAIC:</b></td></tr>\n");
    for (int m = 0; m < modelCount; m++) {
        if (models[m]->getAttribute(ATTRIBUTE_AIC) != bestAIC)
            continue;
        printSearchRow(fd, models[m], attrID, 0);
    }

    if (checkAlpha) {
        if (!showAlpha) {
            if (!htmlMode)
                fprintf(fd, "(No Best Model by Information, since none have Alpha < 0.05.)\n");
            else
                fprintf(fd,
                        "<tr><td colspan=8><b>(No Best Model by Information, since none have Alpha < 0.05.)</b></td></tr>\n");
        } else {
            if (!htmlMode)
                fprintf(fd, "Best Model(s) by Information, with Alpha < 0.05:\n");
            else
                fprintf(fd, "<tr><td colspan=8><b>Best Model(s) by Information, with Alpha < 0.05</b>:</td></tr>\n");
            for (int m = 0; m < modelCount; m++) {
                if (models[m]->getAttribute(ATTRIBUTE_EXPLAINED_I) != bestInfoAlpha)
                    continue;
                if (models[m]->getAttribute(ATTRIBUTE_ALPHA) > 0.05)
                    continue;
                printSearchRow(fd, models[m], attrID, 0);
            }
        }
    }
    if (checkIncr) {
        if (showIncr) {
            if (!htmlMode)
                fprintf(fd, "Best Model(s) by Information, with all Inc. Alpha < 0.05:\n");
            else
                fprintf(fd,
                        "<tr><td colspan=8><b>Best Model(s) by Information, with all Inc. Alpha < 0.05</b>:</td></tr>\n");
            for (int m = 0; m < modelCount; m++) {
                if (models[m]->getAttribute(ATTRIBUTE_EXPLAINED_I) != bestInfoIncr)
                    continue;
                if (models[m]->getAttribute(ATTRIBUTE_INCR_ALPHA_REACHABLE) != 1)
                    continue;
                printSearchRow(fd, models[m], attrID, 0);
            }
        }
    }

    if (showPercentCorrect) {
        if (!htmlMode)
            fprintf(fd, "Best Model(s) by %%C(Test):\n");
        else
            fprintf(fd, "<tr><td colspan=8><b>Best Model(s) by %%C(Test)</b>:</td></tr>\n");
        for (int m = 0; m < modelCount; m++) {
            if (models[m]->getAttribute(ATTRIBUTE_PCT_CORRECT_TEST) != bestTest)
                continue;
            printSearchRow(fd, models[m], attrID, 0);
        }
    }

    if (!htmlMode)
        fprintf(fd, "\n\n");
    else
        fprintf(fd, "</table><br>\n");

    delete attrID;
}

// Print out the line of column headers for the search output report
void ocReport::printSearchHeader(FILE *fd, int* attrID) {
    int sepStyle = htmlMode ? 0 : separator;
    int pad, tlen;
    switch (sepStyle) {
        case 0:
            fprintf(fd, "<tr><th align=left>ID</th><th align=left>MODEL</th>");
            break;
        case 2:
            fprintf(fd, "ID,MODEL");
            break;
        case 1:
        case 3:
        default:
            pad = maxNameLength - 5 + 1;
            if (pad < 0)
                pad = 1;
            fprintf(fd, "  ID   MODEL%*c", pad, ' ');
            break;
    }
    const int cwid = 15;
    char titlebuf[1000];
    for (int a = 0; a < attrCount; a++) {
        const char *title;
        if (attrID[a] >= 0) {
            title = attrDescriptions[attrID[a]].title;
        } else {
            title = attrs[a];
        }
        const char *pct = strchr(title, '$');
        tlen = strlen(title);
        if (pct != NULL) {
            tlen = pct - title;
            strncpy(titlebuf, title, tlen);
            titlebuf[tlen] = '\0';
            title = titlebuf;
        }
        switch (sepStyle) {
            case 0:
                fprintf(fd, "<th width=80 align=left>%s</th>\n", title);
                break;
            case 1:
                fprintf(fd, "\t%s", title);
                break;
            case 2:
                fprintf(fd, ",%s", title);
                break;
            case 3:
            default:
                pad = cwid - tlen;
                if (pad < 1)
                    pad = 1;
                //if (a == 0) pad += cwid - 5;
                fprintf(fd, "%*c%s", pad, ' ', title);
                break;
        }
    }
    if (sepStyle)
        fprintf(fd, "\n");
    else
        fprintf(fd, "</tr>\n");
}

// Print out a single row of the search report results
void ocReport::printSearchRow(FILE *fd, ocModel* model, int* attrID, bool isOddRow) {
    const char *mname = model->getPrintName(manager->getUseInverseNotation());
    int ID = model->getID();
    int pad;
    const int cwid = 15;
    char field[100];
    int sepStyle = htmlMode ? 0 : separator;
    const char *reachable = " ";
    if ((model->getAttribute(ATTRIBUTE_INCR_ALPHA) != -1)
            && (model->getAttribute(ATTRIBUTE_INCR_ALPHA_REACHABLE) == 1)) {
        reachable = "*";
    }
    switch (sepStyle) {
        case 0:
            if (isOddRow)
                fprintf(fd, "<tr class=r1><td>%d%s</td><td>%s</td>", ID, reachable, mname);
            else
                fprintf(fd, "<tr><td>%d%s</td><td>%s</td>", ID, reachable, mname);
            break;
        case 2:
            fprintf(fd, "%d%s,%s", ID, reachable, mname);
            break;
        case 1:
        case 3:
        default:
            pad = maxNameLength - strlen(mname) + 1;
            if (pad < 0)
                pad = 1;
            fprintf(fd, "%4d%s  %s%*c", ID, reachable, mname, pad, ' ');
            break;
    }
    for (int a = 0; a < attrCount; a++) {
        const char *fmt = (attrID[a] >= 0) ? attrDescriptions[attrID[a]].fmt : NULL;
        if (fmt == NULL) {
            // get format info from name, if present
            const char *pct = strchr(attrs[a], '$');
            fmt = (pct != NULL && toupper(*(pct + 1)) == 'I') ? "%8.0f" : "%8.4f";
        }
        double attr = model->getAttribute(attrs[a]);
        // -1 means uninitialized, so don't print
        if (attr == -1.0)
            field[0] = '\0';
        else
            sprintf(field, fmt, attr);
        switch (sepStyle) {
            case 0:
                fprintf(fd, "<td>%s</td>\n", field);
                break;
            case 1:
                fprintf(fd, "\t");
                fprintf(fd, field);
                break;
            case 2:
                fprintf(fd, ",");
                fprintf(fd, field);
                break;
            case 3:
                pad = cwid - strlen(field);
                fprintf(fd, "%*c", pad, ' ');
                fprintf(fd, field);
                break;
        }
    }

    if (!htmlMode)
        fprintf(fd, "\n");
    else
        fprintf(fd, "</tr>\n");
}

void ocReport::print(int fd) {
    //	int fd2 = dup(fd);	// don't close old fd
    FILE *f = fdopen(fd, "w");
    print(f);
    fflush(f);
    fclose(f);
}

static ocVariableList *sort_var_list;
static int sort_count;
static int *sort_vars;
static ocKeySegment **sort_keys;
static ocTable *sort_table;
int sortKeys(const void *d1, const void *d2) {
    int keysize = sort_var_list->getKeySize();
    ocKeySegment *k1, *k2;
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
        s1 = sort_var_list->getVarValue(v, ocKey::getKeyValue(k1, keysize, sort_var_list, v));
        s2 = sort_var_list->getVarValue(v, ocKey::getKeyValue(k2, keysize, sort_var_list, v));
        test = strcmp(s1, s2);
        if (test != 0)
            return test;
    }
    return 0;
}

void ocReport::printResiduals(FILE *fd, ocModel *model) {
    printResiduals(fd, model, NULL);
}

void ocReport::printResiduals(FILE *fd, ocRelation *rel) {
    printResiduals(fd, NULL, rel);
}

void ocReport::printResiduals(FILE *fd, ocModel *model, ocRelation *rel) {
    ocVariableList *varlist = manager->getVariableList();
    if (varlist->isDirected())
        return;
    ocTable *input_data = manager->getInputData();
    ocTable *test_data = manager->getTestData();
    ocTable *input_table = NULL, *fit_table = NULL, *test_table = NULL;
    long var_count = varlist->getVarCount();
    double sample_size = manager->getSampleSz();
    double test_sample_size = manager->getTestSampleSize();
    int keysize = input_data->getKeySize();
    const char *format, *format_r, *header, *header_r, *footer, *traintitle, *testtitle, *delim;
    char *keystr;
    if (htmlMode)
        fprintf(fd, "<br><br>\n");
    if (rel == NULL) {
        fprintf(fd, "RESIDUALS for model %s\n", model->getPrintName());
        fit_table = manager->getFitTable();
        test_table = test_data;
        input_table = input_data;
    } else {
        fprintf(fd, "\nResiduals for relation %s\n", rel->getPrintName());
        // make refData and testData point to projections
        fit_table = rel->getTable();
        input_table = new ocTable(keysize, input_data->getTupleCount());
        manager->makeProjection(input_data, input_table, rel);
        if (test_data != NULL && test_sample_size > 0.0) {
            test_table = new ocTable(keysize, test_data->getTupleCount());
            manager->makeProjection(test_data, test_table, rel);
        }
    }
    if (fit_table == NULL) {
        fprintf(fd, "Error: no fitted table computed\n");
        return;
    }
    if (htmlMode)
        fprintf(fd, "<br>");
    //-- set appropriate format
    int sepStyle = htmlMode ? 0 : separator;
    switch (sepStyle) {
        case 0:
            header =
                    "<table border=1 cellspacing=0 cellpadding=0><tr><th>Cell</th><th>Obs.Prob.</th><th>Obs.Freq.</th><th>Calc.Prob.</th><th>Calc.Freq.</th><th>Residual</th></tr>\n";
            header_r =
                    "<table border=1 cellspacing=0 cellpadding=0><tr><th>Cell</th><th>Obs.Prob.</th><th>Obs.Freq.</th></tr>\n";
            traintitle = "<br>Training Data\n";
            testtitle = "Test Data\n";
            format =
                    "<tr><td>%s</td><td>%#6.8g</td><td>%#6.8g</td><td>%#6.8g</td><td>%#6.8g</td><td>%+#6.8g</td></tr>\n";
            format_r = "<tr><td>%s</td><td>%#6.8g</td><td>%#6.8g</td></tr>\n";
            footer = "</table><br><br>";
            delim = " ";
            break;
        case 1:
            header = "Cell\tObs.Prob.\tObs.Freq.\tCalc.Prob.\tCalc.Freq.\tResidual\n";
            header_r = "Cell\tObs.Prob.\tObs.Freq.\n";
            traintitle = "\nTraining Data\n";
            testtitle = "\nTest Data\n";
            format = "%s\t%#6.8g\t%#6.8g\t%#6.8g\t%#6.8g\t%#6.8g\n";
            format_r = "%s\t%#6.8g\t%#6.8g\n";
            footer = "";
            delim = "\t";
            break;
        case 2:
            header = "Cell,Obs.Prob.,Obs.Freq.,Calc.Prob.,Calc.Freq.,Residual\n";
            header_r = "Cell,Obs.Prob.,Obs.Freq.\n";
            traintitle = "\nTraining Data\n";
            testtitle = "\nTest Data\n";
            format = "%s,%#6.8g,%#6.8g,%#6.8g,%#6.8g,%#6.8g\n";
            format_r = "%s,%#6.8g,%#6.8g\n";
            footer = "";
            delim = ",";
            break;
        case 3:
            header =
                    " Cell   Obs.Prob.    Obs.Freq.    Calc.Prob.    Calc.Freq.    Residual\n    ---------------------------------------------\n";
            header_r =
                    " Cell   Obs.Prob.    Obs.Freq.\n    ---------------------------------------------\n";
            traintitle = "\nTraining Data\n";
            testtitle = "\nTest Data\n";
            format = "%8s  %#6.8g   %#6.8g   %#6.8g   %#6.8g   %#6.8g\n";
            format_r = "%8s  %#6.8g   %#6.8g\n";
            footer = "";
            delim = " ";
            break;
    }
    if (rel != NULL)
        header = header_r;
    keystr = new char[var_count * (MAXABBREVLEN + strlen(delim)) + 1];
    if (rel == NULL) {
        if (htmlMode)
            fprintf(fd, "<br>\n");
        fprintf(fd, "Variable order: ");
        for (int i = 0; i < var_count; i++) {
            fprintf(fd, "%s", varlist->getVariable(i)->abbrev);
        }
        fprintf(fd, "\n");
        if (htmlMode)
            fprintf(fd, "<br>");
    }
    long long dataCount, index, refindex, compare;
    ocKeySegment *refkey, *key;
    double value, refvalue, res;
    double adjustConstant = manager->getFunctionConstant() + manager->getNegativeConstant();
    // Walk through both lists. Missing values are zero.
    // We don't print anything if missing in both lists.
    index = 0;
    refindex = 0;
    fprintf(fd, traintitle);
    for (int i = 1; i < var_count; i++) {
        fprintf(fd, delim);
    }
    fprintf(fd, header);
    dataCount = input_table->getTupleCount();
    int *key_order = new int[dataCount];
    for (long long i = 0; i < dataCount; i++) {
        key_order[i] = i;
    }
    sort_var_list = varlist;
    sort_count = var_count;
    sort_vars = NULL;
    sort_keys = NULL;
    sort_table = input_table;
    qsort(key_order, dataCount, sizeof(int), sortKeys);
    int i;
    for (long long order_i = 0; order_i < dataCount; order_i++) {
        i = key_order[order_i];
        refkey = input_table->getKey(i);
        refvalue = input_table->getValue(i);
        ocKey::keyToUserString(refkey, varlist, keystr, delim);
        if (rel == NULL) {
            index = fit_table->indexOf(refkey, true);
            if (index == -1) {
                value = 0.0;
            } else {
                value = fit_table->getValue(index);
            }
            res = value - refvalue;
            fprintf(fd, format, keystr, refvalue, refvalue * sample_size - adjustConstant, value,
                    value * sample_size - adjustConstant, res);
        } else {
            fprintf(fd, format_r, keystr, refvalue, refvalue * sample_size - adjustConstant);
        }
    }
    fprintf(fd, footer);
    if (test_table != NULL) {
        fprintf(fd, testtitle);
        for (int i = 1; i < var_count; i++) {
            fprintf(fd, delim);
        }
        fprintf(fd, header);
        long long testCount = test_table->getTupleCount();
        int *key_order = new int[testCount];
        for (long long i = 0; i < testCount; i++) {
            key_order[i] = i;
        }
        sort_count = var_count;
        sort_table = test_table;
        qsort(key_order, testCount, sizeof(int), sortKeys);
        for (long long order_i = 0; order_i < testCount; order_i++) {
            i = key_order[order_i];
            refkey = test_table->getKey(i);
            refvalue = test_table->getValue(i);
            ocKey::keyToUserString(refkey, varlist, keystr, delim);
            if (rel == NULL) {
                index = fit_table->indexOf(refkey, true);
                if (index == -1) {
                    value = 0.0;
                } else {
                    value = fit_table->getValue(index);
                }
                res = value - refvalue;
                fprintf(fd, format, keystr, refvalue, refvalue * test_sample_size - adjustConstant, value,
                        value * test_sample_size - adjustConstant, res);
            } else {
                fprintf(fd, format_r, keystr, refvalue, refvalue * test_sample_size - adjustConstant);
            }
        }
        fprintf(fd, footer);
    }
    delete keystr;
    if (rel != NULL) {
        if (test_sample_size > 0.0) {
            delete test_table;
        }
        delete input_table;
    } else {
        if (model->getRelationCount() > 1) {
            for (int i = 0; i < model->getRelationCount(); i++) {
                printResiduals(fd, model->getRelation(i));
            }
        }
    }
}

// Figure out the alphabetical order for an array of strings (such as the dv states)
// (This isn't the most efficient algorithm, but it's simple, and enough to sort a few string values.)
// Maybe could/should be using the DVOrder() from ocManagerBase
static void orderIndices(const char **stringArray, int len, int *order) {
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

void ocReport::printConditional_DV(FILE *fd, ocModel *model, bool calcExpectedDV) {
    printConditional_DV(fd, model, NULL, calcExpectedDV);
}

void ocReport::printConditional_DV(FILE *fd, ocRelation *rel, bool calcExpectedDV) {
    printConditional_DV(fd, NULL, rel, calcExpectedDV);
}

void ocReport::printConditional_DV(FILE *fd, ocModel *model, ocRelation *rel, bool calcExpectedDV) {
    if (model == NULL && rel == NULL) {
        fprintf(fd, "No model or relation specified.\n");
        return;
    }
    ocTable *input_data = manager->getInputData();
    ocTable *test_data = manager->getTestData();
    ocTable *fit_table;
    double sample_size = manager->getSampleSz();
    double test_sample_size = manager->getTestSampleSize();
    ocVariableList *var_list = manager->getVariableList();
    if (!var_list->isDirected())
        return;

    int dv_index = var_list->getDV(); // Get the first DV's index
    ocVariable *dv_var = var_list->getVariable(dv_index); // Get the (first) DV itself
    int var_count = var_list->getVarCount(); // Get the number of variables
    int key_size = input_data->getKeySize(); // Get the key size from the reference data
    int dv_card = dv_var->cardinality; // Get the cardinality of the DV
    double dv_bin_value[dv_card]; // Contains the DV values for calculating expected values.

    ocTable *input_table, *test_table = NULL;
    ocRelation *iv_rel; // A pointer to the IV component of a model, or the relation itself
    ocModel *relModel;

    input_table = new ocTable(key_size, input_data->getTupleCount());
    if (test_sample_size > 0.0)
        test_table = new ocTable(key_size, test_data->getTupleCount());
    if (rel == NULL) {
        ocTable* orig_table = manager->getFitTable();
        if (orig_table == NULL) {
            fprintf(fd, "Error: no fitted table computed.\n");
            return;
        }
        int var_indices[var_count], return_count;
        manager->getPredictingVars(model, var_indices, return_count, true);
        ocRelation *predRelWithDV = manager->getRelation(var_indices, return_count);

        fit_table = new ocTable(key_size, orig_table->getTupleCount());
        manager->makeProjection(orig_table, fit_table, predRelWithDV);
        manager->makeProjection(input_data, input_table, predRelWithDV);
        if (test_sample_size > 0.0)
            manager->makeProjection(test_data, test_table, predRelWithDV);
        //iv_rel = model->getRelation(0);
        iv_rel = predRelWithDV;
    } else {        // Else, if we are working with a relation, make projections of the input and test tables.
        if (rel->isStateBased()) {
            relModel = new ocModel(3);            // make a model of IV and the relation and the DV
            relModel->addRelation(manager->getIndRelation());
            relModel->addRelation(rel);
            relModel->addRelation(manager->getDepRelation());
            // make a fit table for the model
            manager->makeFitTable(relModel);
            // point table links to this new model
            ocTable* orig_table = manager->getFitTable();
            if (orig_table == NULL) {
                fprintf(fd, "Error: no fitted table computed.\n");
                return;
            }
            int var_indices[var_count], return_count;
            manager->getPredictingVars(relModel, var_indices, return_count, true);
            ocRelation *predRelWithDV = manager->getRelation(var_indices, return_count);
            fit_table = new ocTable(key_size, orig_table->getTupleCount());
            manager->makeProjection(orig_table, fit_table, predRelWithDV);
            manager->makeProjection(input_data, input_table, predRelWithDV);
            if (test_sample_size > 0.0)
                manager->makeProjection(test_data, test_table, predRelWithDV);
            iv_rel = predRelWithDV;
        } else {
            fit_table = rel->getTable();
            manager->makeProjection(input_data, input_table, rel);
            if (test_sample_size > 0.0)
                manager->makeProjection(test_data, test_table, rel);
            iv_rel = rel;
        }
    }

    bool use_alt_default = false;
    ocTable *alt_table;
    ocRelation *alt_relation;
    int alt_indices[var_count], alt_var_count;
    int alt_missing_indices[var_count], alt_missing_count;
    if (rel != NULL)
        defaultFitModel = NULL; // Only consider the alternate default model for the main model, not the component relations.
    if (defaultFitModel != NULL) {
        // Check that the alternate model is below the main model on the lattice, and not equal to it.
        if ((model != defaultFitModel) && model->containsModel(defaultFitModel)) {
            use_alt_default = true;
            // If things are okay, make the alternate default table and project it to the active variables
            manager->getPredictingVars(defaultFitModel, alt_indices, alt_var_count, true);
            alt_relation = manager->getRelation(alt_indices, alt_var_count);
            alt_table = new ocTable(key_size, fit_table->getTupleCount());
            manager->makeProjection(fit_table, alt_table, alt_relation);
            // Now get a list of the missing variables from the relation, for use in breaking ties later
            alt_missing_count = alt_relation->copyMissingVariables(alt_missing_indices, var_count);
        }
    }

    int iv_statespace = ((int) manager->computeDF(iv_rel) + 1) / dv_card; // iv_rel statespace divided by cardinality of the DV
    const char **dv_label = (const char**) dv_var->valmap;
    ocKeySegment **fit_key = new ocKeySegment *[iv_statespace];
    double **fit_prob = new double *[iv_statespace];
    double *fit_dv_prob = new double[dv_card];
    double *fit_key_prob = new double[iv_statespace];
    int *fit_rule = new int[iv_statespace];
    bool *fit_tied = new bool[iv_statespace];
    double *fit_dv_expected = new double[iv_statespace];
    ocKeySegment **alt_key = new ocKeySegment *[iv_statespace];
    double **alt_prob = new double *[iv_statespace];
    double *alt_key_prob = new double[iv_statespace];
    int *alt_rule = new int[iv_statespace];
    ocKeySegment **input_key = new ocKeySegment *[iv_statespace];
    double **input_freq = new double *[iv_statespace];
    double *input_dv_freq = new double[dv_card];
    double *input_key_freq = new double[iv_statespace];
    //int *input_rule = new int[iv_statespace];
    ocKeySegment **test_key;
    double **test_freq;
    double *test_dv_freq;
    double *test_key_freq;
    int *test_rule;
    if (test_sample_size > 0) {
        test_key = new ocKeySegment *[iv_statespace];
        test_freq = new double *[iv_statespace];
        test_dv_freq = new double[dv_card];
        test_key_freq = new double[iv_statespace];
        test_rule = new int[iv_statespace];
    }

    // Allocate space for keys and frequencies
    ocKeySegment *temp_key;
    double *temp_double_array;
    for (int i = 0; i < iv_statespace; i++) {
        fit_key_prob[i] = 0.0;
        alt_key_prob[i] = 0.0;
        input_key_freq[i] = 0.0;
        fit_dv_expected[i] = 0.0;

        temp_key = new ocKeySegment[key_size];
        for (int j = 0; j < key_size; j++)
            temp_key[j] = DONT_CARE;
        fit_key[i] = temp_key;

        temp_key = new ocKeySegment[key_size];
        for (int j = 0; j < key_size; j++)
            temp_key[j] = DONT_CARE;
        alt_key[i] = temp_key;

        temp_key = new ocKeySegment[key_size];
        for (int j = 0; j < key_size; j++)
            temp_key[j] = DONT_CARE;
        input_key[i] = temp_key;

        temp_double_array = new double[dv_card];
        for (int k = 0; k < dv_card; k++)
            temp_double_array[k] = 0.0;
        fit_prob[i] = temp_double_array;

        temp_double_array = new double[dv_card];
        for (int k = 0; k < dv_card; k++)
            temp_double_array[k] = 0.0;
        alt_prob[i] = temp_double_array;

        temp_double_array = new double[dv_card];
        for (int k = 0; k < dv_card; k++)
            temp_double_array[k] = 0.0;
        input_freq[i] = temp_double_array;
    }
    if (test_sample_size > 0.0) {
        for (int i = 0; i < iv_statespace; i++) {
            test_key_freq[i] = 0.0;

            temp_key = new ocKeySegment[key_size];
            for (int j = 0; j < key_size; j++)
                temp_key[j] = DONT_CARE;
            test_key[i] = temp_key;

            temp_double_array = new double[dv_card];
            for (int k = 0; k < dv_card; k++)
                temp_double_array[k] = 0.0;
            test_freq[i] = temp_double_array;
        }
    }

    for (int i = 0; i < dv_card; i++) {
        fit_dv_prob[i] = 0.0;
        input_dv_freq[i] = 0.0;
        if (test_sample_size > 0.0)
            test_dv_freq[i] = 0.0;
    }

    if (calcExpectedDV) {
        for (int i = 0; i < dv_card; i++)
            dv_bin_value[i] = strtod(dv_label[i], (char **) NULL);
    }

    const char *new_line = "\n", *blank_line = "\n";
    if (htmlMode) {
        new_line = "<br>\n";
        blank_line = "<br><br>\n";
    }

    const char *block_start, *head_start, *head_sep, *head_end, *head_str1, *head_str2, *head_str3, *head_str4;
    const char *row_start, *block_end, *row_start2, *row_start3, *row_end, *row_sep, *row_sep2, *line_sep;

    // Set appropriate format
    int sep_style = htmlMode ? 0 : separator;
    switch (sep_style) {
        case 0:
            block_start = "<table border=0 cellpadding=0 cellspacing=0>\n";
            head_start = "<tr><th>";
            head_sep = "</th><th>";
            head_end = "</th></tr>\n";
            head_str1 = "</th><th colspan=2 class=r1>calc.&nbsp;q(DV|IV)";
            head_str2 = "</th><th colspan=2 class=r1>obs.&nbsp;p(DV|IV)"; // used twice
            head_str3 = "</th><th colspan=2>%%correct";
            head_str4 = "</th><th colspan=2>Test&nbsp;Data";
            row_start = "<tr><td align=right>";
            row_start2 = "<tr class=r1><td align=right>";
            row_start3 = "<tr class=em><td align=right>";
            row_sep = "</td><td align=right>";
            row_sep2 = "</td><td align=left>";
            row_end = "</td></tr>\n";
            block_end = "</table><br>\n";
            line_sep = "<hr>\n";
            break;
        case 1:
            block_start = "";
            head_start = "";
            head_sep = "\t";
            head_end = "\n";
            head_str1 = "\tcalc. q(DV|IV)\t";
            head_str2 = "\tobs. p(DV|IV)\t";
            head_str3 = "\t%%correct\t";
            head_str4 = "\tTest Data\t";
            row_start = row_start2 = row_start3 = "";
            row_sep = row_sep2 = "\t";
            row_end = "\n";
            block_end = "\n";
            line_sep = "-------------------------------------------------------------------------\n";
            break;
        case 2:
            block_start = "";
            head_start = "";
            head_sep = ",";
            head_end = "\n";
            head_str1 = ",calc. q(DV|IV),";
            head_str2 = ",obs. p(DV|IV),";
            head_str3 = ",%%correct,";
            head_str4 = ",Test Data,";
            row_start = row_start2 = row_start3 = "";
            row_sep = row_sep2 = ",";
            row_end = "\n";
            block_end = "\n";
            line_sep = "-------------------------------------------------------------------------\n";
            break;
        case 3:
            block_start = "";
            head_start = "";
            head_sep = "    ";
            head_end = "\n";
            head_str1 = "calc. q(DV|IV)";
            head_str2 = "obs. p(DV|IV)";
            head_str3 = "%%correct";
            head_str4 = "Test Data";
            row_start = row_start2 = row_start3 = "";
            row_sep = row_sep2 = "    ";
            row_end = "\n";
            block_end = "\n";
            line_sep = "-------------------------------------------------------------------------\n";
            break;
    }
    if (rel != NULL)
        fprintf(fd, "%s%s%s", blank_line, line_sep, blank_line);

    int *ind_vars = new int[var_count];
    int iv_count = iv_rel->getIndependentVariables(ind_vars, var_count);
    if (rel == NULL) {
        fprintf(fd, "Conditional DV (D) (%%) for each IV composite state for the Model %s.", model->getPrintName());
        fprintf(fd, new_line);
        fprintf(fd, "IV order: ");
        for (int i = 0; i < iv_count; i++) {
            fprintf(fd, "%s", var_list->getVariable(ind_vars[i])->abbrev);
        }
        fprintf(fd, " (");
        for (int i = 0; i < iv_count; i++) {
            if (i > 0)
                fprintf(fd, "; ");
            fprintf(fd, "%s", var_list->getVariable(ind_vars[i])->name);
        }
        fprintf(fd, ").");
    } else {
        if (rel->isStateBased()) {
            fprintf(fd, "Conditional DV (D) (%%) for each IV composite state for the Submodel %s.", relModel->getPrintName());
            fprintf(fd, new_line);
//            fprintf(fd, "(For component relations, the Data and Model parts of the table are equal, so only one is given.)");
        } else {
            fprintf(fd, "Conditional DV (D) (%%) for each IV composite state for the Relation %s.", rel->getPrintName());
            fprintf(fd, new_line);
            fprintf(fd, "(For component relations, the Data and Model parts of the table are equal, so only one is given.)");
        }
    }
    if (defaultFitModel != NULL) {
        fprintf(fd, new_line);
        if (use_alt_default == false) {
            if (model == defaultFitModel) {
                fprintf(fd,
                        "The specified alternate default model cannot be identical to the fitted model. Using independence model instead.");
            } else {
                fprintf(fd,
                        "The specified alternate default model is not a child of the fitted model. Using independence model instead.");
            }
        } else {
            fprintf(fd, "Using %s as alternate default model.", defaultFitModel->getPrintName());
        }
    }
    fprintf(fd, blank_line);

    int index = 0;
    int keys_found = 0;
    int alt_keys_found = 0;
    ocKeySegment *key;
    double temp_value;
    long *index_sibs = new long[dv_card];
    int key_compare, num_sibs;

    int fit_table_size = fit_table->getTupleCount();
    int input_table_size = input_table->getTupleCount();
    int alt_table_size = 0;
    if (use_alt_default) {
        alt_table_size = alt_table->getTupleCount();
    }
    int test_table_size = 0;
    if (test_sample_size > 0.0) {
        test_table_size = test_table->getTupleCount();
    }
    int dv_value, best_i;

    // Count up the total frequencies for each DV value in the reference data, for the output table.
    for (int i = 0; i < input_table_size; i++) {
        temp_key = input_table->getKey(i);
        dv_value = ocKey::getKeyValue(temp_key, key_size, var_list, dv_index);
        input_dv_freq[dv_value] += input_table->getValue(i) * sample_size;
    }

    // Find the most common DV value, for test data predictions when no input data exists.
    int input_default_dv = manager->getDefaultDVIndex();

    for (int i = 0; i < iv_statespace; i++) {
        fit_rule[i] = input_default_dv;
        alt_rule[i] = input_default_dv;
        fit_tied[i] = false;
        if (test_sample_size > 0.0)
            test_rule[i] = input_default_dv;
    }

    ocKeySegment *temp_key_array = new ocKeySegment[key_size];
    double f1, f2;
    double precision = 1.0e10;

    // Work out the alternate default table, if requested
    if (use_alt_default) {
        while (alt_keys_found < iv_statespace) {
            if (index >= alt_table_size)
                break;

            key = alt_table->getKey(index);
            index++;
            memcpy((int *) temp_key_array, (int *) key, key_size * sizeof(ocKeySegment));
            ocKey::setKeyValue(temp_key_array, key_size, var_list, dv_index, DONT_CARE);

            key_compare = 1;
            for (int i = 0; i < alt_keys_found; i++) {
                key_compare = ocKey::compareKeys((ocKeySegment *) alt_key[i], temp_key_array, key_size);
                if (key_compare == 0)
                    break;
            }
            if (key_compare == 0)
                continue;
            memcpy((int *) alt_key[alt_keys_found], (int *) temp_key_array, sizeof(ocKeySegment) * key_size);
            num_sibs = 0;
            ocKey::getSiblings(key, var_list, alt_table, index_sibs, dv_index, &num_sibs);
            best_i = 0;
            temp_value = 0.0;
            for (int i = 0; i < num_sibs; i++) {
                temp_value += alt_table->getValue(index_sibs[i]);
                ocKeySegment *temp_key = alt_table->getKey(index_sibs[i]);
                dv_value = ocKey::getKeyValue(temp_key, key_size, var_list, dv_index);
                alt_prob[alt_keys_found][dv_value] = alt_table->getValue(index_sibs[i]);
                if (i == 0) {
                    best_i = dv_value;
                } else {
                    f1 = round(alt_prob[alt_keys_found][dv_value] * precision);
                    f2 = round(alt_prob[alt_keys_found][best_i] * precision);
                    if (f1 > f2) {
                        best_i = dv_value;
                    } else if (fabs(f1 - f2) < 1) {
                        if (manager->getDvOrder(best_i) > manager->getDvOrder(dv_value))
                            best_i = dv_value;
                    }
                }
            }
            alt_key_prob[alt_keys_found] = temp_value;
            alt_rule[alt_keys_found] = best_i;
            alt_keys_found++;
        }
    }

    bool tie_flag;
    index = 0;
    // Loop till we have as many keys as the size of the IV statespace (at most)
    while (keys_found < iv_statespace) {
        // Also break the loop if index exceeds the tupleCount for the table
        if (index >= fit_table_size)
            break;

        // Get the key and value for the current index
        key = fit_table->getKey(index);
        index++;
        memcpy((int *) temp_key_array, (int *) key, key_size * sizeof(ocKeySegment));
        ocKey::setKeyValue(temp_key_array, key_size, var_list, dv_index, DONT_CARE);

        // Check if this key has appeared yet
        key_compare = 1;
        for (int i = 0; i < keys_found; i++) {
            key_compare = ocKey::compareKeys((ocKeySegment *) fit_key[i], temp_key_array, key_size);
            // If zero is returned, keys are equal, meaning this key has appeared before.  Stop checking.
            if (key_compare == 0)
                break;
        }
        // If this was a duplicate key, move on to the next index.
        if (key_compare == 0)
            continue;
        // Otherwise, this is a new key.  Place it into the keylist
        memcpy((int *) fit_key[keys_found], (int *) temp_key_array, sizeof(ocKeySegment) * key_size);

        // Get the siblings of the key
        num_sibs = 0;
        ocKey::getSiblings(key, var_list, fit_table, index_sibs, dv_index, &num_sibs);

        tie_flag = false;
        best_i = 0;
        temp_value = 0.0;
        for (int i = 0; i < num_sibs; i++) {
            // Sum up the total probability values among the siblings
            temp_value += fit_table->getValue(index_sibs[i]);
            // Get the key for this sibling
            ocKeySegment *temp_key = fit_table->getKey(index_sibs[i]);
            // Get the dv_value for the sibling
            dv_value = ocKey::getKeyValue(temp_key, key_size, var_list, dv_index);
            // Compute & store the conditional value for the sibling (in probability)
            fit_prob[keys_found][dv_value] = fit_table->getValue(index_sibs[i]);
            // Next keep track of what the best number correct is
            // (ie, if this is the first sib, it's the best.  After that, compare & keep the best.)
            if (i == 0) {
                best_i = dv_value;
            } else {
                // Probabilities are rounded so checks for gt/lt/eq are not skewed by the imprecision in floating point numbers.
                f1 = round(fit_prob[keys_found][dv_value] * precision);
                f2 = round(fit_prob[keys_found][best_i] * precision);
                if (f1 > f2) {
                    best_i = dv_value;
                    tie_flag = false;
                    // If there is a tie, break it by choosing the DV state that was most common in the input data.
                    // If there is a tie in frequency, break it alphabetically, using the actual DV values.
                } else if (fabs(f1 - f2) < 1) {
                    tie_flag = true;
                    if (use_alt_default) {
                        // use temp_key_array, which still contains the current key without the DV
                        // mark unused variables in key as don't care
                        for (int j = 0; j < alt_missing_count; j++)
                            ocKey::setKeyValue(temp_key_array, key_size, var_list, alt_missing_indices[j], DONT_CARE);
                        // find the key in the alt table
                        for (int j = 0; j < alt_keys_found; j++) {
                            key_compare = ocKey::compareKeys((ocKeySegment *) alt_key[j], temp_key_array, key_size);
                            if (key_compare == 0) {
                                // if present, compare the alt values for best_i and dv_value
                                f1 = round(alt_prob[j][dv_value] * precision);
                                f2 = round(alt_prob[j][best_i] * precision);
                                if (f1 > f2)
                                    best_i = dv_value;
                                else if (fabs(f1 - f2) < 1)
                                    // there is a tie in the alternate default as well, so revert to independence
                                    if (manager->getDvOrder(best_i) > manager->getDvOrder(dv_value))
                                        best_i = dv_value;
                                break;
                            }
                        }
                        // if the key was not found in the alt default table, revert to independence
                        if (key_compare != 0)
                            if (manager->getDvOrder(best_i) > manager->getDvOrder(dv_value))
                                best_i = dv_value;
                    } else {
                        if (manager->getDvOrder(best_i) > manager->getDvOrder(dv_value))
                            best_i = dv_value;
                    }
                }
            }
        }
        // Save the total probability for these siblings.
        fit_key_prob[keys_found] = temp_value;
        // Save the final best rule's index.
        fit_rule[keys_found] = best_i;
        fit_tied[keys_found] = tie_flag;
        // And move on to the next key...
        keys_found++;
    }

    // Sort out the input (reference) data
    // Loop through all the input data
    int input_counter = 0;
    index = 0;
    int fit_index = 0;
    while (input_counter < iv_statespace) {
        if (index >= input_table_size)
            break;

        key = input_table->getKey(index);
        index++;
        memcpy((int *) temp_key_array, (int *) key, key_size * sizeof(ocKeySegment));
        ocKey::setKeyValue(temp_key_array, key_size, var_list, dv_index, DONT_CARE);

        // Check if this key has appeared yet -- we only do this so siblings aren't counted multiple times.
        key_compare = 1;
        for (int i = 0; i < input_counter; i++) {
            key_compare = ocKey::compareKeys((ocKeySegment *) input_key[i], temp_key_array, key_size);
            if (key_compare == 0)
                break;
        }
        // If this was a duplicate, move on
        if (key_compare == 0)
            continue;
        // Otherwise, the key is new to the input list, we add it into the list.
        memcpy((int *) input_key[input_counter], (int *) temp_key_array, sizeof(ocKeySegment) * key_size);

        // Next, find out if the index of this key is in the fit_key list, to keep the keys in the same order
        for (fit_index = 0; fit_index < keys_found; fit_index++) {
            key_compare = ocKey::compareKeys((ocKeySegment *) fit_key[fit_index], temp_key_array, key_size);
            if (key_compare == 0)
                break;
        }
        // If the key wasn't found, we must add it to the fit list as well
        if (key_compare != 0) {
            memcpy((int *) fit_key[keys_found], (int *) temp_key_array, sizeof(ocKeySegment) * key_size);
            if (use_alt_default) {
                for (int j = 0; j < alt_missing_count; j++)
                    ocKey::setKeyValue(temp_key_array, key_size, var_list, alt_missing_indices[j], DONT_CARE);
                for (int j = 0; j < alt_keys_found; j++) {
                    key_compare = ocKey::compareKeys((ocKeySegment *) alt_key[j], temp_key_array, key_size);
                    if (key_compare == 0)
                        fit_rule[keys_found] = alt_rule[j];
                }
            }
            fit_tied[keys_found] = true;
            fit_index = keys_found;
            keys_found++;
        }

        // Get the siblings of this key
        num_sibs = 0;
        ocKey::getSiblings(key, var_list, input_table, index_sibs, dv_index, &num_sibs);

        temp_value = 0.0;
        for (int i = 0; i < num_sibs; i++) {
            // Sum up the total frequencies among the siblings
            temp_value += input_table->getValue(index_sibs[i]);
            ocKeySegment *temp_key = input_table->getKey(index_sibs[i]);
            dv_value = ocKey::getKeyValue(temp_key, key_size, var_list, dv_index);
            input_freq[fit_index][dv_value] = input_table->getValue(index_sibs[i]) * sample_size;
        }
        input_key_freq[fit_index] = temp_value * sample_size;
        input_counter++;
    }

    // Compute performance on test data, if present
    // This section will reuse many of the variables from above, since it is performing a similar task.
    if (test_sample_size > 0.0) {
        int test_counter = 0;
        index = 0;
        fit_index = 0;
        while (test_counter < iv_statespace) {
            if (index >= test_table_size)
                break;

            key = test_table->getKey(index);
            index++;
            memcpy((int *) temp_key_array, (int *) key, key_size * sizeof(ocKeySegment));
            ocKey::setKeyValue(temp_key_array, key_size, var_list, dv_index, DONT_CARE);

            // Check if this key has appeared yet -- we only do this so siblings aren't counted multiple times.
            key_compare = 1;
            for (int i = 0; i < test_counter; i++) {
                key_compare = ocKey::compareKeys((ocKeySegment *) test_key[i], temp_key_array, key_size);
                if (key_compare == 0)
                    break;
            }
            // If this was a duplicate, move on
            if (key_compare == 0)
                continue;
            // Otherwise, the key is new to the test list, we add it into the list.
            memcpy((int *) test_key[test_counter], (int *) temp_key_array, sizeof(ocKeySegment) * key_size);

            // Next, find out the index of this key in the fit_key list, to keep the keys in the same order
            for (fit_index = 0; fit_index < keys_found; fit_index++) {
                key_compare = ocKey::compareKeys((ocKeySegment *) fit_key[fit_index], temp_key_array, key_size);
                if (key_compare == 0)
                    break;
            }
            // If the key wasn't found, we must add it to the fit list as well
            if (key_compare != 0) {
                memcpy((int *) fit_key[keys_found], (int *) temp_key_array, sizeof(ocKeySegment) * key_size);
                if (use_alt_default) {
                    for (int j = 0; j < alt_missing_count; j++)
                        ocKey::setKeyValue(temp_key_array, key_size, var_list, alt_missing_indices[j], DONT_CARE);
                    for (int j = 0; j < alt_keys_found; j++) {
                        key_compare = ocKey::compareKeys((ocKeySegment *) alt_key[j], temp_key_array, key_size);
                        if (key_compare == 0)
                            fit_rule[keys_found] = alt_rule[j];
                    }
                }
                fit_tied[keys_found] = true;
                fit_index = keys_found;
                keys_found++;
            }

            // Get the siblings of this key
            num_sibs = 0;
            ocKey::getSiblings(key, var_list, test_table, index_sibs, dv_index, &num_sibs);

            best_i = 0;
            temp_value = 0.0;
            for (int i = 0; i < num_sibs; i++) {
                // Sum up the total frequencies among the siblings
                temp_value += test_table->getValue(index_sibs[i]);
                ocKeySegment *temp_key = test_table->getKey(index_sibs[i]);
                dv_value = ocKey::getKeyValue(temp_key, key_size, var_list, dv_index);
                test_freq[fit_index][dv_value] = test_table->getValue(index_sibs[i]) * test_sample_size;
                if (i == 0) {
                    best_i = dv_value;
                } else {
                    // Note: tie-breaking doesn't matter here, since we are only concerned with finding the best frequency possible,
                    // not with the specific rule that results in that frequency.
                    if (test_freq[fit_index][dv_value] > test_freq[fit_index][best_i])
                        best_i = dv_value;
                }
            }

            test_key_freq[fit_index] = temp_value * test_sample_size;
            test_rule[fit_index] = best_i;
            test_counter++;
        }
    }

    int *dv_order = new int[dv_card];
    // Get an ordering for the dv values, so they can be displayed in ascending order.
    orderIndices(dv_label, dv_card, dv_order);

    // Compute marginals of DV states for the totals row
    double *marginal = new double[dv_card];
    for (int i = 0; i < dv_card; i++) {
        marginal[i] = 0.0;
        for (int j = 0; j < iv_statespace; j++) {
            marginal[i] += fit_prob[j][i];
        }
    }

    // Compute sums for the totals row
    double total_correct = 0.0; // correct on input data by fit rule
    for (int i = 0; i < iv_statespace; i++) {
        total_correct += input_freq[i][fit_rule[i]];
    }

    // Compute marginals & sums for test data, if present.
    double test_by_fit_rule, test_by_test_rule;
    if (test_sample_size > 0.0) {
        for (int i = 0; i < dv_card; i++) {
            for (int j = 0; j < iv_statespace; j++) {
                test_dv_freq[i] += test_freq[j][i];
            }
        }
        test_by_fit_rule = 0.0; // correct on test data by fit rule
        test_by_test_rule = 0.0; // correct on test data by test rule (best possible performance)
        for (int i = 0; i < iv_statespace; i++) {
            test_by_fit_rule += test_freq[i][fit_rule[i]];
            test_by_test_rule += test_freq[i][test_rule[i]];
        }
    }

    int dv_ccount = 0;
    int dv_head_len = 0;
    for (int i = 0; i < dv_card; i++) {
        dv_head_len += strlen(dv_label[dv_order[i]]);
    }
    dv_head_len += dv_card * (strlen(row_sep) + strlen(dv_var->abbrev) + 1) + 1;
    char *dv_header = new char[dv_head_len];
    memset(dv_header, 0, dv_head_len * sizeof(char));
    for (int i = 0; i < dv_card; i++) {
        dv_ccount += snprintf(dv_header + dv_ccount, dv_head_len - dv_ccount, "%s=", dv_var->abbrev);
        dv_ccount += snprintf(dv_header + dv_ccount, dv_head_len - dv_ccount, "%s", dv_label[dv_order[i]]);
        dv_ccount += snprintf(dv_header + dv_ccount, dv_head_len - dv_ccount, row_sep);
    }

    // Header, Row 1
    fprintf(fd, "%s%sIV", block_start, head_start);
    for (int i = 0; i < iv_count; i++)
        fprintf(fd, "%s", head_sep);
    fprintf(fd, "|%sData%s", head_sep, head_sep);
    for (int i = 0; i < dv_card; i++)
        fprintf(fd, "%s", head_sep);
    if (rel == NULL || rel->isStateBased()) {
        fprintf(fd, "|%sModel", head_sep);
        for (int i = 0; i < dv_card; i++)
            fprintf(fd, "%s", head_sep);
    }
    fprintf(fd, "%s%s", head_sep, head_sep);
    if (calcExpectedDV == true)
        fprintf(fd, "%s%s", head_sep, head_sep);
    if (test_sample_size > 0.0)
        fprintf(fd, "%s|%s%s%s", head_sep, head_str4, head_sep, head_sep);
    fprintf(fd, head_end);

    // Header, Row 2
    fprintf(fd, "%s", head_start);
    for (int i = 0; i < iv_count; i++)
        fprintf(fd, "%s", head_sep);
    fprintf(fd, "|%s%s%s", head_sep, head_str2, head_sep);
    if (dv_card > 2)
        for (int i = 2; i < dv_card; i++)
            fprintf(fd, head_sep);
    if (rel == NULL || rel->isStateBased()) {
        fprintf(fd, "|%s%s", head_str1, head_sep);
        if (dv_card > 2)
            for (int i = 2; i < dv_card; i++)
                fprintf(fd, head_sep);
    }
    fprintf(fd, "%s%s", head_sep, head_sep);
    if (calcExpectedDV == true)
        fprintf(fd, "%s%s", head_sep, head_sep);
    if (test_sample_size > 0.0) {
        fprintf(fd, "%s|%s%s", head_sep, head_sep, head_str2);
        if (dv_card > 2)
            for (int i = 2; i < dv_card; i++)
                fprintf(fd, head_sep);
        fprintf(fd, head_str3);
    }
    fprintf(fd, head_end);

    // Header, Row 3
    fprintf(fd, "%s", row_start);
    for (int i = 0; i < iv_count; i++)
        fprintf(fd, "%s%s", var_list->getVariable(ind_vars[i])->abbrev, row_sep);
    fprintf(fd, "|%sfreq%s%s", row_sep, row_sep, dv_header);
    if (rel == NULL || rel->isStateBased())
        fprintf(fd, "|%s%s", row_sep, dv_header);
    fprintf(fd, "rule%s#correct%s%%correct", row_sep, row_sep);
    if (calcExpectedDV == true)
        fprintf(fd, "%sE(DV)%sMSE", row_sep, row_sep);

    if (test_sample_size > 0.0) {
        fprintf(fd, "%s|%sfreq%s%sby rule%sbest", row_sep, row_sep, row_sep, dv_header, row_sep);
        if (calcExpectedDV == true)
            fprintf(fd, "%sMSE", row_sep);
    }
    fprintf(fd, row_end);

    // Body of Table
    double mean_squared_error = 0.0;
    double total_test_error = 0.0;
    double temp_percent = 0.0;
    int keyval;
    int keysize = input_data->getKeySize();
    const char *keyvalstr;

    int *key_order = new int[iv_statespace];        // Created a sorted order for the IV states, so they appear in order in the table
    for (int i = 0; i < iv_statespace; i++)
        key_order[i] = i;
    sort_var_list = var_list;
    sort_count = iv_count;
    sort_vars = ind_vars;
    sort_keys = fit_key;
    qsort(key_order, iv_statespace, sizeof(int), sortKeys);
    int i;
    // For each of the model's keys (i.e., each row of the table)...
    for (int order_i = 0; order_i < iv_statespace; order_i++) {
        i = key_order[order_i];
        if (input_key_freq[i] == 0.0) {
            if (test_sample_size > 0.0) {
                if (test_key_freq[i] == 0.0) {
                    continue;
                }
            } else {
                continue;
            }
        }
        // Also, switch the bgcolor of each row from grey to white, every other row. (If not in HTML, this does nothing.)
        if (order_i % 2)
            fprintf(fd, row_start);
        else
            fprintf(fd, row_start2);
        // Print the states of the IV in separate columns
        for (int j = 0; j < iv_count; j++) {
            keyval = ocKey::getKeyValue(fit_key[i], keysize, var_list, ind_vars[j]);
            keyvalstr = var_list->getVarValue(ind_vars[j], keyval);
            fprintf(fd, "%s%s", keyvalstr, row_sep);
        }
        fprintf(fd, "|%s%.3f%s", row_sep, input_key_freq[i], row_sep);
        // Print out the conditional probabilities of the training data
        temp_percent = 0.0;
        for (int j = 0; j < dv_card; j++) {
            if (input_key_freq[i] == 0.0)
                temp_percent = 0.0;
            else {
                temp_percent = input_freq[i][dv_order[j]] / input_key_freq[i] * 100.0;
            }
            fprintf(fd, "%.3f%s", temp_percent, row_sep);
        }
        if (rel == NULL || rel->isStateBased()) {
            fprintf(fd, "|%s", row_sep);
            // Print out the percentages for each of the DV states
            for (int j = 0; j < dv_card; j++) {
                if (fit_key_prob[i] == 0)
                    temp_percent = 0.0;
                else {
                    temp_percent = fit_prob[i][dv_order[j]] / fit_key_prob[i] * 100.0;
                    if (calcExpectedDV == true) {
                        fit_dv_expected[i] += temp_percent / 100.0 * dv_bin_value[dv_order[j]];
                    }
                }
                fprintf(fd, "%.3f%s", temp_percent, row_sep);
            }
        }
        // Print the DV state of the best rule. If there was no input to base the rule on, use the default rule.
        fprintf(fd, "%c%s%s", fit_tied[i] ? '*' : ' ', dv_label[fit_rule[i]], row_sep);
        // Number correct (of the input data, based on the rule from fit)
        fprintf(fd, "%.3f%s", input_freq[i][fit_rule[i]], row_sep);
        // Percent correct (of the input data, based on the rule from fit)
        if (input_key_freq[i] == 0)
            fprintf(fd, "%.3f", 0.0);
        else
            fprintf(fd, "%.3f", input_freq[i][fit_rule[i]] / input_key_freq[i] * 100.0);
        mean_squared_error = 0.0;
        if (calcExpectedDV == true) {
            fprintf(fd, "%s%.3f", row_sep, fit_dv_expected[i]);
            if (input_key_freq[i] > 0.0) {
                for (int j = 0; j < dv_card; j++) {
                    temp_percent = fit_dv_expected[i] - dv_bin_value[dv_order[j]];
                    mean_squared_error += temp_percent * temp_percent * input_freq[i][dv_order[j]];
                }
                mean_squared_error /= input_key_freq[i];
            } else
                mean_squared_error = 0;
            fprintf(fd, "%s%.3f", row_sep, mean_squared_error);
        }

        // Print test results, if present
        if (test_sample_size > 0.0) {
            // Frequency in test data
            fprintf(fd, "%s|%s%.3f", row_sep, row_sep, test_key_freq[i]);
            // Print out the percentages for each of the DV states
            for (int j = 0; j < dv_card; j++) {
                fprintf(fd, row_sep);
                if (test_key_freq[i] == 0.0)
                    fprintf(fd, "%.3f", 0.0);
                else
                    fprintf(fd, "%.3f", test_freq[i][dv_order[j]] / test_key_freq[i] * 100.0);
            }
            fprintf(fd, row_sep);
            if (test_key_freq[i] == 0.0)
                fprintf(fd, "%.3f", 0.0);
            else
                fprintf(fd, "%.3f", test_freq[i][fit_rule[i]] / test_key_freq[i] * 100.0);
            fprintf(fd, row_sep);
            if (test_key_freq[i] == 0.0)
                fprintf(fd, "%.3f", 0.0);
            else
                fprintf(fd, "%.3f", test_freq[i][test_rule[i]] / test_key_freq[i] * 100.0);
            mean_squared_error = 0.0;
            if (calcExpectedDV == true) {
                if (test_key_freq[i] > 0.0) {
                    for (int j = 0; j < dv_card; j++) {
                        temp_percent = fit_dv_expected[i] - dv_bin_value[dv_order[j]];
                        mean_squared_error += temp_percent * temp_percent * test_freq[i][dv_order[j]];
                    }
                    mean_squared_error /= test_key_freq[i];
                } else
                    mean_squared_error = 0;
                fprintf(fd, "%s%.3f", row_sep, mean_squared_error);
                total_test_error += mean_squared_error * test_key_freq[i];
            }
        }
        fprintf(fd, row_end);
    }

    // Footer, Row 1 (totals)
    double total_expected_value = 0.0;
    fprintf(fd, row_start3);
    for (int i = 0; i < iv_count; i++)
        fprintf(fd, "%s", row_sep);
    fprintf(fd, "|%s%.3f%s", row_sep, sample_size, row_sep);
    // Print the training data DV totals
    for (int j = 0; j < dv_card; j++) {
        fprintf(fd, "%.3f%s", input_dv_freq[dv_order[j]] / sample_size * 100.0, row_sep);
    }
    if (rel == NULL || rel->isStateBased()) {
        fprintf(fd, "|%s", row_sep);
        // Print the marginals for each DV state
        for (int j = 0; j < dv_card; j++) {
            fprintf(fd, "%.3f%s", marginal[dv_order[j]] * 100.0, row_sep);
            if (calcExpectedDV == true)
                total_expected_value += marginal[dv_order[j]] * dv_bin_value[dv_order[j]];
        }
    }
    fprintf(fd, "%s%s%.3f%s%.3f", dv_var->valmap[input_default_dv], row_sep, total_correct, row_sep,
            total_correct / sample_size * 100.0);
    if (calcExpectedDV == true) {
        fprintf(fd, "%s%.3f", row_sep, total_expected_value);
        temp_percent = mean_squared_error = 0.0;
        for (int j = 0; j < dv_card; j++) {
            temp_percent = total_expected_value - dv_bin_value[dv_order[j]];
            mean_squared_error += temp_percent * temp_percent * input_dv_freq[dv_order[j]];
        }
        mean_squared_error /= sample_size;
        fprintf(fd, "%s%.3f", row_sep, mean_squared_error);
    }
    double default_percent_on_test = 0.0;
    double best_percent_on_test = 0.0;
    double fit_percent_on_test = 0.0;
    if (test_sample_size > 0.0) {
        fprintf(fd, "%s|%s%.3f%s", row_sep, row_sep, test_sample_size, row_sep);
        // Print the test marginals for each DV state
        for (int j = 0; j < dv_card; j++) {
            temp_percent = test_dv_freq[dv_order[j]] / test_sample_size * 100.0;
            //if (temp_percent > default_percent_on_test) default_percent_on_test = temp_percent;
            fprintf(fd, "%.3f%s", temp_percent, row_sep);
        }
        default_percent_on_test = test_dv_freq[input_default_dv] / test_sample_size * 100.0;
        fit_percent_on_test = test_by_fit_rule / test_sample_size * 100.0;
        best_percent_on_test = test_by_test_rule / test_sample_size * 100.0;
        fprintf(fd, "%.3f%s%.3f", fit_percent_on_test, row_sep, best_percent_on_test);
        if (calcExpectedDV == true)
            fprintf(fd, "%s%.3f", row_sep, total_test_error / test_sample_size);
    }
    fprintf(fd, row_end);
    // Footer, Row 2 (repeat of Header, Row 3)
    fprintf(fd, row_start);
    for (int i = 0; i < iv_count; i++)
        fprintf(fd, "%s", row_sep);
    fprintf(fd, "|%sfreq%s%s", row_sep, row_sep, dv_header);
    if (rel == NULL || rel->isStateBased())
        fprintf(fd, "|%s%s", row_sep, dv_header);
    fprintf(fd, "rule%s#correct%s%%correct", row_sep, row_sep);
    if (calcExpectedDV == true)
        fprintf(fd, "%sE(DV)%sMSE", row_sep, row_sep);

    if (test_sample_size > 0.0) {
        fprintf(fd, "%s|%sfreq%s%sby rule%sbest", row_sep, row_sep, row_sep, dv_header, row_sep);
        if (calcExpectedDV == true)
            fprintf(fd, "%sMSE", row_sep);
    }
    fprintf(fd, "%s%s", row_end, block_end);

    // Print out a summary of the performance on the test data, if present.
    if (test_sample_size > 0.0) {
        fprintf(fd, "%s%sPerformance on Test Data%s", block_start, row_start, row_end);
        fprintf(fd,
                "%sIndependence Model rule:%s%.3f%%%scorrect (using rule from the independence model of the training data)%s",
                row_start, row_sep, default_percent_on_test, row_sep2, row_end);
        fprintf(fd, "%sModel rule:%s%.3f%%%scorrect%s%s", row_start, row_sep, fit_percent_on_test, row_sep2,
                use_alt_default ? " (augmented by alternate default model)" : "", row_end);
        fprintf(fd, "%sBest possible:%s%.3f%%%scorrect (using rules optimal for the test data)%s", row_start, row_sep,
                best_percent_on_test, row_sep2, row_end);
        temp_percent = best_percent_on_test - default_percent_on_test;
        if ((temp_percent) != 0)
            temp_percent = (fit_percent_on_test - default_percent_on_test) / temp_percent * 100.0;
        fprintf(fd, "%sImprovement by model:%s%.3f%%%s(Model - Default) / (Best - Default)%s%s", row_start, row_sep,
                temp_percent, row_sep2, row_end, block_end);
    }
    if (use_alt_default)
        fprintf(fd, "* Rule selected using the alternate default model.");
    else
        fprintf(fd, "* Rule selected using the independence model.");
    fprintf(fd, blank_line);

    // Print the alternate default table, if required.
    if (use_alt_default) {
        int *alt_ind_vars = new int[var_count];
        int alt_iv_count = alt_relation->getIndependentVariables(alt_ind_vars, var_count);
        fprintf(fd, blank_line);
        fprintf(fd, "Conditional DV for the alternate default model %s.", defaultFitModel->getPrintName());
        fprintf(fd, blank_line);
        // Header, Row 1
        fprintf(fd, "%s%sIV", block_start, head_start);
        for (int i = 0; i < alt_iv_count; i++)
            fprintf(fd, "%s", head_sep);
        fprintf(fd, "|%sModel", head_sep);
        for (int i = 0; i < dv_card; i++)
            fprintf(fd, "%s", head_sep);
        fprintf(fd, head_end);
        // Header, Row 2
        fprintf(fd, "%s", head_start);
        for (int i = 0; i < alt_iv_count; i++)
            fprintf(fd, "%s", head_sep);
        fprintf(fd, "|%s%s", head_str1, head_sep);
        if (dv_card > 2)
            for (int i = 2; i < dv_card; i++)
                fprintf(fd, head_sep);
        fprintf(fd, head_end);
        // Header, Row 3
        fprintf(fd, "%s", row_start);
        for (int i = 0; i < alt_iv_count; i++)
            fprintf(fd, "%s%s", var_list->getVariable(alt_ind_vars[i])->abbrev, row_sep);
        fprintf(fd, "|%s%srule", row_sep, dv_header);
        fprintf(fd, row_end);
        // Body of table
        for (int i = 0; i < alt_keys_found; i++) {
            if (i % 2)
                fprintf(fd, row_start);
            else
                fprintf(fd, row_start2);
            for (int j = 0; j < alt_iv_count; j++) {
                keyval = ocKey::getKeyValue(alt_key[i], keysize, var_list, alt_ind_vars[j]);
                keyvalstr = var_list->getVarValue(alt_ind_vars[j], keyval);
                fprintf(fd, "%s%s", keyvalstr, row_sep);
            }
            fprintf(fd, "|%s", row_sep);
            for (int j = 0; j < dv_card; j++) {
                if (alt_key_prob[i] == 0)
                    temp_percent = 0.0;
                else
                    temp_percent = alt_prob[i][dv_order[j]] / alt_key_prob[i] * 100.0;
                fprintf(fd, "%.3f%s", temp_percent, row_sep);
            }
            fprintf(fd, "%s", dv_label[alt_rule[i]]);
            fprintf(fd, row_end);
        }
        // Footer, Row 1
        fprintf(fd, row_start3);
        for (int i = 0; i < alt_iv_count; i++)
            fprintf(fd, "%s", row_sep);
        fprintf(fd, "|%s", row_sep);
        for (int j = 0; j < dv_card; j++)
            fprintf(fd, "%.3f%s", marginal[dv_order[j]] * 100.0, row_sep);
        fprintf(fd, "%s%s", dv_var->valmap[input_default_dv], row_sep);
        fprintf(fd, row_end);
        // Footer, Row 2
        fprintf(fd, "%s", row_start);
        for (int i = 0; i < alt_iv_count; i++)
            fprintf(fd, "%s", row_sep);
        fprintf(fd, "|%s%srule", row_sep, dv_header);
        fprintf(fd, "%s%s", row_end, block_end);
    }

    // If this is the entire model (not just a relation), print tables for each of the component relations,
    // if there are more than two of them (for VB) or more than 3 (for SB).
    if ((rel == NULL) && ((model->getRelationCount() > 2 && !model->isStateBased()) || (model->isStateBased() && model->getRelationCount() > 3))) {
        for (int i = 0; i < model->getRelationCount(); i++) {
            if (model->getRelation(i)->isIndependentOnly())
                continue;
            if (model->getRelation(i)->isDependentOnly())
                continue;
            printConditional_DV(fd, model->getRelation(i), calcExpectedDV);
        }
    }

    delete[] dv_order;
    delete[] dv_header;
    delete[] marginal;
    delete[] index_sibs;
    delete[] temp_key_array;
    delete[] ind_vars;
    for (int i = 0; i < iv_statespace; i++) {
        delete[] input_freq[i];
        delete[] input_key[i];
        delete[] alt_key[i];
        delete[] alt_prob[i];
        delete[] fit_key[i];
        delete[] fit_prob[i];
    }
    delete[] input_freq;
    delete[] input_key;
    delete[] alt_key;
    delete[] alt_prob;
    delete[] fit_key;
    delete[] fit_prob;
    delete[] alt_rule;
    delete[] alt_key_prob;
    delete[] input_key_freq;
    delete[] input_dv_freq;
    delete[] fit_dv_prob;
    delete[] fit_key_prob;
    delete[] fit_tied;
    delete[] fit_rule;
    delete[] fit_dv_expected;
    if (rel == NULL) {
        delete fit_table;
    }
    if (test_table) {
        for (int i = 0; i < iv_statespace; i++) {
            delete[] test_freq[i];
            delete[] test_key[i];
        }
        delete[] test_freq;
        delete[] test_key;
        delete[] test_key_freq;
        delete[] test_dv_freq;
        delete[] test_rule;
        delete test_table;
    }
    delete input_table;

    return;
}

