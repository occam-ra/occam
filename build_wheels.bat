@echo off
REM =========================================================
REM Build OCCAM Python Extension with MinGW
REM =========================================================

echo =========================================================
echo  OCCAM Python Package Builder v0.1.2
echo  Using MinGW compiler
echo =========================================================
echo.

REM Step 1: Clean
echo [1/5] Cleaning old build artifacts...
rmdir /s /q build 2>nul
rmdir /s /q dist 2>nul
rmdir /s /q pyoccam.egg-info 2>nul
del pyoccam\*.pyd 2>nul
echo   Done.

REM Step 2: Ensure MinGW DLLs present BEFORE building wheel
echo.
echo [2/5] Copying MinGW runtime DLLs...
REM Try multiple possible MinGW locations
copy C:\mingw64\bin\libgcc_s_seh-1.dll pyoccam\ >nul 2>&1
copy C:\mingw64\bin\libstdc++-6.dll pyoccam\ >nul 2>&1
copy C:\mingw64\bin\libwinpthread-1.dll pyoccam\ >nul 2>&1

REM Also try msys64 path
if not exist "pyoccam\libgcc_s_seh-1.dll" (
    copy C:\msys64\mingw64\bin\libgcc_s_seh-1.dll pyoccam\ >nul 2>&1
    copy C:\msys64\mingw64\bin\libstdc++-6.dll pyoccam\ >nul 2>&1
    copy C:\msys64\mingw64\bin\libwinpthread-1.dll pyoccam\ >nul 2>&1
)

REM Check if DLLs were copied
if not exist "pyoccam\libgcc_s_seh-1.dll" (
    echo WARNING: MinGW DLLs not found! The built wheel may not work.
    echo Please manually copy libgcc_s_seh-1.dll, libstdc++-6.dll, and libwinpthread-1.dll
    echo from your MinGW bin folder to the pyoccam folder.
)

REM Step 3: Build extension
echo.
echo [3/5] Building extension with MinGW...
python setup.py build_ext --compiler=mingw32 --inplace
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ERROR: Build failed!
    pause
    exit /b %ERRORLEVEL%
)

REM Step 4: Verify .pyd created
echo.
echo [4/5] Verifying extension...
if exist "pyoccam.pyd" (
    echo   Found: pyoccam.pyd in root
    move pyoccam.pyd pyoccam\ >nul 2>&1
)
if not exist "pyoccam\pyoccam*.pyd" (
    echo ERROR: Extension not created!
    pause
    exit /b 1
)
echo   Extension created successfully.

REM Step 5: Build wheel
echo.
echo [5/5] Building wheel distribution...
python setup.py bdist_wheel
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Wheel build failed!
    pause
    exit /b %ERRORLEVEL%
)

echo.
echo =========================================================
echo  BUILD COMPLETE!
echo =========================================================
echo.
dir dist\*.whl /b
echo.
echo To install: pip install dist\pyoccam-0.1.2-*.whl
echo To test: python -c "import pyoccam; print(pyoccam.__version__)"
echo.
pause