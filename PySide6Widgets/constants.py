


#Create paths enum:
from enum import Enum

class Paths(str, Enum):
	package_name = "PySide6Widgets"
	widgets_subpath = "Widgets"
	models_subpath = "Models"
	examples_subpath = "Examples"