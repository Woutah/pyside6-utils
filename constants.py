


#Create paths enum:
from enum import Enum

class Paths(str, Enum):
	package_name = ""
	widgets_subpath = "Widgets"
	models_subpath = "Models"
	examples_subpath = "Examples"