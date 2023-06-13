
"""
Defines some constants used in the package.
"""

#Create paths enum:
from enum import Enum

class Paths(str, Enum):
	"""Paths to the package's subfolders."""
	PACKAGE_NAME = "PySide6Widgets"
	WIDGETS_SUBPATH = "Widgets"
	MODELS_SUBPATH = "Models"
	EXAMPLES_SUBPATH = "Examples"
