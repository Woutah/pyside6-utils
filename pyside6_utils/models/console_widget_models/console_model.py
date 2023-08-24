"""Implements the base-model for the console widget. 
We can then choose to implement custom sub-class of this model.
"""

import typing
from abc import abstractmethod

from PySide6 import QtCore, QtWidgets


class BaseConsoleItem(QtCore.QObject): #TODO: AbstractQObjectMeta
	"""Base-class for console items. All user-defined console items should inherit from this class.
	"""
	currentTextChanged = QtCore.Signal(str, int) #Emits the string when the text-data changes. If we want to track the
		# cursor position when using a max-string-size we must also emit the buffer-position relative to the 
		# full string
	dataChanged = QtCore.Signal() #When the metadata of the item changes (e.g. last-edit-date, name, running-state)

	@abstractmethod
	def data(self, role : QtCore.Qt.ItemDataRole, column : int = 0):
		"Get the data for the passed role at the passed column"
		raise NotImplementedError()

	@abstractmethod
	def get_current_text(self) -> typing.Tuple[str, int]:
		"""Get the current text (str) of this console-item

		Retuns:
			Tuple[str, int]: The current text and the start-index of this buffer
		"""
		raise NotImplementedError()


class ConsoleModel(QtCore.QAbstractItemModel):
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

	def columnCount(self, parent : QtCore.QModelIndex = QtCore.QModelIndex()) -> int: #pylint: disable=unused-argument
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
