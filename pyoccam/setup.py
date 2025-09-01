from setuptools import setup, Extension
from setuptools.command.build_ext import build_ext
import sys
import os
import pybind11

# Automatically detect the directory of this setup.py
here = os.path.abspath(os.path.dirname(__file__))
cpp_dir = os.path.join(here, '..', 'cpp')
include_dir = os.path.join(here, '..', 'include')

ext_modules = [
    Extension(
        'pyoccam',
        sources=[
            os.path.join(cpp_dir, file) for file in [
                'AttributeList.cpp', 'Input.cpp', 'Key.cpp', 'ManagerBase.cpp',
                'ManagerInitFromCommandLine.cpp', 'Model.cpp', 'ModelCache.cpp',
                'OccamMath.cpp', 'Options.cpp', 'RelCache.cpp', 'Relation.cpp',
                'Report.cpp', 'ReportCommon.cpp', 'ReportPrintConditionalDV.cpp',
                'ReportPrintResiduals.cpp', 'ReportQsort.cpp', 'SBMManager.cpp',
                'Search.cpp', 'SearchBase.cpp', 'StateConstraint.cpp', 'Table.cpp',
                'VBMManager.cpp', 'VariableList.cpp', '_Core.cpp'
            ]
        ] + [os.path.join(here, 'pyoccam_pybind11.cpp')],
        include_dirs=[
            pybind11.get_include(),
            include_dir,
            cpp_dir
        ],
        language='c++',
        extra_compile_args=['-std=c++14', '-O2', '-w', '-DMS_WIN64'],
        extra_link_args=['-static']
    ),
]

setup(
    name='pyoccam',
    version='0.1.0',
    author='David Percy',
    author_email='your.email@example.com',
    description='OCCAM Reconstructability Analysis Tools - Python binding',
    ext_modules=ext_modules,
    cmdclass={'build_ext': build_ext},
    zip_safe=False,
        package_data={
            "": ["*.txt", "*.ipynb", "*.py"],
        },
        include_package_data=True,

)
