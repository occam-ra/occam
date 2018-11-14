/*
 * Copyright © 1990 The Portland State University OCCAM Project Team
 * [This program is licensed under the GPL version 3 or later.]
 * Please see the file LICENSE in the source
 * distribution of this software for license terms.
 */

#ifndef ___Math
#define ___Math

#include <float.h>
#include "VBMManager.h"

/**
 * The functions below are common mathematical operations, where the input
 * data is taken from Core data structures (typically tables)
 */

/**
 * Compute entropy of a single table. This is the sum over all entries i in
 * the table of -pi * log2(pi).
 */
double ocEntropy(Table *p);

/**
 * Compute transmission between two tables. This function requires that the
 * tables be over the same set of variables. This is the sum over all entries
 * i in both tables of pi (log2(pi) / log2(qi)), where the p's come from
 * the first table and the q's from the second. Note that the term is considered
 * zero if either pi or qi are zero.
 */
double ocTransmission(Table *p, Table *q);

double ocInfoDist(Table* p1, Table* q1, Table* q2);
double ocAbsDist(Table* p, Table* q);
double ocTransmissionFlat(Table* p, Table* q);
double ocEucDist(Table* p, Table* q);
double ocHellingerDist(Table* p, Table* q);
double ocMaxDist(Table* p, Table* q);

/**
 * Compute Pearson chisquare measure, 2*nsum((p-q)^2/q). The P table is assumed
 * to be the input data.
 */
double ocPearsonChiSquared(Table *p, Table *q, long sampleSize);
double ocPearsonChiSquaredFlat(int card, double* p, double* q, long sampleSize);
/**
 * Determine whether the relations in a model have overlaps
 */
bool ocHasOverlaps(Model *model);


/**
 * Determine if a model has loops among its relations
 */
bool ocHasLoops(Model *model);

/**
 * Compute the degrees of freedom of a relation.  This takes into account
 * the cardinality of the variables in the relation, but is independent
 * of the data. The df is the total number of cells (i.e., the product of
 * the variable cardinalities) minus 1.
 */
double ocDegreesOfFreedom(Relation *rel);

double ocDegreesOfFreedomStateBased(Model *model);

/**
 * to compute DF for the input data
 */
double ocDegreesOfFreedom(VariableList *varList);

/**
 * for the case where we have a variable list rather than a relation
 */
double ocDegreesOfFreedom(VariableList *varList, int *variables, int varCount);

/**
 * LR - conversion from H and DF, given sample size
 */
double ocLR(double sample, double df, double h);

/**
 * functions from Occam2
 */
double chic (double x2, double df);
double chin2 (double x, double df, double theta, int *ifault);
double csa (double x, double df);
//static double ppnorm (double prob, int *ifault);
double gammds (double y, double p, int *ifault);
double ppchi (double p, double df, int *ifault);
double anorm (double x, int upper);
unsigned chistat (unsigned ntab, double* obs, double* fit, double* g2_ptr, double* p2_ptr);


#endif
