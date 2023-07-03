"""WSGI script."""

import os.path
import sys

sys.path.insert(0, os.path.dirname(__file__))

from hasmail import app as application  # isort:skip

__all__ = ['application']
