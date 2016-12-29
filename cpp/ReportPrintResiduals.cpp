#include "Key.h"
#include "ManagerBase.h"
#include "Report.h"
#include <cstring>
#include "Model.h"

void Report::printResiduals(FILE *fd, Model *model, bool skipTrained, bool skipIVIs) {

    if (manager->getVariableList()->isDirected()) {
        return;
    }

    double adjustConstant = manager->getFunctionConstant() + manager->getNegativeConstant();

    int relCount = model->getRelationCount();
    int trueRelCount = 0;

    // first pass: figure out true rel count
    if (relCount > 1) {
        for (int i = 0; i < relCount; i++) {
            Relation* rel = model->getRelation(i);
            int varCount = rel->getVariableCount();
            if (varCount > 1) { trueRelCount += 1; }
        }
    }   

    // print summary (unless the whole data is "just as good")
    if (trueRelCount > 1 && trueRelCount != relCount) {
        printSummary(fd, model, adjustConstant);
        hl(fd);
    }

    // second pass: print all relations    

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

    // third pass: print single variables
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
    printTestData(fd, NULL, fit_table, adjustConstant, keysize, true);

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
    printTestData(fd, rel, nullptr, adjustConstant, keysize, false);
    delete input_table;
}

void Report::printTestData(FILE* fd, Relation* rel, Table* fit_table, double adjustConstant, int keysize, bool printCalc) { 
    
    

    Table *test_data = manager->getTestData();
    double test_sample_size = manager->getTestSampleSize();
    if (test_data == NULL || test_sample_size <= 0.0) { return; }
    
    fprintf(fd, "Test Data");
    newl(fd);

    Table* test_table = rel == NULL ? test_data : new Table(keysize, test_data->getTupleCount());
    if (rel) { manager->makeProjection(test_data, test_table, rel); }

   // TODO 

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
    printTestData(fd, rel, nullptr, adjustConstant, keysize, false);
    delete input_table;


}
