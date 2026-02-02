cd D:\projects\occam
conda activate py39

REM Clean EVERYTHING
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
del pyoccam\*.pyd

REM Build fresh with only _pyoccam
python setup.py build_ext --compiler=mingw32 --inplace

REM Check what got created
dir pyoccam\*.pyd

REM Should only show _pyoccam.cp39-win_amd64.pyd
REM If pyoccam.cp39-win_amd64.pyd exists, delete it:
del pyoccam\pyoccam.cp39-win_amd64.pyd

REM Now build the wheel
python setup.py bdist_wheel

REM Reinstall
pip uninstall pyoccam -y
pip install dist\pyoccam-0.1.2-cp39-cp39-win_amd64.whl

REM Test
python -c "import pyoccam; print(dir(pyoccam)[:10])"