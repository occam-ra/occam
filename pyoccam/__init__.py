"""
PyOCCAM: Python bindings for OCCAM (Organizational Complexity Computation And Modeling)

OCCAM is a tool for reconstructability analysis and discrete multivariate modeling.
"""

__version__ = "3.0.0"
__author__ = "David Percy and the Portland State University OCCAM Project Team"

# Import the C++ extension module
from pyoccam._pyoccam import *

# Expose version at package level
__all__ = ['__version__', '__author__']
