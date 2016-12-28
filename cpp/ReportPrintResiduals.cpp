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
    if (!skipTrained) { 
        printWholeTable(fd, model, adjustConstant); 
        hl(fd);
    }


    int relCount = model->getRelationCount();
    if (relCount > 1) {
        printSummary(fd, model, adjustConstant);
        hl(fd);
        for (int i = 0; i < relCount; i++) {
            Relation* rel = model->getRelation(i);
            int varCount = rel->getVariableCount();
            if (varCount > 1) {
                printLift(fd, rel, adjustConstant);
                hl(fd);
            } else if (!skipIVIs) { 
                printSingleVariable(fd, rel, adjustConstant);
                hl(fd);
            }
        }
        newl(fd);
    }   
}

void Report::printWholeTable(FILE* fd, Model* model, double adjustConstant) {
    fprintf(fd, "Residuals for all states for the Model %s\n", model->getPrintName());
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

    // make refData and testData point to projections
    Table* fit_table = rel->getTable();

    Table* input_data = manager->getInputData(); 
    double sample_size = manager->getSampleSz();

    int keysize = input_data->getKeySize();
    Table* input_table = new Table(keysize, input_data->getTupleCount());
    manager->makeProjection(input_data, input_table, rel);

    Table* indep_table0 = manager->getIndepTable();
    int ikeysize = indep_table0->getKeySize();
    Table* indep_table = new Table(ikeysize, indep_table0->getTupleCount());
    manager->makeProjection(indep_table0, indep_table, rel);



    printTable(fd, rel, fit_table, input_table, indep_table, adjustConstant, sample_size, printLift, false);
    printTestData(fd, rel, fit_table, adjustConstant, keysize, false);
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
 
    Table* indep_table0 = manager->getIndepTable();
    int ikeysize = indep_table0->getKeySize();
    Table* indep_table = rel == NULL ? indep_table0 : new Table(ikeysize, indep_table0->getTupleCount());
    if (rel) {
        manager->makeProjection(indep_table0, indep_table, rel);
    }

    printTable(fd, rel, fit_table, test_table, indep_table, adjustConstant, test_sample_size, false, printCalc);
    if (rel != NULL) {
        if (test_sample_size > 0.0) {
            delete test_table;
        }
    }

}


void Report::printSummary(FILE* fd, Model* model, double adjustConstant) {
    fprintf(fd, "Lift for the Model %s (summarizing over IVIs)\n", model->getPrintName());
    newl(fd);


    // THIS IS THE KEY TO THIS SUMMARY:
    // `rel` is a relation holding all of the relevant variables.
    int var_count = manager->getVariableList()->getVarCount();
    int var_indices[var_count], return_count;
    manager->getRelevantVars(model, var_indices, return_count, true);
    Relation *rel = manager->getRelation(var_indices, return_count);

    // make refData and testData point to projections
    Table* fit_table = rel->getTable();

    Table* input_data = manager->getInputData(); 
    double sample_size = manager->getSampleSz();

    int keysize = input_data->getKeySize();
    Table* input_table = new Table(keysize, input_data->getTupleCount());
    manager->makeProjection(input_data, input_table, rel);

    Table* indep_table0 = manager->getIndepTable();
    int ikeysize = indep_table0->getKeySize();
    Table* indep_table = new Table(ikeysize, indep_table0->getTupleCount());
    manager->makeProjection(indep_table0, indep_table, rel);

    printTable(fd, rel, fit_table, input_table, indep_table, adjustConstant, sample_size, true, true);
    printTestData(fd, rel, fit_table, adjustConstant, keysize, true);

    delete input_table;

}
