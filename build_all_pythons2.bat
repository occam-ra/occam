@echo off
REM build_all_pythons2.bat - Build wheels for all Python versions
REM Cleaned up version

echo ================================================
echo Building PyOccam for All Python Versions
echo ================================================
echo.

REM ============================================================
REM STEP 1: Clean previous builds
REM ============================================================
echo [1/5] Cleaning previous builds...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist windows-wheels rmdir /s /q windows-wheels
if exist pyoccam.egg-info rmdir /s /q pyoccam.egg-info
del /q pyoccam\*.pyd 2>nul

REM Create fresh directories
mkdir dist
mkdir windows-wheels

REM ============================================================
REM STEP 2: Prepare files for packaging
REM ============================================================
echo [2/5] Preparing files for packaging...
mkdir temp_excluded 2>nul

REM Move unwanted files out (preserve demo files and data files)
echo   Moving test/debug files to temp storage...
for %%f in (pyoccam\*.py) do (
    if not "%%~nxf"=="__init__.py" (
        if not "%%~nxf"=="pyoccam_demo.py" (
            move "%%f" temp_excluded\ >nul 2>&1
        )
    )
)

REM Move notebooks (except demo)
for %%f in (pyoccam\*.ipynb) do (
    if not "%%~nxf"=="pyoccam_demo.ipynb" (
        move "%%f" temp_excluded\ >nul 2>&1
    )
)

REM Move text files (except data files)
for %%f in (pyoccam\*.txt) do (
    if not "%%~nxf"=="dementia05.txt" (
        if not "%%~nxf"=="landslides.txt" (
            move "%%f" temp_excluded\ >nul 2>&1
        )
    )
)

REM Move other unwanted files
move pyoccam\*.bat temp_excluded\ 2>nul
move pyoccam\*.md temp_excluded\ 2>nul
move pyoccam\*.csv temp_excluded\ 2>nul

echo   Files ready for packaging:
dir /B pyoccam\*.py pyoccam\*.txt pyoccam\*.ipynb 2>nul

REM ============================================================
REM STEP 3: Ensure MinGW DLLs are present
REM ============================================================
echo [3/5] Checking MinGW DLLs...
set MINGW_BIN=C:\mingw64\bin
if not exist "pyoccam\libgcc_s_seh-1.dll" (
    echo   Copying MinGW DLLs...
    copy "%MINGW_BIN%\libgcc_s_seh-1.dll" pyoccam\ >nul 2>&1
    copy "%MINGW_BIN%\libstdc++-6.dll" pyoccam\ >nul 2>&1
    copy "%MINGW_BIN%\libwinpthread-1.dll" pyoccam\ >nul 2>&1
) else (
    echo   MinGW DLLs already present
)

REM ============================================================
REM STEP 4: Build wheels for all Python versions
REM ============================================================
echo [4/5] Building wheels...
echo.

REM Save current conda environment
for /f "tokens=2" %%i in ('conda info ^| findstr "active environment"') do set ORIGINAL_ENV=%%i

REM Define Python versions to build
set PYTHON_VERSIONS=39 310 311 312
set COUNT=1

for %%v in (%PYTHON_VERSIONS%) do (
    echo ==========================================
    echo [%COUNT%/4] Building for Python 3.%%v
    echo ==========================================
    
    REM Activate environment
    call conda activate py%%v
    if errorlevel 1 (
        echo   Creating py%%v environment...
        call conda create -n py%%v python=3.%%v pybind11 wheel -y
        call conda activate py%%v
    )
    
    REM Show Python version
    echo   Python version:
    python --version
    echo.
    
    REM Clean build folder only (keep dist)
    if exist build rmdir /s /q build
    
    REM Build wheel
    echo   Building wheel...
    python setup.py build_ext --compiler=mingw32 --inplace bdist_wheel
    
    if errorlevel 1 (
        echo   ERROR: Build failed for Python 3.%%v
        call conda deactivate
        goto :error
    )
    
    echo   Wheel created successfully
    echo.
    
    REM Deactivate environment
    call conda deactivate
    
    set /a COUNT+=1
)

REM Return to original environment
echo Returning to original environment: %ORIGINAL_ENV%
call conda activate %ORIGINAL_ENV%

REM ============================================================
REM STEP 5: Organize wheels
REM ============================================================
echo [5/5] Organizing wheels...
echo.
echo Wheels in dist:
dir /B dist\*.whl

echo.
echo Copying to windows-wheels folder...
xcopy dist\*.whl windows-wheels\ /Y /Q

REM ============================================================
REM RESTORE FILES
REM ============================================================
echo.
echo Restoring excluded files...
if exist temp_excluded (
    move temp_excluded\*.* pyoccam\ >nul 2>nul
    rmdir temp_excluded
)

REM ============================================================
REM SUCCESS
REM ============================================================
echo.
echo ================================================
echo BUILD COMPLETE - SUCCESS!
echo ================================================
echo.
echo Wheels created:
dir /B windows-wheels\*.whl
echo.
echo Location: %CD%\windows-wheels\
echo.
echo To test locally:
echo   pip install windows-wheels\pyoccam-0.1.2-cp312-cp312-win_amd64.whl --force-reinstall
echo.
echo To upload to Test PyPI:
echo   twine upload --repository testpypi windows-wheels\*.whl
echo.
goto :end

REM ============================================================
REM ERROR HANDLING
REM ============================================================
:error
echo.
echo ================================================
echo BUILD FAILED!
echo ================================================
echo.
echo Please check the error messages above.
echo.
REM Restore files even on error
if exist temp_excluded (
    move temp_excluded\*.* pyoccam\ >nul 2>nul
    rmdir temp_excluded
)
pause
exit /b 1

:end
pause
