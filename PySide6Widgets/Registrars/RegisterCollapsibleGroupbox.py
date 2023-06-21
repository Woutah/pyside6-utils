from PySide6Widgets.Widgets.CollapsibleGroupBox import CollapsibleGroupBox
from PySide6.QtDesigner import QPyDesignerCustomWidgetCollection
from PySide6Widgets.constants import Paths
import os


base_name = CollapsibleGroupBox.__name__[0].lower() #lowercase first letter
base_name += CollapsibleGroupBox.__name__[1:]

DOM_XML = f"""
	<ui language='c++'>
		<widget class='{CollapsibleGroupBox.__name__}' name='{base_name}'>
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
MODULE+= f"{CollapsibleGroupBox.__name__}"

QPyDesignerCustomWidgetCollection.registerCustomWidget(CollapsibleGroupBox, 
                                                    	module=MODULE,
                                                       	tool_tip=CollapsibleGroupBox.DESCRIPTION, 
                                                        xml=DOM_XML,
                                                        container=True,
                                                        group="Containers")
                                                        