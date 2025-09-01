@echo off
REM =========================================================
REM Build OCCAM Python Extension + Wheels with MinGW
REM =========================================================

echo Cleaning old build artifacts...
rmdir /s /q build 2>nul
rmdir /s /q dist 2>nul
rmdir /s /q pyoccam.egg-info 2>nul

echo.
echo Building in-place extension (pyoccam.pyd) with MinGW...
python setup.py build_ext --compiler=mingw32 --inplace
if %ERRORLEVEL% NEQ 0 (
    echo Build failed!
    pause
    exit /b %ERRORLEVEL%
)

echo.
echo Building wheel for distribution...
python setup.py build_ext --compiler=mingw32 bdist_wheel
if %ERRORLEVEL% NEQ 0 (
    echo Wheel build failed!
    pause
    exit /b %ERRORLEVEL%
)

echo.
echo =========================================================
echo  OCCAM Python Build Complete!
echo  In-place module: pyoccam\pyoccam.pyd
echo  Wheel package:   dist\*.whl
echo =========================================================
pause
