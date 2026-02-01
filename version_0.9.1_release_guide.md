# PyOccam Version 0.9.1 Release Guide

## What Changed

Updated `setup.py` version from **0.1.2** → **0.9.1**

## Why Version 0.9.1?

This release includes significant improvements:
- ✅ Fixed `skip_ivi_tables` - IVI tables now skipped by default (cleaner output)
- ✅ Added search progress indicator - real-time level-by-level updates
- ✅ Both features work in Jupyter notebooks and Python scripts
- 🎯 Getting close to a 1.0 release!

## Next Steps

### 1. Rebuild All Wheels

Run your build script:
```powershell
build_all_pythons2.bat
```

This will create new wheels in `windows-wheels/`:
- `pyoccam-0.9.1-cp39-cp39-win_amd64.whl`
- `pyoccam-0.9.1-cp310-cp310-win_amd64.whl`
- `pyoccam-0.9.1-cp311-cp311-win_amd64.whl`
- `pyoccam-0.9.1-cp312-cp312-win_amd64.whl`

### 2. Upload to Test PyPI

```powershell
twine upload --repository testpypi windows-wheels\*.whl
```

This should now work since 0.9.1 is a new version!

### 3. Test Installation

Create a fresh conda environment and test:
```powershell
conda create -n test-pyoccam python=3.12 -y
conda activate test-pyoccam
pip install -i https://test.pypi.org/simple/ pyoccam==0.9.1

# Test it
python -c "import pyoccam; print(pyoccam.__version__)"  # Should print: 0.9.1

# Quick functionality test
python -c "
import pyoccam
data = pyoccam.load_dementia()
manager = data.manager
report = manager.generate_search_report('loopless-up', 3, 2)
print('✓ Works!')
"
```

You should see:
```
Level 1/3: X new models, Y kept (total: Z)
Level 2/3: X new models, Y kept (total: Z)
Level 3/3: X new models, Y kept (total: Z)
✓ Works!
```

### 4. Verify Skip IVI Tables

```python
import pyoccam
data = pyoccam.load_dementia()
manager = data.manager
manager.generate_search_report("loopless-up", 3, 2)
best = manager.get_best_model_by_bic()

# Should show just main Conditional DV table (no IVI sub-tables)
fit = manager.generate_fit_report(best, "0")
print(fit)
```

### 5. Tag in Git (Optional)

```bash
git add setup.py
git commit -m "Bump version to 0.9.1"
git tag -a v0.9.1 -m "Release 0.9.1: Progress indicator + skip_ivi_tables fix"
git push origin pyoccam-port --tags
```

## Version History

- **0.1.2** - Initial working release with basic functionality
- **0.9.1** - Progress indicator, skip_ivi_tables default fix, production-ready

## What's New in 0.9.1

### Search Progress Indicator
- Automatically displays level-by-level progress
- Works in Jupyter notebooks and scripts
- No user code required

```
Level 1/7: 4 new models, 3 kept (total: 4)
Level 2/7: 9 new models, 3 kept (total: 7)
...
```

### Cleaner Fit Output
- IVI tables now skipped by default
- Main Conditional DV table (with confusion matrix) always shown
- Users can enable IVI tables: `manager.set_skip_ivi_tables(False)`

### Files Modified
1. `setup.py` - Version bump
2. `pyoccam_pybind11.cpp` - Progress indicator + skip_ivi_tables default
3. `Report.h` - Added skipIVItables parameter
4. `ReportPrintConditionalDV.cpp` - Implemented skip logic

## Ready to Build!

Run `build_all_pythons2.bat` and you're good to go! 🚀
