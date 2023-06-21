"""
Implements a widget that combines a console-view and a tree-like-view so we're able to browse console outputs.
"""
import logging
import os
import typing

from PySide6 import QtCore, QtGui, QtWidgets
from PySide6Widgets.models.console_widget_models.console_standard_item_model import (
    BaseConsoleItem, ConsoleModel)
from PySide6Widgets.models.extended_sort_filter_proxy_model import \
    ExtendedSortFilterProxyModel
from PySide6Widgets.ui.ConsoleFromFileWidget_ui import Ui_ConsoleFromFileWidget
from PySide6Widgets.widgets.delegates.console_widget_delegate import ConsoleWidgetDelegate

log = logging.getLogger(__name__)




class ConsoleWidget(QtWidgets.QWidget):
	"""Widget that dynamically displayes multiple console -
	E.g. in the case of ConsoleModle + ConsoleFromFileItems : watches the selected file for changes and updates the 
	widget accordingly.	Mainly intended for use with a file to which stdout/stderr can be redirected to.
	"""

	DESCRIPTION = """Widget that dynamically displayes the output of multiple console instances - \
	E.g. in the case of ConsoleFromFileModel : watches the selected file for changes and updates the widget accordingly.
	Mainly intended for use with a file to which stdout/stderr can be redirected to."""

	def __init__(self, parent: typing.Optional[QtWidgets.QWidget] = None, display_max_chars = 200_000) -> None:
		"""
		Args:
			parent (QtCore.QObject, optional): The parent. Defaults to None.
			name_date_path_model (QtCore.QStandardItemModel): The table model that contains the <name>, <last edit date>
				and <path> of the file in column 1, 2 and 3 respectively
		"""
		super().__init__(parent)
		self.ui = Ui_ConsoleFromFileWidget() #pylint: disable=invalid-name
		self.ui.setupUi(self)

		self._display_max_chars = display_max_chars #The maximum number of characters to display in the text edit

		self._files_proxy_model = ExtendedSortFilterProxyModel(self) #TODO: this doesn't really seem to work yet
		# self._files_proxy_model = QtCore.QSortFilterProxyModel(self)
		# self._files_proxy_model.setSourceModel(name_date_path_model)
		self.ui.fileSelectionTableView.setModel(self._files_proxy_model)
		# self.ui.fileSelectionTableView.setSortingEnabled(True)

		#==============Treeview ==============
		#Sort first by date, then by name
		self.ui.fileSelectionTableView.sortByColumn(1, QtCore.Qt.SortOrder.AscendingOrder)
		self._files_proxy_model.sort_by_columns([1, 0],
					[QtCore.Qt.SortOrder.DescendingOrder, QtCore.Qt.SortOrder.AscendingOrder]) #Sort by
			# Datetime, then by name


		#Hide the third column (path) and the second column (date) from the view
		# self.ui.fileSelectionTableView.setColumnWidth(1, 0)
		# self.ui.fileSelectionTableView.setColumnWidth(2, 0)
		# self.ui.fileSelectionTableView.setColumnWidth(0, 800)
		self.ui.fileSelectionTableView.hideColumn(1)
		self.ui.fileSelectionTableView.hideColumn(2)

		#Hide headers
		self.ui.fileSelectionTableView.verticalHeader().hide()
		self.ui.fileSelectionTableView.horizontalHeader().hide()

		#Hide borders
		self.ui.fileSelectionTableView.setFrameShape(QtWidgets.QFrame.Shape.NoFrame)
		self.ui.fileSelectionTableView.setShowGrid(False)

		#Make it so tableview fills the entire widget
		# self.ui.fileSelectionTableView.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
		self.ui.fileSelectionTableView.horizontalHeader().setSectionResizeMode(
			QtWidgets.QHeaderView.ResizeMode.Stretch)
		# self.ui.fileSelectionTableView.header().hide()
		# self.ui.fileSelectionTableView.selectionModel().selectionChanged.connect(self._on_file_selection_changed)

		self.set_console_width_percentage(50)
		#============Textedit==================
		#Set editable to false
		self.ui.consoleTextEdit.setReadOnly(True)

		self.ui.fileSelectionTableView.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows)
		self.ui.fileSelectionTableView.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.SingleSelection)
		self.ui.fileSelectionTableView.mouseReleaseEvent = self.mouseReleaseEvent

		#Set the delegate for the first column to the custom delegate
		self.file_selection_delegate = ConsoleWidgetDelegate(self.ui.fileSelectionTableView)
		self.ui.fileSelectionTableView.setItemDelegateForColumn(0, self.file_selection_delegate)
		self.file_selection_delegate.deleteHoverItem.connect(self.delete_file_selector_at_index)

		# self.ui.consoleTextEdit.
		self._current_text_connect = None
		#When moving mouse in fileSelectionTableView, update the currently hovered item
		# self.ui.fileSelectionTableView.viewport().installEventFilter(self)
		self.ui.fileSelectionTableView.viewport().setMouseTracking(True)

		self.ui.fileSelectionTableView.selectionModel().selectionChanged.connect(self.selection_changed)
		# self.ui.fileSelectionTableView.viewport().mouseMoveEvent = self._on_mouse_move_in_treeview

	def selection_changed(self, selection : QtCore.QItemSelection):
		"""Updates the UI based on the new selection

		Args:
			selection (PySide6.QtCore.QItemSelection): The new selection
		"""
		if self._current_text_connect is not None: #If selection changed -> stop subscribing to the old item
			self._current_text_connect.disconnect()
			self._current_text_connect = None

		if len(selection.indexes()) == 0:
			self.ui.consoleTextEdit.setPlainText("")
			return
		elif selection.indexes()[0].isValid():
			index = selection.indexes()[0]
			item = self._files_proxy_model.data(index, role = QtCore.Qt.ItemDataRole.UserRole + 1)
			assert isinstance(item, BaseConsoleItem), "Item is not of type BaseConsoleStandardItemModel"
			item.currentTextChanged.connect(self._on_current_text_changed)
			self._current_text_connect = item.currentTextChanged
			self._on_current_text_changed(item.get_current_text())

	def _on_current_text_changed(self, newtext : str):
		at_end = self.ui.consoleTextEdit.verticalScrollBar().value() == self.ui.consoleTextEdit.verticalScrollBar().maximum()

		if len(newtext) > self._display_max_chars:
			newtext = newtext[-self._display_max_chars:]

		self.ui.consoleTextEdit.setPlainText(newtext[-self._display_max_chars:])

		#If cursor was at the end -> scroll to the end
		if at_end:
			self.ui.consoleTextEdit.moveCursor(QtGui.QTextCursor.MoveOperation.End) #Move the cursor to the end of
				#the text edit
			self.ui.consoleTextEdit.verticalScrollBar().setValue(self.ui.consoleTextEdit.verticalScrollBar().maximum())


	def dragMoveEvent(self, event) -> bool:
		"""Block dragmove events from re-selecting deleted items in the treeview.
		"""
		event.setAccepted(True)
		return True

	def mouseReleaseEvent(self, event) -> None:
		"""NOTE: we use this function to block mouse-release events from re-selecting deleted items in the treeview.
		This seems to be a bug with editorEvent in QStyledItemDelegate - we can't intercept the mouse-release event.
		"""
		#If release of left mouse button, accept the event
		if event.button() == QtCore.Qt.MouseButton.LeftButton:
			event.setAccepted(True)
			return
		#Otherwise propagate
		return super().mouseReleaseEvent(event)

	def delete_file_selector_at_index(self, index : QtCore.QModelIndex):
		"""Deletes the item-selector at the passed index, the console will no longer be available to the user

		Args:
			index (QtCore.QModelIndex): The index of the item to delete
		"""
		original_index = self._files_proxy_model.mapToSource(index)
		#Check if that index is the currently selected index
		selected_indexes = self.ui.fileSelectionTableView.selectionModel().selectedIndexes()
		self._files_proxy_model.sourceModel().removeRow(original_index.row(), original_index.parent()) #TODO: parent?

		selected_row = selected_indexes[0].row() if len(selected_indexes) > 0 else -1
		deleted_row = index.row()
		new_selected_row = selected_row

		if selected_row == deleted_row: #If the selected index is the same as the index to be deleted
			if deleted_row < self._files_proxy_model.rowCount():
				new_selected_row = deleted_row
			elif deleted_row - 1 >= 0 and deleted_row-1 < self._files_proxy_model.rowCount():
				new_selected_row = deleted_row-1
			else:
				new_selected_row = -1
		elif selected_row > 0: #If a selection exists
			if deleted_row < selected_row:
				new_selected_row = selected_row-1
			else:
				new_selected_row = selected_row
		if new_selected_row >= 0:
			self.ui.fileSelectionTableView.setCurrentIndex(self._files_proxy_model.index(new_selected_row, 0))
		else:
			self.ui.fileSelectionTableView.selectionModel().clearSelection()
			self.selection_changed(self.ui.fileSelectionTableView.selectionModel().selection())


	@staticmethod
	def get_file_name_path_dict_in_edit_order(path : str, only_extensions : list | None = None):
		"""Returns a dictionary of the files in the path in the order of the last modified time,
		dictionary of the form:
			<filename_without_extension> : <full_path>

		e.g.:
			{
				"file1" : "C:/path/to/file1.txt",
			}

		Args:
			path (str): The path to the directory

		Returns:
			list: The list of files in the path in the order of the last modified time
		"""
		filelist = sorted(os.listdir(path), key=lambda x: os.path.getmtime(os.path.join(path, x)), reverse=True)

		for filename in filelist: #Remove files that do not have the required extension
			if only_extensions is not None:
				if os.path.splitext(filename)[1] not in only_extensions:
					filelist.remove(filename)

		return { #Return a dictionary of the form: filename_without_extension : full_path
			os.path.splitext(filename)[0] : os.path.join(path, filename) for filename in filelist
		}


	def set_model(self, model : QtCore.QAbstractTableModel | QtCore.QAbstractItemModel):
		"""Set the model for the consolewidget

		Args:
			model (QtCore.QAbstractTableModel | QtCore.QAbstractItemModel): The new QAbastractTableModel
		"""
		self._files_proxy_model.setSourceModel(model)
		self.ui.fileSelectionTableView.hideColumn(1)
		self.ui.fileSelectionTableView.hideColumn(2)


	def get_console_width_percentage(self) -> int:
		"""Get the console width percentage. E.g. 80% would mean that 80% of the width is occupied by the console.

		Returns:
			int: The percentage of the width occupied by the console
		"""
		if self.ui.splitter.sizes()[0] == 0:
			return 0
		elif self.ui.splitter.sizes()[1] == 0:
			return 100

		return int(self.ui.splitter.sizes()[0]/(self.ui.splitter.sizes()[1] + self.ui.splitter.sizes()[0]) * 100)

	def set_console_width_percentage(self, percentage : int) -> None:
		"""Set the width-percentage of the console/selector-treeview. E.g. 80% would mean that 80% of the width is
		occupied by the console and 20% by the treeview.

		Args:
			percentage (int): The width-percentage of the console
		"""
		percentage = max(1, min(100, percentage))
		self.ui.splitter.setSizes([ 10*percentage, 10*(100-percentage)])
		self.ui.splitter.setStretchFactor(0, percentage)
		self.ui.splitter.setStretchFactor(1, 100-percentage)

	ConsoleWidthPercentage = QtCore.Property(int, get_console_width_percentage, set_console_width_percentage)




if __name__ == "__main__":
	#Creates a temp file and mirrors the output to the "console", then deletes the temp file afterwards
	from PySide6Widgets.models.console_widget_models.console_from_file_item import ConsoleFromFileItem
	import tempfile
	import threading
	import time
	print("Now running an example using console from file items, the console should print a number every second")
	temp_dir = tempfile.gettempdir()
	temp_file = tempfile.NamedTemporaryFile(dir=temp_dir, mode='w', delete=False, suffix=".txt") #Delete temporary 
		# file afterwards

	app = QtWidgets.QApplication([])
	test_console_model = ConsoleModel()
	console_widget = ConsoleWidget()
	console_widget.set_model(test_console_model)


	test_console_model.add_item(
		ConsoleFromFileItem(
			name=temp_file.name,
			path = temp_file.name,
		)
	)
	window = QtWidgets.QMainWindow()
	#Set size to 1000
	window.resize(1200, 500)
	console_widget.set_console_width_percentage(80)

	layout = QtWidgets.QVBoxLayout()
	layout.addWidget(console_widget)

	dockable_window = QtWidgets.QDockWidget("Console", window)
	dockable_window.setWidget(console_widget)

	console_widget.set_console_width_percentage(80)

	#Create thread that 
	def log_to_file():
		"""logs integer to file every seconds for 10 seconds"""
		for i in range(20):
			temp_file.write(f"Wrote line {i} to file {temp_file.name}\n")
			temp_file.flush()
			time.sleep(1)
	thread = threading.Thread(target=log_to_file)
	thread.start()


	window.setCentralWidget(dockable_window)
	window.show()
	app.exec()
	temp_file.close()
	#remove the temp file
	os.remove(temp_file.name)
