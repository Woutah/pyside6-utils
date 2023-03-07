from Widgets.FileExplorerView import FileExplorerView
from PySide6.QtDesigner import QPyDesignerCustomWidgetCollection
from constants import Paths
import os

base_name = FileExplorerView.__name__[0].lower() #lowercase first letter
base_name += FileExplorerView.__name__[1:]

DOM_XML = f"""
	<ui language='c++'>
		<widget class='{FileExplorerView.__name__}' name='{base_name}'>
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
module+= f"{FileExplorerView.__name__}"

QPyDesignerCustomWidgetCollection.registerCustomWidget(FileExplorerView, 
                                                    	module=module,#f"Widgets.{FileExplorerView.__name__}",
                                                       	tool_tip=FileExplorerView.DESCRIPTION, 
                                                        xml=DOM_XML,
                                                        container=False,
                                                        group="Item Views (Custom)")
                                                        