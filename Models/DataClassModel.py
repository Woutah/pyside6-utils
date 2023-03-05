
import typing
from PySide6 import QtCore, QtWidgets, QtGui
from dataclasses import dataclass, field, fields
from datetime import datetime
import typing_inspect



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


class DataclassModel(QtCore.QAbstractItemModel):
	"""
	This is a model that can be used to display a dataclass.
	"""

	def __init__(self, data : typing, parent: typing.Optional[QtCore.QObject] = None ) -> None:
		super().__init__(parent)

		self.setDataClass(data)


	

	def setDataClass(self, data: typing.Any) -> None:
		"""
		Sets the dataclass that is used to display data.
		"""
		self.beginResetModel()
		self.data_class = data
		self._root_node = DataClassTreeItem("Root", None, None, None)

		#Build a dictionary with a path structure using dataclass.fields["metadata"]["display_path"] as key, split by "/"
		self.data_hierachy = {}
		temp =  fields(self.data_class)
		for field in fields(self.data_class):
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
		self._build_tree(self.data_class, self.data_hierachy, self._root_node)
		self.modelReset.emit()
		self.endResetModel()
		# self._root_node.print()

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
		keys = list(self.data_class.__dict__.keys())

		# if index.column() == 0: #If retrieving the name of the property
		# 	return keys[index.row()]


		# temp = fields(self.data)
		name_field_dict = {field.name: field for field in fields(self.data_class)}

		if role == QtCore.Qt.DisplayRole:
			# return self.data_class.__dict__[index.internalPointer()[0]]
				
			if index.column() == 0: #If retrieving the name of the property
				try: 
					return name_field_dict[node.name].metadata["display_name"]
				except (IndexError, KeyError, AttributeError):
					return node.name
			else:
				return self.data_class.__dict__.get(node.name, None)

		elif role == QtCore.Qt.EditRole:
			return self.data_class.__dict__.get(node.name, None)
		elif role == QtCore.Qt.ToolTipRole:
			# return self.data.__dict__[index.internalPointer()[0]]
			# try:
			result_str = ""
			try:
				result_str += name_field_dict[node.name].metadata.get("help", None)
			except:
				pass
			try:
				result_str += f" (type: {name_field_dict[node.name].type})"
				result_str += f" (default: {name_field_dict[node.name].default})"
			except:
				pass
			return result_str
			# except (KeyError, AttributeError) as ex:
			# 	print(ex)
			# return None
		elif role == QtCore.Qt.DecorationRole:
			# colors = [QtCore.Qt.red, QtCore.Qt.green, QtCore.Qt.blue, QtCore.Qt.yellow, QtCore.Qt.cyan, QtCore.Qt.magenta]
			# return QtGui.QColor(colors[index.row() % len(colors)])
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
			#Make sure that the first column is displayed properly
			return None
		elif role == QtCore.Qt.FontRole:
			return None
		elif role == QtCore.Qt.InitialSortOrderRole:
			return None
		elif role == QtCore.Qt.UserRole:
			return None
		else:
			return None


	def setData(self, index: QtCore.QModelIndex, value: typing.Any, role: int = QtCore.Qt.EditRole) -> bool:
		"""
		Sets the role data for the item at index to value.
		"""
		if role == QtCore.Qt.EditRole:
			self.data_class.__dict__[index.internalPointer().name] = value
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



LITERAL_EXAMPLE  = typing.Literal["Lit1", "Lit2", "Lit3"]




if __name__ == "__main__":

	from Examples.Data.ExampleDataClass import ExampleDataClass
	from Utility.MoreTableEditorsDelegate import MoreTableEditorsDelegate
	import sys

	app = QtWidgets.QApplication(sys.argv)

	data = ExampleDataClass()

	model = DataclassModel(data)

	view1 = QtWidgets.QTreeView()
	view2= QtWidgets.QTableView()

	#table_view.show()
	view1.setModel(model)
	view1.setItemDelegate(MoreTableEditorsDelegate())
	view2.setModel(model)
	view2.setItemDelegate(MoreTableEditorsDelegate())
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