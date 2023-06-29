"""For use by QtDesigner. If this folder is passed to Qt-Designer by using the environment variable
PYSIDE_DESIGNER_PLUGINS=<this_folder> when launching designer, the registered widget will appear and
will be usable in Qt-Designer.
"""
import os

from PySide6.QtDesigner import QPyDesignerCustomWidgetCollection
from pyside6_utils.utility.utility_functions import snakecase


from pyside6_utils.constants import Paths
from pyside6_utils.widgets.widget_list import WidgetList


BASE_NAME = WidgetList.__name__[0].lower() + WidgetList.__name__[1:]

DOM_XML = f"""
	<ui language='c++'>
		<widget class='{WidgetList.__name__}' name='{BASE_NAME}'>
			<property name='geometry'>
				<rect>
					<x>0</x>
					<y>0</y>
					<width>200</width>
					<height>400</height>
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
MODULE += snakecase(WidgetList.__name__) #Uses snakecase

QPyDesignerCustomWidgetCollection.registerCustomWidget(WidgetList,
														module=MODULE,
													   	tool_tip=WidgetList.DESCRIPTION,
														xml=DOM_XML,
														container=False,
														group="Item Widgets (Item-Based)")
