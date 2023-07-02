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
	value_setter : typing.Callable

class WidgetSwitcher(QtWidgets.QWidget):
	"""Wrapper aroun a QtStackedWidget to allow for easy switching between widget types using a context-menu
	with descriptors for each widget type. Implements a context menu and a button to show the context menu.
	Using the get_value() function, we can get the value of the current widget.
	"""

	DESCRIPTION = ("Wrapper around a QtStackedWidget to allow for easy switching between widget types using a context-menu"
		"with descriptors for each widget type. Implements a context menu and a button to show the context menu."
		"Using the get_value() function, we can get the value of the current widget.")

	currentChanged = QtCore.Signal(int)
	widgetRemoved = QtCore.Signal(int)


	def __init__(self, *args, inline_button = True, **kwargs):
		super().__init__(*args, **kwargs)
		self._widget_descriptors : typing.Dict[str, WidgetDescriptor]= {}
		# self._current_widget = None
		self._current_widget_descriptor = None
		self._menu = QtWidgets.QMenu(self)
		self._menu.aboutToShow.connect(self._update_menu)
		# self._menu.triggered.connect(self._menu_triggered)

		#Create the wrapped stacked widget
		self.setLayout(QtWidgets.QHBoxLayout())
		self._stack_widget = QtWidgets.QStackedWidget()
		self.layout().addWidget(self._stack_widget)
		self.layout().setContentsMargins(0, 0, 0, 0)
		self.layout().setSpacing(0)
		self._stack_widget.currentChanged.connect(self.currentChanged)
		self._stack_widget.widgetRemoved.connect(self.widgetRemoved)
		self._stack_widget.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)
		self._stack_widget.customContextMenuRequested.connect(self.show_menu)

		#Catch right-click events
		self.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)
		self.customContextMenuRequested.connect(self.show_menu)
		self._triangle_button = QtWidgets.QPushButton()
		self._triangle_button.setParent(self)
		self._triangle_button.setIcon(
			QtWidgets.QApplication.style().standardIcon(QtWidgets.QStyle.StandardPixmap.SP_TitleBarUnshadeButton))
		self._triangle_button.clicked.connect(self._context_triangle_clicked)
		self._triangle_button.show()
		self._triangle_button.raise_()
		if inline_button:
			self._triangle_button.setFixedWidth(18)
			self._triangle_button.setSizePolicy(QtWidgets.QSizePolicy.Policy.Fixed, QtWidgets.QSizePolicy.Policy.Expanding)
			self.layout().addWidget(self._triangle_button)
		else: #If not inline, write the button on top of the widget in the bottom right corner
			self._triangle_button.setFixedSize(8, 8)
			self._triangle_button.setStyleSheet("border-radius: 0px") #No border, just icon

		self._button_inline = inline_button
		self.fix_layout()





	def _context_triangle_clicked(self):
		cur_mouse_pos = QtGui.QCursor.pos()
		self._menu.exec(cur_mouse_pos)

	def fix_layout(self):
		"""Fixes the layout of the widget switcher, so that the button is in the correct position"""
		if not self._button_inline:
			self._triangle_button.move( #Button right corner
				self.width() - self._triangle_button.width(), self.height() - self._triangle_button.height()-1
			)

	def resizeEvent(self, event: QtGui.QResizeEvent) -> None:
		super().resizeEvent(event)
		self.fix_layout()

	def showEvent(self, event: QtGui.QShowEvent) -> None:
		ret = super().showEvent(event)
		self._triangle_button.raise_()
		self.fix_layout()
		# self.setMinimumSize(self.minimumSizeHint())
		return ret

	def _update_menu(self):
		"""Update the menu with the available widget descriptors"""
		self._menu.clear()
		for descriptor in self._widget_descriptors.values():
			self._menu.addAction(descriptor.name, lambda x=descriptor.widget: self.setCurrentWidget(x))

	def setCurrentWidget(self, widget: QtWidgets.QWidget) -> None: #pylint: disable=invalid-name
		"""Sets the current widget to the specified widget and updates the current widget descriptor"""
		ret = self._stack_widget.setCurrentWidget(widget)
		self._triangle_button.raise_()
		for descriptor in self._widget_descriptors.values(): #Get the current widget descriptor
			if descriptor.widget == widget:
				self._current_widget_descriptor = descriptor
				break
		self.fix_layout()
		# self.setMinimumSize(self.minimumSizeHint())
		self.updateGeometry()
		return ret

	def setCurrentIndex(self, index: int) -> None: #pylint: disable=invalid-name
		"""Set the current index of the stacked widget and update descriptor"""
		ret = self._stack_widget.setCurrentIndex(index)
		self._current_widget_descriptor = self._widget_descriptors[list(self._widget_descriptors.keys())[index]]
		self._triangle_button.raise_()
		self.fix_layout()
		return ret

	def addWidget(self) -> int: #pylint: disable=invalid-name
		"""Addwidget is not supported, use add_widget instead"""
		raise NotImplementedError("Use add_widget instead - we need to add a descriptor")
		#TODO: might be more neat to instead use the widget name as the key?

	def removeWidget(self, widget : QtWidgets.QWidget) -> None: #pylint: disable=invalid-name
		"""Remove widget from stacked widget and remove the corresponding descriptor"""
		ret = self._stack_widget.removeWidget(widget)

		for descriptor in self._widget_descriptors.values():
			if descriptor.widget == widget:
				del self._widget_descriptors[descriptor.name]
				break
		self.fix_layout()
		return ret

	# def sizeHint(self) -> QtCore.QSize:
	# 	return self.minimumSizeHint()

	# def minimumSizeHint(self) -> QtCore.QSize:
	# 	"""Return the min size policy of the currently selected widget"""

	# 	cur_widget = self._stack_widget.currentWidget()
	# 	cur_size_hint = cur_widget.minimumSizeHint()
	# 	if self._button_inline: #If button part of the size:
	# 		cur_size_hint.setWidth(cur_size_hint.width() + self._triangle_button.width())

	# 	return cur_size_hint

	def add_widget(self,
			widget : QtWidgets.QWidget,
			name: str,
			value_getter : typing.Callable,
			value_setter : typing.Callable
		):
		"""Adds a widget to the widget switcher, with the specified name and value getter

		Args:
			widget (QtWidgets.QWidget): The widget to be added
			name (str): The name (as it should appear in the context menu)
			value_getter (typing.Callable): Used by get_value to get the current value of the widget (e.g. widget.text
				for a QLineEdit)
			value_setter (typing.Callable): Used by set_value to set the current value of the widget (e.g. widget.setText
				for a QLineEdit)
		"""
		self._widget_descriptors[name] = WidgetDescriptor(widget, name, value_getter, value_setter)
		self._stack_widget.addWidget(widget)
		self._triangle_button.raise_()
		self.fix_layout()

	def get_value(self) -> typing.Any:
		"""Returns the value of the current widget using the value_getter passed when the widget was added"""
		# if self._current_widget_descriptor is None:
		# 	return None
		current_index = self._stack_widget.currentIndex()
		if current_index == -1:
			return None
		self._current_widget_descriptor = self._widget_descriptors[list(self._widget_descriptors.keys())[current_index]]
		return self._current_widget_descriptor.value_getter(self._current_widget_descriptor.widget)

	def set_value(self, value : typing.Any) -> typing.Any:
		"""
		Automatically finds the first widget for which the value can be set and sets the value using the value_setter
		NOTE/TODO: at the moment, this is not very robust - it will just try to set the value for each widget in the order
		they were added, and will raise an exception if it cannot set the value for any of them.

		TODO: maybe use typehint-parser based on instance? e.g. [1, 2, 3] -> typing.List[int], and base the
		widget-selection on that?
		"""
		could_set = -1
		for i, descriptor in enumerate(self._widget_descriptors.values()):
			try: #Find the first widget for which we can set the value
				descriptor.value_setter(descriptor.widget, value)
				could_set = i
				self.setCurrentWidget(descriptor.widget) #Switch to that widget
				break
			except Exception: #pylint: disable=broad-except
				continue
		if could_set == -1:
			raise ValueError("Could not set the passed value for any of the widgets")

	def count(self) -> int:
		"""Returns the number of widgets"""
		return self._stack_widget.count()

	def currentIndex(self) -> int:# pylint: disable=invalid-name
		"""Returns the index of the current widget"""
		return self._stack_widget.currentIndex()

	def currentWidget(self) -> QtWidgets.QWidget: #pylint: disable=invalid-name
		"""Returns the current widget"""
		return self._stack_widget.currentWidget()

	def indexOf(self, widget: QtWidgets.QWidget) -> int: #pylint: disable=invalid-name
		"""Returns the index of the specified widget"""
		return self._stack_widget.indexOf(widget)

	# def insertWidget(self, index: int, widget: QtWidgets.QWidget) -> None: #TODO: implement



	def set_current_value(self, value : typing.Any) -> None:
		"""Sets the value of the current widget using the value_setter passed when the widget was added"""
		if self._current_widget_descriptor is None:
			return
		self._current_widget_descriptor.value_setter(self._current_widget_descriptor.widget, value)

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

	print(isinstance(int(3), typing.List))

	def combobox_setter(combobox : QtWidgets.QComboBox, val : str): #Make compatible with set_value
		if combobox.findData(val) == -1:
			if combobox.findText(val) == -1:
				raise ValueError(f"Could not find value {val} in combobox")
			else:
				combobox.setCurrentText(val)
		else:
			combobox.setCurrentIndex(combobox.findData(val))
		# combobox.setCurrentText(val)


	def widget_factory(*_):
		test_widget = WidgetSwitcher()
		test_widget.add_widget(QtWidgets.QPushButton("Button"), "Button", lambda x: "None", lambda x: None)
		combobox = QtWidgets.QComboBox()
		combobox.addItems(["ComboBoxOption1", "ComboBoxOption2", "ComboBoxOption3"])
		test_widget.add_widget(combobox, "Combobox", lambda x: x.currentText(), combobox_setter)
		test_widget.add_widget(
			QtWidgets.QLineEdit("LineEdit"), "LineEdit", lambda x: x.text(), lambda widget, val: widget.setText(val))
		#Show left/right arrow buttons to switch between widgets

		return test_widget

	widget_list = WidgetList(widget_factory,
		widget_value_getter=lambda x: x.get_value(),
		widget_value_setter=WidgetSwitcher.set_value,
		user_addable=True
	)

	widget_list.set_values(["test1", "ComboBoxOption2", "LineEdit"])

	widget_list.widgetsAdded.connect(lambda x, y: log.info(widget_list.get_values()))

	layout.addWidget(widget_list)
	# layout.addSpacerItem(
	# 	QtWidgets.QSpacerItem(0, 0, QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Expanding)
	# )


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