
from dataclasses import dataclass, field
import typing
from datetime import datetime
LITERAL_EXAMPLE = typing.Literal["testliteral1", "testliteral2", "testliteral3"]

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

	test_int_property: int = field(default=0, metadata=dict(
												display_name="Test int property",
												help= "This is a test property (int)",
												changed=True))

	test_literal_property: LITERAL_EXAMPLE = field(default="testliteral", metadata=dict(
												display_name="Test literal property",
												help= "This is a test property (literal)",
												changed=True))

	test_float_property: float = field(default=0.001, metadata=dict(
												display_name="Test float property",
												help= "This is a test property (float)",
												changed=True))
	
	test_bool_property: bool = field(default=False, metadata=dict(
												display_name="Test bool property",
												help= "This is a test property (bool)",
												changed=True))

	test_datetime_property: datetime = field(default=datetime(2050,1,1), metadata=dict(
												display_name="Test datetime property",
												help= "This is a test property (datetime)",
												changed=True))
