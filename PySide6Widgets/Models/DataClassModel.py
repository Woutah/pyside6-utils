
import typing
from PySide6 import QtCore, QtWidgets, QtGui
from dataclasses import dataclass, field, fields
from datetime import datetime
import typing_inspect
from enum import Enum


#Create a custom role
# class DataClassRoles(Enum):
# 	_FirstUserRoleDoNotUse = QtCore.Qt.UserRole
# 	dataclassFieldTypeRole = QtCore.Qt.UserRole + 1 


#Create TreeItem class for dataclass tree view
class DataClassTreeItem(object):
	"""
	This class represents a single item in a tree.
	"""
	def __init__(self, name : str, data: typing.Any, field : any, parent: typing.Optional["DataClassTreeItem"] = None) -> None:
		self.name = name
		self.itemData = data
		self.field = field 
		self.parentItem = parent
		self.childItems = []

	def appendChild(self, item: "DataClassTreeItem") -> None:
		self.childItems.append(item)

	def child(self, row: int) -> "DataClassTreeItem":
		return self.childItems[row]

	def childCount(self) -> int:
		return len(self.childItems)

	def columnCount(self) -> int:
		return 2

	def data(self) -> typing.Any:
		return self.itemData

	def parent(self) -> "DataClassTreeItem":
		return self.parentItem

	def row(self) -> int:
		if self.parentItem:
			return self.parentItem.childItems.index(self)

		return 0


	def print(self, indent: int = 0) -> None:
		print("-" * indent, self.itemData)
		for child in self.childItems:
			child.print(indent + 1)


class SetDataCommand(QtGui.QUndoCommand):
	"""Used to set data in the model, so that these actions can be undone and redone.
	"""
	def __init__(self, model : 'DataclassModel', index : QtCore.QModelIndex, value : any, role : int = QtCore.Qt.EditRole) -> None:
		super().__init__()
		self._model = model
		#Convert index to persistent index, so that it can be used after some time #TODO: is this the best way to do this?
		self._index = QtCore.QPersistentModelIndex(index)
		self._new_value = value
		self._old_value = self._model.data(index, role)
		self._role = role
		self._prop_name = self._model.data( model.index(self._index.row(), 0), QtCore.Qt.DisplayRole) #Used for naming the undo/redo action
		self.setText(f"Set {self._prop_name} ({self._old_value} -> {self._new_value})")

	# def text(self) -> str:
	# 	return "kaas"
		# return f"Set {self._prop_name} ({self._old_value} -> {self._new_value})"

	def undo(self):
		self._model._setData(self._index, self._old_value, self._role)

	def redo(self):
		self._model._setData(self._index, self._new_value, self._role)
		


class DataclassModel(QtCore.QAbstractItemModel):
	"""
	This is a model that can be used to display a dataclass.
	"""


	def __init__(self, data : typing, parent: typing.Optional[QtCore.QObject] = None, undo_stack : QtGui.QUndoStack = None) -> None:
		"""This model can be used to display a dataclass.

		Args:
			data (dataclass): The dataclass that is to be displayed.
			parent (typing.Optional[QtCore.QObject], optional): The parent of this model. Defaults to None.
			undo_stack (QtGui.QUndoStack, optional): The undo stack that is used to undo and redo changes. Defaults to None, in which case no undo stack will be created/used.
		"""
		super().__init__(parent)
		self.maxTooltipLineWidth = 100
		self.ignoreTooltipNextlines = True
		self._undo_stack = undo_stack
		self.setDataClass(data)
	

	def setDataClass(self, data: typing.Any) -> None:
		"""
		Sets the dataclass that is used to display data.
		"""
		self.beginResetModel()
		# if self._undo_stack:
		# 	self._undo_stack.clear() #Reset undo stack NOTE: if we do this, this seemingly causes some issues with the undo stack if we're combining multiple dataclassmodels using a single undo stack
		self._data_class = data
		self._root_node = DataClassTreeItem("Root", None, None, None)


		#Build a dictionary with a path structure using dataclass.fields["metadata"]["display_path"] as key, split by "/"
		self.data_hierachy = {}

		if data is None:
			self.modelReset.emit()
			self.endResetModel()
			return
		
		for field in fields(self._data_class):
			if "display_path" in field.metadata: #TODO: implement a sub-DataClassModel? 
				path = field.metadata["display_path"].split("/")
				current_dict = self.data_hierachy
				for i in range(len(path)):
					if path[i] not in current_dict:
						current_dict[path[i]] = {}
					current_dict = current_dict[path[i]]
				current_dict[field.name] = {}
			else:
				self.data_hierachy[field.name] = {}


		#Build tree using data_hierachy dictionary
		self._build_tree(self._data_class, self.data_hierachy, self._root_node)
		self.modelReset.emit()
		self.endResetModel()
		# self._root_node.print()

	def getDataClass(self) -> typing.Any:
		"""
		Returns the dataclass that is used to display data.
		"""
		return self._data_class

	def _build_tree(self, data : typing.Type[dataclass], data_hierarchy: typing.Dict, parent: DataClassTreeItem) -> None:
		"""
		Recursively builds the tree from a hierachy dictionary. Keys must be strings, if they exist in the dataclass, their data will be added.
		"""
		name_field_dict = {field.name: field for field in fields(data)}
		for key, value in data_hierarchy.items():
			item_data = None
			if key in data.__dict__:
				item_data = data.__dict__[key]


			item = DataClassTreeItem(name=key, data=item_data, field=name_field_dict.get(key, None), parent=parent)
			parent.appendChild(item)
			if isinstance(value, dict) and len(value) > 0:
				self._build_tree(data, value, item)

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

		node : DataClassTreeItem = index.internalPointer() 
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
				result_str += f" (type: {name_field_dict[node.name].type.__name__})"
				result_str += f" (default: {name_field_dict[node.name].default})"
			except:
				pass
			return result_str
		elif role == QtCore.Qt.UserRole: #TODO: maybe create Enum with more descriptive names. NOTE: if we just use an enum, we get an error in ModelIndex.data due to the enum not being an instance of Qt.DisplayRole
			result = name_field_dict.get(node.name, None) #Get field
			if result:
				return result.type #If field is available -> return type
			else:
				return None
		elif role == QtCore.Qt.UserRole+1: #Default value role
			result = name_field_dict.get(node.name, None) #Get field
			if result:
				return result.default
			else:
				return None
		elif role == QtCore.Qt.DecorationRole:
			return None
		elif role == QtCore.Qt.BackgroundRole:
			return None
		elif role == QtCore.Qt.ForegroundRole:
			return None
		elif role == QtCore.Qt.TextAlignmentRole:
			return None
		elif role == QtCore.Qt.CheckStateRole:
			return None
		elif role == QtCore.Qt.SizeHintRole:
			return None
		elif role == QtCore.Qt.FontRole:
			return None
		elif role == QtCore.Qt.InitialSortOrderRole:
			return None
		elif role == QtCore.Qt.UserRole:
			return None
		else:
			return None
		
	
	def _setData(self, index: QtCore.QModelIndex, value: typing.Any, role: int = QtCore.Qt.EditRole) -> bool:
		"""
		Sets the role data for the item at index to value.
		"""
		if role == QtCore.Qt.EditRole:
			self._data_class.__dict__[index.internalPointer().name] = value
			self.dataChanged.emit(index, index)
			return True
		return False
	


	def setData(self, index: QtCore.QModelIndex, value: typing.Any, role: int = QtCore.Qt.EditRole) -> bool:
		"""
		Sets the role data for the item at index to value.
		"""


		if not self._undo_stack:
			return self._setData(index, value, role)
			
		if role == QtCore.Qt.EditRole:
			if self._data_class.__dict__[index.internalPointer().name] == value: #If the value is different from the current value
				return False #Do nothing
			self._undo_stack.push(SetDataCommand(self, index, value, role)) #Push the command to the stack
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
		

	def redo(self):
		if self._undo_stack:
			return self._undo_stack.redo()
		

	def undo(self):
		if self._undo_stack:
			return self._undo_stack.undo()

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



LITERAL_EXAMPLE  = typing.Literal["Lit1", "Lit2", "Lit3"]




if __name__ == "__main__":

	from PySide6Widgets.Examples.Data.ExampleDataClass import ExampleDataClass
	from PySide6Widgets.Utility.DataClassEditorsDelegate import DataClassEditorsDelegate
	import sys

	app = QtWidgets.QApplication(sys.argv)

	data = ExampleDataClass()

	model = DataclassModel(data)

	view1 = QtWidgets.QTreeView()
	view2= QtWidgets.QTableView()

	#table_view.show()
	view1.setModel(model)
	view1.setItemDelegate(DataClassEditorsDelegate())
	view2.setModel(model)
	view2.setItemDelegate(DataClassEditorsDelegate())
	#adjust treeview to fit contents, but allow user to resize
	#Fit header of view 1 to contents, then allow user to resize
	view1.header().setSectionResizeMode(QtWidgets.QHeaderView.ResizeToContents)
	# view2.header().setSectionResizeMode(QtWidgets.QHeaderView.ResizeToContents)
	view1.header().setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)
	# view2.header().setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)
	view1.show()
	view2.show()

	#Set window size to 400 and display
	view1.resize(400, 400)
	view2.resize(400, 400)
	#table_view.resize(400, 400)
	#Place windows next to each other
	view1.move(1000, 400)
	view2.move(1400, 400)
	app.exec_()
	print(data)
	sys.exit()