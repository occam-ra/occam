from setuptools import setup, Extension, find_packages
import sys
import os
import platform  # ADD THIS
import pybind11

# Get Python include directory - FIX FOR LINUX
python_include = os.path.join(sys.prefix, 'Include' if platform.system() == 'Windows' else 'include')

# Platform-specific compile/link args - ADD THIS BLOCK
if platform.system() == 'Windows':
    extra_compile_args = ['-std=c++14', '-O2', '-w', '-DMS_WIN64']
    extra_link_args = []
else:  # Linux/macOS
    extra_compile_args = ['-std=c++14', '-O2']
    extra_link_args = []

ext_modules = [
    Extension(
        'pyoccam._pyoccam',  # CRITICAL: Use _pyoccam to avoid name conflict
        sources=[
            'cpp/AttributeList.cpp',
            'cpp/Input.cpp',
            'cpp/Key.cpp',
            'cpp/ManagerBase.cpp',
            'cpp/ManagerInitFromCommandLine.cpp',
            'cpp/Model.cpp',
            'cpp/ModelCache.cpp',
            'cpp/OccamMath.cpp',
            'cpp/Options.cpp',
            'cpp/RelCache.cpp',
            'cpp/Relation.cpp',
            'cpp/Report.cpp',
            'cpp/ReportCommon.cpp',
            'cpp/ReportPrintConditionalDV.cpp',
            'cpp/ReportPrintResiduals.cpp',
            'cpp/ReportQsort.cpp',
            'cpp/SBMManager.cpp',
            'cpp/Search.cpp',
            'cpp/SearchBase.cpp',
            'cpp/StateConstraint.cpp',
            'cpp/Table.cpp',
            'cpp/VBMManager.cpp',
            'cpp/VariableList.cpp',
            'cpp/_Core.cpp',
            'pyoccam/pyoccam_pybind11.cpp',
        ],
        include_dirs=[
            pybind11.get_include(),
            pybind11.get_include(user=True),
            python_include,
            'include',
            'cpp'
        ],
        language='c++',
        extra_compile_args=extra_compile_args,  # USE VARIABLE
        extra_link_args=extra_link_args        # USE VARIABLE
    ),
]

setup(
    name='pyoccam',
    version='0.9.3',
    author='David Percy',
    author_email='percyd@pdx.edu',
    description='OCCAM Reconstructability Analysis Tools',
    ext_modules=ext_modules,
    packages=find_packages(),  # Use find_packages() to auto-detect
    zip_safe=False,
    package_data={
        'pyoccam': [
            'dementia05.txt',
            'landslides.txt',
            'pyoccam_demo.py',
            'pyoccam_demo.ipynb',
            '*.dll',
            '*.pyd',
        ],
    },
    include_package_data=True,
)