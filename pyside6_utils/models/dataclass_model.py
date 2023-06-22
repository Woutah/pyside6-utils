"""
Defines a model that can be used to display a dataclass as a tree view. See the class doc for more information.
"""

import dataclasses
import datetime
import logging
import typing
from dataclasses import fields, is_dataclass

from PySide6 import QtCore, QtGui, QtWidgets

from pyside6_utils.models.dataclass_tree_item import DataclassTreeItem

log = logging.getLogger(__name__)

class SetDataCommand(QtGui.QUndoCommand):
	"""Used to set data in the model, so that these actions can be undone and redone.
	"""
	def __init__(self,
				dataclass_model : 'DataclassModel',
				index : QtCore.QModelIndex,
				value : typing.Any,
				role : int = QtCore.Qt.ItemDataRole.EditRole
			) -> None:
		super().__init__()
		self._model = dataclass_model
		#Convert index to persistent index, so that it can be used after some time #TODO: is this the best way to do this?
		self._index = QtCore.QPersistentModelIndex(index)
		self._new_value = value
		self._old_value = self._model.data(index, role)
		self._role = role
		self._prop_name = self._model.data(
			dataclass_model.index(self._index.row(), 0), QtCore.Qt.ItemDataRole.DisplayRole
		) #Used for naming the undo/redo action
		self.setText(f"Set {self._prop_name} ({self._old_value} -> {self._new_value})")

	# def text(self) -> str:
	# 	return "kaas"
		# return f"Set {self._prop_name} ({self._old_value} -> {self._new_value})"

	def undo(self):
		self._model._set_data(self._index, self._old_value, self._role) #pylint: disable=protected-access

	def redo(self):
		self._model._set_data(self._index, self._new_value, self._role) #pylint: disable=protected-access



class DataclassModel(QtCore.QAbstractItemModel):
	"""
	A model that can be used to display a dataclass as a QT tree view.
	Meant to be used with a QTreeView, but can also be used with a QTableView. Edits are propagated to the dataclass and
	are undoable/redoable if an undo stack is provided.

	Provides several keywords to add to the metadata of a field in a dataclass to change the way it is displayed:
		- display_name: The name that is displayed in the tree view. If not specified, the name of the field is used.
		- display_path: The path to the field in the tree view. If not specified, the field is displayed at the root of
			the tree.
		- help: A tooltip that is displayed when hovering over the field in the tree view.
		- editable: Whether the field is editable in the tree view. Defaults to True.
		- constraints: A list of constraints that are displayed in the tooltip. Defaults to None.

	"""
	FIELD_ROLE = QtCore.Qt.ItemDataRole.UserRole + 1 #Role for the field
	TYPE_ROLE = QtCore.Qt.ItemDataRole.UserRole #Returns the type of the field

	def __init__(self, dataclass_instance : object,
					parent: typing.Optional[QtCore.QObject] = None,
					undo_stack : QtGui.QUndoStack | None = None,
					allow_non_field_attrs : bool = False
				) -> None:
		"""
		Args:
			datatclass_instance (dataclasses.dataclass): The dataclass that is to be displayed.
			parent (typing.Optional[QtCore.QObject], optional): The parent of this model. Defaults to None.
			undo_stack (QtGui.QUndoStack, optional): The undo stack that is used to undo and redo changes.
				Defaults to None, in which case no undo stack will be created/used.
			allow_non_field_attrs (bool, optional): Whether to allow attributes that are not fields of the dataclass.
				Normally, we go over all attributes and check that all attributes are fields of the dataclass, if not,
				an error is raised. If this is set to True, attributes that are not fields of the dataclass are ignored.
				This is mainly intended for when we forget the @dataclass decorator on a class that inherits from another
				dataclass. If this happens, the new class attributes won't be fields and won't appear in the tree view.
		"""
		super().__init__(parent)
		self._allow_non_field_attrs = allow_non_field_attrs
		self._undo_stack = undo_stack
		self.set_dataclass_instance(dataclass_instance)


	def set_dataclass_instance(self, dataclass_instance: typing.Any) -> None:
		"""
		Sets the dataclass that is used to display data.
		"""
		#Check if dataclass_instance is a dataclass
		if not is_dataclass(dataclass_instance):
			raise TypeError(f"Expected a dataclass instance, got {type(dataclass_instance)} - make sure @dataclass is"
		   		"used on the class definition")

		#Check if dataclass has static attributes, if so, they were probably meant to be fields and the user
		# forgot to add the @dataclass decorator
		# the_dir = dir(dataclass_instance)
		dataclass_fields = dataclasses.fields(dataclass_instance)
		dataclass_field_names = [field.name for field in dataclass_fields]
		if not self._allow_non_field_attrs:
			for attr in dir(dataclass_instance):
				if not attr.startswith("__"):
					if attr not in dataclass_field_names and not callable(getattr(dataclass_instance, attr)):
						raise AttributeError(f"Attribute {attr} is not a field of the dataclass. "
			   				"This most likely happened because "
							" @dataclass decorator to the class definition")

		self.beginResetModel()
		# if self._undo_stack:
		# 	self._undo_stack.clear() #Reset undo stack NOTE: if we do this, this seemingly causes some issues with the
		# 	undo stack if we're combining multiple dataclassmodels using a single undo stack
		self._dataclass = dataclass_instance
		self._root_node = DataclassTreeItem("Root", None, None, None)


		#Build a dictionary with a path structure using dataclass.fields["metadata"]["display_path"] as key, split by "/"
		self.data_hierachy = {}

		if dataclass_instance is None:
			self.modelReset.emit()
			self.endResetModel()
			return

		for cur_field in fields(self._dataclass):
			if "display_path" in cur_field.metadata: #TODO: implement a sub-DataClassModel?
				path = cur_field.metadata["display_path"].split("/")
				current_dict = self.data_hierachy
				for i, cur_path in enumerate(path):
					if cur_path not in current_dict:
						current_dict[cur_path] = {}
					current_dict = current_dict[path[i]]
				current_dict[cur_field.name] = {}
			else:
				self.data_hierachy[cur_field.name] = {}


		#Build tree using data_hierachy dictionary
		self._build_tree(self._dataclass, self.data_hierachy, self._root_node)
		self.modelReset.emit()
		self.endResetModel()
		# self._root_node.print()

	def get_dataclass(self) -> typing.Any:
		"""
		Returns the current dataclass instance that is used to display data.
		"""
		return self._dataclass

	def _build_tree(self,
		 		data : 'DataclassInstance', #type:ignore
				data_hierarchy: typing.Dict,
				parent: DataclassTreeItem
			) -> None:
		"""Recursively builds the tree from a hierachy dictionary. Keys must be strings, if they exist in the dataclass,
		their data will be added.

		Args:
			dataclass_instance (DataclassInstance): dataclass instance used to retrieve the value of the key
			parent (DataClassTreeItem): The parent of the current item
		"""
		name_field_dict = {field.name: field for field in fields(data)}
		for key, value in data_hierarchy.items():
			item_data = None
			if key in data.__dict__:
				item_data = data.__dict__[key]


			item = DataclassTreeItem(name=key, item_data=item_data, field=name_field_dict.get(key, None), parent=parent)
			parent.append_child(item)
			if isinstance(value, dict) and len(value) > 0:
				self._build_tree(data, value, item)

	def parent(self, index: QtCore.QModelIndex) -> QtCore.QModelIndex:
		if not index.isValid():
			return QtCore.QModelIndex()

		item = index.internalPointer() #Get TreeItem from index
		assert isinstance(item, DataclassTreeItem)
		parent_item = item.parent()

		if parent_item == self._root_node or parent_item is None:
			return QtCore.QModelIndex()

		return self.createIndex(parent_item.row(), 0, parent_item)


	def rowCount(self, parent: QtCore.QModelIndex = QtCore.QModelIndex()) -> int:
		if not parent.isValid():
			parent_item = self._root_node
		else:
			parent_item = parent.internalPointer()
		assert isinstance(parent_item, DataclassTreeItem)
		return parent_item.child_count()



	def headerData(self,
				section: int,
				orientation: QtCore.Qt.Orientation,
				role: int = QtCore.Qt.ItemDataRole.DisplayRole
			) -> typing.Any:
		"""
		Returns the data for the given role and section in the header with the specified orientation.
		"""
		if role == QtCore.Qt.ItemDataRole.DisplayRole:
			if orientation == QtCore.Qt.Orientation.Horizontal:
				if section == 0:
					return "Property"
				elif section == 1:
					return "Value"
			else:
				return section
		else:
			return None




	def data(self, index: QtCore.QModelIndex, role: int = QtCore.Qt.ItemDataRole.DisplayRole) -> typing.Any:
		"""
		Returns the data stored under the given role for the item referred to by the index.
		"""
		try:
			if not index.isValid():
				return None

			node : DataclassTreeItem = index.internalPointer() #type: ignore
			name_field_dict = {field.name: field for field in fields(self._dataclass)}


			if role == QtCore.Qt.ItemDataRole.DisplayRole:
				if index.column() == 0: #If retrieving the name of the property
					try:
						return name_field_dict[node.name].metadata["display_name"]
					except (IndexError, KeyError, AttributeError):
						return node.name
				else:
					ret_val = self._dataclass.__dict__.get(node.name, None)
					if ret_val is None:
						return ""
					elif isinstance(ret_val, datetime.datetime):
						return ret_val.strftime("%Y-%m-%d %H:%M:%S")
					elif isinstance(ret_val, bool):
						return str(ret_val).capitalize()
					return ret_val

			elif role == QtCore.Qt.ItemDataRole.EditRole:
				return self._dataclass.__dict__.get(node.name, None)
			elif role == QtCore.Qt.ItemDataRole.ToolTipRole:
				result_str = ""
				result_str += name_field_dict[node.name].metadata.get("help", "")
				item_type_name = name_field_dict[node.name].type.__name__
				result_str += f" (type: {item_type_name[:20]})"

				if hasattr(name_field_dict[node.name], "default"):
					result_str += f" (default: {str(name_field_dict[node.name].default)[:20]})"
				return result_str
			elif role == DataclassModel.TYPE_ROLE: #Get type role #TODO: maybe create Enum with more descriptive names.
					#NOTE: if we just use an enum, we get an error in ModelIndex.data due to the enum not being an instance
					# of Qt.ItemDataRole.DisplayRole
				result = name_field_dict.get(node.name, None) #Get field
				if result:
					return result.type #If field is available -> return type
				else:
					return None
			elif role == DataclassModel.FIELD_ROLE: #Field role
				result = name_field_dict.get(node.name, None) #Get field
				return result
			elif role == QtCore.Qt.ItemDataRole.FontRole:
				if name_field_dict.get(node.name, None) is None:
					return None #If only a header (no data)
				if hasattr(name_field_dict[node.name], "default"):
					default_val = name_field_dict[node.name].default
					#If current value is not equal to the default value, make the font bold
					if self._dataclass.__dict__.get(node.name, None) != default_val:
						font = QtGui.QFont()
						font.setBold(True)
						return font
				return None
		except Exception as exception: #pylint: disable=broad-except
			log.warning(f"Error while retrieving data at index ({index.row()},{index.column()}) - "
	       		f"{type(exception).__name__} : {exception}")

		return None


	def _set_data(self, index: QtCore.QModelIndex | QtCore.QPersistentModelIndex,
					value: typing.Any,
					role: int = QtCore.Qt.ItemDataRole.EditRole) -> bool:
		"""
		Sets the role data for the item at index to value - without using an undo stack.
		"""
		if role == QtCore.Qt.ItemDataRole.EditRole:
			tree_item = index.internalPointer()
			assert isinstance(tree_item, DataclassTreeItem)
			self._dataclass.__dict__[tree_item.name] = value
			self.dataChanged.emit(index, index)
			return True
		return False



	def setData(self,
				index: QtCore.QModelIndex,
				value: typing.Any,
				role: int = QtCore.Qt.ItemDataRole.EditRole
			) -> bool:
		"""
		Sets the role data for the item at index to value.
		"""
		log.debug(f"Setting data at index {index} to {value} of type {type(value)}")


		if not self._undo_stack:
			return self._set_data(index, value, role)

		if role == QtCore.Qt.ItemDataRole.EditRole:
			dataclass_item = index.internalPointer()
			assert isinstance(dataclass_item, DataclassTreeItem)
			if self._dataclass.__dict__[dataclass_item.name] == value: #If the value is different from the current value
				return False #Do nothing
			self._undo_stack.push(SetDataCommand(self, index, value, role)) #Push the command to the undo-stack
			return True
		return False

	def flags(self, index: QtCore.QModelIndex) -> QtCore.Qt.ItemFlag:
		if index.column() == 0:
			return QtCore.Qt.ItemFlag.ItemIsEnabled | QtCore.Qt.ItemFlag.ItemIsSelectable
		else:
			if index.internalPointer():
				node = index.internalPointer()
				assert isinstance(node, DataclassTreeItem)
				if node.field: #TODO: this assumes nodes without fields are not part of the dataclass -> not editable
					flags = QtCore.Qt.ItemFlag.ItemIsEnabled | QtCore.Qt.ItemFlag.ItemIsSelectable
					if node.field.metadata.get("editable", True):
						flags |= QtCore.Qt.ItemFlag.ItemIsEditable
					return flags
			return QtCore.Qt.ItemFlag.ItemIsEnabled

	def set_to_default(self, index: QtCore.QModelIndex) -> None:
		"""Sets the data at the given index to the default value"""
		if not index.isValid():
			return
		tree_item = index.internalPointer()
		assert isinstance(tree_item, DataclassTreeItem)
		field = tree_item.field
		if field is None:
			return
		if hasattr(field, "default"):
			default_value = field.default
			self.setData(index, default_value, QtCore.Qt.ItemDataRole.EditRole)

	def has_default(self, index: QtCore.QModelIndex) -> bool:
		"""Returns whether the given index has a default value"""
		if not index.isValid():
			return False
		tree_item = index.internalPointer()
		assert isinstance(tree_item, DataclassTreeItem)
		field = tree_item.field
		if field is None:
			return False
		return hasattr(field, "default")

	def redo(self):
		"""Trigger redo on undo stack"""
		if self._undo_stack:
			return self._undo_stack.redo()
		return None


	def undo(self):
		"""Trigger undo on undo stack"""
		if self._undo_stack:
			return self._undo_stack.undo()

	def columnCount(self, parent: QtCore.QModelIndex = QtCore.QModelIndex()) -> int: #pylint: disable=unused-argument
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
		assert isinstance(parent_item, DataclassTreeItem)
		child_item =  parent_item.child(row)

		if child_item:
			return self.createIndex(row, column, child_item)
		else:
			return QtCore.QModelIndex()


if __name__ == "__main__":

	import sys

	from pyside6_utils.examples.example_dataclass import ExampleDataClass
	from pyside6_utils.widgets.delegates.dataclass_editors_delegate import DataclassEditorsDelegate
	from pyside6_utils.widgets.dataclass_tree_view import DataClassTreeView


	formatter = logging.Formatter("[{pathname:>90s}:{lineno:<4}]  {levelname:<7s}   {message}", style='{')
	handler = logging.StreamHandler()
	handler.setFormatter(formatter)
	logging.basicConfig(
		handlers=[handler],
		level=logging.DEBUG) #Without time

	app = QtWidgets.QApplication(sys.argv)
	test_data = ExampleDataClass()
	model = DataclassModel(test_data)
	view1 = DataClassTreeView()
	view2= QtWidgets.QTableView()

	view1.setModel(model)
	view1.setItemDelegate(DataclassEditorsDelegate())
	view2.setModel(model)
	view2.setItemDelegate(DataclassEditorsDelegate())
	#adjust treeview to fit contents, but allow user to resize
	#Fit header of view 1 to contents, then allow user to resize
	view1.header().setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
	view1.header().setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeMode.Stretch)
	view1.show()
	view2.show()

	#Set window size to 400 and display
	view1.resize(400, 400)
	view2.resize(400, 400)

	#Place windows next to each other
	view1.move(1000, 400)
	view2.move(1400, 400)
	app.exec()
	print(test_data)
	sys.exit()
