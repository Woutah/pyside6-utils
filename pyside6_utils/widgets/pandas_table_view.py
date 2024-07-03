"""Implements a Qt-View used to display a pandas dataframe as a table.
This view implements some extra funcitonality such as a custom proxy model to enable better sorting and filtering.
Also enables the copy/pasting of data, while setting the status bar to display the number of selected cells, the average
and the sum of the selected data.
"""


import logging
import os
import typing
from enum import Enum

import pandas as pd
from PySide6 import QtCore, QtWidgets, QtGui
from PySide6.QtCore import Qt
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import QApplication, QTableView

from pyside6_utils.widgets.table_filter_dialog import TableFilterDialog
from pyside6_utils.utility.view_filter import RegexFilter, ExpressionFilter, SelectionFilter, CombinationFilter, Filter

log = logging.getLogger(__name__)



class TableViewRoles(Enum):
	"""Enum woth roles used by the table view"""
	HEADER_ROLE = Qt.ItemDataRole.UserRole + 1

# class FilterSortHeaderView(QHeaderView):
# 	def __init__(self, orientation: QtCore.Qt.Orientation, parent: typing.Optional[QtWidgets.QWidget] = None) -> None:
# 		super().__init__(orientation, parent)

class PandasTableProxyModel(QtCore.QSortFilterProxyModel):
	"""
	Enables sorting and filtering and special icons indicating which columns are sorted
	"""
	def __init__(self, parent=None):
		super().__init__(parent)

		self.column_filters : dict[int, Filter] = {} #A dictionary of callable column-filter classes. 
		# The key is the column number and the value is the callable class that filters the rows in this column
		# The callable class should take a single argument (the value) and return True if the value should be accepted 

		self._filter_icon = QtGui.QIcon()
		self._filter_icon.addFile(
			u":/icons/custom/filter.svg", QtCore.QSize(), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)


	def filterAcceptsRow(self, source_row: int, source_parent: QtCore.QModelIndex, column_filter_ignore_list : list[int] | None = None) -> bool:
		"""Check if the row should be accepted based on the filter
		
		Args:
			source_row (int): The row to check
			source_parent (QtCore.QModelIndex): The parent index of the row
			column_filter_ignore_list (list[int]): A list of columns to ignore when filtering (default: []) - this is a 
				addition to the base implementation to enable us to retrieve all rows when filtering on only part of the columns
		"""
		if column_filter_ignore_list is None:
			column_filter_ignore_list = []

		if not self.column_filters or len(self.column_filters.items()) == 0:
			return True

		for column, filter_func in self.column_filters.items():
			if column in column_filter_ignore_list:
				continue
			index = self.sourceModel().index(source_row, column)
			value = self.sourceModel().data(index, Qt.ItemDataRole.EditRole) #TODO: self.filterRole()? Or put inside filter
			if not filter_func(value):
				return False
		return True
	

	def headerData(self,
				section: int,
				orientation: QtCore.Qt.Orientation,
				role: int = Qt.ItemDataRole.DisplayRole
			) -> typing.Any:
		if role == TableViewRoles.HEADER_ROLE.value:
			default_data = self.sourceModel().headerData(section, orientation, Qt.ItemDataRole.DisplayRole)
			# sort_by = None #None=not sorted, Qt.SortOrder.AscendingOrder=ascending, Qt.DescendingOrder=descending
			# #Check if this column is sorted

			return (*default_data,)
		
		if orientation == Qt.Orientation.Horizontal:
			#Add icon if the column has a filter
			if role == Qt.ItemDataRole.DecorationRole:
				if section in self.column_filters:
					# return QtWidgets.QApplication.style().standardIcon(QtWidgets.QStyle.StandardPixmap.SP_DialogYesButton)
					return self._filter_icon

		return super().headerData(section, orientation, role)

	# def filterAcceptsRow(self, source_row: int, source_parent: QtCore.QModelIndex) -> bool:
	# 	"""Check if the row should be accepted based on the filter"""


	def lessThan(self, left: QtCore.QModelIndex, right: QtCore.QModelIndex) -> bool:
		"""Sort by the edit role (so that we can sort by the value in the cell, not the display role)
		
		TODO: maybe setting filterRole is enough to achieve the same except for the pd.isnull part
		"""
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
		except Exception as _:
			return super().lessThan(left, right)



class PandasTableView(QTableView):
	"""A view to display a pandas dataframe, works best in combination with PandasTableModel - places a"
		proxymodel in between the tableview and the model to allow sorting and filtering
		
		The proxymodel allows for individual column-based filtering
		
		"""
	DESCRIPTION = ("A view to display a pandas dataframe, works best in combination with PandasTableModel - places a"
		"proxymodel in between the tableview and the model to allow sorting and filtering")

	def __init__(self, parent=None, status_bar=None):
		QTableView.__init__(self, parent)
		self._status_bar = status_bar
		#If ctrl+c is pressed, copy the selection to the clipboard
		self._copy_shortcut = QShortcut(QKeySequence("Ctrl+C"), self)
		self._copy_shortcut.activated.connect(self.copy_selection_to_clipboard)


		self._source_model = None #The actual source model
		self.proxy_model = PandasTableProxyModel(self) #A proxy model accesible to outside - for some other filtering
		self.proxy_model.setDynamicSortFilter(True)
		self.proxy_model.setSourceModel(None) #type: ignore


		super().setModel(self.proxy_model)
		self.selectionModel().selectionChanged.connect(self.display_selection_stats) #TODO:
		self.setSortingEnabled(True)
		#Detect right-clicks on table headers
		# self.horizontalHeader().sectionClicked.connect(self.headerClicked)


		#========== Add Right-Click Menu to each column header ==========
		self.horizontalHeader().setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
		self.horizontalHeader().customContextMenuRequested.connect(self._column_filter_popup)
		self._cur_column_filter_dialog = None

	#The following function edits the display role of table headers such that a small icon is displayed if the column is sorted
	



	def get_column_entries(
			self,
			column : int,
			role : int = Qt.ItemDataRole.EditRole,
			column_filter_ignore_list : list[int] | None = None,
			skip_nan_none : bool = True
		) -> set:
		"""
		Get set of unique entries in the given column for further filtering purposes. 
		Allows re-filtering the base model while ignoring the to-be-refiltered column.

		args:
			column (int): The column to get the entries from
			role (int): The role to use when getting the data (default: Qt.ItemDataRole.EditRole)
			column_filter_ignore_list (list[int]): A list of columns to ignore when filtering (default: []) - this is a 
				addition to the base implementation to enable us to retrieve all rows when filtering on only part of the columns
		"""
		entries = set()
		need_to_refilter = True
		if column_filter_ignore_list is None or len(column_filter_ignore_list) == 0:
			#No need to refilter if we are not filtering on any columns
			need_to_refilter = False
		else:
			#If we refilter without certain columns, but those had no filter before, we don't need to refilter
			need_to_refilter = False
			for col in column_filter_ignore_list:
				if col in self.proxy_model.column_filters.keys() and self.proxy_model.column_filters[col] is not None:
					need_to_refilter = True
					break
	

		if need_to_refilter:
			if self._source_model is None:
				return entries
			for row in range(self._source_model.rowCount()):
				if not self.proxy_model.filterAcceptsRow(row, QtCore.QModelIndex(), column_filter_ignore_list):
					continue
				index = self._source_model.index(row, column)
				data = self._source_model.data(index, role)
				if skip_nan_none and (data is None or pd.isnull(data)):
					continue
				entries.add(data)
		else:
			#If no re-filtering is needed, just get the entries
			for row in range(self.model().rowCount()): #use proxy-model
				index = self.model().index(row, column)
				data = self.model().data(index, role)
				if skip_nan_none and (data is None or pd.isnull(data)):
					continue
				entries.add(data)
		return entries

	def _column_filter_popup(self, pos : QtCore.QPoint):
		"""Show a popup menu to filter the given column on right-click"""
		
		col = self.horizontalHeader().logicalIndexAt(pos)
		old_filter = self.proxy_model.column_filters.get(col, None)

		dialog = TableFilterDialog(
			column_entries=self.get_column_entries(col, column_filter_ignore_list=[col]), #Get the unique entries in the column - refilter such that we ignore the current column
			old_filter=old_filter,
		)
		#Convert pos to global pos
		pos = self.horizontalHeader().mapToGlobal(pos)
		dialog.move(pos)
		# dialog.show()
		self._cur_column_filter_dialog = dialog
		result = dialog.exec()

		if result == QtWidgets.QDialog.DialogCode.Accepted:
			result_filter = dialog.get_resulting_filter()
			if result_filter is None: #If the filter is None, remove the filter
				if col not in self.proxy_model.column_filters: #If nothing changed -> return
					return
				del self.proxy_model.column_filters[col]
			else:
				self.proxy_model.column_filters[col] = result_filter
		else:
			if dialog.cleared_filter():
				if col not in self.proxy_model.column_filters:
					return
				del self.proxy_model.column_filters[col]

		dialog.deleteLater()
		
		self.proxy_model.invalidateRowsFilter()
		



	def set_status_bar(self, status_bar):
		"""Set the status bar to be used by the view, e.g. when making a selection"""
		self._status_bar = status_bar

	def setModel(self, model: QtCore.QAbstractItemModel) -> None: #type: ignore
		"""Set the model for the table view"""
		self._source_model = model
		return self.proxy_model.setSourceModel(model)



	def copy_selection_to_clipboard(self):
		"""Copy the current selection to the clipboard according to excel-like-format"""
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
		max_col = max(columns)

		#Create a string with the selected data, using tabs and newlines (excel-like-format)
		clip_data = ""
		for row in range(min_row, max_row + 1):
			sep = ""
			for column in range(min_col, max_col + 1):
				clip_data += sep
				index = self.model().index(row, column)
				sep = "\t"
				clip_data += str(self.model().data(index, Qt.ItemDataRole.EditRole))
			clip_data += os.linesep

		clipboard = QApplication.clipboard()
		clipboard.clear()
		clipboard.setText(clip_data)


	def get_selected_cells(self):
		"""Return a list of the selected cells"""
		cells = []
		for index in self.selectedIndexes():
			cells.append((index.row(), index.column()))
		return cells

	def get_selected_data(self, discard_empty=True, discard_nan=True):
		"""Return a list of the selected data"""
		data = []
		for index in self.selectedIndexes():
			if discard_empty and self.model().data(index, Qt.ItemDataRole.DisplayRole) == "":
				continue
			if discard_nan and self.model().data(index, Qt.ItemDataRole.EditRole) is None or\
					pd.isnull(self.model().data(index, Qt.ItemDataRole.EditRole)):
				continue
			data.append(self.model().data(index, Qt.ItemDataRole.EditRole))
		return data


	def display_selection_stats(self):
		"""Display the number of selected cells, the average and the sum of the selected data"""
		if self._status_bar is None: #Only show stats if a status bar is available
			return

		#Get the data from the selected cells
		data = self.get_selected_data()

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
				additional_text = f", Difference: {difference}"
			except (TypeError, ZeroDivisionError):
				additional_text = ""
		#Display the results
		self._status_bar.showMessage(
			f"Selected cells: {len(data)}, Average: {average}, Total: {total}, Sum: {thesum}{additional_text}"
		)


def run_example_app():
	"""Creates a qt-app instance and runs the example"""
	#pylint: disable=import-outside-toplevel
	from PySide6 import QtWidgets

	from pyside6_utils.models import PandasTableModel
	log.info(f"Running example app for {PandasTableView.__name__}...")

	app = QtWidgets.QApplication([])
	test_window = QtWidgets.QMainWindow()
	#====== Example df for PandasTableView ======
	# example_df = pd.DataFrame({
	# 	"Column 1": [1, 2, 3, 4, 5],
	# 	"Column 2": [10, 20, 30, 40, 50],
	# 	"Column 3": [100, 200, 300, 400, 500],
	# 	"Column 4": [1000, 2000, 3000, 4000, 5000],
	# 	"Column 5": [0.1, 0.01, 0.001, 0.0001, 0.00001],
	# 	"Column 6": ["A", "B", "C", "D", "E"],
	# })

	example_df = pd.DataFrame({
		"Column 1" : [i for i in range(10000)],
		"Column 2" : [i*10 for i in range(10000)],
		"Column 3" : [i*100 for i in range(10000)],
		"Column 4" : [i*1000 for i in range(10000)],
		"Column 5" : [i*10000 for i in range(10000)],
		"Column 6" : [i*100000 for i in range(10000)],
	})

	example_df_model = PandasTableModel(example_df)
	example_view = PandasTableView()
	example_view.setModel(example_df_model)
	example_view.set_status_bar(test_window.statusBar())
	test_window.setCentralWidget(example_view)
	example_view.show()
	test_window.show()
	test_window.setFixedSize(800, 600)
	app.exec()





if __name__ == "__main__":
	formatter = logging.Formatter("[{pathname:>90s}:{lineno:<4}]  {levelname:<7s}   {message}", style='{')
	handler = logging.StreamHandler()
	handler.setFormatter(formatter)
	logging.basicConfig(
		handlers=[handler],
		level=logging.DEBUG) #Without time

	#Run example
	run_example_app()