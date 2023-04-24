from PySide6Widgets.Widgets.RangeSelector import RangeSelector
from PySide6.QtDesigner import QPyDesignerCustomWidgetCollection
from PySide6Widgets.constants import Paths
import os

base_name = RangeSelector.__name__[0].lower() #lowercase first letter
base_name += RangeSelector.__name__[1:]

DOM_XML = f"""
	<ui language='c++'>
		<widget class='{RangeSelector.__name__}' name='{base_name}'>
		</widget>
	</ui>

"""

module = ""
if len(Paths.package_name) > 0:
      module+= f"{Paths.package_name}."
if len(Paths.widgets_subpath) > 0:
      module+= f"{Paths.widgets_subpath.replace(os.sep, '.')}."
module+= f"{RangeSelector.__name__}"

QPyDesignerCustomWidgetCollection.registerCustomWidget(RangeSelector, 
                                                    	module=f"Widgets.{RangeSelector.__name__}",
                                                       	tool_tip=RangeSelector.DESCRIPTION, 
                                                        xml=DOM_XML,
                                                        container=False,
                                                        group="Input Widgets (Custom)")
                                                        