/* Copyright 2000, Portland State University Systems Science Program.  All Rights Reserved
 */

/**
 * ocVariableList.cpp - implements the VariableList class. This keeps information about
 * variables in a problem, including name, cardinality, and the position of the variable
 * value in the tuple key.
 */
 
#include "ocCore.h"
#include "_ocCore.h"
#include <assert.h>
#include <string.h>
#include <stdio.h>
#include <ctype.h>
#include "ocWin32.h"

static const char *findUpper(const char *cp)
{
	//-- find next upper case character, indicating beginning of a variable
	for(;;) {
		char ch = *(++cp);	// go to next one first
		if (ch == '\0') return 0;
		if (isupper(ch)) break;
	}
	return cp;
}

static void normalizeCase(char *cp)
{
	//-- convert first letter to upper case, rest lower
	if (islower(*cp)) *cp = toupper(*cp);
	while (*(++cp)) {
		if (isupper(*cp)) *cp = tolower(*cp);
	}
}

ocVariableList::ocVariableList(int maxVars)
{
	//const int MAX_MASK = 4;  // max number of variables = this * (bits in a long)
	maxVarCount = maxVars;
	varCount = 0;
        varCountDF=0;
	vars = new ocVariable[maxVars];
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


ocVariableList::~ocVariableList()
{
	for (int i = 0; i < varCount; i++) {
		ocVariable *varp = vars + i;
		for (int j = 0; j < varp->cardinality; j++) {
			delete varp->valmap[j];
		}
	}
	if (vars) delete vars;
}


long ocVariableList::size()
{
  return maxVarCount * sizeof(ocVariable) + sizeof(ocVariableList);
}


/*
 * addVariable - add a new variable to the end of the list.  Grow the list
 * storage, if needed
 */
int ocVariableList::addVariable(const char *name, const char *abbrev, int cardinality, bool dv, bool rebin, int old_card)
{
	const int GROWTH_FACTOR = 2;
	while (varCount >= maxVarCount) {
		vars = (ocVariable*) growStorage(vars, maxVarCount*sizeof(ocVariable), GROWTH_FACTOR);
		maxVarCount *= GROWTH_FACTOR;
	}
	ocVariable *varp = vars + (varCount++);
	varCountDF++;
	strncpy(varp->name, name, MAXNAMELEN); varp->name[MAXNAMELEN] = '\0';
	strncpy(varp->abbrev, abbrev, MAXABBREVLEN); varp->abbrev[MAXABBREVLEN] = '\0';
	normalizeCase(varp->abbrev);
	varp->cardinality = cardinality;
	varp->dv = dv;
	varp->rebin = rebin;
	varp->old_card = old_card;
	varp->exclude = NULL;

	//-- keep track of longest name (helps storage allocation of other functions
	int abbrevLen = strlen(varp->abbrev);
	if (abbrevLen > maxAbbrevLen) maxAbbrevLen = abbrevLen;
	
	//-- compute size of variable in the key; must have enough space for
	//-- 0..cardinality (to include the DONT_CARE value)
	int size = 0;
	while (cardinality != 0) {	// log2 computation for small numbers
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
		ocVariable *lastp = varp - 1;	// previous entry
		if (lastp->shift >= varp->size) {
			varp->segment = lastp->segment;
			varp->shift = lastp->shift - varp->size;
		} else {	// add a new segment
			varp->segment = lastp->segment + 1;
			varp->shift = KEY_SEGMENT_BITS - varp->size;
		}
	}
	// build a mask with bits in the variable positions
	varp->mask = ((1 << varp->size) - 1) << varp->shift;	// 1's in the var positions

	// clear the value map
	memset(varp->valmap, 0, MAXCARDINALITY * sizeof(const char *));

	return 0;
}


//Anjali
/*
 * good - checks if the variables value have to be just ignored since it is marked as of 
 * type 0. Returns 0 if the variable is marked (that is to be ignored), return 1 for good.
 */
int ocVariableList::good(int varCounter)
{
	return !(noUseMask[varCounter]);
}


//Anjali
/*
 * markForNoUse - mark in a mask if this variable needs to be ignored
 * grow mask size, if needed also increment varCountDF
 */
int ocVariableList::markForNoUse()
{
	//grow the mask if the variables are more than the mask can hold
	const int GROWTH_FACTOR = 2;
	while (varCountDF >= noUseMaskSize) {
		noUseMask = (bool*) growStorage(noUseMask, noUseMaskSize*sizeof(bool), GROWTH_FACTOR);
		noUseMaskSize *= GROWTH_FACTOR;
	}
		
	noUseMask[varCountDF] = true;
	//printf("... marking %d as no use. %d\n", varCountDF, (int)noUseMask[varCountDF]);
	//for (int i = 0; i < noUseMaskSize; i++)
		//noUseMask[i] ? printf("1") : printf("0");
	//printf("\n");
	varCountDF++;
	return 0;
}

/* This function returns the new binning value for an old one for a given variable
*/
int ocVariableList::getnewvalue(int index,char * old_value,char*new_value){
        int i=0,k;
	int chr;
	char myvalue[100];
	for (chr = 0; chr < 100; chr++) {
		if (old_value[chr] == '\0' || isspace(old_value[chr])) break;
		else myvalue[chr] = old_value[chr];
	}
	myvalue[chr]='\0';
	//exclude case
	if((vars+index)->exclude!=NULL){
		if((k=strcmp(myvalue,(vars+index)->exclude))==0)return -1;
		else {
			strcpy(new_value,myvalue);
			return 1;
		}
	}
        for(;;){
                char * value_new=(vars+index)->oldnew[1][i];
                char * value_old=(vars[index]).oldnew[0][i];
                if(value_new==NULL)break;
                if((k=strcmp(value_old,myvalue))==0){
			strcpy(new_value,value_new);
		//	printf("old value %s,new value %s\n",value_old,new_value);
			return 1;
		}
                else if((k=strcmp(value_old,"*"))==0){
			strcpy(new_value,value_new);
		//	printf("old value %s,new value %s\n",value_old,new_value);
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
int ocVariableList::getKeySize()
{
	if (varCount == 0) return 0;
	else return 1 + vars[varCount-1].segment;
}


/**
 * getVariable - return a pointer to a variable structure, by index
 */
ocVariable *ocVariableList::getVariable(int index)
{
	return vars + index;
}


/**
 * dump - generate debug output to stdout
 */
void ocVariableList::dump()
{
	printf("ocVariableList: varCount = %d, maxVarCount=%d\n", varCount, maxVarCount);
	printf("\tDV\tCard\tSeg\tSiz\tShft\tName\t\tAbb\tMask\n");
	for (int i = 0; i < varCount; i++) {
		ocVariable *v = vars + i;
		printf("\t%d\t%d\t%d\t%d\t%d\t%8s\t%s\t%016lx\t", v->dv, v->cardinality, v->segment, v->size, v->shift, v->name, v->abbrev, v->mask);
		for(int j=0; j < v->cardinality; j++) {
		    printf("%s\t", v->valmap[j]);
		}
		printf("\n");
	}
	printf("\n");
	for (int i = 0; i < noUseMaskSize; i++)
		noUseMask[i] ? printf("1") : printf("0");
	printf("\n");
//	printf("%d %d %d\n", sizeof(int), sizeof(long), sizeof(long long));
}

/**
 * Generate a printable variable list, given a list of variable indices
 */
void ocVariableList::getPrintName(char *str, int maxlength, int count, int *vars1, int *states)
{
	int i;
	char *cp = str;
	maxlength--;
	for (i = 0; i < count; i++) {
		if (maxlength <= 0) break;	// no room
		int varID = vars1[i];
		char *name = getVariable(varID)->abbrev;
		int len = strlen(name);
		strncpy(cp, name, maxlength);
		maxlength -= len;
		cp += len;
		if(states != 0) {
			int stateID = 0;
			// left here needs modification
			stateID = states[i];
			if(stateID != DONT_CARE){
				char **map = vars[varID].valmap;
				int len1 = strlen(map[stateID]);
				strncpy(cp, map[stateID], maxlength);
				maxlength -= len1;
				cp += len1;
			}
			
		}
		if (i < count-1) { // at least one more to go
			if (maxlength <= 0) break;
			//*cp++ = '.';
			maxlength--;
		}
	}
	assert(maxlength >= 0);
	*cp = '\0';
}

/**
 * Determine length of printed name. This is conservative but not exact.
 */
int ocVariableList::getPrintLength(int count, int *vars, bool state_b)
{
	int i;
	int len = 0;
	for (i = 0; i < count; i++) {
		int varID = vars[i];
		char *name = getVariable(varID)->abbrev;
		int card = getVariable(varID)->cardinality;
//not consistent...state id and state value are to different things
		card = card / 10;
		len += strlen(name);
		len=len+card+1;
		//len += strlen(name) + 1; // an extra for separator character
	}
	return len;
}

/**
 * Determine if this is a directed system. This is the case if any variables are
 * flagged as dependent.
 */
bool ocVariableList::isDirected()
{
	for (int i = varCount - 1; i >= 0; i--) {
		if (vars[i].dv) return true;
	}
	return false;
}

int ocVariableList::getDV()
{
	for (int i = varCount - 1; i >= 0; i--) {
		if (vars[i].dv) return i;
	}
	return -1;
}

/**
 * Generate variable list from a name. This can then be used to construct a relation
 */
int ocVariableList::getVariableList(const char *name, int *varlist)
{
	const char *cp = name;
	const char *cp2;
	char vname[MAXNAMELEN];
	int pos = 0;
	while (cp != NULL) {
		int i, len;
		cp2 = findUpper(cp);
		if (cp2 != NULL) {	// not the last variable
			len = cp2 - cp;
			strncpy(vname, cp, len);
			vname[len] = '\0';
			cp = cp2;
		}
		else {	// last variable
			strcpy(vname, cp);
			cp = NULL;
		}
		for (i = 0; i < varCount; i++) {
			if (strcasecmp(vars[i].abbrev, vname) == 0) break;
		}
		if (i >= varCount) {
			fprintf(stderr, "variable %s not found\n", vname);
			return 0;	// bad name
		}
		else {
			varlist[pos++] = i;
		}
	}
	return pos;
}
int ocVariableList::getVar_StateList(const char *name, int *varlist,int *stlist)
{
	const char *cp = name;
	const char *cp2;
	char vname[MAXNAMELEN];
	char vname1[MAXNAMELEN];
	char sname[MAXNAMELEN];
	int value=0;
	int pos = 0;
	while (cp != NULL) {
		int i=0, len,j;
		cp2 = findUpper(cp);
		if (cp2 != NULL) {	// not the last variable
			len = cp2 - cp;
			strncpy(vname, cp, len);
			vname[len] = '\0';
			j=sscanf(vname, "%[A-Z,a-z]%[0-9,.]",vname1,sname);
			/*if(j==2){printf("vname is %s and vanme 1 is %s and sname is %s\n",vname,vname1,sname);
			}
			else if(j==1)printf("vname1 is %s\n",vname1);*/
			cp = cp2;
		}
		else {	// last variable
			strcpy(vname, cp);
			j=sscanf(vname,"%[a-z,A-Z]%[0-9,.]",vname1,sname);
			//printf("vname is %s\n",vname);
			//printf("vname1 is %s\n",vname1);
			cp = NULL;
		}
		//printf("i is %d\n and varcount is %d",i,varCount);
		for (i = 0; i < varCount; i++) {
			if (strcasecmp(vars[i].abbrev, vname1) == 0) break;
		}
		if (i >= varCount) {
			fprintf(stderr, "variable %s not found\n", vname);
			return 0;	// bad name
		}
		else {
			//printf("I is %d\n",i);
			varlist[pos] = i;
			if(j==2){
			value = getVarValueIndex(i,sname);
			//printf("value for sname %s is %d\n",sname,value);
			stlist[pos]=value;
			}else{
			stlist[pos]=DONT_CARE; 
			}
			pos++;
		}
	}
	return pos;
}

int ocVariableList::getVarValueIndex(int varindex, const char *value)
{
	int index = 0;
	char **map = vars[varindex].valmap;
	char myvalue[100];
	int chr;
	int cardinality = vars[varindex].cardinality;

	//-- extract the name as a separate string
	for (chr = 0; chr < 100; chr++) {
		if (value[chr] == '\0' || isspace(value[chr])) break;
		else myvalue[chr] = value[chr];
	}
	myvalue[chr] = '\0';

	//-- find this value in the value map. Stop on first empty entry
	while (index < cardinality) {
		if (map[index] == NULL) break;
		if (strcmp(myvalue, map[index]) == 0) return index;
		index++;
	}
	//-- if we have room, add this value. Otherwise return error.
	if (index < cardinality) {
		map[index] = new char[strlen(value)+1];
		strcpy(map[index], myvalue);
		return index;
	}
	else
	return -1;
}

const char *ocVariableList::getVarValue(int varindex, int valueindex)
{
	char **map = vars[varindex].valmap;
	const char *value = map[valueindex];
	if (value) return value;
	else return "?";
}

bool ocVariableList::checkCardinalities()
{
	bool result = true;
	for (int varindex = 0; varindex < varCount; varindex++) {
		int cardinality =vars[varindex].cardinality;
		char **map = vars[varindex].valmap;
		int valuecount = 0;
		while (map[valuecount] != NULL) valuecount++;
		if (valuecount != cardinality) {
			printf("Error: input data cardinality for variable %s is %d, which is less than the specified value of %d.\n",
				vars[varindex].name, valuecount, cardinality);
			// result = false; // no longer fatal
		}
	}
	return result;
}
