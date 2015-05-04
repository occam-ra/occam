#include "Key.h"
#include "Report.h"
#include "ManagerBase.h"
#include <cstring>
#include <cmath>
#include "Math.h"
#include <climits>

void Report::printConditional_DV(FILE *fd, Model *model, bool calcExpectedDV, char* classTarget) {
    printConditional_DV(fd, model, NULL, calcExpectedDV, classTarget);
}

void Report::printConditional_DV(FILE *fd, Relation *rel, bool calcExpectedDV, char* classTarget) {
    printConditional_DV(fd, NULL, rel, calcExpectedDV, classTarget);
}

void Report::printConditional_DV(FILE *fd, Model *model, Relation *rel, bool calcExpectedDV, char* classTarget) {
    if (model == NULL && rel == NULL) {
        fprintf(fd, "No model or relation specified.\n");
        return;
    }
    Table *input_data = manager->getInputData();
    Table *test_data = manager->getTestData();
    Table *fit_table;
    double sample_size = manager->getSampleSz();
    double test_sample_size = manager->getTestSampleSize();
    VariableList *var_list = manager->getVariableList();
    if (!var_list->isDirected())
        return;

    int dv_index = var_list->getDV(); // Get the first DV's index
    Variable *dv_var = var_list->getVariable(dv_index); // Get the (first) DV itself
    int var_count = var_list->getVarCount(); // Get the number of variables
    int key_size = input_data->getKeySize(); // Get the key size from the reference data
    int dv_card = dv_var->cardinality; // Get the cardinality of the DV
    double dv_bin_value[dv_card]; // Contains the DV values for calculating expected values.

    Table *input_table, *test_table = NULL;
    Relation *iv_rel; // A pointer to the IV component of a model, or the relation itself
    Model *relModel;

    input_table = new Table(key_size, input_data->getTupleCount());
    if (test_sample_size > 0.0)
        test_table = new Table(key_size, test_data->getTupleCount());
    if (rel == NULL) {
        Table* orig_table = manager->getFitTable();
        if (orig_table == NULL) {
            fprintf(fd, "Error: no fitted table computed.\n");
            return;
        }
        int var_indices[var_count], return_count;
        manager->getPredictingVars(model, var_indices, return_count, true);
        Relation *predRelWithDV = manager->getRelation(var_indices, return_count);

        fit_table = new Table(key_size, orig_table->getTupleCount());
        manager->makeProjection(orig_table, fit_table, predRelWithDV);
        manager->makeProjection(input_data, input_table, predRelWithDV);
        if (test_sample_size > 0.0)
            manager->makeProjection(test_data, test_table, predRelWithDV);
        //iv_rel = model->getRelation(0);
        iv_rel = predRelWithDV;
    } else {        // Else, if we are working with a relation, make projections of the input and test tables.
        if (rel->isStateBased()) {
            relModel = new Model(3);            // make a model of IV and the relation and the DV
            relModel->addRelation(manager->getIndRelation());
            relModel->addRelation(rel);
            relModel->addRelation(manager->getDepRelation());
            // make a fit table for the model
            manager->makeFitTable(relModel);
            // point table links to this new model
            Table* orig_table = manager->getFitTable();
            if (orig_table == NULL) {
                fprintf(fd, "Error: no fitted table computed.\n");
                return;
            }
            int var_indices[var_count], return_count;
            manager->getPredictingVars(relModel, var_indices, return_count, true);
            Relation *predRelWithDV = manager->getRelation(var_indices, return_count);
            fit_table = new Table(key_size, orig_table->getTupleCount());
            manager->makeProjection(orig_table, fit_table, predRelWithDV);
            manager->makeProjection(input_data, input_table, predRelWithDV);
            if (test_sample_size > 0.0)
                manager->makeProjection(test_data, test_table, predRelWithDV);
            iv_rel = predRelWithDV;
        } else {
            fit_table = rel->getTable();
            manager->makeProjection(input_data, input_table, rel);
            if (test_sample_size > 0.0)
                manager->makeProjection(test_data, test_table, rel);
            iv_rel = rel;
        }
    }

    bool use_alt_default = false;
    Table *alt_table;
    Relation *alt_relation;
    int alt_indices[var_count], alt_var_count;
    int alt_missing_indices[var_count], alt_missing_count;
    if (rel != NULL)
        defaultFitModel = NULL; // Only consider the alternate default model for the main model, not the component relations.
    if (defaultFitModel != NULL) {
        // Check that the alternate model is below the main model on the lattice, and not equal to it.
        if ((model != defaultFitModel) && model->containsModel(defaultFitModel)) {
            use_alt_default = true;
            // If things are okay, make the alternate default table and project it to the active variables
            manager->getPredictingVars(defaultFitModel, alt_indices, alt_var_count, true);
            alt_relation = manager->getRelation(alt_indices, alt_var_count);
            alt_table = new Table(key_size, fit_table->getTupleCount());
            manager->makeProjection(fit_table, alt_table, alt_relation);
            // Now get a list of the missing variables from the relation, for use in breaking ties later
            alt_missing_count = alt_relation->copyMissingVariables(alt_missing_indices, var_count);
        }
    }

    int iv_statespace = ((int) manager->computeDF(iv_rel) + 1) / dv_card; // iv_rel statespace divided by cardinality of the DV
    const char **dv_label = (const char**) dv_var->valmap;
    KeySegment **fit_key = new KeySegment *[iv_statespace];
    double **fit_prob = new double *[iv_statespace];
    double *fit_dv_prob = new double[dv_card];
    double *fit_key_prob = new double[iv_statespace];
    int *fit_rule = new int[iv_statespace];
    bool *fit_tied = new bool[iv_statespace];
    double *fit_dv_expected = new double[iv_statespace];
    KeySegment **alt_key = new KeySegment *[iv_statespace];
    double **alt_prob = new double *[iv_statespace];
    double *alt_key_prob = new double[iv_statespace];
    int *alt_rule = new int[iv_statespace];
    KeySegment **input_key = new KeySegment *[iv_statespace];
    double **input_freq = new double *[iv_statespace];
    double *input_dv_freq = new double[dv_card];
    double *input_key_freq = new double[iv_statespace];
    //int *input_rule = new int[iv_statespace];
    KeySegment **test_key;
    double **test_freq;
    double *test_dv_freq;
    double *test_key_freq;
    int *test_rule;
    if (test_sample_size > 0) {
        test_key = new KeySegment *[iv_statespace];
        test_freq = new double *[iv_statespace];
        test_dv_freq = new double[dv_card];
        test_key_freq = new double[iv_statespace];
        test_rule = new int[iv_statespace];
    }

    // Training and test confusion matrix values
    double trtp, trfp, trtn, trfn, tetp, tefp, tetn, tefn;

    // Allocate space for keys and frequencies
    KeySegment *temp_key;
    double *temp_double_array;
    for (int i = 0; i < iv_statespace; i++) {
        fit_key_prob[i] = 0.0;
        alt_key_prob[i] = 0.0;
        input_key_freq[i] = 0.0;
        fit_dv_expected[i] = 0.0;

        temp_key = new KeySegment[key_size];
        for (int j = 0; j < key_size; j++)
            temp_key[j] = DONT_CARE;
        fit_key[i] = temp_key;

        temp_key = new KeySegment[key_size];
        for (int j = 0; j < key_size; j++)
            temp_key[j] = DONT_CARE;
        alt_key[i] = temp_key;

        temp_key = new KeySegment[key_size];
        for (int j = 0; j < key_size; j++)
            temp_key[j] = DONT_CARE;
        input_key[i] = temp_key;

        temp_double_array = new double[dv_card];
        for (int k = 0; k < dv_card; k++)
            temp_double_array[k] = 0.0;
        fit_prob[i] = temp_double_array;

        temp_double_array = new double[dv_card];
        for (int k = 0; k < dv_card; k++)
            temp_double_array[k] = 0.0;
        alt_prob[i] = temp_double_array;

        temp_double_array = new double[dv_card];
        for (int k = 0; k < dv_card; k++)
            temp_double_array[k] = 0.0;
        input_freq[i] = temp_double_array;
    }
    if (test_sample_size > 0.0) {
        for (int i = 0; i < iv_statespace; i++) {
            test_key_freq[i] = 0.0;

            temp_key = new KeySegment[key_size];
            for (int j = 0; j < key_size; j++)
                temp_key[j] = DONT_CARE;
            test_key[i] = temp_key;

            temp_double_array = new double[dv_card];
            for (int k = 0; k < dv_card; k++)
                temp_double_array[k] = 0.0;
            test_freq[i] = temp_double_array;
        }
    }

    for (int i = 0; i < dv_card; i++) {
        fit_dv_prob[i] = 0.0;
        input_dv_freq[i] = 0.0;
        if (test_sample_size > 0.0)
            test_dv_freq[i] = 0.0;
    }

    if (calcExpectedDV) {
        for (int i = 0; i < dv_card; i++)
            dv_bin_value[i] = strtod(dv_label[i], (char **) NULL);
    }

    const char *new_line = "\n", *blank_line = "\n";
    if (htmlMode) {
        new_line = "<br>\n";
        blank_line = "<br><br>\n";
    }

    const char *block_start, *head_start, *head_sep, *head_end, *head_str1, *head_str2, *head_str3, *head_str4;
    const char *row_start, *block_end, *row_start2, *row_start3, *row_end, *row_sep, *row_sep2, *line_sep;

    // Set appropriate format
    int sep_style = htmlMode ? 0 : separator;
    switch (sep_style) {
        case 0:
            block_start = "<table border=0 cellpadding=0 cellspacing=0>\n";
            head_start = "<tr><th>";
            head_sep = "</th><th>";
            head_end = "</th></tr>\n";
            head_str1 = "</th><th colspan=2 class=r1>calc.&nbsp;q(DV|IV)";
            head_str2 = "</th><th colspan=2 class=r1>obs.&nbsp;p(DV|IV)"; // used twice
            head_str3 = "</th><th colspan=2>%%correct";
            head_str4 = "</th><th colspan=2>Test&nbsp;Data";
            row_start = "<tr><td align=right>";
            row_start2 = "<tr class=r1><td align=right>";
            row_start3 = "<tr class=em><td align=right>";
            row_sep = "</td><td align=right>";
            row_sep2 = "</td><td align=left>";
            row_end = "</td></tr>\n";
            block_end = "</table><br>\n";
            line_sep = "<hr>\n";
            break;
        case 1:
            block_start = "";
            head_start = "";
            head_sep = "\t";
            head_end = "\n";
            head_str1 = "\tcalc. q(DV|IV)\t";
            head_str2 = "\tobs. p(DV|IV)\t";
            head_str3 = "\t%%correct\t";
            head_str4 = "\tTest Data\t";
            row_start = row_start2 = row_start3 = "";
            row_sep = row_sep2 = "\t";
            row_end = "\n";
            block_end = "\n";
            line_sep = "-------------------------------------------------------------------------\n";
            break;
        case 2:
            block_start = "";
            head_start = "";
            head_sep = ",";
            head_end = "\n";
            head_str1 = ",calc. q(DV|IV),";
            head_str2 = ",obs. p(DV|IV),";
            head_str3 = ",%%correct,";
            head_str4 = ",Test Data,";
            row_start = row_start2 = row_start3 = "";
            row_sep = row_sep2 = ",";
            row_end = "\n";
            block_end = "\n";
            line_sep = "-------------------------------------------------------------------------\n";
            break;
        case 3:
            block_start = "";
            head_start = "";
            head_sep = "    ";
            head_end = "\n";
            head_str1 = "calc. q(DV|IV)";
            head_str2 = "obs. p(DV|IV)";
            head_str3 = "%%correct";
            head_str4 = "Test Data";
            row_start = row_start2 = row_start3 = "";
            row_sep = row_sep2 = "    ";
            row_end = "\n";
            block_end = "\n";
            line_sep = "-------------------------------------------------------------------------\n";
            break;
    }
    if (rel != NULL)
        fprintf(fd, "%s%s%s", blank_line, line_sep, blank_line);

    int *ind_vars = new int[var_count];
    int iv_count = iv_rel->getIndependentVariables(ind_vars, var_count);
    if (rel == NULL) {
        fprintf(fd, "Conditional DV (D) (%%) for each IV composite state for the Model %s.", model->getPrintName());
        fprintf(fd, new_line);
        fprintf(fd, "IV order: ");
        for (int i = 0; i < iv_count; i++) {
            fprintf(fd, "%s", var_list->getVariable(ind_vars[i])->abbrev);
        }
        fprintf(fd, " (");
        for (int i = 0; i < iv_count; i++) {
            if (i > 0)
                fprintf(fd, "; ");
            fprintf(fd, "%s", var_list->getVariable(ind_vars[i])->name);
        }
        fprintf(fd, ").");
    } else {
        if (rel->isStateBased()) {
            fprintf(fd, "Conditional DV (D) (%%) for each IV composite state for the Submodel %s.", relModel->getPrintName());
            fprintf(fd, new_line);
//            fprintf(fd, "(For component relations, the Data and Model parts of the table are equal, so only one is given.)");
        } else {
            fprintf(fd, "Conditional DV (D) (%%) for each IV composite state for the Relation %s.", rel->getPrintName());
            fprintf(fd, new_line);
            fprintf(fd, "(For component relations, the Data and Model parts of the table are equal, so only one is given.)");
        }
    }
    if (defaultFitModel != NULL) {
        fprintf(fd, new_line);
        if (use_alt_default == false) {
            if (model == defaultFitModel) {
                fprintf(fd,
                        "The specified alternate default model cannot be identical to the fitted model. Using independence model instead.");
            } else {
                fprintf(fd,
                        "The specified alternate default model is not a child of the fitted model. Using independence model instead.");
            }
        } else {
            fprintf(fd, "Using %s as alternate default model.", defaultFitModel->getPrintName());
        }
    }
    fprintf(fd, blank_line);

    int index = 0;
    int keys_found = 0;
    int alt_keys_found = 0;
    KeySegment *key;
    double temp_value;
    long *index_sibs = new long[dv_card];
    int key_compare, num_sibs;

    int fit_table_size = fit_table->getTupleCount();
    int input_table_size = input_table->getTupleCount();
    int alt_table_size = 0;
    if (use_alt_default) {
        alt_table_size = alt_table->getTupleCount();
    }
    int test_table_size = 0;
    if (test_sample_size > 0.0) {
        test_table_size = test_table->getTupleCount();
    }
    int dv_value, best_i;

    // Count up the total frequencies for each DV value in the reference data, for the output table.
    for (int i = 0; i < input_table_size; i++) {
        temp_key = input_table->getKey(i);
        dv_value = Key::getKeyValue(temp_key, key_size, var_list, dv_index);
        input_dv_freq[dv_value] += input_table->getValue(i) * sample_size;
    }

    // Find the most common DV value, for test data predictions when no input data exists.
    int input_default_dv = manager->getDefaultDVIndex();

    for (int i = 0; i < iv_statespace; i++) {
        fit_rule[i] = input_default_dv;
        alt_rule[i] = input_default_dv;
        fit_tied[i] = false;
        if (test_sample_size > 0.0)
            test_rule[i] = input_default_dv;
    }

    KeySegment *temp_key_array = new KeySegment[key_size];
    double f1, f2;
    double precision = 1.0e10;

    // Work out the alternate default table, if requested
    if (use_alt_default) {
        while (alt_keys_found < iv_statespace) {
            if (index >= alt_table_size)
                break;

            key = alt_table->getKey(index);
            index++;
            memcpy((int *) temp_key_array, (int *) key, key_size * sizeof(KeySegment));
            Key::setKeyValue(temp_key_array, key_size, var_list, dv_index, DONT_CARE);

            key_compare = 1;
            for (int i = 0; i < alt_keys_found; i++) {
                key_compare = Key::compareKeys((KeySegment *) alt_key[i], temp_key_array, key_size);
                if (key_compare == 0)
                    break;
            }
            if (key_compare == 0)
                continue;
            memcpy((int *) alt_key[alt_keys_found], (int *) temp_key_array, sizeof(KeySegment) * key_size);
            num_sibs = 0;
            Key::getSiblings(key, var_list, alt_table, index_sibs, dv_index, &num_sibs);
            best_i = 0;
            temp_value = 0.0;
            for (int i = 0; i < num_sibs; i++) {
                temp_value += alt_table->getValue(index_sibs[i]);
                KeySegment *temp_key = alt_table->getKey(index_sibs[i]);
                dv_value = Key::getKeyValue(temp_key, key_size, var_list, dv_index);
                alt_prob[alt_keys_found][dv_value] = alt_table->getValue(index_sibs[i]);
                if (i == 0) {
                    best_i = dv_value;
                } else {
                    f1 = round(alt_prob[alt_keys_found][dv_value] * precision);
                    f2 = round(alt_prob[alt_keys_found][best_i] * precision);
                    if (f1 > f2) {
                        best_i = dv_value;
                    } else if (fabs(f1 - f2) < 1) {
                        if (manager->getDvOrder(best_i) > manager->getDvOrder(dv_value))
                            best_i = dv_value;
                    }
                }
            }
            alt_key_prob[alt_keys_found] = temp_value;
            alt_rule[alt_keys_found] = best_i;
            alt_keys_found++;
        }
    }

    bool tie_flag;
    index = 0;
    // Loop till we have as many keys as the size of the IV statespace (at most)
    while (keys_found < iv_statespace) {
        // Also break the loop if index exceeds the tupleCount for the table
        if (index >= fit_table_size)
            break;

        // Get the key and value for the current index
        key = fit_table->getKey(index);
        index++;
        memcpy((int *) temp_key_array, (int *) key, key_size * sizeof(KeySegment));
        Key::setKeyValue(temp_key_array, key_size, var_list, dv_index, DONT_CARE);

        // Check if this key has appeared yet
        key_compare = 1;
        for (int i = 0; i < keys_found; i++) {
            key_compare = Key::compareKeys((KeySegment *) fit_key[i], temp_key_array, key_size);
            // If zero is returned, keys are equal, meaning this key has appeared before.  Stop checking.
            if (key_compare == 0)
                break;
        }
        // If this was a duplicate key, move on to the next index.
        if (key_compare == 0)
            continue;
        // Otherwise, this is a new key.  Place it into the keylist
        memcpy((int *) fit_key[keys_found], (int *) temp_key_array, sizeof(KeySegment) * key_size);

        // Get the siblings of the key
        num_sibs = 0;
        Key::getSiblings(key, var_list, fit_table, index_sibs, dv_index, &num_sibs);

        tie_flag = false;
        best_i = 0;
        temp_value = 0.0;
        for (int i = 0; i < num_sibs; i++) {
            // Sum up the total probability values among the siblings
            temp_value += fit_table->getValue(index_sibs[i]);
            // Get the key for this sibling
            KeySegment *temp_key = fit_table->getKey(index_sibs[i]);
            // Get the dv_value for the sibling
            dv_value = Key::getKeyValue(temp_key, key_size, var_list, dv_index);
            // Compute & store the conditional value for the sibling (in probability)
            fit_prob[keys_found][dv_value] = fit_table->getValue(index_sibs[i]);
            // Next keep track of what the best number correct is
            // (ie, if this is the first sib, it's the best.  After that, compare & keep the best.)
            if (i == 0) {
                best_i = dv_value;
            } else {
                // Probabilities are rounded so checks for gt/lt/eq are not skewed by the imprecision in floating point numbers.
                f1 = round(fit_prob[keys_found][dv_value] * precision);
                f2 = round(fit_prob[keys_found][best_i] * precision);
                if (f1 > f2) {
                    best_i = dv_value;
                    tie_flag = false;
                    // If there is a tie, break it by choosing the DV state that was most common in the input data.
                    // If there is a tie in frequency, break it alphabetically, using the actual DV values.
                } else if (fabs(f1 - f2) < 1) {
                    tie_flag = true;
                    if (use_alt_default) {
                        // use temp_key_array, which still contains the current key without the DV
                        // mark unused variables in key as don't care
                        for (int j = 0; j < alt_missing_count; j++)
                            Key::setKeyValue(temp_key_array, key_size, var_list, alt_missing_indices[j], DONT_CARE);
                        // find the key in the alt table
                        for (int j = 0; j < alt_keys_found; j++) {
                            key_compare = Key::compareKeys((KeySegment *) alt_key[j], temp_key_array, key_size);
                            if (key_compare == 0) {
                                // if present, compare the alt values for best_i and dv_value
                                f1 = round(alt_prob[j][dv_value] * precision);
                                f2 = round(alt_prob[j][best_i] * precision);
                                if (f1 > f2)
                                    best_i = dv_value;
                                else if (fabs(f1 - f2) < 1)
                                    // there is a tie in the alternate default as well, so revert to independence
                                    if (manager->getDvOrder(best_i) > manager->getDvOrder(dv_value))
                                        best_i = dv_value;
                                break;
                            }
                        }
                        // if the key was not found in the alt default table, revert to independence
                        if (key_compare != 0)
                            if (manager->getDvOrder(best_i) > manager->getDvOrder(dv_value))
                                best_i = dv_value;
                    } else {
                        if (manager->getDvOrder(best_i) > manager->getDvOrder(dv_value))
                            best_i = dv_value;
                    }
                }
            }
        }
        // Save the total probability for these siblings.
        fit_key_prob[keys_found] = temp_value;
        // Save the final best rule's index.
        fit_rule[keys_found] = best_i;
        fit_tied[keys_found] = tie_flag;
        // And move on to the next key...
        keys_found++;
    }

    // Sort out the input (reference) data
    // Loop through all the input data
    int input_counter = 0;
    index = 0;
    int fit_index = 0;
    while (input_counter < iv_statespace) {
        if (index >= input_table_size)
            break;

        key = input_table->getKey(index);
        index++;
        memcpy((int *) temp_key_array, (int *) key, key_size * sizeof(KeySegment));
        Key::setKeyValue(temp_key_array, key_size, var_list, dv_index, DONT_CARE);

        // Check if this key has appeared yet -- we only do this so siblings aren't counted multiple times.
        key_compare = 1;
        for (int i = 0; i < input_counter; i++) {
            key_compare = Key::compareKeys((KeySegment *) input_key[i], temp_key_array, key_size);
            if (key_compare == 0)
                break;
        }
        // If this was a duplicate, move on
        if (key_compare == 0)
            continue;
        // Otherwise, the key is new to the input list, we add it into the list.
        memcpy((int *) input_key[input_counter], (int *) temp_key_array, sizeof(KeySegment) * key_size);

        // Next, find out if the index of this key is in the fit_key list, to keep the keys in the same order
        for (fit_index = 0; fit_index < keys_found; fit_index++) {
            key_compare = Key::compareKeys((KeySegment *) fit_key[fit_index], temp_key_array, key_size);
            if (key_compare == 0)
                break;
        }
        // If the key wasn't found, we must add it to the fit list as well
        if (key_compare != 0) {
            memcpy((int *) fit_key[keys_found], (int *) temp_key_array, sizeof(KeySegment) * key_size);
            if (use_alt_default) {
                for (int j = 0; j < alt_missing_count; j++)
                    Key::setKeyValue(temp_key_array, key_size, var_list, alt_missing_indices[j], DONT_CARE);
                for (int j = 0; j < alt_keys_found; j++) {
                    key_compare = Key::compareKeys((KeySegment *) alt_key[j], temp_key_array, key_size);
                    if (key_compare == 0)
                        fit_rule[keys_found] = alt_rule[j];
                }
            }
            fit_tied[keys_found] = true;
            fit_index = keys_found;
            keys_found++;
        }

        // Get the siblings of this key
        num_sibs = 0;
        Key::getSiblings(key, var_list, input_table, index_sibs, dv_index, &num_sibs);

        temp_value = 0.0;
        for (int i = 0; i < num_sibs; i++) {
            // Sum up the total frequencies among the siblings
            temp_value += input_table->getValue(index_sibs[i]);
            KeySegment *temp_key = input_table->getKey(index_sibs[i]);
            dv_value = Key::getKeyValue(temp_key, key_size, var_list, dv_index);
            input_freq[fit_index][dv_value] = input_table->getValue(index_sibs[i]) * sample_size;
        }
        input_key_freq[fit_index] = temp_value * sample_size;
        input_counter++;
    }

    // Compute performance on test data, if present
    // This section will reuse many of the variables from above, since it is performing a similar task.
    if (test_sample_size > 0.0) {
        int test_counter = 0;
        index = 0;
        fit_index = 0;
        while (test_counter < iv_statespace) {
            if (index >= test_table_size)
                break;

            key = test_table->getKey(index);
            index++;
            memcpy((int *) temp_key_array, (int *) key, key_size * sizeof(KeySegment));
            Key::setKeyValue(temp_key_array, key_size, var_list, dv_index, DONT_CARE);

            // Check if this key has appeared yet -- we only do this so siblings aren't counted multiple times.
            key_compare = 1;
            for (int i = 0; i < test_counter; i++) {
                key_compare = Key::compareKeys((KeySegment *) test_key[i], temp_key_array, key_size);
                if (key_compare == 0)
                    break;
            }
            // If this was a duplicate, move on
            if (key_compare == 0)
                continue;
            // Otherwise, the key is new to the test list, we add it into the list.
            memcpy((int *) test_key[test_counter], (int *) temp_key_array, sizeof(KeySegment) * key_size);

            // Next, find out the index of this key in the fit_key list, to keep the keys in the same order
            for (fit_index = 0; fit_index < keys_found; fit_index++) {
                key_compare = Key::compareKeys((KeySegment *) fit_key[fit_index], temp_key_array, key_size);
                if (key_compare == 0)
                    break;
            }
            // If the key wasn't found, we must add it to the fit list as well
            if (key_compare != 0) {
                memcpy((int *) fit_key[keys_found], (int *) temp_key_array, sizeof(KeySegment) * key_size);
                if (use_alt_default) {
                    for (int j = 0; j < alt_missing_count; j++)
                        Key::setKeyValue(temp_key_array, key_size, var_list, alt_missing_indices[j], DONT_CARE);
                    for (int j = 0; j < alt_keys_found; j++) {
                        key_compare = Key::compareKeys((KeySegment *) alt_key[j], temp_key_array, key_size);
                        if (key_compare == 0)
                            fit_rule[keys_found] = alt_rule[j];
                    }
                }
                fit_tied[keys_found] = true;
                fit_index = keys_found;
                keys_found++;
            }

            // Get the siblings of this key
            num_sibs = 0;
            Key::getSiblings(key, var_list, test_table, index_sibs, dv_index, &num_sibs);

            best_i = 0;
            temp_value = 0.0;
            for (int i = 0; i < num_sibs; i++) {
                // Sum up the total frequencies among the siblings
                temp_value += test_table->getValue(index_sibs[i]);
                KeySegment *temp_key = test_table->getKey(index_sibs[i]);
                dv_value = Key::getKeyValue(temp_key, key_size, var_list, dv_index);
                test_freq[fit_index][dv_value] = test_table->getValue(index_sibs[i]) * test_sample_size;
                if (i == 0) {
                    best_i = dv_value;
                } else {
                    // Note: tie-breaking doesn't matter here, since we are only concerned with finding the best frequency possible,
                    // not with the specific rule that results in that frequency.
                    if (test_freq[fit_index][dv_value] > test_freq[fit_index][best_i])
                        best_i = dv_value;
                }
            }

            test_key_freq[fit_index] = temp_value * test_sample_size;
            test_rule[fit_index] = best_i;
            test_counter++;
        }
    }

    int *dv_order = new int[dv_card];
    // Get an ordering for the dv values, so they can be displayed in ascending order.
    orderIndices(dv_label, dv_card, dv_order);

    // Compute marginals of DV states for the totals row
    double *marginal = new double[dv_card];
    for (int i = 0; i < dv_card; i++) {
        marginal[i] = 0.0;
        for (int j = 0; j < iv_statespace; j++) {
            marginal[i] += fit_prob[j][i];
        }
    }

    // Compute sums for the totals row
    double total_correct = 0.0; // correct on input data by fit rule
    for (int i = 0; i < iv_statespace; i++) {
        total_correct += input_freq[i][fit_rule[i]];
    }

    // Determine whether the classifier target is valid for confusion matrix
    bool checkTarget = false;
    int dv_target = -1;
    /* TODO: get dv_target from dv_label[dv_order[classTarget]]*/
    for (int i = 0; i < dv_card; i++) {
        if (!strcmp(dv_label[i], classTarget)) {
            dv_target = i;
            checkTarget = true;
        }
    }


    // Compute sums for the confusion matrix
    if (checkTarget) {
            double ftrtp = 0.0;
            double ftrfp = 0.0;
            double ftrtn = 0.0;
            double ftrfn = 0.0;
            for (int i = 0; i < iv_statespace; i++) {

                /* For each IV state,
                 *  if the DV rule is the target class,
                 *  then the portion predicted correctly are TP
                 *  and  the portion predicted incorrectly are FP.
                 *  The portion predicted correctly are
                 *  `input_freq[i][fit_rule[i]]`, 
                 *  as in the computation of `total_correct` above.
                 *  The portion predicted incorrectly are the complement within the population,
                 *  i.e. `input_key_freq[i]` minus the portion predicted correctly.
                 *  Similarly when the DV rule is not the target class,
                 *  correct results are TN and incorrect are FN.
                 */
                if (fit_rule[i] == dv_target) {
                    ftrtp += input_freq[i][fit_rule[i]];
                    ftrfp += input_key_freq[i] - input_freq[i][fit_rule[i]];
                } else {
                    ftrtn += input_freq[i][fit_rule[i]];
                    ftrfn += input_key_freq[i] - input_freq[i][fit_rule[i]];
                }
                
            }
            trtp = ftrtp;
            trfp = ftrfp;
            trtn = ftrtn;
            trfn = ftrfn;
    }
   
    // Compute marginals & sums for test data, if present.
    double test_by_fit_rule, test_by_test_rule;
    if (test_sample_size > 0.0) {
        for (int i = 0; i < dv_card; i++) {
            for (int j = 0; j < iv_statespace; j++) {
                test_dv_freq[i] += test_freq[j][i];
            }
        }
        test_by_fit_rule = 0.0; // correct on test data by fit rule
        test_by_test_rule = 0.0; // correct on test data by test rule (best possible performance)
        for (int i = 0; i < iv_statespace; i++) {
            test_by_fit_rule += test_freq[i][fit_rule[i]];
            test_by_test_rule += test_freq[i][test_rule[i]];
        }
    }


    // Compute sums for the confusion matrix for TEST DATA BY FIT RULE
    if (checkTarget && test_sample_size > 0.0) {
            double ftetp = 0.0;
            double ftefp = 0.0;
            double ftetn = 0.0;
            double ftefn = 0.0;
            for (int i = 0; i < iv_statespace; i++) {
                if (fit_rule[i] == dv_target) {
                    ftetp += test_freq[i][fit_rule[i]];
                    ftefp += test_key_freq[i] - test_freq[i][fit_rule[i]];
                } else {
                    ftetn += test_freq[i][fit_rule[i]];
                    ftefn += test_key_freq[i] - test_freq[i][fit_rule[i]];
                }
                
            }
            tetp = ftetp;
            tefp = ftefp;
            tetn = ftetn;
            tefn = ftefn;
    }

    int dv_ccount = 0;
    int dv_head_len = 0;
    for (int i = 0; i < dv_card; i++) {
        dv_head_len += strlen(dv_label[dv_order[i]]);
    }
    dv_head_len += dv_card * (strlen(row_sep) + strlen(dv_var->abbrev) + 1) + 1;
    const char* eq_sign = equals_sign(htmlMode);
    int eq_sign_len = strlen(eq_sign);
    int buf_len = dv_head_len * eq_sign_len;
    char *dv_header = new char[buf_len];
    memset(dv_header, 0, buf_len * sizeof(char));
    for (int i = 0; i < dv_card; i++) {
        dv_ccount += snprintf(dv_header + dv_ccount, buf_len - dv_ccount, "%s%s", dv_var->abbrev, eq_sign);
        dv_ccount += snprintf(dv_header + dv_ccount, buf_len - dv_ccount, "%s", dv_label[dv_order[i]]);
        dv_ccount += snprintf(dv_header + dv_ccount, buf_len - dv_ccount, row_sep);
    }

    // Header, Row 1
    fprintf(fd, "%s%sIV", block_start, head_start);
    for (int i = 0; i < iv_count; i++)
        fprintf(fd, "%s", head_sep);
    fprintf(fd, "|%sData%s", head_sep, head_sep);
    for (int i = 0; i < dv_card; i++)
        fprintf(fd, "%s", head_sep);
    if (rel == NULL || rel->isStateBased()) {
        fprintf(fd, "|%sModel", head_sep);
        for (int i = 0; i < dv_card; i++)
            fprintf(fd, "%s", head_sep);
    }
    fprintf(fd, "%s%s", head_sep, head_sep);
    if (calcExpectedDV == true)
        fprintf(fd, "%s%s", head_sep, head_sep);
    if (test_sample_size > 0.0)
        fprintf(fd, "%s%s%s|%s%s%s", head_sep, head_sep, head_sep, head_str4, head_sep, head_sep);
    fprintf(fd, head_end);

    // Header, Row 2
    fprintf(fd, "%s", head_start);
    for (int i = 0; i < iv_count; i++)
        fprintf(fd, "%s", head_sep);
    fprintf(fd, "|%s%s%s", head_sep, head_str2, head_sep);
    if (dv_card > 2)
        for (int i = 2; i < dv_card; i++)
            fprintf(fd, head_sep);
    if (rel == NULL || rel->isStateBased()) {
        fprintf(fd, "|%s%s", head_str1, head_sep);
        if (dv_card > 2)
            for (int i = 2; i < dv_card; i++)
                fprintf(fd, head_sep);
    }
    fprintf(fd, "%s%s", head_sep, head_sep);
    if (calcExpectedDV == true)
        fprintf(fd, "%s%s", head_sep, head_sep);
    if (test_sample_size > 0.0) {
        fprintf(fd, "%s%s%s|%s%s", head_sep, head_sep, head_sep, head_sep, head_str2);
        if (dv_card > 2)
            for (int i = 2; i < dv_card; i++)
                fprintf(fd, head_sep);
        fprintf(fd, head_str3);
    }
    fprintf(fd, head_end);

    // Header, Row 3
    fprintf(fd, "%s", row_start);
    for (int i = 0; i < iv_count; i++)
        fprintf(fd, "%s%s", var_list->getVariable(ind_vars[i])->abbrev, row_sep);
    fprintf(fd, "|%sfreq%s%s", row_sep, row_sep, dv_header);
    if (rel == NULL || rel->isStateBased())
        fprintf(fd, "|%s%s", row_sep, dv_header);
    fprintf(fd, "rule%s#correct%s%%correct", row_sep, row_sep);
    if (calcExpectedDV == true)
        fprintf(fd, "%sE(DV)%sMSE", row_sep, row_sep);
    
    fprintf(fd, "%sp(rule)%sp(margin)", row_sep, row_sep);

    
    if (test_sample_size > 0.0) {
        fprintf(fd, "%s|%sfreq%s%sby rule%sbest", row_sep, row_sep, row_sep, dv_header, row_sep);
        if (calcExpectedDV == true)
            fprintf(fd, "%sMSE", row_sep);
    }
    fprintf(fd, row_end);

    // Body of Table
    double mean_squared_error = 0.0;
    double total_test_error = 0.0;
    double temp_percent = 0.0;
    int keyval;
    int keysize = input_data->getKeySize();
    const char *keyvalstr;

    int *key_order = new int[iv_statespace];        // Created a sorted order for the IV states, so they appear in order in the table
    for (int i = 0; i < iv_statespace; i++)
        key_order[i] = i;
    
    
    sort_var_list = var_list;
    sort_count = iv_count;
    sort_vars = ind_vars;
    sort_keys = fit_key;
    
    qsort(key_order, iv_statespace, sizeof(int), sortKeys);

    // Prep for P-MARGIN, P-RULE
    // Make table containing univorm distribution of DV cardinality
    double* uniform = new double[dv_card];
    for (unsigned j = 0; j < dv_card; ++j) {
        uniform[j] = 1.0 / dv_card;
    }
    
    // Make table containing the marginal DV probabilities
    // probability of a given dv state j: marginal[dv_order[j]]
    double* marginal_tab = new double[dv_card];
    for (unsigned j = 0; j < dv_card; ++j) {
        marginal_tab[j] = marginal[dv_order[j]];
    }


    int i;
    // For each of the model's keys (i.e., each row of the table)...
    for (int order_i = 0; order_i < iv_statespace; order_i++) {
        i = key_order[order_i];
        if (input_key_freq[i] == 0.0) {
            if (test_sample_size > 0.0) {
                if (test_key_freq[i] == 0.0) {
                    continue;
                }
            } else {
                continue;
            }
        }
        // Also, switch the bgcolor of each row from grey to white, every other row. (If not in HTML, this does nothing.)
        if (order_i % 2)
            fprintf(fd, row_start);
        else
            fprintf(fd, row_start2);
        // Print the states of the IV in separate columns
        for (int j = 0; j < iv_count; j++) {
            keyval = Key::getKeyValue(fit_key[i], keysize, var_list, ind_vars[j]);
            keyvalstr = var_list->getVarValue(ind_vars[j], keyval);
            fprintf(fd, "%s%s", keyvalstr, row_sep);
        }
        fprintf(fd, "|%s%.3f%s", row_sep, input_key_freq[i], row_sep);
        // Print out the conditional probabilities of the training data
        temp_percent = 0.0;
        for (int j = 0; j < dv_card; j++) {
            if (input_key_freq[i] == 0.0)
                temp_percent = 0.0;
            else {
                temp_percent = input_freq[i][dv_order[j]] / input_key_freq[i] * 100.0;
            }
            fprintf(fd, "%.3f%s", temp_percent, row_sep);
        }
        if (rel == NULL || rel->isStateBased()) {
            fprintf(fd, "|%s", row_sep);
            // Print out the percentages for each of the DV states
            for (int j = 0; j < dv_card; j++) {
                if (fit_key_prob[i] == 0)
                    temp_percent = 0.0;
                else {
                    temp_percent = fit_prob[i][dv_order[j]] / fit_key_prob[i] * 100.0;
                    if (calcExpectedDV == true) {
                        fit_dv_expected[i] += temp_percent / 100.0 * dv_bin_value[dv_order[j]];
                    }
                }
                fprintf(fd, "%.3f%s", temp_percent, row_sep);
            }
        }
        // Print the DV state of the best rule. If there was no input to base the rule on, use the default rule.
        fprintf(fd, "%c%s%s", fit_tied[i] ? '*' : ' ', dv_label[fit_rule[i]], row_sep);

        // Number correct (of the input data, based on the rule from fit)
        fprintf(fd, "%.3f%s", input_freq[i][fit_rule[i]], row_sep);
        // Percent correct (of the input data, based on the rule from fit)
        if (input_key_freq[i] == 0)
            fprintf(fd, "%.3f", 0.0);
        else
            fprintf(fd, "%.3f", input_freq[i][fit_rule[i]] / input_key_freq[i] * 100.0);
        mean_squared_error = 0.0;
        if (calcExpectedDV == true) {
            fprintf(fd, "%s%.3f", row_sep, fit_dv_expected[i]);
            if (input_key_freq[i] > 0.0) {
                for (int j = 0; j < dv_card; j++) {
                    temp_percent = fit_dv_expected[i] - dv_bin_value[dv_order[j]];
                    mean_squared_error += temp_percent * temp_percent * input_freq[i][dv_order[j]];
                }
                mean_squared_error /= input_key_freq[i];
            } else
                mean_squared_error = 0;
            fprintf(fd, "%s%.3f", row_sep, mean_squared_error);
        }

        // Print out P-MARGIN and P-RULE
        
        // Make table containing the calculated DV probabilities at this IV state
        // probability of a given dv state j: fit_prob[i][dv_order[j]] / fit_key_prob[i];
        double* calculated = new double[dv_card];
        for (unsigned j = 0; j < dv_card; ++j) {
            calculated[j] = fit_key_prob[i] == 0 ? 0 : fit_prob[i][dv_order[j]] / fit_key_prob[i];
        }

        double p_rule = ocPearsonChiSquaredFlat(dv_card, calculated, uniform, input_key_freq[i]);
        double p_margin = ocPearsonChiSquaredFlat(dv_card, calculated, marginal_tab, input_key_freq[i]);

        delete [] calculated;

        fprintf(fd, "%s%.3f%s%.3f", row_sep, p_rule, row_sep, p_margin);

        // Print test results, if present
        if (test_sample_size > 0.0) {
            // Frequency in test data
            fprintf(fd, "%s|%s%.3f", row_sep, row_sep, test_key_freq[i]);
            // Print out the percentages for each of the DV states
            for (int j = 0; j < dv_card; j++) {
                fprintf(fd, row_sep);
                if (test_key_freq[i] == 0.0)
                    fprintf(fd, "%.3f", 0.0);
                else
                    fprintf(fd, "%.3f", test_freq[i][dv_order[j]] / test_key_freq[i] * 100.0);
            }
            fprintf(fd, row_sep);
            if (test_key_freq[i] == 0.0)
                fprintf(fd, "%.3f", 0.0);
            else
                fprintf(fd, "%.3f", test_freq[i][fit_rule[i]] / test_key_freq[i] * 100.0);
            fprintf(fd, row_sep);
            if (test_key_freq[i] == 0.0)
                fprintf(fd, "%.3f", 0.0);
            else
                fprintf(fd, "%.3f", test_freq[i][test_rule[i]] / test_key_freq[i] * 100.0);
            mean_squared_error = 0.0;
            if (calcExpectedDV == true) {
                if (test_key_freq[i] > 0.0) {
                    for (int j = 0; j < dv_card; j++) {
                        temp_percent = fit_dv_expected[i] - dv_bin_value[dv_order[j]];
                        mean_squared_error += temp_percent * temp_percent * test_freq[i][dv_order[j]];
                    }
                    mean_squared_error /= test_key_freq[i];
                } else
                    mean_squared_error = 0;
                fprintf(fd, "%s%.3f", row_sep, mean_squared_error);
                total_test_error += mean_squared_error * test_key_freq[i];
            }
        }
        fprintf(fd, row_end);
    }

    // Footer, Row 1 (totals)
    double total_expected_value = 0.0;
    fprintf(fd, row_start3);
    for (int i = 0; i < iv_count; i++)
        fprintf(fd, "%s", row_sep);
    fprintf(fd, "|%s%.3f%s", row_sep, sample_size, row_sep);
    // Print the training data DV totals
    for (int j = 0; j < dv_card; j++) {
        fprintf(fd, "%.3f%s", input_dv_freq[dv_order[j]] / sample_size * 100.0, row_sep);
    }
    if (rel == NULL || rel->isStateBased()) {
        fprintf(fd, "|%s", row_sep);
        // Print the marginals for each DV state
        for (int j = 0; j < dv_card; j++) {
            fprintf(fd, "%.3f%s", marginal[dv_order[j]] * 100.0, row_sep);
            if (calcExpectedDV == true)
                total_expected_value += marginal[dv_order[j]] * dv_bin_value[dv_order[j]];
        }
    }
    // Print out zeroes for p-margin and p-rule here
    fprintf(fd, "%s%s%.3f%s%.3f", dv_var->valmap[input_default_dv], row_sep, total_correct, row_sep,
            total_correct / sample_size * 100.0);
    if (calcExpectedDV == true) {
        fprintf(fd, "%s%.3f", row_sep, total_expected_value);
        temp_percent = mean_squared_error = 0.0;
        for (int j = 0; j < dv_card; j++) {
            temp_percent = total_expected_value - dv_bin_value[dv_order[j]];
            mean_squared_error += temp_percent * temp_percent * input_dv_freq[dv_order[j]];
        }
        mean_squared_error /= sample_size;
        fprintf(fd, "%s%.3f", row_sep, mean_squared_error);
    }

    // Print out blank cells for P-MARGIN and P-RULE
    fprintf(fd, "%s%s", row_sep, row_sep);

    double default_percent_on_test = 0.0;
    double best_percent_on_test = 0.0;
    double fit_percent_on_test = 0.0;
    if (test_sample_size > 0.0) {
        fprintf(fd, "%s|%s%.3f%s", row_sep, row_sep, test_sample_size, row_sep);
        // Print the test marginals for each DV state
        for (int j = 0; j < dv_card; j++) {
            temp_percent = test_dv_freq[dv_order[j]] / test_sample_size * 100.0;
            //if (temp_percent > default_percent_on_test) default_percent_on_test = temp_percent;
            fprintf(fd, "%.3f%s", temp_percent, row_sep);
        }
        default_percent_on_test = test_dv_freq[input_default_dv] / test_sample_size * 100.0;
        fit_percent_on_test = test_by_fit_rule / test_sample_size * 100.0;
        best_percent_on_test = test_by_test_rule / test_sample_size * 100.0;
        fprintf(fd, "%.3f%s%.3f", fit_percent_on_test, row_sep, best_percent_on_test);
        if (calcExpectedDV == true)
            fprintf(fd, "%s%.3f", row_sep, total_test_error / test_sample_size);
    }
    fprintf(fd, row_end);
    // Footer, Row 2 (repeat of Header, Row 3)
    fprintf(fd, row_start);
    for (int i = 0; i < iv_count; i++)
        fprintf(fd, "%s", row_sep);
    fprintf(fd, "|%sfreq%s%s", row_sep, row_sep, dv_header);
    if (rel == NULL || rel->isStateBased())
        fprintf(fd, "|%s%s", row_sep, dv_header);
    fprintf(fd, "rule%s#correct%s%%correct", row_sep, row_sep);
    if (calcExpectedDV == true)
        fprintf(fd, "%sE(DV)%sMSE", row_sep, row_sep);

    fprintf(fd, "%sp(rule)%sp(margin)", row_sep, row_sep);
    if (test_sample_size > 0.0) {
        fprintf(fd, "%s|%sfreq%s%sby rule%sbest", row_sep, row_sep, row_sep, dv_header, row_sep);
        if (calcExpectedDV == true)
            fprintf(fd, "%sMSE", row_sep);
    }
    fprintf(fd, "%s%s", row_end, block_end);

    // Print out a summary of the performance on the test data, if present.
    if (test_sample_size > 0.0) {
        fprintf(fd, "%s%sPerformance on Test Data%s", block_start, row_start, row_end);
        fprintf(fd,
                "%sIndependence Model rule:%s%.3f%%%scorrect (using rule from the independence model of the training data)%s",
                row_start, row_sep, default_percent_on_test, row_sep2, row_end);
        fprintf(fd, "%sModel rule:%s%.3f%%%scorrect%s%s", row_start, row_sep, fit_percent_on_test, row_sep2,
                use_alt_default ? " (augmented by alternate default model)" : "", row_end);
        fprintf(fd, "%sBest possible:%s%.3f%%%scorrect (using rules optimal for the test data)%s", row_start, row_sep,
                best_percent_on_test, row_sep2, row_end);
        temp_percent = best_percent_on_test - default_percent_on_test;
        if ((temp_percent) != 0)
            temp_percent = (fit_percent_on_test - default_percent_on_test) / temp_percent * 100.0;
        fprintf(fd, "%sImprovement by model:%s%.3f%%%s(Model - Default) / (Best - Default)%s%s", row_start, row_sep,
                temp_percent, row_sep2, row_end, block_end);
    }
    if (use_alt_default)
        fprintf(fd, "* Rule selected using the alternate default model.");
    else
        fprintf(fd, "* Rule selected using the independence model.");
    fprintf(fd, blank_line);

    // Print the alternate default table, if required.
    if (use_alt_default) {
        int *alt_ind_vars = new int[var_count];
        int alt_iv_count = alt_relation->getIndependentVariables(alt_ind_vars, var_count);
        fprintf(fd, blank_line);
        fprintf(fd, "Conditional DV for the alternate default model %s.", defaultFitModel->getPrintName());
        fprintf(fd, blank_line);
        // Header, Row 1
        fprintf(fd, "%s%sIV", block_start, head_start);
        for (int i = 0; i < alt_iv_count; i++)
            fprintf(fd, "%s", head_sep);
        fprintf(fd, "|%sModel", head_sep);
        for (int i = 0; i < dv_card; i++)
            fprintf(fd, "%s", head_sep);
        fprintf(fd, head_end);
        // Header, Row 2
        fprintf(fd, "%s", head_start);
        for (int i = 0; i < alt_iv_count; i++)
            fprintf(fd, "%s", head_sep);
        fprintf(fd, "|%s%s", head_str1, head_sep);
        if (dv_card > 2)
            for (int i = 2; i < dv_card; i++)
                fprintf(fd, head_sep);
        fprintf(fd, head_end);
        // Header, Row 3
        fprintf(fd, "%s", row_start);
        for (int i = 0; i < alt_iv_count; i++)
            fprintf(fd, "%s%s", var_list->getVariable(alt_ind_vars[i])->abbrev, row_sep);
        fprintf(fd, "|%s%srule", row_sep, dv_header);
        fprintf(fd, row_end);
        // Body of table
        for (int i = 0; i < alt_keys_found; i++) {
            if (i % 2)
                fprintf(fd, row_start);
            else
                fprintf(fd, row_start2);
            for (int j = 0; j < alt_iv_count; j++) {
                keyval = Key::getKeyValue(alt_key[i], keysize, var_list, alt_ind_vars[j]);
                keyvalstr = var_list->getVarValue(alt_ind_vars[j], keyval);
                fprintf(fd, "%s%s", keyvalstr, row_sep);
            }
            fprintf(fd, "|%s", row_sep);
            for (int j = 0; j < dv_card; j++) {
                if (alt_key_prob[i] == 0)
                    temp_percent = 0.0;
                else
                    temp_percent = alt_prob[i][dv_order[j]] / alt_key_prob[i] * 100.0;
                fprintf(fd, "%.3f%s", temp_percent, row_sep);
            }
            fprintf(fd, "%s", dv_label[alt_rule[i]]);
            fprintf(fd, row_end);
        }
        // Footer, Row 1
        fprintf(fd, row_start3);
        for (int i = 0; i < alt_iv_count; i++)
            fprintf(fd, "%s", row_sep);
        fprintf(fd, "|%s", row_sep);
        for (int j = 0; j < dv_card; j++)
            fprintf(fd, "%.3f%s", marginal[dv_order[j]] * 100.0, row_sep);
        fprintf(fd, "%s%s", dv_var->valmap[input_default_dv], row_sep);
        fprintf(fd, row_end);
        // Footer, Row 2
        fprintf(fd, "%s", row_start);
        for (int i = 0; i < alt_iv_count; i++)
            fprintf(fd, "%s", row_sep);
        fprintf(fd, "|%s%srule", row_sep, dv_header);
        fprintf(fd, "%s%s", row_end, block_end);
    }

    // PRINT CONFUSION MATRICES

    if (!strcmp(classTarget, "") && model) {
        printf("Note: no default state selected, so confusion matrices will not be printed.");
    } else if (!checkTarget && model || trtp + trfn <= 0)  { 
            printf("Note: selected default state '%s=%s' is not among states occurring in the DV in the data, so confusion matrices will not be printed", dv_var->abbrev, classTarget);
    } else if (trtn + trfp <= 0) {
        printf("Note: there are no occurrences of any non-default (\"positive\") conditional DV state (that is, any state other than '%s=%s'), in the training data, so confusion matrices will not be printed", dv_var->abbrev, classTarget);
    } else if (checkTarget) {
        // Print out the confusion matrix and associated statistics
        // Do this for the dual problem: flip positive and negative param order
        printConfusionMatrix(model, rel, dv_var->abbrev, classTarget, trtn, trfn, trtp, trfp, (test_sample_size > 0.0), tetn, tefn, tetp, tefp);
    }


    // If this is the entire model (not just a relation), print tables for each of the component relations,
    // if there are more than two of them (for VB) or more than 3 (for SB).
 
    if ((rel == NULL) && ((model->getRelationCount() > 2 && !model->isStateBased()) || (model->isStateBased() && model->getRelationCount() > 3))) {
        for (int i = 0; i < model->getRelationCount(); i++) {
            if (model->getRelation(i)->isIndependentOnly())
                continue;
            if (model->getRelation(i)->isDependentOnly())
                continue;
            printConditional_DV(fd, model->getRelation(i), calcExpectedDV, classTarget);
        }
    }



    delete[] dv_order;
    delete[] dv_header;
    delete[] marginal;
    delete[] index_sibs;
    delete[] temp_key_array;
    delete[] ind_vars;
    for (int i = 0; i < iv_statespace; i++) {
        delete[] input_freq[i];
        delete[] input_key[i];
        delete[] alt_key[i];
        delete[] alt_prob[i];
        delete[] fit_key[i];
        delete[] fit_prob[i];
    }
    delete[] input_freq;
    delete[] input_key;
    delete[] alt_key;
    delete[] alt_prob;
    delete[] fit_key;
    delete[] fit_prob;
    delete[] alt_rule;
    delete[] alt_key_prob;
    delete[] input_key_freq;
    delete[] input_dv_freq;
    delete[] fit_dv_prob;
    delete[] fit_key_prob;
    delete[] fit_tied;
    delete[] fit_rule;
    delete[] fit_dv_expected;

    delete [] uniform;
    delete [] marginal_tab;
    if (rel == NULL) {
        delete fit_table;
    }
    if (test_table) {
        for (int i = 0; i < iv_statespace; i++) {
            delete[] test_freq[i];
            delete[] test_key[i];
        }
        delete[] test_freq;
        delete[] test_key;
        delete[] test_key_freq;
        delete[] test_dv_freq;
        delete[] test_rule;
        delete test_table;
    }
    delete input_table;

    return;
}

