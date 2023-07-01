"""
Treeview meant to be used with a dataclass-model, adds some extra functionality
NOTE: since this wrapper is VERY simple, it is not included in the registrars
"""


import logging
from dataclasses import Field

from PySide6 import QtCore, QtGui, QtWidgets

from pyside6_utils.models.dataclass_model import DataclassModel, HasNoDefaultError

log = logging.getLogger(__name__)

class DataClassTreeView(QtWidgets.QTreeView):
	"""
	Treeview meant to be used with a dataclass-model, adds some extra functionality
	Extra functionality:
		- Custom contex-menu (right-click) to set back to default
	"""

	def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
		super().__init__(parent)

		# self.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)
		# self.customContextMenuRequested.connect(self.contextMenuEvent)

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
		# index = self.currentIndex()
		if not index.isValid():
			return

		cur_field = index.data(DataclassModel.CustomDataRoles.FieldRole)
		cur_data = index.data(QtCore.Qt.ItemDataRole.EditRole)
		if not isinstance(cur_field, Field):
			log.debug(f"Selected item is not a field: {cur_field}")
			return

		if cur_field is None:
			return

		if not hasattr(cur_field, "default"):
			return

		default_val = cur_field.default
		if default_val == cur_data: #if the default value is the same as the current value, no change
			return
		model = self.model()
		model.setData(index, default_val, QtCore.Qt.ItemDataRole.EditRole)




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