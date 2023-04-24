


from PySide6.QtWidgets import QTableView, QApplication
from PySide6.QtCore import Qt
import PySide6.QtCore as QtCore
from PySide6.QtGui import QKeySequence, QShortcut
import os
import pandas as pd

class PandasTableView(QTableView):
	#Create a constant (uneditable) class-variable that stores a description of the widget
	DESCRIPTION = "A view to display a pandas dataframe, works best in combination with PandasTableModel"

	def __init__(self, parent=None, status_bar=None):
		QTableView.__init__(self, parent)
		self._status_bar = None
		#If ctrl+c is pressed, copy the selection to the clipboard
		self._copy_shortcut = QShortcut(QKeySequence("Ctrl+C"), self)
		self._copy_shortcut.activated.connect(self.copySelection)
	
	def setStatusBar(self, status_bar):
		self._status_bar = status_bar

	def setModel(self, model: QtCore.QAbstractItemModel) -> None:
		ret = super().setModel(model)
		self.selectionModel().selectionChanged.connect(self.displaySelectionStats)
		return ret
	

	
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
				clip_data += str(self.model().data(index, Qt.EditRole))
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
			if discard_empty and self.model().data(index, Qt.DisplayRole) == "":
				continue
			if discard_nan and self.model().data(index, Qt.EditRole) is None or pd.isnull(self.model().data(index, Qt.EditRole)):
				continue
			data.append(self.model().data(index, Qt.EditRole))
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
		except (TypeError, ZeroDivisionError):
			average = "-"
			total = "-"

		#Display the results
		self._status_bar.showMessage(
			"Selected cells: {}, Average: {}, Total: {}".format(
				len(data), average, total
			)
		)