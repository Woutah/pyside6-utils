from PySide6Widgets.Widgets.SquareFrame import SquareFrame
from PySide6.QtDesigner import QPyDesignerCustomWidgetCollection
from PySide6Widgets.constants import Paths
import os

base_name = SquareFrame.__name__[0].lower() #lowercase first letter
base_name += SquareFrame.__name__[1:]

DOM_XML = f"""
	<ui language='c++'>
		<widget class='{SquareFrame.__name__}' name='{base_name}'>
		</widget>
	</ui>
"""

module = ""
if len(Paths.package_name) > 0:
      module+= f"{Paths.package_name}."
if len(Paths.widgets_subpath) > 0:
      module+= f"{Paths.widgets_subpath.replace(os.sep, '.')}."
module+= f"{SquareFrame.__name__}"

QPyDesignerCustomWidgetCollection.registerCustomWidget(SquareFrame, 
                                                    	module=module,
                                                       	tool_tip=SquareFrame.DESCRIPTION, 
                                                        xml=DOM_XML,
														container=True,
                                                        group="Containers")
                                                        