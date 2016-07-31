#include "Key.h"
#include "ManagerBase.h"
#include "Report.h"
#include <cstring>
#include "Model.h"

Model* indepModel(ManagerBase* manager) {
    VariableList* varList = manager->getVariableList();
    int varCount = varList->getVarCount();
    Model* newmodel = new Model();
    for (size_t i=0; i < varCount; i++) {
        int var[1]; var[0] = i;
        Relation* rel = manager->getRelation(var, 1, true);
        newmodel->addRelation(rel, true);
    }
    return newmodel;
}

void Report::printResiduals(FILE *fd, Model *model, bool skipTrained, bool skipIVIs) {

    if (manager->getVariableList()->isDirected()) {
        return;
    }

    double adjustConstant = manager->getFunctionConstant() + manager->getNegativeConstant();
    if (!skipTrained) { 
        hl(fd);
        printWholeTable(fd, model, adjustConstant); 
    }

    int relCount = model->getRelationCount();
    if (relCount > 1) {
        for (int i = 0; i < relCount; i++) {
            Relation* rel = model->getRelation(i);
            int varCount = rel->getVariableCount();
            if (varCount > 1) {
                hl(fd);
                printLift(fd, rel, adjustConstant);
            } else if (!skipIVIs) { 
                hl(fd);
                printSingleVariable(fd, rel, adjustConstant);
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

    VariableList *varlist = manager->getVariableList();
    fprintf(fd, "Variable order: ");
    
    long var_count = varlist->getVarCount();
    for (int i = 0; i < var_count; i++) {
        fprintf(fd, "%s", varlist->getVariable(i)->abbrev);
    }

    double sample_size = manager->getSampleSz();


    Model* indep_model = indepModel(manager);
    manager->makeFitTable(indep_model);
    Table* indep_table = manager->getFitTable();

    printTable(fd, NULL, fit_table, input_table, indep_table, adjustConstant, sample_size, false, true);
    printTestData(fd, NULL, fit_table, adjustConstant, keysize, true);

    delete fit_table;
}

void Report::printSingleVariable(FILE* fd, Relation* rel, double adjustConstant) {
    fprintf(fd, "\nMargins for the Variable %s\n", rel->getPrintName());
    printRel(fd, rel, adjustConstant, false);
}

void Report::printLift(FILE* fd, Relation* rel, double adjustConstant) {
    fprintf(fd, "\nLift for the Relation %s\n", rel->getPrintName());

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

    Model* indep_model = indepModel(manager);
    Table* indep_table = new Table(keysize, input_data->getTupleCount());
    manager->makeFitTable(indep_model);
    manager->makeProjection(manager->getFitTable(), indep_table, rel);

    printTable(fd, rel, fit_table, input_table, indep_table, adjustConstant, sample_size, false, false);
    printTestData(fd, rel, fit_table, adjustConstant, keysize, false);
    delete input_table;
    delete indep_table;
}

void Report::printTestData(FILE* fd, Relation* rel, Table* fit_table, double adjustConstant, int keysize, bool printCalc) { 


    Table *test_data = manager->getTestData();
    double test_sample_size = manager->getTestSampleSize();
    if (test_data == NULL || test_sample_size <= 0.0) { return; }
    
    fprintf(fd, "Test Data");
    newl(fd);

    Table* test_table = rel == NULL ? test_data : new Table(keysize, test_data->getTupleCount());
    if (rel) { manager->makeProjection(test_data, test_table, rel); }
    
    printTable(fd, rel, fit_table, test_table, NULL, adjustConstant, test_sample_size, false, printCalc);
    if (rel != NULL) {
        if (test_sample_size > 0.0) {
            delete test_table;
        }
    }

}
