from setuptools import setup, Extension
from setuptools.command.build_ext import build_ext
import sys
import os
import shutil
import glob
import pybind11

# Compiler flags - EXACTLY FROM YOUR WORKING VERSION
if sys.platform == 'win32':
    extra_compile_args = ['-std=c++14', '-O2', '-w', '-DMS_WIN64']
    extra_link_args = ['-static']  # CRITICAL - THIS PREVENTS -lpython39 ERROR!
else:
    extra_compile_args = ['-std=c++14', '-O2', '-w', '-fPIC']
    extra_link_args = []

# YOUR WORKING EXTENSION DEFINITION - WITH RELATIVE PATHS!
ext_modules = [
    Extension(
        'pyoccam.pyoccam',  # This creates pyoccam/pyoccam.pyd for packaging
        sources=[
            'pyoccam/pyoccam_pybind11.cpp'  # RELATIVE path
        ] + [
            'cpp/' + fname for fname in [  # RELATIVE paths
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
            'include',  # RELATIVE path
            'cpp'       # RELATIVE path
        ],
        language='c++',
        extra_compile_args=extra_compile_args,
        extra_link_args=extra_link_args,
        libraries=[],  # Just in case - prevents -lpython39
    ),
]

# NEW: Custom build_ext to copy DLLs after building
class build_ext_with_dlls(build_ext):
    def run(self):
        super().run()
        
        # After building, copy MinGW DLLs to pyoccam folder
        if sys.platform == 'win32':
            print("\nCopying MinGW DLLs to pyoccam folder...")
            
            dll_names = [
                'libgcc_s_seh-1.dll',
                'libstdc++-6.dll',
                'libwinpthread-1.dll'
            ]
            
            # Try to find DLLs in common locations
            dll_paths = [
                r'C:\mingw64\bin',
                r'C:\msys64\mingw64\bin',
                os.path.join(os.environ.get('CONDA_PREFIX', ''), 'Library', 'mingw-w64', 'bin'),
            ]
            
            # Also check if DLLs are already in pyoccam folder (from build_wheels.bat)
            pyoccam_dir = 'pyoccam'  # RELATIVE path
            os.makedirs(pyoccam_dir, exist_ok=True)
            
            for dll_name in dll_names:
                # Check if already copied by build_wheels.bat
                dest_path = os.path.join(pyoccam_dir, dll_name)
                if os.path.exists(dest_path):
                    print(f"  {dll_name} already present")
                    continue
                    
                # Try to find and copy
                for dll_path in dll_paths:
                    source_path = os.path.join(dll_path, dll_name)
                    if os.path.exists(source_path):
                        shutil.copy2(source_path, dest_path)
                        print(f"  Copied {dll_name}")
                        break
                else:
                    print(f"  WARNING: Could not find {dll_name}")

# NEW: Create __init__.py for the package
pyoccam_dir = 'pyoccam'  # RELATIVE path
init_file = os.path.join(pyoccam_dir, '__init__.py')
if not os.path.exists(init_file):
    os.makedirs(pyoccam_dir, exist_ok=True)
    with open(init_file, 'w') as f:
        f.write("# pyoccam package\nfrom .pyoccam import *\n__version__ = '0.1.0'\n")

# NEW: Package configuration to include DLLs in wheel
package_data = {
    'pyoccam': ['*.dll', '*.pyd', '*.so'],  # Include all DLLs and extensions
}

# YOUR WORKING SETUP CONFIGURATION + PACKAGE ADDITIONS
setup(
    name='pyoccam',
    version='0.1.0',
    author='David Percy',
    author_email='your.email@example.com',
    description='OCCAM Reconstructability Analysis Tools - Python bindings for model search and fit',
    long_description=open('README.md').read() if os.path.exists('README.md') else '',  # RELATIVE path
    long_description_content_type='text/markdown',
    url='https://github.com/occam-ra/occam',
    classifiers=[
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
        'Operating System :: OS Independent',
    ],
    packages=['pyoccam'],  # NEW: Define package
    package_data=package_data,  # NEW: Include DLLs in package
    include_package_data=True,  # NEW: Include all package data
    ext_modules=ext_modules,
    cmdclass={'build_ext': build_ext_with_dlls},  # NEW: Use custom build to copy DLLs
    zip_safe=False,
    python_requires='>=3.9',
)

print("\n" + "=" * 50)
print("OCCAM Python Package Setup")
print("=" * 50)
print("Extension will be built as: pyoccam/pyoccam.pyd")
print("DLLs will be copied to: pyoccam/*.dll")
print("Wheel will include everything in pyoccam/")
print("=" * 50 + "\n")
