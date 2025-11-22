# Copyright © 1990 The Portland State University OCCAM Project Team
# [This program is licensed under the GPL version 3 or later.]
# Please see the file LICENSE in the source distribution of this software for license terms.

project('occam', 'cpp',
  version: '3.0.0',
  meson_version: '>=1.0.0',
  default_options: [
    'cpp_std=c++14',
    'buildtype=release',
    'warning_level=2'
  ],
  license: 'GPL-3.0-or-later'
)

# Build C++ components (library + CLI)
subdir('cpp')

# Note: Python extension (pyoccam) is built separately via pip/meson-python
# This allows proper wheel generation with metadata and multi-version support
#
# To build pyoccam:
#   cd pyoccam && pip install .
#
# To build Flask app:
#   cd flask_app && pip install .
#
# To build wheels for multiple Python versions:
#   python build_wheels.py

# Summary
summary({
  'C++ Library': 'liboccam3.a',
  'C++ CLI': 'occ',
  'Python Extension': 'Build separately in pyoccam/ directory',
  'Flask Server': 'Build separately in flask_app/ directory',
}, section: 'Components')

summary({
  'Build C++ only': 'meson compile -C build',
  'Build Python wheel': 'cd pyoccam && python -m build',
  'Build all wheels': 'python build_wheels.py',
  'Install Flask app': 'cd flask_app && pip install .',
}, section: 'Quick Start')
