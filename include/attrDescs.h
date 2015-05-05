#ifndef ___attrDesc
#define ___attrDesc

#include "Core.h"
// attrDesc: name, title, fmt (all const char*)
struct attrDesc {
        const char *name;
        const char *title;
        const char *fmt;
};

// attrDescriptions: a big static array of attributes
constexpr attrDesc attrDescriptions[] = { 
    { ATTRIBUTE_LEVEL, "Level", "%14.0f" }, 
    { ATTRIBUTE_H, "H", "%12.4f" }, 
    { ATTRIBUTE_T, "T", "%12.4f" }, 
    { ATTRIBUTE_DF, "DF", "%14.0f" }, 
    { ATTRIBUTE_DDF, "dDF", "%14.0f" }, 
    { ATTRIBUTE_FIT_H, "H(IPF)", "%12.4f" }, 
    { ATTRIBUTE_ALG_H, "H(ALG)", "%12.4f" }, 
    { ATTRIBUTE_FIT_T, "T(IPF)", "%12.4f" }, 
    { ATTRIBUTE_ALG_T, "T(ALG)", "%12.4f" }, 
    { ATTRIBUTE_LOOPS, "Loops", "%2.0f" }, 
    { ATTRIBUTE_EXPLAINED_I, "Inf", "%1.8f" }, 
    { ATTRIBUTE_AIC, "dAIC", "%12.4f" },
    { ATTRIBUTE_BIC, "dBIC", "%12.4f" }, 
    { ATTRIBUTE_BP_AIC, "dAIC(BP)", "%12.4f" }, 
    { ATTRIBUTE_BP_BIC, "dBIC(BP)", "%12.4f" }, 
    { ATTRIBUTE_PCT_CORRECT_DATA, "%C(Data)", "%12.4f" }, 
    { ATTRIBUTE_PCT_COVERAGE, "%cover", "%12.4f" }, 
    { ATTRIBUTE_PCT_CORRECT_TEST, "%C(Test)", "%12.4f" }, 
    { ATTRIBUTE_PCT_MISSED_TEST, "%miss", "%12.4f" }, 
    { ATTRIBUTE_BP_EXPLAINED_I, "Inf(BP)", "%12f" },
    { ATTRIBUTE_UNEXPLAINED_I, "Unexp Info", "%12.4f" }, 
    { ATTRIBUTE_T_FROM_H, "T(H)", "%12.4f" }, 
    { ATTRIBUTE_IPF_ITERATIONS, "IPF Iter", "%7.0f" }, 
    { ATTRIBUTE_IPF_ERROR, "IPF Err", "%12.8g" }, 
    { ATTRIBUTE_PROCESSED, "Proc", "%2.0" }, 
    { ATTRIBUTE_IND_H, "H(Ind)", "%12.4f" }, 
    { ATTRIBUTE_DEP_H, "H(Dep)", "%12.4f" }, 
    { ATTRIBUTE_COND_H, "H|Model", "%12.4f" }, 
    { ATTRIBUTE_COND_DH, "dH|Model", "%12.4f" }, 
    { ATTRIBUTE_COND_PCT_DH, "%dH(DV)", "%12.4f" }, 
    { ATTRIBUTE_COND_DF, "DF(Cond)", "%14.0f" },
    { ATTRIBUTE_COND_DDF, "dDF(Cond)", "%14.0f" }, 
    { ATTRIBUTE_TOTAL_LR, "LR Total", "%12.4f" }, 
    { ATTRIBUTE_IND_LR, "LR Ind", "%12.4f" }, 
    { ATTRIBUTE_COND_LR, "LR|Model", "%12.4f" }, 
    { ATTRIBUTE_COND_H_PROB, "H|Model", "%12.4f" }, 
    { ATTRIBUTE_P2, "P2", "%12.4f" }, 
    { ATTRIBUTE_P2_ALPHA, "P2 Alpha", "%12.4f" }, 
    { ATTRIBUTE_P2_BETA, "P2 Beta", "%12.4f" }, 
    { ATTRIBUTE_LR, "dLR", "%12.4f" },
    { ATTRIBUTE_INCR_ALPHA, "Inc.Alpha", "%12.4f" }, 
    { ATTRIBUTE_INCR_ALPHA_REACHABLE, "Inc.A.<threshold", "%1.0f" },
    { ATTRIBUTE_PROG_ID, "Prog.", "%14.0f" }, 
    { ATTRIBUTE_ALPHA, "Alpha", "%12.4f" }, 
    { ATTRIBUTE_BETA, "Beta", "%12.4f" }, 
    { ATTRIBUTE_BP_T, "T(BP)", "%12.4f" }, 
    { ATTRIBUTE_BP_H, "est. H(BP)", "%12.4f" }, 
    { ATTRIBUTE_BP_UNEXPLAINED_I, "est. Unexplained(BP)", "%12.4f" }, 
    { ATTRIBUTE_BP_ALPHA, "Alpha(BP)", "%12.4f" }, 
    { ATTRIBUTE_BP_BETA, "Beta(BP)", "%12.4f" }, 
    { ATTRIBUTE_BP_LR, "LR(BP)", "%12.4f" }, 
    { ATTRIBUTE_BP_COND_H, "H|Model(BP)", "%12.4f" }, 
    { ATTRIBUTE_BP_COND_DH, "dH|Model(BP)", "%12.4f" }, 
    {ATTRIBUTE_BP_COND_PCT_DH, "est. %dH(DV)(BP)", "%12.4f" }, 

};

#endif
