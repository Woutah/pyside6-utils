"""For use by QtDesigner. If this folder is passed to Qt-Designer by using the environment variable
PYSIDE_DESIGNER_PLUGINS=<this_folder> when launching designer, the registered widget will appear and
will be usable in Qt-Designer.
"""
import os

from PySide6.QtDesigner import QPyDesignerCustomWidgetCollection

from PySide6Widgets.constants import Paths
from PySide6Widgets.Widgets.SquareFrame import SquareFrame

BASE_NAME = SquareFrame.__name__[0].lower() #lowercase first letter
BASE_NAME += SquareFrame.__name__[1:]

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
MODULE+= f"{SquareFrame.__name__}"

QPyDesignerCustomWidgetCollection.registerCustomWidget(SquareFrame,
														module=MODULE,
													   	tool_tip=SquareFrame.DESCRIPTION,
														xml=DOM_XML,
														container=True,
														group="Containers")
