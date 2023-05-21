
from PySide6 import QtCore, QtWidgets
from logging.handlers import QueueHandler, QueueListener
from PySide6 import QtCore, QtWidgets, QtGui
from PySide6Widgets.UI.ConsoleFromFileWidget_ui import Ui_ConsoleFromFileWidget
import os
import logging
log = logging.getLogger(__name__)
import typing
import app_resources_rc


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
		self.trash_icon_pixmap = QtWidgets.QApplication.style().standardPixmap(QtWidgets.QStyle.SP_DialogCancelButton)

		# self.greyed_out_trash_icon_pixmap = QtGui.QPixmap(self.trash_icon_pixmap.size())
		# painter = QtGui.QPainter(self.greyed_out_trash_icon_pixmap)
		# painter.setOpacity(0.5)
		# painter.drawPixmap(self.greyed_out_trash_icon_pixmap.rect(), self.trash_icon_pixmap)
		# painter.end()


		# self.trash_icon_pixmap = QtGui.QPixmap(":/Icons/places/user-trash.png")
		self.hovering_del_btn = False 
		

	def paint(self, painter : QtGui.QPainter, option : QtWidgets.QStyleOptionViewItem, index : QtCore.QModelIndex) -> None:
		#First draw the default item
		super().paint(painter, option, index)

		#Set icon size based on the height of the item
		self.icon_size = option.rect.height()

		if option.state & QtWidgets.QStyle.State_MouseOver: #If mouse-over event is detected
			painter.save()
			#Get the rect of the first column
			rect = option.rect
			icon_rect = QtCore.QRect(rect.right() - self.icon_size, rect.top(), self.icon_size, self.icon_size)

			if self.hovering_del_btn: #If hovering over -> create grey background
				painter.fillRect(icon_rect, QtGui.QColor(0, 0, 0, 150))

			#Get the icon rect
			icon_rect = QtCore.QRect(rect.right() - self.icon_size, rect.top(), self.icon_size, self.icon_size)
			#Draw the icon
			painter.drawPixmap(icon_rect, self.trash_icon_pixmap)

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
			icon_rect = QtCore.QRect(rect.right() - self.icon_size, rect.top(), self.icon_size, self.icon_size)
			#Check if the mouse is inside the icon rect
			if icon_rect.contains(globalPos):
				if self.hovering_del_btn == False: #Only update view if state changed	
					self.hovering_del_btn = True
					option.widget.viewport().update()
			elif self.hovering_del_btn:
				self.hovering_del_btn = False
				option.widget.viewport().update()

		return super().editorEvent(event, model, option, index)




class ConsoleStandardItemModel(QtGui.QStandardItemModel):
	"""Small class to overload data-representation of the file-selection treeview based on recency
	and to add icons to the first column
	"""
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self._console_pixmap = QtWidgets.QStyle.SP_TitleBarMaxButton
		self._console_icon = QtWidgets.QApplication.style().standardIcon(self._console_pixmap)


	#Overload the data method to return bold text if changes have been made in the past x seconds
	def data(self, index : QtCore.QModelIndex, role : int = QtCore.Qt.DisplayRole):
		#Check if index is valid
		if not index.isValid():
			return None

		if role == QtCore.Qt.FontRole:
			if index.column() == 0:
				date = self.index(index.row(), 1) 
				if date.data(QtCore.Qt.DisplayRole) > QtCore.QDateTime.currentDateTime().addSecs(-10):
					font = QtGui.QFont()
					font.setBold(True)
					return font
		#Icon role
		elif role == QtCore.Qt.DecorationRole:
			return self._console_icon
		return super().data(index, role)


class ConsoleFromFileWidget(QtWidgets.QWidget):
	DESCRIPTION = "Widget that displays dynamically displays the text contents of a file - watches the selected file for changes and updates the widget accordingly. Mainly intended for use with a file to which stdout/stderr can be redirected to."

	def __init__(self, parent: typing.Optional[QtWidgets.QWidget] = None, name_date_path_model : QtCore.QAbstractTableModel = None) -> None:
		"""
		Args:
			parent (QtCore.QObject, optional): The parent. Defaults to None.
			name_date_path_model (QtCore.QStandardItemModel): The table model that contains the <name>, <last edit date> and <path> of the file in column 1, 2 and 3 respectively
		"""
		super().__init__(parent)
		self.ui = Ui_ConsoleFromFileWidget()
		self.ui.setupUi(self)

		self._files_proxy_model = QtCore.QSortFilterProxyModel()
		self.ui.fileSelectionTreeView.setModel(self._files_proxy_model)
		self.ui.fileSelectionTreeView.setSortingEnabled(True)
		self._files_proxy_model.setSourceModel(name_date_path_model)

		#==============Treeview ==============
		self.ui.fileSelectionTreeView.sortByColumn(1, QtCore.Qt.DescendingOrder) #Sort by date in descending order
		#Hide the third column (path) and the second column (date) from the view
		self.ui.fileSelectionTreeView.hideColumn(1) 
		self.ui.fileSelectionTreeView.hideColumn(2)
		#Hide headers
		self.ui.fileSelectionTreeView.header().hide()
		self.ui.fileSelectionTreeView.selectionModel().selectionChanged.connect(self._on_file_selection_changed)

		self.setConsoleWidthPercentage(50)
		#============Textedit==================
		#Set editable to false
		self.ui.consoleTextEdit.setReadOnly(True)

		#Make tree view non-editable
		self.ui.fileSelectionTreeView.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
		self.ui.fileSelectionTreeView.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
		
		#Set the delegate for the first column to the custom delegate
		self.fileSelectionDelegate = ConsoleFileSelectorWidgetDelegate(self.ui.fileSelectionTreeView)
		self.ui.fileSelectionTreeView.setItemDelegateForColumn(0, self.fileSelectionDelegate)
		self.fileSelectionDelegate.deleteHoverItem.connect(self.deleteFileSelectorHoverItem)
		
		#Align contents bottom
		self._current_file_watcher : QtCore.QFileSystemWatcher = QtCore.QFileSystemWatcher()
		self._current_file_watcher.fileChanged.connect(self._on_content_changes_selected_file)
		self._current_file_path : str = None
		self._current_seek : int = 0 #The current seek position in the current file


		#When moving mouse in fileSelectionTreeView, update the currently hovered item
		# self.ui.fileSelectionTreeView.viewport().installEventFilter(self)
		self.ui.fileSelectionTreeView.viewport().setMouseTracking(True)
		# self.ui.fileSelectionTreeView.viewport().mouseMoveEvent = self._on_mouse_move_in_treeview
	# def _on_mouse_move_in_treeview():
	# 	print("kaas")

	def deleteFileSelectorHoverItem(self, index : QtCore.QModelIndex):
		# #Get the path from the third column
		# path = self._files_proxy_model.data(self._files_proxy_model.index(index.row(), 2), QtCore.Qt.DisplayRole)
		#Remove the row from the model
		self._files_proxy_model.removeRow(index.row())

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

	def _on_content_changes_selected_file(self) -> None:
		"""
		When the contents of selected file changes, this method is called
		"""
		log.debug("Content changes")

		#First check is size is lower than the current seek position, if so, reset the seek position
		if os.path.getsize(self._current_file_path) < self._current_seek:
			self.ui.consoleTextEdit.clear() #Also clear the text edit
			self._current_seek = 0
		
		#Open the file and seek to the current seek position
		with open(self._current_file_path, "r") as f:
			f.seek(self._current_seek)
			newcontent = f.read()  #Read to end of file
			self._current_seek = f.tell() #Make the current seek position the end of the file
			self.ui.consoleTextEdit.insertPlainText(newcontent) #Insert the new content into the text edit
			self.ui.consoleTextEdit.moveCursor(QtGui.QTextCursor.End) #Move the cursor to the end of the text edit

	def _on_selected_path_change(self, new_path : str):
		if new_path == self._current_file_path: #Skip if no change
			return
		if self._current_file_path is not None:
			self._current_file_watcher.removePath(self._current_file_path) #Remove the old path from the watcher
		log.debug(f"New path: {new_path}")

		self._current_file_path = new_path
		self._current_file_watcher.addPath(new_path) #Add the new path to the watcher
		self.ui.consoleTextEdit.clear() #Clear the text edit
		#Open file and read completely
		with open(new_path, "r") as f:
			self.ui.consoleTextEdit.insertPlainText(f.read())
			self.ui.consoleTextEdit.moveCursor(QtGui.QTextCursor.End) #Move the cursor to the end of the text edit
			self._current_seek = f.tell() #Set the current seek position to end of what was read
			
		#Scroll all the way to the bottom
		self.ui.consoleTextEdit.verticalScrollBar().setValue(self.ui.consoleTextEdit.verticalScrollBar().maximum())


	def _on_file_selection_changed(self, selected : QtCore.QItemSelection, deselected : QtCore.QItemSelection):
		if len(selected.indexes()) == 0 or not selected.indexes()[0].isValid():
			# self._on_selected_path_change(None)
			return
		
		index = selected.indexes()[0]
		#Get path from thrid column
		path = self._files_proxy_model.data(self._files_proxy_model.index(index.row(), 2), QtCore.Qt.DisplayRole)
		self._on_selected_path_change(path)

	def setModel(self, model : QtCore.QAbstractTableModel):
		self._files_proxy_model.setSourceModel(model)

		
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
	newitem = QtGui.QStandardItem()
	newitem.setData(QtCore.QDateTime.currentDateTime(), QtCore.Qt.DisplayRole)

	ConsoleModel.appendRow([
		QtGui.QStandardItem("file1"),
		newitem,
		QtGui.QStandardItem(r"C:\Users\user\Documents\radial_drilling\test1.txt")
	])
	ConsoleModel.appendRow([
		QtGui.QStandardItem("file2"),
		newitem,
		QtGui.QStandardItem(r"C:\Users\user\Documents\radial_drilling\test2.txt")
	])


	console_widget = ConsoleFromFileWidget(name_date_path_model=ConsoleModel)
	window = QtWidgets.QMainWindow()
	#Set size to 1000
	window.resize(1200, 500)
	console_widget.setConsoleWidthPercentage(20)

	# console_widget.fileSelectionDelegate.deleteHoverItem.connect(lambda index: ConsoleModel.removeRow(index.row()))

	layout = QtWidgets.QVBoxLayout()
	layout.addWidget(console_widget)

	dockable_window = QtWidgets.QDockWidget("Console", window)
	dockable_window.setWidget(console_widget)
	
	console_widget.setConsoleWidthPercentage(20)

	window.setCentralWidget(dockable_window)
	window.show()
	app.exec()


