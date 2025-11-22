# OCCAM Installation Guide

This guide covers installation of OCCAM on Windows, macOS, and Linux systems using the modern Meson/Ninja build system.

## Quick Start

For users who just want to use PyOCCAM:

```bash
pip install pyoccam
```

For users who want to run the Flask web server:

```bash
pip install pyoccam occam-server
occam-server
```

## Building from Source

### Prerequisites

#### System Requirements

**All Platforms:**
- Python 3.9 or later (3.9, 3.10, 3.11, 3.12, 3.13 supported)
- Meson build system (≥ 1.0.0)
- Ninja build tool
- C++ compiler with C++14 support
- GMP library (GNU Multiple Precision Arithmetic Library)

**Platform-Specific:**

**Linux (Debian/Ubuntu):**
```bash
sudo apt install build-essential g++ gcc meson ninja-build \
    libgmp3-dev python3-dev python3-pip pybind11-dev
```

**Linux (Fedora/RHEL):**
```bash
sudo dnf install gcc gcc-c++ meson ninja-build gmp-devel \
    python3-devel python3-pip pybind11-devel
```

**macOS:**
```bash
# Install Homebrew if not already installed: https://brew.sh
brew install meson ninja gmp python@3.11 pybind11
```

**Windows:**
- Install [MSYS2](https://www.msys2.org/) or [MinGW-w64](https://www.mingw-w64.org/)
- Using MSYS2 terminal:
  ```bash
  pacman -S mingw-w64-x86_64-gcc mingw-w64-x86_64-meson \
      mingw-w64-x86_64-ninja mingw-w64-x86_64-gmp \
      mingw-w64-x86_64-python mingw-w64-x86_64-pybind11
  ```

#### Python Dependencies

```bash
pip install meson ninja meson-python pybind11
```

### Building Components

OCCAM consists of three components that can be built independently or together:

1. **C++ Library and CLI** - Core OCCAM engine and command-line tool
2. **PyOCCAM** - Python bindings for OCCAM
3. **OCCAM Server** - Flask-based web interface

#### Build C++ Library and CLI Only

```bash
# Configure build
meson setup build

# Compile
meson compile -C build

# Test the CLI
./build/cpp/occ

# Install system-wide (optional)
sudo meson install -C build
```

#### Build PyOCCAM (Python Extension)

```bash
cd pyoccam

# Development install (editable)
pip install -e .

# Or build wheel for distribution
pip install build
python -m build

# Install from wheel
pip install dist/pyoccam-*.whl
```

#### Build OCCAM Server (Flask Web Interface)

```bash
cd flask_app

# Install with dependencies
pip install .

# Or install with graph generation support
pip install ".[graphs]"

# Run the server
occam-server --port 8080
```

### Building for Multiple Python Versions

To build PyOCCAM wheels for multiple Python versions (useful for distribution):

```bash
# Build for all available Python versions (3.9-3.13)
python build_wheels.py

# Build for specific versions only
python build_wheels.py 3.11 3.12

# Clean build directories first
python build_wheels.py --clean

# Wheels will be in dist/ directory
ls dist/*.whl
```

### Build Options

Meson supports various build configurations via `meson.options`:

```bash
# Debug build
meson setup build --buildtype=debug

# Release build with optimizations (default)
meson setup build --buildtype=release

# Disable SSE2 optimizations
meson setup build -Dwith_sse2=false

# Don't build the CLI tool
meson setup build -Dbuild_cli=false
```

## Installation Methods

### Method 1: System-Wide Installation

```bash
# Build and install C++ components
meson setup build
meson compile -C build
sudo meson install -C build

# Install PyOCCAM
cd pyoccam
pip install .

# Install OCCAM Server
cd ../flask_app
pip install .
```

### Method 2: Virtual Environment (Recommended)

```bash
# Create virtual environment
python -m venv occam-env

# Activate it
source occam-env/bin/activate  # Linux/macOS
# or
occam-env\Scripts\activate     # Windows

# Install PyOCCAM
cd pyoccam
pip install .

# Install OCCAM Server with optional dependencies
cd ../flask_app
pip install ".[graphs]"
```

### Method 3: Development Installation

For developers who want to modify the code:

```bash
# C++ components
meson setup build
meson compile -C build

# PyOCCAM in development mode
cd pyoccam
pip install -e .

# OCCAM Server in development mode
cd ../flask_app
pip install -e ".[graphs,dev]"
```

## Verification

### Test C++ Installation

```bash
# If installed system-wide
occ --help

# If built locally
./build/cpp/occ --help
```

### Test PyOCCAM Installation

```python
python3 -c "import pyoccam; print(pyoccam.__version__)"
```

### Test OCCAM Server Installation

```bash
occam-server --help
```

## Running OCCAM

### Command-Line Interface

```bash
# Using the C++ CLI
occ input.txt

# See occ help for all options
occ --help
```

### Python Interface

```python
import pyoccam

# Your OCCAM analysis code here
# See pyoccam/pyoccam_demo.py for examples
```

### Web Interface

```bash
# Start Flask development server
occam-server

# Run on specific port
occam-server --port 8080

# Run on all network interfaces
occam-server --host 0.0.0.0 --port 8080

# Enable debug mode
occam-server --debug
```

Then open your browser to `http://localhost:5000` (or the specified port).

### Production Deployment (Web Interface)

For production use, deploy with a WSGI server:

```bash
# Install gunicorn
pip install gunicorn

# Run with gunicorn
cd flask_app
gunicorn -w 4 -b 0.0.0.0:8080 "occam_server:app"
```

Or use Apache/nginx with mod_wsgi. See `flask_app/README.md` for details.

## Troubleshooting

### Meson not found

```bash
pip install --user meson ninja
# Add ~/.local/bin to PATH if needed
export PATH="$HOME/.local/bin:$PATH"
```

### GMP library not found

**Linux:**
```bash
sudo apt install libgmp-dev  # Debian/Ubuntu
sudo dnf install gmp-devel   # Fedora/RHEL
```

**macOS:**
```bash
brew install gmp
```

**Windows:**
Use MSYS2 and install `mingw-w64-x86_64-gmp`

### pybind11 not found

```bash
pip install pybind11
```

Or install system package:
```bash
sudo apt install pybind11-dev  # Debian/Ubuntu
brew install pybind11          # macOS
```

### Python version issues

Ensure you're using Python 3.9 or later:

```bash
python --version
# Should show Python 3.9.x or later
```

If you have multiple Python versions, specify explicitly:

```bash
python3.11 -m pip install .
```

### Build failures on Windows

Make sure you're using the MSYS2 MinGW64 terminal, not the standard Windows Command Prompt. The build requires a Unix-like environment on Windows.

## Additional Resources

- **Build System Documentation**: `BUILD.md` (if present)
- **Flask App Documentation**: `flask_app/README.md`
- **PyOCCAM Examples**: `pyoccam/pyoccam_demo.py`, `pyoccam/pyoccam_demo.ipynb`
- **Contributing**: `CONTRIBUTING.md`
- **License**: `LICENSE`

## Getting Help

- **Issues**: https://github.com/occam-ra/occam/issues
- **Discussions**: https://github.com/occam-ra/occam/discussions

## Legacy Installation

For information about the old Python 2 / Make-based build system, see the git history before the Meson migration (commit XXXXX).
