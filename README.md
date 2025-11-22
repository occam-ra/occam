# OCCAM: Reconstructability Analysis Tools

Copyright (c) 1990 The Portland State University OCCAM Project Team

OCCAM is a collection of software tools comprising a library with both command-line and web interfaces for *Reconstructability Analysis* (RA), a kind of statistical analysis closely related to Factor Analysis and Bayesian Belief Networks.

The OCCAM project has been developed over several decades at Portland State University under the auspices of its creator Prof. Martin Zwick. Programmers contributing to the work have included Ken Willett, Joe Fusion and H. Forrest Alexander.

This software is currently being released for the first time as Free Software under the GPL v3 or later. Please see the file `LICENSE` in this distribution for license terms.

## Quick Start

### Installation

```bash
# Install PyOCCAM from PyPI (when published)
pip install pyoccam

# Or install from source
cd pyoccam
pip install .

# Install Flask web server
pip install occam-server
occam-server
```

### Building from Source

OCCAM uses the Meson build system for cross-platform compilation:

```bash
# Install build dependencies
pip install meson ninja meson-python pybind11

# Build C++ library and CLI
meson setup build
meson compile -C build

# Build Python extension
cd pyoccam
pip install .

# Build wheels for multiple Python versions (3.9-3.13)
python build_wheels.py
```

For detailed build instructions, see **[docs/INSTALL.md](docs/INSTALL.md)**.

## Components

- **liboccam3.a** - Core C++ library for reconstructability analysis
- **occ** - Command-line interface
- **pyoccam** - Python 3 bindings (supports Python 3.9-3.13)
- **occam-server** - Modern Flask-based web interface

## Documentation

- **Installation**: See [docs/INSTALL.md](docs/INSTALL.md) for detailed build and installation instructions
- **Examples**: See `pyoccam/pyoccam_demo.py` and `pyoccam/pyoccam_demo.ipynb`
- **Contributing**: See [CONTRIBUTING.md](CONTRIBUTING.md)
- **Web Server**: See [docs/FLASK_README.md](docs/FLASK_README.md)
- **Container Deployment**: See [docs/CONTAINER_README.md](docs/CONTAINER_README.md)

## Requirements

- **Python**: 3.9 or later
- **C++ Compiler**: GCC, Clang, or MSVC with C++14 support
- **Build Tools**: Meson (≥ 1.0.0), Ninja
- **Libraries**: GMP (GNU Multiple Precision), pybind11

## License

GPL v3 or later. See [LICENSE](LICENSE) for details.
