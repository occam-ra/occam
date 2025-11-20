# Building pyoccam with pybind11

## Prerequisites

### System Packages (Debian/Ubuntu)
```bash
sudo apt-get update
sudo apt-get install -y \
    build-essential \
    g++ \
    libgmp3-dev \
    libboost-math-dev \
    python3-dev \
    python3-pip
```

### Python Packages
```bash
pip3 install pybind11
```

## Build Steps

### Option 1: Manual Build (Development)

```bash
cd /usr/local/src/occam

# Build the C++ library
cd cpp
make clean
make

# This creates liboccam3.so in the cpp/ directory
```

### Option 2: Using setup.py (To Be Created)

A proper `setup.py` using pybind11's build helpers would automate this process:

```python
# setup.py (to be created in pyoccam/)
from setuptools import setup, Extension
from pybind11.setup_helpers import Pybind11Extension, build_ext

ext_modules = [
    Pybind11Extension(
        "_pyoccam",
        ["pyoccam_pybind11.cpp"],
        include_dirs=["../include"],
        libraries=["gmp", "occam3"],
        library_dirs=["../cpp"],
        extra_compile_args=["-std=c++11"],
    ),
]

setup(
    name="pyoccam",
    version="0.1.3",
    author="OCCAM Project Team",
    description="Python 3 bindings for OCCAM Reconstructability Analysis",
    ext_modules=ext_modules,
    cmdclass={"build_ext": build_ext},
    zip_safe=False,
)
```

Then build with:
```bash
cd pyoccam
python3 setup.py build_ext --inplace
```

### Option 3: Using CMake (Recommended for Complex Builds)

Create `CMakeLists.txt` in `pyoccam/`:

```cmake
cmake_minimum_required(VERSION 3.12)
project(pyoccam)

set(CMAKE_CXX_STANDARD 11)

# Find Python and pybind11
find_package(Python3 COMPONENTS Interpreter Development REQUIRED)
find_package(pybind11 CONFIG REQUIRED)

# Find GMP
find_library(GMP_LIBRARY gmp REQUIRED)

# Include directories
include_directories(${CMAKE_SOURCE_DIR}/../include)

# Link to existing OCCAM library
link_directories(${CMAKE_SOURCE_DIR}/../cpp)

# Create Python module
pybind11_add_module(_pyoccam pyoccam_pybind11.cpp)

# Link libraries
target_link_libraries(_pyoccam PRIVATE occam3 gmp boost_math_c99)

# Set output directory
set_target_properties(_pyoccam PROPERTIES
    LIBRARY_OUTPUT_DIRECTORY ${CMAKE_SOURCE_DIR}
)
```

Then build:
```bash
cd pyoccam
mkdir build
cd build
cmake ..
make
# Module is created in pyoccam/_pyoccam.so
```

## Testing the Build

```bash
cd pyoccam
python3 -c "import _pyoccam; print('SUCCESS'); print(dir(_pyoccam))"
```

Should output:
```
SUCCESS
['COMMASEP', 'HTMLFORMAT', 'Model', 'SBMManager', 'SPACESEP', 'TABSEP', 'VBMManager', '__doc__', '__file__', '__loader__', '__name__', '__package__', '__spec__', '__version__']
```

## Creating Wheels for Distribution

### Using cibuildwheel (Recommended)

This builds wheels for multiple platforms:

```bash
pip3 install cibuildwheel

cd pyoccam
cibuildwheel --platform linux
# Creates wheels in wheelhouse/
```

### Manual Wheel Build

```bash
cd pyoccam
python3 setup.py bdist_wheel
# Creates wheel in dist/
```

## Installation

### From Source
```bash
cd pyoccam
pip3 install .
```

### From Wheel
```bash
pip3 install pyoccam-0.1.3-cp310-cp310-linux_x86_64.whl
```

## Troubleshooting

### Error: "cannot find -loccam3"

The C++ library hasn't been built yet:
```bash
cd /usr/local/src/occam/cpp
make
```

### Error: "gmp.h: No such file or directory"

Install GMP development package:
```bash
sudo apt-get install libgmp3-dev
```

### Error: "pybind11/pybind11.h: No such file or directory"

Install pybind11:
```bash
pip3 install pybind11
```

Or for system-wide install:
```bash
sudo apt-get install pybind11-dev
```

### Import Error: "undefined symbol"

The module was built against a different version of the C++ library. Rebuild both:
```bash
cd /usr/local/src/occam/cpp
make clean
make
cd ../pyoccam
python3 setup.py build_ext --inplace
```

## Platform-Specific Notes

### macOS
```bash
brew install gmp boost python3
pip3 install pybind11
```

### Windows
Use Visual Studio with vcpkg:
```cmd
vcpkg install gmp:x64-windows boost:x64-windows pybind11:x64-windows
```

## Next Steps

After successful build:
1. Run tests: `python3 test_pyoccam.py`
2. Install for Flask app: `pip3 install .` or `pip3 install -e .` for development
3. Update Flask app to use the module

## References

- pybind11 documentation: https://pybind11.readthedocs.io/
- Building with CMake: https://pybind11.readthedocs.io/en/stable/compiling.html
- setuptools integration: https://pybind11.readthedocs.io/en/stable/installing.html
