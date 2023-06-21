
"""
Defines some constants used in the package.
"""
from enum import Enum

class Paths(str, Enum):
	"""Paths to the package's subfolders. Used for the registrars"""
	PACKAGE_NAME = "PySide6Widgets"
	WIDGETS_SUBPATH = "widgets"
	MODELS_SUBPATH = "models"
	EXAMPLES_SUBPATH = "examples"
