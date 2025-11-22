# C++ Compiler Warning Analysis Summary
**Build:** C++ with -O2 optimization
**Total Warnings:** 40 (19 maybe-uninitialized + 21 unused-parameter)
**Date:** 2025-11-22

---

## Maybe-Uninitialized Warning Categories (19 total)

### 1. Pointer Variables (2 warnings)
### 2. Test Data Arrays (5 warnings)
### 3. Confusion Matrix Values (8 warnings)
### 4. Test Statistics (2 warnings)
### 5. ManagerBase Variables (2 warnings)

**Result:** 5 potential bugs, 14 false positives

---

## Unused Parameter Warning Categories (21 total)

### 1. Conditional Compilation Functions (6 warnings)
- logMemory (5 params), logProjection (1 param)
- Used only when debugging enabled

### 2. Signal Handlers (2 warnings)
- segfault_handler, fpe_handler
- Required by POSIX signal() API

### 3. Virtual/Override Functions (1 warning)
- SearchBase::search - base class stub

### 4. Algorithm Functions (2 warnings)
- computeH (unused SB), computeTransmission (unused method)
- Possible refactoring artifacts

### 5. Stub Functions (2 warnings)
- fitTestAlgebraic (unused model), projectedModel (unused projectTo)
- Incomplete implementation or future feature

### 6. Callback Signatures (2 warnings)
- tableAction lambda - must match iterator signature

### 7. API Consistency (2 warnings)
- Key::setKeyValue, Key::getKeyValue (unused keysize)
- Could add bounds checking

### 8. Refactored Functions (4 warnings)
- printConfusionMatrixStatsHTML/CSV (unused dv_name, dv_target)
- TODO comment already notes this

**Result:** 10 cannot change, 1 intentional, 10 need review

---

## Overall Summary

**Total:** 40 warnings
- **High priority fixes:** 4 maybe-uninitialized bugs
- **Functions to review:** 10 unused parameters
- **Safe to ignore:** 26 warnings (14 false positives + 12 intentional)

---
