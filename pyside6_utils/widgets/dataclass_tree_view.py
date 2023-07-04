"""
Treeview meant to be used with a dataclass-model, adds some extra functionality
NOTE: since this wrapper is VERY simple, it is not included in the registrars
"""


import logging
import typing

from PySide6 import QtCore, QtGui, QtWidgets
from pyside6_utils.models.dataclass_model import (DataclassModel,
                                                  HasNoDefaultError)
from pyside6_utils.models.dataclass_tree_item import DataclassTreeItem

log = logging.getLogger(__name__)

class DataClassTreeView(QtWidgets.QTreeView):
	"""
	Treeview meant to be used with a dataclass-model, adds some extra functionality
	Extra functionality:
		- Custom contex-menu (right-click) to set back to default
	"""

	def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
		super().__init__(parent)

		#Keep a list of expanded items (by node.name, re-expand them on model reset)
		self._expanded_items = set({})
		#On expand, add the node.name to the list of expanded items
		self.expanded.connect(lambda index, expanded=True: self._on_expansion_change(index, expanded))
		self.collapsed.connect(lambda index, expanded=False: self._on_expansion_change(index, expanded))

		self._model_signals : typing.List[QtCore.SignalInstance] = []

		#Context menu
		self.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)
		self.customContextMenuRequested.connect(self.reset_expansion_state)

	def _on_expansion_change(self, index : QtCore.QModelIndex, expanded : bool) -> None:
		"""
		Keep track of the expanded items (by node.name)
		If we switch to a different model, we want to keep the expanded items the same
		"""
		attr_name = index.data(DataclassModel.CustomDataRoles.AttributeNameRole)
		if expanded and attr_name not in self._expanded_items:
			self._expanded_items.add(attr_name)
		elif not expanded and attr_name in self._expanded_items:
			self._expanded_items.remove(attr_name)
		# log.debug(f"Expansion changed: {index.data()} = {expanded}, expanded items: {self._expanded_items}")

	def _get_set_expansion_state(self, index : QtCore.QModelIndex) -> None:
		"""Recursively sets the expansion state of the given index (and its children) using the current settings"""

		try:
			if index is None or not index.isValid():
				return

			tree_item : DataclassTreeItem = index.data(DataclassModel.CustomDataRoles.TreeItemRole)
			if tree_item.name in self._expanded_items:
				self.expand(index)
			else:
				self.collapse(index)

			for child_nr in range(tree_item.child_count()):
				child = tree_item.child(child_nr)
				child_index = self.model().index(child.row(), 0, index)
				self._get_set_expansion_state(child_index)
				# child_index = self.model().createIndex(child.row(), 0, child)
				# self._get_set_expansion_state(child_index)
		except Exception as exception: #pylint: disable=broad-except
			log.exception(f"Error when setting expansion state {type(exception).__name__}: {exception}")

	def reset_expansion_state(self) -> None:
		"""Resets the expansion state of all items in the treeview"""
		self.blockSignals(True)
		# self._get_set_expansion_state(self.model().index(0, 0).parent())
		# self._get_set_expansion_state(self.rootIndex())
		root = self.rootIndex()
		for child_nr in range(self.model().rowCount(root)): #Get all top-level items
			index = self.model().index(child_nr, 0, root)
			self._get_set_expansion_state(index)
		self.blockSignals(False)

	def setModel(self, model: QtCore.QAbstractItemModel | None) -> None:
		super().setModel(model) #type: ignore #NOTE: before connections, otherwise expand goes wrong bc view is not set
		if len(self._model_signals) > 0: #Disconnect all previous signals
			for signal in self._model_signals:
				self.disconnect(signal) #type: ignore
			self._model_signals = []

		if model is not None:
			self._model_signals.append( #On reset -> re-set all expansion states according to the _expanded_items
				model.modelReset.connect(self.reset_expansion_state) #type: ignore
			)
			#TODO: also do the same (selectively) on rowsInserted and rowsRemoved?


	def mousePressEvent(self, event: QtGui.QMouseEvent) -> bool:
		#Mark event as accepted, so the selection is not changed
		# event.accept()
		if not event.button() == QtCore.Qt.MouseButton.RightButton:
			return super().mousePressEvent(event) #type: ignore
		pos = event.pos()
		index = self.indexAt(pos)
		if not index.isValid():
			return super().mousePressEvent(event) #type: ignore
		return self._try_context_menu_event(pos)


	def _try_context_menu_event(self, pos : QtCore.QPoint) -> bool:
		"""Overridden context menu event to add a custom context menu"""
		menu = QtWidgets.QMenu(self)
		index = self.indexAt(pos)
		if not index.isValid():
			return False

		# cur_field = index.data(DataclassModel.CustomDataRoles.FieldRole)
		cur_data = index.data(QtCore.Qt.ItemDataRole.EditRole)
		# if not isinstance(cur_field, Field):
		# 	log.debug(f"Selected item is not a field: {cur_field}")
		# 	return False

		# if cur_field is None:
		# 	return False

		# if hasattr(cur_field, "default"):
		# 	default_val = cur_field.default
		try:
			default_val = index.data(DataclassModel.CustomDataRoles.DefaultValueRole)
			if default_val != cur_data:
				menu.addAction(f"Set to default ({default_val})", lambda x=index: self.set_index_to_default(index))
			else:
				menu.addAction("Set to default (unchanged)", None)
		except HasNoDefaultError:
			menu.addAction("Set to default (unchanged)", None)


		menu.exec(self.mapToGlobal(pos))
		return True

	def set_index_to_default(self, index : QtCore.QModelIndex) -> None:
		"""Sets the selected item to default"""
		if not index.isValid():
			return
		try:
			model = self.model()
			model.setData(index, None, DataclassModel.CustomDataRoles.DefaultValueRole) #Set default value (found internally)
		except Exception as exception:
			log.exception(f"Error when setting to default {type(exception).__name__}: {exception}")
			raise exception

def run_example_app():
	"""Run an example using ./examples/example_dataclass.py and a dataclass treeview & model
	As well as a tableview with the same model. Note that the tableview does not support nested dataclass-attributes.
	"""
	#pylint: disable=import-outside-toplevel
	import sys

	from pyside6_utils.examples.example_dataclass import ExampleDataClass
	from pyside6_utils.widgets.delegates.dataclass_editors_delegate import \
	    DataclassEditorsDelegate

	app = QtWidgets.QApplication()
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



if __name__ == "__main__":
	formatter = logging.Formatter("[{pathname:>90s}:{lineno:<4}]  {levelname:<7s}   {message}", style='{')
	handler = logging.StreamHandler()
	handler.setFormatter(formatter)
	logging.basicConfig(
		handlers=[handler],
		level=logging.DEBUG) #Without time

	#Run example
	run_example_app()