#include "Key.h"
#include "ManagerBase.h"
#include "Report.h"
#include <cstring>
#include "Model.h"
#include "Math.h"

void Report::printResiduals(FILE *fd, Model *model, bool skipTrained, bool skipIVIs) {

    if (manager->getVariableList()->isDirected()) {
        return;
    }

    double adjustConstant = manager->getFunctionConstant() + manager->getNegativeConstant();

    int relCount = model->getRelationCount();
    int trueRelCount = 0;
    int dyadCount = 0;

    // first pass: figure out true rel count
    if (relCount > 1) {
        for (int i = 0; i < relCount; i++) {
            Relation* rel = model->getRelation(i);
            int varCount = rel->getVariableCount();
            if (varCount > 1) { trueRelCount += 1; }
            if (varCount == 2) { dyadCount += 1; }
        }
    }   

    // print dyad summary table
    if (dyadCount > 0) {
        printDyadSummary(fd, model); 
    }

    // print single variables
    if (relCount > 1 && !skipIVIs) {
        for (int i = 0; i < relCount; i++) {
            Relation* rel = model->getRelation(i);
            int varCount = rel->getVariableCount();
            if (varCount == 1) {
                printSingleVariable(fd, rel, adjustConstant);
                hl(fd);
            }
        }
        newl(fd);
    }

    // print all relations    
    if (relCount > 1) {
        for (int i = 0; i < relCount; i++) {
            Relation* rel = model->getRelation(i);
            int varCount = rel->getVariableCount();
            if (varCount > 1) {
                printLift(fd, rel, adjustConstant);
                hl(fd);
            }
        }
        newl(fd);
    }

    // print summary (unless the whole data is "just as good")
    if (trueRelCount > 1 && trueRelCount != relCount) {
        printSummary(fd, model, adjustConstant);
        hl(fd);
    }

    // print whole data
    if (!skipTrained || trueRelCount == relCount) { 
        printWholeTable(fd, model, adjustConstant); 
        hl(fd);
    }



}

void Report::printWholeTable(FILE* fd, Model* model, double adjustConstant) {
    fprintf(fd, "Observations for all states for the Model %s\n", model->getPrintName());
    newl(fd);

    Table* input_table = manager->getInputData();
    int keysize = input_table->getKeySize();

    Table* fit_table = new Table(keysize, input_table->getTupleCount());
    manager->makeFitTable(model);
    fit_table->copy(manager->getFitTable());
   
    Table* indep_table = manager->getIndepTable();

    VariableList *varlist = manager->getVariableList();
    fprintf(fd, "Variable order: ");
    
    long var_count = varlist->getVarCount();
    for (int i = 0; i < var_count; i++) {
        fprintf(fd, "%s", varlist->getVariable(i)->abbrev);
    }

    double sample_size = manager->getSampleSz();
    
    printTable(fd, NULL, fit_table, input_table, indep_table, adjustConstant, sample_size, true, true);
    printTestData(fd, NULL, fit_table, indep_table, adjustConstant, keysize, true, true);

    delete fit_table;
}

void Report::printSingleVariable(FILE* fd, Relation* rel, double adjustConstant) {
    fprintf(fd, "\nMargins for the Variable %s\n", rel->getPrintName());
    printRel(fd, rel, adjustConstant, false);
}

void Report::printLift(FILE* fd, Relation* rel, double adjustConstant) {
    fprintf(fd, "\nObservations for the Relation %s\n", rel->getPrintName());

    printRel(fd, rel, adjustConstant, true);
}

void Report::printRel(FILE* fd, Relation* rel, double adjustConstant, bool printLift) {

    // Project the data to this relation (Obs. Prob).
    int sample_size = manager->getSampleSz();
    Table* input_data = manager->getInputData();
    int keysize = input_data->getKeySize();
    Table* input_table = new Table(keysize, input_data->getTupleCount());
    manager->makeProjection(input_data, input_table, rel);


    // Get Independence tables (Ind. Prob)
    Table* indep_table = printLift 
        ? manager->projectedFit(rel, manager->getBottomRefModel())
        : nullptr;


    // Print it out...
    printTable(fd, rel, nullptr, input_table, indep_table, adjustConstant, sample_size, printLift, false);
    printTestData(fd, rel, nullptr, indep_table, adjustConstant, keysize, false, printLift);
    delete input_table;
}

void Report::printTestData(FILE* fd, Relation* rel, Table* fit_table, Table* indep_table, double adjustConstant, int keysize, bool printCalc, bool printLift) { 
    Table *test_data = manager->getTestData();
    double test_sample_size = manager->getTestSampleSize();
    if (test_data == NULL || test_sample_size <= 0.0) { return; }
    
    fprintf(fd, "Test Data");
    newl(fd);

    Table* test_table = rel == NULL ? test_data : new Table(keysize, test_data->getTupleCount());
    if (rel) { manager->makeProjection(test_data, test_table, rel); }

    printTable(fd, rel, fit_table, test_table, indep_table, adjustConstant, test_sample_size, printLift, printCalc);
}

void Report::printSummary(FILE* fd, Model* model, double adjustConstant) {
    fprintf(fd, "Observations for the Model %s (summarizing over IVIs)\n", model->getPrintName());
    newl(fd);


    // THIS IS THE KEY TO THIS SUMMARY:
    // `rel` is a relation holding all of the relevant variables.
    int var_count = manager->getVariableList()->getVarCount();
    int var_indices[var_count], return_count;
    manager->getRelevantVars(model, var_indices, return_count, true);
    Relation *rel = manager->getRelation(var_indices, return_count);

    // Project the data to this relation (Obs. Prob).
    int sample_size = manager->getSampleSz();
    Table* input_data = manager->getInputData();
    int keysize = input_data->getKeySize();
    Table* input_table = new Table(keysize, input_data->getTupleCount());
    manager->makeProjection(input_data, input_table, rel);


    // Get Independence tables (Ind. Prob) and also (Calc.Prob.)
    Table* indep_table = manager->projectedFit(rel, manager->getBottomRefModel());
    Table* fit_table = manager->projectedFit(rel, model);


    // Print it out...
    printTable(fd, rel, fit_table, input_table, indep_table, adjustConstant, sample_size, true, true);
    printTestData(fd, rel, fit_table, indep_table, adjustConstant, keysize, true, true);
    delete input_table;
}


constexpr const char* dyadHeader[4] = {
    "<table cellspacing=0 cellpadding=0><tr><th>Relation</th><th>State</th><th>|</th><th>Max.Lift</th><th>Freq.</th><th>T</th><th>Tmax</th><th>T/Tmax</th><th>%%DH(1|2)</th><th>%%DH(2|1)</th></tr>\n",
    "Relation\tState\t|\tMax.Lift\tFreq.\tT\tTmax\tT/Tmax\t%%DH(1|2)\t%%DH(2|1)\n",
    "Relation,State,|,Max.Lift,Freq.,T,Tmax,T/Tmax,%%DH(1|2),%%DH(2|1)\n",
    "Relation    State    |    Max.Lift    Freq.    T    Tmax    T/Tmax    %%DH(1|2)    %%DH(2|1)\n",
};

constexpr const char* dyadFooter[4] = {
    "</table>",
    "\n",
    "\n",
    "\n"
};

constexpr const char* dyadFmt[4] = {
    "<tr %s><td>%s</td><td>%s</td><td>|</td><td>%g</td><td>%g</td><td>%g</td><td>%g</td><td>%g</td><td>%#2.1f</td><td>%#2.1f</td></tr>\n",
    "%s%s\t%s\t|\t%g\t%g\t%g\t%g\t%g\t%#2.1f\t%#2.1f\n",
    "%s%s,%s,|,%g,%g,%g,%g,%g,%#2.1f,%#2.1f\n",
    "%s%s    %s    |    %g    %g    %g    %g    %g    %#2.1f    %#2.1f\n"
};

void Report::findEntropies(Relation* rel, double& h1, double& h2, double& h12) {

        int var_indices1[1] = {rel->getVariable(0)};
        int var_indices2[1] = {rel->getVariable(1)};
        Relation *rel1 = manager->getRelation(var_indices1, 1);
        Relation *rel2 = manager->getRelation(var_indices2, 1);

//        printf("Order: %s, %s\n", rel1->getPrintName(), rel2->getPrintName());

        // To find h1, h2, h12:
        // * get relTab = Obs.Prob. table for the relation by projection
        // * get tab1, tab2 = Obs.Prob. table for each of Var1 and Var2 by projection
        // * from relTab, get H(12)
        // * from tab1, tab2 get H(1), H(2)

        Table* input_data = manager->getInputData();
        int keysize = input_data->getKeySize();
        
        Table* tab1 = new Table(keysize, input_data->getTupleCount());
        manager->makeProjection(input_data, tab1, rel1);

        Table* tab2 = new Table(keysize, input_data->getTupleCount());
        manager->makeProjection(input_data, tab2, rel2);
        
        Table* tab12 = new Table(keysize, input_data->getTupleCount());
        manager->makeProjection(input_data, tab12, rel);
       
        h1 = ocEntropy(tab1);
        h2 = ocEntropy(tab2);
        h12 = ocEntropy(tab12);


}

void Report::findLift(Relation* rel, double& lift, char*& stateName, double& freq) {
        // To find lift, stateName, and freq:
        // do a tableIteration:
        // * look for the maximal lift
        // * when higher lift found:
        //      * record as best so far
        //      * get the key (for use with keyToUserName)
        //      * get the freq (for printing, and breaking ties)
        // * initialize a sufficiently large keystr (needs to be deleted by client)
        // * print into it with Key::keyToUserStr
}

void Report::printDyadSummary(FILE* fd, Model* model) {
    printf("Summary of dyadic relations for the model %s", model->getPrintName());


    printf(dyadHeader[sepStyle()]);

    bool blue = true;
    
    int relCount = model->getRelationCount();
    for (int i = 0; i < relCount; ++i) {
       

        Relation* rel = model->getRelation(i);
        int varcount = rel->getVariableCount();
        if (varcount != 2) { continue; }

        const char* relName = rel->getPrintName();
 
        double lift = -1;
        char* stateName = nullptr;
        double freq = -1;
        findLift(rel, lift, stateName, freq);
 
        double h1 = -1;
        double h2 = -1;
        double h12 = -1;
        findEntropies(rel, h1, h2, h12);

        double t            = h1 + h2 - h12;
        double tmax         = std::min(h1, h2);
        double tOverTmax    = t / tmax;
        double red12        = t / h1;
        double red21        = t / h2;
        
        const char* blueize = (htmlMode && blue) ? "class=r1" : "";

        printf(dyadFmt[sepStyle()], blueize, relName, stateName, lift, freq, t, tmax, tOverTmax, 100*red12, 100*red21); 
        blue = !blue;   
        //printf("H1: %g, H2: %g, H12: %g\n", h1, h2, h12);

        delete[] stateName;
    }

    printf(dyadFooter[sepStyle()]);


    hl(fd);

}
