"""An example dataclass to show functionality of automatic GUI generation."""

import typing
from dataclasses import dataclass, field
from datetime import datetime

from pyside6_utils.utility.constraints import (Interval,
                                                             StrOptions)

LITERAL_EXAMPLE = typing.Literal["testliteral1", "testliteral2", "testliteral3"] #pylint: disable=invalid-name

@dataclass
class ExampleDataClass:
	"""
	This is an example dataclass to test automatic GUI generation - shows the functionality of all types.
	"""

	test_parent_with_property: str = field(
		default="testparentwithpropertystr",
		metadata=dict(
			display_name="Test parent with property (uneditable)",
			help= "This is a test property",
			display_path="test_parent", #Always from base
			editable=False
		)
	)

	test_str_property: str = field(
		default="teststr",
		metadata=dict(
			display_name="Test str property",
			help= "This is a test property",
			display_path="test_parent/test_parent_with_property", #Always from base
			changed=True
		)
	)

	test_int_property: int | None = field(
		default=None,
		metadata=dict(
			display_name="Test int/none property",
			help= "This is a test property that can also be none",
			changed=True
		)
	)

	test_literal_property: typing.Literal["testliteral1", "testliteral2", "testliteral3"] = field(
		default="testliteral1",
		metadata=dict(
			display_name="Test literal property",
			help= "This is a test property",
			changed=True
		)
	)

	test_required_int_property: int | None = field(
		default=None,
		metadata=dict(
			display_name="Test required int property",
			help= "This is a test property that is required",
			changed=True,
			required=True
		)
	)

	test_int_literal_property : typing.Literal[1, 2, 3] = field(
		default=1,
		metadata=dict(
			display_name="Test int literal property",
			help= "This is a test property",
			changed=True
		)
	)

	test_int_options_property : int = field(
		default=1,
		metadata=dict(
			display_name="Test int options property",
			help= "This is a test property",
			changed=True,
			constraints = [Interval(int, 0,10, closed='both'), None]
		)
	)

	test_stroptions_property : typing.Literal["Option1/10", "Option2/10"] = field(
		default="Option1/10",
		metadata=dict(
			display_name="Test stroptions property",
			help= "This is a test property (stroptions)",
			changed=True,
			constraints = [StrOptions({f"Option{i}/10" for i in range(10)}), None], #Similar to literal, but we can
				#create additional options dynamically using constraints
			constraints_help= { f"Option{i}/10" : f"This is help for option{i}/10" for i in range(10) } #This option
				#allows us to add a "help" popup when hovering over individual options in a combobox
		)
	)


	test_float_range_0_1_property: float = field(
		default=0.001,
		metadata=dict(
			display_name="Test float range 0-1 property",
			help= "This is a test property (float)",
			changed=True,
			constraints = [Interval(float, 0,1, closed='both'), None]
		)
	)

	test_bool_property: bool = field(
		default=False,
		metadata=dict(
			display_name="Test bool property",
			help= "This is a test property (bool)",
			changed=True
		)
	)

	test_datetime_property: datetime = field(
		default=datetime(2050,1,1),
		metadata=dict(
			display_name="Test datetime property",
			help= "This is a test property (datetime)",
			changed=True
		)
	)
