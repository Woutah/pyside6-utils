"""
Treeview meant to be used with a dataclass-model, adds some extra functionality
NOTE: since this wrapper is VERY simple, it is not included in the registrars
"""


import logging
from dataclasses import Field

from PySide6 import QtCore, QtGui, QtWidgets


from pyside6_utils.models.dataclass_model import DataclassModel

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

		cur_field = index.data(DataclassModel.FIELD_ROLE)
		cur_data = index.data(QtCore.Qt.ItemDataRole.EditRole)
		if not isinstance(cur_field, Field):
			log.debug(f"Selected item is not a field: {cur_field}")
			return False

		if cur_field is None:
			return False

		if hasattr(cur_field, "default"):
			default_val = cur_field.default
			if default_val != cur_data:
				menu.addAction(f"Set to default ({default_val})", lambda x=index: self.set_index_to_default(index))
			else:
				menu.addAction("Set to default (unchanged)", None)

		menu.exec(self.mapToGlobal(pos))
		return True

	def set_index_to_default(self, index : QtCore.QModelIndex) -> None:
		"""Sets the selected item to default"""
		# index = self.currentIndex()
		if not index.isValid():
			return

		cur_field = index.data(DataclassModel.FIELD_ROLE)
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
	"""Creates a qt-app instance and runs the example
	Creates a temp file and mirrors the output to the "console", then deletes the temp file afterwards
	"""
	#pylint: disable=import-outside-toplevel
	from pyside6_utils.models.console_widget_models.console_from_file_item import ConsoleFromFileItem
	import tempfile
	import threading
	import time
	log.info("Now running an example using console from file items, the console should print a number every second")
	temp_dir = tempfile.gettempdir()
	temp_file = tempfile.NamedTemporaryFile(dir=temp_dir, mode='w', delete=False, suffix=".txt") #Delete temporary
		# file afterwards

	app = QtWidgets.QApplication([])
	test_console_model = ConsoleModel()
	console_widget = ConsoleWidget()
	console_widget.set_model(test_console_model)


	test_console_model.add_item(
		ConsoleFromFileItem(
			name="Output 1",
			path = temp_file.name,
		)
	)
	test_console_model.add_item(
		ConsoleFromFileItem(
			name="Output 2",
			path = temp_file.name,
		)
	)
	window = QtWidgets.QMainWindow()
	#Set size to 1000
	window.resize(1200, 500)
	console_widget.set_console_width_percentage(80)

	layout = QtWidgets.QVBoxLayout()
	layout.addWidget(console_widget)

	console_widget.set_console_width_percentage(80)

	#Create thread that
	def log_to_file():
		"""logs integer to file every seconds for 10 seconds"""
		for i in range(20):
			temp_file.write(f"Wrote line {i} to file {temp_file.name}\n")
			temp_file.flush()
			time.sleep(1)
	thread = threading.Thread(target=log_to_file)
	thread.start()


	window.setCentralWidget(console_widget)
	window.show()
	app.exec()
	temp_file.close()
	#remove the temp file
	os.remove(temp_file.name)



if __name__ == "__main__":
	formatter = logging.Formatter("[{pathname:>90s}:{lineno:<4}]  {levelname:<7s}   {message}", style='{')
	handler = logging.StreamHandler()
	handler.setFormatter(formatter)
	logging.basicConfig(
		handlers=[handler],
		level=logging.DEBUG) #Without time

	#Run example
	run_example_app()