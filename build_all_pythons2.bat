@echo off
REM build-all-pythons-fixed.bat - Build wheels for all Python versions

echo ================================================
echo Building PyOccam for All Python Versions
echo ================================================
echo.

REM Clean previous builds
echo Cleaning previous builds...
rmdir /s /q build 2>nul
rmdir /s /q dist 2>nul
rmdir /s /q pyoccam.egg-info 2>nul
del /q pyoccam\*.pyd 2>nul

REM Create fresh dist directory
mkdir dist

REM Move extra files temporarily to avoid inclusion
echo Creating temporary storage for extra files...
mkdir temp_excluded 2>nul

REM Move debug/test scripts out
move pyoccam\*.py temp_excluded\ 2>nul
move pyoccam\*.ipynb temp_excluded\ 2>nul


REM Move output files out
move pyoccam\*.csv temp_excluded\ 2>nul
move pyoccam\*.txt temp_excluded\ 2>nul

REM Copy included files back
move temp_excluded\pyoccam_demo.py pyoccam\ 2>nul
move temp_excluded\pyoccam_demo.ipynb pyoccam\ 2>nul
move temp_excluded\dementia05.txt pyoccam\ 2>nul
move temp_excluded\landslides.txt pyoccam\ 2>nul



REM Build wheels for Python 3.9, 3.10, 3.11, 3.12

echo ==========================================
echo Building Windows wheels for all Python versions
echo ==========================================
echo.

REM Clean ONCE at the beginning
if exist dist rmdir /s /q dist
if exist windows-wheels rmdir /s /q windows-wheels
mkdir dist
mkdir windows-wheels

REM Ensure MinGW DLLs are in pyoccam folder
echo Ensuring MinGW DLLs are present...
if not exist "pyoccam\libgcc_s_seh-1.dll" (
    copy C:\mingw64\bin\libgcc_s_seh-1.dll pyoccam\ >nul 2>&1
    copy C:\mingw64\bin\libstdc++-6.dll pyoccam\ >nul 2>&1
    copy C:\mingw64\bin\libwinpthread-1.dll pyoccam\ >nul 2>&1
)

REM Save current conda environment
for /f "tokens=2" %%i in ('conda info ^| findstr "active environment"') do set ORIGINAL_ENV=%%i

REM Build for Python 3.9
echo.
echo [1/4] Building for Python 3.9...
echo --------------------------------
call conda activate py39
if errorlevel 1 (
    echo Creating py39 environment...
    call conda create -n py39 python=3.9 pybind11 wheel -y
    call conda activate py39
)
python --version
REM Only clean build folder, NOT dist
if exist build rmdir /s /q build
python setup.py build_ext --compiler=mingw32 --inplace bdist_wheel
echo Wheels in dist after Python 3.9:
dir dist\*.whl /b
call conda deactivate

REM Build for Python 3.10
echo.
echo [2/4] Building for Python 3.10...
echo ---------------------------------
call conda activate py310
if errorlevel 1 (
    echo Creating py310 environment...
    call conda create -n py310 python=3.10 pybind11 wheel -y
    call conda activate py310
)
python --version
REM Only clean build folder, NOT dist
if exist build rmdir /s /q build
python setup.py build_ext --compiler=mingw32 --inplace bdist_wheel
echo Wheels in dist after Python 3.10:
dir dist\*.whl /b
call conda deactivate

REM Build for Python 3.11
echo.
echo [3/4] Building for Python 3.11...
echo ---------------------------------
call conda activate py311
if errorlevel 1 (
    echo Creating py311 environment...
    call conda create -n py311 python=3.11 pybind11 wheel -y
    call conda activate py311
)
python --version
REM Only clean build folder, NOT dist
if exist build rmdir /s /q build
python setup.py build_ext --compiler=mingw32 --inplace bdist_wheel
echo Wheels in dist after Python 3.11:
dir dist\*.whl /b
call conda deactivate

REM Build for Python 3.12
echo.
echo [4/4] Building for Python 3.12...
echo ---------------------------------
call conda activate py312
if errorlevel 1 (
    echo Creating py312 environment...
    call conda create -n py312 python=3.12 pybind11 wheel -y
    call conda activate py312
)
python --version
REM Only clean build folder, NOT dist
if exist build rmdir /s /q build
python setup.py build_ext --compiler=mingw32 --inplace bdist_wheel
echo Wheels in dist after Python 3.12:
dir dist\*.whl /b
call conda deactivate

REM Return to original environment
call conda activate %ORIGINAL_ENV%

REM Copy all wheels to windows-wheels folder
echo.
echo Final dist contents before copy:
dir dist\*.whl /b
echo.
echo Copying wheels to windows-wheels folder...
xcopy dist\*.whl windows-wheels\ /Y

echo.
echo ==========================================
echo Build complete!
echo ==========================================
echo.
echo Wheels in windows-wheels:
dir windows-wheels\*.whl /b
echo.
pause

echo.
echo ================================================
echo Restoring excluded files...
echo ================================================
move temp_excluded\*.* pyoccam\ 2>nul
rmdir temp_excluded

echo.
echo ================================================
echo Build Complete!
echo ================================================
echo.
echo Wheels created in dist\:
dir /B dist\*.whl

echo.
echo To install for testing:
echo   pip install dist\pyoccam-0.1.2-cp39-cp39-win_amd64.whl
echo.
pause