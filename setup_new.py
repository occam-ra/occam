# Updated setup.py for pyoccam v0.9.0
# Shows how to include examples (scripts + notebooks)

from setuptools import setup, Extension, find_packages
from pathlib import Path
import sys

# Read README for long description
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding='utf-8')

# C++ extension configuration
ext_modules = [
    Extension(
        'pyoccam',
        sources=[
            'pyoccam_pybind11.cpp',
            'cpp/_Core.cpp',
            'cpp/AttributeList.cpp',
            'cpp/Input.cpp',
            'cpp/Key.cpp',
            'cpp/ManagerBase.cpp',
            'cpp/ManagerInitFromCommandLine.cpp',
            'cpp/Model.cpp',
            'cpp/ModelCache.cpp',
            'cpp/OccamMath.cpp',
            'cpp/Options.cpp',
            'cpp/Relation.cpp',
            'cpp/RelCache.cpp',
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
            'cpp/Variable.cpp',
            'cpp/VariableList.cpp',
        ],
        include_dirs=['includes'],
        extra_compile_args=['-std=c++11'] if sys.platform != 'win32' else ['/std:c++14'],
        language='c++'
    ),
]

setup(
    name='pyoccam',
    version='0.9.0',
    author='Martin Zwick, Occam-RA Team',
    author_email='your-email@example.com',
    description='Python bindings for Occam - Reconstructability Analysis',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/occam-ra/occam',
    
    # ============================================================
    # PACKAGES: Include main package AND examples subpackage
    # ============================================================
    packages=[
        'pyoccam',                      # Main package
        'pyoccam.examples',             # Examples package (scripts + notebooks)
    ],
    
    # ============================================================
    # PACKAGE DATA: Include data files, scripts, and notebooks
    # ============================================================
    package_data={
        'pyoccam': [
            '*.txt',                    # Sample data files (dementia05.txt, landslides.txt)
        ],
        'pyoccam.examples': [
            'README.md',                # Quick start guide
            '*.py',                     # All Python demo scripts
            '*.ipynb',                  # All Jupyter notebooks
        ],
    },
    
    # ============================================================
    # INCLUDE NON-PYTHON FILES
    # ============================================================
    include_package_data=True,
    
    # ============================================================
    # COMMAND-LINE TOOLS
    # ============================================================
    entry_points={
        'console_scripts': [
            'pyoccam-examples=pyoccam.examples:cli_main',
        ],
    },
    
    # ============================================================
    # EXTENSION MODULE (C++ code)
    # ============================================================
    ext_modules=ext_modules,
    
    # ============================================================
    # DEPENDENCIES
    # ============================================================
    install_requires=[
        'numpy>=1.19.0',
    ],
    
    # ============================================================
    # METADATA
    # ============================================================
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Programming Language :: C++',
        'Topic :: Scientific/Engineering :: Information Analysis',
    ],
    python_requires='>=3.9',
    keywords='reconstructability analysis, discrete multivariate analysis, information theory',
)

# ==================================================================
# INSTALLATION NOTES
# ==================================================================
"""
This setup.py will create the following structure when installed:

site-packages/
└── pyoccam/
    ├── __init__.py
    ├── pyoccam.pyd (or .so)       # Compiled C++ extension
    ├── dementia05.txt              # Sample data 1
    ├── landslides.txt              # Sample data 2
    └── examples/
        ├── __init__.py
        ├── README.md
        ├── basic_analysis.py
        ├── basic_analysis.ipynb
        ├── advanced_analysis.py
        └── advanced_analysis.ipynb

Users can access examples via:
1. import pyoccam; pyoccam.list_examples()
2. import pyoccam; pyoccam.copy_examples()
3. pyoccam-examples --copy
4. from pyoccam.examples import basic_analysis; basic_analysis.main()
"""
