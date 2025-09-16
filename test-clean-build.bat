@echo off
REM Test clean build with current Python only

echo ========================================================
echo TEST: Clean Build with Current Python
echo ========================================================
echo.

REM Quick check
if not exist pyoccam\pyoccam_pybind11.cpp (
    echo ERROR: Missing pyoccam\pyoccam_pybind11.cpp
    pause
    exit /b 1
)

REM Create test directory for moved files
mkdir TEMP_TEST 2>nul

REM Show current state
echo Current pyoccam contents:
dir pyoccam\*.py pyoccam\*.txt pyoccam\*.csv pyoccam\*.ipynb 2>nul | find /c /v ""
echo files total
echo.

REM Move files
echo Moving unwanted files to TEMP_TEST...
move pyoccam\test*.py TEMP_TEST\ >nul 2>&1
move pyoccam\debug*.py TEMP_TEST\ >nul 2>&1
move pyoccam\diagnose*.py TEMP_TEST\ >nul 2>&1
move pyoccam\verify*.py TEMP_TEST\ >nul 2>&1
move pyoccam\check*.py TEMP_TEST\ >nul 2>&1
move pyoccam\examine*.py TEMP_TEST\ >nul 2>&1
move pyoccam\find*.py TEMP_TEST\ >nul 2>&1
move pyoccam\final*.py TEMP_TEST\ >nul 2>&1
move pyoccam\utils.py TEMP_TEST\ >nul 2>&1
move pyoccam\manager.py TEMP_TEST\ >nul 2>&1
move pyoccam\exceptions.py TEMP_TEST\ >nul 2>&1
move pyoccam\simple*.py TEMP_TEST\ >nul 2>&1
move pyoccam\pyoccam2*.py TEMP_TEST\ >nul 2>&1
move pyoccam\*.csv TEMP_TEST\ >nul 2>&1

REM Move output text files (keep only dementia05.txt and landslides.txt)
for %%f in (pyoccam\*.txt) do (
    if not "%%~nxf"=="dementia05.txt" (
        if not "%%~nxf"=="landslides.txt" (
            move "%%f" TEMP_TEST\ >nul 2>&1
        )
    )
)

REM Move extra notebooks (keep only pyoccam_demo.ipynb)
for %%f in (pyoccam\*.ipynb) do (
    if not "%%~nxf"=="pyoccam_demo.ipynb" (
        move "%%f" TEMP_TEST\ >nul 2>&1
    )
)

echo.
echo After moving, pyoccam contains:
dir pyoccam\*.py pyoccam\*.txt pyoccam\*.ipynb 2>nul
echo.
echo Building wheel with current Python...
echo.

REM Build with current Python
python setup.py build_ext --compiler=mingw32 bdist_wheel --dist-dir dist_test

if errorlevel 1 (
    echo.
    echo BUILD FAILED!
    echo Restoring files...
) else (
    echo.
    echo BUILD SUCCESSFUL!
    echo.
    echo Checking wheel contents:
    python -c "import zipfile, glob; w=glob.glob('dist_test/*.whl')[0]; zf=zipfile.ZipFile(w); files=[f for f in zf.namelist() if 'pyoccam/' in f]; print(f'  Total files in pyoccam/: {len(files)}'); py_files=[f for f in files if f.endswith(\".py\")]; print(f'  Python files: {len(py_files)}'); print('  Python files in wheel:'); [print(f'    - {f}') for f in py_files]"
)

REM Restore files
echo.
echo Restoring files...
move TEMP_TEST\*.* pyoccam\ >nul 2>&1
rmdir TEMP_TEST

echo.
echo Test complete. Check dist_test\ for the wheel.
pause
