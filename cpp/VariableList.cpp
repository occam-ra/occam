#include "VariableList.h"
#include "_Core.h"
#include <assert.h>
#include <string.h>
#include <stdio.h>
#include <ctype.h>

static const char *findUpper(const char *cp) {
    //-- find next upper case character, indicating beginning of a variable
    for (;;) {
        char ch = *(++cp); // go to next one first
        if (ch == '\0')
            return 0;
        if (isupper(ch))
            break;
    }
    return cp;
}

static void normalizeCase(char *cp) {
    //-- convert first letter to upper case, rest lower
    if (islower(*cp))
        *cp = toupper(*cp);
    while (*(++cp)) {
        if (isupper(*cp))
            *cp = tolower(*cp);
    }
}

VariableList::VariableList(int maxVars) {
    //const int MAX_MASK = 4;  // max number of variables = this * (bits in a long)
    maxVarCount = maxVars;
    varCount = 0;
    varCountDF = 0;
    vars = new Variable[maxVars];
    maxAbbrevLen = 0;
    //Anjali
    //maxVarMask = MAX_MASK;
    //maskVars = new long[MAX_MASK];
    //for (int i = 0; i < MAX_MASK; i++)
    //maskVars[i]=0;
    noUseMaskSize = maxVars;
    noUseMask = new bool[noUseMaskSize];
    for (int i = 0; i < noUseMaskSize; i++)
        noUseMask[i] = false;
}

VariableList::~VariableList() {
    for (int i = 0; i < varCount; i++) {
        Variable *varp = vars + i;
        for (int j = 0; j < varp->cardinality; j++) {
            delete varp->valmap[j];
        }
        if (varp->exclude)
            delete[] varp->exclude;
    }
    if (vars)
        delete vars;
    if (noUseMask)
        delete[] noUseMask;
}

long VariableList::size() {
    return maxVarCount * sizeof(Variable) + sizeof(VariableList);
}

/*
 * addVariable - add a new variable to the end of the list.  Grow the list storage, if needed
 */
int VariableList::addVariable(const char *name, const char *abbrev, int cardinality, bool dv, bool rebin,
        int old_card) {
    const int GROWTH_FACTOR = 2;
    while (varCount >= maxVarCount) {
        vars = (Variable*) growStorage(vars, maxVarCount*sizeof(Variable), GROWTH_FACTOR);
        maxVarCount *= GROWTH_FACTOR;
    }
    Variable *varp = vars + (varCount++);
    varCountDF++;
    while (varCountDF > noUseMaskSize) {
        noUseMask = (bool*) growStorage(noUseMask, noUseMaskSize*sizeof(bool), GROWTH_FACTOR);
        noUseMaskSize *= GROWTH_FACTOR;
    }
    strncpy(varp->name, name, MAXNAMELEN);
    varp->name[MAXNAMELEN] = '\0';
    strncpy(varp->abbrev, abbrev, MAXABBREVLEN);
    varp->abbrev[MAXABBREVLEN] = '\0';
    normalizeCase(varp->abbrev);
    varp->cardinality = cardinality;
    varp->dv = dv;
    varp->rebin = rebin;
    varp->old_card = old_card;
    varp->exclude = NULL;

    //-- keep track of longest name (helps storage allocation of other functions
    int abbrevLen = strlen(varp->abbrev);
    if (abbrevLen > maxAbbrevLen)
        maxAbbrevLen = abbrevLen;

    //-- compute size of variable in the key; must have enough space for
    //-- 0..cardinality (to include the DONT_CARE value)
    int size = 0;
    while (cardinality != 0) { // log2 computation for small numbers
        size++;
        cardinality >>= 1;
    }
    varp->size = size;

    //-- for first variable, treat as special case
    if (varp == vars) {
        varp->segment = 0;
        varp->shift = KEY_SEGMENT_BITS - varp->size;
    } else {
        //-- see if key will fit in the last segment of the key
        Variable *lastp = varp - 1; // previous entry
        if (lastp->shift >= varp->size) {
            varp->segment = lastp->segment;
            varp->shift = lastp->shift - varp->size;
        } else { // add a new segment
            varp->segment = lastp->segment + 1;
            varp->shift = KEY_SEGMENT_BITS - varp->size;
        }
    }
    // build a mask with bits in the variable positions
    KeySegment keytemp = 1;
    varp->mask = ((keytemp << varp->size) - 1) << varp->shift; // 1's in the var positions

    // clear the value map
    memset(varp->valmap, 0, MAXCARDINALITY * sizeof(const char *));

    return 0;
}

/*
 * isVarInUse - checks if the variable's value has to be ignored since it is marked as of
 * type 0. Returns 0 if the variable is marked (that is to be ignored), returns 1 for good.
 */
int VariableList::isVarInUse(int varCounter) {
    if (varCounter >= noUseMaskSize)
        return 1;
    return !(noUseMask[varCounter]);
}

/*
 * markForNoUse - mark in a mask if this variable needs to be ignored
 * grow mask size, if needed also increment varCountDF
 */
int VariableList::markForNoUse() {
    //grow the mask if the variables are more than the mask can hold
    const int GROWTH_FACTOR = 2;
    while (varCountDF >= noUseMaskSize) {
        noUseMask = (bool*) growStorage(noUseMask, noUseMaskSize*sizeof(bool), GROWTH_FACTOR);
        noUseMaskSize *= GROWTH_FACTOR;
    }
    noUseMask[varCountDF] = true;
    varCountDF++;
    return 0;
}

/* This function returns the new binning value for an old one for a given variable
 */
int VariableList::getNewValue(int index, char * old_value, char*new_value) {
    int i = 0, k;
    int chr;
    char myvalue[100];
    for (chr = 0; chr < 100; chr++) {
        if (old_value[chr] == '\0' || isspace(old_value[chr]) || old_value[chr] == ',')
            break;
        else
            myvalue[chr] = old_value[chr];
    }
    myvalue[chr] = '\0';
    //exclude case
    if ((vars + index)->exclude != NULL) {
        if ((k = strcmp(myvalue, (vars + index)->exclude)) == 0)
            return -1;
        else {
            strcpy(new_value, myvalue);
            return 1;
        }
    }
    for (;;) {
        char * value_new = (vars + index)->oldnew[1][i];
        char * value_old = (vars[index]).oldnew[0][i];
        if (value_new == NULL)
            break;
        if ((k = strcmp(value_old, myvalue)) == 0) {
            strcpy(new_value, value_new);
            return 1;
        } else if ((k = strcmp(value_old, "*")) == 0) {
            strcpy(new_value, value_new);
            return 1;
        }
        i++;
    }
    return -1;
}

/**
 * getKeySize - return the number of required segments for a key.  This is determined
 * by just looking at the last variable
 */
int VariableList::getKeySize() {
    if (varCount == 0)
        return 0;
    else
        return 1 + vars[varCount - 1].segment;
}

/**
 * getVariable - return a pointer to a variable structure, by index
 */
Variable *VariableList::getVariable(int index) {
    return vars + index;
}

/**
 * dump - generate debug output to stdout
 */
void VariableList::dump() {
    printf("VariableList: varCount = %d, maxVarCount=%d\n", varCount, maxVarCount);
    printf("\tDV\tCard\tSeg\tSiz\tShft\tName\t\tAbb\tMask\n");
    for (int i = 0; i < varCount; i++) {
        Variable *v = vars + i;
        printf("\t%d\t%d\t%d\t%d\t%d\t%8s\t%s\t%0*lx\t", v->dv, v->cardinality, v->segment, v->size, v->shift, v->name,
                v->abbrev, sizeof(KeySegment) * 2, v->mask);
        for (int j = 0; j < v->cardinality; j++) {
            printf("%s\t", getVarValue(i,j));
        }
        printf("\n");
    }
    printf("No-Use Mask:");
    for (int i = 0; i < noUseMaskSize; i++)
        noUseMask[i] ? printf("1") : printf("0");
    printf("\n");
}

/**
 * Generate a printable variable list, given a list of variable indices
 */
void VariableList::getPrintName(char *str, int maxlength, int count, int *vars1, int *states) {
    int i;
    char *cp = str;
    maxlength--;
    for (i = 0; i < count; i++) {
        if (maxlength <= 0)
            break; // no room
        int varID = vars1[i];
        char *name = getVariable(varID)->abbrev;
        int len = strlen(name);
        strncpy(cp, name, maxlength);
        maxlength -= len;
        cp += len;
        if (states != NULL) {
            int stateID = 0;
            // left here needs modification
            stateID = states[i];
            if (stateID != DONT_CARE) {
                if (vars[varID].dv && vars[varID].cardinality == 2) {
                    // do nothing
                } else {
                    char **map = vars[varID].valmap;
                    int len1 = strlen(map[stateID]);
                    strncpy(cp, map[stateID], maxlength);
                    maxlength -= len1;
                    cp += len1;
                }
            }
        }
        if (i < count - 1) { // at least one more to go
            if (maxlength <= 0)
                break;
        }
    }
    assert(maxlength >= 0);
    *cp = '\0';
}

/**
 * Determine length of printed name. This is conservative but not exact.
 */
int VariableList::getPrintLength(int count, int *vars, int *states) {
    int len = 0;
    for (int i = 0; i < count; i++) {
        len += strlen(getVariable(vars[i])->abbrev);
        if (states != NULL) {
            if (states[i] != DONT_CARE) {
                len += strlen(getVariable(vars[i])->valmap[states[i]]);
            }
        }
    }
    return len + 1;
}

/**
 * Determine if this is a directed system. This is the case if any variables are
 * flagged as dependent.
 */
bool VariableList::isDirected() {
    for (int i = 0; i < varCount; i++) {
        if (vars[i].dv)
            return true;
    }
    return false;
}

int VariableList::getDV() {
    for (int i = 0; i < varCount; i++) {
        if (vars[i].dv)
            return i;
    }
    return -1;
}

/**
 * Generate variable list from a name. This can then be used to construct a relation
 */
int VariableList::getVariableList(const char *name, int *varlist) {
    const char *cp = name;
    const char *cp2;
    char vname[MAXNAMELEN];
    int pos = 0;
    while (cp != NULL) {
        int i, len;
        cp2 = findUpper(cp);
        if (cp2 != NULL) { // not the last variable
            len = cp2 - cp;
            strncpy(vname, cp, len);
            vname[len] = '\0';
            cp = cp2;
        } else { // last variable
            strcpy(vname, cp);
            cp = NULL;
        }
        for (i = 0; i < varCount; i++) {
            if (strcasecmp(vars[i].abbrev, vname) == 0)
                break;
        }
        if (i >= varCount) {
            fprintf(stdout, "variable %s not found\n", vname);
            fflush(stdout);
            return 0; // bad name
        } else {
            varlist[pos++] = i;
        }
    }
    return pos;
}

int VariableList::getVarStateList(const char *name, int *varlist, int *stlist) {
    const char *cp = name;
    const char *cp2;
    char vname[MAXNAMELEN];
    char vname1[MAXNAMELEN];
    char sname[MAXNAMELEN];
    int value = 0;
    int pos = 0;
    while (cp != NULL) {
        int i = 0, len, j;
        cp2 = findUpper(cp);
        if (cp2 != NULL) { // not the last variable
            len = cp2 - cp;
            strncpy(vname, cp, len);
            vname[len] = '\0';
            j = sscanf(vname, "%[A-Za-z]%[0-9.]", vname1, sname);
            cp = cp2;
        } else { // last variable
            strcpy(vname, cp);
            j = sscanf(vname, "%[a-zA-Z]%[0-9.]", vname1, sname);
            cp = NULL;
        }
        for (i = 0; i < varCount; i++) {
            if (strcasecmp(vars[i].abbrev, vname1) == 0)
                break;
        }
        if (i >= varCount) {
            fprintf(stdout, "variable %s not found\n", vname);
            fflush(stdout);
            return 0; // bad name
        } else {
            varlist[pos] = i;
            if (j == 2) {
                value = getVarValueIndex(i, sname);
                stlist[pos] = value;
            } else {
                stlist[pos] = DONT_CARE;
            }
            pos++;
        }
    }
    return pos;
}

int VariableList::getVarValueIndex(int varindex, const char *value) {
    int index = 0;
    char **map = vars[varindex].valmap;
    char myvalue[100];
    int chr;
    int cardinality = vars[varindex].cardinality;
    //-- extract the name as a separate string
    for (chr = 0; chr < 100; chr++) {
        if (value[chr] == '\0' || isspace(value[chr]) || (value[chr] == ','))
            break;
        else
            myvalue[chr] = value[chr];
    }
    myvalue[chr] = '\0';
    //-- find this value in the value map. Stop on first empty entry
    while (index < cardinality) {
        if (map[index] == NULL)
            break;
        if (strcmp(myvalue, map[index]) == 0)
            return index;
        index++;
    }
    //-- if we have room, add this value. Otherwise return error.
    if (index < cardinality) {
        map[index] = new char[strlen(value) + 1];
        strcpy(map[index], myvalue);
        return index;
    } else
        return -1;
}

const char *VariableList::getVarValue(int varindex, int valueindex) {
    char **map = vars[varindex].valmap;
    const char *value = map[valueindex];
    if (value)
        return value;
    else
        return "?";
}

bool VariableList::checkCardinalities() {
    bool result = true;
    for (int varindex = 0; varindex < varCount; varindex++) {
        int cardinality = vars[varindex].cardinality;
        char **map = vars[varindex].valmap;
        int valuecount = 0;
        while (map[valuecount] != NULL)
            valuecount++;
        if (valuecount < cardinality) {
            printf(
                    "Warning: input data cardinality for variable %s (%s) is %d, but was specified as %d. The lower value will be used.\n",
                    vars[varindex].name, vars[varindex].abbrev, valuecount, cardinality);
            vars[varindex].cardinality = valuecount;
        } else if (valuecount > cardinality) {
            printf(
                    "ERROR: input data cardinality for variable %s (%s) is %d, but was specified as %d. OCCAM will quit.\n",
                    vars[varindex].name, vars[varindex].abbrev, valuecount, cardinality);
            result = false;
        }
    }
    int seenDV = 0;
    char* seenAbbrev = nullptr;
    for (int varindex = 0; varindex < varCount; varindex++) {
        if (vars[varindex].dv) {
            seenDV += 1;
            if (seenDV > 1) {
                vars[varindex].dv = false;
            } else {
                seenAbbrev = vars[varindex].abbrev;
            }
        }

    }
    if (seenDV > 1) {
        printf("NOTE: Occam allows only one DV, so variables other than %s have been converted into IVs.\n", seenAbbrev);
    }
    return result;
}
