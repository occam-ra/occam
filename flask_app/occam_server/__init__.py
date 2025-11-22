"""
OCCAM Flask Web Server

A web interface for OCCAM reconstructability analysis and discrete multivariate modeling.
"""

__version__ = "1.0.0"
__author__ = "Portland State University OCCAM Project Team"

from occam_server.app import app

__all__ = ['app', '__version__', '__author__']
