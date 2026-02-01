#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <string>
#include <vector>
#include <map>
#include <set>
#include <algorithm>
#include <sstream>
#include <iomanip>
#include <cstdio>
#include <cstring>
#include <cmath>
#include <chrono>

// Include OCCAM headers
#include "VBMManager.h"
#include "Model.h"
#include "VariableList.h"
#include "Variable.h"
#include "SearchBase.h"
#include "Report.h"
#include "Types.h"

namespace py = pybind11;

// ========== MODEL WRAPPER ==========
struct PyModel {
    std::string name;
    double h;
    double information;
    double aic;
    double bic;
    double daic;
    double dbic;
    double alpha;
    double df;
    double lr;
    double pct_correct_data;
    double pct_correct_test;  // ADD: Support for test data percent correct
    double pct_coverage;       // ADD: Support for coverage
    double pct_missed_test;    // ADD: Support for missed test cases
    double incr_alpha;
    int level;
};

// ========== MAIN WRAPPER CLASS ==========
class PyVBMManager {
private:
    VBMManager manager;
    Report* report;  // Report object as member variable
    
    // Track models from search
    std::vector<Model*> kept_models;  // Models kept from beam search
    std::map<std::string, Model*> best_models;  // Best models by criterion
    std::map<std::string, Model*> all_models_seen;  // ALL models ever generated (not just kept)
    
    // Configuration
    int report_separator;
    std::string report_variables;
    std::string ref_model;
    bool debug_mode;
    
    // Fit configuration options
    bool calc_expected_dv;
    bool skip_trained_model_table;
    bool skip_ivi_tables;
    std::string fit_classifier_target;
    std::string default_fit_model;
    
    // ========== HELPER FUNCTIONS ==========
    
    std::pair<int, char**> python_list_to_argv(const std::vector<std::string>& args) {
        int argc = args.size();
        char** argv = new char*[argc];
        for (int i = 0; i < argc; i++) {
            argv[i] = new char[args[i].length() + 1];
            strcpy(argv[i], args[i].c_str());
        }
        return std::make_pair(argc, argv);
    }
    
    void cleanup_argv(int argc, char** argv) {
        for (int i = 0; i < argc; i++) {
            delete[] argv[i];
        }
        delete[] argv;
    }
    
    void computeModelStatistics(Model* model, Model* refModel) {
        // Compute fit table first
        manager.makeFitTable(model);
        
        // Let OCCAM compute all statistics - following ocutils.py's doAllComputations pattern
        manager.computeL2Statistics(model);
        // computeDFStatistics doesn't exist - that was the bug!
        manager.computeDependentStatistics(model);
        manager.computeInformationStatistics(model);
        manager.computePercentCorrect(model);
        
        // ADD: If test data exists, compute test statistics
        if (manager.getTestData()) {
            // These methods should exist in VBMManager for test data
            // The percent correct on test is typically computed automatically
            // when computePercentCorrect is called with test data present
        }
        
        // Compute incremental alpha (requires progenitor to be set)
        manager.computeIncrementalAlpha(model);
        
        // For reference model, ensure everything is zero/correct
        if (model == refModel) {
            model->setAttribute("aic", 0.0);
            model->setAttribute("bic", 0.0);
            model->setAttribute("daic", 0.0);
            model->setAttribute("dbic", 0.0);
            model->setAttribute("lr", 0.0);
            model->setAttribute("information", 0.0);
            model->setAttribute("%dH(DV)", 0.0);
            // Reference model should have incr_alpha = 0.0 (perfect fit with itself)
            model->setAttribute("incr_alpha", 0.0);
            model->setAttribute("incr_alpha_reachable", 1.0);
        } else {
            // For non-reference models
            double aic_val = model->getAttribute("aic");
            double bic_val = model->getAttribute("bic");
            model->setAttribute("daic", aic_val);
            model->setAttribute("dbic", bic_val);
            
            // Manually set %dH(DV) - information as percentage
            double info = model->getAttribute("information");
            model->setAttribute("%dH(DV)", info * 100.0);
        }
        
        // Debug output if enabled
        if (debug_mode) {
            double lr = model->getAttribute("lr");
            double ddf = model->getAttribute("ddf");
            double dbic = model->getAttribute("dbic");
            double incr_alpha = model->getAttribute("incr_alpha");
            double pct_dh = model->getAttribute("%dH(DV)");
            double reachable = model->getAttribute("incr_alpha_reachable");
            printf("Model %s: LR=%.2f, dDF=%.0f, dBIC=%.2f, IncAlpha=%.6f, %%dH(DV)=%.2f, Reachable=%.0f\n",
                   model->getPrintName(), lr, ddf, dbic, incr_alpha, pct_dh, reachable);
            
            // ADD: Debug test data statistics if present
            if (manager.getTestData()) {
                double pct_test = model->getAttribute("pct_correct_test");
                double pct_miss = model->getAttribute("pct_missed_test");
                printf("  Test Data: %%Correct=%.2f, %%Missed=%.2f\n", pct_test, pct_miss);
            }
        }
    }
    
    // Following ocutils.py's doAllComputations pattern (without the buggy computeDFStatistics)
    void doAllComputations(Model* model) {
        manager.computeL2Statistics(model);
        // computeDFStatistics doesn't exist - skip it
        manager.computeDependentStatistics(model);
        manager.computePercentCorrect(model);
        manager.computeInformationStatistics(model);
        
        // Set %dH(DV) manually
        double info = model->getAttribute("information");
        model->setAttribute("%dH(DV)", info * 100.0);
        
        // Note: makeFitTable is called elsewhere if needed
    }
    
    PyModel modelToPyModel(Model* model, int level = -1) {
        PyModel pm;
        pm.name = std::string(model->getPrintName());
        pm.h = model->getAttribute("h");
        
        double info = model->getAttribute("information");
        pm.information = info;
        
        pm.aic = model->getAttribute("aic");
        pm.bic = model->getAttribute("bic");
        pm.daic = model->getAttribute("daic");
        pm.dbic = model->getAttribute("dbic");
        
        pm.alpha = model->getAttribute("alpha");
        pm.df = model->getAttribute("ddf");
        pm.lr = model->getAttribute("lr");
        pm.pct_correct_data = model->getAttribute("pct_correct_data");
        
        // ADD: Get test data statistics if available
        pm.pct_correct_test = model->getAttribute("pct_correct_test");
        pm.pct_coverage = model->getAttribute("pct_coverage");
        pm.pct_missed_test = model->getAttribute("pct_missed_test");
        
        pm.incr_alpha = model->getAttribute("incr_alpha");
        pm.level = (level >= 0) ? level : (int)model->getAttribute("level");
        return pm;
    }
    
public:
    PyVBMManager() : report(nullptr), debug_mode(false), 
                     report_separator(3), ref_model("bottom"),
                     calc_expected_dv(false), skip_trained_model_table(false),
                     skip_ivi_tables(true) {  // Default to skipping IVI tables
        // Default report variables - matching server output format
        report_variables = "level$I, h, ddf$I, lr, alpha, %dH(DV), daic, dbic, incr_alpha, pct_correct_data";
    }
    
    ~PyVBMManager() {
        if (report) {
            delete report;
        }
    }
    
    // ========== INITIALIZATION ==========
    
    bool init_from_command_line(const std::vector<std::string>& args) {
        auto [argc, argv] = python_list_to_argv(args);
        
        try {
            bool success = manager.initFromCommandLine(argc, argv);
            cleanup_argv(argc, argv);
            
            if (success && debug_mode) {
                // Debug: Print variables to verify abbreviations
                VariableList* varList = manager.getVariableList();
                if (varList) {
                    std::ostringstream debug;
                    debug << "Variables loaded:\n";
                    int count = varList->getVarCount();
                    for (int i = 0; i < count; i++) {
                        Variable* var = varList->getVariable(i);
                        if (var) {
                            debug << "  " << i << ": " << var->name 
                                  << " (abbrev: " << var->abbrev << ")\n";
                        }
                    }
                    printf("%s", debug.str().c_str());
                }
                
                // ADD: Report if test data was detected
                if (manager.getTestData()) {
                    printf("Test data detected in input file\n");
                }
            }
            
            return success;
        } catch (...) {
            cleanup_argv(argc, argv);
            return false;
        }
    }
    
    // ========== CONFIGURATION ==========
    
    void set_report_separator(int sep) {
        report_separator = sep;
        Report::setSeparator(sep);  // FIX: Actually set Report's static separator!
    }
    
    void set_report_variables(const std::string& variables) {
        report_variables = variables;
    }
    
    void set_ref_model(const std::string& model) {
        ref_model = model;
        manager.setRefModel(const_cast<char*>(model.c_str()));
    }
    
    void set_search_type(const std::string& search_type) {
        manager.setSearch(search_type.c_str());
    }
    
    void set_debug_mode(bool debug) {
        debug_mode = debug;
    }
    
    // Fit configuration
    void set_calc_expected_dv(bool calc) {
        calc_expected_dv = calc;
    }
    
    void set_skip_trained_model_table(bool skip) {
        skip_trained_model_table = skip;
    }
    
    void set_skip_ivi_tables(bool skip) {
        skip_ivi_tables = skip;
    }
    
    void set_fit_classifier_target(const std::string& target) {
        fit_classifier_target = target;
    }
    
    void set_default_fit_model(const std::string& model) {
        default_fit_model = model;
    }
    
    // ========== BEAM SEARCH IMPLEMENTATION (WITH TEST DATA SUPPORT!) ==========
    
    std::string generate_search_report(const std::string& search_type, int levels, int width, 
                                      bool include_test_data = false) {
        
        // Clear previous search state
        kept_models.clear();
        best_models.clear();
        all_models_seen.clear();
        
        // Initialize search
        manager.setSearch(search_type.c_str());
        SearchBase* search = manager.getSearch();
        if (!search) {
            return "Error: Invalid search type";
        }
        
        // Get reference model (bottom for bottom-up search)
        Model* refModel = manager.getBottomRefModel();
        if (!refModel) {
            return "Error: No reference model";
        }
        
        // Set reference model as its own progenitor (or nullptr for root)
        refModel->setProgenitor(nullptr);
        refModel->setAttribute("level", 0.0);
        
        // Initialize reference model attributes for incremental alpha tracking
        refModel->setAttribute("incr_alpha", 0.0);  // Reference has alpha = 0
        refModel->setAttribute("incr_alpha_reachable", 1.0);  // Reference is always reachable
        
        // Compute statistics for reference model
        computeModelStatistics(refModel, refModel);
        refModel->setAttribute("daic", 0.0);
        refModel->setAttribute("dbic", 0.0);
        
        // Add reference model to kept models
        kept_models.push_back(refModel);
        all_models_seen[std::string(refModel->getPrintName())] = refModel;
        
        // Current beam (models to expand)
        std::vector<Model*> current_beam = {refModel};
        
        // Search statistics
        std::ostringstream search_progress;
        search_progress << "Searching levels:\n";
        
        // Beam search: only expand models in current beam
        for (int level = 1; level <= levels; level++) {
            std::vector<Model*> candidates;  // All children generated this level
            
            // Generate children ONLY from current beam
            for (Model* parent : current_beam) {
                Model** children = search->search(parent);
                if (!children) continue;
                
                for (int i = 0; children[i] != nullptr; i++) {
                    Model* child = children[i];
                    std::string model_name = std::string(child->getPrintName());
                    
                    // INCREMENTAL ALPHA FIX: Handle duplicates properly
                    if (all_models_seen.find(model_name) != all_models_seen.end()) {
                        // Model already exists - compare progenitors to find best path
                        Model* existing = all_models_seen[model_name];
                        
                        // Let OCCAM choose the best progenitor
                        manager.compareProgenitors(existing, parent);
                        
                        // Recompute incremental alpha after progenitor change
                        manager.computeIncrementalAlpha(existing);
                        
                        // Don't add to candidates - it was already processed at its original level
                        continue;
                    }
                    
                    // Otherwise add new model
                    all_models_seen[model_name] = child;
                    
                    // Set progenitor for incremental alpha calculation
                    child->setProgenitor(parent);
                    child->setAttribute("level", (double)level);
                    
                    // Compute statistics
                    computeModelStatistics(child, refModel);
                    
                    // CRITICAL FIX: Calculate incr_alpha_reachable for this child
                    // A model is "reachable" (per OCCAM manual) if ALL steps from
                    // the starting model have Inc.Alpha < 0.05
                    double incr_alpha = child->getAttribute("incr_alpha");
                    double parent_reachable = parent->getAttribute("incr_alpha_reachable");
                    
                    // Child is reachable only if:
                    // 1. Parent was reachable (all previous steps were significant)
                    // 2. This step is significant (incr_alpha < 0.05)
                    bool is_reachable = (parent_reachable == 1.0 && incr_alpha < 0.05);
                    child->setAttribute("incr_alpha_reachable", is_reachable ? 1.0 : 0.0);
                    
                    // Debug output for reachability tracking
                    if (debug_mode) {
                        printf("  %s: Inc.Alpha=%.6f, Parent reachable=%s, This step sig=%s -> %s\n",
                               child->getPrintName(),
                               incr_alpha,
                               parent_reachable == 1.0 ? "YES" : "NO",
                               incr_alpha < 0.05 ? "YES" : "NO",
                               is_reachable ? "REACHABLE" : "not reachable");
                    }
                    
                    // Add to candidates for this level
                    candidates.push_back(child);
                }
            }
            
            // Sort candidates by dBIC for SEARCH selection
            // For bottom-up search: HIGHER (more positive) dBIC is better!
            std::sort(candidates.begin(), candidates.end(),
                     [](Model* a, Model* b) {
                         return a->getAttribute("dbic") > b->getAttribute("dbic");
                     });
            
            // Keep only top 'width' models - these become the new beam
            current_beam.clear();
            int kept_count = std::min(width, (int)candidates.size());
            
            for (int i = 0; i < kept_count; i++) {
                Model* kept_model = candidates[i];
                current_beam.push_back(kept_model);  // Add to beam for next level
                kept_models.push_back(kept_model);   // Add to overall kept list
            }
            
            // Track progress
            search_progress << level << " : " << candidates.size() 
                          << " new models, " << kept_count << " kept; "
                          << kept_models.size() << " total kept\n";
            
            // Print progress using pybind11's py::print for Jupyter compatibility
            py::print(py::str("Level {}/{}: {} new models, {} kept (total: {})")
                .format(level, levels, candidates.size(), kept_count, kept_models.size()));
            py::module_::import("sys").attr("stdout").attr("flush")();  // Force flush
            
            // Stop if no models to expand
            if (current_beam.empty()) break;
        }
        
        // Find best models from KEPT models only
        if (!kept_models.empty()) {
            Model* best_bic = nullptr;
            Model* best_aic = nullptr;
            Model* best_info = nullptr;
            Model* best_info_alpha = nullptr;
            
            for (Model* model : kept_models) {
                // Skip reference model for best model selection
                if (model == refModel && model->getAttribute("level") == 0) continue;
                
                if (!best_bic || model->getAttribute("dbic") > best_bic->getAttribute("dbic")) {
                    best_bic = model;
                }
                if (!best_aic || model->getAttribute("daic") > best_aic->getAttribute("daic")) {
                    best_aic = model;
                }
                if (!best_info || model->getAttribute("information") > best_info->getAttribute("information")) {
                    best_info = model;
                }
                
                // Track best model with incremental alpha < 0.05 AND reachable
                // Check incr_alpha_reachable attribute to ensure ALL steps have inc.alpha < 0.05
                double reachable = model->getAttribute("incr_alpha_reachable");
                if (reachable == 1.0) {  // Model is reachable (all steps have inc.alpha < 0.05)
                    if (!best_info_alpha || 
                        model->getAttribute("information") > best_info_alpha->getAttribute("information")) {
                        best_info_alpha = model;
                    }
                }
            }
            
            if (best_bic) best_models["bic"] = best_bic;
            if (best_aic) best_models["aic"] = best_aic;
            if (best_info) best_models["information"] = best_info;
            if (best_info_alpha) best_models["info_alpha"] = best_info_alpha;
            
            // Debug output for best model selection
            if (debug_mode) {
                printf("\n=== Best Model Selection ===");
                if (best_bic) printf("\n  Best by BIC: %s (dBIC=%.2f)", 
                    best_bic->getPrintName(), best_bic->getAttribute("dbic"));
                if (best_info) printf("\n  Best by raw Info: %s (%%dH=%.2f%%)",
                    best_info->getPrintName(), best_info->getAttribute("information")*100);
                if (best_info_alpha) printf("\n  Best by Info (OCCAM def): %s (%%dH=%.2f%%, Inc.Alpha=%.4f)",
                    best_info_alpha->getPrintName(), 
                    best_info_alpha->getAttribute("information")*100,
                    best_info_alpha->getAttribute("incr_alpha"));
                else printf("\n  Best by Info (OCCAM def): NONE - no models with all steps significant!");
                printf("\n");
            }
        }
        
        // Create fresh report for this search (delete old one if exists)
        if (report) {
            delete report;
        }
        report = new Report(&manager);
        report->setSeparator(report_separator);
        
        // MODIFY: Configure report variables based on test data presence
        std::string actual_report_vars = report_variables;
        
        // Auto-detect test data and add columns if requested or if test data exists
        if ((include_test_data || manager.getTestData()) && manager.getTestData()) {
            // Don't include ID and Model - they're added automatically by Report class!
            // Start with Level and other columns
            actual_report_vars = "Level$I, h, ddf$I, lr, alpha, %dH(DV), daic, dbic, incr_alpha, pct_correct_data";
            
            // Add test-specific columns
            actual_report_vars += ", pct_coverage, pct_correct_test, pct_missed_test";
            
            // Note: The column headers in the gold standard are:
            // %C(Data) %cover %C(Test) %miss
            // These map to: pct_correct_data, pct_coverage, pct_correct_test, pct_missed_test
        }
        
        report->setAttributes(const_cast<char*>(actual_report_vars.c_str()));
        
        // Add all kept models to report
        for (Model* model : kept_models) {
            report->addModel(model);
        }
        
        // Sort report by information (descending) for DISPLAY
        report->sort("information", Direction::Descending);
        
        // Generate report output using Report class
        char tempname[L_tmpnam];
        tmpnam(tempname);
        FILE* temp = fopen(tempname, "w+");
        if (!temp) return "Error: Could not create temp file";
        
        report->print(temp);
        
        rewind(temp);
        std::string output;
        char buffer[4096];
        while (fgets(buffer, sizeof(buffer), temp)) {
            output += buffer;
        }
        
        fclose(temp);
        remove(tempname);
        
        // For CSV format, don't include search progress text
        if (report_separator == 2) {  // COMMASEP = 2
            return output;  // Return just the CSV data
        } else {
            // For other formats, include search progress
            return search_progress.str() + "\n" + output;
        }
    }
    
    // ========== COMPLETE FIT REPORT (WITH AUTO TEST DATA SUPPORT) ==========
    
    std::string generate_fit_report(const std::string& model_name, const std::string& target_state = "0") {
        // Following ocutils.py's doFit pattern
        
        
        // Clear confusion matrix before generating new report
        // This ensures CM values are fresh for this model/target combination
        manager.clearMainModelConfusionMatrix();
        
        // Make the model with fit table (second parameter = 1)
        Model* model = manager.makeModel(model_name.c_str(), true);
        if (!model) {
            return "Error: Could not create model " + model_name;
        }
        
        // Set reference model
        manager.setRefModel(const_cast<char*>(ref_model.c_str()));
        Model* refModel = manager.getBottomRefModel();
        
        // Do all computations following ocutils.py pattern
        doAllComputations(model);
        
        // Use the configured fit_classifier_target if set, otherwise use passed target_state
        std::string actual_target = target_state;
        if (!fit_classifier_target.empty()) {
            actual_target = fit_classifier_target;
        }
        
        // Build the complete fit report output
        std::ostringstream output;
        
        // 1. Print basic statistics (optional - but printBasicStatistics prints to stdout)
        // We could capture it but for now just add key stats directly
        output << "Sample size: " << manager.getSampleSz() << "\n";
        VariableList* varList = manager.getVariableList();
        if (varList) {
            output << "Variables: " << varList->getVarCount() << "\n";
        }
        
        // ADD: Report test data presence
        if (manager.getTestData()) {
            output << "Test data: Present\n";
        }
        
        output << "\n";
        
        // 2. Print fit report from manager
        char tempname1[L_tmpnam];
        tmpnam(tempname1);
        FILE* temp1 = fopen(tempname1, "w+");
        if (temp1) {
            manager.printFitReport(model, temp1);
            rewind(temp1);
            char buffer[4096];
            while (fgets(buffer, sizeof(buffer), temp1)) {
                output << buffer;
            }
            fclose(temp1);
            remove(tempname1);
        }
        output << "\n";
        
        // 3. Make fit table (already done above with makeModel(..., true))
        // But call it again to be sure
        manager.makeFitTable(model);
        
        // 4. Create a Report for residuals and conditional DV
        Report* fit_report = new Report(&manager);
        fit_report->setSeparator(report_separator);
        
        // Use custom report variables if set
        if (!report_variables.empty()) {
            fit_report->setAttributes(const_cast<char*>(report_variables.c_str()));
        }
        
        // Add the model to the report
        fit_report->addModel(model);
        
        // Set default fit model if specified
        if (!default_fit_model.empty()) {
            Model* defaultModel = manager.makeModel(default_fit_model.c_str(), true);
            if (defaultModel) {
                fit_report->setDefaultFitModel(defaultModel);
            }
        }
        
        // 5. Print residuals from Report class
        char tempname2[L_tmpnam];
        tmpnam(tempname2);
        FILE* temp2 = fopen(tempname2, "w+");
        if (temp2) {
            fit_report->printResiduals(temp2, model, skip_trained_model_table, skip_ivi_tables);
            rewind(temp2);
            char buffer[4096];
            while (fgets(buffer, sizeof(buffer), temp2)) {
                output << buffer;
            }
            fclose(temp2);
            remove(tempname2);
        }
        output << "\n";
        
        // 6. Print conditional DV tables with confusion matrix
        char tempname3[L_tmpnam];
        tmpnam(tempname3);
        FILE* temp3 = fopen(tempname3, "w+");
        if (temp3) {
            // IMPORTANT: Pass the actual_target for confusion matrix
            // Don't pass empty string - that disables confusion matrix!
            fit_report->printConditional_DV(temp3, model, calc_expected_dv, 
                                           const_cast<char*>(actual_target.c_str()), skip_ivi_tables);
            rewind(temp3);
            char buffer[4096];
            int line_count = 0;
            while (fgets(buffer, sizeof(buffer), temp3)) {
                output << buffer;
                line_count++;
            }
            fclose(temp3);
            remove(tempname3);
        }
        
        // ADD: If test data is present, the performance on test data section
        // should automatically be included by printConditional_DV when test data exists
        
        // Clean up the temporary fit report
        delete fit_report;
        
        return output.str();
    }
    
    // ========== CONFUSION MATRIX EXTRACTION ==========
    // Simple architecture: get_confusion_matrix() only reads values
    // If values don't exist OR are for a different model, it calls generate_fit_report()
    
    py::dict get_confusion_matrix(const std::string& model_name, 
                                  const std::string& target_state = "0") {
        py::dict result;
        
        
        try {
            // Check if we already have CM values for THIS specific model/target
            auto cm = manager.getMainModelConfusionMatrix();
            
            // If no values exist, OR values are for a different model/target, regenerate
            if (!cm.isFor(model_name.c_str(), target_state.c_str())) {
                // Generate the fit report which stores CM as a side effect
                generate_fit_report(model_name, target_state);
                
                // Now read the values that should have been stored
                cm = manager.getMainModelConfusionMatrix();
            } else {
            }
            
            // Check if values were actually computed
            if (!cm.has_values) {
                result["error"] = "Confusion matrix could not be computed for this model/target. "
                                 "Make sure the model is valid and the target state exists.";
                result["has_values"] = false;
                return result;
            }
            
            // Double-check we got the right model (defensive)
            if (!cm.isFor(model_name.c_str(), target_state.c_str())) {
                result["error"] = "Internal error: CM computed for wrong model/target";
                result["has_values"] = false;
                return result;
            }
            
            // Convert to Python dict (training data)
            double total = cm.train_tp + cm.train_fp + cm.train_tn + cm.train_fn;
            
            // SKLEARN-COMPATIBLE KEYS: Use train_* and test_* prefixes
            // Follows sklearn.model_selection.cross_validate() pattern
            
            // Training confusion matrix elements
            result["train_tn"] = cm.train_tn;
            result["train_fp"] = cm.train_fp;
            result["train_fn"] = cm.train_fn;
            result["train_tp"] = cm.train_tp;
            
            // Training derived metrics
            result["train_accuracy"] = (total > 0) ? (cm.train_tp + cm.train_tn) / total : 0.0;
            result["train_sensitivity"] = (cm.train_tp + cm.train_fn > 0) ? 
                                          cm.train_tp / (cm.train_tp + cm.train_fn) : 0.0;
            result["train_specificity"] = (cm.train_tn + cm.train_fp > 0) ? 
                                          cm.train_tn / (cm.train_tn + cm.train_fp) : 0.0;
            result["train_precision"] = (cm.train_tp + cm.train_fp > 0) ?
                                        cm.train_tp / (cm.train_tp + cm.train_fp) : 0.0;
            
            // F1 score (harmonic mean of precision and recall/sensitivity)
            double train_precision = result["train_precision"].cast<double>();
            double train_sensitivity = result["train_sensitivity"].cast<double>();
            result["train_f1_score"] = (train_precision + train_sensitivity > 0) ?
                                       2.0 * (train_precision * train_sensitivity) / 
                                       (train_precision + train_sensitivity) : 0.0;
            
            // NPV (Negative Predictive Value)
            result["train_npv"] = (cm.train_tn + cm.train_fn > 0) ?
                                  cm.train_tn / (cm.train_tn + cm.train_fn) : 0.0;
            
            result["has_values"] = true;
            
            // Test data if available
            if (cm.has_test_data) {
                double test_total = cm.test_tp + cm.test_fp + cm.test_tn + cm.test_fn;
                
                // Test confusion matrix elements
                result["test_tn"] = cm.test_tn;
                result["test_fp"] = cm.test_fp;
                result["test_fn"] = cm.test_fn;
                result["test_tp"] = cm.test_tp;
                
                // Test derived metrics
                result["test_accuracy"] = (test_total > 0) ? 
                                          (cm.test_tp + cm.test_tn) / test_total : 0.0;
                result["test_sensitivity"] = (cm.test_tp + cm.test_fn > 0) ?
                                             cm.test_tp / (cm.test_tp + cm.test_fn) : 0.0;
                result["test_specificity"] = (cm.test_tn + cm.test_fp > 0) ?
                                             cm.test_tn / (cm.test_tn + cm.test_fp) : 0.0;
                result["test_precision"] = (cm.test_tp + cm.test_fp > 0) ?
                                           cm.test_tp / (cm.test_tp + cm.test_fp) : 0.0;
                
                // Test F1 and NPV
                double test_precision = result["test_precision"].cast<double>();
                double test_sensitivity = result["test_sensitivity"].cast<double>();
                result["test_f1_score"] = (test_precision + test_sensitivity > 0) ?
                                          2.0 * (test_precision * test_sensitivity) / 
                                          (test_precision + test_sensitivity) : 0.0;
                result["test_npv"] = (cm.test_tn + cm.test_fn > 0) ?
                                     cm.test_tn / (cm.test_tn + cm.test_fn) : 0.0;
                
                result["has_test_data"] = true;
            } else {
                result["has_test_data"] = false;
            }
            
        } catch (const std::exception& e) {
            result["error"] = std::string("Exception: ") + e.what();
            result["has_values"] = false;
        }
        
        return result;
    }
    
    // ========== BEST MODEL GETTERS ==========
    
    std::string get_best_model_by_bic() {
        auto it = best_models.find("bic");
        if (it != best_models.end() && it->second) {
            return std::string(it->second->getPrintName());
        }
        return "";
    }
    
    std::string get_best_model_by_aic() {
        auto it = best_models.find("aic");
        if (it != best_models.end() && it->second) {
            return std::string(it->second->getPrintName());
        }
        return "";
    }
    
    // OCCAM Manual Definition (Section IV "Search Output"):
    // "Best Model by Information" = highest information model that is REACHABLE,
    // where "reachable" means ALL steps from starting model have Inc.Alpha < 0.05
    std::string get_best_model_by_information() {
        auto it = best_models.find("info_alpha");  // Uses statistically significant models only
        if (it != best_models.end() && it->second) {
            return std::string(it->second->getPrintName());
        }
        return "";
    }
    
    // DEPRECATED: Use get_best_model_by_information() instead
    // Kept for backward compatibility - returns same result
    std::string get_best_model_by_info_alpha() {
        return get_best_model_by_information();  // Just calls the main function
    }
    
    // Get highest raw information (ignores statistical significance)
    // WARNING: May return overfitted models! Use get_best_model_by_information() instead.
    std::string get_best_model_by_raw_information() {
        auto it = best_models.find("information");
        if (it != best_models.end() && it->second) {
            return std::string(it->second->getPrintName());
        }
        return "";
    }
    
    // ========== MODEL OPERATIONS ==========
    
    PyModel make_model(const std::string& model_name, bool make_fit_table = false) {
        Model* model = manager.makeModel(model_name.c_str(), make_fit_table);
        if (!model) {
            PyModel empty;
            empty.name = "ERROR";
            return empty;
        }
        
        if (make_fit_table) {
            Model* refModel = manager.getBottomRefModel();
            computeModelStatistics(model, refModel);
        }
        
        return modelToPyModel(model);
    }
    
    PyModel get_model_statistics(const std::string& model_name) {
        return make_model(model_name, true);
    }
    
    // ========== INFORMATION GETTERS ==========
    
    std::vector<std::string> get_variable_list() {
        std::vector<std::string> result;
        VariableList* varList = manager.getVariableList();
        if (varList) {
            int count = varList->getVarCount();
            for (int i = 0; i < count; i++) {
                Variable* var = varList->getVariable(i);
                if (var) {
                    result.push_back(std::string(var->name));
                }
            }
        }
        return result;
    }
    
    std::string get_basic_statistics() {
        std::ostringstream stats;
        stats << "Sample size: " << manager.getSampleSz() << "\n";
        
        VariableList* varList = manager.getVariableList();
        if (varList) {
            stats << "Variables: " << varList->getVarCount() << "\n";
        }
        
        Model* bottom = manager.getBottomRefModel();
        if (bottom) {
            double h_data = manager.computeH(bottom);
            stats << "H(data): " << h_data << "\n";
        }
        
        // ADD: Report test data status
        if (manager.getTestData()) {
            stats << "Test data: Present\n";
            // Could add test sample size if available
        } else {
            stats << "Test data: None\n";
        }
        
        return stats.str();
    }
    
    int get_sample_size() {
        return manager.getSampleSz();
    }
    
    bool has_test_data() {
        // FIX: Actually check for test data using VBMManager method
        // getTestData() returns a pointer, so check if it's non-null
        return manager.getTestData() != nullptr;
    }
    
    std::vector<std::string> get_available_search_types() {
        return {"loopless-up", "loopless-down", "full-up", "full-down", 
                "disjoint-up", "disjoint-down", "chain-up", "chain-down"};
    }
    
    // ========== REPORT ACCESS ==========
    
    std::vector<PyModel> get_kept_models() {
        std::vector<PyModel> result;
        for (Model* model : kept_models) {
            result.push_back(modelToPyModel(model));
        }
        return result;
    }
    
    int get_search_model_count() {
        return kept_models.size();
    }
};

// ========== PYBIND11 MODULE DEFINITION ==========

PYBIND11_MODULE(_pyoccam, m) {
    m.doc() = "OCCAM Python bindings - Version 44 with Test Data Support";
    
    // PyModel class
    py::class_<PyModel>(m, "Model")
        .def(py::init<>())
        .def_readwrite("name", &PyModel::name)
        .def_readwrite("h", &PyModel::h)
        .def_readwrite("information", &PyModel::information)
        .def_readwrite("aic", &PyModel::aic)
        .def_readwrite("bic", &PyModel::bic)
        .def_readwrite("daic", &PyModel::daic)
        .def_readwrite("dbic", &PyModel::dbic)
        .def_readwrite("alpha", &PyModel::alpha)
        .def_readwrite("df", &PyModel::df)
        .def_readwrite("lr", &PyModel::lr)
        .def_readwrite("pct_correct_data", &PyModel::pct_correct_data)
        .def_readwrite("pct_correct_test", &PyModel::pct_correct_test)  // ADD
        .def_readwrite("pct_coverage", &PyModel::pct_coverage)  // ADD
        .def_readwrite("pct_missed_test", &PyModel::pct_missed_test)  // ADD
        .def_readwrite("incr_alpha", &PyModel::incr_alpha)
        .def_readwrite("level", &PyModel::level);
    
    // PyVBMManager class
    py::class_<PyVBMManager>(m, "VBMManager")
        .def(py::init<>())
        
        // Initialization
        .def("init_from_command_line", &PyVBMManager::init_from_command_line,
             "Initialize OCCAM from command line arguments")
        
        // Configuration
        .def("set_report_separator", &PyVBMManager::set_report_separator,
             "Set report separator (1=tab, 2=comma, 3=space, 4=HTML)")
        .def("set_report_variables", &PyVBMManager::set_report_variables,
             "Set variables to display in reports")
        .def("set_ref_model", &PyVBMManager::set_ref_model,
             "Set reference model for statistics")
        .def("set_search_type", &PyVBMManager::set_search_type,
             "Set search algorithm type")
        .def("set_debug_mode", &PyVBMManager::set_debug_mode,
             "Enable/disable debug mode")
        
        // Fit configuration
        .def("set_calc_expected_dv", &PyVBMManager::set_calc_expected_dv,
             "Set whether to calculate expected DV values")
        .def("set_skip_trained_model_table", &PyVBMManager::set_skip_trained_model_table,
             "Skip trained model table in output")
        .def("set_skip_ivi_tables", &PyVBMManager::set_skip_ivi_tables,
             "Skip IVI tables in output")
        .def("set_fit_classifier_target", &PyVBMManager::set_fit_classifier_target,
             "Set target state for classifier confusion matrix")
        .def("set_default_fit_model", &PyVBMManager::set_default_fit_model,
             "Set default model for fit comparison")
        
        // Main operations
        .def("generate_search_report", &PyVBMManager::generate_search_report,
             "Generate search report with beam search (auto-includes test columns if test data present)",
             py::arg("search_type"), py::arg("levels"), py::arg("width"), 
             py::arg("include_test_data") = false)
        .def("generate_fit_report", &PyVBMManager::generate_fit_report,
             "Generate complete fit report for a model (auto-includes test performance if test data present)",
             py::arg("model_name"), py::arg("target_state") = "0")
        .def("get_confusion_matrix", &PyVBMManager::get_confusion_matrix,
             "Get confusion matrix for a model as a dictionary with TN, FP, FN, TP and derived metrics",
             py::arg("model_name"), py::arg("target_state") = "0")
        
        // Best model getters
        .def("get_best_model_by_bic", &PyVBMManager::get_best_model_by_bic,
             "Get best model by BIC (most parsimonious)")
        .def("get_best_model_by_aic", &PyVBMManager::get_best_model_by_aic,
             "Get best model by AIC")
        .def("get_best_model_by_information", &PyVBMManager::get_best_model_by_information,
             "Get best model by information (OCCAM manual definition: highest info where ALL steps have Inc.Alpha < 0.05)")
        .def("get_best_model_by_info_alpha", &PyVBMManager::get_best_model_by_info_alpha,
             "DEPRECATED: Use get_best_model_by_information() - returns same result")
        .def("get_best_model_by_raw_information", &PyVBMManager::get_best_model_by_raw_information,
             "Get model with highest raw information (WARNING: may be overfitted, ignores statistical significance)")
        
        // Model operations
        .def("make_model", &PyVBMManager::make_model,
             "Create and optionally fit a model",
             py::arg("model_name"), py::arg("make_fit_table") = false)
        .def("get_model_statistics", &PyVBMManager::get_model_statistics,
             "Get statistics for a specific model")
        
        // Information getters
        .def("get_variable_list", &PyVBMManager::get_variable_list,
             "Get list of variable names")
        .def("get_basic_statistics", &PyVBMManager::get_basic_statistics,
             "Get basic statistics as string")
        .def("get_sample_size", &PyVBMManager::get_sample_size,
             "Get sample size")
        .def("has_test_data", &PyVBMManager::has_test_data,
             "Check if test data is available")
        .def("get_available_search_types", &PyVBMManager::get_available_search_types,
             "Get list of available search types")
        
        // Report access
        .def("get_kept_models", &PyVBMManager::get_kept_models,
             "Get list of kept models from beam search")
        .def("get_search_model_count", &PyVBMManager::get_search_model_count,
             "Get count of kept models");
    
    // Constants
    m.attr("TABSEP") = 1;
    m.attr("COMMASEP") = 2;
    m.attr("SPACESEP") = 3;
    m.attr("HTMLFORMAT") = 4;
    
    m.attr("__version__") = "0.1.3";  // Fixed get_best_model_by_information() to match OCCAM manual
}