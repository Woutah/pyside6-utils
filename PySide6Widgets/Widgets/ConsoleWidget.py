"""
Implements a widget that combines a console-view and a tree-like-view so we're able to browse console outputs.
"""
import logging
import os
from abc import ABC, abstractmethod

from PySide6 import QtCore, QtGui, QtWidgets

from PySide6Widgets.Models.ExtendedSortFilterProxyModel import \
    ExtendedSortFilterProxyModel
from PySide6Widgets.UI.ConsoleFromFileWidget_ui import Ui_ConsoleFromFileWidget

log = logging.getLogger(__name__)
import typing


class ConsoleWidgetDelegate(QtWidgets.QStyledItemDelegate):
	"""Custom delegate that implements an "x" button
	"""

	deleteHoverItem = QtCore.Signal(QtCore.QModelIndex) #Emitted index when the "delete" button is clicked on an item

	#Custom delegate that puts an x-button at the end of the first column of the file-selection treeview
	#When this button is clicked, the file is deleted
	def __init__(self, parent : QtWidgets.QWidget | None = None) -> None:
		super().__init__(parent)
		# self._delete_button.setFixedSize(16, 16)

		#Get the icon size (normal)
		self.icon_size = QtWidgets.QApplication.style().pixelMetric(QtWidgets.QStyle.PixelMetric.PM_LargeIconSize)

		#Create pixmap from ":/Icons/places/user-trash.png"
		self.trash_icon = QtWidgets.QApplication.style().standardIcon(
			QtWidgets.QStyle.StandardPixmap.SP_TitleBarCloseButton)

		# self.trash_icon_pixmap = QtGui.QPixmap(":/Icons/places/user-trash.png")
		self.hovering_del_btn = False


	def paint(self,
	   		painter : QtGui.QPainter,
			option : QtWidgets.QStyleOptionViewItem, #TODO: typehinting not working? rect, state and widget not found
			index : QtCore.QModelIndex | QtCore.QPersistentModelIndex
		) -> None:
		#First draw the default item
		super().paint(painter, option, index)

		option_state : QtWidgets.QStyle.StateFlag = option.state #type: ignore
		option_rect : QtCore.QRect = option.rect #type: ignore

		#Set icon size based on the height of the item
		self.icon_size = option_rect.height() - 10 #10 is the padding on both top and bottom

		if option_state & \
				(QtWidgets.QStyle.StateFlag.State_MouseOver | (QtWidgets.QStyle.StateFlag.State_Selected)):
				#If mouse-over event is detected or part of selection #TODO: active?
			painter.save()
			#Get the rect of the first column
			icon_rect = QtCore.QRect(
				option_rect.right() - self.icon_size,
				option_rect.top() + (option_rect.height()-self.icon_size)//2,
			    self.icon_size,
				self.icon_size
			)
			option_widget : QtWidgets.QWidget = option.widget #type: ignore
			mouse_pos =  option_widget.mapFromGlobal(QtGui.QCursor.pos())
			if icon_rect.contains(mouse_pos):
				painter.fillRect(icon_rect, QtGui.QColor(0, 0, 0, 150))

			QtGui.QIcon.paint(self.trash_icon,
				painter,
				icon_rect,
				mode=QtGui.QIcon.Mode.Normal,
				state=QtGui.QIcon.State.On
			)


			#Restore the painter state
			painter.restore()


	def editorEvent(self,
			event : QtCore.QEvent,
			model : QtCore.QAbstractItemModel,
			option : QtWidgets.QStyleOptionViewItem, #TODO: typehinting not working? rect, state and widget not found
			index : QtCore.QModelIndex) -> bool:

		event_pos = event.position() #Local position #type: ignore
		global_pos = event_pos.toPoint()
		option_widget : QtWidgets.QTreeWidget = option.widget #type: ignore #TODO: option typehinting not working?
		option_rect : QtCore.QRect = option.rect #type: ignore



		#Check if the user clicked on the icon
		if event.type() == QtCore.QEvent.Type.MouseButtonPress:
			#Get the rect of the first column
			option_rect : QtCore.QRect = option.rect #type: ignore
			#Get the icon rect
			icon_rect = QtCore.QRect(option_rect.right() - self.icon_size, option_rect.top(), self.icon_size, self.icon_size)
			#Check if the mouse is inside the icon rect
			if icon_rect.contains(global_pos):
				#Emit the delete signal
				self.deleteHoverItem.emit(index)
				#Block event propagation
				event.setAccepted(True)
				return True

		elif event.type() == QtCore.QEvent.Type.MouseMove:
			#Get the rect of the first column
			#Get the icon rect
			icon_rect = QtCore.QRect(
				option_rect.right() - self.icon_size, option_rect.top() + (option_rect.height()-self.icon_size)//2,
				self.icon_size,
				self.icon_size
			)
			#Check if the mouse is inside the icon rect
			if icon_rect.contains(global_pos):
				if not self.hovering_del_btn: #Only update view if state changed
					self.hovering_del_btn = True
					option_widget.viewport().update()
				return True #Make sure that mousemove does not selet the underlying item
			elif self.hovering_del_btn:
				self.hovering_del_btn = False
				option_widget.viewport().update()

		return super().editorEvent(event, model, option, index)



class BaseConsoleItem(QtCore.QObject): #TODO: AbstractQObjectMeta
	"""Base-class for console items. All user-defined console items should inherit from this class.
	"""
	currentTextChanged = QtCore.Signal(str) #Emits the buffer when the text in the file changes
	dataChanged = QtCore.Signal() #When the metadata of the item changes (e.g. last-edit-date, name, running-state)

	@abstractmethod
	def data(self, role : QtCore.Qt.ItemDataRole, column : int = 0):
		"Get the data for the passed role at the passed column"
		raise NotImplementedError()

	@abstractmethod
	def get_current_text(self) -> str:
		"""Get the current text (str) of this console-item
		"""
		raise NotImplementedError()


class BaseConsoleStandardItemModel(QtCore.QAbstractItemModel):
	"""Small class to overload data-representation of the file-selection treeview based on recency
	and to add icons to the first column

	Is compatible with ConsoleFromFileItems

	NOTE: this model does not seem to work with treeviews, only tableviews
	"""
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self._console_pixmap = QtWidgets.QStyle.StandardPixmap.SP_TitleBarMaxButton
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
		return True

	def rowCount(self, parent : QtCore.QModelIndex = QtCore.QModelIndex()) -> int:
		if not parent.isValid(): #If model index is not valid -> top level item -> so all items
			return len(self._item_list)
		else:  #If one of the sub-items
			return 0

	def parent(self, index : QtCore.QModelIndex) -> QtCore.QModelIndex: #pylint: disable=unused-argument
		return QtCore.QModelIndex() #No parents

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



	def append_row(self, item : BaseConsoleItem):
		"""Append a row to the model - consisting of a single ConsoleStandardItem

		"""
		self.beginInsertRows(QtCore.QModelIndex(), self.rowCount(), self.rowCount())
		self._item_list.append(item)
		item.dataChanged.connect(
			lambda *_ : self.dataChanged.emit(self.index(self.rowCount()-1, 0), self.index(self.rowCount()-1, 2)))

		self.endInsertRows()

	def add_item (self, item : BaseConsoleItem):
		"""Add an item to the model, same as append_row

		Args:
			item (ConsoleStandardItem): The item to add
		"""
		self.append_row(item)

	#Overload the data method to return bold text if changes have been made in the past x seconds
	def data(self, index : QtCore.QModelIndex, role : QtCore.Qt.ItemDataRole = QtCore.Qt.ItemDataRole.DisplayRole):
		#Check if index is valid
		if not index.isValid(): #if index is not valid, return None
			return None

		#Get the item from the index
		item = index.internalPointer()

		assert isinstance(item, BaseConsoleItem)

		if role == QtCore.Qt.ItemDataRole.DisplayRole or role == QtCore.Qt.ItemDataRole.EditRole:
			return item.data(role=role, column=index.column()) #Return the data (str) of the item
		elif role == QtCore.Qt.ItemDataRole.DecorationRole:
			return self._console_icon
		elif role == QtCore.Qt.ItemDataRole.UserRole + 1:
			return item
		else:
			return None
		# return super().data(index, role)


class ConsoleWidget(QtWidgets.QWidget):
	"""Widget that dynamically displayes multiple console -
	E.g. in the case of ConsoleFromFileModel : watches the selected file for changes and updates the widget accordingly.
	Mainly intended for use with a file to which stdout/stderr can be redirected to."""

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

		#Make tree view non-editable
		# self.ui.fileSelectionTableView.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
		self.ui.fileSelectionTableView.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows)
		self.ui.fileSelectionTableView.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.SingleSelection)
		self.ui.fileSelectionTableView.mouseReleaseEvent = self.mouseReleaseEvent
		# self.ui.fileSelectionTableView.dragMoveEvent = self.dragMoveEvent
		# # self.ui.fileSelectionTableView.dragEnabled = False
		# self.ui.fileSelectionTableView.dragEnterEvent = self.dragMoveEvent
		# self.ui.fileSelectionTableView.dragLeaveEvent = self.dragMoveEvent
		# self.ui.fileSelectionTableView.setDragEnabled(False)

		#Set the delegate for the first column to the custom delegate
		self.file_selection_delegate = ConsoleWidgetDelegate(self.ui.fileSelectionTableView)
		self.ui.fileSelectionTableView.setItemDelegateForColumn(0, self.file_selection_delegate)
		self.file_selection_delegate.deleteHoverItem.connect(self.delete_file_selector_at_index)

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
			# test = self._files_proxy_model.data(index)
			item.currentTextChanged.connect(self._on_current_text_changed)
			self._current_text_connect = item.currentTextChanged
			# self.ui.consoleTextEdit.setPlainText(item.getCurrentText())

			self._on_current_text_changed(item.getCurrentText())
			# self._on_current_text_changed(item.getCurrentText())

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
	app = QtWidgets.QApplication([])
	ConsoleModel = BaseConsoleStandardItemModel()
	# newitem = QtGui.QStandardItem()
	# newitem.setData(QtCore.QDateTime.currentDateTime(), QtCore.Qt.ItemDataRole.DisplayRole)

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

	# ConsoleModel.addPath("file1", r"C:\Users\user\Documents\radial_drilling\test1.txt")
	# ConsoleModel.addPath("file2", r"C:\Users\user\Documents\radial_drilling\test2.txt")

	# defaulttableview = QtWidgets.QTreeView()
	# # defaulttableview = QtWidgets.QTableView()
	# proxy_model = QtCore.QSortFilterProxyModel()
	# proxy_model.setSourceModel(ConsoleModel)
	# defaulttableview.setModel(ConsoleModel)
	# defaulttableview.setSortingEnabled(True)
	# # defaulttableview.setModel(ConsoleModel)
	# defaulttableview.show()


	console_widget = ConsoleWidget()
	console_widget.set_model(ConsoleModel)
	window = QtWidgets.QMainWindow()
	#Set size to 1000
	window.resize(1200, 500)
	console_widget.set_console_width_percentage(20)

	# console_widget.fileSelectionDelegate.deleteHoverItem.connect(lambda index: ConsoleModel.removeRow(index.row()))

	layout = QtWidgets.QVBoxLayout()
	layout.addWidget(console_widget)

	dockable_window = QtWidgets.QDockWidget("Console", window)
	dockable_window.setWidget(console_widget)
	# dockable_window.setWidget(defaulttableview)

	console_widget.set_console_width_percentage(20)

	window.setCentralWidget(dockable_window)
	window.show()
	app.exec()
