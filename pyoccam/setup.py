from setuptools import setup, Extension
from setuptools.command.build_ext import build_ext
import sys
import os
import shutil
import pybind11

# Compiler flags - EXACTLY FROM YOUR WORKING VERSION
if sys.platform == 'win32':
    extra_compile_args = ['-std=c++14', '-O2', '-w', '-DMS_WIN64']
    extra_link_args = ['-static']  # CRITICAL - THIS PREVENTS -lpython39 ERROR!
else:
    extra_compile_args = ['-std=c++14', '-O2', '-w', '-fPIC']
    extra_link_args = []

# CORRECTED: pyoccam_pybind11.cpp is already IN pyoccam folder
ext_modules = [
    Extension(
        'pyoccam.pyoccam',  # This creates pyoccam/pyoccam.pyd for packaging
        sources=[
            'pyoccam/pyoccam_pybind11.cpp'  # Already in pyoccam/
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

# Custom build_ext to copy DLLs after building
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
            
            pyoccam_dir = 'pyoccam'
            
            for dll_name in dll_names:
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

# Create/update __init__.py for the package
pyoccam_dir = 'pyoccam'
init_file = os.path.join(pyoccam_dir, '__init__.py')
if not os.path.exists(init_file) or os.path.getsize(init_file) < 50:
    with open(init_file, 'w') as f:
        f.write("""# pyoccam package
from .pyoccam import *
import os
from pathlib import Path

__version__ = '0.1.0'

# Get the package directory
PACKAGE_DIR = Path(__file__).parent

# Helper functions for accessing packaged data
def get_data_file(filename):
    \"\"\"Get the full path to a packaged data file\"\"\"
    path = PACKAGE_DIR / filename
    if path.exists():
        return str(path)
    else:
        raise FileNotFoundError(f"Data file '{filename}' not found in package")

def list_data_files():
    \"\"\"List all available data files\"\"\"
    return [f.name for f in PACKAGE_DIR.glob("*.txt") if f.is_file()]

# Convenience paths for common data files (if they exist)
try:
    DEMENTIA_DATA = get_data_file("dementia05.txt")
except FileNotFoundError:
    DEMENTIA_DATA = None
""")
    print(f"Created/updated {init_file}")

# Package data - EXPLICIT list, no wildcards!
package_data = {
    'pyoccam': [
        # Compiled extensions (these wildcards are OK as they're specific)
        '*.pyd',               # Windows compiled extension
        '*.so',                # Linux/Mac compiled extension
        
        # Windows DLLs - explicit names only
        'libgcc_s_seh-1.dll',
        'libstdc++-6.dll', 
        'libwinpthread-1.dll',
        
        # Data files - EXPLICIT list only
        'dementia05.txt',
        'dementia05ApEdC.txt', 
        'landslides.txt',
        'SY_sample_pts_to_occam3_shuffle_split42_hdr.txt',
        
        # Demo files - EXPLICIT list only
        'pyoccam_demo.py',
        'pyoccam_demo.ipynb',
        
        # CSV files - EXPLICIT list only (comment out if not needed)
        # 'dementia05_search_fullup.csv',
        # 'dementia05_fit_IV_ApZ_EdZ_CZ.csv',
        # 'SY_sample_pts_to_occam3_shuffle_split42_hdr_search_loopless.csv',
        # 'SY_sample_pts_to_occam3_shuffle_split42_hdr_search_full_up.csv',
    ],
}

setup(
    name='pyoccam',
    version='0.1.0',
    author='David Percy',
    author_email='percyd@pdx.edu',
    description='OCCAM Reconstructability Analysis Tools - Python bindings for model search and fit',
    long_description=open('README.md').read() if os.path.exists('README.md') else '',
    long_description_content_type='text/markdown',
    url='https://github.com/occam-ra/occam',
    classifiers=[
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
        'Operating System :: OS Independent',
    ],
    packages=['pyoccam'],
    package_data=package_data,
    include_package_data=False,  # Use explicit package_data instead of MANIFEST.in
    ext_modules=ext_modules,
    cmdclass={'build_ext': build_ext_with_dlls},
    zip_safe=False,
    python_requires='>=3.9',
)

print("\n" + "=" * 50)
print("OCCAM Python Package Setup")
print("=" * 50)
print("Files are already in pyoccam/ folder")
print("Extension will be built as: pyoccam/pyoccam.pyd")
print("Package will include only specified data files")
print("=" * 50 + "\n")
