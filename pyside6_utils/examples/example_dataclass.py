"""An example dataclass to show functionality of automatic GUI generation."""

import typing
from dataclasses import dataclass, field
from datetime import datetime

from pyside6_utils.utility.constraints import (Interval, ConstrainedList,
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
			display_name="Test Parent With Value",
			help= "This is a parent with an unsettable property",
			# display_path="Test Parent With Value", #Always from base
			editable=False
		)
	)

	test_str: str = field(
		default="teststr",
		metadata=dict(
			display_name="Test str property",
			help= "This is a test property",
			display_path="test_parent_with_property/Dummy Parent", #Always from base
		)
	)

	test_int: int | None = field(
		default=None,
		metadata=dict(
			display_name="Test int/none property",
			help= "This is a test property that can also be none",
			changed=True
		)
	)

	test_literal: typing.Literal["testliteral1", "testliteral2", "testliteral3"] = field(
		default="testliteral1",
		metadata=dict(
			display_name="Test literal property",
			help= "This is a test property",
			changed=True
		)
	)

	test_required_int: int | None = field(
		default=None,
		metadata=dict(
			display_name="Test required int property",
			help= "This is a test property that is required",
			changed=True,
			required=True
		)
	)

	test_int_literal : typing.Literal[1, 2, 3] = field(
		default=1,
		metadata=dict(
			display_name="Test int literal property",
			help= "This is a test property",
			changed=True
		)
	)

	test_int_options : int = field(
		default=1,
		metadata=dict(
			display_name="Test int options property",
			help= "This is a test property that stays within 0-10 interval",
			changed=True,
			constraints = [Interval(int, 0,10, closed='both')]
		)
	)

	test_intlist : typing.List[int] = field(
		default_factory=list,
		metadata=dict(
			display_name="Test intlist property",
			help= "This is a test property",
			changed=True,
			constraints = [ConstrainedList([Interval(int, 0,10, closed='both')]), None]
		)
	)

	test_int_or_none_list : typing.List[int | None] = field(
		default_factory=list,
		metadata=dict(
			display_name="Test int or none list property",
			help= "This is a test property",
			changed=True,
			constraints = [
				ConstrainedList([Interval(int, 0,10, closed='both'), None])
			]
		)
	)

	test_stroptions_property : typing.Literal["Option 1/10", "Option 2/10"] = field(
		default="Option 1/10",
		metadata=dict(
			display_name="Test stroptions property",
			help= "This is a test property (stroptions)",
			changed=True,
			constraints = [StrOptions({f"Option {i}/10" for i in range(10)}), None], #Similar to literal, but we can
				#create additional options dynamically using constraints
			constraints_help= { f"Option {i}/10" : f"This is help for option{i}/10" for i in range(10) } #This option
				#allows us to add a "help" popup when hovering over individual options in a combobox
		)
	)


	test_float_range_0_1_property: float = field(
		default=0.001,
		metadata=dict(
			display_name="Test float range 0-1 property",
			help= "This is a test float property",
			changed=True,
			constraints = [Interval(float, 0,1, closed='both'), None]
		)
	)

	test_bool_property: bool = field(
		default=False,
		metadata=dict(
			display_name="Test bool property",
			help= "This is a test bool property ",
			changed=True
		)
	)

	test_datetime_property: datetime = field(
		default=datetime(2050,1,1),
		metadata=dict(
			display_name="Test datetime property",
			help= "This is a test datetime property",
			changed=True
		)
	)
