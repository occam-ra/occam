/* Copyright 2000, Portland State University Systems Science Program.  All Rights Reserved
 */

/**
 * ocInput.cpp - implements functions for processing input.
 */

#include "ocInput.h"
#include "ocCore.h"
#include "ocOptions.h"
#include <stdio.h>
#include <string.h>
#include <ctype.h>
#include <stdlib.h>

struct LostVar {
        int num;
        char * ValidList[MAXCARDINALITY];
        int all; //flag to mark if all values are valid
        LostVar *next;
};

bool isLostVar(int i, LostVar ** varp, LostVar *lostvarp) {
    while (lostvarp != NULL) {
        if (lostvarp->num == i) {
            *varp = lostvarp;
            return true;
        }
        lostvarp = lostvarp->next;
    }
    return false;
}

bool KeepVal(LostVar *lostvarpt, char * var) {
    int i = 0, k;
    while (lostvarpt->ValidList[i] != NULL) {
        if (lostvarpt->all == 1)
            return true;
        else if ((k = strcmp(lostvarpt->ValidList[i], var)) == 0)
            return true;
        i++;
    }
    return false;
}

/*ReadData - read data tuples, one per line; return number of lines read
 */
long ocReadData(FILE *fin, ocVariableList *vars, ocTable *indata, LostVar *lostvarp) {
    char line[MAXLINE];
    ocKeySegment *key = 0;
    int lineno = 0;
    double tupleValue;
    LostVar *lostvarpt;
    int keysize = vars->getKeySize();
    key = new ocKeySegment[keysize];
    int varCountDF = vars->getVarCountDF(); //Anjali
    int varCount = vars->getVarCount();
    int *values, *indices;
    bool gotLine = false;
    int b_lostvar = 0;
    int flag = KEEP;
    char var[MAXLINE];
    char newvalue[MAXLINE];
    bool keepval = true;
    values = new int[varCount];
    indices = new int[varCount];
    int j = 0;
    int value = 0;
    int l = 0;
    gotLine = ocOptions::getLine(fin, line, &lineno);
    if (!gotLine) {
        printf("No data\n");
        return false;
    }
    while (gotLine) {
        char *cp = line;
        l++;
        for (int i = 0; i < varCountDF; i++) { //Anjali
            newvalue[0] = '\0';
            if (vars->isVarInUse(i)) { //Anjali
                if ((vars->getVariable(j)->rebin == true) || (vars->getVariable(j)->exclude != NULL)) {
                    vars->getNewValue(j, cp, newvalue);
                    if (newvalue[0] != '\0') {
                        value = vars->getVarValueIndex(j, newvalue);
                        if (value < 0) { // cardinality error
                            printf("Error in data, line %d: new value exceeds cardinality of variable #%d, \"%s\".\n",
                                    lineno, i, vars->getVariable(j)->abbrev);
                            printf("Data line: %s\n", line);
                            exit(1);
                        } else {
                            values[j] = value;
                            indices[j] = j;
                        }
                    } else
                        flag = DISCARD;
                } else {
                    value = vars->getVarValueIndex(j, cp);
                    if (value < 0) { // cardinality error
                        printf("Error in data, line %d: new value exceeds cardinality of variable #%d, \"%s\".\n",
                                lineno, i, vars->getVariable(j)->abbrev);
                        printf("Data line: %s\n", line);
                        exit(1);
                    } else {
                        values[j] = value;
                        indices[j] = j;
                    }
                }
                while (*cp && !(isspace(*cp) || (*cp == ',')))
                    cp++;
                while (*cp && (isspace(*cp) || (*cp == ',')))
                    cp++; // now at next value
                j++;
            } else { //Anjali
                //check if it is in LostVar list, if yes then if all its values are valid then this row of table can go
                //otherwise mark it for being removed from building a key
                if (lostvarp != NULL) {
                    b_lostvar = isLostVar(i, &lostvarpt, lostvarp);
                    if (b_lostvar) {
                        int ret = sscanf(cp, "%[^\t ]", var);
                        if (ret == 1) {
                            keepval = KeepVal(lostvarpt, var);
                            if (!keepval)
                                flag = DISCARD;
                        } else {
                            printf("something went wrong");
                            exit(1);
                        }
                    }
                }
                while (*cp && !(isspace(*cp) || (*cp == ',')))
                    cp++;
                while (*cp && (isspace(*cp) || (*cp == ',')))
                    cp++; // now at next value
            } //Anjali
        }
        j = 0;
        while (*cp && (isspace(*cp) || (*cp == ',')))
            cp++;
        if (*cp) { // there is still a tuple value on the line
            tupleValue = (double) strtod(cp, (char **) NULL);
        } else {
            tupleValue = 1;
        }
        if (flag == KEEP) {
            ocKey::buildKey(key, keysize, vars, indices, values, varCount);
            indata->sumTuple(key, tupleValue);
        }
        flag = KEEP;

        gotLine = ocOptions::getLine(fin, line, &lineno);
        //-- see if there is test data; if so, stop here
        if (strcmp(line, ":test") == 0)
            break;
        else if (line[0] == ':') {
            printf("Unrecognized directive here: %s\n", line);
            break;
        }
    }
    delete[] indices;
    delete[] values;
    delete[] key;
    return l;
}

void ocDefineVariables(ocOptions *options, ocVariableList *vars) {
    //-- variable def is "name,cardinality,type,abbrev"
    //-- types are 1=iv, 0 or 2=dv. Note that neutral systems may have all variables dv,
    //-- and we want them marked as iv, so there is a second pass below.
    void *nextp = NULL;
    const char *vardef;
    int type, cardinality;
    char name[MAXLINE + 1], abbrev[MAXLINE + 1];
    bool isdv, alldv = true;
    while (options->getOptionString("nominal", &nextp, &vardef)) {
        int count = sscanf(vardef, " %[^, \t] , %d , %d , %[A-Za-z]", name, &cardinality, &type, abbrev);
        // Should probably check if the abbrev inlcudes numbers here, rather than just ignoring them
        if (count != 4) {
            fprintf(stdout, "Error in variable definition: %s\n", vardef);
            fflush(stdout);
        } else {
            if (type != 0) { //Anjali
                isdv = type == 2;
                alldv &= isdv;
                vars->addVariable(name, abbrev, cardinality, isdv, false);
            } else {
                vars->markForNoUse();
            } //Anjali
        }
    }
    if (alldv) {
        int i;
        for (i = 0; i < vars->getVarCount(); i++)
            vars->getVariable(i)->dv = false;
    }
}

//this function is called instead of ocDefineVar if rebinning is required
//needs to be made elegant
void ocRebinDefineVar(ocOptions *options, ocVariableList *vars, LostVar ** lostvarp) {
    //-- Variable def is "name, cardinality, type, abbrev"
    //-- Types are 1=iv, 2=dv, 0=variable disregarded.
    //-- Note that neutral systems may have all variables dv,
    //-- and we want them marked as iv, so there is a second pass below.

    void *nextp = NULL;
    const char *vardef = NULL;
    LostVar * lostvarp1 = NULL;
    char * pos = NULL;
    int type = 0;
    int cardinality = 0;
    //int sp_val=-1; //assuming negative values are not there in the table
    char name[MAXLINE], abbrev[MAXLINE], rebinarray[MAXLINE], *rebin = rebinarray, rebin1[MAXLINE];
    char abbrev_temp[MAXLINE];
    bool isdv, alldv = true;
    int num_var_df = 0;
    int flag_1 = 0;
    int index_card = 0;
    char e[] = "exclude";
    int v = 0;
    int num_var_actual = 0;

    // Three cases: First, rebin string not present, so do normal stuff.  Second case, rebin string present and ';' not present,
    // so variable is not kept (marked for no use).  Third case, the rebin string present and ';' present, so variable needs to
    // be kept and second case stuff
    while (options->getOptionString("nominal", &nextp, &vardef)) {
        name[0] = '\0';
        cardinality = 0;
        type = 0;
        abbrev[0] = '\0';
        abbrev_temp[0] = '\0';
        rebin[0] = '\0';
        int count = sscanf(vardef, " %[^, \t] , %d , %d , %[^,] , %s", name, &cardinality, &type, abbrev_temp, rebin);
        num_var_df++;

        // *** We are temporarily allowing numbers in short names, for a project that Marty and Steve Shervais
        // are working on.  They've been using them for a bit, so I'm backing this code out till they're done.
        // Actually, I'm just adding 0-9 into the scan pattern.  Remove that part of it to return to letters only.
        int count2 = sscanf(abbrev_temp, "%[A-Za-z0-9]", abbrev);
        if ((count2 != 1) || (strcmp(abbrev, abbrev_temp) != 0)) {
            printf("Error in variable definition. Only letters and numbers may be used in the abbreviation: %s\n",
                    vardef);
            exit(1);
        }

        if (count < 4 || count > 5) {
            printf("Error in variable definition: %s\n", vardef);
            exit(1);
        } else {
            char *cp = rebin;
            while (*cp && isspace(*cp))
                cp++;
            if (((v = strncmp(cp, e, 7)) == 0) && type != 0) {
                //************exclude case**************
                ocVariable *varpt = NULL;
                char myvalue[100];
                //while (*cp && isspace(*cp)) cp++;
                isdv = type == 2;
                alldv &= isdv;
                vars->addVariable(name, abbrev, cardinality - 1, isdv, false);
                num_var_actual++;
                cp = cp + strlen(e);
                if (*cp != '(') {
                    printf("Error in rebinning string\n");
                    exit(1);
                }
                cp++;
                while (*cp && isspace(*cp))
                    cp++;
                //////////correct this....
                sscanf(cp, "%[^) ]", myvalue);
                cp = cp + strlen(myvalue);
                while (*cp && isspace(*cp))
                    cp++;
                if (*cp != ')') {
                    printf("Error in rebinning string\n");
                    exit(1);
                }
                varpt = vars->getVariable(num_var_actual - 1);
                if (varpt == NULL) {
                    printf("varpt is NULL\n");
                    exit(1);
                }
                varpt->exclude = new char[strlen(myvalue) + 1];
                strcpy(varpt->exclude, myvalue);
                //	printf("exclude %s\n",varpt->exclude);
            } else if ((cp[0] != '\0') && (cp[0] != '[') && (type != 0)) {
                //*****************single value to be considered
                //printf("the string to be kept %s for variable %s\n",cp,abbrev);
                vars->markForNoUse();
                if (flag_1 == 0) {
                    lostvarp1 = new LostVar; //this might have some issues
                    if (lostvarp1 == NULL) {
                        printf("error allocating mem\n");
                        exit(1);
                    }
                    flag_1 = 1;
                    *lostvarp = lostvarp1;
                    lostvarp1->next = NULL;
                } else {
                    lostvarp1->next = new LostVar; //ithis might have issues
                    lostvarp1 = lostvarp1->next;
                    lostvarp1->next = NULL;
                }
                lostvarp1->num = num_var_df - 1;
                lostvarp1->ValidList[0] = new char[strlen(cp) + 1];
                strcpy(lostvarp1->ValidList[0], cp);
                lostvarp1->ValidList[1] = NULL;
            } else if (count == 5 && (type == 1 || type == 2)) {
                //rebinning required********************rebin********************
                sscanf(rebin, "[%[^] ]]", rebin1);
                rebin[0] = '\0';
                strcpy(rebin, rebin1);
                if ((pos = strchr(rebin, 59)) == NULL) {
                    //looking for semicolon***************var lost************
                    //variable will be lost
                    int ret = 0;
                    char number[MAXLINE]; //a MAXLINE-digit long number
                    char rest[MAXLINE]; //space for rest of the string
                    int ind = 0;
                    vars->markForNoUse();
                    if (flag_1 == 0) {
                        lostvarp1 = new LostVar; //this might have some issues
                        if (lostvarp1 == NULL) {
                            printf("error allocating mem\n");
                            exit(1);
                        }
                        flag_1 = 1;
                        *lostvarp = lostvarp1;
                        lostvarp1->next = NULL;
                    } else {
                        lostvarp1->next = new LostVar; //ithis might have issues
                        lostvarp1 = lostvarp1->next;
                        lostvarp1->next = NULL;
                    }
                    lostvarp1->num = num_var_df - 1;

                    //********string format checking begins***************
                    //check to see if the string is correctly formed
                    char *loc1, *loc2, *loc3, *loc4, *loc6, *loc7;
                    cp = rebin;
                    while (*cp && isspace(*cp))
                        cp++;
                    loc1 = cp; //looking for first no.
                    loc2 = strchr(rebin, 40); //looking for '('
                    loc3 = strchr(rebin, 44); //looking for first ','
                    loc4 = strchr(rebin, 41); //looking for ')'
                    if ((loc1 == NULL) || (loc2 == NULL) || (loc4 == NULL)) {
                        printf("error 200\n");
                        printf("Error in rebinning string\n");
                        exit(1);
                    }
                    if (loc3 != NULL) {
                        if (!(loc4 > loc3 && loc3 > loc2 && loc2 > loc1)) {
                            printf("error 201\n");
                            printf("Error in rebinning string\n");
                            exit(1);
                        }
                    } else {
                        if (!(loc4 > loc2 && loc2 > loc1)) {
                            printf("error 201\n");
                            printf("Error in rebinning string\n");
                            exit(1);
                        }
                    }
                    //check to see if there are more than one '(' or ')'
                    if ((loc6 = strchr(loc2 + 1, '(')) != NULL) {
                        printf("error 204\n");
                        printf("Error in rebinning string\n");
                        exit(1);
                    }
                    if ((loc7 = strchr(loc4 + 1, ')')) != NULL) {
                        printf("error 204\n");
                        printf("Error in rebinning string\n");
                        exit(1);
                    }
                    //********string format checking ends***************
                    // look for '*', if that is present its equivalent to the 0 option
                    char *loc5;
                    if (((loc5 = strchr(rebin, 42)) != NULL)) {
                        //this is like 0 option but make sure the string is correctly formed
                        if ((loc5 > loc4) || (loc5 < loc2)) {
                            printf("error 203\n");
                            printf("Error in rebinning string\n");
                            exit(1);
                        }
                        lostvarp1->all = 1;
                        goto done1;
                    }
                    //get the list of variable values which needs to be kept in the table
                    //rest all should be lost
                    //mark those values in the cardinality size mask and go through the
                    //table and discard all unwanted
                    //no * found in the string so needs to modify the mask one bit at a time
                    if (loc5 == NULL) {
                        while (*cp && isspace(*cp))
                            cp++;
                        ret = sscanf(cp, "%[^( ](%[^; ]", number, rest);
                        if (ret == 0 || ret == 1) {
                            printf("error 111\n");
                            printf("Error in rebinning string\n");
                            exit(1);
                        }
                        cp = rest;
                        for (;;) {
                            while (*cp && isspace(*cp))
                                cp++;
                            ret = sscanf(cp, "%[^, ],%[^; ]", number, rest);
                            if (ret == 0) {
                                printf("error 111\n");
                                printf("Error in rebinning string\n");
                                exit(1);
                            }
                            // if(ret==2)
                            //       printf("number %s, and the remaining string %s\n",number,rest);
                            //if(ret==1)
                            //       printf("number %s\n",number);
                            if (ret == 2) {
                                //this is not the last number
                                lostvarp1->ValidList[ind] = new char[strlen(number) + 1];
                                strcpy(lostvarp1->ValidList[ind], number);
                                cp = rest;
                                while (*cp && isspace(*cp))
                                    cp++;
                                ///////check...
                                ind++;
                            } else if (ret == 1) {
                                ret = sscanf(number, "%[^) ])", rest);
                                lostvarp1->ValidList[ind] = new char[strlen(rest) + 1];
                                strcpy(lostvarp1->ValidList[ind], rest);
                                ind++;
                                break;
                            }
                        } //for loop
                        lostvarp1->ValidList[ind] = NULL;
                    } //no * found case there has to be an else case
                } else {
                    //variable is kept*********************var kept*************
                    //Though cardinality might need adjusting
                    //The cardinality (if rebinning is used)is eq to the number of ';'+1
                    //int oldnewTable[2][MAXCARDINALITY];
                    ocVariable *varpt = NULL;
                    int card = 1;
                    char* locator = rebin;
                    int index = 0;
                    int flag_old_1 = 0;
                    bool rebinning_f = true;
                    while ((locator = strchr(&rebin[index_card], 59)) != NULL) {
                        index_card = locator - rebin + 1;
                        card++;
                    }
                    index_card = 0;
                    //add the variable
                    if (type != 0) { //Anjali
                        isdv = type == 2;
                        alldv &= isdv;
                        vars->addVariable(name, abbrev, card, isdv, rebinning_f, cardinality);
                    } else {
                        printf("we hope we dont come here\n");
                    } //Anjali
                    num_var_actual++;
                    //state based parsing find matching brackets and stuff

                    char cur_token[MAXLINE], rest[MAXLINE];
                    char * loc1, *loc2, *loc3, *loc4, *loc5;
                    int temp = 0;
                    varpt = vars->getVariable(num_var_actual - 1);
                    if (varpt == NULL) {
                        printf("varpt is NULL\n");
                        exit(1);
                    }

                    while (temp = sscanf(rebin, "%[^; \t];%[^& ]", cur_token, rest)) {
                        cp = cur_token;
                        //if(temp==2)printf("cur_token %s and rest %s\n",cur_token,rest);
                        //else if(temp ==1)printf("cur token %s",cur_token);
                        while (*cp && isspace(*cp))
                            cp++;
                        loc1 = cp; //looking for first no.
                        loc2 = strchr(cur_token, 40); //looking for '('
                        loc3 = strchr(cur_token, 44); //looking for first ','
                        loc4 = strchr(cur_token, 41); //looking for ')'
                        if ((loc1 == NULL) || (loc2 == NULL) || (loc4 == NULL)) {
                            printf("error 206\n");
                            printf("Error in rebinning string\n");
                            exit(1);
                        }
                        if (loc3 != NULL) {
                            if (!((loc4 > loc3) && loc3 > loc2 && loc2 > loc1)) {
                                printf("error 207\n");
                                printf("Error in rebinning string\n");
                                exit(1);
                            }
                        } else {
                            if (!(loc4 > loc2 && loc2 > loc1)) {
                                printf("error 212\n");
                                printf("Error in rebinning string\n");
                                exit(1);
                            }
                        }
                        //first look for '*', if that is present
                        if (((loc5 = strchr(cur_token, 42)) != NULL)) {
                            //this is like 0 option but make sure the string is correctly formed
                            //check if * is anywhere else other than last token
                            if ((loc5 > loc4) || (loc5 < loc2) || (temp == 2)) {
                                printf("error 208\n");
                                printf("Error in rebinning string\n");
                                exit(1);
                            }
                        }
                        //checks over get to real work of extracting each nuber from token
                        //and putting it at correct place
                        char valp[MAXLINE];
                        char *cp = cur_token;
                        char rest_tok[MAXLINE];
                        char rest_tok1[MAXLINE];
                        int flag_newval = 0;
                        char * ch1 = NULL;

                        int ret = 0;
                        while (*cp && isspace(*cp))
                            cp++;
                        ret = sscanf(cp, "%[^( ](%[^) ])%[^] ]", valp, rest_tok, rest_tok1);
                        if (ret == 0 || ret == 1 || ret == 3) {
                            printf("error 111\n");
                            printf("Error in rebinning string\n");
                            exit(1);
                        }
                        varpt->oldnew[NEW_ROW][index] = new char[strlen(valp) + 1];
                        strcpy(varpt->oldnew[NEW_ROW][index], valp);
                        cp = rest_tok;
                        for (;;) {
                            while (*cp && isspace(*cp))
                                cp++;
                            ret = sscanf(cp, "%[^, ],%[^; ]", valp, rest_tok);
                            if (ret == 2 || ret == 1) {
                                if ((ch1 = strchr(valp, 42)) != NULL) {
                                    //there is a legal * and we might want do something about it
                                    if (flag_old_1 == 1) {
                                        varpt->oldnew[NEW_ROW][index] = varpt->oldnew[NEW_ROW][index - 1];
                                    }
                                    varpt->oldnew[OLD_ROW][index] = new char[1 + 1];
                                    strcpy(varpt->oldnew[OLD_ROW][index], "*");
                                    index++;
                                    goto Done;
                                    //may be a goto is better inspite of
                                    //what our grand parents told us
                                    //we need to get out of whileloop as well
                                }
                                if (flag_old_1 == 1) {
                                    varpt->oldnew[NEW_ROW][index] = varpt->oldnew[NEW_ROW][index - 1];
                                } else
                                    flag_old_1 = 1;
                                varpt->oldnew[OLD_ROW][index] = new char[strlen(valp) + 1];
                                strcpy(varpt->oldnew[OLD_ROW][index], valp);
                                index++;
                                if (ret == 2)
                                    cp = rest_tok;
                                else {
                                    flag_old_1 = 0;
                                    flag_newval = 0;
                                    break;
                                }
                            }
                        } //end of for
                        if (temp == 2)
                            rebin = rest;
                        else
                            break;
                    } //end of while for tokenizing
                    Done: varpt->oldnew[NEW_ROW][index] = NULL; //marks end of mapping

                } //end of variable is kept
                done1: rebin[0] = '\0';
                pos = NULL;
            } else {
                // Normal case no rebinning, or since the variable type is 0, the rebinning string will be ignored.
                if (type != 0) {
                    isdv = type == 2;
                    alldv &= isdv;
                    vars->addVariable(name, abbrev, cardinality, isdv, false);
                    num_var_actual++;
                    //sp_val=-1;
                } else {
                    vars->markForNoUse();
                }
            }
        }
    }
    if (alldv) {
        int i;
        for (i = 0; i < vars->getVarCount(); i++)
            vars->getVariable(i)->dv = false;
    }
    return;
}

/*
 * oldRead - read old format files.
 */
int ocReadFile(FILE *fd, ocOptions *options, ocTable **indata, ocTable **testdata, ocVariableList **vars) {
    ocVariableList *varp = NULL;
    ocTable *indatap = NULL;
    ocTable *testdatap = NULL;
    LostVar *lostvarp = NULL;
    int dataLines = 0;
    int testLines = 0;
    *vars = varp = new ocVariableList(8);
    if (fd) {
        options->readOptions(fd);
    }
    ocRebinDefineVar(options, varp, &lostvarp);
    //-- If not at end of file, there is data in this file
    if (!feof(fd)) {
        *indata = indatap = new ocTable(varp->getKeySize(), 64);
        dataLines = ocReadData(fd, varp, indatap, lostvarp);
        indatap->sort();
    }
    //-- If there's still data, then it must be test data
    if (!feof(fd)) {
        *testdata = testdatap = new ocTable(varp->getKeySize(), 64);
        testLines = ocReadData(fd, varp, testdatap, lostvarp);
        testdatap->sort();
    }
    bool result = varp->checkCardinalities();
    if (result == false)
        exit(1);
    return dataLines;
}

