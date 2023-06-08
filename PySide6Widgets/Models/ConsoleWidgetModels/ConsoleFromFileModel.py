
from PySide6 import QtCore, QtGui, QtWidgets
import os
import time

class FileCheckerWorker(QtCore.QObject):
	"""A class that continuously checks a file path for changes in file size, if so, it emits a simple signal, 
	indicating that the file has changed
	"""
	fileChanged = QtCore.Signal() #Emitted when the file has changed

	def __init__(self, path, polling_interval : float = 0.2, *args, **kwargs) -> None:
		super().__init__(*args, **kwargs)
		self._path = path
		self.run_flag = True #Keep track of whether the thread should keep running
		self._polling_interval = polling_interval #The interval in seconds to check the file for changes 
			#TODO: make parameter
		self._last_size = 0

	def doWork(self):
		self._last_size = -1 #File doesnt exist
		while(self.run_flag):
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


class FileConsoleItem(QtCore.QObject):
	currentTextChanged = QtCore.Signal(str) #Emitted when the text in the file changes
	emitDataChanged = QtCore.Signal() #Emitted when the data of the item changes

	def __init__(self, name : str, path : str = None, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self._console_pixmap = QtWidgets.QStyle.SP_TitleBarMaxButton
		self._console_icon = QtWidgets.QApplication.style().standardIcon(self._console_pixmap)

		self._name = name
		self._path = path

		self._current_text : str = "" #The current text in the file
		self._last_edited = QtCore.QDateTime.fromSecsSinceEpoch(0) #Set to 0 so that it is always updated on first change
		self._current_seek : int = 0 #The current seek position in the current file


		#Check if file exists
		if self._path is None or not os.path.exists(self._path):
			raise ValueError(f"File {self._path} does not exist - Console Item will not be able to initiate a file-watcher so updates will not be shown.")

		# class FileWatcherHandler(watchdog.events.FileSystemEventHandler):
		# 	def __init__(self, item : ConsoleItem):
		# 		super().__init__()
		# 		self.item = item

		# 	def on_modified(self, event):
		# 		# print(f'event type: {event.event_type}  path : {event.src_path}')
		# 		if event.src_path == self.item._path:
		# 		# print("kaas")
		# 			self.item._on_content_changes_selected_file()

		#Align contents bottom
		# self._file_watcher = watchdog.observers.Observer()
		self._polling_interval = 0.2 #The interval in seconds to poll the file for changes #TODO: make parameter

		# self._file_watcher : QtCore.QFileSystemWatcher = QtCore.QFileSystemWatcher()
		# self._file_watcher.fileChanged.connect(self._on_content_changes_selected_file)
		# self._file_watcher.addPath(self._path)
		self._current_seek : int = 0 #The current seek position in the current file
		self._on_content_changes_selected_file() #Call this method once to get the initial text
		# self._file_monitor_thread = threading.Thread(target = self.fileCheckerWorker) #TODO: move to separate class so that the thread can be stopped when the item is deleted
		# self._file_monitor_thread.start()

		self._file_monitor_worker = FileCheckerWorker(self._path)
		self._worker_thread = QtCore.QThread()
		self._worker_thread.started.connect(self._file_monitor_worker.doWork)
		self._file_monitor_worker.moveToThread(self._worker_thread)
		#Connect deleteLater to the finished signal of the thread
		# self._worker_thread.finished.connect(self._file_monitor_worker.deleteLater)
		self._file_monitor_worker.fileChanged.connect(self._on_content_changes_selected_file)
		#Connect doWork to the started signal of the thread
		self._worker_thread.start()



	#IF class is destroyed, stop the file watcher
	# def __del__(self):
	# 	self._worker_thread.run_flag = False
	# 	self._worker_thread.quit()


	# def fileCheckerWorker(self) -> None:
	# 	while(True):
	# 		time.sleep(self._polling_interval)
	# 		self._on_content_changes_selected_file()

	def getCurrentText(self) -> str:
		return self._current_text


	def data(self, role : int = 0):
		if role == 0 : return self._name
		elif role == 1 : return self._last_edited
		elif role == 2 : return self._path
		raise ValueError(f"Invalid role for ConsoleStandardItem: {role}")
		# return super().data(role)
	
	def _on_content_changes_selected_file(self) -> None:
		"""
		When the contents of selected file changes, this method is called
		"""

		if not os.path.exists(self._path): #If file does not exist, clear the text edit
			self._current_text = ""
			self._current_seek = 0
			self.currentTextChanged.emit("")
			return
		
		cur_size = os.path.getsize(self._path)

		#First check is size is lower than the current seek position, if so, reset the seek position
		if cur_size < self._current_seek:
			# self.ui.consoleTextEdit.clear() #Also clear the text edit
			self._current_seek = 0
			self._current_text = "" #Reset the current text
		
		if cur_size <= self._current_seek: #If file size is equal to the current seek position, do nothing
			return

		#Open the file and seek to the current seek position
		with open(self._path, "r") as f:
			f.seek(self._current_seek)
			newcontent = f.read()  #Read to end of file
			self._current_seek = f.tell() #Make the current seek position the end of the file
			self._current_text += newcontent #Add the new content to the current text
			# self.ui.consoleTextEdit.insertPlainText(newcontent) #Insert the new content into the text edit
			# self.ui.consoleTextEdit.moveCursor(QtGui.QTextCursor.End) #Move the cursor to the end of the text edit

		#Retrieve the last edit date
		time = os.path.getmtime(self._path)
		# self._last_edited = QtCore.QDateTime.fromSecsSinceEpoch(time
		self._last_edited = time
		# self.emitDataChanged.emit() #Emit the data changed signal (as self._last_edited has changed)
		# print("New file contents for file ", self._path)
		self.currentTextChanged.emit(self._current_text) #Emit the current text