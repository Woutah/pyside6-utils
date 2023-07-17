"""
Implements a widget that combines a console-view and a tree-like-view so we're able to browse console outputs.
"""
import logging
import os
import typing

from PySide6 import QtCore, QtGui, QtWidgets
from pyside6_utils.models.console_widget_models.console_model import (
    BaseConsoleItem, ConsoleModel)
from pyside6_utils.models.extended_sort_filter_proxy_model import \
    ExtendedSortFilterProxyModel
from pyside6_utils.ui.ConsoleWidget_ui import Ui_ConsoleWidget
from pyside6_utils.widgets.delegates.console_widget_delegate import ConsoleWidgetDelegate
import time
from pyside6_utils.utility.signal_blocker import SignalBlocker
import threading

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
	    	display_max_chars = 200_000,
		    ui_text_min_update_interval : float = 0.2
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
		self.ui.consoleTextEdit.verticalScrollBar().valueChanged.connect(self.onTextScrollBarMoved)
		# self.ui.fileSelectionTableView.viewport().mouseMoveEvent = self._on_mouse_move_in_treeview

		# self._has_queued_update = False #Whether a text-update is queued
		self._ui_text_min_update_interval = ui_text_min_update_interval #The minimum interval in seconds between updating the

		self._queued_text_lock = threading.Lock() #Lock for the queued text
		self._queued_text = None #The text that is queued to be updated
		self._queued_text_from_index = 0 #The index of the start of the new text according to the console-item
		self._last_queued_time = 0 #The last time the text was queued (if something goes wrong, after some time, we start new queue)
		self._last_text_update_time = 0 #The last time the text was updated

		self._target_console_text_index = 0 #The target index in the real buffer in the console-item
		self._first_char_index = 0 #The index of the first character in the textedit (in the "real" buffer in the console-item)
		self._updating_scrollbar_pos = False

		# self._prev_textedit_index = 0 #The previous target character relative to the text in the textedit



		self._cur_text = ""
		self._moving_scrollbar = False #If moving the scrollbar -> don't reset the value


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
			assert isinstance(item, BaseConsoleItem), "Item is not of type BaseConsoleItem"
			item.currentTextChanged.connect(self._on_selected_item_text_changed)
			self._current_text_connect = item.currentTextChanged
			self._on_selected_item_text_changed(item.get_current_text())

	def _on_selected_item_text_changed(self, newtext : str, from_index : int = 0):
		"""
		The function to be called when the text of the currently selected item changes.

		args:
			newtext (str): The new text of the item
			from_index (int | None): The index of the start of the new text according to the console-item. This allows
				us to stay at the same position in the text when updating, even when the queue-item only caches part
				of the text. If 0 - treat the text as if it is the "full" text.
		"""
		cur_time = time.time()
		if cur_time - self._last_text_update_time > self._ui_text_min_update_interval: #if time for update -> update
			self._process_text_changed(newtext, from_index)
			return
		else:
			#Start _queue_text in a new qthread (since it waits for a lock)
			QtCore.QTimer.singleShot( #Queue this function in a new thread
				0, lambda: self._queue_new_text(newtext, from_index, cur_time)
			)

	def _queue_new_text(self, newtext : str, from_index : int, cur_time):
		with self._queued_text_lock: #If not time for update -> queue (or update the to-be-updated text)
			# if self._queued_text is not None: #If there is already a queued text -> update it
			self._queued_text = newtext #Update the queued text
			self._queued_text_from_index = from_index
			if cur_time - self._last_queued_time < self._ui_text_min_update_interval * 2\
				or cur_time - self._last_text_update_time < self._ui_text_min_update_interval:
				#If last update didn't go wrong or update has taken place in mean time when getting lock, keep waiting
				return
			#If last update took to long, start a new timer
			self._last_queued_time = cur_time

			#Set 1-time timer to update the UI
			QtCore.QTimer.singleShot( #Convert update-interval to milliseconds and queue the update
				int(self._ui_text_min_update_interval*1000), lambda: self._update_queued_text
			)
			self._process_text_changed(newtext)
			# self._queued_text = None

	def _update_queued_text(self):
		"""Used icw a timer, updates the UI with the queued text"""
		with self._queued_text_lock:
			if self._queued_text is not None:
				if time.time() - self._last_text_update_time < self._ui_text_min_update_interval:
					#If a recent update has taken place in the mean time, don't update
					self._queued_text = None
					return
				self._process_text_changed(self._queued_text, self._queued_text_from_index)
				self._queued_text = None

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
			

	def _process_text_changed(self, new_text : str, from_index : int):
		"""
		Actually update the UI. This function is only called after taking into account cur_text_min_update_interval to
		make sure we don't overload the UI with too many updates.
		"""
		self._last_text_update_time = time.time()
		at_end = self.ui.consoleTextEdit.verticalScrollBar().value() == self.ui.consoleTextEdit.verticalScrollBar().maximum()
		

		
		if len(new_text) > self._display_max_chars:
			self._cur_text = new_text[-self._display_max_chars:]
		else:
			self._cur_text = new_text

		with SignalBlocker(self.ui.consoleTextEdit.verticalScrollBar()): #Block signals from the scrollbar when setting text
			self._updating_scrollbar_pos = True
			self.ui.consoleTextEdit.setPlainText(self._cur_text)
			self._updating_scrollbar_pos = False


		# new_first_char_index = from_index + (len(new_text) - self._display_max_chars)
		# shift = new_first_char_index - self._first_char_index
		self._first_char_index = from_index + ( max(0, len(new_text) - self._display_max_chars))

		#If cursor was at the end -> stay at the end
		if at_end:
			self._updating_scrollbar_pos = True
			self.ui.consoleTextEdit.verticalScrollBar().setValue(self.ui.consoleTextEdit.verticalScrollBar().maximum())
			self._updating_scrollbar_pos = False
		else:
			if self._target_console_text_index < self._first_char_index:
				self._updating_scrollbar_pos = True
				self.ui.consoleTextEdit.verticalScrollBar().setValue(0)
				self._updating_scrollbar_pos = False
				return #If target index < first char, just stay at the top

			if not self._moving_scrollbar:
				#Get the numbr of \n characters in self._cur_text before (from_index + self._cur_console_text_index)
				target_line = self._cur_text[:self._target_console_text_index - self._first_char_index].count("\n")
				self._updating_scrollbar_pos = True
				self.ui.consoleTextEdit.verticalScrollBar().setValue(target_line)
				self._updating_scrollbar_pos = False

	def onTextScrollBarMoved(self, value : int):
		"""Called when the scrollbar of the textedit is moved"""
		if self._updating_scrollbar_pos:
			return
		self._moving_scrollbar = True
		target_textedit_index = self._get_index_nth_occurence(self._cur_text, "\n", value)
		if target_textedit_index >= 0:
			self._target_console_text_index = self._first_char_index + target_textedit_index
			self._moving_scrollbar = False
			log.debug(f"Text scrollbar moved to line {value}, corresponding to index {target_textedit_index} = {self._target_console_text_index} !")
			return
		self._moving_scrollbar = False
		raise ValueError(f"Scrollbar moved to {value}, but no line found at that position")


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
	from pyside6_utils.models.console_widget_models.console_from_file_item import ConsoleFromFileItem
	import tempfile
	import threading
	log.info("Now running an example using console from file items, the console should print a number every second")
	temp_dir = tempfile.gettempdir()
	temp_file = tempfile.NamedTemporaryFile(dir=temp_dir, mode='w', delete=False, suffix=".txt") #Delete temporary
		# file afterwards

	app = QtWidgets.QApplication([])
	test_console_model = ConsoleModel()
	console_widget = ConsoleWidget(ui_text_min_update_interval=0.1)
	console_widget.set_model(test_console_model)


	class TestConsoleItem(BaseConsoleItem):
		def __init__(self, id):
			super().__init__()
			self._id = id
			self._text = ""

		def get_current_text(self) -> str:
			return self._text
		
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
		test_console_item._text = "\n".join([f"{i%10} "*100 for i in range(20_000)])
		for i in range(20000): #First test test-item
			test_console_item._text += f"Wrote line {i} to file {temp_file.name}\n"
			test_console_item.currentTextChanged.emit(test_console_item._text)
			time.sleep(0.2)

		for i in range(200000):
			temp_file.write(f"Wrote line {i} to file {temp_file.name}\n")
			temp_file.flush()
			time.sleep(0.1)
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