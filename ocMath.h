/* Copyright 2000, Portland State University Systems Science Program.  All Rights Reserved
 */
#ifndef OCMATH_H
#define OCMATH_H

#include <float.h>
#include "ocCore.h"

/**
 * The functions below are common mathematical operations, where the input
 * data is taken from ocCore data structures (typically tables)
 */

/**
 * Compute entropy of a single table. This is the sum over all entries i in
 * the table of -pi * log2(pi).
 */
double ocEntropy(ocTable *p);

/**
 * Compute transmission between two tables. This function requires that the
 * tables be over the same set of variables. This is the sum over all entries
 * i in both tables of pi (log2(pi) / log2(qi)), where the p's come from
 * the first table and the q's from the second. Note that the term is considered
 * zero if either pi or qi are zero.
 */
double ocTransmission(ocTable *p, ocTable *q);

/**
 * Compute Pearson chisquare measure, 2*nsum((p-q)^2/q). The P table is assumed
 * to be the input data.
 */
double ocPearsonChiSquared(ocTable *p, ocTable *q, long sampleSize);

/**
 * Determine whether the relations in a model have overlaps
 */
bool ocHasOverlaps(ocModel *model);


/**
 * Determine if a model has loops among its relations
 */
bool ocHasLoops(ocModel *model);

/**
 * Compute the degrees of freedom of a relation.  This takes into account
 * the cardinality of the variables in the relation, but is independent
 * of the data. The df is the total number of cells (i.e., the product of
 * the variable cardinalities) minus 1.
 */
double ocDegreesOfFreedom(ocRelation *rel);

double ocDegreesOfFreedomStateBased(ocModel *model);

/**
 * to compute DF for the input data
 */
double ocDegreesOfFreedom(ocVariableList *varList);

/**
 * for the case where we have a variable list rather than a relation
 */
double ocDegreesOfFreedom(ocVariableList *varList, int *variables, int varCount);

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
