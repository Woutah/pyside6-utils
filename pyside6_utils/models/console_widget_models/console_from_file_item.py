"""Implements the model needed to sync to a file and dynamically display the contents to a widget"""
import os
import time
import typing

from PySide6 import QtCore, QtWidgets

from pyside6_utils.models.console_widget_models.console_model import \
    BaseConsoleItem


class FileCheckerWorker(QtCore.QObject):
	"""A class that continuously checks a file path for changes in file size, if so, it emits a simple signal,
	indicating that the file has changed, used by ConsoleFromFileItem to check for changes in the file.

	TODO: file polling might not be the best approach, especially when using multiple files.
	"""
	fileChanged = QtCore.Signal() #Emitted when the file has changed

	def __init__(self, path, polling_interval : float = 0.2, *args, **kwargs) -> None: #pylint: disable=W1113
		super().__init__(*args, **kwargs)
		self._path = path
		self.run_flag = True #Keep track of whether the thread should keep running
		self._polling_interval = polling_interval #The interval in seconds to check the file for changes
			#TODO: make parameter
		self._last_size = 0

	def do_work(self):
		"""Continuously check the file for changes in size, if so, emit the fileChanged signal."""
		self._last_size = -1 #File doesnt exist
		while self.run_flag:
			time.sleep(self._polling_interval)

			if not os.path.exists(self._path): #If file does not exist, clear the text edit
				if self._last_size != -1:
					self._last_size = -1
					self.fileChanged.emit()
				continue

			cur_size = os.path.getsize(self._path)

			if cur_size != self._last_size:
				self._last_size = cur_size
				self.fileChanged.emit()


class ConsoleFromFileItem(BaseConsoleItem):
	"""An item that represents a single row in the console widget.
	Continually monitors the passed path for changes, and emits the current text when the file changes.
	E.g. we can monitor the output of a running program by calling:
	sys.stdout = LoggerWriter(log.info)
	Inside of a running process. Where LoggerWriter is an object that outputs to a file monitored by a ConsoleFromFileItem.
	
	TODO: file polling might not be the best approach, especially when using a lot of files.
	"""
	loadedLinesChanged = QtCore.Signal(list, int) #Emits all lines that have been changed, together with the line-index 
	emitDataChanged = QtCore.Signal() #Emitted when the data of the item changes

	def __init__(self, name : str, path : str, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self._console_pixmap = QtWidgets.QStyle.StandardPixmap.SP_TitleBarMaxButton
		self._console_icon = QtWidgets.QApplication.style().standardIcon(self._console_pixmap)

		self._name = name
		self._path = path

		# self._current_text : str = "" #The current text in the file #TODO: probably list of lines works better...
		self._current_line_list : list[str] = [] #List of lines
		self._cur_lines = [0, 0] #What lines are currently loaded
		self._last_edited = QtCore.QDateTime.fromSecsSinceEpoch(0) #Set to 0 so that it is always updated on first change
		self._current_seek : int = 0 #The current seek position in the current file


		#Check if file exists
		if self._path is None or not os.path.exists(self._path):
			raise ValueError(f"File {self._path} does not exist - Console Item will not be able to initiate a"
		    	"file-watcher so updates will not be shown.")


		#Align contents bottom
		self._polling_interval = 0.2 #The interval in seconds to poll the file for changes #TODO: make parameter

		self._current_seek : int = 0 #The current seek position in the current file
		self._on_content_changes_selected_file() #Call this method once to get the initial text

		self._file_monitor_worker = FileCheckerWorker(self._path)
		self._worker_thread = QtCore.QThread()
		self._worker_thread.started.connect(self._file_monitor_worker.do_work)
		self._file_monitor_worker.moveToThread(self._worker_thread)
		#Connect deleteLater to the finished signal of the thread
		self._file_monitor_worker.fileChanged.connect(self._on_content_changes_selected_file)

		#Connect doWork to the started signal of the thread
		self._worker_thread.start()


	def get_current_line_list(self) -> tuple[list[str], int]:
		"""Retrieves the current text in the watched file - as currently known to the item.
		ICW the start-index of this buffer. When the full file is loaded, this will be 0.
		"""
		# return self._current_text, 0 #TODO: No limit implemented yet
		return self._current_line_list, self._cur_lines[0]


	def data(self, role : QtCore.Qt.ItemDataRole, column : int = 0):
		"""Retrieve the data for the given role for this item."""
		if column == 0 :
			return self._name
		elif column == 1 :
			return self._last_edited
		elif column == 2 :
			return self._path
		raise ValueError(f"Invalid role for ConsoleStandardItem: {role}")
		# return super().data(role)

	def _on_content_changes_selected_file(self, encoding="utf-8") -> None:
		"""
		When the contents of selected file changes, this method is called
		"""

		if not os.path.exists(self._path): #If file does not exist, clear the text edit
			self._current_line_list = []
			self._current_seek = 0
			self.loadedLinesChanged.emit([], 0)
			return

		cur_size = os.path.getsize(self._path)

		#First check is size is lower than the current seek position, if so, reset the seek position (assume file reset)
		if cur_size < self._current_seek:
			# self.ui.consoleTextEdit.clear() #Also clear the text edit
			self._current_seek = 0
			self._current_text = "" #Reset the current text

		if cur_size <= self._current_seek: #If file size is equal to the current seek position, do nothing
			return

		cur_line = len(self._current_line_list)+1 #Get the current line number
		new_line_list : typing.List[str]= [] #List of new lines

		#Open the file and seek to the current seek position
		with open(self._path, "r", encoding=encoding) as in_file:
			in_file.seek(self._current_seek)
			if len(self._current_line_list) > 0 and not self._current_line_list[-1].endswith("\n"): #TODO os.linesep?
				self._current_line_list[-1] += in_file.readline()
				new_line_list.append(self._current_line_list[-1])
				cur_line -= 1 #Also update the last line number
			for line in in_file: #Read the new lines #TODO: maybe make a bit more efficient?
				self._current_line_list.append(line)
				new_line_list.append(line)
			self._current_seek = in_file.tell() #Make the current seek position the end of the file

		#Retrieve the last edit date
		self._last_edited = os.path.getmtime(self._path)
		# self.currentTextChanged.emit(self._current_text, 0) #Emit the current text
		self.loadedLinesChanged.emit(new_line_list, cur_line) #Emit the current text
