@echo off
REM Even safer approach - build in a clean copy

echo Building clean PyOccam wheels (clean copy method)...
echo.

REM Create clean pyoccam_clean directory with ONLY what we want
echo Creating clean build directory...
if exist pyoccam_clean rmdir /s /q pyoccam_clean
mkdir pyoccam_clean

REM Copy ONLY the files we want to package
copy pyoccam\__init__.py pyoccam_clean\ >nul
copy pyoccam\pyoccam_demo.py pyoccam_clean\ >nul 2>&1
copy pyoccam\pyoccam_demo.ipynb pyoccam_clean\ >nul 2>&1
copy pyoccam\dementia05.txt pyoccam_clean\ >nul
copy pyoccam\landslides.txt pyoccam_clean\ >nul
copy pyoccam\pyoccam_pybind11.cpp pyoccam_clean\ >nul
copy pyoccam\*.dll pyoccam_clean\ >nul 2>&1
copy pyoccam\*.pyd pyoccam_clean\ >nul 2>&1

echo.
echo Files in clean build directory:
dir pyoccam_clean\*.* 2>nul | find /v "Directory" | find /v "Volume"
echo.

REM Swap directories temporarily
ren pyoccam pyoccam_backup
ren pyoccam_clean pyoccam

REM Clean dist
if exist dist rmdir /s /q dist
mkdir dist

REM Build for each Python version
for %%v in (39 310 311 312) do (
    echo Building for Python 3.%%v...
    call conda activate py%%v 2>nul
    if not errorlevel 1 (
        if exist build rmdir /s /q build
        python setup.py build_ext --compiler=mingw32 bdist_wheel
        call conda deactivate
        echo.
    )
)

REM Restore original directory
ren pyoccam pyoccam_clean
ren pyoccam_backup pyoccam

REM Clean up
rmdir /s /q pyoccam_clean

echo ================================================
echo Build Complete!
echo ================================================
echo.
echo Clean wheels are in dist\
dir dist\*.whl 2>nul | find ".whl"
echo.
pause
