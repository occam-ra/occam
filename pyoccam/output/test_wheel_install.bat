@echo off
SETLOCAL

 1. Define virtual environment name
set VENV_NAME=pyoccam2-test-venv

 2. Create fresh venv in current folder (if exists, remove first)
echo.
echo === Removing old virtualenv (if exists) ===
rmdir S Q %VENV_NAME% 2nul

echo.
echo === Creating new virtualenv %VENV_NAME% ===
python -m venv %VENV_NAME%

 3. Activate the venv
call %VENV_NAME%Scriptsactivate

 4. Upgrade pip and install your wheel
echo.
echo === Installing wheel and dependencies ===
pip install --upgrade pip
pip install distpyoccam2-.whl
pip install notebook

 5. Run test script
echo.
echo === Running test script test_exact_server.py ===
python test_exact_server.py

 6. Launch notebook (optional step — comment if not needed)
echo.
echo === Launching Jupyter notebook (optional) ===
start jupyter notebook minimal-occam-notebook.ipynb

 7. Done
echo.
echo === ✅ Wheel installation test complete! ===
pause
ENDLOCAL
