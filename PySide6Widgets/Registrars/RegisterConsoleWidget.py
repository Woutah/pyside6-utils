import os

from PySide6.QtDesigner import QPyDesignerCustomWidgetCollection

from PySide6Widgets.constants import Paths
from PySide6Widgets.Widgets.ConsoleWidget import ConsoleWidget

base_name = ConsoleWidget.__name__[0].lower() #lowercase first letter
base_name += ConsoleWidget.__name__[1:]

DOM_XML = f"""
	<ui language='c++'>
		<widget class='{ConsoleWidget.__name__}' name='{base_name}'>
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

module = ""
if len(Paths.PACKAGE_NAME) > 0:
	MODULE+= f"{Paths.PACKAGE_NAME}."
if len(Paths.WIDGETS_SUBPATH) > 0:
	MODULE+= f"{Paths.WIDGETS_SUBPATH.replace(os.sep, '.')}." #NOTE: assumes the file-name is the same as the class-name
module+= f"{ConsoleWidget.__name__}"

QPyDesignerCustomWidgetCollection.registerCustomWidget(ConsoleWidget, 
                                                    	module=module,
                                                       	tool_tip=ConsoleWidget.DESCRIPTION, 
                                                        xml=DOM_XML,
														container=False,
                                                        group="Item Views (Custom)")
                                                        