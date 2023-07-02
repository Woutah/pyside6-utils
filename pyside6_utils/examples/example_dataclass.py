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
			display_name="Test str",
			help= "This is a test",
			display_path="test_parent_with_property/Dummy Parent", #Always from base
		)
	)

	test_int: int | None = field(
		default=None,
		metadata=dict(
			display_name="Test int/none",
			help= "This is a test that can also be none",
			changed=True
		)
	)

	test_literal: typing.Literal["testliteral1", "testliteral2", "testliteral3"] = field(
		default="testliteral1",
		metadata=dict(
			display_name="Test literal",
			help= "This is a test",
			changed=True
		)
	)

	test_required_int: int | None = field(
		default=None,
		metadata=dict(
			display_name="Test required int",
			help= "This is a test int that is required",
			changed=True,
			required=True
		)
	)

	test_int_literal : typing.Literal[1, 2, 3] = field(
		default=1,
		metadata=dict(
			display_name="Test int literal",
			help= "This is a test",
			changed=True
		)
	)

	test_int_options : int = field(
		default=1,
		metadata=dict(
			display_name="Test int options",
			help= "This is a test that stays within 0-10 interval",
			changed=True,
			constraints = [Interval(int, 0,10, closed='both')]
		)
	)

	test_intlist : typing.List[int] = field(
		default_factory=list,
		metadata=dict(
			display_name="Test intlist",
			help= "This is a test",
			changed=True,
			constraints = [ConstrainedList([Interval(int, 0,10, closed='both')]), None]
		)
	)

	test_int_or_none_list : typing.List[int | None] = field(
		default_factory=list,
		metadata=dict(
			display_name="Test int 0<->10 or None list",
			help= "This is a test",
			changed=True,
			constraints = [
				ConstrainedList([Interval(int, 0,10, closed='both'), None])
			]
		)
	)


	test_float_or_option : typing.List[float | str] = field(
		default_factory=list,
		metadata=dict(
			display_name="Either 0-1 float or 'string1' or 'string2'",
			help= "This is a test",
			changed=True,
			constraints = [
				ConstrainedList([Interval(float, 0,1, closed='both'), StrOptions({"string1", "string2"})])
			]
		)
	)

	test_float_or_int_list : typing.List[float | int] = field(
		default_factory=list,
		metadata=dict(
			display_name="Test List[float|int]",
			help= "This is a test using only typing.List[float|int], no constraints",
			changed=True,
		)
	)

	test_stroptions_property : typing.Literal["Option 1/10", "Option 2/10"] = field(
		default="Option 1/10",
		metadata=dict(
			display_name="Test stroptions",
			help= "This is a test (stroptions)",
			changed=True,
			constraints = [StrOptions({f"Option {i}/10" for i in range(10)}), None], #Similar to literal, but we can
				#create additional options dynamically using constraints
			constraints_help= { f"Option {i}/10" : f"This is help for option {i}/10" for i in range(10) } #This option
				#allows us to add a "help" popup when hovering over individual options in a combobox
		)
	)


	test_float_range_0_1_property: float = field(
		default=0.001,
		metadata=dict(
			display_name="Test float range 0-1",
			help= "This is a test float",
			changed=True,
			constraints = [Interval(float, 0,1, closed='both'), None]
		)
	)

	test_bool_property: bool = field(
		default=False,
		metadata=dict(
			display_name="Test bool",
			help= "This is a test bool",
			changed=True
		)
	)

	test_datetime_property: datetime = field(
		default=datetime(2050,1,1),
		metadata=dict(
			display_name="Test datetime",
			help= "This is a test datetime",
			changed=True
		)
	)
