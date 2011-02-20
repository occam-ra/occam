/* Copyright 2000, Portland State University Systems Science Program.  All Rights Reserved
 */

#include "ocOptions.h"
#include <stdio.h>
#include <stdlib.h>
#include <ctype.h>
#include <string.h>


static void trim(char *line)
{
    // trim leading and trailing whitespace, and trailing comments
    char *cp1, *cp2;

    // stomp trailing comment
    if ((cp2 = strchr(line, '#')) != NULL) *cp2 = '\0';

    // shift string to eliminate leading space
    cp1 = cp2 = line;
    while (*cp2 && isspace(*cp2)) cp2++;
    if (cp1 != cp2) {
	while (*cp2) {
	    (*cp1++) = (*cp2++);
	}
	*cp1 = '\0';
    }

    // stomp trailing space
    cp1 = line + strlen(line);
    while (cp1 > line && isspace(*(--cp1))) *cp1 = '\0';	// eliminate trailing space
}


/**
 * initialize options object
 */
struct ocOptionValue {
    ocOptionValue *next;
    char *value;
    char *tip;
    ocOptionValue() : next(NULL), value(NULL), tip(NULL) {}
    ~ocOptionValue() {
	delete value; delete tip;
    }
};


struct ocOptionDef {
    ocOptionDef *next;
    char *name;
    char *abbrev;
    char *tip;
    bool multi;
    struct ocOptionValue *values;
    ocOptionDef() : next(NULL), name(NULL), abbrev(NULL), tip(NULL), multi(false), values(NULL) {}
    ~ocOptionDef() {
	delete name; delete abbrev; delete tip;
	while (values) {
	    ocOptionValue *p = values;
	    values = p->next;
	    delete p;
	}
    }
};


struct ocOption {
    ocOption *next;
    ocOptionDef *def;
    char *value;
    ocOption(ocOptionDef *d, const char *v) :
	next(NULL), def(d), value(NULL)
    {
	value = new char[strlen(v) + 1];
	strcpy(value, v);
    }

    ~ocOption() { if (value) delete value; }
};


/**
 * setStandardOptions - set up the standard option definitions
 */
static void setStandardOptions(ocOptions *opts)
{
    ocOptionDef *def;
    def = opts->addOptionName("action", "a", "Specify activity for run");
    opts->addOptionValue(def, "table", "Output metrics for all relations");
    opts->addOptionValue(def, "lat", "Compute all models in the lattice, with no data");
    opts->addOptionValue(def, "fit", "Compute fit metrics for a single model");
    opts->addOptionValue(def, "search", "Search for the best fitting models");
    opts->addOptionValue(def, "recons", "Do set-based analysis");
    def = opts->addOptionName("nominal", "n", "Define nominal variables", true);
    //Anjali
    opts->addOptionValue(def, "$", "name, cardinality, type, abbreviation");
    def = opts->addOptionName("maxiv", "", "Max number of ind. variables (tables)");
    opts->addOptionValue(def, "#", "");
    def = opts->addOptionName("nmaxdh", "h", "Max number of relations per ind. var group (tables)");
    opts->addOptionValue(def, "#", "");
    def = opts->addOptionName("alpha-cutoff", "A", "Parameter for uncertainty reduction output; default=1.0");
    opts->addOptionValue(def, "#", "");
    def = opts->addOptionName("search-levels", "L", "Max levels to search (search), default=all");
    opts->addOptionValue(def, "#", "");
    def = opts->addOptionName("short-model", "m", "A model (colon delimited relation list using abbreviations)");
    opts->addOptionValue(def, "$", "e.g., AB:BC:D, NULL, SAT");
    def = opts->addOptionName("long-model", "M", "A model (colon delimited relation list using names)");
    opts->addOptionValue(def, "$", "e.g., height,weight:weight,age");
    def = opts->addOptionName("post-model-constraint", "P", "Filter out certain model types from output");
    opts->addOptionValue(def, "loops", "models with loops");
    opts->addOptionValue(def, "overlaps", "models with overlaps");
    def = opts->addOptionName("constraint", "c", "Specify a fitting constraint (search)");
    opts->addOptionValue(def, "information", "information");
    opts->addOptionValue(def, "ndf", "ndf");
    def = opts->addOptionName("optimize", "o", "Specify an optimization feature");
    opts->addOptionValue(def, "alpha", "alpha");
    opts->addOptionValue(def, "information", "information");
    opts->addOptionValue(def, "entropy", "entropy");
    opts->addOptionValue(def, "lr", "Chi-squared likelihood ratio");
    def = opts->addOptionName("optimize-search-width", "w", "Max models to keep at each level");
    opts->addOptionValue(def, "#", "");
    def = opts->addOptionName("reference-model", "f", "Specify reference model (default undirected=top, directed=bottom)");
    opts->addOptionValue(def, "top", "reference is saturated model");
    opts->addOptionValue(def, "bottom", "reference is independence model");
    opts->addOptionValue(def, "default", "reference is top for undirected, bottom for directed");
    def = opts->addOptionName("search-direction", "S", "Specify search up or down lattice");
    opts->addOptionValue(def, "up", "search up");
    opts->addOptionValue(def, "down", "search down");
    def = opts->addOptionName("ipf-maxit", "I", "Max iterations for IPF, default=266");
    opts->addOptionValue(def, "#", "");
    def = opts->addOptionName("ipf-maxdev", "i", "Max error in IPF, default=0.25");
    opts->addOptionValue(def, "#", "");
    def = opts->addOptionName("no-frequency", "", "There is no frequency data in table");
    def = opts->addOptionName("zero-value", "", "Set replacment value for zero tuples");
    opts->addOptionValue(def, "#", "");
    def = opts->addOptionName("dump-data", "", "Dump loaded data");	
    def = opts->addOptionName("palpha", "p", "Set alpha for power computation");
    opts->addOptionValue(def, "#", "");
    def = opts->addOptionName("limit", "l", "Show only COUNT best reports");
    opts->addOptionValue(def, "#", "");
    def = opts->addOptionName("title", "T", "Set title string");
    opts->addOptionValue(def, "$", "");
    def = opts->addOptionName("res", "r", "Residual plot type");
    opts->addOptionValue(def, "none", "none");
    opts->addOptionValue(def, "observed", "observed");
    opts->addOptionValue(def, "fit", "fit");
    opts->addOptionValue(def, "both", "both");
    def = opts->addOptionName("res-confband", "", "Std devs for confidence bands");
    opts->addOptionValue(def, "#", "");
    def = opts->addOptionName("res-sorted", "", "Sort residual plot");
    // I don't think this next option is used anywhere [jsf]
    def = opts->addOptionName("res-table", "R", "Print residual table and DV|IV, if directed");
    def = opts->addOptionName("sort", "s", "Sort fit-reports by features, default=info", true);
    opts->addOptionValue(def, "model", "model");
    opts->addOptionValue(def, "alpha", "alpha");
    opts->addOptionValue(def, "beta", "beta");
    opts->addOptionValue(def, "entropy", "entropy");
    opts->addOptionValue(def, "info", "info");
    opts->addOptionValue(def, "df", "df");
    def = opts->addOptionName("break-after-model", "b", "Insert a line break after printing model");
    def = opts->addOptionName("no-parse", "", "Assume the input is pure data");
    def = opts->addOptionName("verbose", "v", "Print variable and interaction lists");
    def = opts->addOptionName("re-bin", "B", "Re-binning of data required");

    //-- default option (if no command line switch) - can also be used explicitly
    def = opts->defaultOptDef = opts->addOptionName("datafile", "", "Specify data file");
    opts->addOptionValue(def, "$", "");
}


ocOptions::ocOptions()
    : defs(NULL), options(NULL)
{
    setStandardOptions(this);
}


ocOptions::~ocOptions()
{
    ocOptionDef *def;
    ocOption *opt;
    while (defs) {
	def = defs;
	defs = def->next;
	delete def;
    }	
    while (options) {
	opt = options;
	options = opt->next;
	delete opt;
    }	
}


/**
 * add a named option to the options list.  Initially this has no values
 */
ocOptionDef *ocOptions::addOptionName(const char *name, const char *abbrev, const char *tip, bool multi)
{
    ocOptionDef *def = new ocOptionDef();
    char *cp = new char[strlen(name)+1];
    strcpy(cp, name);
    def->name = cp;
    cp = new char[strlen(abbrev)+1];
    strcpy(cp, abbrev);
    def->abbrev = cp;
    cp = new char[strlen(tip)+1];
    strcpy(cp, tip);
    def->tip = cp;
    def->multi = multi;
    def->next = defs;
    defs = def;
    return defs;
}


void ocOptions::addOptionValue(struct ocOptionDef *option, const char *value, const char *tip)
{
    ocOptionValue *vp = new ocOptionValue();
    char *cp = new char[strlen(value)+1];
    strcpy(cp, value);
    vp->value = cp;
    cp = new char[strlen(tip)+1];
    strcpy(cp, tip);
    vp->tip = cp;
    vp->next = option->values;
    option->values = vp;
}


ocOptionDef *ocOptions::findOptionByName(const char *name)
{
    ocOptionDef *def = defs;
    while (def) {
	if (strcmp(name, def->name) == 0) break;
	else def = def->next;
    }
    return def;		// NULL or else matching entry
}


ocOptionDef *ocOptions::findOptionByAbbrev(const char *abbrev)
{
    ocOptionDef *def = defs;
    while (def) {
	if (strcmp(abbrev, def->abbrev) == 0) break;
	else def = def->next;
    }
    return def;		// NULL or else matching entry
}


bool ocOptions::setOptions(int argc, char **argv)
{
    char optname[MAXLINE], optvalue[MAXLINE];
    //-- command line arguments are either "--name=value" or "-abbrev" "value"
    //-- any arguments following the option are considered to be values for it
    ocOptionDef *currentOptDef = findOptionByName("");
    for(int i = 1; i < argc; i++) {
	const char *cp = argv[i];
	if (cp[0] == '-') {
	    if (cp[1] == '-') {
		//-- long form: --name=value (or for booleans, just --name)
		char * eqpos = strchr((char *)cp+2, '=');
		if (eqpos != NULL) {
		    //-- has "=value" on end
		    strncpy(optname, cp+2, eqpos-(cp+2));
		    optname[eqpos-(cp+2)] = '\0';
		    strcpy(optvalue, eqpos+1);
		}
		else {
		    //-- no value
		    strcpy(optname, cp+2);
		    optvalue[0] = '\0';
		}
		currentOptDef = findOptionByAbbrev(optname);
		if (currentOptDef) {
		    if (currentOptDef->values == NULL) { // boolean
			setOptionString(currentOptDef, "");
		    }
		    else if (strcmp(currentOptDef->values->value, "#") == 0) { // numeric
			setOptionFloat(currentOptDef, atof(optvalue));
		    }
		    else {
			setOptionString(currentOptDef, optvalue);
		    }
		    currentOptDef = NULL;	// done
		}
		else {
		    printf("Error: option %s not recognized\n", cp);
		}				
	    }
	    else {
		currentOptDef = findOptionByName(cp+1);
	    }
	    if (currentOptDef == NULL) {
		printf("Error: option %s not recognized\n", cp);
	    }
	    else {
		//-- for boolean option, set value as "true"
		if (currentOptDef->values == NULL) {
		    setOptionString(currentOptDef, "");
		}
		currentOptDef = NULL;
	    }
	}
	else {	// values for current option
	    if (currentOptDef) {
		//-- check for numeric
		if (strcmp(currentOptDef->values->value, "#") == 0) {
		    setOptionFloat(currentOptDef, atof(cp));
		}
		else {
		    setOptionString(currentOptDef, cp);
		}
		currentOptDef = NULL;
	    }
	    //-- if there is no current option, use the default option (datafile)
	    //-- this builds a list of the file arguments not accompanied by switches
	    else {
		setOptionString(defaultOptDef, cp);
	    }
	}
    }
    return true;
}


bool ocOptions::getLine(FILE *fd, char *line, int *lineno)
{
    int count;
    char current;
    line[0] = '\0';
    while(true) {
	count = 0;
	while ( count < MAXLINE ) {
	    current = (char) fgetc(fd);
	    if ( (count == 0) && feof(fd) ) break;
	    if ( (current == '\r') || (current == '\n') || feof(fd) ) {
		line[count++] = '\n';
		break;
	    } else if (current == '#') {
		while ( (current != '\r') && (current != '\n') && !feof(fd) ) {
		    current = (char) fgetc(fd);
		}
		if (count == 0) continue;
		line[count++] = '\n';
		break;
	    } else {
		line[count++] = current;
	    }
	}
	if ( (count == MAXLINE) && (line[count - 1] != '\n') ) {
	    printf("Error: maximum line length (%d) exceeded in data file.\n", MAXLINE);
	    line[MAXLINE] = '\0';
	    printf("Line begins:\n%s\n", line);
	    exit(1);
	}
	if (count > 0) {
	    line[count++] = '\0';
	    (*lineno)++;
	    trim(line);
	    if (line[0] == '\0') continue;	// skip blank lines, comments
	    if (line[0] == '\n') continue;	// skip blank lines, comments
	    return true;
	}
	else break;
    }
    return false;	// end of file
}


bool ocOptions::readOptions(FILE *fd)
{
    //-- Read options from a file.  The option name is on a line by itself,
    //-- starting with a colon.  Any option values follow on separate lines
    //-- A given option ends when there is another line with a colon or EOF.
    //-- No options are read past the :data option
    ocOptionDef *currentOptDef = NULL;
    char line[MAXLINE];
    char *cp;
    int lineno = 0;
    bool gotLine = getLine(fd, line, &lineno);
    while(gotLine) {
	cp = line;
	if (*cp == ':') {	// beginning of a new option
	    if (strcmp(cp, ":data") == 0) break;	// data values follow
	    currentOptDef = findOptionByName(cp+1);
	    if (currentOptDef == NULL) {
		printf("[%d] Error: option %s not recognized\n", lineno, cp);
	    }
	    else {
		//-- for boolean option, set value as "Y"
		if (currentOptDef->values == NULL) {
		    setOptionString(currentOptDef, "Y");
		    currentOptDef = NULL;
		}
	    }
	}
	else {	// values for current option
	    if (currentOptDef) {
		//-- check for numeric
		if (strcmp(currentOptDef->values->value, "#") == 0) {
		    setOptionFloat(currentOptDef, atof(cp));
		}
		else {
		    setOptionString(currentOptDef, cp);
		}
		// if its not a multivalue we are done
		if (!currentOptDef->multi) currentOptDef = NULL;
	    }
	    else {
		printf("[%d] Error: '%s' unexpected\n", lineno, cp);
	    }
	}
	gotLine = getLine(fd, line, &lineno);
    }
    return true;	
}


bool ocOptions::setOptionString(ocOptionDef *def, const char *value)
{
    //-- find the option value.  If there is one already, and
    //-- the option is not a multiple option, update it.
    //-- otherwise append a new option to the list
    ocOption *opt = options, *lastopt = NULL;
    ocOptionValue *val = def->values;
    while (val) {
	//-- an option of "$" means any string is legal
	//-- an option of "#" means numeric
	//-- an option of "?" means boolean
	if (strcmp("$", val->value) == 0 ||
		strcmp("#", val->value) == 0) break;
	else if (strcmp(value, val->value) == 0) break;
	else val = val->next;
    }
    if (val == NULL && toupper(value[0]) != 'Y') {
	//-- no match on option value, and it's not a boolean
	printf("Error, value '%s' not legal for option '%s'\n", value, def->name);
    }
    else {
	while (opt) {
	    if (opt->def == def && !def->multi) break;
	    lastopt = opt;
	    opt = opt -> next;
	}
	if (opt == NULL) {	// not found, or multiples allowed; append to list
	    if (lastopt == NULL) { 
		options = new ocOption(def, value); // first time
	    }
	    else {
		lastopt->next = new ocOption(def, value);	// append to list
	    }
	}
	else {	// match - update it
	    delete opt->value;
	    opt->value = new char[strlen(value)+1];
	    strcpy(opt->value, value);
	}
    }
    return true;
}


bool ocOptions::setOptionFloat(ocOptionDef *def, double nvalue)
{
    char val[32];
    sprintf(val, "%14lf", nvalue);
    return setOptionString(def, val);
}


bool ocOptions::getOptionString(const char *name, void **nextp, const char **value)
{
    ocOption *opt = nextp ? (ocOption *) *nextp : NULL;
    if (opt == NULL) opt = options;	// start of list, if next is null
    else opt = opt->next;	// already processed this one last time
    while (opt) {
	if (strcmp(opt->def->name, name) == 0) break;
	else opt = opt->next;
    }
    if (opt == NULL) return false;
    else {
	*value = opt->value;
	if (nextp) *nextp = opt;	// return for next iteration
	return true;
    }
}


bool ocOptions::getOptionFloat(const char *name, void **nextp, double *nvalue)
{
    const char *value;
    if (getOptionString(name, nextp, &value)) {
	sscanf(value, "%lf", nvalue);
	return true;
    }
    else {
	*nvalue = -1;
	return false;
    }
}


void ocOptions::write(FILE *fd, bool printHTML)
{
    const char *startline, *endline, *fieldsep;

    ocOption *opt = options;
    if (fd == NULL) fd = stdout;
    if (printHTML) {
	startline = "<TR><TD>";
	endline = "</TD></TR>\n";
	fieldsep = "</TD><TD>";
    }
    else {
	startline = "";
	endline = "\n";
	fieldsep = ",";
    }
    fprintf(fd, "%sOption settings:%s", startline, endline);
    //Anjali 
    while (opt) {
	const char *name = opt->def->name;
	const char *value = opt->value;
	// (kenw) don't print data file name here; the real name is printed elsewhere
	if (strcmp(name, "datafile") != 0) {
	    fprintf(fd, "%s%s%s%s%s", startline, name, fieldsep, value, endline);
	}
	opt = opt->next;
    }
}


