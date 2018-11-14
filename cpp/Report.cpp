/*
 * Copyright © 1990 The Portland State University OCCAM Project Team
 * [This program is licensed under the GPL version 3 or later.]
 * Please see the file LICENSE in the source
 * distribution of this software for license terms.
 */

#include <math.h>
#include "attrDescs.h"
#include "_Core.h"
#include "Report.h"
#include "ManagerBase.h"
#include "Math.h"
#include <string.h>
#include <ctype.h>
#include <stdlib.h>

/* Global and static variables...
 * collected towards the top in an attempt to increase my understanding */
int attrDescCount = sizeof(attrDescriptions) / sizeof(attrDesc);
bool Report::htmlMode = false;
int Report::maxNameLength;


Report::Report(class ManagerBase *mgr) {
    manager = mgr;
    extern int searchDir;
    searchDir = -1;
    maxModelCount = 10;
    models = new Model*[maxModelCount];
    memset(models, 0, maxModelCount * sizeof(Model*));
    defaultFitModel = NULL;
    attrs = 0;
    modelCount = 0;
    attrCount = 0;
    separator = 3;
}

Report::~Report() {
    //-- models don't belong to us, so don't delete them; just the pointer block.
    delete[] models;
    delete[] attrs;
}

void Report::addModel(class Model *model) {
    const int FACTOR = 2;
    while (modelCount >= maxModelCount) {
        models = (Model**) growStorage(models, maxModelCount*sizeof(Model*), FACTOR);
        maxModelCount *= FACTOR;
    }
    models[modelCount++] = model;
}

void Report::setDefaultFitModel(class Model *model) {
    defaultFitModel = model;
}

void Report::setAttributes(const char *attrlist) {
    int listCount = 1;
    const char *cp;
    //-- count the attributes in list (commas + 1)
    for (cp = attrlist; *cp; cp++)
        if (*cp == ',')
            listCount++;

    //-- delete old list and create new one
    if (attrs) { delete[] attrs; }
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

void Report::sort(const char *attr, Direction dir) {
    extern const char *sortAttr;
    extern Direction sortDir;
    extern Direction searchDir;
    sortAttr = attr;
    sortDir = dir;
    searchDir = manager->getSearchDirection();
    qsort(models, modelCount, sizeof(Model*), sortCompare);
}

void Report::sort(class Model** models, long modelCount, const char *attr, Direction dir) {
    extern const char *sortAttr;
    extern Direction sortDir;
    sortAttr = attr;
    sortDir = dir;
    qsort(models, modelCount, sizeof(Model*), sortCompare);
}

// Print a report of the search results
void Report::print(FILE *fd) {
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
    if (manager->getSearchDirection() == Direction::Descending) {
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
    if ((manager->getSearchDirection() == Direction::Ascending) 
     && (models[0]->getAttribute(ATTRIBUTE_INCR_ALPHA) != -1)) {
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
            if (models[m]->getAttribute(ATTRIBUTE_ALPHA) < manager->alpha_threshold) {
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
                fprintf(fd, "(No Best Model by Information, since none have Alpha < %g.)\n", manager->alpha_threshold);
            else
                fprintf(fd,
                        "<tr><td colspan=8><b>(No Best Model by Information, since none have Alpha < %g.)</b></td></tr>\n", manager->alpha_threshold);
        } else {
            if (!htmlMode)
                fprintf(fd, "Best Model(s) by Information, with Alpha < %g:\n", manager->alpha_threshold);
            else
                fprintf(fd, "<tr><td colspan=8><b>Best Model(s) by Information, with Alpha < %g</b>:</td></tr>\n", manager->alpha_threshold);
            for (int m = 0; m < modelCount; m++) {
                if (models[m]->getAttribute(ATTRIBUTE_EXPLAINED_I) != bestInfoAlpha)
                    continue;
                if (models[m]->getAttribute(ATTRIBUTE_ALPHA) > manager->alpha_threshold)
                    continue;
                printSearchRow(fd, models[m], attrID, 0);
            }
        }
    }
    if (checkIncr) {
        if (showIncr) {
            if (!htmlMode)
                fprintf(fd, "Best Model(s) by Information, with all Inc. Alpha < %g:\n", manager->alpha_threshold);
            else
                fprintf(fd,
                        "<tr><td colspan=8><b>Best Model(s) by Information, with all Inc. Alpha < %g</b>:</td></tr>\n", manager->alpha_threshold);
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
        if (!htmlMode) {
            fprintf(fd, "Best Model(s) by %%C(Test):\n"); 
            fprintf(fd, "Warning: models should not be selected based on %%correct(test).\n");
        }
        else {
            fprintf(fd, "<tr><td colspan=8><b>Best Model(s) by %%C(Test)</b>:</td></tr>\n");
            fprintf(fd, "<tr><td colspan=16><b>Warning</b>: models should not be selected based on %%correct(test).</td></tr>\n");
        }
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
void Report::printSearchHeader(FILE *fd, int* attrID) {
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
void Report::printSearchRow(FILE *fd, Model* model, int* attrID, bool isOddRow) {
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

void Report::print(int fd) {
    //	int fd2 = dup(fd);	// don't close old fd
    FILE *f = fdopen(fd, "w");
    print(f);
    fflush(f);
    fclose(f);
}

void printd(double d) {
    if (isnan(d)) {
        printf("undefined");
    } else {
        printf("%0.3f", d);
    }
}

void printConfusionMatrixHTML(const char* dv_name, const char* dv_target, double tp, double fp, double tn, double fn) {
    printf("<table style='text-align:right' border=0><tr><th>Actual</th><th>|</th><th colspan=2 align=center>Rule</th></tr>");
    printf("<tr><td></td><td>|</td><td class=r1>%s%s%s</td><td class=r1>%s%s%s</td></tr>", dv_name, equals_sign(true), dv_target, dv_name, not_equals_sign(true), dv_target);
    printf("<tr><td>%s%s%s</td><td>|</td><td>TN=%0.3f</td><td>FP=%0.3f</td><td><b>AN=%0.3f</b></tr>", dv_name, equals_sign(true), dv_target, tn, fp, tn + fp);
    printf("<tr class=r1><td>%s%s%s</td><td>|</td><td>FN=%0.3f</td><td>TP=%0.3f</td><td><b>AP=%0.3f</b></tr>",dv_name, not_equals_sign(true), dv_target, fn, tp, fn + tp);
    printf("<tr><td></td><td>|</td><td><b>RN=%0.3f</b></td><td><b>RP=%0.3f</b></td><td><b>#correct=%0.3f</b></td></tr>", tn + fn, tp + fp, tp + tn);
    printf("</table>");
}

void printConfusionMatrixStatsHTML(const char* dv_name, const char* dv_target, double tp, double fp, double tn, double fn) {
    // TODO: DRY this out
    // Population totals
    const double pop = tp + fp + tn + fn;
    const double rule_pos = tp + fp;
    const double rule_neg = tn + fn;
    const double real_pos = tp + fn;
    const double real_neg = tn + fp;

    const double right = tp + tn;
    const double wrong = fp + fn;
    const double prevalence = double(real_pos) / pop;
    const double accuracy = double(right) / pop;

    // By test outcome:
    const double precision = double(tp) / rule_pos;
    const double npv = double(tn) / rule_neg;

    // By real condition:
    const double sensitivity = double(tp) / real_pos;
    const double specificity = double(tn) / real_neg;

    // F-measure
    const double f_1 = 2 * (precision * sensitivity) / (precision + sensitivity);

    // TODO : what's missing? 
    printf("<table style='text-align:right;'>");
    // TODO: comment out or remove the line below - accuracy is reported elsewhere
    printf("<tr><th>Statistic</th><th>Definition</th><th>Value</th>");
    printf("<tr class=r1><td>%%correct</td><td> correct / sample size</td><td>%.03f</td></tr>", accuracy);
    printf("<tr><td>Sensitivity (aka Recall)</td><td> (TP / AP)</td><td>");printd(sensitivity); printf("</td></tr>");
    printf("<tr class=r1><td>Specificity</td><td> (TN / AN)</td><td>"); printd(specificity); printf("</td></tr>");
    printf("<tr><td>Precision</td><td> (TP / RP)</td><td>"); printd(precision); printf("</td></tr>");
    printf("<tr class=r1><td>Negative Predictive Value</td><td> (TN / RN)</td><td>"); printd(npv); printf("</td></tr>");
    printf("<tr><td>F1 score</td><td> (precision * sensitivity) / (precision + sensitivity) </td><td>%.03f</td></tr>", f_1);
    printf("</table>");
}

void printConfusionMatrixCSV(const char* dv_name, const char* dv_target, double tp, double fp, double tn, double fn) {
      printf(",Actual,|,Rule\n");
    printf(",,|,%s%s%s,,%s%s%s\n", dv_name, equals_sign(false), dv_target, dv_name, not_equals_sign(false), dv_target);
    printf(",%s%s%s,|,TN=,%0.3f,FP=,%0.3f,AN=,%0.3f\n", dv_name, equals_sign(false), dv_target, tn, fp, tn + fp);
    printf(",%s%s%s,|,FN=,%0.3f,TP=,%0.3f,AP=,%0.3f\n",dv_name, not_equals_sign(false), dv_target, fn, tp, fn + tp);
    printf(",,|,RN=,%0.3f,RP=,%0.3f,#correct=,%0.3f\n\n", tn + fn, tp + fp, tp + tn);
}
void printConfusionMatrixStatsCSV(const char* dv_name, const char* dv_target, double tp, double fp, double tn, double fn) {
    const double pop = tp + fp + tn + fn;
    const double rule_pos = tp + fp;
    const double rule_neg = tn + fn;
    const double real_pos = tp + fn;
    const double real_neg = tn + fp;
    const double right = tp + tn;
    const double wrong = fp + fn;
    const double prevalence = double(real_pos) / pop;
    const double accuracy = double(right) / pop;
    const double precision = double(tp) / rule_pos;
    const double npv = double(tn) / rule_neg;
    const double sensitivity = double(tp) / real_pos;
    const double specificity = double(tn) / real_neg;
    const double f_1 = 2 * (precision * sensitivity) / (precision + sensitivity);
    printf(",Statistic,Definition,Value\n");
    printf(",%%correct,correct / sample size,%.03f\n", accuracy);

    printf(",Sensitivity (aka Recall), (TP / AP),"); printd(sensitivity); printf("\n");
    printf(",Specificity,(TN / AN),"); printd(specificity); printf("\n");
    printf(",Precision,(TP / RP),"); printd(precision); printf("\n");
    printf(",Negative Predictive Value,(TN / RN),"); printd(npv); printf("\n");
    printf(",>F1 score,(precision * sensitivity) / (precision + sensitivity),%.03f\n", f_1);
    printf("\n");
}

void Report::printConfusionMatrix(Model* model, Relation* rel, 
                                  const char* dv_name, const char* dv_target,
                                  double trtp, double trfp, 
                                  double trtn, double trfn,
                                  bool test, double tetp,  double tefp, 
                                  double tetn, double tefn) {
    if (dv_target < 0) { return; }
  

    if (htmlMode) printf("<br><br>"); else printf("\n\n");
    if (model == NULL) {
        const char *relname = rel->getPrintName(manager->getUseInverseNotation());
        printf("Confusion Matri%s for the Relation %s with default ('negative') state (after rebinning) %s%s%s.\n", test ? "ces" : "x", relname, dv_name, equals_sign(htmlMode), dv_target);
    } else {
        const char *mname = model->getPrintName(manager->getUseInverseNotation());
        printf("Confusion Matri%s for the Model %s with default ('negative') state (after rebinning) %s%s%s.\n", test ? "ces" : "x", mname, dv_name, equals_sign(htmlMode), dv_target);
    }

    if (htmlMode) { printf("<br><br>&nbsp;&nbsp;"); }

    printf("Confusion Matrix for Fit Rule (Training)\n");

    if(htmlMode) {
        printf("<br><br>");
        printConfusionMatrixHTML(dv_name, dv_target, trtp, trfp, trtn, trfn);
        printf("<br>&nbsp;&nbsp;Additional Statistics (Training)\n");
        printConfusionMatrixStatsHTML(dv_name, dv_target, trtp,trfp,trtn,trfn);
    } else {
        printConfusionMatrixCSV(dv_name, dv_target, trtp,trfp,trtn,trfn);
        printf(",Additional Statistics (Training)\n");
        printConfusionMatrixStatsCSV(dv_name, dv_target, trtp,trfp,trtn,trfn);
    }

    if(htmlMode) { printf("<br><br>&nbsp;&nbsp;"); }
    if(test) {
        printf("Confusion Matrix for Fit Rule (Test)\n");
        if(htmlMode) {
            printf("<br><br>");
            printConfusionMatrixHTML(dv_name, dv_target, tetp, tefp, tetn, tefn);
            printf("<br>&nbsp;&nbsp;Additional Statistics (Test)\n");
            printConfusionMatrixStatsHTML(dv_name, dv_target, tetp,tefp,tetn,tefn);
        } else {
            printConfusionMatrixCSV(dv_name, dv_target, tetp,tefp,tetn,tefn);
            printf(",Additional Statistics (Test)\n");
            printConfusionMatrixStatsCSV(dv_name, dv_target, tetp,tefp,tetn,tefn);
        }
    }
}
