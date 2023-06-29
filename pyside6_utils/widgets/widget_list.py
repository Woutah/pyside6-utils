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
		  	widget_type : type = QtWidgets.QLineEdit,
			widget_value_getter : typing.Callable = QtWidgets.QLineEdit.text, #How to get the value from
			widget_creation_args : dict | None = None,
			user_addable : bool = True,
			layout_orientation : QtCore.Qt.Orientation = QtCore.Qt.Orientation.Vertical,
			*args,
			**kwargs
		):

		if widget_creation_args is None:
			widget_creation_args = {}

		# super(WidgetList, self).__init__(*args, **kwargs)
		super().__init__(*args, **kwargs)

		# self.val_type = utility.get_dict_entry(item_dict, ("entry", "value_type"))
		self._layout_type = QtWidgets.QHBoxLayout \
			if layout_orientation == QtCore.Qt.Orientation.Horizontal else QtWidgets.QVBoxLayout
		self._opposite_layout_type = QtWidgets.QVBoxLayout \
			if layout_orientation == QtCore.Qt.Orientation.Horizontal else QtWidgets.QHBoxLayout

		self._add_icon = QtGui.QIcon(":/icons/actions/list-add.png")
		self._remove_icon = QtGui.QIcon(":/icons/actions/list-remove.png")


		self.setLayout(self._layout_type(self))
		self._layout_container = QtWidgets.QWidget()
		self._addable_items_layout = self._layout_type()
		self._addable_items_layout.setContentsMargins(0, 0, 0, 0)
		self._layout_container.setLayout(self._addable_items_layout)
		self.layout().addWidget(self._layout_container)


		self._add_btn = QtWidgets.QPushButton()
		self._add_btn.setIcon(self._add_icon)
		self._add_btn.setIconSize(QtCore.QSize(16, 16))

		if user_addable: #If user can add/remove widgets
			self.layout().addWidget(self._add_btn)


		self._user_addable = user_addable #Whether user can add/remove widgets
		self.widget_type = widget_type
		self.widget_creation_args = widget_creation_args
		self.widget_value_getter = widget_value_getter
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
		container_widget = QtWidgets.QWidget()
		container_widget.setLayout(self._opposite_layout_type())
		container_widget.layout().setContentsMargins(0, 0, 0, 0)
		container_widget.layout().setSpacing(0)
		self._widget_layout_containers.insert(index, container_widget)

		#Create actual widget
		new_widget = self.widget_type(**self.widget_creation_args)
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
		# self.widgetCountChanged.emit(len(self.widgets))
		self.widgetsAdded.emit([index], [new_widget])
		return new_widget

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
	widget_list.append()
	widget_list.append()
	widget_list.append()
	widget_list.append()
	layout.addWidget(widget_list)
	layout.addSpacerItem(QtWidgets.QSpacerItem(0,
		0,
		QtWidgets.QSizePolicy.Policy.Expanding,
		QtWidgets.QSizePolicy.Policy.Expanding)
	)

	widget_list._add_btn.clicked.connect(lambda: print(widget_list.get_values())) #pylint: disable=protected-access

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