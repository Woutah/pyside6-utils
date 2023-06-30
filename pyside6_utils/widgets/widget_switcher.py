"""
Wrapper aroun a QtStackedWidget to allow for easy switching between widget types using a context-menu
with descriptors for each widget type.
"""
import logging
import typing
from dataclasses import dataclass

from PySide6 import QtCore, QtGui, QtWidgets

import pyside6_utils.icons.app_resources_rc  # pylint: disable=unused-import

log = logging.getLogger(__name__)


@dataclass
class WidgetDescriptor:
	"""A descriptor for a widget type"""
	# container_widget: QtWidgets.QWidget
	widget : QtWidgets.QWidget #The actual widget
	name: str
	value_getter : typing.Callable

class WidgetSwitcher(QtWidgets.QStackedWidget):
	"""Wrapper aroun a QtStackedWidget to allow for easy switching between widget types using a context-menu
	with descriptors for each widget type. Implements a context menu and a button to show the context menu.
	Using the get_value() function, we can get the value of the current widget.
	"""

	DESCRIPTION = ("Wrapper around a QtStackedWidget to allow for easy switching between widget types using a context-menu"
		"with descriptors for each widget type. Implements a context menu and a button to show the context menu."
		"Using the get_value() function, we can get the value of the current widget.")

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self._widget_descriptors : typing.Dict[str, WidgetDescriptor]= {}
		# self._current_widget = None
		self._current_widget_descriptor = None
		self._menu = QtWidgets.QMenu(self)
		self._menu.aboutToShow.connect(self._update_menu)
		# self._menu.triggered.connect(self._menu_triggered)

		#Catch right-click events
		self.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)
		self.customContextMenuRequested.connect(self.show_menu)
		self._triangle_button = QtWidgets.QPushButton()
		self._triangle_button.setParent(self)
		self._triangle_button.setIcon(QtWidgets.QApplication.style().standardIcon(QtWidgets.QStyle.StandardPixmap.SP_TitleBarUnshadeButton))
		self._triangle_button.setFixedSize(20, 20)
		self._triangle_button.setStyleSheet("border-radius: 0px") #No border, just icon
		self._triangle_button.clicked.connect(self._context_triangle_clicked)
		self._triangle_button.show()
		self._triangle_button.raise_()

	

	def _context_triangle_clicked(self):
		cur_mouse_pos = QtGui.QCursor.pos()
		self._menu.exec(cur_mouse_pos)

	def resizeEvent(self, event: QtGui.QResizeEvent) -> None:
		super().resizeEvent(event)
		self._triangle_button.move( #Button right corner
			self.width() - self._triangle_button.width(), self.height() - self._triangle_button.height()
		)

	def showEvent(self, event: QtGui.QShowEvent) -> None:
		ret = super().showEvent(event)
		self._triangle_button.raise_()
		return ret

	def _update_menu(self):
		"""Update the menu with the available widget descriptors"""
		self._menu.clear()
		for descriptor in self._widget_descriptors.values():
			self._menu.addAction(descriptor.name, lambda x=descriptor.widget: self.setCurrentWidget(x))

	def setCurrentWidget(self, widget: QtWidgets.QWidget) -> None:
		ret = super().setCurrentWidget(widget)
		self._triangle_button.raise_()
		for descriptor in self._widget_descriptors.values(): #Get the current widget descriptor
			if descriptor.widget == widget:
				self._current_widget_descriptor = descriptor
				break

		return ret

	def setCurrentIndex(self, index: int) -> None:
		ret = super().setCurrentIndex(index)
		self._current_widget_descriptor = self._widget_descriptors[list(self._widget_descriptors.keys())[index]]
		self._triangle_button.raise_()
		return ret

	def addWidget(self) -> int:
		raise NotImplementedError("Use add_widget instead - we need to add a descriptor")
		#TODO: might be more neat to instead use the widget name as the key?

	def removeWidget(self, w: QtWidgets.QWidget) -> None:
		ret = super().removeWidget(w)

		for descriptor in self._widget_descriptors.values():
			if descriptor.widget == w:
				del self._widget_descriptors[descriptor.name]
				break
		return ret

	def add_widget(self, widget : QtWidgets.QWidget, name: str, value_getter : typing.Callable):
		"""Adds a widget to the widget switcher, with the specified name and value getter

		Args:
			widget (QtWidgets.QWidget): The widget to be added
			name (str): The name (as it should appear in the context menu)
			value_getter (typing.Callable): Used by get_value to get the current value of the widget (e.g. widget.text
				for a QLineEdit)
		"""
		self._widget_descriptors[name] = WidgetDescriptor(widget, name, value_getter)
		super().addWidget(widget)
		self._triangle_button.raise_()

	def get_value(self) -> typing.Any:
		"""Returns the value of the current widget using the value_getter passed when the widget was added"""
		if self._current_widget_descriptor is None:
			return None
		return self._current_widget_descriptor.value_getter(self._current_widget_descriptor.widget)


	def show_menu(self, pos: QtCore.QPoint):
		"""Show the context menu at the specified position"""
		self._menu.exec(self.mapToGlobal(pos))
		self._triangle_button.raise_()




def run_example_app():
	"""Runs an example of this widget"""
	#pylint: disable=import-outside-toplevel
	import sys

	from pyside6_utils.widgets.widget_list import WidgetList
	app = QtWidgets.QApplication(sys.argv)

	example_window = QtWidgets.QMainWindow()
	central_widget = QtWidgets.QWidget()
	example_window.setCentralWidget(central_widget)
	layout = QtWidgets.QVBoxLayout()
	central_widget.setLayout(layout)

	def widget_factory(*_):
		test_widget = WidgetSwitcher()
		test_widget.add_widget(QtWidgets.QPushButton("Test1"), "Button1", lambda x: "None")
		test_widget.add_widget(QtWidgets.QPushButton("Test2"), "Button2", lambda x: "None")
		test_widget.add_widget(QtWidgets.QLineEdit("Test3"), "LineEdit", lambda x: x.text())
		#Show left/right arrow buttons to switch between widgets

		return test_widget
	
	widget_list = WidgetList(widget_factory, lambda x: x.get_value(), user_addable=True)

	widget_list.widgetsAdded.connect(lambda x, y: log.info(widget_list.get_values()))

	layout.addWidget(widget_list)
	layout.addSpacerItem(
		QtWidgets.QSpacerItem(0, 0, QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Expanding)
	)


	example_window.show()

	app.exec()


if __name__ == "__main__":
	formatter = logging.Formatter("[{pathname:>90s}:{lineno:<4}]  {levelname:<7s}   {message}", style='{')
	handler = logging.StreamHandler()
	handler.setFormatter(formatter)
	logging.basicConfig(
		handlers=[handler],
		level=logging.DEBUG) #Without time
	logging.getLogger().setLevel(logging.DEBUG)

	log.info("Now running test app for widget list")
	run_example_app()