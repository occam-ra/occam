from setuptools import setup, Extension
from setuptools.command.build_ext import build_ext
import sys
import os
import pybind11

here = os.path.abspath(os.path.dirname(__file__))
cpp_dir = os.path.join(here, 'cpp')
include_dir = os.path.join(here, 'include')
binding_cpp = os.path.join(here, 'pyoccam', 'pyoccam_pybind11.cpp')  

# Compiler flags
if sys.platform == 'win32':
    extra_compile_args = ['-std=c++14', '-O2', '-w', '-DMS_WIN64']
    extra_link_args = ['-static']
else:
    extra_compile_args = ['-std=c++14', '-O2', '-w', '-fPIC']
    extra_link_args = []

ext_modules = [
    Extension(
        'pyoccam',
        sources=[
            binding_cpp
        ] + [
            os.path.join(cpp_dir, fname) for fname in [
                'AttributeList.cpp', 'Input.cpp', 'Key.cpp', 'ManagerBase.cpp',
                'ManagerInitFromCommandLine.cpp', 'Model.cpp', 'ModelCache.cpp',
                'OccamMath.cpp', 'Options.cpp', 'RelCache.cpp', 'Relation.cpp',
                'Report.cpp', 'ReportCommon.cpp', 'ReportPrintConditionalDV.cpp',
                'ReportPrintResiduals.cpp', 'ReportQsort.cpp', 'SBMManager.cpp',
                'Search.cpp', 'SearchBase.cpp', 'StateConstraint.cpp', 'Table.cpp',
                'VBMManager.cpp', 'VariableList.cpp', '_Core.cpp'
            ]
        ],
        include_dirs=[
            pybind11.get_include(),
            include_dir,
            cpp_dir
        ],
        language='c++',
        extra_compile_args=extra_compile_args,
        extra_link_args=extra_link_args,
    ),
]

setup(
    name='pyoccam',
    version='0.1.0',
    author='David Percy',
    author_email='your.email@example.com',  # Optional
    description='OCCAM Reconstructability Analysis Tools – Python bindings for model search and fit',
    long_description=open(os.path.join(here, 'README.md')).read() if os.path.exists(os.path.join(here, 'README.md')) else '',
    long_description_content_type='text/markdown',
    url='https://github.com/occam-ra/occam',
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',  # or whatever license you’re using
        'Operating System :: OS Independent',
    ],
    ext_modules=ext_modules,
    cmdclass={'build_ext': build_ext},
    zip_safe=False,
    python_requires='>=3.9',
)
