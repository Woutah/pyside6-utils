
from dataclasses import dataclass, field
import typing
from datetime import datetime
LITERAL_EXAMPLE = typing.Literal["testliteral1", "testliteral2", "testliteral3"]
from PySide6Widgets.Utility.sklearn_param_validation import Interval, StrOptions

@dataclass
class ExampleDataClass:
	"""
	This is an example dataclass to test automatic GUI generation.
	"""

	test_parent_with_property: str = field(default="testparentwithpropertystr", metadata=dict(
												display_name="Test parent with property (uneditable)",
												help= "This is a test property (str)",
												display_path="test_parent", #Always from base
												editable=False)) #TODO: changed? 

	test_str_property: str = field(default="teststr", metadata=dict(
												display_name="Test str property",
												help= "This is a test property (str)",
												display_path="test_parent/test_parent_with_property", #Always from base
												changed=True))

	test_int_property: int = field(default=None, metadata=dict(
												display_name="Test int/none property",
												help= "This is a test property (int) that can also be none",
												changed=True,
												constraints = [int, None]

												))

	test_literal_property: LITERAL_EXAMPLE = field(default="testliteral", metadata=dict(
												display_name="Test literal property",
												help= "This is a test property (literal)",
												changed=True))
	
	test_stroptions_property : typing.Literal["Option1/10", "Option2/10"] = field(default="None", metadata=dict( 
												display_name="Test stroptions property",
												help= "This is a test property (stroptions)",
												changed=True,					
												constraints = [StrOptions({f"Option{i}/10" for i in range(10)}), None], #Similar to literal, but we can create additional options dynamically using constraints
												constraints_help= { f"Option{i}/10" : f"This is help for option{i}/10" for i in range(10) } #This option allows us to add a "help" popup when hovering over individual options in a combobox
												))
	

	test_float_property: float = field(default=0.001, metadata=dict(
												display_name="Test float property",
												help= "This is a test property (float)",
												changed=True,		
												constraints = [Interval(float, 0,1, closed='both'), None]
												
												))
	
	test_bool_property: bool = field(default=False, metadata=dict(
												display_name="Test bool property",
												help= "This is a test property (bool)",
												changed=True))

	test_datetime_property: datetime = field(default=datetime(2050,1,1), metadata=dict(
												display_name="Test datetime property",
												help= "This is a test property (datetime)",
												changed=True))
