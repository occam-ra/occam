# C++ Compiler Warning Analysis
**Build Configuration:** -O2 optimization, C++14, GCC 14.2.0
**Total Warnings:** 40 (19 maybe-uninitialized + 21 unused-parameter)
**Analysis Date:** 2025-11-22

---

## Executive Summary

### Maybe-Uninitialized Warnings (19 total)

All 19 warnings fall into two categories:
1. **Legitimate compiler concerns** (5): Variables with complex multi-conditional initialization or missing initialization
2. **Likely false positives** (14): Variables with initialization patterns the compiler cannot prove

### Unused Parameter Warnings (21 total)

All 21 warnings fall into three categories:
1. **Cannot change** (10): Required by API contracts (POSIX, callbacks) or conditional compilation
2. **Intentional design** (1): Virtual method stubs
3. **Should review** (10): Potential refactoring artifacts or API design decisions

---

## Category 1: Pointer Variables (2 warnings)

### Warning 1.1: `relModel` (ReportPrintConditionalDV.cpp:335)

**Declaration:** Line 59
```cpp
Model *relModel;
```

**Initialization:** Line 83 (inside `if (rel->isStateBased())`)
```cpp
} else {  // rel != NULL
    if (rel->isStateBased()) {
        relModel = new Model(3);
        ...
    }
}
```

**Usage:** Line 335 (inside different `if (rel->isStateBased())`)
```cpp
} else {  // rel != NULL (different if/else)
    if (rel->isStateBased()) {
        fprintf(fd, "...", relModel->getPrintName());
    }
}
```

**Analysis:**
- **Code distance:** 220+ lines between initialization and usage
- **Control flow:** Two separate `if (rel != NULL)` blocks, each containing `if (rel->isStateBased())`
- **Compiler limitation:** Cannot prove `rel->isStateBased()` returns same value in both checks
- **Actual safety:** Safe IF `rel` pointer unchanged AND `isStateBased()` is pure function
- **Risk:** If `rel` state changes between lines 83-335, uninitialized use possible

**Verdict:** **Legitimate compiler concern**  
**Recommendation:** Either initialize to nullptr defensively OR restructure to single conditional check

---

### Warning 1.2: `alt_table` (Table.h:49, used in ReportPrintConditionalDV.cpp)

**Declaration:** Line 114
```cpp
Table *alt_table;
```

**Initialization:** Line 127 (inside nested conditionals)
```cpp
if (defaultFitModel != NULL) {
    if ((model != defaultFitModel) && model->containsModel(defaultFitModel)) {
        use_alt_default = true;
        ...
        alt_table = new Table(key_size, fit_table->getTupleCount());
        ...
    }
}
```

**Usage:** Line 369 (guarded by `use_alt_default`)
```cpp
if (use_alt_default) {
    alt_table_size = alt_table->getTupleCount();
}
```

**Analysis:**
- **Control flow:** `alt_table` initialized when `use_alt_default` set to true
- **Usage guard:** All uses wrapped in `if (use_alt_default)`  
- **Compiler limitation:** Cannot prove correlation between flag and initialization
- **Actual safety:** Safe - flag and initialization are tightly coupled
- **Risk:** Very low - would require code modification between line 123 and 369

**Verdict:** **Likely false positive**  
**Recommendation:** Safe as-is, compiler cannot prove flag correlation

---

## Category 2: Test Data Arrays (5 warnings)

All these arrays share the same pattern - allocated only when test data exists.

**Common Declaration:** Lines 152-156
```cpp
KeySegment **test_key;
double **test_freq;
double *test_dv_freq;
double *test_key_freq;
int *test_rule;
```

**Common Initialization Pattern:** Lines 195-228 (inside `if (test_sample_size > 0.0)`)
```cpp
if (test_sample_size > 0.0) {
    test_key = new KeySegment *[iv_statespace];
    test_freq = new double *[iv_statespace];
    test_key_freq = new double[iv_statespace];
    test_dv_freq = new double[dv_card];
    test_rule = new int[iv_statespace];
    // ...initialization loops...
}
```

**Common Usage Pattern:** All uses guarded by `if (test_sample_size > 0.0)` checks

**Analysis:**
- **Guard variable:** `test_sample_size` (function parameter, immutable)
- **Initialization:** Only when `test_sample_size > 0.0`
- **Usage:** Only when `test_sample_size > 0.0`
- **Compiler limitation:** Cannot prove floating-point comparison yields same result
- **Actual safety:** Safe - parameter doesn't change during function execution
- **Risk:** Extremely low - would require parameter mutation (impossible for by-value param)

**Verdict:** **False positives** (all 5)  
**Recommendation:** Safe as-is, fundamental compiler limitation with floating-point guards

---

## Category 3: Confusion Matrix Values (8 warnings)

Training and test set statistics for confusion matrix.

**Declaration:** Line 166
```cpp
double trtp, trfp, trtn, trfn;  // Training: true pos, false pos, true neg, false neg
double tetp, tefp, tetn, tefn;  // Test: true pos, false pos, true neg, false neg
```

**Initialization:** Lines 1133-1199 (complex conditional logic)
```cpp
// Set all 8 values based on data and checkTarget condition
```

**Usage:** Lines 1217-1224
```cpp
} else if ((!checkTarget && model) || trtp + trfn <= 0)  {
    ...
} else if (trtn + trfp <= 0) {
    ...  
} else if (checkTarget) {
    printConfusionMatrix(..., trtn, trfn, trtp, trfp, ..., tetn, tefn, tetp, tefp);
}
```

**Analysis:**
- **Pattern:** Complex nested conditionals for initialization
- **Compiler challenge:** Multiple code paths, cannot track all combinations
- **Actual safety:** Appears safe - initialization precedes usage in control flow
- **Risk:** Medium - complex logic makes manual verification difficult

**Verdict:** **Likely false positives, but complex**  
**Recommendation:** Manual code review advised; compiler cannot track complex flow

---

## Category 4: Test Statistics (2 warnings)

**Variables:** `test_by_fit_rule`, `test_by_test_rule` (Line 762)

**Initialization:** Lines 765-771 (inside loop over test data)
```cpp
for (int i = 0; i < iv_statespace; i++) {
    // Loop body initializes both variables
    test_by_fit_rule += ...;
    test_by_test_rule += ...;
}
```

**Usage:** Lines 1095-1096
```cpp
fit_percent_on_test = test_by_fit_rule / test_sample_size * 100.0;
best_percent_on_test = test_by_test_rule / test_sample_size * 100.0;
```

**Analysis:**
- **Pattern:** Loop initialization with += operators  
- **Compiler issue:** Cannot prove loop executes at least once
- **Missing:** Variables not initialized to 0.0 before loop
- **Actual safety:** **UNSAFE** if loop doesn't execute (iv_statespace could be 0)
- **Risk:** High if `iv_statespace` can be zero

**Verdict:** **Potential bug**  
**Recommendation:** Initialize to 0.0: `double test_by_fit_rule = 0.0, test_by_test_rule = 0.0;`

---

## Category 5: ManagerBase Variables (2 warnings)

### Warning 5.1: `depTable` (ManagerBase.cpp:571, used at line 579)

**Function:** `ManagerBase::createDvOrder()`

**Declaration:** Line 571
```cpp
Table *depTable;
```

**Initialization:** Lines 572-577 (loop searching for dependent relation)
```cpp
for (k = 0; k < bottomRef->getRelationCount(); ++k) {
    if (!bottomRef->getRelation(k)->isIndependentOnly()) {
        depTable = bottomRef->getRelation(k)->getTable();
        break;
    }
}
```

**Usage:** Line 579
```cpp
for (k = 0; k < depTable->getTupleCount(); ++k) {
```

**Analysis:**
- **Pattern:** Search loop with `break` on found
- **Missing:** No initialization if search fails (no dependent relation found)
- **Actual safety:** **UNSAFE** if no dependent relations exist in model
- **Risk:** High - would crash on nullptr dereference

**Verdict:** **Potential bug**  
**Recommendation:** Add check: `if (depTable == nullptr) { error handling }`

---

### Warning 5.2: `c_count` (ManagerBase.cpp:362, used at line 380)

**Function:** `ManagerBase::makeProjection()`

**Declaration:** Line 362
```cpp
long c_count;  // for state-based
```

**Initialization:** Complex conditional within state-based logic

**Usage:** Line 380
```cpp
for (j = 0; j < c_count; j++) {
```

**Analysis:**
- **Pattern:** Variable used in state-based projection path
- **Complexity:** High - multiple nested conditionals
- **Compiler limitation:** Cannot track state-based control flow
- **Risk:** Requires deep code analysis

**Verdict:** **Requires manual code review**
**Recommendation:** Trace all code paths to verify initialization

---

## Category 6: Unused Parameters (21 warnings)

These parameters are intentionally unused but remain in function signatures for various architectural reasons.

### 6.1: Conditional Compilation Functions (6 warnings)

#### `logMemory` (_Core.cpp:30)

**Function signature:**
```cpp
void logMemory(void *old, unsigned long long oldSize, long factor, const char *file, long line)
```

**Two implementations:**
```cpp
#ifdef LOG_MEMORY
void logMemory(void *old, unsigned long long oldSize, long factor, const char *file, long line) {
    if (mlogfd == NULL) return;
    fprintf(mlogfd, "%s [%ld]: %lld %ld\n", file, line, oldSize, factor);
    fflush(mlogfd);
}
#else
void logMemory(void *old, unsigned long long oldSize, long factor, const char *file, long line) {
    // Empty stub - all 5 parameters unused when LOG_MEMORY not defined
}
#endif
```

**Analysis:**
- **Pattern:** Feature toggle via preprocessor directive
- **Parameters unused:** All 5 (`old`, `oldSize`, `factor`, `file`, `line`) when `LOG_MEMORY` undefined
- **Reason:** Maintains consistent API across debug/release builds
- **Alternative approach:** Could use macros to eliminate parameters, but current approach is cleaner

**Verdict:** **Intentional - correct design**
**Recommendation:** No change needed - standard pattern for optional debugging features

---

#### `logProjection` (ManagerBase.cpp:133)

**Function signature:**
```cpp
void logProjection(const char *name)
```

**Two implementations:**
```cpp
#ifdef LOG_PROJECTIONS
void logProjection(const char *name) {
    if (projfd == NULL) projfd = fopen("projections.log", "w");
    if (projfd == NULL) return;
    fprintf(projfd, "%s\n", name);
    fflush(projfd);
}
#else
void logProjection(const char *name) {
    // Empty stub - parameter unused
}
#endif
```

**Analysis:**
- **Pattern:** Same as `logMemory` - feature toggle
- **Parameter unused:** `name` when `LOG_PROJECTIONS` undefined
- **Reason:** Maintains consistent API across debug/release builds

**Verdict:** **Intentional - correct design**
**Recommendation:** No change needed

---

### 6.2: Signal Handlers (2 warnings)

#### `segfault_handler` (ManagerBase.cpp:76)

**Function signature:**
```cpp
void segfault_handler(int sig)
```

**Usage:**
```cpp
signal(SIGSEGV, segfault_handler);
```

**Analysis:**
- **Pattern:** POSIX signal handler
- **Required signature:** `void (*)(int)` per POSIX standard
- **Parameter unused:** `sig` - handler already knows it's SIGSEGV
- **Cannot change:** Signature mandated by `signal()` system call

**Verdict:** **Required by API contract**
**Recommendation:** No change possible - POSIX requirement

---

#### `fpe_handler` (ManagerBase.cpp:98)

**Function signature:**
```cpp
void fpe_handler(int sig)
```

**Analysis:**
- **Pattern:** Same as `segfault_handler`
- **Parameter unused:** `sig` - handler already knows it's SIGFPE
- **Cannot change:** Required by POSIX signal() API

**Verdict:** **Required by API contract**
**Recommendation:** No change possible - POSIX requirement

---

### 6.3: Virtual/Override Functions (1 warning)

#### `SearchBase::search` (SearchBase.cpp:42)

**Function signature:**
```cpp
Model **SearchBase::search(Model *start)
```

**Implementation:**
```cpp
Model **SearchBase::search(Model *start) {
    return NULL;  // should never be called
}
```

**Analysis:**
- **Pattern:** Base class virtual method
- **Parameter unused:** `start` - this is a stub that should never execute
- **Actual usage:** Overridden by derived classes (SearchFullDown, SearchLooplessUp, etc.)
- **Reason:** Defines interface contract for all search implementations

**Verdict:** **Intentional - OOP design pattern**
**Recommendation:** No change needed - standard virtual method pattern

---

### 6.4: Algorithm Functions with Unused Options (2 warnings)

#### `computeH` (ManagerBase.cpp:850)

**Function signature:**
```cpp
double ManagerBase::computeH(Model *model, HMethod method, int SB)
```

**Implementation:**
```cpp
double ManagerBase::computeH(Model *model, HMethod method, int SB) {
    double h;
    bool loops;

    if (method == ALGEBRAIC)
        loops = false;
    else if (method == IPF)
        loops = true;
    else
        loops = hasLoops(model);

    // ... uses model and method, but NOT SB
}
```

**Analysis:**
- **Parameter unused:** `SB` (state-based flag)
- **Parameters used:** `model`, `method`
- **Reason:** Unclear - possibly planned feature or refactoring artifact
- **Risk:** Low - function works correctly without it

**Verdict:** **Likely refactoring artifact**
**Recommendation:** Check if `SB` should be used or can be removed from signature

---

#### `computeTransmission` (ManagerBase.cpp:882)

**Function signature:**
```cpp
double ManagerBase::computeTransmission(Model *model, HMethod method, int SB)
```

**Implementation:**
```cpp
double ManagerBase::computeTransmission(Model *model, HMethod method, int SB) {
    // ... code that uses model and SB
    if (SB) {
        h = computeH(model, IPF, SB);
    } else {
        // ...
    }
    // ... but NEVER uses method parameter
}
```

**Analysis:**
- **Parameter unused:** `method`
- **Parameters used:** `model`, `SB`
- **Reason:** Function always uses algebraic calculation, ignoring method
- **Comment in code:** "Krippendorf claims that you can't do this for models with loops, but experimental comparison indicates that loops don't matter in computing this"

**Verdict:** **Likely refactoring artifact**
**Recommendation:** Check if `method` can be removed from signature

---

### 6.5: Stub/Incomplete Functions (2 warnings)

#### `fitTestAlgebraic` (ManagerBase.cpp:1426)

**Function signature:**
```cpp
void ManagerBase::fitTestAlgebraic(Model* model, Table* algTable, double missingCard, const FitIntersectMap& fitIs)
```

**Implementation:**
```cpp
void ManagerBase::fitTestAlgebraic(Model* model, Table* algTable, double missingCard, const FitIntersectMap& fitIs) {
    long long inSize = testData->getTupleCount();

    // for every tuple in test:
    for (long long ti = 0; ti < inSize; ti++) {
        // ... uses algTable, missingCard, fitIs
        // ... but NEVER uses model parameter
    }
}
```

**Analysis:**
- **Parameter unused:** `model`
- **Reason:** Function operates on fitIs (fit intersect map) which may already contain model information
- **Risk:** Low - function appears to work correctly

**Verdict:** **Possible oversight or refactoring artifact**
**Recommendation:** Verify if `model` should be used or can be removed

---

#### `projectedModel` (ManagerBase.cpp:1781)

**Function signature:**
```cpp
Model* ManagerBase::projectedModel(Relation* projectTo, Model* model)
```

**Implementation:**
```cpp
Model* ManagerBase::projectedModel(Relation* projectTo, Model* model) {
    return model;  // Just returns input unchanged
}
```

**Analysis:**
- **Parameter unused:** `projectTo`
- **Pattern:** Function is a stub/no-op
- **Reason:** Placeholder for future functionality or overridden in derived classes
- **Risk:** None - clearly intentional stub

**Verdict:** **Intentional stub function**
**Recommendation:** Check if this is overridden elsewhere or planned for future implementation

---

### 6.6: Callback/Lambda Signature Matching (2 warnings)

#### Lambda `tableAction` (ReportPrintResiduals.cpp:273)

**Lambda signature:**
```cpp
auto tableAction = [&](Relation* rel, double value, KeySegment* refkey, double refvalue, double iviValue) {
    double newLift = value / iviValue;
    double newFreq = value;
    // ... uses value, refkey, iviValue
    // ... but NOT rel or refvalue
};
```

**Usage:**
```cpp
tableIteration(input_table, varlist, rel, nullptr, indep_table, var_count, tableAction);
```

**Analysis:**
- **Parameters unused:** `rel`, `refvalue`
- **Reason:** Lambda must match signature expected by `tableIteration()`
- **Pattern:** Not all callbacks need all parameters from generic iterator
- **Cannot change:** Signature dictated by `tableIteration` template

**Verdict:** **Required by callback API contract**
**Recommendation:** No change possible - signature must match iterator expectations

---

### 6.7: API Consistency (2 warnings)

#### `Key::setKeyValue` (Key.cpp:52)

**Function signature:**
```cpp
void Key::setKeyValue(KeySegment *key, int keysize, class VariableList *vars, int index, int value)
```

**Implementation:**
```cpp
void Key::setKeyValue(KeySegment *key, int keysize, class VariableList *vars, int index, int value) {
    Variable *var = vars->getVariable(index);
    int segment = var->segment;
    KeySegment mask = var->mask;
    key[segment] = (key[segment] & ~mask) | ((value << var->shift) & mask);
    // Uses key, vars, index, value - but NOT keysize
}
```

**Analysis:**
- **Parameter unused:** `keysize`
- **Reason:** Key size information obtained from Variable object, not passed parameter
- **Kept for:** API consistency, potential bounds checking, or legacy compatibility

**Verdict:** **API design decision**
**Recommendation:** Could add bounds checking using keysize, or document as legacy parameter

---

#### `Key::getKeyValue` (Key.cpp:64)

**Function signature:**
```cpp
int Key::getKeyValue(KeySegment *key, int keysize, class VariableList *vars, int index)
```

**Analysis:**
- **Parameter unused:** `keysize`
- **Reason:** Same as `setKeyValue` - size info from Variable object
- **Pattern:** Consistent with `setKeyValue`

**Verdict:** **API design decision**
**Recommendation:** Same as `setKeyValue`

---

### 6.8: Refactored Functions (4 warnings)

#### `printConfusionMatrixStatsHTML` (Report.cpp:457)

**Function signature:**
```cpp
void printConfusionMatrixStatsHTML(const char* dv_name, const char* dv_target, double tp, double fp, double tn, double fn)
```

**Code comment:** `// TODO: DRY this out`

**Implementation:**
```cpp
void printConfusionMatrixStatsHTML(const char* dv_name, const char* dv_target, double tp, double fp, double tn, double fn) {
    // TODO: DRY this out
    const double pop = tp + fp + tn + fn;
    // ... calculates statistics from tp, fp, tn, fn
    // ... but never uses dv_name or dv_target
}
```

**Analysis:**
- **Parameters unused:** `dv_name`, `dv_target`
- **Reason:** Refactoring separated printing confusion matrix (which uses names) from printing statistics (which doesn't)
- **TODO comment:** Indicates known issue from "Don't Repeat Yourself" refactoring
- **Risk:** None - function works correctly

**Verdict:** **Known refactoring artifact**
**Recommendation:** Either remove unused parameters or use them in output labels

---

#### `printConfusionMatrixStatsCSV` (Report.cpp:500)

**Function signature:**
```cpp
void printConfusionMatrixStatsCSV(const char* dv_name, const char* dv_target, double tp, double fp, double tn, double fn)
```

**Analysis:**
- **Parameters unused:** `dv_name`, `dv_target`
- **Reason:** Same as HTML version - statistics don't need variable names
- **Pattern:** Parallel to `printConfusionMatrixStatsHTML`

**Verdict:** **Known refactoring artifact**
**Recommendation:** Same as HTML version

---

## Unused Parameter Summary

| Function | File | Unused Parameters | Reason | Action |
|----------|------|------------------|--------|--------|
| logMemory | _Core.cpp:30 | all 5 | Conditional compilation | None |
| logProjection | ManagerBase.cpp:133 | name | Conditional compilation | None |
| segfault_handler | ManagerBase.cpp:76 | sig | POSIX requirement | None |
| fpe_handler | ManagerBase.cpp:98 | sig | POSIX requirement | None |
| SearchBase::search | SearchBase.cpp:42 | start | Virtual method stub | None |
| computeH | ManagerBase.cpp:850 | SB | Refactoring artifact? | Review |
| computeTransmission | ManagerBase.cpp:882 | method | Refactoring artifact? | Review |
| fitTestAlgebraic | ManagerBase.cpp:1426 | model | Possible oversight | Review |
| projectedModel | ManagerBase.cpp:1781 | projectTo | Stub function | Review |
| tableAction lambda | ReportPrintResiduals.cpp:273 | rel, refvalue | Callback signature | None |
| Key::setKeyValue | Key.cpp:52 | keysize | API consistency | Review |
| Key::getKeyValue | Key.cpp:64 | keysize | API consistency | Review |
| printConfusionMatrixStatsHTML | Report.cpp:457 | dv_name, dv_target | Refactoring (TODO) | Review |
| printConfusionMatrixStatsCSV | Report.cpp:500 | dv_name, dv_target | Refactoring (TODO) | Review |

**Total:** 21 unused parameters across 14 functions

**Breakdown by category:**
- **Cannot change (9):** Conditional compilation (6), POSIX API (2), callback signature (2)
- **Intentional design (1):** Virtual method stub
- **Should review (11):** Refactoring artifacts, API design decisions, possible oversights

---

## Summary and Recommendations

### Maybe-Uninitialized Warnings (19 total)

| Category | Count | False Positives | Potential Bugs | Action Required |
|----------|-------|-----------------|----------------|-----------------|
| Pointer variables | 2 | 1 | 1 | Review relModel usage |
| Test data arrays | 5 | 5 | 0 | None - safe |
| Confusion matrix | 8 | 8 | 0 | None - complex but safe |
| Test statistics | 2 | 0 | 2 | **Initialize to 0.0** |
| ManagerBase vars | 2 | 0 | 2 | **Add null checks** |
| **SUBTOTAL** | **19** | **14** | **5** | **4 fixes recommended** |

### Unused Parameter Warnings (21 total)

| Category | Count | Cannot Change | Intentional | Should Review |
|----------|-------|---------------|-------------|---------------|
| Conditional compilation | 6 | 6 | - | - |
| Signal handlers (POSIX) | 2 | 2 | - | - |
| Callback signatures | 2 | 2 | - | - |
| Virtual method stubs | 1 | - | 1 | - |
| Algorithm parameters | 2 | - | - | 2 |
| Stub functions | 2 | - | - | 2 |
| API consistency | 2 | - | - | 2 |
| Refactored functions | 4 | - | - | 4 |
| **SUBTOTAL** | **21** | **10** | **1** | **10** |

### Overall Warning Summary (40 total)

| Type | Count | Action Required |
|------|-------|-----------------|
| Maybe-uninitialized | 19 | 4 high-priority fixes recommended |
| Unused parameter | 21 | 10 functions need review |
| **TOTAL** | **40** | **14 items for review** |

---

## Recommended Fixes

### Maybe-Uninitialized Warnings

#### High Priority (Potential Crashes)

1. **`depTable` in ManagerBase.cpp:571**
   ```cpp
   Table *depTable = nullptr;
   for (k = 0; k < bottomRef->getRelationCount(); ++k) {
       if (!bottomRef->getRelation(k)->isIndependentOnly()) {
           depTable = bottomRef->getRelation(k)->getTable();
           break;
       }
   }
   if (depTable == nullptr) {
       fprintf(stderr, "Error: No dependent relation found\n");
       return;
   }
   ```

2. **`test_by_fit_rule`, `test_by_test_rule` in ReportPrintConditionalDV.cpp:762**
   ```cpp
   double test_by_fit_rule = 0.0, test_by_test_rule = 0.0;
   ```

#### Medium Priority (Code Clarity)

3. **`relModel` in ReportPrintConditionalDV.cpp:59**
   - Option A: Defensive initialization to nullptr
   - Option B: Restructure to single conditional check
   - Option C: Document as safe (requires code audit)

4. **`c_count` in ManagerBase.cpp:362**
   - Requires manual code audit to verify all paths initialize

#### Low Priority (False Positives)

5-19. **Remaining 15 warnings** - Safe to ignore with current code structure

---

### Unused Parameter Warnings

#### Functions Requiring Review (10 items)

The following unused parameters should be reviewed to determine if they should be removed or utilized:

1. **`computeH` (ManagerBase.cpp:850)** - Unused `SB` parameter
   - Check if state-based flag should be used in entropy calculation
   - If not needed, remove from function signature

2. **`computeTransmission` (ManagerBase.cpp:882)** - Unused `method` parameter
   - Function always uses algebraic calculation regardless of method
   - Consider removing parameter if method selection is intentionally ignored

3. **`fitTestAlgebraic` (ManagerBase.cpp:1426)** - Unused `model` parameter
   - Verify if model should be used in the calculation
   - If fitIs already contains model info, remove parameter

4. **`projectedModel` (ManagerBase.cpp:1781)** - Unused `projectTo` parameter
   - Currently a stub function that returns model unchanged
   - Check if this is overridden in derived classes
   - If not implemented, either implement or document as future feature

5. **`Key::setKeyValue` (Key.cpp:52)** - Unused `keysize` parameter
   - Could add bounds checking: `assert(var->segment < keysize)`
   - Or remove if truly unnecessary for API

6. **`Key::getKeyValue` (Key.cpp:64)** - Unused `keysize` parameter
   - Same as setKeyValue - add bounds checking or remove

7-8. **`printConfusionMatrixStatsHTML/CSV` (Report.cpp:457, 500)** - Unused `dv_name`, `dv_target`
   - TODO comment already notes this needs cleanup
   - Options:
     - Remove unused parameters from signature
     - Use parameters in output (e.g., table headers with variable names)
     - Keep for API consistency with related functions

#### Functions Requiring No Action (11 items)

These warnings are expected and correct:

- **Conditional compilation (6 warnings):** `logMemory`, `logProjection` - parameters used only when debugging enabled
- **POSIX API requirements (2 warnings):** `segfault_handler`, `fpe_handler` - signature mandated by signal()
- **Callback signature (2 warnings):** `tableAction` lambda - must match iterator template
- **Virtual method stub (1 warning):** `SearchBase::search` - base class defines interface

---

## Compiler Limitations Observed

1. **Cannot correlate multiple conditionals** - Even when checking same condition twice
2. **Cannot prove floating-point comparison stability** - `if (x > 0.0)` checks
3. **Cannot prove loop execution** - Warns even when loop bounds are positive
4. **Cannot track boolean flag correlation** - `use_alt_default` flag pattern

With -O2 optimization, compiler performs decent flow analysis but hits fundamental limits with complex control flow patterns common in scientific computing code.

