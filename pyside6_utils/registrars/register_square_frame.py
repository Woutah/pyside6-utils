"""For use by QtDesigner. If this folder is passed to Qt-Designer by using the environment variable
PYSIDE_DESIGNER_PLUGINS=<this_folder> when launching designer, the registered widget will appear and
will be usable in Qt-Designer.
"""
import os

from PySide6.QtDesigner import QPyDesignerCustomWidgetCollection
from pyside6_utils.utility.utility_functions import snakecase


from pyside6_utils.constants import Paths
from pyside6_utils.widgets.square_frame import SquareFrame


BASE_NAME = SquareFrame.__name__[0].lower() + SquareFrame.__name__[1:]

DOM_XML = f"""
	<ui language='c++'>
		<widget class='{SquareFrame.__name__}' name='{BASE_NAME}'>
		</widget>
	</ui>
"""

MODULE = ""
if len(Paths.PACKAGE_NAME) > 0:
	MODULE+= f"{Paths.PACKAGE_NAME}."
if len(Paths.WIDGETS_SUBPATH) > 0:
	MODULE+= f"{Paths.WIDGETS_SUBPATH.replace(os.sep, '.')}."
MODULE += snakecase(SquareFrame.__name__) #Uses snakecase

QPyDesignerCustomWidgetCollection.registerCustomWidget(SquareFrame,
														module=MODULE,
													   	tool_tip=SquareFrame.DESCRIPTION,
														xml=DOM_XML,
														container=True,
														group="Containers")
