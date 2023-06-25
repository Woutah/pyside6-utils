"""Implements and extended version of QSortFIlterProxyModel with extra functionality (see class docstring)"""

import logging
import math
import numbers
import typing

from PySide6 import QtCore

log = logging.getLogger(__name__)



FilterFunctionType =\
	typing.Callable[[int, QtCore.QModelIndex | QtCore.QPersistentModelIndex, QtCore.QAbstractItemModel], bool] #Filter
		#function => source_row, source_parent (index), source_model

class ExtendedSortFilterProxyModel(QtCore.QSortFilterProxyModel):
	"""
	Wrapper around the QSortFilterProxyModel which enables the use of multiple sort-columns instead of just one.
	If 2 items are not-sortable by column 1, we sort by column 2, then 3 etc. etc.

	Also implements a function-list based custom filtering system.
	Using setFilterFunction, the user can add a function that is used to AND-filter the rows.
	Filter-functions take a row as argument and return a bool. If the function returns True, the row is accepted.

	NOTE: Filtering is AND-ed with the default filterAcceptsRow function, so we can still use the default functionality
	in addition to the custom functions.
	"""

	def __init__(self, parent: QtCore.QObject | None = ...) -> None:
		super().__init__(parent)
		self._sort_columns : list[int] = []
		self._sort_orders : list[QtCore.Qt.SortOrder] = []
		self._filter_functions : typing.Dict[str, FilterFunctionType] = {}


	def _val_less_than(self, leftval, rightval):
		if leftval is None or (isinstance(leftval, numbers.Number) and math.isnan(leftval)): #type: ignore
			return True
		elif rightval is None or (isinstance(rightval, numbers.Number) and math.isnan(rightval)): #type: ignore
			return False
		return leftval < rightval #type: ignore

	def lessThan(self, left: QtCore.QModelIndex, right: QtCore.QModelIndex) -> bool:
		"""
		Reimplemented from QSortFilterProxyModel.
		"""

		if len(self._sort_columns) == 0: #If using default behaviour, use the default implementation
			return super().lessThan(left, right)
		else:
			for column, order in zip(self._sort_columns, self._sort_orders):
				left = self.sourceModel().index(left.row(), column)
				right = self.sourceModel().index(right.row(), column)
				leftval = left.data(role=QtCore.Qt.ItemDataRole.EditRole)
				rightval = right.data(role=QtCore.Qt.ItemDataRole.EditRole)
				if self._val_less_than(leftval, rightval) == self._val_less_than(leftval=rightval, rightval=leftval):
					#If the values are equal, continue to the next column
					continue
				else:
					return self._val_less_than(leftval, rightval) if \
						order == QtCore.Qt.SortOrder.AscendingOrder else self._val_less_than(leftval, rightval)

		return False #If we can't differentiate the rows, return False (i.e. don't swap them)


	def sort_by_columns(self, columns: list[int], orders: list[QtCore.Qt.SortOrder] | None = None) -> None:
		"""
		Sets the sort-columns and their respective sort-orders.

		:param columns: The columns to sort by.
		:param orders: The sort-orders to use for the columns. If None, the default sort-order is used.
		"""
		if orders is None or orders == []: #If no orders are specified, use the default order
			orders = [QtCore.Qt.SortOrder.AscendingOrder] * len(columns)
		self._sort_columns = columns
		self._sort_orders = orders
		self.invalidate()

	def set_filter_function(self,
			   function_name : str,
			   function : FilterFunctionType
			):
		"""
		Adds a filter function to the proxy model. All filter-functions together are AND-ed with the default
		filterAcceptsRow function to determine if a row is accepted.

		NOTE: overwrites any existing filter function with the same name, if it does, filters are invalidated

		Args:
			function_name (str): The name of the filter function (used to identify it)
			function (FILTER_FUNCTION_TYPE): The filter function to add
		"""
		invalidate = False
		if function_name in self._filter_functions:
			invalidate = True
		self._filter_functions[function_name] = function
		if invalidate:
			self.invalidateFilter()


	def clear_function_filters(self):
		"""Clear all filter functions"""
		self._filter_functions = {}
		self.invalidateFilter()

	def get_filter_functions(self) -> typing.Dict[str, FilterFunctionType]:
		"""Returns a dict of all filter functions"""
		return self._filter_functions

	def filterAcceptsRow(self,
				source_row: int,
				source_parent: QtCore.QModelIndex | QtCore.QPersistentModelIndex
			) -> bool:
		"""Calls QSortFilterProxyModel.filterAcceptsRow and ANDs the result with all filter functions

		NOTE: if any filter function raises an exception on a row, the row is not accepted and the error is logged.
		All filter functions are "AND-ed" together with the default filterAcceptsRow function.
		"""
		if not super().filterAcceptsRow(source_row, source_parent):
			return False
		for function in self._filter_functions.values():
			try:
				if not function(source_row, source_parent, self.sourceModel()):
					return False
			except Exception as exception: #pylint: disable=broad-except
				log.error(f"Error while filtering row {exception} - {type(exception).__name__}: {exception}")
				return False
		return True
