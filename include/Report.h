/*
 * Report.h - generate reports from model data.
 * an Report object holds a list of models, and a list of attributes to print.
 * The collection can be sorted and/or filtered, and the resulting models printed.
 */

#ifndef OCREPORT_H
#define OCREPORT_H
#include <stdio.h>
#include "Core.h"

struct dv_Data{
    KeySegment **key;
    char **dv_value;
    double **cdv_value;
    double *t_freq;
    int *dv_freq;
    double *num_correct;
    double *percent_correct;
    int *rule_index;
};

int sortKeys(const void *d1, const void *d2);
int sortCompare(const void *k1, const void *k2);
void orderIndices(const char **stringArray, int len, int *order);

class Report {
    public:
	enum SortDir {ASCENDING, DESCENDING};
	Report(class ManagerBase *mgr);
	~Report();

	//-- Add a model to the list of models. The model is added at the end. Run sort() after
	//-- all models are added to sort them.
	void addModel(class Model *model);

	void setDefaultFitModel(class Model *model);

	//-- Set the attributes to report. This is a comma-separated list, from those in
	//-- Core.h
	void setAttributes(const char *attrlist);

	//-- One-time sort of models, based on the given attribute.
	void sort(const char *attr, SortDir dir);

	//-- Static function others can use to sort model lists
	static void sort(class Model** models, long modelCount, const char *attr, SortDir dir);
    const char* bestModelName() { return models[0]->getPrintName(); }

	//-- Print a tabular output format.
	void print(FILE *fd);
	void print(int fnum);	// use a file number instead of FILE*
	//-- Set report separator type: 1=tab, 2=comma, 3=space filled
	void setSeparator(int sep) { separator = sep; }

	//-- HTML Mode - changes formatting
	static bool isHTMLMode() {return htmlMode; }
	static void setHTMLMode(bool mode) { htmlMode = mode; }

	//-- Print residual table
	void printResiduals(FILE *fd, Model *model);
    void printResiduals(FILE *fd, Relation *rel);
    void printResiduals(FILE *fd, Model *model, Relation* rel);

	//-- Print conditional DVs
	//-- Print conditionals for a model.
	void printConditional_DV(FILE *fd, Model *model, bool calcExpectedDV);
	//-- Print conditionals for a relation.
	void printConditional_DV(FILE *fd, Relation *rel, bool calcExpectedDV);
	//-- This function is called by both of the others above.
	//-- If both model and relation are present, the relation is printed.
	void printConditional_DV(FILE *fd, Model *model, Relation *rel, bool calcExpectedDV);

    // static variables
    static int searchDir;

    // used in sortCompare
    static const char *sortAttr;
    static Report::SortDir sortDir;

    // used several places, such as Report::print
    static int maxNameLength;

    // used in sortKeys
    static VariableList *sort_var_list;
    static int sort_count;
    static int *sort_vars;
    static KeySegment **sort_keys;
    static Table *sort_table;


    protected:
	static bool htmlMode;
	class ManagerBase *manager;
	Model **models;
	Model *defaultFitModel;
	char **attrs;
	long modelCount, maxModelCount;
	long attrCount;
	int separator;
	void printSearchHeader(FILE *fd, int* attrID);
	void printSearchRow(FILE *fd, Model* model, int* attrID, bool isOddRow);
};

#endif
