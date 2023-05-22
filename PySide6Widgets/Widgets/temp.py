
from typing import List, Union
from PySide6 import QtCore, QtWidgets
from logging.handlers import QueueHandler, QueueListener
from PySide6 import QtCore, QtWidgets, QtGui
import PySide6.QtCore
from PySide6Widgets.UI.ConsoleFromFileWidget_ui import Ui_ConsoleFromFileWidget
import os
import logging
log = logging.getLogger(__name__)
import typing
import app_resources_rc


# class ConsoleStandardItem(QtWidgets.QTableWidgetItem):
class ConsoleItem():
	"""
	This class represents a single item in a tree.
	"""
	def __init__(self, name : str, data: typing.Any, field : any, parent: typing.Optional["ConsoleItem"] = None) -> None:
		self.name = name
		self.itemData = data
		self.field = field 
		self.parentItem = parent
		self.childItems = []

	def appendChild(self, item: "ConsoleItem") -> None:
		self.childItems.append(item)

	def child(self, row: int) -> "ConsoleItem":
		return self.childItems[row]

	def childCount(self) -> int:
		return len(self.childItems)

	def columnCount(self) -> int:
		return 2

	def data(self) -> typing.Any:
		return self.itemData

	def parent(self) -> "ConsoleItem":
		return self.parentItem

	def row(self) -> int:
		if self.parentItem:
			return self.parentItem.childItems.index(self)

		return 0


	def print(self, indent: int = 0) -> None:
		print("-" * indent, self.itemData)
		for child in self.childItems:
			child.print(indent + 1)

# class ConsoleStandardItemModel(QtGui.QStandardItemModel):
class ConsoleStandardItemModel(QtCore.QAbstractItemModel):
	"""
	This is a model that can be used to display a dataclass.
	"""


	def __init__(self, data : typing, parent: typing.Optional[QtCore.QObject] = None, undo_stack : QtGui.QUndoStack = None) -> None:
		"""This model can be used to display a dataclass.

		Args:
			data (dataclass): The dataclass that is to be displayed.
			parent (typing.Optional[QtCore.QObject], optional): The parent of this model. Defaults to None.
		"""
		super().__init__(parent)
		self.maxTooltipLineWidth = 100
		self.ignoreTooltipNextlines = True
		self.setDataClass(data)
	

	def getDataClass(self) -> typing.Any:
		"""
		Returns the dataclass that is used to display data.
		"""
		return self._data_class



	def parent(self, index: QtCore.QModelIndex) -> QtCore.QModelIndex:
		if not index.isValid():
			return QtCore.QModelIndex()

		item = index.internalPointer() #Get TreeItem from index
		parent_item = item.parent()

		if parent_item == self._root_node:
			return QtCore.QModelIndex()

		return self.createIndex(parent_item.row(), 0, parent_item)


	def rowCount(self, parent: QtCore.QModelIndex = QtCore.QModelIndex()) -> int:
		if not parent.isValid():
			parent_item = self._root_node
		else:
			parent_item = parent.internalPointer()

		return parent_item.childCount()
	


	def headerData(self, section: int, orientation: QtCore.Qt.Orientation, role: int = QtCore.Qt.DisplayRole) -> typing.Any:
		"""
		Returns the data for the given role and section in the header with the specified orientation.
		"""
		if role == QtCore.Qt.DisplayRole:
			if orientation == QtCore.Qt.Horizontal:
				if section == 0:
					return "Property"
				elif section == 1:
					return "Value"
			else:
				return section
		else:
			return None




	def data(self, index: QtCore.QModelIndex, role: int = QtCore.Qt.DisplayRole) -> typing.Any:
		"""
		Returns the data stored under the given role for the item referred to by the index.
		"""
		if not index.isValid():
			return None

		node : ConsoleItem = index.internalPointer() 
		name_field_dict = {field.name: field for field in fields(self._data_class)}

		if role == QtCore.Qt.DisplayRole:
			# return self.data_class.__dict__[index.internalPointer()[0]]
				
			if index.column() == 0: #If retrieving the name of the property
				try: 
					return name_field_dict[node.name].metadata["display_name"]
				except (IndexError, KeyError, AttributeError):
					return node.name
			else:
				return self._data_class.__dict__.get(node.name, None)

		elif role == QtCore.Qt.EditRole:
			return self._data_class.__dict__.get(node.name, None)
		elif role == QtCore.Qt.ToolTipRole:
			result_str = ""
			try:
				result_str += name_field_dict[node.name].metadata.get("help", None)
			except:
				pass
			try:
				#Get both but cap the length of each to 20 characters
				result_str += f" (type: {name_field_dict[node.name].type.__name__[:20]})"
				result_str += f" (default: {name_field_dict[node.name].default[:20]})"
				# constraints = name_field_dict[node.name].metadata.get("constraints", None)
				# if constraints is not None:
				# 	result_str += f" (constraints: {' '.join(constraints)})"
			except:
				pass
			return result_str
		elif role == QtCore.Qt.UserRole: #Get type role #TODO: maybe create Enum with more descriptive names. NOTE: if we just use an enum, we get an error in ModelIndex.data due to the enum not being an instance of Qt.DisplayRole
			result = name_field_dict.get(node.name, None) #Get field
			if result:
				return result.type #If field is available -> return type
			else:
				return None
		elif role == QtCore.Qt.UserRole+1: #Field role
			result = name_field_dict.get(node.name, None) #Get field
			return result
		else:
			return None
		
	
	def setData(self, index: QtCore.QModelIndex, value: typing.Any, role: int = QtCore.Qt.EditRole) -> bool:
		"""
		Sets the role data for the item at index to value.
		"""
		if role == QtCore.Qt.EditRole:
			self._data_class.__dict__[index.internalPointer().name] = value
			self.dataChanged.emit(index, index)
			return True
		return False
	

	def flags(self, index: QtCore.QModelIndex) -> QtCore.Qt.ItemFlags:

		if index.column() == 0:
			return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable
		else:
			if index.internalPointer():
				node = index.internalPointer()
				if node.field: #TODO: this assumes nodes without fields are not part of the dataclass -> not editable 
					flags = QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable
					if node.field.metadata.get("editable", True):
						flags |= QtCore.Qt.ItemIsEditable
					return flags
			return QtCore.Qt.ItemIsEnabled
		


	def columnCount(self, parent: QtCore.QModelIndex = QtCore.QModelIndex()) -> int:
		"""
		Returns the number of columns for the children of the given parent.
		"""
		return 2

	def index(self, row: int, column: int, parent: QtCore.QModelIndex = QtCore.QModelIndex()) -> QtCore.QModelIndex:
		"""
		Returns the index of the item in the model specified by the given row, column and parent index.
		"""

		if not parent.isValid():
			parent_item = self._root_node #If the parent is invalid, then the parent is the root
		else:
			parent_item = parent.internalPointer()
		
		child_item =  parent_item.child(row)

		if child_item:
			return self.createIndex(row, column, child_item)
		else:
			return QtCore.QModelIndex()



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
	ConsoleModel.appendRow(
		ConsoleItem("file1", r"C:\Users\user\Documents\radial_drilling\test1.txt", "test")
	)
	ConsoleModel.appendRow(
		ConsoleItem("file2", r"C:\Users\user\Documents\radial_drilling\test2.txt", "test2")
	)	
	ConsoleModel.appendRow(
		ConsoleItem("file3", r"C:\Users\user\Documents\radial_drilling\test2.txt", "test3")
	)

	defaulttableview = QtWidgets.QTreeView()
	# defaulttableview = QtWidgets.QTableView()
	proxy_model = QtCore.QSortFilterProxyModel()
	proxy_model.setSourceModel(ConsoleModel)
	defaulttableview.setModel(ConsoleModel)
	defaulttableview.setSortingEnabled(True)
	# defaulttableview.setModel(ConsoleModel)
	# defaulttableview.show()


	console_widget = ConsoleFromFileWidget(name_date_path_model=ConsoleModel)
	window = QtWidgets.QMainWindow()
	#Set size to 1000
	window.resize(1200, 500)
	console_widget.setConsoleWidthPercentage(20)

	# console_widget.fileSelectionDelegate.deleteHoverItem.connect(lambda index: ConsoleModel.removeRow(index.row()))

	layout = QtWidgets.QVBoxLayout()
	layout.addWidget(console_widget)

	dockable_window = QtWidgets.QDockWidget("Console", window)
	# dockable_window.setWidget(console_widget)
	dockable_window.setWidget(defaulttableview)
	
	console_widget.setConsoleWidthPercentage(20)

	window.setCentralWidget(dockable_window)
	window.show()
	app.exec()


