"""For use by QtDesigner. If this folder is passed to Qt-Designer by using the environment variable
PYSIDE_DESIGNER_PLUGINS=<this_folder> when launching designer, the registered widget will appear and
will be usable in Qt-Designer.
"""
import os

from PySide6.QtDesigner import QPyDesignerCustomWidgetCollection
from pyside6_utils.utility.utility_functions import snakecase


from pyside6_utils.constants import Paths
from pyside6_utils.widgets.widget_switcher import WidgetSwitcher


BASE_NAME = WidgetSwitcher.__name__[0].lower() + WidgetSwitcher.__name__[1:]

DOM_XML = f"""
	<ui language='c++'>
		<widget class='{WidgetSwitcher.__name__}' name='{BASE_NAME}'>
			<property name='geometry'>
				<rect>
					<x>0</x>
					<y>0</y>
					<width>100</width>
					<height>24</height>
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
MODULE += snakecase(WidgetSwitcher.__name__) #Uses snakecase

QPyDesignerCustomWidgetCollection.registerCustomWidget(WidgetSwitcher,
														module=MODULE,
													   	tool_tip=WidgetSwitcher.DESCRIPTION,
														xml=DOM_XML,
														container=True,
														group="Containers")
