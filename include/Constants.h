/*
 * Copyright © 1990 The Portland State University OCCAM Project Team
 * [This program is licensed under the GPL version 3 or later.]
 * Please see the file LICENSE in the source
 * distribution of this software for license terms.
 */

#ifndef ___Constants
#define ___Constants

const int DONT_CARE = 0xffffffff; // all bits on
const int KEY_SEGMENT_BITS = 32; // number of usable bits in a key segment
//const int DONT_CARE = ULONG_MAX;	// all bits on
//const int KEY_SEGMENT_BITS = sizeof(KeySegment) * 8;	// number of usable bits in a key segment

const int MAXNAMELEN = 32;
const int MAXABBREVLEN = 8;
const int MAXCARDINALITY = 65535;

const int ALL = 1;
const int REST_ALL = -1;
const int KEEP = 1;
const int DISCARD = -1;

const double PRINT_MIN = 1e-8;
const double PROB_MIN = 1e-36;

#define OLD_ROW 0
#define NEW_ROW 1

#define ATTRIBUTE_LEVEL "level"
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
#define ATTRIBUTE_AIC "aic"
#define ATTRIBUTE_BIC "bic"
#define ATTRIBUTE_BP_AIC "bp_aic"
#define ATTRIBUTE_BP_BIC "bp_bic"
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
#define ATTRIBUTE_INCR_ALPHA "incr_alpha"
#define ATTRIBUTE_INCR_ALPHA_REACHABLE "incr_alpha_reachable"
#define ATTRIBUTE_PROG_ID "prog_id"
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
#define ATTRIBUTE_PCT_COVERAGE "pct_coverage"
#define ATTRIBUTE_PCT_CORRECT_TEST "pct_correct_test"
#define ATTRIBUTE_PCT_MISSED_TEST "pct_missed_test"



#endif
