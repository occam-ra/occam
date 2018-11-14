/*
 * Copyright © 1990 The Portland State University OCCAM Project Team
 * [This program is licensed under the GPL version 3 or later.]
 * Please see the file LICENSE in the source
 * distribution of this software for license terms.
 */

#ifndef ___Options
#define ___Options

#include "stdlib.h"
#include <stdio.h>

// maximum line length in input file
#define MAXLINE 65535

/**
 * Defines a class which maintains the options specified by the user.
 * each option has a name and value. The options table holds all the
 * legal options and values, as well as the current options.
 */
class Options {
    public:
	Options();
	~Options();
	//-- set up options definitions.  First the option name is added,
	//-- then any values for that option.  An option with no values
	//-- is a boolean (on/off) value.  An option whose value is '#'
	//-- has a numeric value.
	class ocOptionDef *addOptionName(const char *name, const char *abbrev, const char *tip, bool multi=false);
	void addOptionValue(class ocOptionDef *option, const char *value, const char *tip);
	ocOptionDef *findOptionByName(const char *name);
	ocOptionDef *findOptionByAbbrev(const char *abbrev);

	//-- set options based on command arguments or an input file
	void setOptions(int argc, char **argv);
	bool readOptions(FILE *fd);

	//-- line reader function; for use by other input services
	static bool getLine(FILE *fd, char *line, int *lineno);

	//-- set individual options
	bool setOptionString(ocOptionDef *def, const char *value);
	bool setOptionFloat(ocOptionDef *def, double nvalue);

	//-- get option. If next == NULL, the first (or only) setting of the option
	//-- is found.  For multivalued options, pass in the argument as returned,
	//-- e.g.:
	//-- next = NULL;
	//-- while (getOption(name, &next, &value)) { ... do something with value ... }
	bool getOptionString(const char *name, void **next, const char **value);
	bool getOptionFloat(const char *name, void **next, double *nvalue);

	//-- write options to a file
	void write(FILE *fd=NULL, bool printHTML=false, bool skipNominal=false);

	class ocOptionDef *defaultOptDef;
    private:
	//-- both of these are singly linked lists.
	class ocOptionDef *defs;
	class ocOption *options;
	//-- pointer to default option (for file names on command line)
};

#endif

