@echo off
REM Build wheels for Python 3.9, 3.10, and 3.11

echo ==========================================
echo Building Windows wheels for all Python versions
echo ==========================================
echo.

REM Clean previous builds
if exist dist rmdir /s /q dist
if exist build rmdir /s /q build
if exist windows-wheels rmdir /s /q windows-wheels
mkdir dist
mkdir windows-wheels

REM Save current conda environment
for /f "tokens=2" %%i in ('conda info ^| findstr "active environment"') do set ORIGINAL_ENV=%%i

REM Build for Python 3.9
echo.
echo [1/4] Building for Python 3.9...
echo --------------------------------
call conda activate py39
if errorlevel 1 (
    echo Creating py39 environment...
    call conda create -n py39 python=3.9 pybind11 -y
    call conda activate py39
)
python --version
python setup.py build_ext --compiler=mingw32 --inplace
python setup.py bdist_wheel
call conda deactivate

REM Build for Python 3.10
echo.
echo [2/4] Building for Python 3.10...
echo ---------------------------------
call conda activate py310
if errorlevel 1 (
    echo Creating py310 environment...
    call conda create -n py310 python=3.10 pybind11 -y
    call conda activate py310
)
python --version
python setup.py build_ext --compiler=mingw32 --inplace
python setup.py bdist_wheel
call conda deactivate

REM Build for Python 3.11
echo.
echo [3/4] Building for Python 3.11...
echo ---------------------------------
call conda activate py311
if errorlevel 1 (
    echo Creating py311 environment...
    call conda create -n py311 python=3.11 pybind11 -y
    call conda activate py311
)
python --version
python setup.py build_ext --compiler=mingw32 --inplace
python setup.py bdist_wheel
call conda deactivate

REM Build for Python 3.12
echo.
echo [4/4] Building for Python 3.12...
echo ---------------------------------
call conda activate py312
if errorlevel 1 (
    echo Creating py312 environment...
    call conda create -n py312 python=3.12 pybind11 -y
    call conda activate py312
)
python --version
python setup.py build_ext --compiler=mingw32 --inplace
python setup.py bdist_wheel
call conda deactivate




REM Return to original environment
call conda activate %ORIGINAL_ENV%

REM Copy all wheels to windows-wheels folder
echo.
echo Copying wheels to windows-wheels folder...
copy dist\*.whl windows-wheels\

echo.
echo ==========================================
echo Build complete!
echo ==========================================
dir windows-wheels\*.whl
echo.
echo Now run:
echo   git add windows-wheels
echo   git commit -m "Add Windows wheels for Python 3.9, 3.10, 3.11, 3.12"
echo   git push origin pyoccam-port
echo.
pause
