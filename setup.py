from setuptools import setup, Extension
from setuptools.command.build_ext import build_ext as build_ext_orig
from distutils.ccompiler import new_compiler
from distutils.sysconfig import customize_compiler
import os, sys

# --- Force MinGW for all builds ---
class build_ext_mingw(build_ext_orig):
    def build_extensions(self):
        compiler = new_compiler(compiler='mingw32')
        customize_compiler(compiler)
        self.compiler = compiler
        super().build_extensions()

# --- Try to locate pybind11 ---
try:
    import pybind11
    pybind11_path = pybind11.get_include()
except ImportError:
    pybind11_path = r"C:\Users\bjpd\Anaconda3\Lib\site-packages\pybind11\include"

ext_modules = [
    Extension(
        "pyoccam.pyoccam",
        sources=[
            "cpp/AttributeList.cpp",
            "cpp/Input.cpp",
            "cpp/Key.cpp",
            "cpp/ManagerBase.cpp",
            "cpp/ManagerInitFromCommandLine.cpp",
            "cpp/Model.cpp",
            "cpp/ModelCache.cpp",
            "cpp/OccamMath.cpp",
            "cpp/Options.cpp",
            "cpp/RelCache.cpp",
            "cpp/Relation.cpp",
            "cpp/Report.cpp",
            "cpp/ReportCommon.cpp",
            "cpp/ReportPrintConditionalDV.cpp",
            "cpp/ReportPrintResiduals.cpp",
            "cpp/ReportQsort.cpp",
            "cpp/SBMManager.cpp",
            "cpp/Search.cpp",
            "cpp/SearchBase.cpp",
            "cpp/StateConstraint.cpp",
            "cpp/Table.cpp",
            "cpp/VBMManager.cpp",
            "cpp/VariableList.cpp",
            "cpp/_Core.cpp",
            "pyoccam/bindings/pyoccam_pybind11.cpp",
        ],
        include_dirs=[
            "include",
            "cpp",
            ".",
            pybind11_path,
            os.path.join(sys.prefix, "include"),
        ],
        libraries=["python39"],
        library_dirs=[r"C:\Users\bjpd\AppData\Local\anaconda3\envs\pyoccam-build"],
        extra_link_args=[],
        language="c++",
        extra_compile_args=["-std=c++14", "-O2", "-w", "-DMS_WIN64"],
    )
]

if not os.path.exists("pyoccam/__init__.py"):
    with open("pyoccam/__init__.py", "w") as f:
        f.write("# pyoccam package\nfrom .pyoccam import *\n")

setup(
    name="pyoccam",
    version="0.1.0",
    description="Python bindings for OCCAM Reconstructability Analysis",
    packages=["pyoccam"],
    package_dir={"pyoccam": "pyoccam"},
    ext_modules=ext_modules,
    zip_safe=False,
    cmdclass={'build_ext': build_ext_mingw},  # Always use MinGW
)

print("\n" + "=" * 50)
print("🚀 OCCAM Python Package - Build Complete!")
print("=" * 50)
print("Built extension: pyoccam.pyoccam")
print("Output directory:", os.path.abspath("pyoccam"))
print("=" * 50 + "\n")
