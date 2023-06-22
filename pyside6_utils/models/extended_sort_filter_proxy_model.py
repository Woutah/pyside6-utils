"""Implements and extended version of QSortFIlterProxyModel with extra functionality (see class docstring)"""

import math
import numbers

from PySide6 import QtCore


class ExtendedSortFilterProxyModel(QtCore.QSortFilterProxyModel):
	"""
	Wrapper around the QSortFilterProxyModel which enables the use of multiple sort-columns instead of just one.
	If 2 items are not-sortable by column 1, we sort by column 2, then 3 etc. etc.
	"""
	def __init__(self, parent: QtCore.QObject | None = ...) -> None:
		super().__init__(parent)
		self._sort_columns : list[int] = []
		self._sort_orders : list[QtCore.Qt.SortOrder] = []


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
