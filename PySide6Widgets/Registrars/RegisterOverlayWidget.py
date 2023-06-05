from PySide6Widgets.Widgets.OverlayWidget import OverlayWidget
from PySide6.QtDesigner import QPyDesignerCustomWidgetCollection
from PySide6Widgets.constants import Paths
import os

base_name = OverlayWidget.__name__[0].lower() #lowercase first letter
base_name += OverlayWidget.__name__[1:]

DOM_XML = f"""
	<ui language='c++'>
		<widget class='{OverlayWidget.__name__}' name='{base_name}'>
			<property name='geometry'>
				<rect>
					<x>0</x>
					<y>0</y>
					<width>400</width>
					<height>200</height>
				</rect>
			</property>
            <property name='overlayHidden'>
				<bool>True</bool>
			</property>
		</widget>
	</ui>

"""

module = ""
if len(Paths.package_name) > 0:
      module+= f"{Paths.package_name}."
if len(Paths.widgets_subpath) > 0:
      module+= f"{Paths.widgets_subpath.replace(os.sep, '.')}."
module+= f"{OverlayWidget.__name__}"

QPyDesignerCustomWidgetCollection.registerCustomWidget(OverlayWidget, 
                                                    	module=module,#f"Widgets.{OverlayWidget.__name__}",
                                                       	tool_tip=OverlayWidget.DESCRIPTION, 
                                                        xml=DOM_XML,
                                                        container=True,
                                                        group="Containers")
                                                        