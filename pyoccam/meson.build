# Copyright © 1990 The Portland State University OCCAM Project Team
# [This program is licensed under the GPL version 3 or later.]
# Please see the file LICENSE in the source distribution of this software for license terms.

project('pyoccam', 'cpp',
  version: '3.0.0',
  default_options: [
    'cpp_std=c++14',
    'optimization=3',
    'warning_level=1'
  ]
)

# Python module
py = import('python').find_installation(pure: false)

# Dependencies
pybind11_dep = dependency('pybind11', required: true)
gmp_dep = dependency('gmp', required: true)
math_dep = meson.get_compiler('cpp').find_library('m', required: false)

# Compiler flags for floating-point precision
add_project_arguments([
  '-frounding-math',
  '-fsignaling-nans',
  '-fsigned-zeros',
  '-fno-finite-math-only'
], language: 'cpp')

# Platform-specific optimizations
if host_machine.cpu_family() == 'x86' or host_machine.cpu_family() == 'x86_64'
  add_project_arguments(['-msse2', '-mfpmath=sse'], language: 'cpp')
endif

# Platform-specific compile flags
if host_machine.system() == 'windows'
  add_project_arguments(['-DMS_WIN64'], language: 'cpp')
endif

# C++ source files from parent cpp/ directory
cpp_sources = files(
  '../cpp/AttributeList.cpp',
  '../cpp/Input.cpp',
  '../cpp/Key.cpp',
  '../cpp/ManagerBase.cpp',
  '../cpp/ManagerInitFromCommandLine.cpp',
  '../cpp/Model.cpp',
  '../cpp/ModelCache.cpp',
  '../cpp/OccamMath.cpp',
  '../cpp/Options.cpp',
  '../cpp/RelCache.cpp',
  '../cpp/Relation.cpp',
  '../cpp/Report.cpp',
  '../cpp/ReportCommon.cpp',
  '../cpp/ReportPrintConditionalDV.cpp',
  '../cpp/ReportPrintResiduals.cpp',
  '../cpp/ReportQsort.cpp',
  '../cpp/SBMManager.cpp',
  '../cpp/Search.cpp',
  '../cpp/SearchBase.cpp',
  '../cpp/StateConstraint.cpp',
  '../cpp/Table.cpp',
  '../cpp/VBMManager.cpp',
  '../cpp/VariableList.cpp',
  '../cpp/_Core.cpp'
)

# Pybind11 binding file
pybind_sources = files('pyoccam_pybind11.cpp')

# Python extension module (_pyoccam.so or _pyoccam.pyd)
py.extension_module('_pyoccam',
  cpp_sources + pybind_sources,
  dependencies: [pybind11_dep, gmp_dep, math_dep],
  include_directories: [
    include_directories('../include'),
    include_directories('../cpp')
  ],
  install: true,
  subdir: 'pyoccam'
)

# Install Python package files
py.install_sources(
  '__init__.py',
  subdir: 'pyoccam',
  preserve_path: false
)

# Install demo files
py.install_sources(
  'pyoccam_demo.py',
  subdir: 'pyoccam',
  preserve_path: false
)

# Install data files
py.install_sources(
  'dementia05.txt',
  'landslides.txt',
  subdir: 'pyoccam',
  preserve_path: false
)

# Install Jupyter notebook
py.install_sources(
  'pyoccam_demo.ipynb',
  subdir: 'pyoccam',
  preserve_path: false
)
