/*
 * ocReport.cpp - implements model reports
 */

#include "ocCore.h"
#include "_ocCore.h"
#include "ocReport.h"
#include "ocManagerBase.h"
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
{ATTRIBUTE_H, "H", "%12f"},
{ATTRIBUTE_T, "T", "%12f"},
{ATTRIBUTE_DF, "DF", "%14.0f"},
{ATTRIBUTE_DDF, "dDF", "%14.0f"},
{ATTRIBUTE_FIT_H, "H(IPF)", "%12f"},
{ATTRIBUTE_ALG_H, "H(ALG)", "%12f"},
{ATTRIBUTE_FIT_T, "T(IPF)", "%12f"},
{ATTRIBUTE_ALG_T, "T(ALG)", "%12f"},
{ATTRIBUTE_LOOPS, "LOOPS", "%2.0f"},
{ATTRIBUTE_EXPLAINED_I, "Information", "%12f"},
{ATTRIBUTE_UNEXPLAINED_I, "Unexp Info", "%12f"},
{ATTRIBUTE_T_FROM_H, "T(H)", "%12f"},
{ATTRIBUTE_IPF_ITERATIONS, "IPF Iter", "%7.0f"},
{ATTRIBUTE_IPF_ERROR, "IPF Err", "%12f"},
{ATTRIBUTE_PROCESSED, "Proc", "%2.0"},
{ATTRIBUTE_IND_H, "H(Ind)", "%12f"},
{ATTRIBUTE_DEP_H, "H(Dep)", "%12f"},
{ATTRIBUTE_COND_H, "H|Model", "%12f"},
{ATTRIBUTE_COND_DH, "dH|Model", "%12f"},
{ATTRIBUTE_COND_PCT_DH, "%dH(DV)", "%12f"},
{ATTRIBUTE_COND_DF, "DF(Cond)", "%14.0f"},
{ATTRIBUTE_COND_DDF, "dDF(Cond)", "%14.0f"},
{ATTRIBUTE_TOTAL_LR, "LR Total", "%12f"},
{ATTRIBUTE_IND_LR, "LR Ind", "%12f"},
{ATTRIBUTE_COND_LR, "LR|Model", "%12f"},
{ATTRIBUTE_COND_H_PROB, "H|Model", "%12f"},
{ATTRIBUTE_P2, "P2", "%12f"},
{ATTRIBUTE_P2_ALPHA, "P2 Alpha", "%12f"},
{ATTRIBUTE_P2_BETA, "P2 Beta", "%12f"},
{ATTRIBUTE_LR, "LR", "%12f"},
{ATTRIBUTE_ALPHA, "Alpha", "%12f"},
{ATTRIBUTE_BETA, "Beta", "%12f"},
{ATTRIBUTE_BP_T, "T(BP)", "%12f"},
{ATTRIBUTE_BP_H, "est. H(BP)", "%12f"},
{ATTRIBUTE_BP_EXPLAINED_I, "Information(BP)", "%12f"},
{ATTRIBUTE_BP_UNEXPLAINED_I, "est. Unexplained(BP)", "%12f"},
{ATTRIBUTE_BP_ALPHA, "Alpha(BP)", "%12f"},
{ATTRIBUTE_BP_BETA, "Beta(BP)", "%12f"},
{ATTRIBUTE_BP_LR, "LR(BP)", "%12f"},
{ATTRIBUTE_BP_COND_H, "H|Model(BP)", "%12f"},
{ATTRIBUTE_BP_COND_DH, "dH|Model(BP)", "%12f"},
{ATTRIBUTE_BP_COND_PCT_DH, "est. %dH(DV)(BP)", "%12f"},
{ATTRIBUTE_PCT_CORRECT, "% Correct", "%12f"},
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
			sprintf(field, fmt, attr);
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

	fprintf(fd, "        RESIDUALS\n\n");
	if (table1 == NULL) {
		fprintf(fd, "Error: no fitted table computed\n");
		return;
	}
	long varcount = varlist->getVarCount();
	int keysize = refData->getKeySize();
	const int cwid=15;
	const char *format, *header, *footer;
	char *keystr = new char[varcount+1];

	//-- set appropriate format
	int sepStyle = htmlMode ? 0 : separator;
	switch(sepStyle) {
	case 0:
		header = "<table><tr><th>Cell</th><th>Obs</th><th>Exp</th><th>Res</th></tr>\n";
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
			ocKey::keyToString(key, varlist, keystr);
		}
		else if (compare > 0) {
			//-- ref value is zero
			refvalue = 0;
			value = table1->getValue(index++);
			ocKey::keyToString(key, varlist, keystr);
		}
		else {
			//-- table value is zero
			refvalue = refData->getValue(refindex++);
			value = 0;
			ocKey::keyToString(refkey, varlist, keystr);
		}
		res = value - refvalue;
		if (value != 0.0 || refvalue != 0.0)
			fprintf(fd, format, keystr, refvalue, value, res);
	}
	fprintf(fd, footer);
	delete keystr;
}
