from enum import Enum
from numbers import Number
import datetime
from dateutil import parser
import re
import typing

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


class RegexFilter:
	"""
	A filter based on a regex pattern that can be used to filter a list of values.
	"""
	def __init__(self, pattern : str):
		self._pattern = pattern
		self._regex = re.compile(pattern)

	def set_pattern(self, pattern : str):
		self._pattern = pattern
		self._regex = re.compile(pattern)

	def get_pattern(self) -> str:
		return self._pattern

	def __call__(self, value) -> bool:
		return bool(self._regex.search(str(value)))


class ExpressionFilter:
	"""
	A filter based on an expression that can be used to filter a list of values.
	Although usage can be similar to a SelectionFilter, this filter acts in a more general way. 

	For example: 
	'x < 5 and x > 3'
	'x < 2022-01-01 or x > 2025-01-01' 
	
	These expressions are internally 
	"""
	def __init__(self, expression : str, value_type : type[Number | datetime.datetime]):
		self.value_type = value_type
		self._expression = expression
		self.set_expression(expression)


	def set_expression(self, expression : str):
		self._expression = expression
		self._parsed_expression, self._filter_lambda =\
			generate_filter_from_string(expression, self.value_type) #Generate a lambda-like function from the expression


	def __call__(self, value) -> bool:
		try: 
			res = self._filter_lambda(value)
		except Exception as e:
			print(f"Error filtering value {value} with expression {self._expression} parsed to {self._parsed_expression}")
			raise e

		return res

class SelectionFilter:
	"""
	A filter based on a set of values, if the value is in the set, the filter returns True
	"""
	def __init__(self, values : set):
		self._values = values
	
	def set_selection(self, values : set):
		self._values = values
	
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

def generate_filter_from_string(filter : str, value_type : type[Number | datetime.datetime]) -> tuple[str, typing.Callable]:
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
	if value_type == datetime.datetime:
		#Replace all instances (Also time) such as:
		# 2022-01-01
		# 2022/01/01 12:00:00
		# 01-01-2022 12:00:00
		filter = re.sub(r"(\d{4}[/-]\d{2}[/-]\d{2})(\s?\d{2}:\d{2}(:\d{2})?)?", "parser.parse('\\1 \\2\\3')", filter)
		filter = re.sub(r"(\d{2}[/-]\d{2}[/-]\d{4})(\s*\d{2}:\d{2}(:\d{2})?)?", "parser.parse('\\1 \\2\\3')", filter)

		
	return filter, eval(f"lambda x: ({filter})")





if __name__ == "__main__":
	print("Running tests")
	parsednumb, numb = generate_filter_from_string(	
		"( <5 & >3) | ==4 | == 0.1 | ends_with(1000000.001) | starts_with(200.00000001)", Number)
	parseddat, dat = generate_filter_from_string(
		"<2022-01-01 and >2021-01-01 12:30 or >01-01-2021 12:30 or == 2021-01-01", datetime.datetime)
	
	parseddat2, dat2 = generate_filter_from_string(
		"ends_with('01-09') or starts_with('2021-01')", datetime.datetime
	)

	print(parsednumb)
	print(parseddat)
	print(parseddat2)

	print(numb(4))
	print(dat(datetime.datetime(2021, 1, 1, 12, 30)))
	print(dat(datetime.datetime(2021, 1, 1, 12, 31)))
	print(dat2(datetime.datetime(2021, 1, 9)))
	print(dat2(datetime.datetime(2022, 1, 9)))