@echo off
REM Build pyoccam wheels with MinGW

echo ==========================================
echo Building pyoccam Windows wheels with MinGW
echo ==========================================
echo.

REM Clean previous builds
if exist dist rmdir /s /q dist
if exist build rmdir /s /q build
if exist pyoccam.egg-info rmdir /s /q pyoccam.egg-info
if exist pyoccam\*.pyd del pyoccam\*.pyd
mkdir dist

REM Build with explicit MinGW compiler
echo Building with MinGW...
python setup.py build_ext --compiler=mingw32 --inplace
if errorlevel 1 (
    echo ERROR: Build failed!
    pause
    exit /b 1
)

REM Copy MinGW DLLs manually (just to be sure)
echo.
echo Copying MinGW DLLs to pyoccam folder...
copy C:\mingw64\bin\libgcc_s_seh-1.dll pyoccam\ >nul 2>&1
copy C:\mingw64\bin\libstdc++-6.dll pyoccam\ >nul 2>&1
copy C:\mingw64\bin\libwinpthread-1.dll pyoccam\ >nul 2>&1

REM Also try msys64 path
copy C:\msys64\mingw64\bin\libgcc_s_seh-1.dll pyoccam\ >nul 2>&1
copy C:\msys64\mingw64\bin\libstdc++-6.dll pyoccam\ >nul 2>&1
copy C:\msys64\mingw64\bin\libwinpthread-1.dll pyoccam\ >nul 2>&1

REM Build the wheel
echo.
echo Building wheel...
python setup.py bdist_wheel
if errorlevel 1 (
    echo ERROR: Wheel build failed!
    pause
    exit /b 1
)

echo.
echo ==========================================
echo Build complete! Wheels are in dist/
echo ==========================================
dir dist\*.whl

echo.
echo To test:
echo   pip install dist\pyoccam-0.1.0-cp39-cp39-win_amd64.whl
echo   python -c "import pyoccam"
echo.
pause
