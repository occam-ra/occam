"""
OCCAM Python Package - Python Orchestration of occ.cpp
"""

from .manager import VBMManager
from .utils import search, fit, call_occ, find_occ_executable
from .exceptions import OCCAMError

__version__ = "3.4.0"

# Constants
TABSEP = 1
COMMASEP = 2
SPACESEP = 3
HTMLFORMAT = 4

__all__ = [
    'VBMManager',
    'search', 
    'fit',
    'call_occ',
    'find_occ_executable',
    'TABSEP', 'COMMASEP', 'SPACESEP', 'HTMLFORMAT',
    'OCCAMError'
]