"""
Implements a widget that allows the user to add/remove widgets of a certain type.
"""
import logging
import typing
from PySide6 import QtCore, QtGui, QtWidgets
import pyside6_utils.icons.app_resources_rc #pylint: disable=unused-import

log = logging.getLogger(__name__)

class WidgetList(QtWidgets.QWidget):
	"""
	Create a widget to which we can add/remove instances of the same widget type using a +-button at the end of the
	widget list and a - button next to each widget.
	"""
	DESCRIPTION = ("Create a widget to which we can add/remove instances of a user-passed widget type using a +-button at "
		"the end of the widget list. We can remove widgets by pressing the '-' button next to each widget.")
	widgetsAdded = QtCore.Signal(list, list) #indexes of widget in list, widget list
	widgetsRemoved = QtCore.Signal(list, list) #(previous) indexes of widget in list, widget list

	def __init__(self, #pylint: disable=keyword-arg-before-vararg
		  	widget_source : type | typing.Callable[['WidgetList'], QtWidgets.QWidget] = QtWidgets.QLineEdit,
			widget_value_getter : typing.Callable = QtWidgets.QLineEdit.text, #How to get the value from
			widget_value_setter : typing.Callable = QtWidgets.QLineEdit.setText, #How to set the value of
			widget_creation_args : dict | None = None, #If widget_source is a type, pass these arguments to the constructor
			user_addable : bool = True,
			layout_orientation : QtCore.Qt.Orientation = QtCore.Qt.Orientation.Vertical,
			*args,
			**kwargs
		):
		"""A list of widgets, we can add/remove widgets of the same type using a +-button at the end of the widget list
		using either a factory or a type (with creation arguments)

		Args:
			widget_source (type | typing.Callable[['WidgetList'], QtWidgets.QWidget], optional): The type of widget to
				add to the list, or a function that returns a widget (factory). Defaults to QtWidgets.QLineEdit.
			widget_value_getter (typing.Callable, optional): The function to call on the widgets to get the value,
				is used by the get_value() function to get the list of current values. Defaults to QtWidgets.QLineEdit.text.
			widget_value_setter (typing.Callable, optional): The function to call on the widgets to set the value,
				is used by the set_value() function to set the values of the widgets. Defaults to QtWidgets.QLineEdit.setText.
			widget_creation_args (dict | None, optional): The arguments to pass to the constructor of the widget, if
				widget_source is a type. Defaults to None.
			user_addable (bool, optional): Whether the user can add/remove widgets. Defaults to True.
			layout_orientation (QtCore.Qt.Orientation, optional): _description_. Defaults to QtCore.Qt.Orientation.Vertical.

		Raises:
			TypeError: _description_
		"""

		if widget_creation_args is None:
			widget_creation_args = {}

		super().__init__(*args, **kwargs)

		self._layout_type = QtWidgets.QHBoxLayout \
			if layout_orientation == QtCore.Qt.Orientation.Horizontal else QtWidgets.QVBoxLayout
		self._opposite_layout_type = QtWidgets.QVBoxLayout \
			if layout_orientation == QtCore.Qt.Orientation.Horizontal else QtWidgets.QHBoxLayout

		self._add_icon = QtGui.QIcon(":/icons/actions/list-add.png")
		self._remove_icon = QtGui.QIcon(":/icons/actions/list-remove.png")



		self.setLayout(self._layout_type(self))
		self.layout().setContentsMargins(0, 0, 0, 0)
		self._layout_container = QtWidgets.QWidget()
		self._layout_container.setBaseSize(0, 0)
		self._addable_items_layout = self._layout_type()
		self._addable_items_layout.setContentsMargins(0, 0, 0, 0)
		self._addable_items_layout.setSpacing(0)
		self._layout_container.setLayout(self._addable_items_layout)
		self.layout().addWidget(self._layout_container)


		self._add_btn = QtWidgets.QPushButton(self)
		self._add_btn.setIcon(self._add_icon)
		self._add_btn.setIconSize(QtCore.QSize(16, 16))
		self.layout().setSpacing(0)

		if user_addable: #If user can add/remove widgets
			self.layout().addWidget(self._add_btn)


		self._user_addable = user_addable #Whether user can add/remove widgets

		self.widget_type = None
		self.widget_factory = None
		if isinstance(widget_source, type): #If widget_source is a type
			self.widget_type = widget_source
		elif isinstance(widget_source, typing.Callable): #If widget_source is a function
			self.widget_factory = widget_source
		else:
			raise TypeError(f"widget_source must be a type or a function (factory), not {type(widget_source)}")

		self.widget_creation_args = widget_creation_args
		self.widget_value_getter = widget_value_getter
		self.widget_value_setter = widget_value_setter
		self.widgets : typing.List[QtWidgets.QWidget] = [] #Public - makes it easier to set/get values
		self._widget_layout_containers : typing.List[QtWidgets.QWidget] = [] #Contains the container widgets with the
			# widget to be added/removed and a '-' button

		self._add_btn.clicked.connect(self._append_btn_clicked)



	def set_widgetcount(self, new_count : int):
		"""Set the new widget-count. Keeps appending or popping widgets until the widget count is equal to
		the specified count
		"""
		if new_count == len(self.widgets): #If nothing changed
			return
		new_count = max(0 , new_count)
		self.blockSignals(True)
		while len(self.widgets) > new_count:
			self.pop()
		while len(self.widgets) < new_count:
			self.append()

		self.blockSignals(False)
		# self.widgetCountChanged.emit(len(self.widgets))

	def get_values(self, *args, **kwargs):
		"""Get the values of all widgets using the provided widget_value_getter-function and return a list of values"""
		return [self.widget_value_getter(widget, *args, **kwargs) for widget in self.widgets]

	def get_values_using_getter(self, getter : typing.Callable, *args, **kwargs):
		"""Get the values of all widgets using the provided getter-function and return a list of values"""
		return [getter(widget, *args, **kwargs) for widget in self.widgets]

	def set_values(self, values : list, delete_superfluous_widgets : bool = True, *args, **kwargs): #pylint: disable=keyword-arg-before-vararg
		"""Set the values of all widgets using the provided widget_value_setter-function.
		if delete_superfluous_widgets is True, remove widgets if the number of values is less than the number of widgets.
		"""
		self.set_values_using_setter(self.widget_value_setter, values, delete_superfluous_widgets, *args, **kwargs)

	def set_values_using_setter(self, #pylint: disable=keyword-arg-before-vararg
			setter : typing.Callable,
			values : list,
			delete_superfluous_widgets : bool = True,
			*args,
			**kwargs
		):
		"""Set the values of all widgets using the provided setter-function.
		if delete_superfluous_widgets is True, remove widgets if the number of values is less than the number of widgets.
		"""
		if not delete_superfluous_widgets and len(values) > len(self.widgets):
			pass
		else:
			self.set_widgetcount(len(values))
		for widget, value in zip(self.widgets, values):
			setter(widget, value, *args, **kwargs)


	def _append_btn_clicked(self, *_):
		"""If user presses append button"""
		self.append()

	def remove_widget_by_object(self, widget : QtWidgets.QWidget):
		"""Remove the specified widget from the list"""
		index = self.widgets.index(widget) #Get index of widget
		self.remove_widget(index)

	def remove_widget(self, index : int):
		"""Remove the widget at the specified index"""
		if index < 0 or index >= len(self.widgets):
			raise ValueError(f"Cannot remove widget at index {index} - widget count is {len(self.widgets)}")
		self._addable_items_layout.removeWidget(self._widget_layout_containers[index]) #Remove from layout
		self._widget_layout_containers[index].setParent(None) #type:ignore #Set parent to None (delete widget)
		self.widgets[index].setParent(None) #type:ignore #Set parent to None (delete widget)
		del self._widget_layout_containers[index] #Remove from list
		del self.widgets[index] #Remove from list
		self.widgetsRemoved.emit([index], [self.widgets]) #Emit signal




	def insert_widget(self, index : int):
		"""Insert a widget at the specified index"""
		if index < 0 or index > len(self.widgets):
			raise ValueError(f"Cannot insert widget at index {index} - widget count is {len(self.widgets)}")

		#Set the new sizehint to be the same as the previous sizehint, but with the new widget added
		# self._layout_container.sizeHi(QtCore.QSize(self._layout_container.sizeHint().width(),
		container_widget = QtWidgets.QWidget()
		container_widget.setLayout(self._opposite_layout_type())
		container_widget.layout().setContentsMargins(0, 0, 0, 0)
		container_widget.layout().setSpacing(0)
		self._widget_layout_containers.insert(index, container_widget)

		#Create actual widget
		if self.widget_factory is not None:
			new_widget = self.widget_factory(self)
		elif self.widget_type is not None:
			new_widget = self.widget_type(**self.widget_creation_args)
		else:
			raise RuntimeError("Both widget_factory and widget_type are None - this should not happen")

		self.widgets.insert(index, new_widget)
		container_widget.layout().addWidget(new_widget)


		#Create a '-' button
		remove_btn = QtWidgets.QPushButton()
		remove_btn.setIcon(self._remove_icon)
		remove_btn.setIconSize(QtCore.QSize(16, 16))
		remove_btn.setFixedSize(QtCore.QSize(25, 25))
		remove_btn.clicked.connect(lambda x=new_widget: self.remove_widget_by_object(new_widget))
		container_widget.layout().addWidget(remove_btn)

		self._addable_items_layout.insertWidget(index, container_widget) #Take
		self.updateGeometry()
		return new_widget

	# def sizeHint(self) -> QtCore.QSize:
	# 	cur_hint = self._add_btn.minimumSizeHint()

	# 	for item in self._widget_layout_containers:
	# 		if self._layout_type == QtWidgets.QHBoxLayout:
	# 			cur_hint.setWidth(cur_hint.width() + item.minimumSizeHint().width())
	# 			cur_hint.setHeight(max(cur_hint.height(), item.minimumSizeHint().height()))
	# 		elif self._layout_type == QtWidgets.QVBoxLayout:
	# 			cur_hint.setHeight(cur_hint.height() + item.minimumSizeHint().height())
	# 			cur_hint.setWidth(max(cur_hint.width(), item.minimumSizeHint().width()))

	# 	min_width = max(cur_hint.width(), self._layout_container.minimumSizeHint().width())
	# 	self.setMaximumHeight(cur_hint.height())
	# 	return cur_hint

	# 	return self.minimumSizeHint()
	# 	# return super().sizeHint()

	# def minimumSizeHint(self) -> QtCore.QSize:
	# 	cur_hint = self._add_btn.minimumSizeHint()

	# 	for item in self._widget_layout_containers:
	# 		if self._layout_type == QtWidgets.QHBoxLayout:
	# 			cur_hint.setWidth(cur_hint.width() + item.minimumSizeHint().width())
	# 			cur_hint.setHeight(max(cur_hint.height(), item.minimumSizeHint().height()))
	# 		elif self._layout_type == QtWidgets.QVBoxLayout:
	# 			cur_hint.setHeight(cur_hint.height() + item.minimumSizeHint().height())
	# 			cur_hint.setWidth(max(cur_hint.width(), item.minimumSizeHint().width()))

	# 	# min_width = max(cur_hint.width(), self._layout_container.minimumSizeHint().width())

	# 	return cur_hint
		# return QtCore.QSize(max(min_width, cur_hint.width()), cur_hint.height() + height_addition)

	def append(self):
		"""Appends a widget to the end of the layout"""
		self.insert_widget(len(self.widgets))

	def pop(self):
		"""Removes the last widget from the layout"""
		self.remove_widget(len(self.widgets)-1)



def run_example_app():
	"""Runs an example of this widget"""
	#pylint: disable=import-outside-toplevel
	import sys
	app = QtWidgets.QApplication(sys.argv)

	example_window = QtWidgets.QMainWindow()
	central_widget = QtWidgets.QWidget()
	example_window.setCentralWidget(central_widget)
	layout = QtWidgets.QVBoxLayout()
	central_widget.setLayout(layout)

	widget_list = WidgetList() #By default, use line-edit
	layout.addWidget(widget_list)

	print(f"Size before appending: {widget_list.sizeHint()}, minsize = {widget_list.minimumSize()}")
	widget_list.append()
	widget_list.append()
	widget_list.append()
	widget_list.append()

	print(f"Size after appending: {widget_list.sizeHint()}, minsize = {widget_list.minimumSize()}")
	layout.addSpacerItem(QtWidgets.QSpacerItem(0,
		0,
		QtWidgets.QSizePolicy.Policy.Expanding,
		QtWidgets.QSizePolicy.Policy.Expanding)
	)

	widget_list._add_btn.clicked.connect(lambda: print(f"{widget_list.get_values()}")) #pylint: disable=protected-access
	widget_list._add_btn.clicked.connect(lambda: print(f"Size: {widget_list.size()}")) #pylint: disable=protected-access
	widget_list._add_btn.clicked.connect(lambda: print(f"Sizehint: {widget_list.sizeHint()}")) #pylint: disable=protected-access
	widget_list._add_btn.clicked.connect(lambda: print(f"Minsizehint: {widget_list.minimumSizeHint()}")) #pylint: disable=protected-access

	example_window.show()
	print(f"Size after showing: {widget_list.sizeHint()}")
	widget_list.append()
	widget_list.append()
	print(f"Size after appending: {widget_list.sizeHint()}")

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