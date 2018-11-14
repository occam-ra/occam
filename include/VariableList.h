/*
 * Copyright © 1990 The Portland State University OCCAM Project Team
 * [This program is licensed under the GPL version 3 or later.]
 * Please see the file LICENSE in the source
 * distribution of this software for license terms.
 */

#ifndef ___VariableList
#define ___VariableList

#include "Variable.h"

/**
 * VariableList - defines a list of variables for the current problem. A public
 * variable object is not required, because all variables are referenced by index
 * (i.e., there is an implied order).
 */
class VariableList {
    public:
        VariableList(int maxvars);
        ~VariableList();
        long size();

        //-- addVariable - add a variable, and return the index
        int addVariable(const char *name, const char *abbrev, int cardinality, bool dv = false,
                bool rebin = false, int old_card = -1);

        //-- get the required minimum size for keys, based on all defined variables
        int getKeySize();

        //-- get the information about a variable
        Variable *getVariable(int index);

        //-- get the number of variables
        int getVarCount() {
            return varCount;
        }

        //-- get the number of variables in the actual data file
        int getVarCountDF() {
            return varCountDF;
        }

        //-- generate printable variable list (copied to str, max=maxlength)
        void getPrintName(char *str, int maxlength, int count, int *vars, int *states = nullptr);
        int getPrintLength(int count, int *vars, int *states = nullptr);

        //-- see if this is a directed system
        bool isDirected();

        //--gets the first DV
        int getDV();

        //-- generate a variable index list from a standard format name name
        int getVariableList(const char *name, int *varlist);

        //-generate a variable index and state constrain index list from a standard format name name
        int getVarStateList(const char *name, int *varlist, int *stlist);

        int getMaxAbbrevLen() {
            return maxAbbrevLen;
        }

        //-- get the value index for a nominal value. If this value has been seen before,
        //-- it is looked up in the value map. If not, it is added to the map. -1 is returned
        //-- if the value map is full, meaning that the cardinality information for the
        //-- variable is incorrect.
        int getVarValueIndex(int varindex, const char *value);

        //-- get the printable variable value from a given value index
        const char *getVarValue(int varindex, int valueindex);

        //-- check cardinalities of variables against the data, after input
        bool checkCardinalities();

        //-- dump debug output
        void dump();

        // Checks whether a variable is in use.  Returns 1 for yes, 0 for no (marked to ignore in input file).
        int isVarInUse(int i);

        //Anjali
        //marks a particular variable as not be considered in the model
        int markForNoUse();

        //Anjali
        //get the new rebinning value for an old one
        int getNewValue(int, char*, char*);

    private:
        Variable *vars;
        int varCount; // number of variables defined so far
        int varCountDF; //(Anjali) original no. of variables in data file, some may be marked for no use
        int maxVarCount; // max number of variables
        int maxAbbrevLen;
        //int maxVarMask;		//(Anjali) max no. of longs being used for mask at any given time
        //long *maskVars;		//(Anjali) this should store the positions of variables which are to be ignored
        int noUseMaskSize;
        bool *noUseMask;
};

#endif
