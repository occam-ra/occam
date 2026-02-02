"""
OCCAM Exception Classes
"""

class OCCAMError(Exception):
    """Base exception for OCCAM operations"""
    pass

class OCCAMExecutableNotFoundError(OCCAMError):
    """Raised when occ.cpp executable cannot be found"""
    pass

class OCCAMDataFileError(OCCAMError):
    """Raised when there's an issue with the data file"""
    pass

class OCCAMSearchError(OCCAMError):
    """Raised when search operation fails"""
    pass

class OCCAMFitError(OCCAMError):
    """Raised when fit operation fails"""
    pass