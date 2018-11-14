/*
 * Copyright © 1990 The Portland State University OCCAM Project Team
 * [This program is licensed under the GPL version 3 or later.]
 * Please see the file LICENSE in the source
 * distribution of this software for license terms.
 */

#ifndef ___Report
#define ___Report

#include "Model.h"

#include <stdio.h>

constexpr const char* equals_sign(bool html) {
    return html ?  "<b style='font-size:110%;'>=</b>" : "=";
}

constexpr const char* not_equals_sign(bool html) { 
    return html ? "<b style='font-size:110%;'>&ne;</b>" : "=not";
}

class dv_Data{
  public:
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
	Report(class ManagerBase *mgr);
	~Report();

    void newl(FILE* fd);
    void hl(FILE* fd);
    int sepStyle(); 
    void header(FILE* fd, Relation* rel, bool printLift, bool printCalc, bool printStart=true);
    const char* format(bool printLift, bool printCalc);
    void footer(FILE* fd);
    const char* delim();
    const char* hdr_delim();


	//-- Add a model to the list of models. The model is added at the end. Run sort() after
	//-- all models are added to sort them.
	void addModel(class Model *model);

	void setDefaultFitModel(class Model *model);

	//-- Set the attributes to report. This is a comma-separated list, from those in
	//-- Core.h
	void setAttributes(const char *attrlist);

	//-- One-time sort of models, based on the given attribute.
	void sort(const char *attr, Direction dir);

	//-- Static function others can use to sort model lists
	static void sort(class Model** models, long modelCount, const char *attr, Direction dir);
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
	void printResiduals(FILE *fd, Model *model, bool skipTrainedTable, bool skipIVItables);
    void printSingleVariable(FILE* fd, Relation* rel, double adjustConstant);
    void printLift(FILE* fd, Relation* rel, double adjustConstant);
    void printWholeTable(FILE* fd, Model* model, double adjustConstant);
    void printRel(FILE* fd, Relation* rel, double adjustconstant, bool printLift);
    void printSummary(FILE* fd, Model* model, double adjustConstant);
    //-- Print conditional DVs
	//-- Print conditionals for a model.
	void printConditional_DV(FILE *fd, Model *model, bool calcExpectedDV, char* classTarget);
	//-- Print conditionals for a relation.
	void printConditional_DV(FILE *fd, Relation *rel, bool calcExpectedDV, char* classTarget);
	//-- This function is called by both of the others above.
	//-- If both model and relation are present, the relation is printed.
	void printConditional_DV(FILE *fd, Model *model, Relation *rel, bool calcExpectedDV, char* classTarget);

    void printConfusionMatrix(Model* model, Relation* rel, const char* dv_name, const char* dv_target,
        double trtp, double trfp, double trtn, double trfn,
        bool test, double tetp, double tefp, double tetn, double tefn);


    // static variables
    // used several places, such as Report::print
    static int maxNameLength;
	
    class ManagerBase *manager;

	static bool htmlMode;
	Model **models;
	Model *defaultFitModel;
	char **attrs;
	long modelCount, maxModelCount;
	long attrCount;
	int separator;
	void printSearchHeader(FILE *fd, int* attrID);
	void printSearchRow(FILE *fd, Model* model, int* attrID, bool isOddRow);
    char* alloc_dv_header();


    void printTableRow(FILE* fd, bool blue, VariableList* vl, int var_count, Relation* rel, double value, KeySegment* refkey, double refvalue, double iviValue, double adjustConstant, double sample_size, bool printLift, bool printCalc);
    void printTable(FILE* fd, Relation* rel, Table* fit_table, Table* input_table, Table* indep_table, double adjustConstant, double sample_size, bool printLift, bool printCalc);
    
    void printTestData(FILE* fd, Relation* rel, Table* fit_table, Table* indep_table, double adjustConstant, int keysize, bool printCalc, bool printLift);

    void printDyadSummary(FILE* fd, Model* model);
    void findEntropies(Relation* rel, double& h1, double& h2, double& h12);
    void findLift(Relation* rel, double sample_size, double& lift, char*& stateName, double& freq);
};



#endif
