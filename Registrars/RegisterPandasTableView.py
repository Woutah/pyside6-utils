from Widgets.PandasTableView import PandasTableView
from PySide6.QtDesigner import QPyDesignerCustomWidgetCollection
from constants import Paths
import os

base_name = PandasTableView.__name__[0].lower() #lowercase first letter
base_name += PandasTableView.__name__[1:]

DOM_XML = f"""
	<ui language='c++'>
		<widget class='{PandasTableView.__name__}' name='{base_name}'>
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
module+= f"{PandasTableView.__name__}"

QPyDesignerCustomWidgetCollection.registerCustomWidget(PandasTableView, 
                                                    	module=f"Widgets.{PandasTableView.__name__}",
                                                       	tool_tip=PandasTableView.DESCRIPTION, 
                                                        xml=DOM_XML,
                                                        container=True,
                                                        group="AAA")
                                                        