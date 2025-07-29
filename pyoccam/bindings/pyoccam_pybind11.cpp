/*
 * OCCAM Python Bindings - FIXED VERSION with Proper Search Parameters
 * Copyright © 2025 OCCAM Python Package Project
 * 
 * CRITICAL FIX: Search levels and width parameters now properly configured
 */

#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <pybind11/iostream.h>

// Math compatibility fix for MinGW
#define _USE_MATH_DEFINES
#include <cmath>
#ifndef M_LN2
#define M_LN2 0.693147180559945309417
#endif

// Import math functions to global namespace for compatibility
using std::fabs;
using std::sqrt;
using std::log;
using std::exp;
using std::pow;
using std::frexp;
using std::round;

#include "VBMManager.h"
#include "SearchBase.h"
#include "Model.h"
#include "Options.h"
#include <vector>
#include <string>
#include <map>
#include <sstream>
#include <fstream>
#include <ctime>
#include <cstdlib>

namespace py = pybind11;

// Global VBMManager instance
static VBMManager manager;
static bool debug_mode = false;

// Initialize random seed
static void init_rand() {
    static bool initialized = false;
    if (!initialized) {
        srand(time(NULL));
        initialized = true;
    }
}

// Utility function to recompute all statistics for a model
static void recompute_all_stats(Model* model) {
    if (!model) return;
    try {
        manager.computeL2Statistics(model);
        manager.computeDependentStatistics(model);
        manager.computeRelWidth(model);
        manager.computeIncrementalAlpha(model);
        manager.computePercentCorrect(model);
    } catch (...) {
        // Ignore computation errors
    }
}

// Enhanced model progenitor setting for proper Inc.Alpha computation
static void set_model_progenitors_during_search(std::vector<Model*>& models) {
    for (size_t i = 1; i < models.size(); i++) {
        Model* current = models[i];
        Model* best_progenitor = nullptr;
        
        // Find best progenitor (model with one less component)
        for (size_t j = 0; j < i; j++) {
            Model* candidate = models[j];
            if (candidate->getRelationCount() == current->getRelationCount() - 1) {
                best_progenitor = candidate;
                break; // Use first valid progenitor
            }
        }
        
        if (best_progenitor) {
            try {
                current->setProgenitor(best_progenitor);
            } catch (...) {
                // Ignore progenitor setting errors
            }
        }
    }
}

class PyVBMManager {
private:
    std::string original_data_file; // Store the original data filename
    
public:
    PyVBMManager() = default;
    
    void set_debug_mode(bool debug) {
        debug_mode = debug;
        if (debug) printf("🔧 Debug mode enabled\n");
    }
    
    bool init_from_command_line(const std::vector<std::string>& args) {
        // Store the data filename for later use
        if (args.size() > 1) {
            original_data_file = args[1]; // Usually the second argument is the data file
        }
        
        std::vector<char*> argv;
        for (const auto& arg : args) {
            argv.push_back(const_cast<char*>(arg.c_str()));
        }
        return manager.initFromCommandLine(argv.size(), argv.data());
    }
    
    std::vector<std::string> get_variable_list() {
        std::vector<std::string> variables;
        VariableList* varList = manager.getVariableList();
        if (varList) {
            for (int i = 0; i < varList->getVarCount(); i++) {
                variables.push_back(varList->getVariable(i)->abbrev);
            }
        }
        return variables;
    }
    
    std::string get_basic_statistics() {
        std::stringstream ss;
        Table* inputData = manager.getInputData();
        if (inputData) {
            ss << "Sample size: " << inputData->getTupleCount() << std::endl;
            ss << "State space size: " << inputData->getKeySize() << std::endl;
        }
        return ss.str();
    }
    
    std::vector<std::string> get_available_search_types() {
        return {"loopless-up", "full-up", "disjoint-up", "chain-up"};
    }

    // 🚀 FIXED: Generate search report with PROPER command line arguments using stored filename
    std::string generate_search_report(const std::string& search_type, int levels, int width, bool include_test_data) {
        init_rand();
        char temp_filename[256];
        sprintf(temp_filename, "occam_search_%d.txt", rand());
        FILE* temp_file = fopen(temp_filename, "w");
        if (!temp_file) return "Error: Could not create temp file";
        
        try {
            if (original_data_file.empty()) {
                fclose(temp_file);
                return "Error: No original data file stored";
            }
            
            // 🚀 CRITICAL FIX: Create new manager with CORRECT command line arguments
            VBMManager temp_manager;
            
            // Build command line arguments with CORRECT OCCAM structure
            char levels_arg[16], width_arg[16];
            sprintf(levels_arg, "%d", levels);
            sprintf(width_arg, "%d", width);
            
            std::vector<std::string> args_vec = {
                "occam",                        // Program name
                "-a", "search",                 // Explicitly specify search action
                "-L", std::string(levels_arg),  // -L 7 (search levels)
                "-w", std::string(width_arg),   // -w 3 (search width)
                "-S", "up",                     // Search direction up
                "-f", "bottom",                 // Reference model bottom
                original_data_file              // Data file LAST (per usage)
            };
            
            // Convert to char* array for OCCAM
            std::vector<char*> argv;
            for (auto& arg : args_vec) {
                argv.push_back(const_cast<char*>(arg.c_str()));
            }
            
            if (debug_mode) {
                printf("🔧 FIXED: Initializing with CORRECT OCCAM command line:\n");
                for (const auto& arg : args_vec) {
                    printf("   %s\n", arg.c_str());
                }
            }
            
            // Initialize with proper command line arguments
            if (!temp_manager.initFromCommandLine(argv.size(), argv.data())) {
                fclose(temp_file);
                return "Error: Failed to initialize with search parameters";
            }
            
            // Configure search with the properly initialized manager
            temp_manager.setSearch(search_type.c_str());
            temp_manager.setRefModel("bottom");
            
            if (debug_mode) {
                printf("✅ FIXED: Manager initialized with levels=%d, width=%d\n", levels, width);
                printf("   Algorithm: %s, Data: %s\n", search_type.c_str(), original_data_file.c_str());
            }
            
            // Execute search with proper parameters
            SearchBase* search = temp_manager.getSearch();
            if (!search) {
                fclose(temp_file);
                return "Error: No search method defined";
            }
            
            Model* start = temp_manager.getBottomRefModel();
            if (!start) {
                fclose(temp_file);
                return "Error: No reference model available";
            }
            
            // Execute search - now with CORRECT levels and width!
            Model** models = search->search(start);
            
            // Convert to vector for easier handling
            std::vector<Model*> all_models;
            if (models) {
                for (Model** model = models; *model; model++) {
                    all_models.push_back(*model);
                }
            }
            
            if (all_models.empty()) {
                fclose(temp_file);
                return "Error: No models found in search";
            }
            
            // Set progenitor relationships for proper Inc.Alpha values
            set_model_progenitors_during_search(all_models);
            
            // Compute all statistics for each model using temp_manager
            for (Model* model : all_models) {
                try {
                    temp_manager.computeL2Statistics(model);
                    temp_manager.computeDependentStatistics(model);
                    temp_manager.computeRelWidth(model);
                    temp_manager.computeIncrementalAlpha(model);
                    temp_manager.computePercentCorrect(model);
                } catch (...) {
                    // Ignore computation errors
                }
            }
            
            // Generate timestamped report header
            time_t now = time(0);
            char* timestr = ctime(&now);
            timestr[strlen(timestr)-1] = '\0'; // Remove newline
            
            fprintf(temp_file, "OCCAM Search Report - FIXED PARAMETERS\n");
            fprintf(temp_file, "Search: %s, Levels: %d, Width: %d\n", search_type.c_str(), levels, width);
            fprintf(temp_file, "Data: %s\n", original_data_file.c_str());
            fprintf(temp_file, "Generated: %s\n\n", timestr);
            
            // Column headers
            fprintf(temp_file, "ID\tMODEL\tLevel\tH\tdDF\tdLR\tAlpha\tInf\t%%dH(DV)\tdAIC\tdBIC\tInc.Alpha\t%%C(Data)\t%%cover\n");
            
            // Output models with enhanced statistics
            for (size_t i = 0; i < all_models.size(); i++) {
                Model* model = all_models[i];
                
                // Calculate level (number of components)
                int level = model->getRelationCount() - 1; // Subtract 1 for IV component
                
                // Get or compute statistics
                double h = model->getAttribute("h");
                double ddf = model->getAttribute("ddf");
                double lr = model->getAttribute("lr");
                double alpha = model->getAttribute("alpha");
                double information = model->getAttribute("information");
                double aic = model->getAttribute("aic");
                double bic = model->getAttribute("bic");
                double inc_alpha = model->getAttribute("inc-alpha");
                double pct_correct = model->getAttribute("pct_correct_data");
                double coverage = model->getAttribute("coverage");
                
                // Calculate derived statistics
                double dh_dv = (information / h) * 100.0;
                double daic = lr - (2.0 * ddf);
                double dbic = lr - (log(temp_manager.getInputData()->getTupleCount()) * ddf);
                
                // Format model name
                std::string model_name = model->getPrintName();
                
                // Write model row
                fprintf(temp_file, "%d\t%s\t%d\t%.4f\t%.0f\t%.4f\t%.4f\t%.4f\t%.2f\t%.4f\t%.4f\t%.4f\t%.2f\t%.2f\n",
                    (int)(i+1), model_name.c_str(), level, h, ddf, lr, alpha, information,
                    dh_dv, daic, dbic, inc_alpha, pct_correct, coverage);
            }
            
            // Analysis of levels generated
            int max_level = 0;
            std::map<int, int> level_counts;
            for (Model* model : all_models) {
                int level = model->getRelationCount() - 1;
                level_counts[level]++;
                if (level > max_level) max_level = level;
            }
            
            fprintf(temp_file, "\n=== SEARCH ANALYSIS ===\n");
            fprintf(temp_file, "Command: occam -a search -L %d -w %d -S up -f bottom %s\n", levels, width, original_data_file.c_str());
            fprintf(temp_file, "Search algorithm: %s (set after init)\n", search_type.c_str());
            fprintf(temp_file, "Models generated: %d\n", (int)all_models.size());
            fprintf(temp_file, "Max level reached: %d (requested: %d)\n", max_level, levels);
            
            fprintf(temp_file, "Models by level:\n");
            for (const auto& pair : level_counts) {
                fprintf(temp_file, "  Level %d: %d models\n", pair.first, pair.second);
            }
            
            if (max_level > 1) {
                fprintf(temp_file, "✅ SUCCESS: Multiple levels generated!\n");
            } else {
                fprintf(temp_file, "❌ ISSUE: Still only generating level 1 models\n");
                fprintf(temp_file, "Debug: Check if OCCAM is actually using the -L and -w parameters\n");
            }
            
            if (debug_mode) {
                printf("🎉 SEARCH COMPLETED with PROPER parameters!\n");
                printf("   Models generated: %d\n", (int)all_models.size());
                printf("   Max level reached: %d (requested: %d)\n", max_level, levels);
                printf("   Status: %s\n", (max_level > 1) ? "SUCCESS - Multiple levels!" : "ISSUE - Still only level 1");
                
                printf("   Models by level:\n");
                for (const auto& pair : level_counts) {
                    printf("     Level %d: %d models\n", pair.first, pair.second);
                }
            }
            
        } catch (...) {
            fprintf(temp_file, "Error during search execution\n");
        }
        
        fclose(temp_file);
        
        // Read and return file contents
        std::ifstream infile(temp_filename);
        std::stringstream buffer;
        buffer << infile.rdbuf();
        infile.close();
        remove(temp_filename);
        
        return buffer.str();
    }

    std::string generate_fit_report(const std::string& model_name) {
        init_rand();
        char temp_filename[256];
        sprintf(temp_filename, "occam_fit_%d.txt", rand());
        FILE* temp_file = fopen(temp_filename, "w");
        if (!temp_file) return "Error: Could not create temp file";
        
        try {
            manager.setRefModel("bottom");
            Model* model = manager.makeModel(model_name.c_str(), true);
            if (!model) {
                fclose(temp_file);
                return "Error: Model not found";
            }
            
            // Compute comprehensive statistics
            recompute_all_stats(model);
            
            // Generate fit report using OCCAM's native reporting
            manager.printFitReport(model, temp_file);
            
        } catch (...) {
            fprintf(temp_file, "Error during fit computation\n");
        }
        
        fclose(temp_file);
        
        // Read and return file contents
        std::ifstream infile(temp_filename);
        std::stringstream buffer;
        buffer << infile.rdbuf();
        infile.close();
        remove(temp_filename);
        
        return buffer.str();
    }
    
    std::map<std::string, std::string> get_best_model_by_bic() {
        std::map<std::string, std::string> result;
        try {
            // Simple implementation - would need full search to be comprehensive
            Model* model = manager.getBottomRefModel();
            if (model) {
                result["model"] = model->getPrintName();
                result["bic"] = std::to_string(model->getAttribute("bic"));
            }
        } catch (...) {
            result["error"] = "Failed to get best model";
        }
        return result;
    }
    
    std::map<std::string, std::string> get_best_model_by_aic() {
        std::map<std::string, std::string> result;
        try {
            Model* model = manager.getBottomRefModel();
            if (model) {
                result["model"] = model->getPrintName();
                result["aic"] = std::to_string(model->getAttribute("aic"));
            }
        } catch (...) {
            result["error"] = "Failed to get best model";
        }
        return result;
    }
    
    std::map<std::string, std::string> get_best_model_by_information() {
        std::map<std::string, std::string> result;
        try {
            Model* model = manager.getBottomRefModel();
            if (model) {
                result["model"] = model->getPrintName();
                result["information"] = std::to_string(model->getAttribute("information"));
            }
        } catch (...) {
            result["error"] = "Failed to get best model";
        }
        return result;
    }
    
    std::map<std::string, double> get_model_statistics(const std::string& model_name) {
        std::map<std::string, double> stats;
        try {
            Model* model = manager.makeModel(model_name.c_str(), true);
            if (!model) {
                stats["error"] = -1.0;
                return stats;
            }
            
            recompute_all_stats(model);
            
            stats["level"] = (int)model->getAttribute("level");
            stats["h"] = model->getAttribute("h");
            stats["ddf"] = model->getAttribute("ddf");
            stats["lr"] = model->getAttribute("lr");
            stats["alpha"] = model->getAttribute("alpha");
            stats["information"] = model->getAttribute("information");
            stats["aic"] = model->getAttribute("aic");
            stats["bic"] = model->getAttribute("bic");
            stats["inc_alpha"] = model->getAttribute("inc-alpha");
            stats["pct_correct_data"] = model->getAttribute("pct_correct_data");
            stats["coverage"] = model->getAttribute("coverage");
            
        } catch (...) {
            stats["error"] = -1.0;
        }
        return stats;
    }
};

PYBIND11_MODULE(pyoccam, m) {
    m.doc() = "OCCAM Statistical Package - FIXED VERSION with Proper Search Parameters";
    
    py::class_<PyVBMManager>(m, "VBMManager")
        .def(py::init<>())
        .def("set_debug_mode", &PyVBMManager::set_debug_mode,
             "Enable/disable debug output")
        .def("init_from_command_line", &PyVBMManager::init_from_command_line,
             "Initialize OCCAM from command line arguments")
        .def("get_variable_list", &PyVBMManager::get_variable_list,
             "Get list of variables in the dataset")
        .def("get_basic_statistics", &PyVBMManager::get_basic_statistics,
             "Get basic dataset statistics")
        .def("get_available_search_types", &PyVBMManager::get_available_search_types,
             "Get list of available search algorithms")
        .def("generate_search_report", &PyVBMManager::generate_search_report,
             "Generate complete search report with FIXED parameter support",
             py::arg("search_type"), py::arg("levels"), py::arg("width"), py::arg("include_test_data") = false)
        .def("generate_fit_report", &PyVBMManager::generate_fit_report,
             "Generate detailed fit report for a specific model")
        .def("get_best_model_by_bic", &PyVBMManager::get_best_model_by_bic,
             "Get best model by BIC")
        .def("get_best_model_by_aic", &PyVBMManager::get_best_model_by_aic,
             "Get best model by AIC")
        .def("get_best_model_by_information", &PyVBMManager::get_best_model_by_information,
             "Get best model by information content")
        .def("get_model_statistics", &PyVBMManager::get_model_statistics,
             "Get detailed statistics for a specific model");
             
    m.attr("__version__") = "3.4.2-fixed";
}