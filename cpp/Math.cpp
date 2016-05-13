#include <math.h>

#include "Math.h"
#include "Model.h"
#include "Relation.h"
#include "_Core.h"

#include <stdio.h>
#include <string.h>
#include <float.h>

//-- very small probabilities are considered zero, to avoid underflow
//-- errors from log functions.
const double PROB_MIN = 1e-36;

double ocEntropy(Table *p) {
    double h = 0.0;
    long long count = p->getTupleCount();
    double pv;
    for (long long i = 0; i < count; ++i) {
        pv = p->getValue(i);
        if (pv > PROB_MIN)
            h -= pv * log(pv);
    }
    h /= log(2.0); // convert h to log2 rather than ln
    return h;
}

double ocTransmission(Table *p, Table *q) {
    // To prevent underflow errors, probabilities
    // less than PROB_MIN are considered zero.
    double h = 0.0;
    long long count = p->getTupleCount();
    for (long long i = 0; i < count; i++) {
        double pv = p->getValue(i);
        KeySegment *pv_key = p->getKey(i);
        long long qi_index = q->indexOf(pv_key); // find matching entry in q
        double qi = qi_index >= 0 ? q->getValue(qi_index) : 0.0;
        if (qi > PROB_MIN && pv > PROB_MIN)
            h += pv * log(pv / qi);
    }
    h /= log(2.0); // convert h to log2 rather than ln
    return h;
}

double ocTransmissionFlat(Table* p, Table* q) {
/*
    double h = 0.0;
    long long count = unifySize(p, q);
    for (long long i = 0; i < count; i++) {
        double pv = p[i];
        double qv = q[i];
        double a = (qv > PROB_MIN && pv > PROB_MIN)
                 ? (pv * log(pv / qv)) : 0;
        h += a;
    }
    return h / log(2.0);
*/
}

double ocAbsDist(Table* p, Table* q) {
/*
    long long size = unifySize(p, q);


    double h = 0.0;
    for (long long i = 0; i < size; i++) { h += fabs(p[i] - q[i]); }

    return h;
*/
}

double ocEucDist(Table* p, Table* q) {
/*
    long long count = unifySize(p, q);
    double h = 0.0;
    for (long long i = 0; i < count; i++) {
        double pv = p[i];
        double qv = q[i];
        h += (pv - qv) * (pv - qv);
    }
    return sqrt(h);
*/
}

double ocHellingerDist(Table* p, Table* q) {
/*
    long long count = unifySize(p, q);
    double h = 0.0;
    for (long long i = 0; i < count; i++) {
        double pv = p[i];
        double qv = q[i];
        h += sqrt(pv * qv);
    }
    return sqrt(1-h);
*/
}

double ocMaxDist(Table* p, Table* q) {
/*
    double h = 0.0;
    long long count = unifySize(p, q);
    for (long long i = 0; i < count; i++) {
        double pv = p[i];
        double qv = q[i];
        double t = fabs(pv - qv);
        if (t > h) h = t;
    }
    return h;
*/
}

double ocInfoDist(Table* p1, Table* q1, Table* q2) {
/*
    double h = 0.0;
    auto count = unifySize(q1, q2);
    count = unifySize(p1, q1);
    // For each state in `p1`:
    for (auto i = 0; i < count; ++i) {
        auto p1v = p1[i];
        auto q1v = q1[i];
        auto q2v = q2[i];
        if (p1v > PROB_MIN && q1v > PROB_MIN && q2v > PROB_MIN) {
            h += p1v * log(q1v / q2v);
        }
    }
    return h / log(2.0);
*/
}


// TODO: Rewrite this to use a "iteratorWithFlat" function;
// currently it unnecessarily flattens the input before comparing to the margin,
// where it would be nicer to just iterate over states in the input and margin.
double ocPearsonChiSquaredFlat(int card, double* p, double* q, long sampleSize) {

    double p2 = 0.0;
    for (unsigned i = 0; i < card; ++i) {

        double pi = p[i];
        double qi = q[i];
        if (pi < PROB_MIN) {
            p2 += qi; // works even if q1 near zero
        } else if (qi > PROB_MIN) {
            p2 += (pi - qi) * (pi - qi) / qi;
        }
    }
    p2 *= sampleSize;
    //if (isnan(p2)) return 1;
    return csa(p2, card - 1);
}


double ocPearsonChiSquared(Table *p, Table *q, long sampleSize) {
    // To prevent underflow errors, probabilities
    // less than PROB_MIN are considered zero.
    double p2 = 0.0;
    long count = p->getTupleCount();
    for (long i = 0; i < count; i++) {
        double pi = p->getValue(i);
        KeySegment *pi_key = p->getKey(i);
        long qi_index = q->indexOf(pi_key); // find matching entry in q
        double qi = qi_index >= 0 ? q->getValue(qi_index) : 0.0;
        if (pi < PROB_MIN)
            p2 += qi; // works even if q1 near zero
        else if (qi > PROB_MIN)
            p2 += (pi - qi) * (pi - qi) / qi;
    }
    p2 *= sampleSize;
    return p2;
}


double ocDegreesOfFreedom(Relation *rel) {
    double df = 1.0;
    int count = rel->getVariableCount();
    VariableList *vars = rel->getVariableList();
    for (int i = 0; i < count; i++) {
        int varIndex = rel->getVariable(i);
        df *= vars->getVariable(varIndex)->cardinality;
    }
    return df - 1;
}

double ocDegreesOfFreedom(VariableList *varList) {
    double df = 1.0;
    int count = varList->getVarCount();
    for (int i = 0; i < count; i++) {
        df *= varList->getVariable(i)->cardinality;
    }
    return df - 1;
}

//-- for use when we have the variable index array
double ocDegreesOfFreedom(VariableList *varList, int *variables, int varCount) {
    double df = 1;
    for (int i = 0; i < varCount; i++) {
        int varIndex = variables[i];
        df *= varList->getVariable(varIndex)->cardinality;
    }
    return df - 1;
}

bool ocHasOverlaps(Model *model) {
    // check for overlaps. This is done via pairwise comparison
    // of the variable masks for the relations.
    int count = model->getRelationCount();
    // get the key size, from the variable list (just use the first relation)
    int keysize = model->getRelation(0)->getVariableList()->getKeySize();
    for (int i = 0; i < count; i++) {
        for (int j = i + 1; j < count; j++) {
            KeySegment *ki = model->getRelation(i)->getMask();
            KeySegment *kj = model->getRelation(j)->getMask();
            for (int k = 0; k < keysize; k++) {
                if ((ki[k] & kj[k]) != 0)
                    return true; // same variable in both
            }
        }
    }
    return false;
}

//-- these definitions are used in loop checking
struct VarList {
        int varCount;
        int *vars;
        VarList() :
                varCount(0), vars(0) {
        }
        ~VarList() {
            if (vars)
                delete[] vars;
        }
        void setVars(int *newVars) {
            if (vars)
                delete[] vars;
            vars = newVars;
        }
};

//-- copy a VarList
static void VLCopy(VarList &from, VarList &to) {
    if (to.varCount < from.varCount) {
        to.setVars(new int[from.varCount]);
    }
    to.varCount = from.varCount;
    if (to.varCount > 0)
        memcpy(to.vars, from.vars, to.varCount * sizeof(int));
}

//-- remove variables from v1 which are present in v2
static void VLComplement(VarList &v1, VarList &v2) {
    if (v1.varCount == 0 || v1.varCount == 0)
        return;
    int *newvars = new int[v1.varCount];
    int count = 0, i, j;
    for (i = 0; i < v1.varCount; i++) {
        for (j = 0; j < v2.varCount; j++) {
            if (v2.vars[j] == v1.vars[i])
                break;
        }
        if (j >= v2.varCount) { // not found; add it to result
            newvars[count++] = v1.vars[i];
        }
    }
    v1.setVars(newvars);
    v1.varCount = count;
}

//-- check for containment (v1 contains v2)
static bool VLContains(VarList &v1, VarList &v2) {
    if (v1.varCount < v2.varCount)
        return false; // quick check for impossibility
    return ocContainsVariables(v1.varCount, v1.vars, v2.varCount, v2.vars);
}

// returns true if first boolean array is a superset of (or equal to) second
bool isSuperset(bool *first, bool *second, int length) {
    for (int i = 0; i < length; i++)
        if (second[i] && !first[i])
            return false;
    return true;
}

bool ocSbHasLoops(Model *model) {
    if (model == NULL) {
        fprintf(stdout, "ocSbHasLoops(): Error. Model is NULL.\n");
        fflush(stdout);
        exit(1);
    }
    int rel_count = model->getRelationCount();
//    if (rel_count > 3) return false;
    VariableList *var_list;
    if (rel_count > 0) {
        var_list = model->getRelation(0)->getVariableList();
    } else {
        fprintf(stdout, "ocSbHasLoops(): Error. Model has no relations.\n");
        fflush(stdout);
        exit(1);
    }
    int i, j, k;
    int var_count = var_list->getVarCount();
    int *card_array = new int[var_count];
    int *card_offsets = new int[var_count];
    int total_card = 0;
    // Make a list of all variable cardinalities, and also the total cardinality.
    // Also we make an offset list, to make it easier to reference where variables
    // will start in the boolean arrays below.
    for (i = 0; i < var_count; i++) {
        card_array[i] = var_list->getVariable(i)->cardinality;
        if (i == 0) {
            card_offsets[i] = 0;
        } else {
            card_offsets[i] = card_array[i - 1] + card_offsets[i - 1];
        }
        total_card += card_array[i];
    }
    // Make a boolean array of rel_count * total_card, to hold flags of which var states
    // are in which relations.
    bool **state_flags = new bool *[rel_count];
    //StateConstraint *constraints;
    int *var_indices, *state_indices;
    for (i = 0; i < rel_count; i++) {
        state_flags[i] = new bool[total_card];
        memset(state_flags[i], 0, total_card * sizeof(bool));
        // Now we populate the array from the relation's constraints.
        var_indices = model->getRelation(i)->getVariables();
        state_indices = model->getRelation(i)->getStateIndices();
        for (j = 0; j < model->getRelation(i)->getVariableCount(); j++) {
            if (state_indices[j] != DONT_CARE) {
                state_flags[i][state_indices[j] + card_offsets[var_indices[j]]] = true;
            } else {
                for (k = 0; k < card_array[var_indices[j]]; k++) {
                    state_flags[i][k + card_offsets[var_indices[j]]] = true;
                }
            }
        }
    }
    // We now have a set of boolean arrays that represent which states are present or not.
    // We can proceed with the standard loop-finding algorithm now, where we drop variables (states)
    // that are unique to one relation, and then drop any relations that are subsets of other
    // relations, continuing until we can't make a change. When done, if anything remains, there
    // was a loop.
    delete[] card_offsets;
    delete[] card_array;
    bool changed = true;
    int count, found_at;
    bool *cleared = new bool[rel_count];
    int clear_count = 0;
    memset(cleared, 0, rel_count * sizeof(bool));
    while (changed) {
        changed = false;
        // check for var states that only exist in one key (key masked by var) (and eliminate)
        for (i = 0; i < total_card; i++) {
            count = 0;
            for (j = 0; j < rel_count; j++) {
                if (state_flags[j][i]) {
                    count++;
                    if (count > 1)
                        break;
                    found_at = j;
                }
            }
            if (count == 1) {
                state_flags[found_at][i] = false;
                changed = true;
            }
        }
        // check for var combos that are subsets of another (and eliminate)
        for (i = 0; i < rel_count; i++) {
            if (cleared[i])
                continue;
            for (j = i + 1; j < rel_count; j++) {
                if (cleared[j])
                    continue;
                if (isSuperset(state_flags[i], state_flags[j], total_card)) {
                    // clear subset row j
                    for (k = 0; k < total_card; k++)
                        state_flags[j][k] = false;
                    changed = true;
                    cleared[j] = true;
                    clear_count++;
                } else if (isSuperset(state_flags[j], state_flags[i], total_card)) {
                    // clear subset row i
                    for (k = 0; k < total_card; k++)
                        state_flags[i][k] = false;
                    changed = true;
                    cleared[i] = true;
                    clear_count++;
                }
            }
        }
        // If we ever know that we've cleared all rows, there is no loop and we can return false immediately.
        if (clear_count == rel_count) {
            for (int d = 0; d < rel_count; d++) {
                delete[] state_flags[d];
            }
            delete[] state_flags;
            delete[] cleared;
            return false;
        }
    }
    // Once all changes are complete, check if anything is left.  If so, there is a loop.
    for (i = 0; i < rel_count; i++) {
        if (cleared[i])
            continue;
        for (j = 0; j < total_card; j++)
            if (state_flags[i][j]) {
                for (int d = 0; d < rel_count; d++) {
                    delete[] state_flags[d];
                }
                delete[] state_flags;
                delete[] cleared;
                return true;
            }
    }
    for (int d = 0; d < rel_count; d++) {
        delete[] state_flags[d];
    }
    delete[] state_flags;
    delete[] cleared;
    return false;
}

bool ocHasLoops(Model *model) {
    if (model == NULL) {
        fprintf(stdout, "ocHasLoops(): Error. Model is NULL.\n");
        fflush(stdout);
        exit(1);
    }
    if (model->isStateBased())
        return ocSbHasLoops(model);
    int i, j, relcount;
    relcount = model->getRelationCount();
    VarList *rels = new VarList[relcount];
    //-- copy variable lists from relations
    for (i = 0; i < relcount; i++) {
        Relation *relation = model->getRelation(i);
        rels[i].varCount = relation->getVariableCount();
        rels[i].setVars(new int[rels[i].varCount]);
        relation->copyVariables(rels[i].vars, rels[i].varCount);
    }

    for (;;) {
        bool change = false;
        //-- repeat until no further change:
        //-- first eliminate variables occuring in only one relation.
        //-- then eliminate relations which are subsets of others
        for (i = 0; i < relcount; i++) {
            VarList newList;
            VLCopy(rels[i], newList);
            for (j = 0; j < relcount; j++) {
                if (j != i)
                    VLComplement(newList, rels[j]);
            }
            if (newList.varCount > 0) {
                VLComplement(rels[i], newList);
                change = true;
            }
        }
        for (i = 0; i < relcount; i++) {
            for (j = 0; j < relcount; j++) {
                if (i != j && rels[i].varCount > 0 && rels[j].varCount > 0 && VLContains(rels[i], rels[j])) {
                    change = true;
                    rels[j].varCount = 0;
                }
            }
        }
        if (!change)
            break;
    }

    //-- do cleanup, and also see if there are any relations left.
    int remaining = 0;
    for (i = 0; i < relcount; i++) {
        if (rels[i].varCount > 0)
            remaining++;
    }
    delete[] rels;
    return remaining > 1;
}

double ocLR(double sample, double df, double h) {
    return 2.0 * M_LN2 * sample * (log(df) / M_LN2 - h);
}

//-- log-gamma function, since Windows doesn't have one
//-- obtained from http://astronomy.swin.edu.au/pbourke/analysis/gammafcn

double LnGamma(double xx) {
    int j;
    double x, y, tmp, ser;
    double cof[6] = { 76.18009172947146, -86.50532032941677, 24.01409824083091, -1.231739572450155,
            0.1208650973866179e-2, -0.5395239384953e-5 };

    y = x = xx;
    tmp = x + 5.5 - (x + 0.5) * log(x + 5.5);
    ser = 1.000000000190015;
    for (j = 0; j <= 5; j++)
        ser += (cof[j] / ++y);
    return (log(2.5066282746310005 * ser / x) - tmp);
}

//-- Math functions from occam2

#ifdef __CYGWIN32__
int signgam;
#endif

/*
 Upper-tail ALPHA probabilities of the central
 chi-squared distribution for critical value X2
 and DF degrees of freedom. Both arguments are
 input of type real.  If either argument is
 invalid CHIC is returned with the self-
 flagging nonsense value of -1. CHIC calls
 real function GAMMLN which returns the
 natural logarithm of the gamma function.
 */

#define CHIC_ITMAX 300
#define CHIC_EPS 3.E-7

double chic(double x2, double df) {
    double a0, a1, an, ana, anf, ap, b0, b1, d, del, fac, g, gold, sum, x;
    int n;

    /* Screen arguments */

    if (x2 == 0.0)
        /* There is nothing to do. */
        return 1.0;
    else if (x2 < 0.0 || df < 0.0)
        /*
         Nonsense!  Note:  DF should be strictly
         positive, but non-negativity is accepted
         for standard handling of the saturated model.
         */
        return -1.0;
    else if (x2 > 100 && (x2 / df) > 5.0)
        /* Excessive arguments likely to cause underflow */
        return 0.0;

    /* Arguments OK */
    x = 0.5 * x2;
    d = 0.5 * df;

    /*
     Determine approximation method
     based on relation of X2 and DF
     */

    if (x < d + 1.0) {
        /* Use a series representation */
        ap = d;
        sum = 1.0 / d;
        del = sum;
        for (n = 0; n < CHIC_ITMAX; n++) {
            ap += 1.0;
            del *= x / ap;
            sum += del;
            if (fabs(del) < fabs(sum) * CHIC_EPS)
                return 1.0 - sum * exp(-x + d * log(x) - LnGamma(d));
        }
    } else {
        /* Use a continued fraction */
        gold = 0.0;
        a0 = 1.0;
        a1 = x;
        b0 = 0.0;
        b1 = 1.0;
        fac = 1.0;
        for (n = 1; n <= CHIC_ITMAX; n++) {
            an = (double) n;
            ana = an - d;
            a0 = (a1 + a0 * ana) * fac;
            b0 = (b1 + b0 * ana) * fac;
            anf = an * fac;
            a1 = x * a0 + anf * a1;
            b1 = x * b0 + anf * b1;
            if (a1 != 0.0) {
                fac = 1.0 / a1;
                g = b1 * fac;
                if (fabs((g - gold) / g) < CHIC_EPS)
                    return exp(-x + d * log(x) - LnGamma(d)) * g;
                gold = g;
            }
        }
    }
    return 0; // should never get here
}

/* Computes the lower-tail area of the chi-squared
 distribution function with positive real degrees of
 freedom f and noncentrality parameter theta.  If
 theta=0 chin2 returns the central chi-squared value. */

#define ZERO 0.0
#define ONE 1.0
#define TWO 2.0
#define THIRD .3333333
#define NINE 9.0
#define PREC 37.3
#define CHIN2_EPS 1.0E-6
#define CHIN2_ITMAX 200
#define A -1.5976
#define B 0.04417
#define FALSE 0
#define TRUE 1

double chin2(double x, double df, double theta, int *ifault) {
    int flag;
    int n;
    double ret;

    double c1, c2, lam, u, v, x2, f2, t, term, bound, tst, z, arg;
    ret = x;

    *ifault = 2;
    if (df < 0.0 || theta < ZERO)
        return ret;

    *ifault = 3;
    if (x < ZERO)
        return ret;

    *ifault = 0;
    if (x == ZERO)
        return ret;

    ret = ONE;

    if (df == 0.0)
        return ret;

    n = 1;
    x2 = x / TWO;
    f2 = df / TWO;
    lam = theta / TWO;

    tst = f2 * log(x2) - x2 - LnGamma(f2 + ONE);

    if ((tst - lam) < -PREC) {
        /* Use the Aickin central X2 approximation to
         the non-central X2, and the Wilson-Hilferty
         transformation for the central X2 approximation.
         Aickin */

        c1 = df + theta;
        c2 = df + TWO * theta;
        x2 = x * c2 / c1;
        v = (c1 * c1) / c2;
        /* Wilson-Hilferty */
        c1 = pow(x2 / v, THIRD);
        c2 = TWO / (NINE * v);
        z = (c1 - ONE + c2) / sqrt(c2);
        arg = A * z * (ONE + B * z * z);
        if (arg < -PREC)
            ret = ONE;
        else if (arg > PREC)
            ret = ZERO;
        else
            ret = ONE / (ONE + exp(arg));
        return ret;
    } else {
        u = exp(-lam);
        t = exp(tst);
    }
    v = u;
    term = v * t;
    ret = term;

    flag = FALSE;
    while (1) {
        if ((df + TWO * (double) n - x) <= ZERO)
            goto thirty;
        flag = TRUE;

        twenty: bound = t * x / (df + TWO * (double) n - x);
        if (bound > CHIN2_EPS && n <= CHIN2_ITMAX)
            goto thirty;
        if (bound > CHIN2_EPS) {
            *ifault = 1;
            return ret;
        }
        return ret;

        thirty: u = u * lam / (double) n;
        v += u;
        t = t * x / (df + TWO * (double) n);
        term = v * t;
        ret += term;
        n++;
        if (flag)
            goto twenty;
    }
    return 0;
}

/*
 A quick approximation to upper-tail probabilities of
 the central chi-squared distribution for IDF degrees
 of freedom and critical value X.  Accurate to the
 second decimal place over the ranges of IDF and X,
 and accurate to the third decimal place almost every-
 where. If either argument is negative CSA is returned
 with the self-flagging nonsense value of -1.

 UFLO and OFLO are far from actual under- and overflow
 limits; nonetheless these values preserve four-digit
 accuracy, which exceeds the suggested reporting precision.
 */
#define UFLO -12.0
#define OFLO 12.0
#define A -1.5976
#define B 0.04417

double csa(double x, double df) {
    if (x == 0.0 || df == 0.0) {
        /* There is nothing to do.  Zero degrees of freedom
         are allowed to accommodate the saturated model. */
        return 1.0;
    } else if (x < 0.0 || df < 0.0) {
        /* Nonsense!  Note IDF=0 is also nonsense, but we
         allow it here to accommodate the saturated model */
        return -1.0;
    }

    if (df == 1.0) {
        double arg = A * sqrt(x) * (1.0 + B * x);

        if (arg <= UFLO)
            return 0.0;
        else
            return 2.0 - 2.0 / (1.0 + exp(arg));
    } else if (df == 2.0) {
        if (x >= (2.0 * OFLO))
            return 0.0;
        else
            return exp(-x / 2.0);
    } else if (df > 2.0) {
        double v = df;
        double c1 = pow(x / v, 0.333333333);
        double c2 = 2.0 / (9.0 * v);
        double z = (c1 - 1.0 + c2) / sqrt(c2);
        double arg = A * z * (1.0 + B * (z * z));

        if (arg <= UFLO)
            return 0.0;
        else if (arg >= OFLO)
            return 1.0;
        else {
            double ret = 1.0 - 1.0 / (1.0 + exp(arg));

            if (ret <= 0.0001)
                return 0.0;
            return ret;
        }
    }
    return 0.0; // should never get here
}

#define ZERO 0.0
#define HALF 0.5
#define ONE 1.0

#define NSPLIT 0.42
#define NA0 2.50662823884
#define NA1 -18.61500062529
#define NA2 41.39119773534
#define NA3 -25.44106049637
#define NB1 -8.47351093090
#define NB2 23.08336743743
#define NB3 -21.06224101826
#define NB4 3.13082909833
#define NC0 -2.78718931138
#define NC1 -2.29796479134
#define NC2 4.85014127135
#define NC3 2.32121276858
#define ND1 3.54388924762
#define ND2 1.63706781897

static double ppnorm(double prob, int *ifault) {
    /*
     Returns the value of X=PPNORM where

     tX
     u-l  N(t)zdt  = PROB

     and N(t) is the standarized normal pdf */

    double ppnorm;
    double p, q, r;

    *ifault = 0;
    p = prob;
    q = p - HALF;
    if (fabs(q) > NSPLIT) {
        r = p;
        if (q > ZERO)
            r = ONE - p;
        if (r > ZERO) {
            r = sqrt(-log(r));
            ppnorm = (((NC3 * r + NC2) * r + NC1) * r + NC0) / ((ND2 * r + ND1) * r + ONE);
            if (q < ZERO)
                ppnorm = -ppnorm;
        } else {
            *ifault = 1;
            ppnorm = 0.0;
        }
    } else {
        r = q * q;
        ppnorm = q * (((NA3 * r + NA2) * r + NA1) * r + NA0) / ((((NB4 * r + NB3) * r + NB2) * r + NB1) * r + ONE);
    }
    return ppnorm;
}

#define E 1.e-06

double gammds(double y, double p, int *ifault) {
    double gammds, f, a, c;

    /* Check admissibility of arguments and value of F. */

    *ifault = 1;
    gammds = ZERO;

    if (y <= ZERO || p <= ZERO)
        return gammds;

    *ifault = 2;

    f = exp(p * log(y) - LnGamma(p + ONE) - y);
    if (f == ZERO)
        return gammds;

    *ifault = 0;

    /* Series begins */

    c = ONE;
    gammds = ONE;
    a = p;

    one: a += ONE;
    c *= y / a;
    gammds += c;
    if (c / gammds > E)
        goto one;
    gammds *= f;

    return gammds;
}

#define PPCHI_EPS 0.5E-06
#define PMIN 0.000002
#define PMAX 0.999998

#define TWO 2.0
#define THREE 3.0
#define SIX 6.0

#define C1 .01
#define C2 .222222
#define C3 .32
#define C4 .40
#define C5 1.24
#define C6 2.2
#define C7 4.67
#define C8 6.66
#define C9 6.73
#define C10 13.32
#define C11 60.0
#define C12 70.0
#define C13 84.0
#define C14 105.0
#define C15 120.0
#define C16 127.0
#define C17 140.0
#define C18 175.0
#define C19 210.0
#define C20 252.0
#define C21 264.0
#define C22 294.0
#define C23 346.0
#define C24 420.0
#define C25 462.0
#define C26 606.0
#define C27 672.0
#define C28 707.0
#define C29 735.0
#define C30 889.0
#define C31 932.0
#define C32 966.0
#define C33 1141.0
#define C34 1182.0
#define C35 1278.0
#define C36 1740.0
#define C37 2520.0
#define C38 5040.0

double ppchi(double p, double df, int *ifault) {
    int if1, kount;
    double a, b, c, g, p1, p2, q, s1, s2, s3, s4, s5, s6, t, x, xx;
    double v = df;
    double ch;
    double ppchi;

    ppchi = -ONE;
    *ifault = 1;
    if (p < PMIN || p > PMAX)
        return ppchi;
    *ifault = 2;
    if (v <= ZERO)
        return ppchi;
    *ifault = 0;
    xx = HALF * v;
    c = xx - ONE;
    g = LnGamma(xx);

    /* Starting approximation for small chi-squared. */

    if (v >= -C5 * log(p))
        goto one;
    ch = pow(p * xx * exp(g + xx * M_LN2), (ONE / xx));
    if (ch < PPCHI_EPS)
        goto six;
    goto four;

    /* Starting approximation for V s 0.32 */
    one: if (v > C3)
        goto three;
    ch = C4;
    a = log(ONE - p);
    two: q = ch;
    p1 = ONE + ch * (C7 + ch);
    p2 = ch * (C9 + ch * (C8 + ch));
    t = -HALF + (C7 + TWO * ch) / p1 - (C9 + ch * (C10 + THREE * ch)) / p2;
    ch -= (ONE - exp(a + g + HALF * ch + c * M_LN2) * p2 / p1) / t;
    if (fabs(q / ch - ONE) > C1)
        goto two;
    goto four;

    /* Call routine for percentage points of the normal distribution. */
    three: x = ppnorm(p, &if1);

    /* Starting approximation using Wilson & Hilferty estimate. */

    p1 = C2 / v;
    ch = v * pow((x * sqrt(p1) + ONE - p1), 3.0);

    /* Starting approximation for P tending to 1. */

    if (ch > (C6 * v + SIX))
        ch = -TWO * (log(ONE - p) - c * log(HALF * ch) + g);

    /* Calculation of the seven-term taylor series includes a call
     to a routine for the integral of the central X distribution. */

    kount = 0;
    four: q = ch;
    p1 = HALF * ch;
    kount++;
    p2 = p - gammds(p1, xx, &if1);
    if (if1 != 0) {
        *ifault = 3;
        return ppchi;
    }
    t = p2 * exp(xx * a + g + p1 - c * log(ch));
    b = t / ch;
    a = HALF * t - b * c;
    s1 = (C19 + a * (C17 + a * (C14 + a * (C13 + a * (C12 + C11 * a))))) / C24;
    s2 = (C24 + a * (C29 + a * (C32 + a * (C33 + C35 * a)))) / C37;
    s3 = (C19 + a * (C25 + a * (C28 + C31 * a))) / C37;
    s4 = (C20 + a * (C27 + C34 * a) + c * (C22 + a * (C30 + C36 * a))) / C38;
    s5 = (C13 + C21 * a + c * (C18 + C26 * a)) / C37;
    s6 = (C15 + c * (C23 + C16 * c)) / C38;
    ch = ch + t * (ONE + HALF * t * s1 - b * c * (s1 - b * (s2 - b * (s3 - b * (s4 - b * (s5 - b * s6))))));
    if (fabs(q / ch - ONE) > PPCHI_EPS)
        goto four;
    six: ppchi = ch;
    return ppchi;
}

#define LTONE 7.0
#define UTZERO 18.66

#define ZERO 0.0
#define HALF 0.5
#define ONE 1.0
#define CON 1.28

#define A1 0.39894228044
#define A2 0.39990343850
#define A3 5.7588548045
#define A4 29.821355780
#define A5 2.62433121679
#define A6 48.69599306920
#define A7 5.92885724438

#define B1 0.398942280385
#define B2 3.8052E-8
#define B3 1.00000615302
#define B4 3.98064794E-4
#define B5 1.98615381364
#define B6 0.151679116635
#define B7 5.29330324926
#define B8 4.8385912808
#define B9 15.1508972451
#define B10 0.742380924027
#define B11 30.789933034
#define B12 3.99019417011

double anorm(double x, int upper) {
    int up;
    double ret;
    double y, z;

    up = upper;
    z = x;

    if (z < ZERO) {
        up = !up;
        z = -z;
    }

    if (z <= LTONE || (up && z <= UTZERO))
        y = HALF * z * z;
    else
        return !up ? ONE : ZERO;

    ret = (z > CON) ?
            B1 * exp(-y) / (z - B2 + B3 / (z + B4 + B5 / (z - B6 + B7 / (z + B8 - B9 / (z + B10 + B11 / (z + B12)))))) :
            HALF - z * (A1 - A2 * y / (y + A3 - A4 / (y + A5 + A6 / (y + A7))));

    return !up ? ONE - ret : ret;
}

/***************************************************************
 Compute likelihood ratio and Pearson chi-squared statistics.
 NZ = number of fitted zero values for adjusting DFs.

 lowest model = independence model A:B:C:...
 top model = saturated model m0 = ABC... (observed data)
 */

#define CHISTAT_EPS 1.0e-30
#define MIN_PROB 1.0e-36

unsigned chistat(unsigned ntab, double* obs, double* fit, double* g2_ptr, double* p2_ptr) {
    unsigned int i;
    int nz = 0;
    double g2 = 0.0, p2 = 0.0;
    double r;

    /* Compute n*sum(p*ln(p/q))
     */
    for (i = 0; i < ntab; i++) {
        if (fit[i] <= CHISTAT_EPS)
            /* Note fit=0 ==> table=0 ==> resid=0 */
            nz++;
        else {
            double diff = fabs(obs[i] - fit[i]);
            double p_q = obs[i] / fit[i];

            r = diff * diff;
            p2 += r / fit[i];
            if ((obs[i] > CHISTAT_EPS) && (diff > CHISTAT_EPS) && (p_q > MIN_PROB))
                g2 += obs[i] * log(p_q);
        }
    }
    g2 *= 2.0; /* g2 = 2*n*sum(p*ln(p/q)) = L^2 = LR */
    *g2_ptr = g2;
    *p2_ptr = p2;

    return nz;
}

// Gaussian elimination method to calculate rank
// source: http://www.wikipedia.org/wiki/Gauss_elimination_method
double ocDegreesOfFreedomStateBased(Model *model) {
    int nrows = 0, ncols = 0;
    int i = 0, j = 0;
    double **matrix = NULL;
    int **struct_matrix = model->getStructMatrix(&ncols, &nrows);
    if (struct_matrix == NULL) {
        fprintf(stdout, "ocDegreesOfFreedomStateBased(): Error. Model %s: struct matrix not found.\n", model->getPrintName());
        fflush(stdout);
        exit(1);
    }
    // create a copy of the matrix to manipulate
    matrix = new double *[nrows];
    for (i = 0; i < nrows; i++) {
        matrix[i] = new double[ncols];
    }
    for (i = 0; i < nrows; i++) {
        if (i < nrows - 1) {
            for (j = 0; j < ncols; j++) {
                matrix[i + 1][j] = (double)struct_matrix[i][j];
            }
        } else {
            for (j = 0; j < ncols; j++) {
                matrix[0][j] = (double)struct_matrix[i][j];
            }
        }
    }
    model->deleteStructMatrix();
    int irow, jrow, icol, jcol;
    bool have_pivot = false;
    int rowmax = 0;
    icol = 0;
    int i1, j1;
    double *temp_ptr;
    for (irow = 0; irow < nrows; irow++) {    // Find pivot in column j, starting in row i:
        have_pivot = false;
        do {
            rowmax = irow;
            if (icol >= ncols) break;
            for (jrow = irow + 1; jrow < nrows; jrow++) {
                if (fabs(matrix[jrow][icol]) > fabs(matrix[rowmax][icol])) {
                    rowmax = jrow;
                }
            }
            if (fabs(matrix[rowmax][icol]) > DBL_EPSILON) {
                have_pivot = true;
                if (rowmax != irow) {   //switch rows irow and rowmax
                    temp_ptr = matrix[irow];
                    matrix[irow] = matrix[rowmax];
                    matrix[rowmax] = temp_ptr;
                }
            } else {
                matrix[rowmax][icol] = 0.0;
                icol = icol + 1;
            }
        } while ((!have_pivot) && (icol < ncols));
        if (icol >= ncols) {
            break;
        }
        double factor;
        if (fabs(matrix[irow][icol]) > DBL_EPSILON) {
            for (jrow = irow+1; jrow < nrows; jrow++) {
                factor = matrix[jrow][icol] / matrix[irow][icol];
                for (jcol = icol+1; jcol < ncols; jcol++) {
                    matrix[jrow][jcol] -= matrix[irow][jcol] * factor;
                }
                matrix[jrow][icol] = 0.0;
            }
        }
        icol++;
    }
    double rank = 0;
    double limit = pow(FLT_RADIX, DBL_MANT_DIG);
    for (i = 0; i < nrows; i++) {
        for (j = i; j < ncols; j++) {
            if (fabs(matrix[i][j]) > DBL_EPSILON) {
                if (rank >= limit) {
                    fprintf(stdout, "ocDegreesOfFreedomStateBased(): Error. DF exceeds current limits of State-based OCCAM.\n");
                    fflush(stdout);
                    exit(1);
                } else {
                    rank++;
                    break;
                }
            }
        }
    }
    for (i = 0; i < nrows; i++) {
        delete[] matrix[i];
    }
    delete[] matrix;
    return rank - 1;
}
