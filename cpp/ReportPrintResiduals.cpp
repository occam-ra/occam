#include "Key.h"
#include "ManagerBase.h"
#include "Report.h"

#include <cstring>

void Report::printResiduals(FILE *fd, Model *model, bool skipTrained) {
    printResiduals(fd, model, NULL, skipTrained);
}

void Report::printResiduals(FILE *fd, Relation *rel, bool skipTrained) {
    printResiduals(fd, NULL, rel, skipTrained);
}

void Report::printResiduals(FILE *fd, Model *model, Relation *rel, bool skipTrainedTable) {
    VariableList *varlist = manager->getVariableList();
    if (varlist->isDirected()) {  return; }
    long var_count = varlist->getVarCount();
    Table *input_data = manager->getInputData();
    Table *test_data = manager->getTestData();
    Table *input_table = NULL, *fit_table = NULL, *test_table = NULL;
    double sample_size = manager->getSampleSz();
    double test_sample_size = manager->getTestSampleSize();
    int keysize = input_data->getKeySize();
    const char *format, *format_r, *header, *header_r, *footer, *traintitle, *testtitle, *delim;
    if (htmlMode)
        fprintf(fd, "<br><br>\n");
    if (rel == NULL) {
        fprintf(fd, "RESIDUALS for model %s\n", model->getPrintName());
        fit_table = manager->getFitTable();
        test_table = test_data;
        input_table = input_data;
    } else if (rel != NULL) {
        fprintf(fd, "\nResiduals for relation %s\n", rel->getPrintName());
        // make refData and testData point to projections
        fit_table = rel->getTable();
        input_table = new Table(keysize, input_data->getTupleCount());
        manager->makeProjection(input_data, input_table, rel);
        if (test_data != NULL && test_sample_size > 0.0) {
            test_table = new Table(keysize, test_data->getTupleCount());
            manager->makeProjection(test_data, test_table, rel);
        }
    }
    if (fit_table == NULL) {
        fprintf(fd, "Error: no fitted table computed\n");
        return;
    }
    if (htmlMode)
        fprintf(fd, "<br>");
    //-- set appropriate format
    int sepStyle = htmlMode ? 0 : separator;
    switch (sepStyle) {
        case 0:
            header =
                    "<table border=1 cellspacing=0 cellpadding=0><tr><th>Cell</th><th>Obs.Prob.</th><th>Obs.Freq.</th><th>Calc.Prob.</th><th>Calc.Freq.</th><th>Residual</th></tr>\n";
            header_r =
                    "<table border=1 cellspacing=0 cellpadding=0><tr><th>Cell</th><th>Obs.Prob.</th><th>Obs.Freq.</th></tr>\n";
            traintitle = "<br>Training Data\n";
            testtitle = "Test Data\n";
            format =
                    "<tr><td>%s</td><td>%#6.8g</td><td>%#6.8g</td><td>%#6.8g</td><td>%#6.8g</td><td>%+#6.8g</td></tr>\n";
            format_r = "<tr><td>%s</td><td>%#6.8g</td><td>%#6.8g</td></tr>\n";
            footer = "</table><br><br>";
            delim = " ";
            break;
        case 1:
            header = "Cell\tObs.Prob.\tObs.Freq.\tCalc.Prob.\tCalc.Freq.\tResidual\n";
            header_r = "Cell\tObs.Prob.\tObs.Freq.\n";
            traintitle = "\nTraining Data\n";
            testtitle = "\nTest Data\n";
            format = "%s\t%#6.8g\t%#6.8g\t%#6.8g\t%#6.8g\t%#6.8g\n";
            format_r = "%s\t%#6.8g\t%#6.8g\n";
            footer = "";
            delim = "\t";
            break;
        case 2:
            header = "Cell,Obs.Prob.,Obs.Freq.,Calc.Prob.,Calc.Freq.,Residual\n";
            header_r = "Cell,Obs.Prob.,Obs.Freq.\n";
            traintitle = "\nTraining Data\n";
            testtitle = "\nTest Data\n";
            format = "%s,%#6.8g,%#6.8g,%#6.8g,%#6.8g,%#6.8g\n";
            format_r = "%s,%#6.8g,%#6.8g\n";
            footer = "";
            delim = ",";
            break;
        case 3:
            header =
                    " Cell   Obs.Prob.    Obs.Freq.    Calc.Prob.    Calc.Freq.    Residual\n    ---------------------------------------------\n";
            header_r =
                    " Cell   Obs.Prob.    Obs.Freq.\n    ---------------------------------------------\n";
            traintitle = "\nTraining Data\n";
            testtitle = "\nTest Data\n";
            format = "%8s  %#6.8g   %#6.8g   %#6.8g   %#6.8g   %#6.8g\n";
            format_r = "%8s  %#6.8g   %#6.8g\n";
            footer = "";
            delim = " ";
            break;
    }
    if (rel != NULL)
        header = header_r;
    char* keystr = new char[var_count * (MAXABBREVLEN + strlen(delim)) + 1];
    if (rel == NULL) {
        if (htmlMode)
            fprintf(fd, "<br>\n");
        fprintf(fd, "Variable order: ");
        for (int i = 0; i < var_count; i++) {
            fprintf(fd, "%s", varlist->getVariable(i)->abbrev);
        }
        fprintf(fd, "\n");
        if (htmlMode)
            fprintf(fd, "<br>");
    }
    long long index, refindex, compare;
    KeySegment *refkey, *key;
    double value, refvalue, res;
    double adjustConstant = manager->getFunctionConstant() + manager->getNegativeConstant();
    // Walk through both lists. Missing values are zero.
    // We don't print anything if missing in both lists.
    index = 0;
    refindex = 0;

    auto tableAction = [&](Relation* rel, long long index, double value, KeySegment* refkey, double refvalue) {
        char* keystr = new char[var_count * (MAXABBREVLEN + strlen(delim)) + 1];
        Key::keyToUserString(refkey, varlist, keystr, delim);
        if (rel == NULL) {
            double res = value - refvalue;
            fprintf(fd, format, keystr, refvalue, refvalue * sample_size - adjustConstant, value,
                    value * sample_size - adjustConstant, res);
        } else if(rel != NULL) { fprintf(fd, format_r, keystr, refvalue, refvalue * sample_size - adjustConstant); }
        delete[] keystr;
    };

    if (rel != NULL || !skipTrainedTable) {
        fprintf(fd, traintitle);
        for (int i = 1; i < var_count; i++) {
            fprintf(fd, delim);
        }
        fprintf(fd, header);
        tableIteration(input_table, varlist, rel, fit_table, var_count, tableAction);  
        printf(footer);
    }
    if (test_table != NULL) {
        fprintf(fd, testtitle);
        for (int i = 1; i < var_count; i++) {
            fprintf(fd, delim);
        }
        fprintf(fd, header);
        long long testCount = test_table->getTupleCount();
        int *key_order = new int[testCount];
        for (long long i = 0; i < testCount; i++) {
            key_order[i] = i;
        }
        sort_count = var_count;
        sort_table = test_table;
        qsort(key_order, testCount, sizeof(int), sortKeys);
        for (long long order_i = 0; order_i < testCount; order_i++) {
            long long i = key_order[order_i];
            refkey = test_table->getKey(i);
            refvalue = test_table->getValue(i);
            Key::keyToUserString(refkey, varlist, keystr, delim);
            if (rel == NULL) {
                index = fit_table->indexOf(refkey, true);
                if (index == -1) {
                    value = 0.0;
                } else {
                    value = fit_table->getValue(index);
                }
                res = value - refvalue;
                fprintf(fd, format, keystr, refvalue, refvalue * test_sample_size - adjustConstant, value,
                        value * test_sample_size - adjustConstant, res);
            } else {
                fprintf(fd, format_r, keystr, refvalue, refvalue * test_sample_size - adjustConstant);
            }
        }
        fprintf(fd, footer);
    }
    delete keystr;
    if (rel != NULL) {
        if (test_sample_size > 0.0) {
            delete test_table;
        }
        delete input_table;
    } else {
        if (model->getRelationCount() > 1) {
            for (int i = 0; i < model->getRelationCount(); i++) {
                printResiduals(fd, model->getRelation(i), skipTrainedTable);
            }
        }
    }
}


