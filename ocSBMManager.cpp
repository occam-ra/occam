/* Copyright 2000, Portland State University Systems Science Program.  All Rights Reserved
 */

#include "ocCore.h"
#include "ocMath.h"
#include "ocSBMManager.h"
#include "ocModelCache.h"
#include "ocSearchBase.h"
#include "ocReport.h"
#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include "ocWin32.h"

ocSBMManager::ocSBMManager(ocVariableList *vars, ocTable *input):
    ocManagerBase(vars, input)
{
    topRef = bottomRef = refModel = NULL;
    projection = true;
    filterAttr = NULL;
    filterOp = EQUALS;
    filterValue = 0.0;
    sortAttr = NULL;
    sortDirection = 0;
}

ocSBMManager::ocSBMManager():
    ocManagerBase()
{
    topRef = bottomRef = refModel = NULL;
    projection = true;
    filterAttr = NULL;
    filterOp = EQUALS;
    filterValue = 0.0;
    sortAttr = NULL;
    sortDirection = 0;
}

ocSBMManager::~ocSBMManager()
{
    if (filterAttr) delete filterAttr;
    if (sortAttr) delete sortAttr;
}

bool ocSBMManager::initFromCommandLine(int argc, char **argv)
{
    if (!ocManagerBase::initFromCommandLine(argc, argv)) return false;
    if (varList) {
	int varCount = varList->getVarCount();
	ocRelation *top = new ocRelation(varList, varCount);
	int i;
	for (i = 0; i < varCount; i++) top->addVariable(i);	// all vars in saturated model
	top->setTable(inputData);
	makeReferenceModels(top);
    }
    return true;
}


void ocSBMManager::makeReferenceModels(ocRelation *top)
{
    ocModel *model = new ocModel(1);
    model->addRelation(top);
    //modelCache->addModel(model);
    topRef = model;
    //-- Generate bottom reference model. If system is neutral.
    //-- this has a relation per variable. Otherwise it has a
    //-- relation per dependent variable, and one containing all
    //-- the independent variables.
    int varCount = varList->getVarCount();
    int* varindices = new int[varCount];
    ocRelation *rel;
    int i;
    if (varList->isDirected()) {
	//-- first, make a relation with all the independent variables
	model = new ocModel(2);	// typical case: one dep variable
	int pos = 0;
	ocVariable *var;
	for (i = 0; i < varCount; i++) {
	    var = varList->getVariable(i);
	    if (!var->dv) varindices[pos++] = i;
	}
	rel = getRelation(varindices, pos, true);
	model->addRelation(rel);
	//-- now add a unary relation for each dependent variable
	for (i = 0; i < varCount; i++) {
	    var = varList->getVariable(i);
	    if (var->dv) {
		varindices[0] = i;
		rel = getRelation(varindices, 1, true);
		model->addRelation(rel);
	    }
	}
    }
    else {
	//this needs to change since in SB the bottom reference is uniform model and 
	//not independence model
	model = new ocModel(varCount);
	for (i = 0; i < varCount; i++) {
	    //-- build a list of all variables but r
	    varindices[0] = i;
	    rel = getRelation(varindices, 1, true);
	    model->addRelation(rel);
	    /*
	       int inputCells = 1;
	       int varcount = varList->getVarCount();
	       for (i = 0; i < varcount; i++) {
	       inputCells *= varList->getVariable(i)->cardinality;
	       }
	       double cellWeight = 1.0 / inputCells;
	       int *varvalues = new int[varcount];

	       for (i = 0; i < varcount; i++) {
	       varvalues[i] = 0;
	       }
	       ocKeySegment *key = new ocKeySegment[keysize];
	       long cellCount = 0;
	       for(;;) {
	       ocKey::buildFullKey(key, keysize, varList, varvalues);
	       fitTable1->addTuple(key, cellWeight);
	       cellCount++;
	       if (!nextTuple(varList, varvalues)) break;
	       }
	       delete [] varvalues;

	     */
	}
    }
    //modelCache->addModel(model);
    bottomRef = model;
    computeDF(topRef);
    computeH(topRef);
    computeDF(bottomRef);
    computeH(bottomRef);
    //-- compute relation statistics for the top relation
    computeStatistics(topRef->getRelation(0));

    //-- set default reference model depending on whether
    //-- the system is directed or neutral
    refModel = varList->isDirected() ? bottomRef : topRef;
    delete [] varindices;
}

ocModel *ocSBMManager::setRefModel(const char *name)
{
    //printf("in SB manager\n");
    if (strcasecmp(name, "top") == 0) {
	refModel = topRef;
    }
    else if (strcasecmp(name, "bottom") == 0) {
	refModel = bottomRef;
    }
    else {
	//Anjali....the top reference trouble might be from here
	refModel = makeSBModel(name, true);
    }
    return refModel;
}

double ocSBMManager::computeExplainedInformation(ocModel *model)
{
    double topH = topRef->getAttribute(ATTRIBUTE_H);
    double botH = bottomRef->getAttribute(ATTRIBUTE_H);
    double modelT = computeTransmission(model,IPF);
    double info = (botH - topH - modelT) / (botH - topH);
    // info is normalized but may not quite be between zero and 1 due to
    // roundoff. Fix this here.
    if (info <= 0.0) info = 0.0;
    if (info >= 1.0) info = 1.0;
    model->setAttribute(ATTRIBUTE_EXPLAINED_I, info);
    return info;
}

double ocSBMManager::computeUnexplainedInformation(ocModel *model)
{
    double topH = topRef->getAttribute(ATTRIBUTE_H);
    double botH = bottomRef->getAttribute(ATTRIBUTE_H);
    double modelT = computeTransmission(model,IPF);
    double info = modelT / (botH - topH);
    // info is normalized but may not quite be between zero and 1 due to
    // roundoff. Fix this here.
    if (info <= 0.0) info = 0.0;
    if (info >= 1.0) info = 1.0;
    model->setAttribute(ATTRIBUTE_UNEXPLAINED_I, info);
    return info;
}

double ocSBMManager::computeDDF(ocModel *model)
{
    double refDF = getRefModel()->getAttribute(ATTRIBUTE_DF);
    double modelDF = model->getAttribute(ATTRIBUTE_DF);
    double df = refDF - modelDF;
    //-- for bottom reference the sign will be wrong
    df = fabs(df);
    model->setAttribute(ATTRIBUTE_DDF, df);
    return df;
}


void ocSBMManager::computeDFStatistics(ocModel *model)
{
    compute_SB_DF(model);
    computeDDF(model);
}



void ocSBMManager::computeInformationStatistics(ocModel *model)
{
    //printf("compute H in SB computeInformationStat\n");
    computeH(model,IPF,1);
    computeTransmission(model,IPF,1);
    computeExplainedInformation(model);
    computeUnexplainedInformation(model);
}



void ocSBMManager::computeL2Statistics(ocModel *model)
{
    //-- make sure we have the fittted table (needed for some statistics)
    //-- this will return immediately if the table was already created.

    //-- make sure the other attributes are there
    //printf("in L2 statistics\n");
    computeDFStatistics(model);

    //exit(1);
    computeInformationStatistics(model);
    //-- compute chi-squared statistics and related statistics. L2 = 2*n*sum(p(ln p/q))
    //-- which is 2*n*ln(2)*T
    int errcode;
    double modelT = computeTransmission(model,IPF);
    double modelL2 = 2.0 * M_LN2 * sampleSize * modelT;
    double refT = computeTransmission(refModel);
    double refL2 = 2.0 * M_LN2 * sampleSize * refT;
    double refModelL2 = refL2 - modelL2;
    double modelDF = compute_SB_DF(model);
    double refDF = computeDF(refModel);
    double refDDF = modelDF - refDF;

    //-- depending on the relative position of the reference model and the
    //-- current model in the hierarchy, refDDF may be positive or negative
    //-- as may refModel2. But the signs should be the same. If they aren't,
    //-- the csa computation will fail.
    if (refDDF < 0) {
	refDDF = -refDDF;
	refModelL2 = - refModelL2;
    }

    //-- eliminate negative value due to small roundoff
    if (refModelL2 <= 0.0) refModelL2 = 0.0;

    double refL2Prob = csa(refModelL2, refDDF);

    double critX2=0, refL2Power=0;

    errcode = 0;
    double alpha;
    if (!getOptionFloat("alpha", NULL, &alpha)) alpha = 0.0;
    if (alpha > 0) critX2 = ppchi(alpha, refDDF, &errcode);
    else critX2 = refModelL2;
    if (errcode) printf("ppchi: errcode=%d\n", errcode);
    refL2Power = 1.0 - chin2(critX2, refDDF, refModelL2, &errcode);

    //?? do something with these returned errors
    model->setAttribute(ATTRIBUTE_DDF, refDDF);
    model->setAttribute(ATTRIBUTE_LR, refModelL2);
    model->setAttribute(ATTRIBUTE_ALPHA, refL2Prob);
    model->setAttribute(ATTRIBUTE_BETA, refL2Power);
}

void ocSBMManager::computePearsonStatistics(ocModel *model)
{
    //-- these statistics require a full contingency table, so make
    //-- sure one has been created.
    if (model == NULL || bottomRef == NULL) return;
    makeFitTable(model,1);

    ocTable *modelFitTable = new ocTable(keysize, fitTable1->getTupleCount());

    modelFitTable->copy(fitTable1);
    makeFitTable(bottomRef);
    double modelP2 = ocPearsonChiSquared(inputData, modelFitTable, (long)round(sampleSize));
    double refP2 = ocPearsonChiSquared(inputData, fitTable1, (long)round(sampleSize));

    int errcode;
    double modelDF = compute_SB_DF(model);
    double refDF = computeDF(refModel);
    double refDDF = fabs(modelDF - refDF);
    double refModelP2 = refP2 - modelP2;
    double refP2Prob = csa(refModelP2, refDDF);

    double critX2, refP2Power;
    errcode=0;
    double alpha;

    if (!getOptionFloat("alpha", NULL, &alpha)) alpha = 0.0;
    if (alpha > 0) critX2 = ppchi(alpha, refDDF, &errcode);
    else critX2 = modelP2;
    if (errcode) printf("ppchi: errcode=%d\n", errcode);
    refP2Power = 1.0 - chin2(critX2, refDDF, modelP2, &errcode);
    if (errcode) printf("chin2: errcode=%d, %.2f, %.2f\n", errcode, refDDF, modelP2);
    //?? do something with these returned errors

    model->setAttribute(ATTRIBUTE_P2, modelP2);
    model->setAttribute(ATTRIBUTE_P2_ALPHA, refP2Prob);
    model->setAttribute(ATTRIBUTE_P2_BETA, refP2Power);
}

void ocSBMManager::computeDependentStatistics(ocModel *model)
{
    //-- the basic metric is the conditional uncertainty u(Z|ABC...), which is
    //-- u(model) - u(ABC...), where ABC... are the independent variables
    //-- first, compute the relation stats for the bottom reference model, which
    //-- will give us the u(ABC...).
    if (!getVariableList()->isDirected()) return;	// can only do this for directed models
    double depH = topRef->getRelation(0)->getAttribute(ATTRIBUTE_DEP_H);
    ocRelation *indRel;
    int i;
    for (i = 0; i < bottomRef->getRelationCount(); i++) {
	indRel = bottomRef->getRelation(i);
	if (indRel->isIndOnly()) break;	// this is the one.
    }
    double indH = indRel->getAttribute(ATTRIBUTE_H);
    double refH = computeH(bottomRef);
    double refCondH = refH - indH;

    //printf("compute H in SB computeDependStat\n");
    double h = computeH(model,IPF);
    double condH = h - indH;
    model->setAttribute(ATTRIBUTE_COND_H, condH);
    model->setAttribute(ATTRIBUTE_COND_DH, refH - h);
    model->setAttribute(ATTRIBUTE_COND_PCT_DH, 100 * (refH - h) / depH);
}

void ocSBMManager::computeBPStatistics(ocModel *model)
{
    // this function computes transmission using the Fourier BP method.
    // Individual q values are computed as the mean value from each projection,
    // q(x) = sum (R(x)/|R|) - (nR - 1), where R(x) is the projected value
    // which contains state x in relation R; |R| is the number of states collapsed
    // into each state of relation R; and nR is the number of relations in the model.
    //
    // Since the transmission terms are p(x) log (p(x)/q(x)), these computations
    // are only done for nonzero p and q values.
    // Subtracting for overlaps may leave the result un-normalized because of 
    // Null overlaps (for example, AB:CD has no overlaps, but p(AB)+p(CD) = 2, not 1)
    // The count of origin terms which much still be deducted for normalization
    // is maintained, and the q values corrected at the end.

    class BPIntersectProcessor : public ocIntersectProcessor
    {
	public:
	    BPIntersectProcessor(ocTable *inData, int rels, long fullDim)
	    {
		inputData = inData;
		keysize = inputData->getKeySize();
		qData = new ocTable(keysize, inputData->getTupleCount());
		//-- seed the computed table with the tuples from the input data,
		//-- but with zero values. These are the only tuples we care about.
		for (int i = 0; i < inputData->getTupleCount(); i++) {
		    ocKeySegment *key = inputData->getKey(i);
		    qData->addTuple(key, 0);
		}

		//-- keep track of the total probability so we can deduct
		//-- the appropriate number of origin terms.
		originTerms = 0;

		relCount = rels;

		fullDimension = fullDim;
	    }


	    virtual void process(int sign, ocRelation *rel)
	    {
		ocKeySegment *key = new ocKeySegment[keysize];
		double qi, q;
		//-- get the orthogonal dimension of the relation (the number of states
		//-- projected into one substate)
		long relDimension = fullDimension / 
		    ((long)ocDegreesOfFreedom(rel) + 1);
		//-- add the scaled contribution to each q
		for (int i = 0; i < qData->getTupleCount(); i++) {
		    qData->copyKey(i, key);
		    q = qData->getValue(i);
		    ocKeySegment *mask = rel->getMask();
		    for (int k = 0; k < keysize; k++) key[k] |= mask[k];
		    int j = rel->getTable()->indexOf(key);
		    if (j >= 0) {
			qi = sign * (rel->getTable()->getValue(j) / relDimension);
			qData->setValue(i, qi + q);
		    }
		}
		originTerms += sign;
	    }

	    double getTransmission()
	    {
		correctOriginTerms();

		double t, p, q;
		t = 0;
		for (long i = 0; i < inputData->getTupleCount(); i++) {
		    long j = qData->indexOf(inputData->getKey(i));
		    p = inputData->getValue(i);
		    q = qData->getValue(j);
		    if (p > 0 && q > 0)
			t += p * log (p/q);
		}
		t/= log(2.0);
		return t;
	    }

	    void correctOriginTerms()
	    {
		double q;
		double originTerm = ((double)(originTerms-1)) / fullDimension;
		for (long i = 0; i < qData->getTupleCount(); i++) {
		    q = qData->getValue(i);
		    q -= originTerm;
		    qData->setValue(i, q);
		}
	    }

	    ocTable *qData, *inputData;
	    long fullDimension;
	    int keysize;
	    int relCount;
	    int originTerms;
    };

    long fullDimension = (long)ocDegreesOfFreedom(topRef->getRelation(0)) + 1;

    BPIntersectProcessor processor(inputData, model->getRelationCount(), fullDimension);
    doIntersectionProcessing(model, &processor);
    double t = processor.getTransmission();
    model->setAttribute(ATTRIBUTE_BP_T, t);
}


void ocSBMManager::setFilter(const char *attrname, double attrvalue, RelOp op)
{
    if (filterAttr) delete filterAttr;
    filterAttr = new char[strlen(attrname) + 1];
    strcpy(filterAttr, attrname);
    filterValue = attrvalue;
    filterOp = op;
}

bool ocSBMManager::applyFilter(ocModel *model)
{
    //-- if no filter defined, then it passes
    if (filterAttr == NULL) return true;

    //-- make sure require attributes were computed
    computeRelWidth(model);
    computeL2Statistics(model);
    computeDependentStatistics(model);

    //-- now apply the test
    double val = model->getAttribute(filterAttr);
    switch (filterOp) {
	case LESSTHAN:
	    return val < filterValue;
	case EQUALS:
	    return fabs(val - filterValue) < DBL_EPSILON;
	case GREATERTHAN:
	    return val > filterValue;
	default:
	    return false;
    }
}


void ocSBMManager::setSortAttr(const char *name)
{
    if (sortAttr) delete sortAttr;
    sortAttr = new char[strlen(name) + 1];
    strcpy(sortAttr, name);
}


static void printRefTable(ocModel *model, FILE *fd, const char *ref, const char **strings, int rows)
{
    //-- Print general report for a single model, similar to Fit in Occam2
    const char *header, *beginLine, *endLine, *separator, *footer, *headerSep;
    if (ocReport::isHTMLMode()) {
	header = "<br><hr><br><table border=0 cellpadding=0 cellspacing=0>\n";
	beginLine = "<tr><td>";
	separator = "</td><td>";
	endLine = "</td></tr>\n";
	footer = "</table>";
	headerSep = "<tr><td colspan=10><hr></td></tr>\n";
    }
    else {
	header = "";
	beginLine = "    ";
	separator = ",";
	endLine = "\n";
	footer = "\n";
	headerSep = 
	    "--------------------------------------------------------------------------------\n";
    }
    int cols = 4;
    int labelwidth = 20;
    int colwidth = 18;
    int row, col, rowlabel;
    const char *label;

    fprintf(fd, header);
    fprintf(fd, "%sREFERENCE = %s%s", beginLine, ref, endLine);
    label = "Value";
    fprintf(fd, "%s%s%s%s", beginLine, separator, label, separator);
    label = "Prob. (Alpha)";
    fprintf(fd, "%s%s", label, separator);
    label = "Power (Beta)";
    fprintf(fd, "%s%s", label, endLine);

    fprintf(fd, headerSep);
    for (row = 0; row < rows; row++) {
	rowlabel = row * cols; 
	fprintf(fd, "%s%s", beginLine, strings[rowlabel]);
	for (col = 1; col < cols; col++) {
	    double value = model->getAttribute(strings[rowlabel + col]);
	    if (value >= 0)
		fprintf(fd, "%s%g", separator, value);
	    else
		fprintf(fd, "%s", separator);
	}
	fprintf(fd, endLine);
    }
    fprintf(fd, footer);
}


void ocSBMManager::printFitReport(ocModel *model, FILE *fd)
{
    //-- Print general report for a single model, similar to Fit in Occam2
    const char *header, *beginLine, *endLine, *separator, *footer;
    const char *beginLine1, *endLine1, *separator1;
    if (ocReport::isHTMLMode()) {
	header = "<table>\n";
	beginLine = "<tr><td>";
	separator = "</td><td>";
	endLine = "</td></tr>\n";
	footer = "</table>";
	beginLine1 = "<tr><td>";
	separator1 = "</td><td>";
	endLine1 = "</td></tr>\n";

    }
    else {
	header = "";
	beginLine = beginLine1 = "    ";
	separator =separator1= ",";
	endLine =endLine1= "\n";
	footer = "\n";
    }
    //printf("in print fit report\n");
    bool directed = getVariableList()->isDirected();
    fprintf(fd, header);
    fprintf(fd, "%sModel%s%s%s", beginLine, separator, model->getPrintName(), separator);
    if (directed)
	fprintf(fd, "Directed System%s", endLine);
    else
	fprintf(fd, "Neutral System%s", endLine);

    //-- Print relations using long names
    int i, j;
    for (i = 0; i < model->getRelationCount(); i++) {
	fprintf(fd, beginLine);
	ocRelation *rel = model->getRelation(i);
	for (j = 0; j <rel->getVariableCount(); j++) {
	    const char *varname = getVariableList()->getVariable(rel->getVariable(j))->name;
	    if (j > 0) fprintf(fd, ", ");
	    fprintf(fd, varname);
	}
	fprintf(fd, endLine);
    }

    //-- Print some general stuff
    int cwid = 40;
    const char *label;
    double value;

    label = "Sample size:";
    fprintf(fd, "%s%s%s%g%s", beginLine, label, separator, sampleSize, endLine);
    label = "Number of cells:";
    value = topRef->getAttribute("df") + 1;
    fprintf(fd, "%s%s%s%g%s", beginLine, label, separator, value, endLine);
    label = "Degrees of Freedom (DF):";
    value = model->getAttribute("df");
    fprintf(fd, "%s%s%s%g%s", beginLine, label, separator, value, endLine);

    label="Structure Matrix:";
    fprintf(fd,"%s%s%s",beginLine,label,endLine);
    int statespace,Total_const;
    int **struct_matrix=model->get_structMatrix(&statespace,&Total_const);
    for(int i=0;i<Total_const;i++){
	fprintf(fd, "%s%s%s%s", beginLine1, separator1, separator1, separator1);
	for(int j=0;j<statespace;j++){
	    fprintf(fd,"%d %s",struct_matrix[i][j],separator1);
	}
	fprintf(fd,"%s",endLine1);
    }
    //exit(2);

    label = "Loops:";
    //value = model->getAttribute("h");
    fprintf(fd, "%s%s%s%s%s", beginLine, label, separator, value > 0 ? "?" : "?", endLine);
    label = "Entropy(H):";
    value = model->getAttribute("h");
    fprintf(fd, "%s%s%s%g%s", beginLine, label, separator, value, endLine);
    label = "Information captured (%):";
    value = model->getAttribute("information") * 100.0;
    fprintf(fd, "%s%s%s%g%s", beginLine, label, separator, value, endLine);
    label = "Transmission (T):";
    value = model->getAttribute("t");
    fprintf(fd, "%s%s%s%g%s", beginLine, label, separator, value, endLine);
    fprintf(fd, footer);
    //-- print top and bottom reference tables
    const char *topFields[] = {
	"Log-Likelihood (LR)", ATTRIBUTE_LR, ATTRIBUTE_ALPHA, ATTRIBUTE_BETA,
	"Pearson X2", ATTRIBUTE_P2, ATTRIBUTE_P2_ALPHA, ATTRIBUTE_P2_BETA,
	"Delta DF (dDF)", ATTRIBUTE_DDF, "", "",
    };
    const char *bottomFields[] = {
	"Log-Likelihood (LR)", ATTRIBUTE_LR, ATTRIBUTE_ALPHA, ATTRIBUTE_BETA,
	"Pearson X2", ATTRIBUTE_P2, ATTRIBUTE_P2_ALPHA, ATTRIBUTE_P2_BETA,
	"Delta DF (dDF)", ATTRIBUTE_DDF, "", "",
    };
    //-- compute attributes for top and bottom references
    model->getAttributeList()->reset();
    setRefModel("top");
    computeInformationStatistics(model);
    computeDependentStatistics(model);
    computeL2Statistics(model);
    computePearsonStatistics(model);
    printRefTable(model, fd, "TOP", topFields, 3);

    model->getAttributeList()->reset();
    setRefModel("bottom");
    computeInformationStatistics(model);
    computeDependentStatistics(model);
    computeL2Statistics(model);
    computePearsonStatistics(model);
    printRefTable(model, fd, "BOTTOM", bottomFields, 3);
}

