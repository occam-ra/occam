/*
 * Copyright Ã‚Â© 1990 The Portland State University OCCAM Project Team
 * [This program is licensed under the GPL version 3 or later.]
 * Please see the file LICENSE in the source
 * distribution of this software for license terms.
 */

#ifndef ___ConfusionMatrixValues
#define ___ConfusionMatrixValues

#include <cstring>  // For strcmp in isFor() method

/**
 * ConfusionMatrixValues - Confusion Matrix Storage Structure
 * 
 * PURPOSE:
 * This struct stores confusion matrix values for a specific model and target state,
 * enabling efficient programmatic access to classification performance metrics
 * without requiring text parsing of OCCAM output.
 * 
 * LIFECYCLE:
 * 1. CREATION: Allocated as a member of ManagerBase
 * 2. POPULATION: Filled by Report::printConditional_DV() during fit report generation
 * 3. STORAGE: Persisted in ManagerBase so it outlives temporary Report objects
 * 4. RETRIEVAL: Accessed by Python bindings via get_confusion_matrix()
 * 
 * CACHING STRATEGY:
 * Values are cached with their associated model name and target state.
 * The cache remains valid until:
 * - A new model is analyzed (call clearMainModelConfusionMatrix())
 * - A different target state is requested
 * 
 * THE DOUBLE-SWAP PATTERN:
 * OCCAM handles the "dual problem" for negative class classification by internally
 * swapping positive/negative designations. To ensure Python receives values that
 * match the printed output, the storage code in ReportPrintConditionalDV.cpp
 * applies the same swap when storing values. See ReportPrintConditionalDV.cpp
 * line ~1220 for detailed explanation.
 * 
 * USAGE EXAMPLE (from Python):
 *   cm = manager.get_confusion_matrix("IV:ApZ:EdZ:CZ", "0")
 *   print(f"TN={cm['TN']}, TP={cm['TP']}")
 *   print(f"Accuracy={cm['accuracy']}")
 */
struct ConfusionMatrixValues {
    // === TRAINING DATA CONFUSION MATRIX ===
    // Core 2x2 matrix values for classification performance
    double train_tn = 0.0;  // True Negatives: correctly predicted negative class
    double train_fp = 0.0;  // False Positives: incorrectly predicted positive class
    double train_fn = 0.0;  // False Negatives: incorrectly predicted negative class
    double train_tp = 0.0;  // True Positives: correctly predicted positive class
    
    // === TEST DATA CONFUSION MATRIX (OPTIONAL) ===
    // Same metrics computed on held-out test data if available
    double test_tn = 0.0;   // Test set True Negatives
    double test_fp = 0.0;   // Test set False Positives
    double test_fn = 0.0;   // Test set False Negatives
    double test_tp = 0.0;   // Test set True Positives
    
    // === METADATA FOR CACHE VALIDATION ===
    // These fields identify which model and target state these values correspond to,
    // enabling efficient cache validation in get_confusion_matrix()
    char model_name[256] = "";    // Model notation (e.g., "IV:ApZ:EdZ:CZ")
    char target_state[64] = "";   // Target state for "negative" class (e.g., "0")
    
    // === STATUS FLAGS ===
    bool has_values = false;      // True if training CM was successfully computed
    bool has_test_data = false;   // True if test data CM was successfully computed
    
    // === CONSTRUCTORS ===
    // Default constructor initializes all fields to zero/false/empty
    ConfusionMatrixValues() = default;
    
    // === HELPER METHODS ===
    /**
     * Check if these cached CM values match a specific model and target state.
     * Used by get_confusion_matrix() to determine if cached values are still valid.
     * 
     * @param model Model notation to check (e.g., "IV:ApZ")
     * @param target Target state to check (e.g., "0")
     * @return true if this CM is for the requested model/target and has valid values
     */
    bool isFor(const char* model, const char* target) const {
        return has_values && 
               strcmp(model_name, model) == 0 && 
               strcmp(target_state, target) == 0;
    }
};

#endif // ___ConfusionMatrixValues
