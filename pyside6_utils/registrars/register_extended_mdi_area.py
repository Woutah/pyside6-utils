"""For use by QtDesigner. If this folder is passed to Qt-Designer by using the environment variable
PYSIDE_DESIGNER_PLUGINS=<this_folder> when launching designer, the registered widget will appear and
will be usable in Qt-Designer.
"""
import os

from PySide6.QtDesigner import QPyDesignerCustomWidgetCollection
from pyside6_utils.utility.utility_functions import snakecase


from pyside6_utils.constants import Paths
from pyside6_utils.widgets.extended_mdi_area import ExtendedMdiArea

BASE_NAME = ExtendedMdiArea.__name__[0].lower() + ExtendedMdiArea.__name__[1:]

DOM_XML = f"""
	<ui language='c++'>
		<widget class='{ExtendedMdiArea.__name__}' name='{BASE_NAME}'>
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
MODULE += snakecase(ExtendedMdiArea.__name__) #Uses snakecase

QPyDesignerCustomWidgetCollection.registerCustomWidget(ExtendedMdiArea,
														module=MODULE,
													   	tool_tip=ExtendedMdiArea.DESCRIPTION,
														xml=DOM_XML,
														container=True,
														group="Containers")
