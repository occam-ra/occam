@echo off
echo ============================================================
echo BUILDING pyoccam WHEEL AND EXTENSION
echo ============================================================

REM Activate your conda environment if needed
REM call C:\Users\bjpd\anaconda3\Scripts\activate.bat pyoccam-build

echo Cleaning previous build artifacts...
rmdir /s /q build
rmdir /s /q dist
rmdir /s /q pyoccam.egg-info

echo.
echo ============================================================
echo 🚀 BUILDING PYOCCAM EXTENSION USING MinGW
echo ============================================================
python setup.py build_ext --inplace --compiler=mingw32

echo.
echo ============================================================
echo 🛞 BUILDING PYPI WHEEL
echo ============================================================
python setup.py bdist_wheel

echo.
echo ============================================================
echo ✅ pyoccam Build Complete!
echo Wheel is located in: dist\pyoccam-*.whl
echo ============================================================

pause
