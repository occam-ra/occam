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
#include "ocWin32.h"

struct attrDesc{
	const char *name;
	const char *title;
	const char *fmt;
};

static attrDesc attrDescriptions[] = {
{ATTRIBUTE_H, "H", "%12.4f"},
{ATTRIBUTE_T, "T", "%12.4f"},
{ATTRIBUTE_DF, "DF", "%14.0f"},
{ATTRIBUTE_DDF, "dDF", "%14.0f"},
{ATTRIBUTE_FIT_H, "H(IPF)", "%12.4f"},
{ATTRIBUTE_ALG_H, "H(ALG)", "%12.4f"},
{ATTRIBUTE_FIT_T, "T(IPF)", "%12.4f"},
{ATTRIBUTE_ALG_T, "T(ALG)", "%12.4f"},
{ATTRIBUTE_LOOPS, "LOOPS", "%2.0f"},
{ATTRIBUTE_EXPLAINED_I, "Inf", "%12.4f"},
{ATTRIBUTE_AIC, "dAIC", "%12.4f"},
{ATTRIBUTE_BIC, "dBIC", "%12.4f"},
{ATTRIBUTE_BP_AIC, "dAIC(BP)", "%12.4f"},
{ATTRIBUTE_BP_BIC, "dBIC(BP)", "%12.4f"},
{ATTRIBUTE_PCT_CORRECT_DATA, "%C(Data)", "%12.4f"},
{ATTRIBUTE_PCT_CORRECT_TEST, "%C(Test)", "%12.4f"},
{ATTRIBUTE_BP_EXPLAINED_I, "Inf(BP)", "%12f"},
//*******************************************************************************
{ATTRIBUTE_UNEXPLAINED_I, "Unexp Info", "%12.4f"},
{ATTRIBUTE_T_FROM_H, "T(H)", "%12.4f"},
{ATTRIBUTE_IPF_ITERATIONS, "IPF Iter", "%7.0f"},
{ATTRIBUTE_IPF_ERROR, "IPF Err", "%12.4f"},
{ATTRIBUTE_PROCESSED, "Proc", "%2.0"},
{ATTRIBUTE_IND_H, "H(Ind)", "%12.4f"},
{ATTRIBUTE_DEP_H, "H(Dep)", "%12.4f"},
{ATTRIBUTE_COND_H, "H|Model", "%12.4f"},
{ATTRIBUTE_COND_DH, "dH|Model", "%12.4f"},
{ATTRIBUTE_COND_PCT_DH, "%dH(DV)", "%12.4f"},
{ATTRIBUTE_COND_DF, "DF(Cond)", "%14.0f"},
{ATTRIBUTE_COND_DDF, "dDF(Cond)", "%14.0f"},
{ATTRIBUTE_TOTAL_LR, "LR Total", "%12.4f"},
{ATTRIBUTE_IND_LR, "LR Ind", "%12.4f"},
{ATTRIBUTE_COND_LR, "LR|Model", "%12.4f"},
{ATTRIBUTE_COND_H_PROB, "H|Model", "%12.4f"},
{ATTRIBUTE_P2, "P2", "%12.4f"},
{ATTRIBUTE_P2_ALPHA, "P2 Alpha", "%12.4f"},
{ATTRIBUTE_P2_BETA, "P2 Beta", "%12.4f"},
{ATTRIBUTE_LR, "dLR", "%12.4f"},
{ATTRIBUTE_ALPHA, "Alpha", "%12.4f"},
{ATTRIBUTE_BETA, "Beta", "%12.4f"},
{ATTRIBUTE_BP_T, "T(BP)", "%12.4f"},
{ATTRIBUTE_BP_H, "est. H(BP)", "%12.4f"},
{ATTRIBUTE_BP_UNEXPLAINED_I, "est. Unexplained(BP)", "%12.4f"},
{ATTRIBUTE_BP_ALPHA, "Alpha(BP)", "%12.4f"},
{ATTRIBUTE_BP_BETA, "Beta(BP)", "%12.4f"},
{ATTRIBUTE_BP_LR, "LR(BP)", "%12.4f"},
{ATTRIBUTE_BP_COND_H, "H|Model(BP)", "%12.4f"},
{ATTRIBUTE_BP_COND_DH, "dH|Model(BP)", "%12.4f"},
{ATTRIBUTE_BP_COND_PCT_DH, "est. %dH(DV)(BP)", "%12.4f"},
};

bool ocReport::htmlMode = false;

int attrDescCount = sizeof(attrDescriptions) / sizeof(attrDesc);

static void deleteStringTable(char **table, long stringCount)
{
	int i;
	for (i = 0; i < stringCount; i++) delete table[i];
	delete table;
}

ocReport::ocReport(class ocManagerBase *mgr)
{
	manager = mgr;
	maxModelCount = 100;
	models = new ocModel*[maxModelCount];
	memset(models, 0, 100*sizeof(ocModel*));
	attrs = 0;
	modelCount = 0;
	attrCount = 0;
	separator = 3;
}

ocReport::~ocReport()
{
	//-- models don't belong to us, so don't delete them; just the pointer block.
	delete models;
	deleteStringTable(attrs, attrCount);
}

void ocReport::addModel(class ocModel *model)
{
	const int FACTOR = 2;
	if (modelCount >= maxModelCount) {
		models = (ocModel**) growStorage(models, maxModelCount*sizeof(ocModel*), FACTOR);
		maxModelCount *= FACTOR;
	}
	models[modelCount++] = model;
}

void ocReport::setAttributes(const char *attrlist)
{
	int listCount = 1;
	const char *cp;
	//-- count the attributes in list (commas + 1)
	for (cp = attrlist; *cp; cp++) if (*cp == ',') listCount++;

	//-- delete old list and create new one
	if (attrs) deleteStringTable(attrs, attrCount);
	attrs = new char *[listCount];
	attrCount = 0;
	cp = attrlist;
	const char *cpcomma, *cpend;
	for(;;) {
		while (isspace(*cp)) cp++;
		cpcomma = strchr(cp, ',');
		if (cpcomma == 0) cpcomma = cp + strlen(cp);	// cpcomma points to null byte
		cpend = cpcomma - 1;
		while (isspace(*cpend)) cpend--;
		char *newAttr = new char[cpend - cp + 2];	//allow for null
		strncpy(newAttr, cp, cpend - cp + 1);
		newAttr[cpend - cp + 1] = '\0';
		attrs[attrCount++] = newAttr;
		if (*cpcomma == '\0') break;
		cp = cpcomma + 1;
	}
}

//-- support routines for quicksort. The static variables
//-- are used to communicate between the sort and compare routines
static const char *sortAttr;
static ocReport::SortDir sortDir;
static int sortCompare(const void *k1, const void *k2)
{
	ocModel *m1 = *((ocModel**) k1);
	ocModel *m2 = *((ocModel**) k2);
	double a1 = m1->getAttributeList()->getAttribute(sortAttr);
	double a2 = m2->getAttributeList()->getAttribute(sortAttr);
	if (sortDir == ocReport::DESCENDING) {
		return (a1 > a2) ? -1 : (a1 < a2) ? 1 : 0;
	}
	else {
		return (a1 < a2) ? -1 : (a1 > a2) ? 1 : 0;
	}
}

		
void ocReport::sort(const char *attr, SortDir dir)
{
	sortAttr = attr;
	sortDir = dir;
	qsort(models, modelCount, sizeof(ocModel*), sortCompare);
}

void ocReport::sort(class ocModel** models, long modelCount,
		const char *attr, SortDir dir)
{
	sortAttr = attr;
	sortDir = dir;
	qsort(models, modelCount, sizeof(ocModel*), sortCompare);
}


// Print a report of the search results
void ocReport::print(FILE *fd)
{
	// To speed things up, we make a list of the indices of the attribute descriptions
	int *attrID = new int[attrCount];
	for (int a = 0; a < attrCount; a++) {
		attrID[a] = -1;
		// Find the attribute
		const char *attrp = attrs[a];
		for (int d = 0; d < attrDescCount; d++) {
			if (strcasecmp(attrp, attrDescriptions[d].name) == 0) {
				attrID[a] = d;
				break;
			}
		}
	}
	
	// Print out the search results for each model, with the header before and after
	if (htmlMode) fprintf(fd, "<table border=0 cellpadding=0 cellspacing=0>\n");
	printSearchHeader(fd, attrID);
	for (int m = 0; m < modelCount; m++) {
		printSearchRow(fd, models[m], attrID);
	}
	printSearchHeader(fd, attrID);

	// Loop through the models to find the best values for each measure of model quality
	ocAttributeList *modelAttrs;
	double bestBIC, bestAIC, bestInf_01, bestInf_05, bestInf_1, bestTest;
	double tempBIC, tempAIC, tempAlpha, tempInf, tempTest;
	bestBIC = bestAIC = bestInf_01 = bestInf_05 = bestInf_1 = bestTest = -100;

	// Only show best info/alpha valuse when searching from the bottom.
	bool showAlpha = false;
	if ( (manager->getRefModel() == manager->getBottomRefModel()) || 
	( (manager->getRefModel() != manager->getTopRefModel()) && manager->getSearchDirection() == 0) ) 
		showAlpha = true;

	// Only show percent correct on test data when it's present.
	bool showPercentCorrect = false;
	if (models[0]->getAttributeList()->getAttribute(ATTRIBUTE_PCT_CORRECT_TEST) != -1.0) showPercentCorrect = true;

	for (int m = 0; m < modelCount; m++) {
		modelAttrs = models[m]->getAttributeList();
		tempBIC   = modelAttrs->getAttribute(ATTRIBUTE_BIC);
		tempAIC   = modelAttrs->getAttribute(ATTRIBUTE_AIC);
		if (tempBIC > bestBIC) bestBIC = tempBIC;
		if (tempAIC > bestAIC) bestAIC = tempAIC;
		if (showAlpha) {
			tempAlpha = modelAttrs->getAttribute(ATTRIBUTE_ALPHA);
			tempInf   = modelAttrs->getAttribute(ATTRIBUTE_EXPLAINED_I);
			if ((tempAlpha < 0.01) && (tempInf > bestInf_01)) bestInf_01 = tempInf;
			if ((tempAlpha < 0.05) && (tempInf > bestInf_05)) bestInf_05 = tempInf;
			if ((tempAlpha < 0.1 ) && (tempInf > bestInf_1 )) bestInf_1  = tempInf;
		}
		if (showPercentCorrect) {
			tempTest  = modelAttrs->getAttribute(ATTRIBUTE_PCT_CORRECT_TEST);
			if (tempTest > bestTest) bestTest = tempTest;
		}
	}

	// Now print out the best models for each of the various measures
	if (!htmlMode) fprintf(fd, "\n\nBest Model(s) by dBIC:\n");
	else fprintf(fd, "<tr><td colspan=8><br><br><b>Best Model(s) by dBIC:</b></td></tr>\n");
	for (int m = 0; m < modelCount; m++) {
		modelAttrs = models[m]->getAttributeList();
		if (modelAttrs->getAttribute(ATTRIBUTE_BIC) != bestBIC) continue;
		printSearchRow(fd, models[m], attrID);
	}

	if (!htmlMode) fprintf(fd, "Best Model(s) by dAIC:\n");
	else fprintf(fd, "<tr><td colspan=8><b>Best Model(s) by dAIC:</b></td></tr>\n");
	for (int m = 0; m < modelCount; m++) {
		modelAttrs = models[m]->getAttributeList();
		if (modelAttrs->getAttribute(ATTRIBUTE_AIC) != bestAIC) continue;
		printSearchRow(fd, models[m], attrID);
	}

	if(showAlpha) {
		if (!htmlMode) fprintf(fd, "Best Model(s) by Information, with Alpha < 0.01:\n");
		else fprintf(fd, "<tr><td colspan=8><b>Best Model(s) by Information, with Alpha < 0.01</b>:</td></tr>\n");
		for (int m = 0; m < modelCount; m++) {
			modelAttrs = models[m]->getAttributeList();
			if (modelAttrs->getAttribute(ATTRIBUTE_EXPLAINED_I) != bestInf_01) continue;
			if (modelAttrs->getAttribute(ATTRIBUTE_ALPHA) > 0.01) continue;
			printSearchRow(fd, models[m], attrID);
		}
	
		if (!htmlMode) fprintf(fd, "Best Model(s) by Information, with Alpha < 0.05:\n");
		else fprintf(fd, "<tr><td colspan=8><b>Best Model(s) by Information, with Alpha < 0.05</b>:</td></tr>\n");
		for (int m = 0; m < modelCount; m++) {
			modelAttrs = models[m]->getAttributeList();
			if (modelAttrs->getAttribute(ATTRIBUTE_EXPLAINED_I) != bestInf_05) continue;
			if (modelAttrs->getAttribute(ATTRIBUTE_ALPHA) > 0.05) continue;
			printSearchRow(fd, models[m], attrID);
		}
	
		if (!htmlMode) fprintf(fd, "Best Model(s) by Information, with Alpha < 0.1:\n");
		else fprintf(fd, "<tr><td colspan=8><b>Best Model(s) by Information, with Alpha < 0.1</b>:</td></tr>\n");
		for (int m = 0; m < modelCount; m++) {
			modelAttrs = models[m]->getAttributeList();
			if (modelAttrs->getAttribute(ATTRIBUTE_EXPLAINED_I) != bestInf_1) continue;
			if (modelAttrs->getAttribute(ATTRIBUTE_ALPHA) > 0.1) continue;
			printSearchRow(fd, models[m], attrID);
		}
	}

	if (showPercentCorrect) {
		if (!htmlMode) fprintf(fd, "Best Model(s) by %%C(Test):\n");
		else fprintf(fd, "<tr><td colspan=3><b>Best Model(s) by %%C(Test)</b>:</td></tr>\n");
		for (int m = 0; m < modelCount; m++) {
			modelAttrs = models[m]->getAttributeList();
			if (modelAttrs->getAttribute(ATTRIBUTE_PCT_CORRECT_TEST) != bestTest) continue;
			printSearchRow(fd, models[m], attrID);
		}
	}

	if (!htmlMode) fprintf(fd, "\n\n");
	else fprintf(fd, "</table><br>\n");

	delete attrID;
}


// Print out the line of column headers for the search output report
void ocReport::printSearchHeader(FILE *fd, int* attrID) {
	int sepStyle = htmlMode ? 0 : separator;
	if (sepStyle) fprintf(fd, "MODEL");
	else fprintf(fd, "<tr><th align=left>MODEL</th>"); 
	int pad, tlen;
	const int cwid = 15;
	char titlebuf[1000];
	for (int a = 0; a < attrCount; a++) {
		const char *title = (attrID[a] >= 0) ? attrDescriptions[attrID[a]].title : attrs[a];
		const char *pct = strchr(title, '$');
		tlen = strlen(title);
		if (pct) {
			tlen = pct - title;
			strncpy(titlebuf, title, tlen);
			titlebuf[tlen] = '\0';
			title = titlebuf;
		}
		int tlen = (pct == 0) ? strlen(title) : pct - title;
		switch(sepStyle) {
			case 0:
				fprintf(fd, "<th width=80 align=left>%s</th>\n", title); break;
			case 1:
				fprintf(fd, "\t%s", title); 	break;
			case 2:
				fprintf(fd, ",%s", title); 	break;
			case 3:
			default:
				pad = cwid - tlen;
				if (pad < 0) pad = 0;
				if (a == 0) pad += cwid - 5;
				fprintf(fd, "%*c%s", pad, ' ', title); break;
		}
	}
	if (sepStyle) fprintf(fd, "\n");
	else fprintf(fd, "</tr>\n");
}


// Print out a single row of the search report results
void ocReport::printSearchRow(FILE *fd, ocModel* model, int* attrID) {
	ocAttributeList *modelAttrs = model->getAttributeList();
	const char *mname = model->getPrintName();
	int pad;
	const int cwid = 15;
	char field[100];
	int sepStyle = htmlMode ? 0 : separator;
	if (sepStyle) {
		pad = cwid - strlen(mname);
		if (pad < 0) pad = 1;
		fprintf(fd, "%s%*c", mname, pad, ' ');
	} else {
		fprintf(fd, "<tr><td>%s</td>", mname);
	}
	for (int a = 0; a < attrCount; a++) {
		const char *fmt = attrID[a] >= 0 ? attrDescriptions[attrID[a]].fmt : 0;
		if (fmt == 0) {
			// get format info from name, if present
			const char *pct = strchr(attrs[a], '$');
			fmt = (pct && toupper(*(pct+1)) == 'I') ? "%14.0f" : "%12f";
		}
		double attr = modelAttrs->getAttribute(attrs[a]);
		// -1 means uninitialized, so don't print
		if (attr == -1.0) field[0] = '\0';
		else sprintf(field, fmt, attr);
		switch(sepStyle) {
		case 0:
			fprintf(fd, "<td>%s</td>\n", field); 	break;
		case 1:
			fprintf(fd, "\t"); fprintf(fd, field); 	break;
		case 2:
			fprintf(fd, ","); fprintf(fd, field); 	break;
		case 3:
			pad = cwid - strlen(field); 	fprintf(fd, "%*c", pad, ' ');
			fprintf(fd, field); 		break;
		}
	}
	
	if (!htmlMode) fprintf(fd, "\n");
	else fprintf(fd, "</tr>\n");
}


void ocReport::print(int fd) {
//	int fd2 = dup(fd);	// don't close old fd
	FILE *f = fdopen(fd, "w");
	print(f);
	fflush(f);
	fclose(f);
}


void ocReport::printResiduals(FILE *fd, ocModel *model) {
	ocTable *refData = manager->getInputData();
	ocTable *table1 = manager->getFitTable();
	ocVariableList *varlist = model->getRelation(0)->getVariableList();
	if (htmlMode) fprintf(fd,"<br><br>\n");
	if(varlist->isDirected()) {
		printf("(Residuals not calculated for directed systems.)");
		if (htmlMode) fprintf(fd, "<br>\n");
		return;
	} else {
		fprintf(fd, "RESIDUALS\n");
		if (htmlMode) fprintf(fd, "<br>");
	}
	if (table1 == NULL) {
		fprintf(fd, "Error: no fitted table computed\n");
		return;
	}
	if (htmlMode) fprintf(fd,"<br><br>\n");
	long var_count = varlist->getVarCount();
	int keysize = refData->getKeySize();
	const char *format, *header, *footer;
	char *keystr = new char[var_count+1];

	//-- set appropriate format
	int sepStyle = htmlMode ? 0 : separator;
	switch(sepStyle) {
	case 0:
		header = "<table border=1 cellspacing=0 cellpadding=0><tr><th>Cell</th><th>Obs</th><th>Exp</th><th>Res</th></tr>\n";
		format = "<tr><td>%s</td><td>%6.3f</td><td>%6.3f</td><td>%6.3f</td></tr>\n";
		footer = "</table><br><br>";
		break;
	case 1:
		header = "Cell\tObs\tExp\tRes\n";
		format = "%s\t%6.3f\t%6.3f\t%6.3f\n";
		footer = "";
		break;
	case 2:
		header = "Cell,Obs,Exp,Res\n";
		format = "%s,%6.3f,%6.3f,%6.3f\n";
		break;
	case 3:
		header = "    Cell    Obs      Exp      Res\n    ------------------------------------\n";
		format = "%8s  %6.3f   %6.3f   %6.3f\n";
		footer = "";
		break;
	}

	int index, refindex, compare;
	ocKeySegment *refkey, *key;
	double value, refvalue, res;

	// Walk through both lists. Missing values are zero.
	// We don't print anything if missing in both lists.
	index = 0; refindex = 0;
	fprintf(fd, header);
	for(;;) {
		if (refindex >= refData->getTupleCount()) break;
		if (index >= table1->getTupleCount()) break;

		refkey = refData->getKey(refindex);
		key = table1->getKey(index);
		compare = ocKey::compareKeys(refkey, key, keysize);

		if (compare == 0) { 		// matching keys; both values present
			refvalue = refData->getValue(refindex++);
			value = table1->getValue(index++);
			ocKey::keyToUserString(key, varlist, keystr);
		} else if (compare > 0) { 	// ref value is zero
			refvalue = 0;
			value = table1->getValue(index++);
			ocKey::keyToUserString(key, varlist, keystr);
		} else { 			// table value is zero
			refvalue = refData->getValue(refindex++);
			value = 0;
			ocKey::keyToUserString(refkey, varlist, keystr);
		}
		res = value - refvalue;
		if (value != 0.0 || refvalue != 0.0)
			fprintf(fd, format, keystr, refvalue, value, res);
	}
	fprintf(fd, footer);
	delete keystr;
}


static void orderIndices(const char **stringArray, int len, int *order) {
	//// Figure out the alphabetical order for an array of strings (such as the dv states)
	// (This isn't the most effficient algorithm, but it's simple, and enough to sort a few string values.)
	
	// Find the last value in the order list, to initialize the other searches with
	int last = 0;
	for(int i=0; i < len; i++) {
		if(strcmp(stringArray[last], stringArray[i]) < 0) {
			last = i;
		}
	}
	// Loop through order, finding the lowest value for each spot that is bigger than the previous values
	for(int j=0; j < len; j++) {
		// Set initial values all to the last value
		order[j] = last;
		// Loop through all the values looking for a lower one
		for(int i=0; i < len; i++) {
			if(strcmp(stringArray[order[j]], stringArray[i]) > 0) {
				// If a lower value is found for the first slot, use it
				if(j == 0) {
					order[j] = i;
				// If it's not the first slot, make sure it's bigger than the previous slot before using it
				} else if(strcmp(stringArray[order[j-1]], stringArray[i]) < 0) {
					order[j] = i;
				}
			}
		}
	}
}


void ocReport::printConditional_DV(FILE *fd, ocModel *model, bool calcExpectedDV)
{
	printConditional_DV(fd, model, NULL, calcExpectedDV);
}


void ocReport::printConditional_DV(FILE *fd, ocRelation *rel, bool calcExpectedDV)
{
	printConditional_DV(fd, NULL, rel, calcExpectedDV);
}


void ocReport::printConditional_DV(FILE *fd, ocModel *model, ocRelation *rel, bool calcExpectedDV)
{
	if (model == NULL && rel == NULL) {
		fprintf(fd, "No model or relation specified.\n");
		return;
	}
	ocTable *input_data = manager->getInputData();
	ocTable *test_data = manager->getTestData();
	ocTable *fit_table;
	// If we are working with just a model, use that fit table.  Otherwise get the relation's table.
	if (rel == NULL)
		fit_table = manager->getFitTable();
	else
		fit_table = rel->getTable();
	double sample_size = manager->getSampleSz();
	double test_sample_size = manager->getTestSampleSize();
	if (fit_table == NULL) {
		fprintf(fd, "Error: no fitted table computed.\n");
		return;
	}
	ocVariableList *var_list = manager->getVariableList();
	if(!var_list->isDirected()){
		fprintf(fd, "(DV calculation not possible for neutral systems.)\n");
		return;
	}

	int dv_index = var_list->getDV();			// Get the first DV's index
	ocVariable *dv_var = var_list->getVariable(dv_index);	// Get the (first) DV itself
	int var_count = var_list->getVarCount();		// Get the number of variables
	int key_size = input_data->getKeySize();		// Get the key size from the reference data
        int dv_card = dv_var->cardinality;			// Get the cardinality of the DV
	double dv_bin_value[dv_card];				// Contains the DV values for calculating expected values.

	ocTable *input_table, *test_table;
	long degrees = (long) ocDegreesOfFreedom(var_list);
	ocRelation *iv_rel;					// A ptr to the IV component of a model, or the relation itself
	// If we are working with a model, we use the input and test data directly.
	if (rel == NULL) {
		input_table = input_data;
		test_table = test_data;
		iv_rel = model->getRelation(0);
	// Else, if we are working with a relation, make projections of the input and test tables.
	} else {
		input_table = new ocTable(key_size, degrees + 1);
		manager->makeProjection(input_data, input_table, rel, 0);
		if(test_sample_size > 0) {
			test_table  = new ocTable(key_size, degrees + 1);
			manager->makeProjection(test_data,  test_table,  rel, 0);
		}
		iv_rel = rel;
	}

	char *key_str = new char[var_count + 1];		// Used to hold user-strings for keys in several places

	int iv_statespace = (degrees + 1) / dv_card;	// full statespace divided by cardinality of the DV
	const char **dv_label = (const char**)dv_var->valmap;
	ocKeySegment **fit_key = new ocKeySegment *[iv_statespace];
	double **fit_prob = new double *[iv_statespace];
	double *fit_dv_prob = new double[dv_card];
	double *fit_key_prob = new double[iv_statespace]; 
	int *fit_rule = new int[iv_statespace]; 	
	double *fit_dv_expected = new double[iv_statespace];
	ocKeySegment **input_key = new ocKeySegment *[iv_statespace];
	int **input_freq = new int *[iv_statespace];
	int *input_dv_freq = new int[dv_card];
	int *input_key_freq = new int[iv_statespace]; 
	//int *input_rule = new int[iv_statespace]; 	
	ocKeySegment **test_key = new ocKeySegment *[iv_statespace];
	int **test_freq = new int *[iv_statespace];
	int *test_dv_freq = new int[dv_card];
	int *test_key_freq = new int[iv_statespace]; 
	int *test_rule = new int[iv_statespace]; 	
	
	// Allocate space for keys and frequencies
	ocKeySegment *temp_key;
	int *temp_int_array;
	double *temp_double_array;
	for(int i=0; i < iv_statespace; i++) {
		fit_key_prob[i] = 0.0;
		input_key_freq[i] = 0;
		fit_dv_expected[i] = 0.0;

		temp_key = new ocKeySegment[key_size];
		for(int j=0; j < key_size; j++) { temp_key[j] = DONT_CARE; }
		fit_key[i] = temp_key;

		temp_key = new ocKeySegment[key_size];
		for(int j=0; j < key_size; j++) { temp_key[j] = DONT_CARE; }
		input_key[i] = temp_key;

		temp_double_array = new double[dv_card];
		for(int k=0; k < dv_card; k++) { temp_double_array[k] = 0.0; }
		fit_prob[i] = temp_double_array;

		temp_int_array = new int[dv_card];
		for(int k=0; k < dv_card; k++) { temp_int_array[k] = 0; }
		input_freq[i] = temp_int_array;
	}
	if(test_sample_size > 0) {
		for(int i=0; i < iv_statespace; i++) {
			test_key_freq[i] = 0;
	
			temp_key = new ocKeySegment[key_size];
			for(int j=0; j < key_size; j++) { temp_key[j] = DONT_CARE; }
			test_key[i] = temp_key;

			temp_int_array = new int[dv_card];
			for(int k=0; k < dv_card; k++) { temp_int_array[k] = 0; }
			test_freq[i] = temp_int_array;
		}
	}
	
	for(int i=0; i < dv_card; i++) {
		fit_dv_prob[i] = 0.0;
		input_dv_freq[i] = 0;
		test_dv_freq[i] = 0;
	}

	if(calcExpectedDV) {
		for (int i=0; i < dv_card; i++) {
			dv_bin_value[i] = strtod(dv_label[i], (char **)NULL);
		}
	}
	
	const char *new_line,  *blank_line;
	if (htmlMode) {
		new_line = "<br>\n";
		blank_line = "<br><br>\n";
	} else {
		new_line = "\n";
		blank_line = "\n\n";
	}
	
	const char *block_start, *head_start, *head_sep, *head_end, *head_str1, *head_str2, *head_str3, *head_str4;
 	const char *row_start, *block_end, *row_start2, *row_start3, *row_end, *row_sep, *line_sep;

	// Set appropriate format
	int sep_style = htmlMode ? 0 : separator;
	switch(sep_style) {
	case 0:
		block_start = "<table border=0 cellpadding=0 cellspacing=0>\n";
		head_start  = "<tr><th>";
		head_sep    = "</th><th>";
		head_end    = "</th></tr>\n";
		head_str1   = "</th><th colspan=2 class=r1>calc.&nbsp;q(DV|IV)";
		head_str2   = "</th><th colspan=2 class=r1>obs.&nbsp;p(DV|IV)";
		head_str3   = "</th><th colspan=2>%%correct";
		head_str4   = "</th><th colspan=2>Test&nbsp;Data";
 		row_start   = "<tr><td align=right>";
 		row_start2  = "<tr class=r1><td align=right>";
 		row_start3  = "<tr class=em><td align=right>";
		row_sep     = "</td><td align=right>";	
		row_end     = "</td></tr>\n";
		block_end   = "</table><br>\n";
		line_sep    = "<hr>\n";
		break;
	case 1:
		block_start = "";
		head_start  = "";
		head_sep    = "\t";
		head_end    = "\n";
		head_str1   = "\tcalc. q(DV|IV)\t";
		head_str2   = "\tobs. p(DV|IV)\t";
		head_str3   = "\t%%correct\t";
		head_str4   = "\tTest Data\t";
		row_start = row_start2 = row_start3 = "";
		row_sep     = "\t";
		row_end     = "\n";
		block_end   = "\n";
		line_sep    = "-------------------------------------------------------------------------\n";
		break;
	case 2:
		block_start = "";
		head_start  = "";
		head_sep    = ",";
		head_end    = "\n";
		head_str1   = ",calc. q(DV|IV),";
		head_str2   = ",obs. p(DV|IV),";
		head_str3   = ",%%correct,";
		head_str4   = ",Test Data,";
		row_start = row_start2 = row_start3 = "";
		row_sep     = ",";
		row_end     = "\n";
		block_end   = "\n";
		line_sep    = "-------------------------------------------------------------------------\n";
		break;
	case 3:
		block_start = "";
		head_start  = "";
		head_sep    = "    ";
		head_end    = "\n";
		head_str1   = "calc. q(DV|IV)";
		head_str2   = "obs. p(DV|IV)";
		head_str3   = "%%correct";
		head_str4   = "Test Data";
		row_start = row_start2 = row_start3 = "";
		row_sep     = "    ";
		row_end     = "\n";
		block_end   = "\n";
		line_sep    = "-------------------------------------------------------------------------\n";
		break;
	}
	fprintf(fd, "%s%s%s", blank_line, line_sep, blank_line);

	int *ind_vars = new int[var_count];
	int iv_count = iv_rel->getIndependentVariables(ind_vars, var_count);
	if(rel == NULL) {
		fprintf(fd, "Conditional DV (D) (%%) for each IV composite state for the Model %s", model->getPrintName());
		//fprintf(fd, new_line);
		//fprintf(fd, "IV order: %s (", iv_rel->getPrintName());
		//for(int i=0; i < iv_count; i++) {
			//if (i > 0) fprintf(fd, "; ");
			//fprintf(fd, "%s", var_list->getVariable(iv_rel->getVariable(i))->name);
		//}
		//fprintf(fd, ")");
	} else {
		// The iv_count is off by one for relations, as the DV seems to still get counted.
		iv_count--;
		fprintf(fd, "Conditional DV (D) (%%) for each IV composite state for the Relation %s", rel->getPrintName());
	}
	fprintf(fd, blank_line);

	int index = 0;
	int keys_found = 0;
	ocKeySegment *key;
	double temp_value;
	long *index_sibs = new long[dv_card];
	int key_compare, num_sibs;

	int fit_table_size = fit_table->getTupleCount();
	int input_table_size = input_table->getTupleCount();
	int test_table_size = 0;
	if(test_sample_size > 0) {
		test_table_size = test_table->getTupleCount();
	}
	int dv_value, best_i, temp_return;

	// Count up the total frequencies for each DV value in the reference data, for use in tie-breaking
	for (int i=0; i < input_table_size; i++) {
		temp_key = input_table->getKey(i);
		dv_value = ocKey::getKeyValue(temp_key, key_size, var_list, dv_index);
		temp_return = (int) (input_table->getValue(i) * sample_size);
		input_dv_freq[dv_value] += temp_return;
	}

	// Find the most common DV value, for test data predictions when no input data exists.
	int input_default_dv = 0;
	for (int i=0; i < dv_card; i++) {
		if(input_dv_freq[i] > input_dv_freq[input_default_dv])
			input_default_dv = i;
	}
	for (int i=0; i < iv_statespace; i++) {
		fit_rule[i] = input_default_dv;
	}


	ocKeySegment *temp_key_array = new ocKeySegment[key_size];
	// Loop till we have as many keys as the size of the IV statespace
	while (keys_found < iv_statespace) {
		// Also break the loop if index exceeds the tupleCount for the table
		if (index >= fit_table_size) break;

		// Get the key and value for the current index
		key = fit_table->getKey(index);
		index++;
        	memcpy((int *)temp_key_array, (int *)key, key_size * sizeof(ocKeySegment));
		ocKey::setKeyValue(temp_key_array, key_size, var_list, dv_index, DONT_CARE);

		// Check if this key has appeared yet
		key_compare = 1;
		for(int i = 0; i < keys_found; i++) {
			key_compare = ocKey::compareKeys((ocKeySegment *)fit_key[i], temp_key_array, key_size);	
			// If zero is returned, keys are equal, meaning this key has appeared before.  Stop checking.
			if(key_compare == 0) break;
		}
		// If this was a duplicate key, move on to the next index.
		if(key_compare == 0) continue;
		// Otherwise, this is a new key.  Place it into the keylist
		memcpy((int *)fit_key[keys_found], (int *)temp_key_array, sizeof(ocKeySegment) * key_size);

		// Get the siblings of the key
		num_sibs = 0;
		ocKey::getSiblings(key, var_list, fit_table, index_sibs, dv_index, &num_sibs);
	
		best_i = 0;	temp_value = 0.0;
		for(int i=0; i < num_sibs; i++) {
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
			if(i == 0) {
				best_i = dv_value;
			} else {		
				if(fit_prob[keys_found][dv_value] > fit_prob[keys_found][best_i]) {
					best_i = dv_value;
				// If there is a tie, break it by choosing the DV state that was most common in the input data.
				} else if(fit_prob[keys_found][dv_value] == fit_prob[keys_found][best_i]) {
					if(input_dv_freq[best_i] < input_dv_freq[dv_value]) {
						best_i = dv_value;
					}	
				}
			}
		}
		// Save the total probability for these siblings.
		fit_key_prob[keys_found] = temp_value;
		// Save the final best rule's index.
		fit_rule[keys_found] = best_i;
		// And move on to the next key...
		keys_found++;
	}


	// Sort out the input (reference) data
	// Loop through all the input data
	int input_counter = 0;
	index = 0;
	int fit_index = 0;
	while (input_counter < iv_statespace) {
		if (index >= input_table_size) break;

		key = input_table->getKey(index);
		index++;
		memcpy((int *)temp_key_array, (int *)key, key_size * sizeof(ocKeySegment));
		ocKey::setKeyValue(temp_key_array, key_size, var_list, dv_index, DONT_CARE);

		// Check if this key has appeared yet -- we only do this so siblings aren't counted multiple times.
		key_compare = 1;
		for (int i=0; i < input_counter; i++) {
			key_compare = ocKey::compareKeys((ocKeySegment *)input_key[i], temp_key_array, key_size);
			if (key_compare == 0) break;
		}
		// If this was a duplicate, move on
		if (key_compare == 0) continue;
		// Otherwise, the key is new to the input list, we add it into the list.
		memcpy((int *)input_key[input_counter], (int *)temp_key_array, sizeof(ocKeySegment) * key_size);

		// Next, find out if the index of this key is in the fit_key list, to keep the keys in the same order
		for (fit_index=0; fit_index < keys_found; fit_index++) {
			key_compare = ocKey::compareKeys((ocKeySegment *)fit_key[fit_index], temp_key_array, key_size);
			if(key_compare == 0) break;
		}
		// If the key wasn't found, we must add it to the fit list as well
		if(key_compare != 0) {
			memcpy((int *)fit_key[keys_found], (int *)temp_key_array, sizeof(ocKeySegment) * key_size);
			fit_index = keys_found;
			keys_found++;
		}

		// Get the siblings of this key
		num_sibs = 0;
		ocKey::getSiblings(key, var_list, input_table, index_sibs, dv_index, &num_sibs);

		temp_value = 0.0;
		for(int i=0; i < num_sibs; i++) {
			// Sum up the total frequencies among the siblings
			temp_value += input_table->getValue(index_sibs[i]);
			ocKeySegment *temp_key = input_table->getKey(index_sibs[i]);
			dv_value = ocKey::getKeyValue(temp_key, key_size, var_list, dv_index);
			input_freq[fit_index][dv_value] = (int)round(input_table->getValue(index_sibs[i]) * sample_size);
		}
		input_key_freq[fit_index] = (int)round(temp_value * sample_size);
		input_counter++;
	}


	// Compute performance on test data, if present
	// This section will reuse many of the variables from above, since it is performing a similar task.
	if (test_sample_size > 0) {
		int test_counter = 0;
		index = 0;
		fit_index = 0;
		while (test_counter < iv_statespace) {
			if (index >= test_table_size) break;
	
			key = test_table->getKey(index);
			index++;
			memcpy((int *)temp_key_array, (int *)key, key_size * sizeof(ocKeySegment));
			ocKey::setKeyValue(temp_key_array, key_size, var_list, dv_index, DONT_CARE);
	
			// Check if this key has appeared yet -- we only do this so siblings aren't counted multiple times.
			key_compare = 1;
			for (int i=0; i < test_counter; i++) {
				key_compare = ocKey::compareKeys((ocKeySegment *)test_key[i], temp_key_array, key_size);
				if (key_compare == 0) break;
			}
			// If this was a duplicate, move on
			if (key_compare == 0) continue;
			// Otherwise, the key is new to the test list, we add it into the list.
			memcpy((int *)test_key[test_counter], (int *)temp_key_array, sizeof(ocKeySegment) * key_size);
	
			// Next, find out the index of this key in the fit_key list, to keep the keys in the same order
			for (fit_index=0; fit_index < keys_found; fit_index++) {
				key_compare = ocKey::compareKeys((ocKeySegment *)fit_key[fit_index], temp_key_array, key_size);
				if(key_compare == 0) break;
			}
			// If the key wasn't found, we must add it to the fit list as well
			if(key_compare != 0) {
				memcpy((int *)fit_key[keys_found], (int *)temp_key_array, sizeof(ocKeySegment) * key_size);
				fit_index = keys_found;
				keys_found++;
			}
	
			// Get the siblings of this key
			num_sibs = 0;
			ocKey::getSiblings(key, var_list, test_table, index_sibs, dv_index, &num_sibs);
	
			best_i = 0;	temp_value = 0.0;
			for(int i=0; i < num_sibs; i++) {
				// Sum up the total frequencies among the siblings
				temp_value += test_table->getValue(index_sibs[i]);
				ocKeySegment *temp_key = test_table->getKey(index_sibs[i]);
				dv_value = ocKey::getKeyValue(temp_key, key_size, var_list, dv_index);
				test_freq[fit_index][dv_value] = (int)round(test_table->getValue(index_sibs[i]) * test_sample_size);
				if(i == 0) {
					best_i = dv_value;
				} else {
					if(test_freq[fit_index][dv_value] > test_freq[fit_index][best_i]) {
						best_i = dv_value;
					}
				}
			}
	
			test_key_freq[fit_index] = (int)round(temp_value * test_sample_size);
			test_rule[fit_index] = best_i;
			test_counter++;
		}
	}


	int *dv_order = new int[dv_card];
	// Get an ordering for the dv values, so they can be displayed in ascending order.
	orderIndices(dv_label, dv_card, dv_order);

	// Compute marginals of DV states for the totals row
	double *marginal = new double[dv_card];
	for(int i=0; i < dv_card; i++) {
		marginal[i] = 0.0;
		for(int j=0; j < iv_statespace; j++) {
			marginal[i] += fit_prob[j][i];
		}
	}

	// Compute sums for the totals row
	int total_correct = 0;		// correct on input data by fit rule
	for(int i=0; i < iv_statespace; i++) {
		total_correct += input_freq[i][fit_rule[i]];
	}

	// Compute marginals & sums for test data, if present.
	int test_by_fit_rule, test_by_test_rule;
	if(test_sample_size > 0) {
		for(int i=0; i < dv_card; i++) {
			for(int j=0; j < iv_statespace; j++) {
				test_dv_freq[i] += test_freq[j][i];
			}
		}
		test_by_fit_rule = 0;	// correct on test data by fit rule
		test_by_test_rule = 0;	// correct on test data by test rule (best possible performance)
		for(int i=0; i < iv_statespace; i++) {
			test_by_fit_rule += test_freq[i][fit_rule[i]];
			test_by_test_rule += test_freq[i][test_rule[i]];
		}
	}

	int dv_ccount = 0;
	char *dv_header = new char[100];
	for(int i=0; i < dv_card; i++) {
		dv_ccount += snprintf(dv_header + dv_ccount, 100 - dv_ccount, "%s=", dv_var->abbrev);
		dv_ccount += snprintf(dv_header + dv_ccount, 100 - dv_ccount, "%s", dv_label[dv_order[i]]);
		dv_ccount += snprintf(dv_header + dv_ccount, 100 - dv_ccount, row_sep);
	}

	// Header, Row 1
	fprintf(fd, "%s%sIV", block_start, head_start);
	for(int i=0; i < iv_count; i++) fprintf(fd, "%s", head_sep);
	fprintf(fd, "|%sData%s", head_sep, head_sep);
	for(int i=0; i < dv_card; i++) fprintf(fd, "%s", head_sep);
	fprintf(fd, "|%sModel", head_sep);
	for(int i=0; i < dv_card; i++) fprintf(fd, "%s", head_sep);
	fprintf(fd, "%s%s", head_sep, head_sep);
	if(calcExpectedDV == true) fprintf(fd, "%s%s", head_sep, head_sep);
	if(test_sample_size > 0)
		fprintf(fd, "%s|%s%s%s", head_sep, head_str4, head_sep, head_sep);
	fprintf(fd, head_end);

	// Header, Row 2
	fprintf(fd, "%s", head_start);
	for(int i=0; i < iv_count; i++) fprintf(fd, "%s", head_sep);
	fprintf(fd, "|%s%s", head_sep, head_sep);
	for(int i=0; i < dv_card; i++) fprintf(fd, "%s", head_sep);
	fprintf(fd, "|%s%s", head_str1, head_sep);
	if(dv_card > 2)
		for(int i=2; i < dv_card; i++)
			fprintf(fd, head_sep);
	fprintf(fd, "%s%s", head_sep, head_sep);
	if(calcExpectedDV == true) fprintf(fd, "%s%s", head_sep, head_sep);
	if(test_sample_size > 0) {
		fprintf(fd, "%s|%s%s", head_sep, head_sep, head_str2);
		if(dv_card > 2)
			for(int i=2; i < dv_card; i++)
				fprintf(fd, head_sep);
		fprintf(fd, head_str3); }
	fprintf(fd, head_end);

	// Header, Row 3
	fprintf(fd, "%s", row_start);
	for(int i=0; i < iv_count; i++)
		fprintf(fd, "%s%s", var_list->getVariable(iv_rel->getVariable(i))->abbrev, row_sep);
	fprintf(fd, "|%sfreq%s%s|%s%srule%s#correct%s%%correct", row_sep, row_sep, dv_header, row_sep, dv_header, row_sep, row_sep);
	if(calcExpectedDV == true)
		fprintf(fd, "%sE(DV)%sMSE", row_sep, row_sep);

	if(test_sample_size > 0) {
		fprintf(fd, "%s|%sfreq%s%sby rule%sbest", row_sep, row_sep, row_sep, dv_header, row_sep);
		if(calcExpectedDV == true)
			fprintf(fd, "%sMSE", row_sep);
	}
	fprintf(fd, row_end);

	// Body of Table
	double mean_squared_error = 0.0;
	double total_test_error = 0.0;
	double temp_percent = 0.0;
	// For each of the model's keys (ie, each row of the table)...
	for(int i=0; i < iv_statespace; i++) {
		if (input_key_freq[i] == 0) { if (test_sample_size > 0) {
				if (test_key_freq[i] == 0) { continue; }
			} else { continue; }
		}
		ocKey::keyToUserString(fit_key[i], var_list, key_str);
		// Also, switch the bgcolor of each row from grey to white, every other row. (If not in HTML, this does nothing.)
		if (i % 2) fprintf(fd, row_start);
		else fprintf(fd, row_start2);
		// Print the states of the IV in separate columns
		for (int j=0; j < iv_count; j++)
			fprintf(fd, "%c%s", key_str[j], row_sep);
		fprintf(fd, "|%s%d%s", row_sep, input_key_freq[i], row_sep);
		// Print out the frequencies of the training data
		for(int j=0; j < dv_card; j++)
			fprintf(fd, "%d%s", input_freq[i][j], row_sep);
		fprintf(fd, "|%s", row_sep);
		// Print out the percentages for each of the DV states
		temp_percent = 0.0;
		for(int j=0; j < dv_card; j++) {
			if (fit_key_prob[i] == 0) temp_percent = 0.0;
			else {
				temp_percent = fit_prob[i][dv_order[j]] / fit_key_prob[i] * 100.0;
				if(calcExpectedDV == true) {
					fit_dv_expected[i] += temp_percent / 100.0 * dv_bin_value[dv_order[j]];
				}
			}
			fprintf(fd, "%6.3f%s", temp_percent, row_sep);
		}
		// Print the DV state of the best rule. If there was no input to base the rule on, use the default rule.
		fprintf(fd, "%s%s", dv_label[fit_rule[i]], row_sep);
		// Number correct (of the input data, based on the rule from fit)
		fprintf(fd, "%d%s", input_freq[i][fit_rule[i]], row_sep);
		// Percent correct (of the input data, based on the rule from fit)
		if (input_key_freq[i] == 0) fprintf(fd, "%6.3f", 0.0);
		else fprintf(fd, "%6.3f", (double)input_freq[i][fit_rule[i]] / (double)input_key_freq[i] * 100.0);
		mean_squared_error = 0.0;
		if(calcExpectedDV == true) {
			fprintf(fd, "%s%6.3f", row_sep, fit_dv_expected[i]);
			if (input_key_freq[i] > 0) {
				for (int j=0; j < dv_card; j++) {
					temp_percent = fit_dv_expected[i] - dv_bin_value[dv_order[j]];
					mean_squared_error += temp_percent * temp_percent * input_freq[i][dv_order[j]];
				}
				mean_squared_error /= input_key_freq[i];
			} else mean_squared_error = 0;
			fprintf(fd, "%s%6.3f", row_sep, mean_squared_error);
		}

		// Print test results, if present
		if(test_sample_size > 0) {
			// Frequency in test data
			fprintf(fd, "%s|%s%d", row_sep, row_sep, test_key_freq[i]);
			// Print out the percentages for each of the DV states
			for(int j=0; j < dv_card; j++) {
				fprintf(fd, row_sep);
				if (test_key_freq[i] == 0) fprintf(fd, "%6.3f", 0.0);
				else fprintf(fd, "%6.3f", (double)test_freq[i][dv_order[j]] / (double)test_key_freq[i] * 100.0);	
			}
			fprintf(fd, row_sep);
			if (test_key_freq[i] == 0) fprintf(fd, "%6.3f", 0.0);
			else fprintf(fd, "%6.3f", (double)test_freq[i][fit_rule[i]] / (double)test_key_freq[i] * 100.0);
			fprintf(fd, row_sep);
			if (test_key_freq[i] == 0) fprintf(fd, "%6.3f", 0.0);
			else fprintf(fd, "%6.3f", (double)test_freq[i][test_rule[i]] / (double)test_key_freq[i] * 100.0);
			mean_squared_error = 0.0;
			if(calcExpectedDV == true) {
				if (test_key_freq[i] > 0) {
					for (int j=0; j < dv_card; j++) {
						temp_percent = fit_dv_expected[i] - dv_bin_value[dv_order[j]];
						mean_squared_error += temp_percent * temp_percent * test_freq[i][dv_order[j]];
					}
					mean_squared_error /= test_key_freq[i];
				} else mean_squared_error = 0;
				fprintf(fd, "%s%6.3f", row_sep, mean_squared_error);
				total_test_error += mean_squared_error * test_key_freq[i];
			}
		}
		fprintf(fd, row_end);
	}

	// Footer, Row 1 (totals)
	double total_expected_value = 0.0;
	fprintf(fd, row_start3);
	for(int i=0; i < iv_count; i++) fprintf(fd, "%s", row_sep);
	fprintf(fd, "|%s%d%s", row_sep, (int)sample_size, row_sep);
	for(int j=0; j < dv_card; j++) {
		fprintf(fd, "%d%s", input_dv_freq[j], row_sep);
	}
	fprintf(fd, "|%s", row_sep);
	// Print the marginals for each DV state
	for(int j=0; j < dv_card; j++) {
		fprintf(fd, "%6.3f%s", marginal[dv_order[j]] * 100.0, row_sep);
		if(calcExpectedDV == true)
			total_expected_value += marginal[dv_order[j]] * dv_bin_value[dv_order[j]];
	}
	fprintf(fd, "%s%d%s%6.3f", row_sep, total_correct, row_sep, (double)total_correct / sample_size * 100.0);
	if(calcExpectedDV == true) {
		fprintf(fd, "%s%6.3f", row_sep, total_expected_value);
		temp_percent = mean_squared_error = 0.0;
		for(int j=0; j < dv_card; j++) {
			temp_percent = total_expected_value - dv_bin_value[dv_order[j]];
			mean_squared_error += temp_percent * temp_percent * (double)input_dv_freq[dv_order[j]];
		}
		mean_squared_error /= sample_size;
		fprintf(fd, "%s%6.3f", row_sep, mean_squared_error);
	}
	double default_percent_on_test = 0.0;
	double best_percent_on_test = 0.0;
	double fit_percent_on_test = 0.0;
	if(test_sample_size > 0) {
		fprintf(fd, "%s|%s%d%s", row_sep, row_sep, (int)test_sample_size, row_sep);
		// Print the test marginals for each DV state
		for(int j=0; j < dv_card; j++) {
			temp_percent = (double)test_dv_freq[dv_order[j]] / test_sample_size * 100.0;
			if (temp_percent > default_percent_on_test) default_percent_on_test = temp_percent;
			fprintf(fd, "%6.3f%s", temp_percent, row_sep);
		}
		fit_percent_on_test = (double)test_by_fit_rule / test_sample_size * 100.0;
		best_percent_on_test = (double)test_by_test_rule / test_sample_size * 100.0;
		fprintf(fd, "%6.3f%s%6.3f", fit_percent_on_test, row_sep, best_percent_on_test);
		if(calcExpectedDV == true)
			fprintf(fd, "%s%6.3f", row_sep, total_test_error/test_sample_size);
	}
	fprintf(fd, row_end);
	// Footer, Row 2 (repeat of Header, Row 3)
	fprintf(fd, row_start);
	for(int i=0; i < iv_count; i++) fprintf(fd, "%s", row_sep);
	fprintf(fd, "|%sfreq%s%s|%s%srule%s#correct%s%%correct", row_sep, row_sep, dv_header, row_sep, dv_header, row_sep, row_sep);
	if(calcExpectedDV == true)
		fprintf(fd, "%sE(DV)%sMSE", row_sep, row_sep);

	if(test_sample_size > 0) {
		fprintf(fd, "%s|%sfreq%s%sby rule%sbest", row_sep, row_sep, row_sep, dv_header, row_sep);
		if(calcExpectedDV == true)
			fprintf(fd, "%sMSE", row_sep);
	}
	fprintf(fd, "%s%s", row_end, block_end);

	// Print out a summary of the performance on the test data, if present.
	if(test_sample_size > 0) {
		fprintf(fd, "%s%sPerformance on Test Data%s", block_start, row_start, row_end);
		fprintf(fd, "%sDefault:%s%6.3f%%%scorrect%s", row_start, row_sep, default_percent_on_test, row_sep, row_end);
		fprintf(fd, "%sModel rule:%s%6.3f%%%scorrect%s", row_start, row_sep, fit_percent_on_test, row_sep, row_end);
		fprintf(fd, "%sBest possible:%s%6.3f%%%scorrect%s", row_start, row_sep, best_percent_on_test, row_sep, row_end);
		temp_percent = best_percent_on_test - default_percent_on_test;
		if ((temp_percent) != 0)
			temp_percent = (fit_percent_on_test - default_percent_on_test) / temp_percent * 100.0;
		fprintf(fd, "%sImprovement by model:%s%6.3f%%%s%s", row_start, row_sep, temp_percent, row_end, block_end);
	}

	// If this is the entire model, print tables for each of the component relations.
	if(rel == NULL) {
		for(int i=1; i < model->getRelationCount(); i++){
			printConditional_DV(fd, model->getRelation(i), calcExpectedDV);
		}
	}

	delete[] dv_header;		 delete[] marginal;		delete[] dv_order;
	delete[] temp_key_array;	delete[] index_sibs;
	if(test_sample_size > 0) {
		for(int i=0; i < iv_statespace; i++) {
			delete[] test_key[i];	delete[] test_freq[i];
		}
	}
	for(int i=0; i < iv_statespace; i++) {
		delete[] fit_key[i];	delete[] input_key[i];
		delete[] fit_prob[i];	delete[] input_freq[i];
	}
	delete[] test_rule;		delete[] test_key_freq;		delete[] test_dv_freq;	
	delete[] test_freq;		delete[] test_key;		delete[] input_key_freq;
	delete[] input_dv_freq;		delete[] input_freq;		delete[] input_key;
	delete[] fit_dv_expected;	delete[] fit_rule;		delete[] fit_key_prob;
	delete[] fit_dv_prob;		delete[] fit_prob;		delete[] fit_key;		delete[] key_str;
	
	return;
}


