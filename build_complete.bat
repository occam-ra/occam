@echo off
REM =========================================================
REM Complete Build Script for OCCAM Python Extension
REM This avoids the -lpython39 error by using our fixed setup
REM =========================================================

echo =========================================================
echo  OCCAM Python Package Builder (MinGW)
echo =========================================================
echo.

REM Step 1: Clean everything
echo [1/5] Cleaning old build artifacts...
rmdir /s /q build 2>nul
rmdir /s /q dist 2>nul
rmdir /s /q pyoccam.egg-info 2>nul
del pyoccam\*.pyd 2>nul
del pyoccam\*.dll 2>nul
echo   Done.

REM Step 2: Build extension
echo.
echo [2/5] Building extension with MinGW...
python setup.py build_ext --compiler=mingw32 --inplace
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ERROR: Build failed!
    echo.
    echo Common fixes:
    echo   1. Make sure pybind11 is installed: pip install pybind11
    echo   2. Check that MinGW is in your PATH
    echo   3. Verify all .cpp files exist in cpp/ folder
    echo.
    pause
    exit /b %ERRORLEVEL%
)
echo   Success! Built pyoccam\pyoccam.pyd

REM Step 3: Copy DLLs
echo.
echo [3/5] Copying MinGW runtime DLLs...
call copy_dlls.bat
if not exist "pyoccam\libgcc_s_seh-1.dll" (
    echo.
    echo WARNING: DLLs not copied. Trying manual copy...
    
    REM Try to find in PATH
    where libgcc_s_seh-1.dll >nul 2>&1
    if %ERRORLEVEL% EQU 0 (
        for /f "tokens=*" %%i in ('where libgcc_s_seh-1.dll') do (
            copy "%%i" "pyoccam\" >nul 2>&1
            echo   Found in PATH: %%i
        )
    )
)

REM Step 4: Build wheel
echo.
echo [4/5] Building wheel for distribution...
python setup.py bdist_wheel
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ERROR: Wheel build failed!
    pause
    exit /b %ERRORLEVEL%
)

REM Step 5: Verify
echo.
echo [5/5] Verifying build...
echo.
echo Contents of pyoccam folder:
dir pyoccam\*.* /b
echo.
echo Wheels created:
dir dist\*.whl /b

REM Quick test
echo.
echo =========================================================
echo  BUILD COMPLETE!
echo =========================================================
echo.
echo Testing import...
python -c "import pyoccam; print('SUCCESS: pyoccam imported successfully!')" 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo WARNING: Import test failed. 
    echo This might be normal if you haven't installed the package yet.
)

echo.
echo To install the wheel:
echo   pip install dist\pyoccam-0.1.0-cp*-cp*-win_amd64.whl
echo.
echo To upload to TestPyPI:
echo   twine upload --repository testpypi dist\*.whl
echo.
pause
