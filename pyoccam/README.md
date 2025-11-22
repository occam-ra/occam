# pyoccam

**Python bindings for OCCAM Reconstructability Analysis Tools**

[![Build Wheels](https://github.com/occam-ra/occam/actions/workflows/build-wheels.yml/badge.svg)](https://github.com/occam-ra/occam/actions/workflows/build-wheels.yml)

---

## What is pyoccam?

`pyoccam` is a standalone, cross-platform Python package that wraps the core OCCAM Reconstructability Analysis tools using modern C++ and `pybind11`. It provides powerful information-theoretic modeling capabilities for categorical data, especially useful for:

- Environmental modeling (e.g., landslides, wildfires)
- System science
- Social and ecological systems
- Complex multivariate interactions

OCCAM uses variable-based and state-based search to discover significant structures in complex systems, emphasizing **interpretability** and **information preservation** over black-box prediction.

---

## Installation

### Quick Install (Prebuilt Wheels)

Once published to PyPI:
```bash
pip install pyoccam
```

For now, install from a local wheel:
```bash
pip install dist/pyoccam-3.0.0-*.whl
```

### Building from Source

#### System Requirements

**Linux (Ubuntu/Debian):**
```bash
sudo apt install build-essential libgmp-dev python3-dev meson ninja-build
```

**macOS:**
```bash
brew install gmp meson ninja
```

**Windows:**
- Install Visual Studio 2019 or later with C++ support
- Install GMP (e.g., via vcpkg: `vcpkg install gmp:x64-windows`)
- Install Meson and Ninja: `pip install meson ninja`

#### Build Steps

**Option 1: Using pip (Recommended)**
```bash
# Install build dependencies
pip install -r requirements-build.txt

# Build and install in development mode
pip install -e .

# Or build a wheel
pip install build
python -m build
pip install dist/pyoccam-*.whl
```

**Option 2: Using Meson directly**
```bash
# From project root
meson setup builddir
ninja -C builddir

# Python extension will be in builddir/pyoccam/
# To use it, add to PYTHONPATH or install with pip
```

#### Development Installation

For development with testing and documentation tools:
```bash
pip install -r requirements-dev.txt
pip install -e .
```

---

## Usage

### Basic Example

```python
import _pyoccam as occam

# Create a manager for variable-based modeling
manager = occam.Manager()

# Load data
manager.initFromCommandLine([
    "action:fit",
    "data:mydata.txt",
    "model:IV:DV"
])

# Perform analysis
manager.doAction("fit")

# Get results
print(manager.getReport())
```

### Working with Data

```python
# Example data format (tab-separated):
# Variable1	Variable2	DV	:Count
# 0	0	0	5
# 0	1	1	3
# 1	0	1	2
# 1	1	0	1
```

---

## API Reference

### Manager Class

Main interface to OCCAM functionality:

- `Manager(mode)` - Create manager ("VB" for variable-based, "SB" for state-based)
- `initFromCommandLine(args)` - Initialize from command arguments
- `doAction(action)` - Perform action: "fit", "search", "test"
- `getReport()` - Get results as string

For detailed documentation, see the main [OCCAM documentation](../README.md).

---

## Building Wheels for Distribution

Build wheels for Python 3.9-3.13:

```bash
# Install build tools
pip install build

# Build wheel
python -m build

# Wheels will be in dist/
ls dist/pyoccam-3.0.0-*.whl
```

For multi-platform wheel building, see the GitHub Actions workflow at `.github/workflows/build-wheels.yml`.

---

## Requirements Files

This package includes several requirements files for different purposes:

- `requirements.txt` - Empty (no runtime dependencies)
- `requirements-build.txt` - Dependencies for building from source
- `requirements-dev.txt` - Development dependencies (includes build + testing)

---

## Development

### Running Tests

```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Run tests (when implemented)
pytest tests/
```

### Code Style

The C++ code follows the existing OCCAM style. Python bindings use `pybind11` conventions.

---

## Technical Details

- **Language**: C++14 with Python 3.9+ bindings
- **Build System**: Meson + meson-python
- **Bindings**: pybind11
- **Dependencies**: GMP (GNU Multiple Precision Arithmetic Library)
- **Platform Support**: Linux, macOS, Windows

---

## License

GPL-3.0-or-later

Copyright © 1990 The Portland State University OCCAM Project Team

---

## Links

- [Project Homepage](https://github.com/occam-ra/occam)
- [Issues](https://github.com/occam-ra/occam/issues)
- [Main Documentation](../README.md)
