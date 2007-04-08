/* Copyright 2000, Portland State University Systems Science Program.  All Rights Reserved
 */
#ifndef OCCORE_H
#define OCCORE_H

  
//-- typedef for constructing data keys - defined as a 32-bit type. A key consists
//-- of an array of key segments.  Variable values are packed together into the key
//-- but don't cross segment boundaries. For example, 16 3-state variables can be
//-- packed into one key segment.
typedef unsigned long ocKeySegment;
typedef double ocTupleValue;

/**
 * ocTable - defines a data table, which is a collection of tuples. The tuples are stored
 * in a contiguous table.  Since tuples are variable sized, the ocTable object stores the
 * size information for the tuple storage.
 */
class ocTable {
public:
	//-- table types
	enum TableType {INFO_TYPE, SET_TYPE};
	ocTable(int keysz, long maxTuples, TableType typ = INFO_TYPE);	// initialize the table and allocate tuple space
	~ocTable();
	long size();
	
	void copy(const ocTable *from);	// copy data table
	
	//-- add or sum tuples in the table.  These take into account the type of table
	//-- (info theoretic or set theoretic)
	void addTuple(ocKeySegment *key, double value);	// append to end
	void insertTuple(ocKeySegment *key, double value, long index);	// insert in given spot
	void sumTuple(ocKeySegment *key, double value); // add (or) this value to matching tuple
	
	//-- key and value access functions	
	double getValue(long index);
	void setValue(long index, double value);
	ocKeySegment *getKey(long index);
	void copyKey(long index, ocKeySegment *key);
	
	//-- find the given key. If matchOnly is true, -1 is returned on no match.
	//-- if matchOnly is false, the position of the next higher tuple is returned
	long indexOf(ocKeySegment *key, bool matchOnly = true);	//
	long getTupleCount() { return tupleCount; }
	int getKeySize()	{ return keysize; }
	
	void sort();	// sort tuples by key
	void reset(int keysize);	// reset table to empty, but reuse the storage
	
	// dump debug output
	void dump(bool detail = false);
	
	// normalize information-theoretic table.  No effect for set-theoretic tables
	// if these are counts, then the return value is the sample size
	int normalize();

	// get index of maximum value
	long getMaxValue();
	
private:
	void* data;			// storage for all keys and values
	int keysize;		// number of key segments in the key for each tuple
	long tupleCount;	// number of tuples in the tuple array
	long maxTupleCount;	// the total size of the data member, in terms of tuples
	TableType type;			// one of INFO_TYPE, SET_TYPE
};

/**
 * static functions for manipulating keys and masks (a mask has all 0's in the
 * slot for a variable if it is included in the mask, 1's otherwise)
 */
class ocKey {
public:
	//-- key construction and manipulation functions
	
	// build a key, setting don't care's for all variables except those provided,
	// and setting the appropriate values where provided. Space for the key is
	// allocated by the caller. Key points to key storage of at least keysize;
	// varindices and varvalues are the same length and
	static void buildKey(ocKeySegment *key, int keysize, class ocVariableList *vars,
		int *varindices, int *varvalues, int varcount);
	
	// build a key with a value for every variable.
	static void buildFullKey(ocKeySegment *key, int keysize, class ocVariableList *vars, int *varvalues);
		
	// set a single value within a key. Value can be DONT_CARE or a legal variable value.
	static void setKeyValue(ocKeySegment *key, int keysize, class ocVariableList *vars, int index, int value);
	// get a single value within a key. Value can be DONT_CARE or a legal variable value.
	static int getKeyValue(ocKeySegment *key, int keysize, class ocVariableList *vars, int index);

		
	// compare two keys, returning -1, 0, or 1 as the first is less than, equal to, or
	// greater than the second (lexically).
	static int compareKeys(ocKeySegment *key1, ocKeySegment *key2, int keysize);

	// copy key1 to key1
	static int copyKey(ocKeySegment *key1, ocKeySegment *key2, int keysize);

	static void buildMask(ocKeySegment *mask, int keysize, class ocVariableList *vars, int *varindices, int varcount);

	static void keyToString(ocKeySegment *key, ocVariableList *var, char *str);
	static void keyToUserString(ocKeySegment *key, ocVariableList *var, char *str);
	static void getSiblings(ocKeySegment *key, ocVariableList *vars, ocTable *table, long *i_sibs, int DV_ind, int *no_sib);


};

const int DONT_CARE = 0xffffffff;	// all bits on
const int KEY_SEGMENT_BITS = 32;	// number of usable bits in a key segment


/**
 * ocVariableList - defines a list of variables for the current problem. A public
 * variable object is not required, because all variables are referenced by index
 * (i.e., there is an implied order).
 */
const int MAXNAMELEN = 32;
const int MAXABBREVLEN = 8;
const int MAXCARDINALITY = 100;
 
const int ALL =1;
const int REST_ALL=-1;
const int KEEP =1;
const int DISCARD =-1;
#define OLD_ROW 0
#define NEW_ROW 1

struct ocVariable {	// internal use only - see ocVariableList
	int cardinality;	// number of values of the variable
	int segment;	// which ocKeySegment of the key this variable is in
	int shift;		// starting rightmost bit position of value in segment
	int size;		// number of bits (log2 of (cardinality+1))
	bool dv;		// is it a dependent variable?
	ocKeySegment mask;	// a bitmask of 1's in the bit positions for this variable
	char name[MAXNAMELEN+1]; 	// long name of variable (max 32 chars
	char abbrev[MAXABBREVLEN+1];	// abbreviated name for variable
	char* valmap[MAXCARDINALITY];	// maps input file values to nominal values
	bool rebin; //is rebinning required for this variable
	char * oldnew[2][MAXCARDINALITY];
	int old_card;	
	char *exclude;	

};

class ocVariableList {
public:
	ocVariableList(int maxvars);
	~ocVariableList();
	long size();
	
	//-- addVariable - add a variable, and return the index
	int addVariable(const char *name, const char *abbrev, int cardinality, bool dv = false,bool rebin=false,int old_card=-1);
	
	//-- get the required minimum size for keys, based on all defined variables
	int getKeySize();

	//-- get the information about a variable
	ocVariable *getVariable(int index);
	
	//-- get the number of variables
	int getVarCount() { return varCount; }

	//-- get the number of variables in the actual data file
	int getVarCountDF() { return varCountDF; }

	//-- generate printable variable list (copied to str, max=maxlength)	
	void getPrintName(char *str, int maxlength, int count, int *vars,int *state=0);
	int getPrintLength(int count, int *vars,bool state_b=false);
	
	//-- see if this is a directed system
	bool isDirected();

	//--gets the first DV
	int getDV();
	
	//-- generate a variable index list from a standard format name name
	int getVariableList(const char *name, int *varlist);

	//-generate a variable index and state constrain index list from a standard format name name
	int getVar_StateList(const char *name, int *varlist, int *stlist);
	
	int getMaxAbbrevLen() { return maxAbbrevLen; }

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

	//Anjali
	//checks whether this variable has to be dropped since its type is 0 or is  it good 
	int good(int i);

	//Anjali
	//marks a particular variable as not be considered in the model
	int markForNoUse();

	//Anjal
        //get the new rebinning value for an old one
        int getnewvalue(int,char*,char*);



			
private:
	ocVariable *vars;
	int varCount;		// number of variables defined so far
	int varCountDF;   //(Anjali) original no. of variables in data file, some may be marked for no use
	int maxVarCount;	// max number of variables
	int maxVarMask;     //(Anjali) max no. of longs being used for mask at any given time
	int maxAbbrevLen;
	long *maskVars;  //(Anjali) //this should store the positions of variables which are
							//to be ignored
};


/*
 * ocRelation - defines a list of variables, and optionally a table which has been
 * constructed based on that relation. A relation can also contain a StateConstraint
 * object, which specifies certain states as being constrained in the relation. If
 * there is no StateConstraint object, then all states are constrained (the normal
 * variable-based modeling case).
 * The variables in a relation are always kept in sorted order.
 */
class ocRelation {
public:
	// initializes an empty relation object. The size argument is a hint as to the 
	// number of variables to allocate space for (but relations can grow dynamically
	// if needed).
	ocRelation(ocVariableList *list = 0, int size = 0,int keysz=0,int stateconstsz =0);
	~ocRelation();
	long size();

	// adds a variable to the relation
	void addVariable(int varindex,int stateind=-5);


	// returns the ocVariableList for this relation
	ocVariableList *getVariableList();

	// returns the list of variable indices. Function return value is the number of
	// variables. maxVarCount is the allocated size of indices.
	int copyVariables(int *indices, int maxCount, int skip = -1);
	int *getVariables();
	long long int getDDFPortion();
	int getIndependentVariables(int *indices, int maxCount);
	int getDependentVariables(int *indices, int maxCount);
	int copyMissingVariables(int *indices, int maxCount);

	// get a single variable from its index
	int getVariable(int index);
	
	// find a variable and return its index
	int findVariable(int varid);
	
	// return number of variables in relation
	int getVariableCount();
	
	// get the size of the orthogonal expansion of the projection
	double getExpansionSize();

	// sets a pointer to the table in the relation object
	void setTable(ocTable *tbl);
	
	// returns a reference to the table for this relation, NULL if none computed yet.
	ocTable *getTable();
	// deletes the projection table to recover storage
        void deleteTable();

	
	// sets/gets the state constraints for the relation
	void setStateConstraints(class ocStateConstraint *constraints);
	ocStateConstraint *getStateConstraints();
	
	// compare two relations; returns 0 if they are equal (have the same set
	// of variables); otherwise returns -1 or 1 based on lexical comparison
	// of the variable lists
	int compare(const ocRelation *other);
	// int compare(const ocRelation *other) {return compare(*other);}
	
	// see if one relation contains another
	bool contains(const ocRelation *other);
	
	// see if all variables are independent
	bool isIndOnly();
	
	// get the NC (cartesian product size)
	long getNC();
	
	// create a mask with 1's in the don't care slots, and zeros elsewhere
	// this can be OR'd with a key to set all the don't care slots to DONT_CARE
	// one form of this function copies the key, the other just returns a pointer
	void makeMask(ocKeySegment *msk);
	ocKeySegment *getMask();
	
	// get the key size; a convenience function for getting in from the variable list
	int getKeySize() { return varList->getKeySize(); }
	
	// sort the variable indices
	void sort();
	static void sort(int *vars, int varcount);
	
	// set, get hash chain linkages
	ocRelation *getHashNext() { return hashNext; }
	void setHashNext(ocRelation *next) { hashNext = next; }
	
	// get the attribute list for the relation
	class ocAttributeList *getAttributeList() { return attributeList; }
	
	// get a printable name for the relation, using the variable abbreviations
	const char *getPrintName();
	
	// get a tuple value from the projection table, which matches the key passed in.
	// the key may contain don't cares but must have actual values for all the variables
	// of this relation (otherwise zero is returned).
	double getMatchingTupleValue(ocKeySegment *key);
	
	// dump data to stdout
	void dump();
	class ocStateConstraint *getStateConstraint(){return stateConstraints;}
	
private:
	void buildMask();		// build the variable mask from the list of variables

	ocVariableList *varList;	// variable list associated with this relation
	int *vars;		// array of variable indices
	int *states;		//ARRAY OF STATES associated with each
			// variable in the rel,DONT_CARE if no state specified 
	int varCount;	// number of vars in relation
	int maxVarCount;	// size of vars array
	class ocTable *table;
	class ocStateConstraint *stateConstraints;		// state constraints
	ocRelation *hashNext;	// linkage for storing relations in a hash table
	ocKeySegment *mask;		// mask has zero for variables in this rel, 1's elsewhere
	class ocAttributeList *attributeList;
	char *printName;
};


/**
 * ocModel - defines a model as a list of Relations.
*/

class ocModel {
public:
	// initialize model, with space for the given number of relations
	ocModel(int size = 4);
	~ocModel();
	long size();

	// get/set relations
	void addRelation(ocRelation *relation, bool normalize=true);
	int getRelations(ocRelation **rels, int maxRelations);
	ocRelation *getRelation(int index);
	bool containsRelation(ocRelation *relation);
	int getRelationCount();
	ocTable *getFitTable();
	void setFitTable(ocTable *tbl);
	void deleteFitTable();
	void deleteRelationLinks();
	
	// copy relation references (but not the objects)
	void copyRelations(ocModel &model, int skip1 = -1, int skip2 = -1);

	// get the attribute list for the model
	class ocAttributeList *getAttributeList() { return attributeList; }

	// get a printable name for the relation, using the variable abbreviations
	const char *getPrintName();
	
	// set, get hash chain linkages
	ocModel *getHashNext() { return hashNext; }
	void setHashNext(ocModel *next) { hashNext = next; }
	
	// print out model info
	void dump();
	
	//state based models need to make structure matrix for Df calculation
        void makeStructMatrix(int statespace,ocVariableList * vars,int **State_sp_Arr);	
	int * get_indicesfromKey(ocKeySegment *key, ocVariableList *vars, int statespace,int **State_Sp_Arr, int *counter);

	void printStructMatrix();
	int **get_structMatrix(int *statespace,int* Total_const){
		*statespace=State_Space_sz;
		*Total_const=Total_constraints;
		return structMatrix;};
private:
	ocRelation **relations;
	int relationCount;
	int maxRelationCount;
	class ocTable *fitTable;
	class ocAttributeList *attributeList;
	ocModel *hashNext;
	char *printName;
	int **structMatrix;
	int Total_constraints;
	int State_Space_sz;
};


/**
 * ocAttributeList - assciated with models and relations, an attribute carries a name
 * and a numeric value.
*/
class ocAttributeList {
public:
	// initialize empty attribute list
	ocAttributeList(int size);
	~ocAttributeList();
	long size();
	void reset();

	// add an attribute. Names are not copied so the name argument must point to a
	// permanent string. If an attribute by this name already exists, it is replaced.
	void setAttribute(const char *name, double value);
	double getAttribute(const char *name);
	int getAttributeIndex(const char *name);
	int getAttributeCount();
	double getAttributeByIndex(int index);
	
	// print out values
	void dump();
	
private:
	const char** names;
	double *values;
	int attrCount;
	int maxAttrCount;
};

#define ATTRIBUTE_H "h"
#define ATTRIBUTE_T "t"
#define ATTRIBUTE_DF "df"
#define ATTRIBUTE_DDF "ddf"
#define ATTRIBUTE_DDF_IND "ddf_bot"
#define ATTRIBUTE_FIT_H "fit_h"
#define ATTRIBUTE_ALG_H "alg_h"
#define ATTRIBUTE_FIT_T "fit_t"
#define ATTRIBUTE_ALG_T "alg_t"
#define ATTRIBUTE_LOOPS "loops"
#define ATTRIBUTE_EXPLAINED_I "information"

//***********************************************************************
                                                // Junghan
#define ATTRIBUTE_AIC "aic"                     // new
#define ATTRIBUTE_BIC "bic"                     // new
#define ATTRIBUTE_BP_AIC "bp_aic"               // new
#define ATTRIBUTE_BP_BIC "bp_bic"               // new
//***********************************************************************

#define ATTRIBUTE_UNEXPLAINED_I "unexplained"
#define ATTRIBUTE_T_FROM_H "t_h"
#define ATTRIBUTE_IPF_ITERATIONS "ipf_iterations"
#define ATTRIBUTE_IPF_ERROR "ipf_error"
#define ATTRIBUTE_PROCESSED "processed"
#define ATTRIBUTE_IND_H "h_ind_vars"
#define ATTRIBUTE_DEP_H "h_dep_vars"
#define ATTRIBUTE_COND_H "cond_h"
#define ATTRIBUTE_COND_DH "cond_dh"
#define ATTRIBUTE_COND_PCT_DH "cond_pct_dh"
#define ATTRIBUTE_COND_DF "cond_df"
#define ATTRIBUTE_COND_DDF "cond_ddf"
#define ATTRIBUTE_TOTAL_LR "total_lr"
#define ATTRIBUTE_IND_LR "ind_lr"
#define ATTRIBUTE_COND_LR "cond_lr"
#define ATTRIBUTE_COND_H_PROB "cond_h_prob"
#define ATTRIBUTE_P2 "p2"
#define ATTRIBUTE_P2_IND "p2_bot"
#define ATTRIBUTE_P2_ALPHA_IND "p2_alpha_bot"
#define ATTRIBUTE_P2_BETA_IND "p2_beta_bot"
#define ATTRIBUTE_P2_ALPHA_SAT "p2_alpha_top"
#define ATTRIBUTE_P2_BETA_SAT "p2_beta_top"
#define ATTRIBUTE_P2_ALPHA "p2_alpha"
#define ATTRIBUTE_P2_BETA "p2_beta"
#define ATTRIBUTE_LR "lr"
#define ATTRIBUTE_LR_IND "lr_bot"
#define ATTRIBUTE_ALPHA_IND "alpha_bot"
#define ATTRIBUTE_BETA_IND "beta_bot"
#define ATTRIBUTE_ALPHA_SAT "alpha_top"
#define ATTRIBUTE_BETA_SAT "beta_top"
#define ATTRIBUTE_ALPHA "alpha"
#define ATTRIBUTE_BETA "beta"
#define ATTRIBUTE_MAX_REL_WIDTH "max_rel_width"
#define ATTRIBUTE_MIN_REL_WIDTH "min_rel_width"
#define ATTRIBUTE_BP_T "bp_t"
#define ATTRIBUTE_BP_H "bp_h"
#define ATTRIBUTE_BP_LR "bp_lr"
#define ATTRIBUTE_BP_ALPHA "bp_alpha"
#define ATTRIBUTE_BP_BETA "bp_beta"
#define ATTRIBUTE_BP_EXPLAINED_I "bp_information"
#define ATTRIBUTE_BP_UNEXPLAINED_I "bp_unexplained"
#define ATTRIBUTE_BP_COND_H "bp_cond_h"
#define ATTRIBUTE_BP_COND_DH "bp_cond_dh"
#define ATTRIBUTE_BP_COND_PCT_DH "bp_cond_pct_dh"
#define ATTRIBUTE_PCT_CORRECT_DATA "pct_correct_data"
#define ATTRIBUTE_PCT_CORRECT_TEST "pct_correct_test"

/**
 * ocStateConstraint - defines the set of states (variable combinations) within a relation
 * whose values are fixed.
 */
class ocStateConstraint {
public:
	// initialize a set of constraints.  Size is a hint of the number needed
	ocStateConstraint(int keysize, int size);
	~ocStateConstraint();
	
	// add a constraint. 
	void addConstraint(ocKeySegment *key);
	
	// get the number of constraints in the list
	long getConstraintCount();
	
	// retrieve a constraint, given the index (0 .. constraintCount-1)
	ocKeySegment *getConstraint(int index);
	
	// get the key size for this constraint table
	int getKeySize();

private:
	ocKeySegment *constraints;
	long constraintCount;
	long maxConstraintCount;
	int keysize;
};

	
#endif

