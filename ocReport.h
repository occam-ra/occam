/*
 * ocReport.h - generate reports from model data.
 * an ocReport object holds a list of models, and a list of attributes to print.
 * The collection can be sorted and/or filtered, and the resulting models printed.
 */
 
#ifndef OCREPORT_H
#define OCREPORT_H
#include <stdio.h>
#include "ocCore.h"

struct dv_Data{
        ocKeySegment **key;
	char **dv_value;
        double **cdv_value;
        double *t_freq;
	int *dv_freq;
	double *num_correct;
	double *percent_correct;
	int *rule_index;
};


class ocReport {
public:
	enum SortDir {ASCENDING, DESCENDING};
	ocReport(class ocManagerBase *mgr);
	~ocReport();
	
	//-- Add a model to the list of models. The model is added at the end. Run sort() after
	//-- all models are added to sort them.
	void addModel(class ocModel *model);
	
	//-- Set the attributes to report. This is a comma-separated list, from those in
	//-- ocCore.h
	void setAttributes(const char *attrlist);
	
	//-- One-time sort of models, based on the given attribute.
	void sort(const char *attr, SortDir dir);
	
	//-- Static function others can use to sort model lists
	static void sort(class ocModel** models, long modelCount,
		const char *attr, SortDir dir);
	
	
	//-- Print a tabular output format.
	void print(FILE *fd);
	void print(int fnum);	// use a file number instead of FILE*
	//-- Set report separator type: 1=tab, 2=comma, 3=space filled
	void setSeparator(int sep) { separator = sep; }
	
	//-- HTML Mode - changes formatting
	static bool isHTMLMode() {return htmlMode; }
	static void setHTMLMode(bool mode) { htmlMode = mode; }

	//-- Print residual table
	void printResiduals(FILE *fd, ocModel *model);
	
	//-- Print conditional DVs
	//-- Print conditionals for a model.
	void printConditional_DV(FILE *fd, ocModel *model, bool calcExpectedDV);
	//-- Print conditionals for a relation.
	void printConditional_DV(FILE *fd, ocRelation *rel, bool calcExpectedDV);
	//-- This function is called by both of the others above.
	//-- If both model and relation are present, the relation is printed.
	void printConditional_DV(FILE *fd, ocModel *model, ocRelation *rel, bool calcExpectedDV);

protected:
	static bool htmlMode;
	class ocManagerBase *manager;
	ocModel **models;
	char **attrs;
	long modelCount, maxModelCount;
	long attrCount;
	int separator;
	void printSearchHeader(FILE *fd, int* attrID);
	void printSearchRow(FILE *fd, ocModel* model, int* attrID);
};

#endif
