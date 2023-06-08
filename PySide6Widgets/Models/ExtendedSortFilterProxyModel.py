from typing import Optional
from PySide6 import QtCore, QtWidgets, QtGui
import PySide6.QtCore
import math
import numbers

	# def lessThan(self, left: QtCore.QModelIndex, right: QtCore.QModelIndex) -> bool:
	# 	"""Sort by the edit role (so that we can sort by the value in the cell, not the display role)"""
	# 	ldata = self.sourceModel().data(left, Qt.EditRole)
	# 	rdata = self.sourceModel().data(right, Qt.EditRole)
	# 	lnone = ldata is None or pd.isnull(ldata)
	# 	rnone = rdata is None or pd.isnull(rdata)
	# 	if lnone:
	# 		if rnone:
	# 			return False
	# 		return True
	# 	try:
	# 		val = ldata < rdata
	# 		return val
	# 	except Exception as e:
	# 		return super().lessThan(left, right)



class ExtendedSortFilterProxyModel(QtCore.QSortFilterProxyModel):
	"""
	Wrapper around the QSortFilterProxyModel which enables the use of multiple sort-columns instead of just one.
	If 2 items are not-sortable by column 1, we sort by column 2, then 3 etc. etc.
	"""
	def __init__(self, parent: QtCore.QObject | None = ...) -> None:
		super().__init__(parent)
		self._sort_columns : list[int] = []
		self._sort_orders : list[QtCore.Qt.SortOrder] = []


	def _valLessThan(self, leftval, rightval):
		if leftval is None or (isinstance(leftval, numbers.Number) and math.isnan(leftval)):
			return True
		elif rightval is None or (isinstance(rightval, numbers.Number) and math.isnan(rightval)):
			return False
		
		return leftval < rightval

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
				leftval = left.data(role=QtCore.Qt.EditRole)
				rightval = right.data(role=QtCore.Qt.EditRole)
				# print(f"{leftval} < {rightval} = {self._valLessThan(leftval, rightval)} -> other way around : {self._valLessThan(rightval, leftval)}")
				if self._valLessThan(leftval, rightval) == self._valLessThan(rightval, leftval): #If the values are equal, continue to the next column
					continue
				else:
					return self._valLessThan(leftval, rightval) if order == QtCore.Qt.AscendingOrder else self._valLessThan(rightval, leftval)

		return False #If we can't differentiate the rows, return False (i.e. don't swap them)


	def sortByColumns(self, columns: list[int], orders: list[QtCore.Qt.SortOrder] = None) -> None:
		"""
		Sets the sort-columns and their respective sort-orders.
		
		:param columns: The columns to sort by.
		:param orders: The sort-orders to use for the columns. If None, the default sort-order is used.
		"""
		if orders is None:
			orders = [QtCore.Qt.AscendingOrder] * len(columns)
		self._sort_columns = columns
		self._sort_orders = orders
		self.invalidate()

