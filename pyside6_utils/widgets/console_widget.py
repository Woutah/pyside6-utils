"""
Implements a widget that combines a console-view and a tree-like-view so we're able to browse console outputs.
"""
import logging
import os
import threading
import time
import typing

from PySide6 import QtCore, QtWidgets, QtGui

from pyside6_utils.models.console_widget_models.console_model import (
    BaseConsoleItem, ConsoleModel)
from pyside6_utils.models.extended_sort_filter_proxy_model import \
    ExtendedSortFilterProxyModel
from pyside6_utils.ui.ConsoleWidget_ui import Ui_ConsoleWidget
from pyside6_utils.widgets.delegates.console_widget_delegate import \
    ConsoleWidgetDelegate

log = logging.getLogger(__name__)




class ConsoleWidget(QtWidgets.QWidget):
	"""Widget that dynamically displayes multiple console -
	E.g. in the case of ConsoleModel + ConsoleFromFileItems : watches the selected file for changes and updates the
	widget accordingly.	Mainly intended for use with a file to which stdout/stderr can be redirected to.
	"""

	DESCRIPTION = ("Widget that dynamically displayes multiple console - "
	"E.g. in the case of ConsoleModel + ConsoleFromFileItems : watches the selected file for changes and updates the"
	"widget accordingly. Mainly intended for use with a file to which stdout/stderr can be redirected to.")

	def __init__(self, parent: typing.Optional[QtWidgets.QWidget] = None,
			display_max_blocks = 1000, #How many blocks of text to display (lines)
		    ui_text_min_update_interval : float = 0.05
		) -> None:
		"""
		Args:
			parent (QtCore.QObject, optional): The parent. Defaults to None.
			name_date_path_model (QtCore.QStandardItemModel): The table model that contains the <name>, <last edit date>
				and <path> of the file in column 1, 2 and 3 respectively
			ui_text_min_update_interval (float, optional): The minimum interval in seconds between updating the
				current text in the UI. Defaults to 0.1.
				NOTE that setting this too low might cause the UI to become unresponsive if the console-output is updated
				too frequently (e.g. when logging a lot).
		"""
		super().__init__(parent)
		self.ui = Ui_ConsoleWidget() #pylint: disable=invalid-name
		self.ui.setupUi(self)


		self._display_max_blocks = display_max_blocks #The maximum number of blocks to display in the text edit
		self.ui.consoleTextEdit.setMaximumBlockCount(display_max_blocks)
		# self.ui.consoleTextEdit.setCenterOnScroll(True)
		self._files_proxy_model = ExtendedSortFilterProxyModel(self) #TODO: this doesn't really seem to work yet
		self.ui.fileSelectionTableView.setModel(self._files_proxy_model)

		#==============Treeview ==============
		#Sort first by date, then by name
		self.ui.fileSelectionTableView.sortByColumn(1, QtCore.Qt.SortOrder.AscendingOrder)
		self._files_proxy_model.sort_by_columns([1, 0],
					[QtCore.Qt.SortOrder.DescendingOrder, QtCore.Qt.SortOrder.AscendingOrder]) #Sort by
			# Datetime, then by name


		#Hide the third column (path) and the second column (date) from the view
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

		self._current_linechange_connect = None
		self.ui.fileSelectionTableView.viewport().setMouseTracking(True)

		self.ui.fileSelectionTableView.selectionModel().selectionChanged.connect(self.selection_changed)
		self._ui_text_min_update_interval = ui_text_min_update_interval #The minimum interval in seconds between updating the


		self.currently_loaded_lines = [0, 0] #Start with no lines


	def selection_changed(self, selection : QtCore.QItemSelection):
		"""
		Updates the UI based on the new selection. Starts the subscribtion to the new item:
		- Retrieve the current text of the item (e.g. the logfile)
		- Subscribe to the currentTextChanged signal of the item so any new text is automatically added to the UI

		Args:
			selection (PySide6.QtCore.QItemSelection): The new selection
		"""
		if self._current_linechange_connect is not None: #If selection changed -> stop subscribing to the old item
			# self._current_linechange_connect.disconnect()
			self.disconnect(self._current_linechange_connect)
			self._current_linechange_connect = None

		if len(selection.indexes()) == 0:
			self.ui.consoleTextEdit.setPlainText("")
			return
		elif selection.indexes()[0].isValid():
			self.ui.consoleTextEdit.setPlainText("")
			index = selection.indexes()[0]
			item = self._files_proxy_model.data(index, role = QtCore.Qt.ItemDataRole.UserRole + 1)
			assert isinstance(item, BaseConsoleItem), "Item is not of type BaseConsoleItem"

			#Subscribe to new lines
			self._current_linechange_connect = item.loadedLinesChanged.connect(self.process_line_change)

			#Get the current text of the item
			cur_line_list, from_index = item.get_current_line_list()
			self.process_line_change(cur_line_list, from_index)
			#Set slider to bottom
			self.ui.consoleTextEdit.verticalScrollBar().setValue(self.ui.consoleTextEdit.verticalScrollBar().maximum())


	@staticmethod
	def _get_index_nth_occurence(string : str, char : str, occurence : int) -> int:
		counter = 0
		if occurence <= 0:
			return 0
		for i, char in enumerate(string):
			if char == "\n":
				counter += 1
			if counter >= occurence:
				# self._prev_textedit_index = i
				return i

		return -1

	def process_line_change(self, new_line_list : list[str], from_line : int = 0):
		"""
		When the text of the selected item changes, this method is called.
		NOTE: it is probably most efficient if we only call this method with the new text, not the entire text, pyside
			might not be able to send python-lists efficiently TODO: check

		#TODO: also implement a reset (e.g. when file is cleared)? Right now we can only add to an existing file
		Args:
			new_line_list (list[str]): The new text of the item
			from_line (int, optional): The line-index (in the original) buffer of the item from which we replace/append the new
				lines.
		"""
		if len(new_line_list) > self._display_max_blocks: #Don't just append useless new lines that will be removed anyway
			from_line = from_line + len(new_line_list) - self._display_max_blocks
			new_line_list = new_line_list[-self._display_max_blocks:]

		new_loaded_lines = [ #Calculate the new currently loaded lines
			# max(self.currently_loaded_lines[0], from_line),
			min(self.currently_loaded_lines[0], from_line),
			max(from_line + len(new_line_list), self.currently_loaded_lines[1])
		]
		shift = 0
		#If we're exceeding the block-limit, shift the currently loaded lines
		if new_loaded_lines[1] - new_loaded_lines[0] > self._display_max_blocks:
			# new_line_list = new_line_list[new_loaded_lines[1] - new_loaded_lines[0] - self._display_max_blocks:]
			shift = new_loaded_lines[1] - self._display_max_blocks - new_loaded_lines[0]
			new_loaded_lines = new_loaded_lines[1]- self._display_max_blocks, new_loaded_lines[1] #Only keep the last x lines

		start_line = max(from_line - self.currently_loaded_lines[0], 0) #Relative to the left-most line

		#Set cursor to the desired position
		cur_cursor = self.ui.consoleTextEdit.textCursor()
		cur_cursor.movePosition(QtGui.QTextCursor.MoveOperation.Start)
		cur_cursor.movePosition(QtGui.QTextCursor.MoveOperation.Down, QtGui.QTextCursor.MoveMode.MoveAnchor, start_line)

		#Set to overwrite mode
		cur_cursor.insertText("".join([i + "\n" for i in new_line_list]))

		#Move scrollbar <shift> lines up if not at the bottom
		if self.ui.consoleTextEdit.verticalScrollBar().value() < self.ui.consoleTextEdit.verticalScrollBar().maximum()-2:
			self.ui.consoleTextEdit.verticalScrollBar().setValue(
				self.ui.consoleTextEdit.verticalScrollBar().value() - shift)
		else:
			self.ui.consoleTextEdit.verticalScrollBar().setValue(self.ui.consoleTextEdit.verticalScrollBar().maximum()-1)

		# self.currently_loaded_lines = [from_line, from_line + len(new_line_list)]
		self.currently_loaded_lines = new_loaded_lines




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




def run_example_app():
	"""Creates a qt-app instance and runs the example
	Creates a temp file and mirrors the output to the "console", then deletes the temp file afterwards
	"""
	#pylint: disable=import-outside-toplevel
	import tempfile

	from pyside6_utils.models.console_widget_models.console_from_file_item import \
	    ConsoleFromFileItem
	log.info("Now running an example using console from file items, the console should print a number every second")
	temp_dir = tempfile.gettempdir()
	temp_file = tempfile.NamedTemporaryFile(dir=temp_dir, mode='w', delete=False, suffix=".txt") #Delete temporary
		# file afterwards

	app = QtWidgets.QApplication([])
	test_console_model = ConsoleModel()
	console_widget = ConsoleWidget(ui_text_min_update_interval=0.1, display_max_blocks=5000)
	console_widget.set_model(test_console_model)


	class TestConsoleItem(BaseConsoleItem):
		def __init__(self, item_id):
			super().__init__()
			self._id = item_id
			self._line_list = []

		def get_current_line_list(self) -> typing.Tuple[list[str], int]:
			return self._line_list, 0

		def data(self, role : QtCore.Qt.ItemDataRole, column : int = 0):
			if role == QtCore.Qt.ItemDataRole.DisplayRole:
				return self._id
			else:
				return None

	test_console_item = TestConsoleItem("Test item")

	test_console_model.add_item(
		test_console_item
	)
	test_console_model.add_item(
		ConsoleFromFileItem(
			name="Output 2",
			path = temp_file.name,
		)
	)
	window = QtWidgets.QMainWindow()
	#Set size to 1000
	window.resize(1200, 500)
	console_widget.set_console_width_percentage(80)

	layout = QtWidgets.QVBoxLayout()
	layout.addWidget(console_widget)

	console_widget.set_console_width_percentage(80)

	#Create thread that
	def log_to_file():
		"""logs integer to file every seconds for 10 seconds"""
		# test_console_item._text = ("KAAS"*100 + "\n") * 20_000
		# test_console_item._line_list = "\n".join([f"{i%10} "*100 for i in range(20_000)]) #pylint: disable=protected-access
		test_console_item._line_list = [f"{i%10} "*100 for i in range(20_000)] #pylint: disable=protected-access
		cur = 0
		for i in range(20_000): #First test test-item
			newmsg = f"Wrote line {i} to file {temp_file.name}"
			test_console_item._line_list.append(newmsg) #pylint: disable=protected-access
			test_console_item.loadedLinesChanged.emit([newmsg], len(test_console_item._line_list))
			cur += 1
			time.sleep(0.02)
		print("DONE!")
		# for i in range(200000):
		# 	temp_file.write(f"Wrote line {i} to file {temp_file.name}\n")
		# 	temp_file.flush()
		# 	time.sleep(0.1)
	thread = threading.Thread(target=log_to_file)
	thread.start()


	window.setCentralWidget(console_widget)
	window.show()
	app.exec()
	temp_file.close()
	#remove the temp file
	os.remove(temp_file.name)



if __name__ == "__main__":
	formatter = logging.Formatter("[{pathname:>90s}:{lineno:<4}]  {levelname:<7s}   {message}", style='{')
	handler = logging.StreamHandler()
	handler.setFormatter(formatter)
	logging.basicConfig(
		handlers=[handler],
		level=logging.DEBUG) #Without time

	#Run example
	run_example_app()