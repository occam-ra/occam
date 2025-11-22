# Copyright © 1990 The Portland State University OCCAM Project Team
# [This program is licensed under the GPL version 3 or later.]
# Please see the file LICENSE in the source distribution of this software for license terms.

project('occam-cpp', 'cpp',
  version: '3.0.0',
  default_options: [
    'cpp_std=c++14',
    'warning_level=2',
    'optimization=3',
    'b_ndebug=if-release'
  ]
)

# Dependencies
gmp_dep = dependency('gmp', required: true)
thread_dep = dependency('threads', required: false)
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

# Library source files (excluding occ.cpp and pyoccam.cpp)
lib_sources = files(
  'AttributeList.cpp',
  'Input.cpp',
  'Key.cpp',
  'ManagerBase.cpp',
  'ManagerInitFromCommandLine.cpp',
  'OccamMath.cpp',
  'Model.cpp',
  'ModelCache.cpp',
  'Options.cpp',
  'RelCache.cpp',
  'Relation.cpp',
  'Report.cpp',
  'ReportCommon.cpp',
  'ReportPrintConditionalDV.cpp',
  'ReportPrintResiduals.cpp',
  'ReportQsort.cpp',
  'SBMManager.cpp',
  'SearchBase.cpp',
  'Search.cpp',
  'StateConstraint.cpp',
  'Table.cpp',
  'VBMManager.cpp',
  'VariableList.cpp',
  '_Core.cpp'
)

# Include directories
inc = include_directories('../include')

# Static library
liboccam = static_library('occam3',
  lib_sources,
  include_directories: inc,
  dependencies: [gmp_dep, math_dep],
  install: true,
  pic: true
)

# Command-line executable
occ_exe = executable('occ',
  'occ.cpp',
  include_directories: inc,
  link_with: liboccam,
  dependencies: [gmp_dep, math_dep],
  install: true
)

# Make library available to parent project and other subprojects
liboccam_dep = declare_dependency(
  link_with: liboccam,
  include_directories: inc,
  dependencies: [gmp_dep, math_dep]
)

# Install headers
install_headers(
  '../include/AttributeList.h',
  '../include/Constants.h',
  '../include/Globals.h',
  '../include/Input.h',
  '../include/Key.h',
  '../include/ManagerBase.h',
  '../include/Model.h',
  '../include/ModelCache.h',
  '../include/OccamMath.h',
  '../include/Options.h',
  '../include/RelCache.h',
  '../include/Relation.h',
  '../include/Report.h',
  '../include/SBMManager.h',
  '../include/Search.h',
  '../include/SearchBase.h',
  '../include/StateConstraint.h',
  '../include/Table.h',
  '../include/Types.h',
  '../include/VBMManager.h',
  '../include/VarIntersect.h',
  '../include/Variable.h',
  '../include/VariableList.h',
  '../include/_Core.h',
  '../include/attrDescs.h',
  subdir: 'occam'
)
