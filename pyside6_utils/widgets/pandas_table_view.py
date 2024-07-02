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
from PySide6 import QtCore, QtWidgets
from PySide6.QtCore import Qt
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import QApplication, QTableView

from pyside6_utils.widgets.table_filter_dialog import TableFilterDialog

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

		self.column_filters : dict[int, typing.Callable] = {} #A dictionary of callable column-filter classes. 
		# The key is the column number and the value is the callable class that filters the rows in this column
		# The callable class should take a single argument (the value) and return True if the value should be accepted 

		self.filterRole

	def acceptRow(self, source_row: int, source_parent: QtCore.QModelIndex) -> bool:
		"""Check if the row should be accepted based on the filter"""
		if not self.column_filters or len(self.column_filters.items()) == 0:
			return True

		for column, filter_func in self.column_filters.items():
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
		except Exception as exception: #pylint: disable=broad-except,unused-variable
			return super().lessThan(left, right)



class PandasTableView(QTableView):
	"""A view to display a pandas dataframe, works best in combination with PandasTableModel - places a"
		proxymodel in between the tableview and the model to allow sorting and filtering
		
		Also enables the use of individual QSortFilterProxyModels for each column to enable column-specific filtering
		As soon as a column-filter is added, the structure becomes:

		<Original Model>
		|
		proxy_model
		|
		column_filter_proxy_model (for column 1)
		|
		etc. (Other column-filters)
		| 
		View
		
		"""
	DESCRIPTION = ("A view to display a pandas dataframe, works best in combination with PandasTableModel - places a"
		"proxymodel in between the tableview and the model to allow sorting and filtering")

	def __init__(self, parent=None, status_bar=None):
		QTableView.__init__(self, parent)
		self._status_bar = status_bar
		#If ctrl+c is pressed, copy the selection to the clipboard
		self._copy_shortcut = QShortcut(QKeySequence("Ctrl+C"), self)
		self._copy_shortcut.activated.connect(self.copy_selection_to_clipboard)



		self.proxy_model = PandasTableProxyModel(self) #A proxy model accesible to outside - for some other filtering
		self.proxy_model.setDynamicSortFilter(True)
		self.proxy_model.setSourceModel(None) #type: ignore


		self._column_filter_proxies : dict[int, PandasTableProxyModel] = {

		} #Dictionary of subproxy models using the format:
		# {
		# 	column_name: proxy_model
		# 	etc.
		# }
		self._column_filter_proxy_order = [] #List of proxies in the filter-order (most recently added last)

		super().setModel(self.proxy_model)

		self.selectionModel().selectionChanged.connect(self.display_selection_stats) #TODO:
		self.setSortingEnabled(True)
		#Detect right-clicks on table headers
		# self.horizontalHeader().sectionClicked.connect(self.headerClicked)


		#========== Add Right-Click Menu to each column header ==========
		self.horizontalHeader().setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
		self.horizontalHeader().customContextMenuRequested.connect(self._column_filter_popup)
		self._cur_column_filter_dialog = None


	def get_column_entries(
			self,
			column : int,
			convert_to_string : bool = True,
			role : int = Qt.ItemDataRole.EditRole
		) -> set:
		"""
		Get set of unique entries in the given column for filtering purposes

		convert_to_string: If True, convert all entries to strings
		role: The role to use when getting the data (default: Qt.ItemDataRole.EditRole)
		"""
		entries = set()
		for row in range(self.model().rowCount()):
			index = self.model().index(row, column)
			entries.add(self.model().data(index, role))
		return entries

	def _column_filter_popup(self, pos : QtCore.QPoint):
		"""Show a popup menu to filter the given column on right-click"""
		
		col = self.horizontalHeader().logicalIndexAt(pos)
		old_filter = None
		if col in self._column_filter_proxies:
			old_filter = self._column_filter_proxies[col].filterRegularExpression()

		dialog = TableFilterDialog(
			column_entries=self.get_column_entries(col),
			old_filter=old_filter,
		)

		#Convert pos to global pos
		pos = self.horizontalHeader().mapToGlobal(pos)
		dialog.move(pos)
		dialog.show()

		self._cur_column_filter_dialog = dialog

	def get_column_proxy(self, column : int, create_if_none : bool = False):
		"""Return the proxy for the given column
		If create_if_none is True, create a new proxy if none exists
		"""	
		if column in self._column_filter_proxies:
			return self._column_filter_proxies[column]
		elif create_if_none:
			self.set_column_regex_filter(column, filter="")
			return self._column_filter_proxies[column]
		else:
			return None

	def set_column_regex_filter(self, column : int, filter : typing.Optional[str] = None) -> None:
		"""
		Create a proxy for the given column and set the filter to the given regex (or remove the filter if None).

		The proxy is added to a list of proxies (if multiple columns are filtered, the proxies are linked together)
		so that the view can be set to the last added proxy to show the filtered data.

		NOTE: Empty string creates a proxy that filters nothing
		"""

		if filter is None: 
			if column in self._column_filter_proxies:
				filter_order = self._column_filter_proxy_order.index(column)
				if len(self._column_filter_proxy_order) == 1:
					#If this was the only filter -> remove the filter and set view to the proxy_model
					super().setModel(self.proxy_model)
				elif filter_order == len(self._column_filter_proxy_order) - 1:
					#If most recently added (last item in list) -> remove the filter and set view to the previous filter
					previous_filter_id = self._column_filter_proxy_order[-2]
					super().setModel(self._column_filter_proxies[previous_filter_id])
				elif filter_order == 0: 
					#If the first filter -> remove the filter 
					next_filter = self._column_filter_proxies[self._column_filter_proxy_order[1]]
					next_filter.setSourceModel(self.proxy_model)
				else:
					#If removing a proxy in the middle -> link left and right proxies
					left_filter = self._column_filter_proxies[self._column_filter_proxy_order[filter_order - 1]]
					right_filter = self._column_filter_proxies[self._column_filter_proxy_order[filter_order + 1]]
					left_filter.setSourceModel(right_filter) 

				
				
				del self._column_filter_proxies[column] #Delete the filter
				del self._column_filter_proxy_order[filter_order] #Delete the filter from the ordering
				return
		else:
			#If the filter is not None, create a new filter
			proxy = PandasTableProxyModel(self)
			proxy.setSourceModel(self.proxy_model)
			proxy.setFilterKeyColumn(column)
			proxy.setFilterRegularExpression(filter)

		
		pass




	# def reset_column_filters(self):
	# 	"""Remove all column filters and"""

	# 	self._subproxy_models = {}

	def set_status_bar(self, status_bar):
		"""Set the status bar to be used by the view, e.g. when making a selection"""
		self._status_bar = status_bar

	def setModel(self, model: QtCore.QAbstractItemModel) -> None: #type: ignore
		"""Set the model for the table view"""
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
	example_df = pd.DataFrame({
		"Column 1": [1, 2, 3, 4, 5],
		"Column 2": [10, 20, 30, 40, 50],
		"Column 3": [100, 200, 300, 400, 500],
		"Column 4": [1000, 2000, 3000, 4000, 5000],
		"Column 5": [0.1, 0.01, 0.001, 0.0001, 0.00001],
		"Column 6": ["A", "B", "C", "D", "E"],
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