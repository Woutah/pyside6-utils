from Widgets.CollapsibleGroupBox import CollapsibleGroupBox
from PySide6.QtDesigner import QPyDesignerCustomWidgetCollection
from constants import Paths
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
module = ""
if len(Paths.package_name) > 0:
      module+= f"{Paths.package_name}."
if len(Paths.widgets_subpath) > 0:
      module+= f"{Paths.widgets_subpath.replace(os.sep, '.')}."
module+= f"{CollapsibleGroupBox.__name__}"

QPyDesignerCustomWidgetCollection.registerCustomWidget(CollapsibleGroupBox, 
                                                    	module=module,
                                                       	tool_tip=CollapsibleGroupBox.DESCRIPTION, 
                                                        xml=DOM_XML,
                                                        container=True,
                                                        group="Containers")
                                                        