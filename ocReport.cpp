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
{ATTRIBUTE_LOOPS, "LOOPS", "%2.0f"},      // Junghan
{ATTRIBUTE_EXPLAINED_I, "Inf", "%12.4f"},             // change name "Information" to "Inf"
{ATTRIBUTE_AIC, "dAIC", "%12.4f"},                    // new
{ATTRIBUTE_BIC, "dBIC", "%12.4f"},                            // new
{ATTRIBUTE_BP_AIC, "dAIC(BP)", "%12.4f"},                       // new
{ATTRIBUTE_BP_BIC, "dBIC(BP)", "%12.4f"},                       // new
{ATTRIBUTE_PCT_CORRECT_DATA, "%C(Data)", "%12.4f"},       // change name % correct
{ATTRIBUTE_PCT_CORRECT_TEST, "%C(Test)", "%12.4f"},       // change name % correct
{ATTRIBUTE_BP_EXPLAINED_I, "Inf(BP)", "%12f"},          // change name "Information" to "Inf"
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
{ATTRIBUTE_LR, "LR", "%12.4f"},
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

void ocReport::print(FILE *fd)
{
	//-- ignore separator style in HTML mode
	int sepStyle = htmlMode ? 0 : separator;

	//-- to speed things up, we make a list of the indices of the attribute descriptions
	int *attrID = new int[attrCount];
	int a, d;
	for (a = 0; a < attrCount; a++) {
		attrID[a] = -1;
		//-- find the attribute
		const char *attrp = attrs[a];
		for (d = 0; d < attrDescCount; d++) {
			if (strcasecmp(attrp, attrDescriptions[d].name) == 0) {
				attrID[a] = d;
				break;
			}
		}
	}
	
	const int cwid=15;

	//-- print the header
	if (sepStyle) {
		fprintf(fd, "MODEL");
	}
	else {
		fprintf(fd, "<table><tr><th>MODEL</th>");
	} 
	int pad, tlen;
	char titlebuf[1000];
	for (a = 0; a < attrCount; a++) {
		const char *title = attrID[a] >= 0 ? attrDescriptions[attrID[a]].title : attrs[a];
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
			fprintf(fd, "<th width=100 align=left>%s</th>\n", title);
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
			if (pad < 0) pad = 0;
			if (a == 0) pad += cwid - 5;
			fprintf(fd, "%*c%s", pad, ' ', title);
			break;
		}
	}
	if (sepStyle) {
		fprintf(fd, "\n");
	}
	else {
		fprintf(fd, "</tr>\n");
	}
	
	//-- print a line for each model
	int m;
	char field[100];
	const char *mname;
	for (m = 0; m < modelCount; m++) {
		ocAttributeList *modelAttrs = models[m]->getAttributeList();
		mname = models[m]->getPrintName();
		if (sepStyle) {
			pad = cwid - strlen(mname);
			if (pad < 0) pad = 1;
			fprintf(fd, "%s%*c", mname, pad, ' ');
		}
		else {
			fprintf(fd, "<tr><td>%s</td>", mname);
		}
		for (a = 0; a < attrCount; a++) {
			const char *fmt = attrID[a] >= 0 ? attrDescriptions[attrID[a]].fmt : 0;
			if (fmt == 0) {
				//-- get format info from name, if present
				const char *pct = strchr(attrs[a], '$');
				fmt = (pct && toupper(*(pct+1)) == 'I') ? "%14.0f" : "%12f";
			}
			double attr = modelAttrs->getAttribute(attrs[a]);
			//-- -1 means uninitialized, so don't print
			if (attr == -1.0) field[0] = '\0';
			else sprintf(field, fmt, attr);
			switch(sepStyle) {
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
		if (sepStyle) {
			fprintf(fd, "\n");
		}
		else {
			fprintf(fd, "</tr>\n");
		}
	}
	if (sepStyle) {
		fprintf(fd, "\n");
	}
	else {
		fprintf(fd, "</table>");
	}
}

void ocReport::print(int fd)
{
//	int fd2 = dup(fd);	// don't close old fd
	FILE *f = fdopen(fd, "w");
	print(f);
	fflush(f);
	fclose(f);
}

void ocReport::printResiduals(FILE *fd, ocModel *model)
{
	ocTable *refData = manager->getInputData();
	ocTable *table1 = manager->getFitTable();
	ocVariableList *varlist = model->getRelation(0)->getVariableList();
	if (htmlMode) fprintf(fd,"<br><br>\n");
	if(varlist->isDirected()) {
		printf("(Residuals not calculated for directed systems.)<br>\n");
		return;
	} else {
		fprintf(fd, "RESIDUALS<br>\n");
	}
	if (table1 == NULL) {
		fprintf(fd, "Error: no fitted table computed\n");
		return;
	}
	if (htmlMode) fprintf(fd,"<br><br>\n");
	long varcount = varlist->getVarCount();
	int keysize = refData->getKeySize();
	const char *format, *header, *footer;
	char *keystr = new char[varcount+1];

	//-- set appropriate format
	int sepStyle = htmlMode ? 0 : separator;
	switch(sepStyle) {
	case 0:
		header = "<table border =\"1\"><tr><th>Cell</th><th>Obs</th>><th>Exp</th><th>Res</th></tr>\n";
		format = "<tr><td>%s</td><td>%6.3f</td><td>%6.3f</td><td>%6.3f</td></tr>\n";
		footer = "</table>";
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

	//-- walk through both lists. Missing values are zero.
	//-- we don't print anything if missing in both lists.
	index = 0; refindex = 0;
	fprintf(fd, header);
	for(;;) {
		if (refindex >= refData->getTupleCount()) break;
		if (index >= table1->getTupleCount()) break;

		refkey = refData->getKey(refindex);
		key = table1->getKey(index);
		compare = ocKey::compareKeys(refkey, key, keysize);

		if (compare == 0) {
			//-- matching keys; both values present
			refvalue = refData->getValue(refindex++);
			value = table1->getValue(index++);
			ocKey::keyToUserString(key, varlist, keystr);
		}
		else if (compare > 0) {
			//-- ref value is zero
			refvalue = 0;
			value = table1->getValue(index++);
			ocKey::keyToUserString(key, varlist, keystr);
		}
		else {
			//-- table value is zero
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


static void orderIndices(char **stringArray, int len, int *order) {
	//// Figure out alphabetical order for the dv states
	// (This isn't the most effficient algorithm, but it's simple, and enough to sort a few string values.)
//	int *order = new int[len];
	
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


void ocReport::printConditional_DV(FILE *fd, ocModel *model)
{
	ocTable *input_data = manager->getInputData();
	ocTable *test_data = manager->getTestData();
	ocTable *fit_table = manager->getFitTable();
	double sample_size = manager->getSampleSz();
	double test_sample_size = manager->getTestSampleSize();
	if (fit_table == NULL) {
		fprintf(fd, "Error: no fitted table computed.\n");
		return;
	}
	ocVariableList *var_list = manager->getVariableList();
	if(!var_list->isDirected()){
		printf("(DV calculation not possible for neutral systems.)\n");
		return;
	}

	int dv_index = var_list->getDV();			// Get the first DV's index
	ocVariable *dv_var = var_list->getVariable(dv_index);	// Get the (first) DV itself
	int var_count = var_list->getVarCount();		// Get the number of variables
	int key_size = input_data->getKeySize();		// Get the key size from the reference data
        int dv_card = dv_var->cardinality;			// Get the cardinality of the DV

	char *key_str = new char[var_count + 1];		// Used to hold user-strings for keys in several places

	int iv_statespace = ((long) ocDegreesOfFreedom(var_list) + 1) / dv_card;	// full statespace divided by cardinality of the DV
	char **dv_label = new char*[dv_card];
	ocKeySegment **fit_key = new ocKeySegment *[iv_statespace];
	double **fit_prob = new double *[iv_statespace];
	double *fit_dv_prob = new double[dv_card];
	double *fit_key_prob = new double[iv_statespace]; 
	int *fit_rule = new int[iv_statespace]; 	
	ocKeySegment **input_key = new ocKeySegment *[iv_statespace];
	int **input_freq = new int *[iv_statespace];
	int *input_dv_freq = new int[dv_card];
	int *input_key_freq = new int[iv_statespace]; 
	int *input_rule = new int[iv_statespace]; 	
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
	
	char **map = dv_var->valmap;
	for(int i=0; i < dv_card; i++) {
		int len1 = strlen(map[i]);
		dv_label[i] = new char[len1+1];
		strncpy(dv_label[i], map[i], len1);	
		dv_label[i][len1] = '\0';
		fit_dv_prob[i] = 0.0;
		input_dv_freq[i] = 0;
		test_dv_freq[i] = 0;
	}
	
	const char *format, *header, *header_sep, *header_test1, *header_test2, *header_end, *header2, *footer;
	const char *format_percent, *format_str, *format_float, *format_int;
	const char *row0, *row1, *emphasis, *end, *cell_sep;
	format_percent = "%6.3f";
	format_str     = "%s";
	format_float   = "%6.0f";
	format_int     = "%d";
	footer = row0 = row1 = emphasis = "";
	end = "\n";

	if (htmlMode) fprintf(fd,"<br>\n");
	fprintf(fd,"-------------------------------------------------------------------------\n");
	if (htmlMode) fprintf(fd,"<br><br>\n");
	fprintf(fd, "Conditional DV (D) (%%) for each IV composite state for the Model %s    \n", model->getPrintName());
	if (htmlMode) fprintf(fd, "<br><br>\n");

	// Set appropriate format
	int sep_style = htmlMode ? 0 : separator;
	switch(sep_style) {
	case 0:
		header  = " <table border=0 cellpadding=0 cellspacing=0><tr><th>Cell</th><th>Freq</th><th></th><th colspan=2>Cond_DV</th>";
		header_sep = "<th> </th>";
		header_test1 = "<th> </th><th> </th><th> </th><th> </th><th>|</th><th colspan=2>Test Data</th>";
		header_test2 = "<th> </th><th colspan=2>%%correct</th>";
		header_end = "</tr>\n";
		header2 = "<tr><td>&nbsp;</td><td> ";
		format  = "<tr class=\"%s\"><td>%s</td><td>%d</td><td>";
		// These three are row styles, for white & grey background colors and bold text
		row0 = "r0";
		row1 = "r1";
		emphasis = "em";
		cell_sep = "</td><td align=center>";	
		end     = "</td></tr>\n";
		footer  = "</table><br>\n";
		break;
	case 1:
		header = "Cell\tFreq\tCond_DV\t ";
		header_sep = "\t ";
		header_test1 = "\t \t \t \t \t|\tTest Data";
		header_test2 = "\t \t%%correct\t ";
		header_end = "\n";
		header2="\t";
		format = "%s%s\t%d";
		cell_sep = "\t";
		break;
	case 2:
		header = "Cell,Freq,Cond_DV,";
		header_sep = ", ";
		header_test1 = ", , , , ,|,Test Data";
		header_test2 = ", ,%%correct, ";
		header_end = "\n";
		header2=",";
		format = "%s%s,%d";
		cell_sep = ",";
		break;
	case 3:
		header = "    Cell    Freq     Cond_DV    ";
		header_sep = "    ";
		header_test1 = "                     |  Test Data";
		header_test2 = "    %%correct    ";
		header_end = "\n    ------------------------------------\n";
		header2="              ";
		format = "%s%8s  %d";
		cell_sep = "  ";
		break;
	}

	int index = 0;
	int keys_found = 0;
	ocKeySegment *key;
	double temp_value;
	long *index_sibs = new long[dv_card];
	int key_compare, num_sibs;

	int fit_table_size = fit_table->getTupleCount();
	int input_data_size = input_data->getTupleCount();
	int test_data_size = 0;
	if(test_data != NULL) {
		test_data_size = test_data->getTupleCount();
	}
	int dv_value, best_i;

	// Count up the total frequencies for each DV value in the reference data, for use in tie-breaking
	for (int i=0; i < input_data_size; i++) {
		temp_key = input_data->getKey(i);
		ocKey::getKeyValue(temp_key, key_size, var_list, dv_index, &dv_value);
		input_dv_freq[dv_value] += (int)(input_data->getValue(i) * sample_size);
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
			ocKey::getKeyValue(temp_key, key_size, var_list, dv_index, &dv_value);	
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
		if (index >= input_data_size) break;

		key = input_data->getKey(index);
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
		ocKey::getSiblings(key, var_list, input_data, index_sibs, dv_index, &num_sibs);

		temp_value = 0.0;
		for(int i=0; i < num_sibs; i++) {
			// Sum up the total frequencies among the siblings
			temp_value += input_data->getValue(index_sibs[i]);
			ocKeySegment *temp_key = input_data->getKey(index_sibs[i]);
			ocKey::getKeyValue(temp_key, key_size, var_list, dv_index, &dv_value);
			input_freq[fit_index][dv_value] = (int)round(input_data->getValue(index_sibs[i]) * sample_size);
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
			if (index >= test_data_size) break;
	
			key = test_data->getKey(index);
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
			ocKey::getSiblings(key, var_list, test_data, index_sibs, dv_index, &num_sibs);
	
			best_i = 0;	temp_value = 0.0;
			for(int i=0; i < num_sibs; i++) {
				// Sum up the total frequencies among the siblings
				temp_value += test_data->getValue(index_sibs[i]);
				ocKeySegment *temp_key = test_data->getKey(index_sibs[i]);
				ocKey::getKeyValue(temp_key, key_size, var_list, dv_index, &dv_value);
				test_freq[fit_index][dv_value] = (int)round(test_data->getValue(index_sibs[i]) * test_sample_size);
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



	// Display the data for debugging
	if(0) {
		double value;
		if(test_sample_size > 0) {
			fprintf(fd, "[DEBUG] Test Data:<br>\n");
			for(long i=0; i < test_data_size; i++) {
				key = test_data->getKey(i);
				value = test_data->getValue(i);
				ocKey::keyToUserString(key, var_list, key_str);
				fprintf(fd, "%d: %s %6.3f<br>\n", i, key_str, value);
			}
			fprintf(fd, "<br>\n");
		}
	
		fprintf(fd, "[DEBUG] Reference Data:<br>\n");
		for(long i=0; i < input_data_size; i++) {
			key = input_data->getKey(i);
			value = input_data->getValue(i);
			ocKey::keyToUserString(key, var_list, key_str);
			fprintf(fd, "%d: %s %6.3f<br>\n", i, key_str, value);
		}
		fprintf(fd, "<br>\n");
	
		fprintf(fd, "[DEBUG] Fit Table:<br>\n");
		for(long i=0; i < fit_table_size; i++) {
			key = fit_table->getKey(i);
			value = fit_table->getValue(i);
			ocKey::keyToUserString(key, var_list, key_str);
			fprintf(fd, "%d: %s %6.4f<br>\n", i, key_str, value);
		}
		fprintf(fd, "<br>\n");
	
		fprintf(fd, "[DEBUG] Fit & Input Freqs:<br>\n");
		for(int i=0; i < iv_statespace; i++) {
			fprintf(fd, "%d: %6.3f %6.3f %d %d %d %d<br>\n", i, fit_prob[i][0], fit_prob[i][1], input_freq[i][0], input_freq[i][1], test_freq[i][0], test_freq[i][1]);
		}
		fprintf(fd, "<br>\n");
	}

	// Get an ordering for the dv values, so they can be displayed in ascending order.
	int *dv_order = new int[dv_card];
	orderIndices(dv_label, dv_card, dv_order);

	// Print the header rows for the output table
	fprintf(fd, header);
	if(dv_card > 2) {
		for(int i=2; i < dv_card; i++) {
			fprintf(fd, header_sep);
		}
	}
	if(test_sample_size > 0) {
		fprintf(fd, header_test1);
		if(dv_card > 2) {
			for(int i=2; i < dv_card; i++) {
				fprintf(fd, header_sep);
			}
		}
		fprintf(fd, header_test2);
	}
	fprintf(fd, header_end);
	fprintf(fd, header2);
	fprintf(fd, cell_sep);
	// Print the values for the DV states, above each column
	for(int i=0; i < dv_card; i++) {
		fprintf(fd, cell_sep);
		fprintf(fd, "%s=", dv_var->abbrev);
		fprintf(fd, dv_label[dv_order[i]]);	
	}
	fprintf(fd, cell_sep);
	fprintf(fd, cell_sep);
	fprintf(fd, "rule");
	fprintf(fd, cell_sep);
	fprintf(fd, "#correct");
	fprintf(fd, cell_sep);
	fprintf(fd, "%%correct");

	if(test_sample_size > 0) {
		fprintf(fd, cell_sep);
		fprintf(fd, "|");
		// Print the values for the DV states, above each column
		for(int i=0; i < dv_card; i++) {
			fprintf(fd, cell_sep);
			fprintf(fd, "%s=", dv_var->abbrev);
			fprintf(fd, dv_label[dv_order[i]]);
		}
		fprintf(fd, cell_sep);
		fprintf(fd, "freq");
		fprintf(fd, cell_sep);
		fprintf(fd, "rule");
		fprintf(fd, cell_sep);
		fprintf(fd, "best");
	}
	fprintf(fd,end);

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
	int *test_marginal;
	int test_by_fit_rule, test_by_test_rule;
	if(test_sample_size > 0) {
		test_marginal = new int[dv_card];
		for(int i=0; i < dv_card; i++) {
			test_marginal[i] = 0;
			for(int j=0; j < iv_statespace; j++) {
				test_marginal[i] += test_freq[j][i];
			}
		}
		test_by_fit_rule = 0;	// correct on test data by fit rule
		test_by_test_rule = 0;	// correct on test data by test rule (best possible performance)
		for(int i=0; i < iv_statespace; i++) {
			test_by_fit_rule += test_freq[i][fit_rule[i]];
			test_by_test_rule += test_freq[i][test_rule[i]];
		}
	}

	// For each of the model's keys (ie, each row of the table)...
	for(int i=0; i < iv_statespace; i++) {
		ocKey::keyToUserString(fit_key[i], var_list, key_str);
		// Print out the key (the "Cell" column) and the frequency of that key.
		// Also, switch the bgcolor of each row from grey to white, every other row. (If not in HTML, this does nothing.)
		if (i % 2) {
			fprintf(fd, format, row0, key_str, input_key_freq[i]);
		} else {
			fprintf(fd, format, row1, key_str, input_key_freq[i]);
		}
		// Print out the percentages for each of the DV states
		for(int j=0; j < dv_card; j++) {
			fprintf(fd, cell_sep);
			fprintf(fd, format_percent, fit_prob[i][dv_order[j]] / fit_key_prob[i] * 100.0);
		}
		fprintf(fd, cell_sep);
		// Print the DV state of the best rule.
		fprintf(fd, cell_sep);
		fprintf(fd, format_str, dv_label[fit_rule[i]]);
		fprintf(fd, cell_sep);
		// Number correct (of the input data, based on the rule from fit)
		fprintf(fd, format_int, input_freq[i][fit_rule[i]]);
		fprintf(fd, cell_sep);
		// Percent correct (of the input data, based on the rule from fit)
		fprintf(fd, format_percent, (double)input_freq[i][fit_rule[i]] / (double)input_key_freq[i] * 100.0);
		if(test_sample_size > 0) {
			fprintf(fd, cell_sep);
			fprintf(fd, "|");
			// Test data
			// Print out the percentages for each of the DV states
			for(int j=0; j < dv_card; j++) {
				fprintf(fd, cell_sep);
				fprintf(fd, format_percent, (double)test_freq[i][dv_order[j]] / (double)test_key_freq[i] * 100.0);	
			}
			fprintf(fd, cell_sep);
			// Frequency in test data
			fprintf(fd, format_int, test_key_freq[i]);
			fprintf(fd, cell_sep);
			fprintf(fd, format_percent, (double)test_freq[i][fit_rule[i]] / (double)test_key_freq[i] * 100.0);
			fprintf(fd, cell_sep);
			fprintf(fd, format_percent, (double)test_freq[i][test_rule[i]] / (double)test_key_freq[i] * 100.0);
		}
		fprintf(fd, end);
	}

	// Print out the totals row.
	fprintf(fd, format, emphasis, "total", (int)sample_size);
	fprintf(fd, cell_sep);
	// Print the marginals for each DV state
	for(int j=0; j < dv_card; j++) {
		fprintf(fd, format_percent, marginal[dv_order[j]] * 100.0);
		fprintf(fd, cell_sep);
	}
	fprintf(fd, cell_sep);
	fprintf(fd, cell_sep);
	fprintf(fd, format_int, total_correct);
	fprintf(fd, cell_sep);
	fprintf(fd, format_percent, (double)total_correct / sample_size * 100.0);
	if(test_sample_size > 0) {
		fprintf(fd, cell_sep);
		fprintf(fd, "|");
		fprintf(fd, cell_sep);
		// Print the test marginals for each DV state
		for(int j=0; j < dv_card; j++) {
			fprintf(fd, format_percent, (double)test_marginal[dv_order[j]] / test_sample_size * 100.0);
			fprintf(fd, cell_sep);
		}
		fprintf(fd, format_int, (int)test_sample_size);
		fprintf(fd, cell_sep);
		fprintf(fd, format_percent, (double)test_by_fit_rule / test_sample_size * 100.0);
		fprintf(fd, cell_sep);
		fprintf(fd, format_percent, (double)test_by_test_rule / test_sample_size * 100.0);
	}
	fprintf(fd, end);

	fprintf(fd, footer);

	delete key_str;
	delete dv_order;
	for(int i=1; i < model->getRelationCount(); i++){
		printConditional_DV_rel(fd,model->getRelation(i));	
	}
	exit(1);
}



void ocReport::printConditional_DV_rel(FILE *fd, ocRelation *rel)
{
	ocTable *refData = manager->getInputData();
	ocTable *fitTable1 = rel->getTable();
	double samplesz=manager->getSampleSz();
	if (fitTable1 == NULL) {
		fprintf(fd, "Error: no fitted table computed\n");
		return;
	}
	ocVariableList *varlist = rel->getVariableList();
	// table to store conditional DV values.
	//ocTable *table_DV= new ocTable(varlist->getKeySize(),100);
	int DV_index = -1;
	if(varlist->isDirected()) {
		 DV_index=varlist->getDV();
	} else {
		printf("DV calculation not possible for neutral system\n");
		exit(1);
	}

	long varcount = varlist->getVarCount();
	int keysize = refData->getKeySize();

	ocVariable *var = varlist->getVariable(DV_index);
        int card=var->cardinality;
	long *index_sibs=new long[card];

	// allocate space for dv_data
	dv_Data dv_data;	
	int StateSpace = (long) ocDegreesOfFreedom(varlist) + 1;
	int i_statespace = StateSpace / card;	// statespace divide by cardinalty of output variable 
	dv_data.key=new ocKeySegment *[i_statespace];
	dv_data.cdv_value=new double *[i_statespace];
	dv_data.t_freq=new double[i_statespace]; 	
	dv_data.num_correct=new double[i_statespace]; 	
	dv_data.percent_correct = new double[i_statespace]; 	
	dv_data.rule_index = new int[i_statespace]; 	
	ocKeySegment *t_key;
	double *t_valptr;
	for(int i=0; i < i_statespace; i++) {
		t_key=new ocKeySegment[keysize];
		for(int j=0; j < keysize; j++) {
			t_key[j] = DONT_CARE;
		}
		dv_data.key[i]=t_key;
		t_valptr = new double[card];
		for(int k=0; k < card; k++) {
			t_valptr[k] = 0.0;
		}
		dv_data.cdv_value[i] = t_valptr;
	}
	
	

	const char *format, *header, *header2, *footer, *format1, *format2, *format3;
	const char *end, *separator1;
	char *keystr = new char[varcount+1];
	fprintf(fd,"-------------------------------------------------------------------------\n");
	if (htmlMode) fprintf(fd, "<br><br>\n");
	fprintf(fd, "\nConditional DV (D) (%%) for each IV composite state for the relation %s    \n\n",rel->getPrintName());
	if (htmlMode) fprintf(fd, "<br><br>\n");

	//-- set appropriate format
	int sepStyle = htmlMode ? 0 : separator;
	switch(sepStyle) {
	case 0:
		header = "<table border=0 cellpadding=0 cellspacing=0><tr><th>Cell</th><th>Freq</th><th></th><th colspan=2>Cond_DV</th></tr>\n";
		header2="<tr><td>    </td><td>       x";
		separator1="</td><td>";
		format = "<tr bgcolor=\"%s\"><td>%s</td><td>%d</td><td>";
		format1="%6.3f";
		format2="%s";
		format3="%6.0f";
		end="</td></tr>\n";
		footer = "</table>";
		break;
	case 1:
		header = "Cell\tFreq\tCond_DV\n";
		header2="\t";
		format = "%s\t%d";
		format1="%6.3f";
		format2="%s";
		format3="%6.0f";
		separator1="\t";
		end="\n";
		footer = "";
		break;
	case 2:
		header = "Cell,Freq,Cond_DV\n";
		format = "%s,%d";
		header2=",";
		format1="%6.3f";
		format2="%s";
		format3="%6.0f";
		separator1=",";
		end="\n";
		footer = "";
		break;
	case 3:
		header = "    Cell    Freq     Cond_DV\n    ------------------------------------\n";
		format = "%8s  %d";
		header2="              ";
		format1="%6.3f";
		format2="%s";
		format3="%6.0f";
		separator1="  ";
		end="\n";
		footer = "";
		break;
	}
	int index, refindex;
	ocKeySegment *key;
	ocKeySegment *temp_key=new ocKeySegment[keysize];
	double value;
	
	//-- walk through both lists. Missing values are zero.
	//-- we don't print anything if missing in both lists.
	index = 0; refindex = 0;
	fprintf(fd, header);
	fprintf(fd, header2);
	int k_count=0;

	//initiallize dv_vale in dv_data
	dv_data.dv_value = new char*[card];
	char **map = var->valmap;
	for(int i=0; i < card; i++) {
		int len1 = strlen(map[i]);
		dv_data.dv_value[i]=new char[len1+1];
                strncpy(dv_data.dv_value[i], map[i], len1);	
		dv_data.dv_value[i][len1]='\0';
	}
	
	fprintf(fd, separator1);
	for(int i=0; i < card; i++) {
		fprintf(fd, separator1);
		fprintf(fd,dv_data.dv_value[i]);	
	}
	fprintf(fd,end);
	
	for(;;) {
		int num_sibs=0;
		double t_value=0; 
		double t_freq=0;
		double percent_DV=0;
		if (refindex >= refData->getTupleCount()) break;
		if (index >= fitTable1->getTupleCount()) break;

		//refkey = refData->getKey(refindex);
		key = fitTable1->getKey(index);
		//compare = ocKey::compareKeys(refkey, key, keysize);

		// Why is this block here? [jsf]
		{
			//-- matching keys; both values present
			//refvalue = refData->getValue(refindex++);
			value = fitTable1->getValue(index++);
			//ocKey::keyToUserString(key, varlist, keystr);
        		memcpy((int *)temp_key,(int *)key,keysize*sizeof(ocKeySegment));
			ocKey::setKeyValue(temp_key,keysize,varlist,DV_index,DONT_CARE);
//check this*******
			int flag=0;
			for(int i=0;i<k_count;i++){
				int comp=ocKey::compareKeys((ocKeySegment *)dv_data.key[i],temp_key,keysize);	
				if(comp ==0)flag= 1;
			}
			if(flag == 0) {
				memcpy((int *)dv_data.key[k_count],(int *)temp_key,sizeof(ocKeySegment)*keysize);
				ocKey::getSiblings(key,varlist,fitTable1,index_sibs,DV_index,&num_sibs);
				for(int i=0; i < num_sibs; i++) {
					t_value+=fitTable1->getValue(index_sibs[i]);	
				}
				//printf("no of siblings %d\n",num_sibs);
				percent_DV = ((value * 1000) / (t_value * 1000)) * 100;
				for(int i=0; i < num_sibs; i++) {
					ocKeySegment *tkey=fitTable1->getKey(index_sibs[i]);	
					int dv_value=0;
					ocKey::getKeyValue(tkey,keysize,varlist,DV_index,&dv_value);	
					double cdv_value=0;
					cdv_value=((fitTable1->getValue(index_sibs[i]))/t_value)*100;
					//put it in dv_data
					dv_data.cdv_value[k_count][dv_value]=cdv_value;
					//long ref_key_i=refData->indexOf(tkey);
					//t_freq+=refData->getValue(ref_key_i)*1000;
					if(i==0) {
						dv_data.num_correct[k_count]=cdv_value;		
					} else {
						if(cdv_value>dv_data.cdv_value[k_count][dv_value - 1]) {
							dv_data.num_correct[k_count] = cdv_value;
						} else {
							dv_data.num_correct[k_count] = dv_data.cdv_value[k_count][dv_value - 1];
						}
					}			
				}
				dv_data.num_correct[k_count] = dv_data.num_correct[k_count] * t_value * samplesz / 100;	
				t_freq = t_value;
				dv_data.t_freq[k_count] = t_freq;
				k_count++;
			}
		}
		if(k_count >= i_statespace) break;
	}
	double *marginal=new double[card];
	for(int i=0;i<card;i++){
		marginal[i]=0.0;
		for(int j=0;j<k_count;j++){
		marginal[i]+=dv_data.cdv_value[j][i]*dv_data.t_freq[j];
	
		}
		marginal[i]=marginal[i];
	}
	double percent_correct = 0.0;
	for(int i=0; i < k_count; i++) {
		percent_correct+=dv_data.num_correct[i];	
	}
	percent_correct = percent_correct * 100 / samplesz;
	fprintf(fd, header2);
	fprintf(fd, separator1);
	for(int i=0; i < card; i++) {
		fprintf(fd, separator1);
		fprintf(fd,format1,marginal[i]);	
	}
	fprintf(fd, separator1);
	fprintf(fd, separator1);
	fprintf(fd,"rule");
	fprintf(fd, separator1);
	fprintf(fd, separator1);
	fprintf(fd,"# correct");
	fprintf(fd,end);
	char *rule;
	char *bgcolor;
	// For each of the model's states (ie, each row of the table)...
	for(int i=0; i < k_count; i++) {
		ocKey::keyToUserString(dv_data.key[i], varlist, keystr);
		// Switch the bgcolor of each row from grey to white, every other row
		if (i % 2) {
			bgcolor = "#ffffff";
		} else {
			bgcolor = "#e0e0e0";
		}
		int o = (int)((dv_data.t_freq[i]) * samplesz);
		double m = (dv_data.t_freq[i]) * samplesz - (double)o ;
		if(m > 0.5) o = o + 1;
		// Print out the key, or model state (the "Cell" column)
		// and the frequency of that state
		fprintf(fd, format, bgcolor, keystr, o);
		double rule_val = 0;
		for(int j=0; j < card; j++) {
			// Write out the percentages for each of the conditional values
			fprintf(fd, separator1);
			fprintf(fd, format1, dv_data.cdv_value[i][j]);	
			if(rule_val <= dv_data.cdv_value[i][j]) {
				rule = dv_data.dv_value[j];
				rule_val = dv_data.cdv_value[i][j];
			}			
		}
		fprintf(fd, separator1);
		fprintf(fd, separator1);
		fprintf(fd, format2, rule);	
		fprintf(fd, separator1);
		fprintf(fd, separator1);
		fprintf(fd, format3, dv_data.num_correct[i]);	
		fprintf(fd, end);
	}
	fprintf(fd, separator1);
	fprintf(fd, separator1);
	fprintf(fd, separator1);
	fprintf(fd, separator1);
	for(int j=0; j < card; j++) {
		fprintf(fd, separator1);
	}
	fprintf(fd, separator1);
	fprintf(fd, "%% correct");
	fprintf(fd, separator1);
	fprintf(fd, separator1);
	fprintf(fd,format1,percent_correct);
	fprintf(fd, end);
	fprintf(fd, footer);
	delete keystr;
	//exit(1);
}


