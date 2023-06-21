


from PySide6.QtWidgets import QTableView, QApplication, QHeaderView
from PySide6.QtCore import Qt
# import PySide6.QtCore as QtCore
from PySide6 import QtCore, QtWidgets, QtGui
from PySide6.QtGui import QKeySequence, QShortcut
import typing
import os
import pandas as pd
from enum import Enum
from numbers import Number

class TableViewRoles(Enum):
	headerRole = Qt.ItemDataRole.UserRole + 1

# class FilterSortHeaderView(QHeaderView):
# 	def __init__(self, orientation: QtCore.Qt.Orientation, parent: typing.Optional[QtWidgets.QWidget] = None) -> None:
# 		super().__init__(orientation, parent)

class PandasTableProxyModel(QtCore.QSortFilterProxyModel): #Enables sorting and filtering and special icons indicating which columns are sorted
	def __init__(self, parent=None):
		super().__init__(parent)

		self._sort_columns = [] #List of column names to sort by
		self._sort_order = [] #Qt.DescendingOrder or Qt.SortOrder.AscendingOrder
		self._filter_columns = [] #List of column names to filter by
		self._filter_strings = [] #List of strings to filter by
		# self.setSortRole(QtCore.Qt.ItemDataRole.EditRole) #Sort by the edit role (so that we can sort by the value in the cell, not the display role)


	def headerData(self,
				section: int,
				orientation: QtCore.Qt.Orientation,
				role: int = Qt.ItemDataRole.DisplayRole
			) -> typing.Any:
		if role == TableViewRoles.headerRole.value:
			default_data = self.sourceModel().headerData(section, orientation, Qt.ItemDataRole.DisplayRole)
			sort_by = None #None=not sorted, Qt.SortOrder.AscendingOrder=ascending, Qt.DescendingOrder=descending
			#Check if this column is sorted
			for i, col in enumerate(self._sort_columns):
				if col == default_data:
					sort_by = self._sort_order[i]
					break

			return (*default_data, )

		return super().headerData(section, orientation, role)

	def lessThan(self, left: QtCore.QModelIndex, right: QtCore.QModelIndex) -> bool:
		"""Sort by the edit role (so that we can sort by the value in the cell, not the display role)"""
		ldata = self.sourceModel().data(left, Qt.ItemDataRole.EditRole)
		rdata = self.sourceModel().data(right, Qt.ItemDataRole.EditRole)
		lnone = ldata is None or pd.isnull(ldata)
		rnone = rdata is None or pd.isnull(rdata)
		if lnone:
			if rnone:
				return False
			return True
		try:
			val = ldata < rdata
			return val
		except Exception as e:
			return super().lessThan(left, right)



class PandasTableView(QTableView):
	DESCRIPTION = "A view to display a pandas dataframe, works best in combination with PandasTableModel - places a proxymodel in between the tableview and the model to allow sorting and filtering"

	def __init__(self, parent=None, status_bar=None):
		QTableView.__init__(self, parent)
		self._status_bar = None
		#If ctrl+c is pressed, copy the selection to the clipboard
		self._copy_shortcut = QShortcut(QKeySequence("Ctrl+C"), self)
		self._copy_shortcut.activated.connect(self.copySelection)


		self.Proxy_Model = PandasTableProxyModel(self)
		self.Proxy_Model.setDynamicSortFilter(True)
		self.Proxy_Model.setSourceModel(None)
		# self._proxy_model.setSortRole(QtCore.Qt.ItemDataRole.EditRole) #Sort by the edit role (so that we can sort by the value in the cell, not the display role)
		super().setModel(self.Proxy_Model)
		# self.Proxy_Model.setSortRole(QtCore.Qt.ItemDataRole.EditRole) #Sort by the edit role (so that we can sort by the value in the cell, not the display role)

		self.selectionModel().selectionChanged.connect(self.displaySelectionStats) #TODO:

		self.setSortingEnabled(True)
		#Detect right-clicks on table headers
	# 	self.horizontalHeader().sectionClicked.connect(self.headerClicked)


	def setStatusBar(self, status_bar):
		self._status_bar = status_bar

	def setModel(self, model: QtCore.QAbstractItemModel) -> None:
		return self.Proxy_Model.setSourceModel(model)



	def copySelection(self):
		# clear the current contents of the clipboard
		selected = self.selectedIndexes()
		rows = []
		columns = []
		# cycle all selected items to get the minimum row and column, so that the
		# reference will always be [0, 0]
		for index in selected:
			rows.append(index.row())
			columns.append(index.column())
		min_row = min(rows)
		max_row = max(rows)
		min_col = min(columns)
		maxCol = max(columns)

		#Create a string with the selected data, using tabs and newlines (excel-like-format)
		clip_data = ""
		for row in range(min_row, max_row + 1):
			sep = ""
			for column in range(min_col, maxCol + 1):
				clip_data += sep
				index = self.model().index(row, column)
				sep = "\t"
				clip_data += str(self.model().data(index, Qt.ItemDataRole.EditRole))
			clip_data += os.linesep

		clipboard = QApplication.clipboard()
		clipboard.clear()
		clipboard.setText(clip_data)


	def getSelectedCells(self):
		"""Return a list of the selected cells"""
		cells = []
		for index in self.selectedIndexes():
			cells.append((index.row(), index.column()))
		return cells

	def getSelectedData(self, discard_empty=True, discard_nan=True):
		"""Return a list of the selected data"""
		data = []
		for index in self.selectedIndexes():
			if discard_empty and self.model().data(index, Qt.ItemDataRole.DisplayRole) == "":
				continue
			if discard_nan and self.model().data(index, Qt.ItemDataRole.EditRole) is None or pd.isnull(self.model().data(index, Qt.ItemDataRole.EditRole)):
				continue
			data.append(self.model().data(index, Qt.ItemDataRole.EditRole))
		return data


	def displaySelectionStats(self):
		"""Display the number of selected cells, the average and the sum of the selected data"""
		if self._status_bar is None: #Only show stats if a status bar is available
			return

		#Get the data from the selected cells
		data = self.getSelectedData()

		#Get the average and sum of the selected data
		try:
			average = round(sum(data) / len(data), 2)
			total = round(sum(data), 2)
			thesum = sum(data)
		except (TypeError, ZeroDivisionError):
			average = "-"
			total = "-"
			thesum = "-"
		additional_text = ""

		if len(data) == 2: #If we selected exactly 2 cells -> also show the difference
			try:
				difference = abs(data[1] - data[0])
				additional_text = ", Difference: {}".format(difference)
			except (TypeError, ZeroDivisionError):
				additional_text = ""
		#Display the results
		self._status_bar.showMessage(
			"Selected cells: {}, Average: {}, Total: {}, Sum: {}{}".format(
				len(data), average, total, thesum,additional_text
			)
		)