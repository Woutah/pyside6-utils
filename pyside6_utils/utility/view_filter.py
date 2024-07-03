from enum import Enum
from numbers import Number
import datetime
from dateutil import parser
import re
import typing
import logging
log = logging.getLogger(__name__)

#Enum with the different types of number comparitors
class FilterComparitors(Enum):
	"""Enum with the different types of comparators implemented in the filter dialog 
	"""
	EQUAL = "=="
	NOT_EQUAL = "!="
	GREATER = ">"
	GREATER_EQUAL = ">="
	LESS = "<"
	LESS_EQUAL = "<="

class FilterFunctions(Enum):
	"""
	Enum with the different types of functions implemented in the filter dialog 
	"""
	ENDSWITH = "ends_with"
	STARTSWITH = "starts_with"


class FilterMethods(Enum):
	"""
	Enum with the different types of filters which can be used to filter table views using
	a QSortFilterProxyModel
	"""
	REGEX = "Regex" #The default implementation of the Pyside6 QSortFilterProxyModel - adapted to work with the TableFilterDialog
	EXPRESSION = "Expression"
	SELECTION = "Selection"


class Filter:
	"""
	A base class for all filters
	"""
	def __init__(self):
		pass

	def __call__(self, value) -> bool:
		raise NotImplementedError
	

class CombinationFilter(Filter):
	"""
	A filter that or-combines multiple filters into one. 
	"""

	def __init__(self, filters : list[Filter | None]):
		super().__init__()
		self._filters : list[Filter] = []
		self.or_combine_filters(filters)

	def or_combine_filters(self, filters : list[Filter | None]):
		"""
		Or-combine multiple filters into one filter. None values are ignored.
		"""
		for cur_filter in filters:
			if cur_filter is None: #Skip None values
				continue
			if not isinstance(cur_filter, Filter):
				raise TypeError(f"Expected a Filter, got {type(cur_filter)}")

			if isinstance(cur_filter, CombinationFilter): #If the filter is a combination filter, add all filters in the combination filter
				self._filters.extend(cur_filter._filters)
			else:
				self._filters.append(cur_filter)
			#TODO: also merge individual filters? 


	def __call__(self, value) -> bool:
		for filter in self._filters:
			if filter(value):
				return True
		return False


class RegexFilter(Filter):
	"""
	A filter based on a regex pattern that can be used to filter a list of values.
	"""
	def __init__(self, pattern : str, case_sensitive : bool = False):
		self._pattern = pattern
		if case_sensitive:
			self._regex = re.compile(pattern)
		else:
			self._regex = re.compile(pattern, re.IGNORECASE)

	def set_pattern(self, pattern : str):
		self._pattern = pattern
		self._regex = re.compile(pattern)

	def get_pattern(self) -> str:
		return self._pattern

	def __call__(self, value) -> bool:
		return bool(self._regex.search(str(value)))


class ExpressionFilter(Filter):
	"""
	A filter based on an expression that can be used to filter a list of values.
	Although usage can be similar to a SelectionFilter, this filter acts in a more general way. 

	For example: 
	'x < 5 and x > 3'
	'x < 2022-01-01 or x > 2025-01-01' 
	
	These expressions are internally 
	"""
	def __init__(self, expression : str):
		self._expression = expression
		self.set_expression(expression)


	def set_expression(self, expression : str):
		"""
		Raises:
		SyntaxError: If the expression is not valid
		"""
		self._expression = expression
		self._parsed_expression, self._filter_lambda =\
			generate_filter_from_string(expression) #Generate a lambda-like function from the expression


	def __call__(self, value) -> bool:
		"""
		Filters the value based on the expression

		Raises:
			NameError: If the lambda contains a variable that is not defined
		"""
		res = self._filter_lambda(value)
		return res

class SelectionFilter(Filter):
	"""
	A filter based on a set of values, if the value is in the set, the filter returns True
	"""
	def __init__(self, values : set):
		self._values = values
	
	def set_selection(self, values : set):
		self._values = values
	
	def remove_item(self, value):
		self._values.remove(value)
	
	def add_item(self, value):
		self._values.add(value)

	def get_selection(self) -> set:
		return self._values

	def __call__(self, value) -> bool:
		return value in self._values


def ends_with(value, filter_value) -> bool:
	"""Check if the value ends with the filter_value
	"""
	return str(value).endswith(str(filter_value))

def starts_with(value, filter_value) -> bool:
	"""Check if the value starts with the filter_value
	"""
	return str(value).startswith(str(filter_value))

def generate_filter_from_string(filter : str) -> tuple[str, typing.Callable]:
	"""
	Tries to parse an input-string to a lambda function that can be used to filter a list of values.
	Takes in a filter such as:
	"<5 and >3 or ==4 or == 0.1 or startswith(2.01)"

	And converts it to:
	lambda x : x < 5 and x > 3 or x == 4 or x == 0.1 or endswith(x, 1000000.001) or startswith(x, 2.01)

	NOTE: & and | are converted to and and or respectively - not the bit-wise operators in python	
	"""

	filter = re.sub(r"\s+\|\s+", " or ", filter)
	filter = re.sub(r"\s+\&\s+", " and ", filter)


	#Loop over comparitors
	for comparitor in FilterComparitors:
		filter = filter.replace(comparitor.value, f"x {comparitor.value} ")
	

	#Loop over functions
	for function in FilterFunctions:
		#If () is used, replace everything inside with x, value
		filter = re.sub(f"{function.value}\s*\((.*)\)", f"{function.value}(x, \\1)", filter)

		#If not; 

	#if datetime, regex search for dates and replace them with datetime objects
	#Replace all instances (Also time) such as:
	# 2022-01-01
	# 2022/01/01 12:00:00
	# 01-01-2022 12:00:00
	filter = re.sub(r"(\d{4}[/-]\d{2}[/-]\d{2})(\s?\d{2}:\d{2}(:\d{2})?)?", "parser.parse('\\1 \\2\\3')", filter)
	filter = re.sub(r"(\d{2}[/-]\d{2}[/-]\d{4})(\s*\d{2}:\d{2}(:\d{2})?)?", "parser.parse('\\1 \\2\\3')", filter)

	lambda_str = f"lambda x: ({filter})"

	return lambda_str, eval(lambda_str)





if __name__ == "__main__":
	print("Running tests")
	parsednumb, numb = generate_filter_from_string(	
		"( <5 & >3) | ==4 | == 0.1 | ends_with(1000000.001) | starts_with(200.00000001)")
	parseddat, dat = generate_filter_from_string(
		"<2022-01-01 and >2021-01-01 12:30 or >01-01-2021 12:30 or == 2021-01-01")
	
	parseddat2, dat2 = generate_filter_from_string(
		"ends_with('01-09') or starts_with('2021-01')"
	)

	print(parsednumb)
	print(parseddat)
	print(parseddat2)

	print(numb(4))
	print(dat(datetime.datetime(2021, 1, 1, 12, 30)))
	print(dat(datetime.datetime(2021, 1, 1, 12, 31)))
	print(dat2(datetime.datetime(2021, 1, 9)))
	print(dat2(datetime.datetime(2022, 1, 9)))