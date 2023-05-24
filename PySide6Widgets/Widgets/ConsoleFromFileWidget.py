
# from typing import List, Optional, Union
from PySide6 import QtCore, QtWidgets
# from logging.handlers import QueueHandler, QueueListener
from PySide6 import QtCore, QtWidgets, QtGui
import PySide6.QtCore
from PySide6Widgets.UI.ConsoleFromFileWidget_ui import Ui_ConsoleFromFileWidget
import os
import logging
log = logging.getLogger(__name__)
import typing
import time

class ConsoleFileSelectorWidgetDelegate(QtWidgets.QStyledItemDelegate):

	deleteHoverItem = QtCore.Signal(QtCore.QModelIndex) #Emitted index when the "delete" button is clicked on an item
	
	#Custom delegate that puts an x-button at the end of the first column of the file-selection treeview 
	#When this button is clicked, the file is deleted
	def __init__(self, parent : QtWidgets.QWidget = None) -> None:
		super().__init__(parent)
		# self._delete_button.setFixedSize(16, 16)

		#Get the icon size (normal)
		self.icon_size = QtWidgets.QApplication.style().pixelMetric(QtWidgets.QStyle.PM_LargeIconSize)

		#Create pixmap from ":/Icons/places/user-trash.png"
		self.trash_icon = QtWidgets.QApplication.style().standardIcon(QtWidgets.QStyle.SP_TitleBarCloseButton)
		# self.trash_icon_pixmap = QtWidgets.QStyle.SP_TitleBarMaxButton

		# self.trash_icon_pixmap = QtGui.QPixmap(":/Icons/places/user-trash.png")
		self.hovering_del_btn = False 
		

	def paint(self, painter : QtGui.QPainter, option : QtWidgets.QStyleOptionViewItem, index : QtCore.QModelIndex) -> None:
		#First draw the default item
		super().paint(painter, option, index)

		#Set icon size based on the height of the item
		self.icon_size = option.rect.height() - 10 #10 is the padding on both top and bottom

		if option.state & (QtWidgets.QStyle.State_MouseOver | (QtWidgets.QStyle.State_Selected)): #If mouse-over event is detected or part of selection #TODO: active? 
			painter.save()
			#Get the rect of the first column
			rect = option.rect
			icon_rect = QtCore.QRect(rect.right() - self.icon_size, rect.top() + (rect.height()-self.icon_size)/2, self.icon_size, self.icon_size)

			mouse_pos =  option.widget.mapFromGlobal(QtGui.QCursor.pos())
			if icon_rect.contains(mouse_pos):
				painter.fillRect(icon_rect, QtGui.QColor(0, 0, 0, 150))
			# if self.hovering_del_btn: #If hovering over -> create grey background
			# 	painter.fillRect(icon_rect, QtGui.QColor(0, 0, 0, 150))

			#Get the icon rect
			# icon_rect = QtCore.QRect(rect.right() - self.icon_size, rect.top(), self.icon_size, self.icon_size)
			#Draw the icon
			# painter.drawPixmap(icon_rect, self.trash_icon_pixmap)
			# painter.paint
			QtGui.QIcon.paint(self.trash_icon, painter, icon_rect, mode=QtGui.QIcon.Normal, state=QtGui.QIcon.On)


			#Restore the painter state
			painter.restore()


	def editorEvent(self, event : QtCore.QEvent, model : QtCore.QAbstractItemModel, option : QtWidgets.QStyleOptionViewItem, index : QtCore.QModelIndex) -> bool:
		p = event.position() #Local position
		globalPos = p.toPoint()

		#Check if the user clicked on the icon
		if event.type() == QtCore.QEvent.MouseButtonPress:
			#Get the rect of the first column
			rect = option.rect
			#Get the icon rect
			icon_rect = QtCore.QRect(rect.right() - self.icon_size, rect.top(), self.icon_size, self.icon_size)
			#Check if the mouse is inside the icon rect
			if icon_rect.contains(globalPos):
				#Emit the delete signal
				self.deleteHoverItem.emit(index)
				return True
		
		elif event.type() == QtCore.QEvent.MouseMove:
			#Get the rect of the first column
			rect = option.rect
			#Get the icon rect
			icon_rect = QtCore.QRect(rect.right() - self.icon_size, rect.top() + (rect.height()-self.icon_size)/2, self.icon_size, self.icon_size)
			#Check if the mouse is inside the icon rect
			if icon_rect.contains(globalPos):
				if self.hovering_del_btn == False: #Only update view if state changed	
					self.hovering_del_btn = True
					option.widget.viewport().update()
			elif self.hovering_del_btn:
				self.hovering_del_btn = False
				option.widget.viewport().update()

		return super().editorEvent(event, model, option, index)


class FileCheckerWorker(QtCore.QObject):
	"""A class that continuously checks a file path for changes in file size, if so, it emits a simple signal, indicating that the file has changed
	"""
	fileChanged = QtCore.Signal() #Emitted when the file has changed

	def __init__(self, path, polling_interval : float = 0.2, *args, **kwargs) -> None:
		super().__init__(*args, **kwargs)
		self._path = path
		self.run_flag = True #Keep track of whether the thread should keep running
		self._polling_interval = polling_interval #The interval in seconds to check the file for changes #TODO: make parameter
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

# class ConsoleItem(QtWidgets.QTableWidgetItem):
class ConsoleItem(QtCore.QObject):
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

# class ConsoleStandardItemModel(QtGui.QStandardItemModel):
class ConsoleStandardItemModel(QtCore.QAbstractItemModel):
	"""Small class to overload data-representation of the file-selection treeview based on recency
	and to add icons to the first column 

	NOTE: this model does not seem to work with treeviews, only tableviews
	"""
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self._console_pixmap = QtWidgets.QStyle.SP_TitleBarMaxButton
		self._console_icon = QtWidgets.QApplication.style().standardIcon(self._console_pixmap)
		self._item_list = [] #List of ConsoleStandardItem's

	def columnCount(self, parent : QtCore.QModelIndex = QtCore.QModelIndex()) -> int:
		return 3
	
	def removeRow(self, row: int, parent : QtCore.QModelIndex) -> bool:
		self.beginRemoveRows(parent, row, row)
		# self._item_list.pop(row)
		del self._item_list[row]
		self.endRemoveRows()
		self.modelReset.emit() #Why is this needed?

	def rowCount(self, parent : QtCore.QModelIndex = QtCore.QModelIndex()) -> int:
		if not parent.isValid(): #If model index is not valid -> top level item -> so all items
			return len(self._item_list)
		else:  #If one of the sub-items
			return 0 

	def addPath(self, name : str, path : str): 
		"""Add a path to the model to be displayed in the listview (name is the name of the file, path is the full path to the file)
		This class will then monitor the file as to update the last edit date in the listview 
		
		Args:
			name (str): The name of the file
			path (str): The full path to the file
		"""
		newitem = ConsoleItem(name, path)
		self.appendRow(newitem)

	def parent(self, index : QtCore.QModelIndex) -> QtCore.QModelIndex:
		if not index.isValid():
			return QtCore.QModelIndex()
		else:
			return self.createIndex(0, 0, None)


	def index(self, row : int, column : int, parent : QtCore.QModelIndex = QtCore.QModelIndex()) -> QtCore.QModelIndex:
		"""Return the index of the item in the model specified by the given row, column and parent index.
		
		Args:
			row (int): The row of the item
			column (int): The column of the item
			parent (QtCore.QModelIndex, optional): The parent index. Defaults to QtCore.QModelIndex().
		
		Returns:
			QtCore.QModelIndex: The index of the item
		"""
		if not parent.isValid(): #If top-level item (should be all items actually)
			return self.createIndex(row, column, self._item_list[row])
		else: #If item -> no children
			return QtCore.QModelIndex()



	def appendRow(self, item : ConsoleItem):
		"""Append a row to the model - consisting of a single ConsoleStandardItem
		
		"""
		self.beginInsertRows(QtCore.QModelIndex(), self.rowCount(), self.rowCount())
		self._item_list.append(item)
		item.emitDataChanged.connect(lambda *_ : self.dataChanged.emit(self.index(self.rowCount()-1, 0), self.index(self.rowCount()-1, 2)))
		
		self.endInsertRows()

	def addItem (self, item : ConsoleItem):
		"""Add an item to the model
		
		Args:
			item (ConsoleStandardItem): The item to add
		"""
		self.appendRow(item)

	#Overload the data method to return bold text if changes have been made in the past x seconds
	def data(self, index : QtCore.QModelIndex, role : int = QtCore.Qt.DisplayRole):
		#Check if index is valid
		if not index.isValid(): #if index is not valid, return None
			return None

		#Get the item from the index
		item = index.internalPointer()
		
		if role == QtCore.Qt.DisplayRole or role == QtCore.Qt.EditRole:
			return item.data(index.column()) #Return the data (str) of the item
		elif role == QtCore.Qt.DecorationRole:
			return self._console_icon
		elif role == QtCore.Qt.UserRole + 1:
			return item
		else:
			return None
		# return super().data(index, role)


class ConsoleFromFileWidget(QtWidgets.QWidget):
	DESCRIPTION = "Widget that displays dynamically displays the text contents of a file - watches the selected file for changes and updates the widget accordingly. Mainly intended for use with a file to which stdout/stderr can be redirected to."

	def __init__(self, parent: typing.Optional[QtWidgets.QWidget] = None, display_max_chars = 200_000) -> None:
		"""
		Args:
			parent (QtCore.QObject, optional): The parent. Defaults to None.
			name_date_path_model (QtCore.QStandardItemModel): The table model that contains the <name>, <last edit date> and <path> of the file in column 1, 2 and 3 respectively
		"""
		super().__init__(parent)
		self.ui = Ui_ConsoleFromFileWidget()
		self.ui.setupUi(self)

		self._display_max_chars = display_max_chars #The maximum number of characters to display in the text edit

		self._files_proxy_model = QtCore.QSortFilterProxyModel()
		# self._files_proxy_model.setSourceModel(name_date_path_model)
		self.ui.fileSelectionTableView.setModel(self._files_proxy_model)
		# self.ui.fileSelectionTableView.setSortingEnabled(True)

		#==============Treeview ==============
		self.ui.fileSelectionTableView.sortByColumn(1, QtCore.Qt.DescendingOrder) #Sort by date in descending order
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
		self.ui.fileSelectionTableView.setFrameShape(QtWidgets.QFrame.NoFrame)
		self.ui.fileSelectionTableView.setShowGrid(False)

		#Make it so tableview fills the entire widget
		# self.ui.fileSelectionTableView.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
		self.ui.fileSelectionTableView.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)
		# self.ui.fileSelectionTableView.header().hide()
		# self.ui.fileSelectionTableView.selectionModel().selectionChanged.connect(self._on_file_selection_changed)

		self.setConsoleWidthPercentage(50)
		#============Textedit==================
		#Set editable to false
		self.ui.consoleTextEdit.setReadOnly(True)

		#Make tree view non-editable
		self.ui.fileSelectionTableView.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
		self.ui.fileSelectionTableView.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
		
		#Set the delegate for the first column to the custom delegate
		self.fileSelectionDelegate = ConsoleFileSelectorWidgetDelegate(self.ui.fileSelectionTableView)
		self.ui.fileSelectionTableView.setItemDelegateForColumn(0, self.fileSelectionDelegate)
		self.fileSelectionDelegate.deleteHoverItem.connect(self.deleteFileSelectorHoverItem)
		
		#Align contents bottom
		# self._current_file_watcher : QtCore.QFileSystemWatcher = QtCore.QFileSystemWatcher()
		# self._current_file_watcher.fileChanged.connect(self._on_content_changes_selected_file)
		# self._current_file_path : str = None
		# self._current_seek : int = 0 #The current seek position in the current file

		# self.ui.consoleTextEdit.
		self._current_text_connect = None
		#When moving mouse in fileSelectionTableView, update the currently hovered item
		# self.ui.fileSelectionTableView.viewport().installEventFilter(self)
		self.ui.fileSelectionTableView.viewport().setMouseTracking(True)

		self.ui.fileSelectionTableView.selectionModel().selectionChanged.connect(self.selectionChanged)
		# self.ui.fileSelectionTableView.viewport().mouseMoveEvent = self._on_mouse_move_in_treeview
	
	def selectionChanged(self, selection : PySide6.QtCore.QItemSelection):
		if self._current_text_connect is not None: #If selection changed -> stop subscribing to the old item
			self._current_text_connect.disconnect()
			self._current_text_connect = None
		
		if len(selection.indexes()) == 0:
			self.ui.consoleTextEdit.setPlainText("")
			return
		elif selection.indexes()[0].isValid():
			index = selection.indexes()[0]
			item = self._files_proxy_model.data(index, role = QtCore.Qt.UserRole + 1)
			# test = self._files_proxy_model.data(index)
			item.currentTextChanged.connect(self._on_current_text_changed)
			self._current_text_connect = item.currentTextChanged
			# self.ui.consoleTextEdit.setPlainText(item.getCurrentText())

			self._on_current_text_changed(item.getCurrentText())
			# self._on_current_text_changed(item.getCurrentText())

	def _on_current_text_changed(self, newtext : str):
		if len(newtext) > self._display_max_chars:
			newtext = newtext[-self._display_max_chars:]

		self.ui.consoleTextEdit.setPlainText(newtext[-self._display_max_chars:])
		self.ui.consoleTextEdit.moveCursor(QtGui.QTextCursor.End) #Move the cursor to the end of the text edit
		self.ui.consoleTextEdit.verticalScrollBar().setValue(self.ui.consoleTextEdit.verticalScrollBar().maximum())


	def deleteFileSelectorHoverItem(self, index : QtCore.QModelIndex):
		#Remove the row from the model
		# print("Trying to remove row")
		original_index = self._files_proxy_model.mapToSource(index)
		#Check if that index is the currently selected index
		self._files_proxy_model.sourceModel().removeRow(original_index.row(), original_index.parent())

	@staticmethod
	def get_file_name_path_dict_in_edit_order(path : str, only_extensions : list = None):
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


	def _on_selected_path_change(self, new_path : str):
		raise NotImplementedError()
		# if new_path is None:
		# 	self.ui.consoleTextEdit.clear()
		# 	return
		# if new_path == self._current_file_path: #Skip if no change
		# 	return
		# if self._current_file_path is not None:
		# 	self._current_file_watcher.removePath(self._current_file_path) #Remove the old path from the watcher
		# log.debug(f"New path: {new_path}")

		# self._current_file_path = new_path
		# self._current_file_watcher.addPath(new_path) #Add the new path to the watcher
		# self.ui.consoleTextEdit.clear() #Clear the text edit
		# #Open file and read completely
		# with open(new_path, "r") as f:
		# 	self.ui.consoleTextEdit.insertPlainText(f.read())
		# 	self.ui.consoleTextEdit.moveCursor(QtGui.QTextCursor.End) #Move the cursor to the end of the text edit
		# 	self._current_seek = f.tell() #Set the current seek position to end of what was read
			
		# #Scroll all the way to the bottom
		# self.ui.consoleTextEdit.verticalScrollBar().setValue(self.ui.consoleTextEdit.verticalScrollBar().maximum())

	def setModel(self, model : QtCore.QAbstractTableModel):
		self._files_proxy_model.setSourceModel(model)
		self.ui.fileSelectionTableView.hideColumn(1) 
		self.ui.fileSelectionTableView.hideColumn(2)

		
	def consoleWidthPercentage(self) -> int:
		if self.ui.splitter.sizes()[0] == 0:
			return 0
		elif self.ui.splitter.sizes()[1] == 0:
			return 100

		return int(self.ui.splitter.sizes()[0]/(self.ui.splitter.sizes()[1] + self.ui.splitter.sizes()[0]) * 100)
	
	def setConsoleWidthPercentage(self, percentage : int) -> None:
		percentage = max(1, min(100, percentage))
		self.ui.splitter.setSizes([ 10*percentage, 10*(100-percentage)])
		self.ui.splitter.setStretchFactor(0, percentage)
		self.ui.splitter.setStretchFactor(1, 100-percentage)
		
	ConsoleWidthPercentage = QtCore.Property(int, consoleWidthPercentage, setConsoleWidthPercentage)




if __name__ == "__main__":
	app = QtWidgets.QApplication([])
	ConsoleModel = ConsoleStandardItemModel()
	# newitem = QtGui.QStandardItem()
	# newitem.setData(QtCore.QDateTime.currentDateTime(), QtCore.Qt.DisplayRole)

	# ConsoleModel.appendRow([
	# 	QtGui.QStandardItem("file1"),
	# 	newitem,
	# 	QtGui.QStandardItem(r"C:\Users\user\Documents\radial_drilling\test1.txt")
	# ])
	# ConsoleModel.appendRow([
	# 	QtGui.QStandardItem("file2"),
	# 	newitem,
	# 	QtGui.QStandardItem(r"C:\Users\user\Documents\radial_drilling\test2.txt")
	# ])
	# ConsoleModel.appendRow(
	# 	ConsoleItem("file1", r"C:\Users\user\Documents\radial_drilling\test1.txt")
	# )
	# ConsoleModel.appendRow(
	# 	ConsoleItem("file2", r"C:\Users\user\Documents\radial_drilling\test2.txt")
	# )	
	# ConsoleModel.appendRow(
	# 	ConsoleItem("file3", r"C:\Users\user\Documents\radial_drilling\test2.txt")
	# )

	ConsoleModel.addPath("file1", r"C:\Users\user\Documents\radial_drilling\test1.txt")
	ConsoleModel.addPath("file2", r"C:\Users\user\Documents\radial_drilling\test2.txt")

	# defaulttableview = QtWidgets.QTreeView()
	# # defaulttableview = QtWidgets.QTableView()
	# proxy_model = QtCore.QSortFilterProxyModel()
	# proxy_model.setSourceModel(ConsoleModel)
	# defaulttableview.setModel(ConsoleModel)
	# defaulttableview.setSortingEnabled(True)
	# # defaulttableview.setModel(ConsoleModel)
	# defaulttableview.show()


	console_widget = ConsoleFromFileWidget()
	console_widget.setModel(ConsoleModel)
	window = QtWidgets.QMainWindow()
	#Set size to 1000
	window.resize(1200, 500)
	console_widget.setConsoleWidthPercentage(20)

	# console_widget.fileSelectionDelegate.deleteHoverItem.connect(lambda index: ConsoleModel.removeRow(index.row()))

	layout = QtWidgets.QVBoxLayout()
	layout.addWidget(console_widget)

	dockable_window = QtWidgets.QDockWidget("Console", window)
	dockable_window.setWidget(console_widget)
	# dockable_window.setWidget(defaulttableview)
	
	console_widget.setConsoleWidthPercentage(20)

	window.setCentralWidget(dockable_window)
	window.show()
	app.exec()


