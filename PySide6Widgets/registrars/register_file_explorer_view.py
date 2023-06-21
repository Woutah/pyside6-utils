"""For use by QtDesigner. If this folder is passed to Qt-Designer by using the environment variable
PYSIDE_DESIGNER_PLUGINS=<this_folder> when launching designer, the registered widget will appear and 
will be usable in Qt-Designer.
"""
import os

from PySide6.QtDesigner import QPyDesignerCustomWidgetCollection
from PySide6Widgets.utility.utility_functions import snakecase


from PySide6Widgets.constants import Paths
from PySide6Widgets.widgets.file_explorer_view import FileExplorerView


BASE_NAME = FileExplorerView.__name__[0].lower() + FileExplorerView.__name__[1:]

DOM_XML = f"""
	<ui language='c++'>
		<widget class='{FileExplorerView.__name__}' name='{BASE_NAME}'>
			<property name='geometry'>
				<rect>
					<x>0</x>
					<y>0</y>
					<width>400</width>
					<height>200</height>
				</rect>
			</property>
		</widget>
	</ui>

"""

MODULE = ""
if len(Paths.PACKAGE_NAME) > 0:
	MODULE+= f"{Paths.PACKAGE_NAME}."
if len(Paths.WIDGETS_SUBPATH) > 0:
	MODULE+= f"{Paths.WIDGETS_SUBPATH.replace(os.sep, '.')}."
MODULE += snakecase(FileExplorerView.__name__) #Uses snakecase

QPyDesignerCustomWidgetCollection.registerCustomWidget(FileExplorerView,
														module=MODULE,#f"Widgets.{FileExplorerView.__name__}",
													   	tool_tip=FileExplorerView.DESCRIPTION,
														xml=DOM_XML,
														container=False,
														group="Item Views (Custom)")
