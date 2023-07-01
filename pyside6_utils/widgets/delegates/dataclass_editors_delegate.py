"""Implements the delegate for a """
import logging
import math
import types
import typing
from datetime import datetime
from numbers import Integral, Real
from typing import Union

from PySide6 import QtCore, QtWidgets
import PySide6.QtCore
import PySide6.QtWidgets

from pyside6_utils.widgets.widget_switcher import WidgetSwitcher
from pyside6_utils.widgets.widget_list import WidgetList
from pyside6_utils.utility.constraints import Interval, Options, StrOptions, ConstrainedList, _InstancesOf, make_constraint, _Constraint, _NoneConstraint
from pyside6_utils.models.dataclass_model import DataclassModel

log = logging.getLogger(__name__)



def combobox_setter(combobox : QtWidgets.QComboBox, val : typing.Any):
	"""
	Combobox-setter function that throws an exception if the value is not found in the combobox (either in data or text)

	Args:
		combobox (QtWidgets.QComboBox): The combobox
		val (typing.Any): The new value
	"""
	if combobox.findData(val) == -1: #First try to set by data
		if combobox.findText(val) == -1: #Then by text
			raise ValueError(f"Could not find value {val} in combobox")
		else:
			combobox.setCurrentText(val)
	else:
		combobox.setCurrentIndex(combobox.findData(val))

class DataclassEditorsDelegate(QtWidgets.QStyledItemDelegate):
	"""
	Custom delegate made especially for the DataClassModel. This delegate allows for editing of various datatypes.
	TODO: maybe use a factory instead for the editors
	"""
	#Custom delegate that allows for editing of different data types of DataClassModel
	def __init__(self, background_color : QtCore.Qt.GlobalColor = QtCore.Qt.GlobalColor.white,  *args, **kwargs) -> None: #pylint: disable=unused-argument
		super().__init__()
		self._frameless_window = QtWidgets.QMainWindow()
		self._frameless_window.setWindowFlags(QtCore.Qt.WindowType.FramelessWindowHint | QtCore.Qt.WindowType.WindowStaysOnTopHint)

		# #Transparent background
		# self._frameless_window.setAttribute(QtCore.Qt.WidgetAttribute.WA_TranslucentBackground, True)

		self._background_color = background_color
		self._parent = None

		palette = self._frameless_window.palette()
		palette.setColor(self._frameless_window.backgroundRole(), self._background_color)
		self._frameless_window.setPalette(palette)
		# self._frameless_window.resizeEvent = self._frameless_window_resize_event

	# def _frameless_window_resize_event(self, event):
	# 	print("RESIZE EVENT")
	# 	# self._frameless_window.resizeEvent(event)		
	# 	new_size = self._frameless_window.centralWidget().sizeHint()
	# 	self._frameless_window.resize(new_size)

	def get_editor_from_constraints(self,
			constraint : typing.List[_Constraint],
			metadata,
			parent
		) -> typing.Tuple[QtWidgets.QWidget, typing.Callable, typing.Callable]:
		"""
		Get the editor from the passed constraint (sklearn-constraint)

		Args:
			constraint (sklearn-constraint): The constraint to get the editor for
				The possible constraints are:
					- "array-like"
					- "sparse matrix"
					- "random_state"
					- callable
					- None
					- type #Type-enforcing constraint
					- (Interval, StrOptions, Options, HasMethods)
					- "boolean"
					- "verbose"
					- "missing_values"
					- "cv_object"
			metadata (dict): The metadata of the field
			parent (QtWidgets.QWidget): The parent widget to use for the editor

		Returns:
			QtWidgets.QWidget: The editor widget
			Callable: The getter function to get the value from the editor
			Callable: The setter function to set the value to the editor

		"""
		if isinstance(constraint, list): #If the main list of constraints,
			editor_list : typing.List[typing.Tuple[QtWidgets.QWidget, typing.Callable, typing.Callable]]= []
			constraint_list = constraint

			for cur_constraint in constraint_list:
				cur_editor, cur_getter, cur_setter = self.get_editor_from_constraints(cur_constraint, metadata, parent)
				if cur_editor is not None:
					editor_list.append((cur_editor, cur_getter, cur_setter))
			if len(editor_list) == 0:
				# return None, lambda *_: None, lambda *_: None 
				raise ValueError(f"Could not create editor for constraints {constraint} - no editor found")
			elif len(editor_list) == 1:
				return editor_list[0]
			else:
				#Create a WidgetSwitcher with the editors as widgets
				switcher = WidgetSwitcher(parent=parent)
				for cur_constraint, (cur_editor, cur_getter, cur_setter) in zip(constraint_list, editor_list):
					cur_editor.setParent(switcher) #Set the parent to the switcher
					switcher.add_widget(cur_editor, str(cur_constraint).capitalize(), cur_getter, cur_setter)
				return switcher, WidgetSwitcher.get_value, WidgetSwitcher.set_value

		elif isinstance(constraint, ConstrainedList):
			#Retrieve getter/setter and set the constraints-widget-getter as the factory for the list
			widget_instance, getter, setter = self.get_editor_from_constraints(constraint.constraints, metadata, parent)
			widget_list = WidgetList(
				lambda widget_list: self.get_editor_from_constraints(constraint.constraints, metadata, widget_list)[0], #TODO: what if None? #type: ignore
				widget_value_getter=getter,
				widget_value_setter=setter,
				parent=parent,
			)
			return widget_list, WidgetList.get_values, WidgetList.set_values
		elif constraint is None or constraint == "None" or constraint == "none" or\
				isinstance(constraint, _NoneConstraint):
			label = QtWidgets.QLabel("None")
			#Fill background with default
			label.setAutoFillBackground(True)
			parent_palette = parent.palette()
			#Set background color to white:
			parent_palette.setColor(label.backgroundRole(), self._background_color) 
			label.setPalette(parent_palette)
			# label.setPalette(parent.palette())
			return label, lambda *_: None, lambda *_: None
		elif isinstance(constraint, _InstancesOf): #If type-enforcing constraint
			the_type = constraint.type
			if the_type == bool or the_type == "boolean":
				editor = QtWidgets.QComboBox(parent)
				editor.addItem("True", True)
				editor.addItem("False", False)
				return editor, QtWidgets.QComboBox.currentData, combobox_setter
			elif the_type == datetime:
				editor = QtWidgets.QDateTimeEdit(parent)
				editor.setCalendarPopup(True)
				return editor, lambda widget : QtWidgets.QDateTimeEdit.dateTime(widget).toPython(), QtWidgets.QDateTimeEdit.setDateTime
			elif issubclass(the_type, Integral): #If int or (other subclass of) integral
				editor = QtWidgets.QSpinBox(parent)
				editor.setMaximum(9999999)
				editor.setMinimum(-9999999)
				return editor, QtWidgets.QSpinBox.value, QtWidgets.QSpinBox.setValue
			elif issubclass(the_type, Real): #If float or (other subclass of) real
				editor = QtWidgets.QDoubleSpinBox(parent)
				editor.setDecimals(4) #TODO: make this user-selectable?
				editor.setMinimum(-9999999)
				editor.setMaximum(9999999)
				return editor, QtWidgets.QDoubleSpinBox.value, QtWidgets.QDoubleSpinBox.setValue
		# elif isinstance(constraint, ConstrainedList):
		elif isinstance(constraint, Interval):
			if issubclass(constraint.type, Integral):
				editor = QtWidgets.QSpinBox(parent)
				editor_type = QtWidgets.QSpinBox
			else:
				editor = QtWidgets.QDoubleSpinBox(parent)
				editor_type = QtWidgets.QDoubleSpinBox
			if constraint.right:
				editor.setMaximum(constraint.right)
			if constraint.left:
				editor.setMinimum(constraint.left)

			#Set decimals by max-min/1000 +2 (e.g. if max-min = 1000, set decimals to 1+2 = 3)
			if isinstance(editor, QtWidgets.QDoubleSpinBox):
				if constraint.right is not None and constraint.left is not None:
					editor.setDecimals(
						max(0, -int(math.floor(math.log10(abs(constraint.right - constraint.left)/1000)))) + 2
					)
					editor.setSingleStep((constraint.right - constraint.left)/100)
				else:
					editor.setDecimals(2)

			return editor, editor_type.value, editor_type.setValue
		elif isinstance(constraint, Options) or isinstance(constraint, StrOptions):
			editor = QtWidgets.QComboBox(parent)
			all_options = list(constraint.options)
			all_options = sorted(all_options, key=lambda x: str(x).lower()) #Sort options alphabetically

			for option in all_options:
				editor.addItem(str(option), option) #Add the option as data

			try:
				constraints_help_dict = metadata["constraints_help"]
				for i, option in enumerate(all_options):
					if str(option) in constraints_help_dict: #If key-help is defined, add it as tooltip
						editor.setItemData(i, constraints_help_dict[option], QtCore.Qt.ItemDataRole.ToolTipRole)
			except KeyError:
				pass
			return editor, QtWidgets.QComboBox.currentData, combobox_setter
		else:
			log.debug(f"Could not create editor for constraint {constraint} - returning None-editor")

		# return None, lambda *_: None, lambda *_: None
		return QtWidgets.QLineEdit(parent), QtWidgets.QLineEdit.text, QtWidgets.QLineEdit.setText
		# raise ValueError(f"Could not create editor for constraint {constraint} - no editor found")



	@staticmethod
	def get_constraints_from_typehint(typehint) -> typing.List[_Constraint] | None:
		"""Retrieve the constraints-objects using the passed typehint.
		E.g.: typing.Union[None, int] -> [_NoneConstraint, _InstancesOf(int)]

		"""
		constraints = None
		if typehint == type(None): #Nonetype = None constraint
			constraints = [make_constraint(None)]
		elif isinstance(typehint, type):
			return [make_constraint(typehint)]
		elif isinstance(typehint, types.UnionType) or \
				typing.get_origin(typehint) == typing.Union:
			type_list = list(typing.get_args(typehint))
			constraints = []
			for cur_type in type_list:
				new_constraint = DataclassEditorsDelegate.get_constraints_from_typehint(cur_type)
				if new_constraint:
					constraints.extend(new_constraint)
		elif isinstance(typehint, typing.List):
			# constraints = [ConstrainedList(DataclassEditorsDelegate.get_constraints_from_typehint(typehint[0]))]
			constraints = [ConstrainedList(DataclassEditorsDelegate.get_constraints_from_typehint(cur_type)) for cur_type in typehint]
		elif typing.get_origin(typehint) == typing.Literal: #pylint: disable=comparison-with-callable
			constraints = [Options(typing.Any, set(typehint.__args__))] #TODO: maybe check if all the same type instead
				# of typing.Any?
		return constraints

	def sizeHintChanged(index):
		print("SIZE HINT CHANGED")

	def updateEditorGeometry(self, editor, option, index): #pylint: disable=unused-argument
		if self._frameless_window:
			min_size = editor.minimumSizeHint()
			desired_size = editor.sizeHint()
			# print(f"Min size: {min_size}, desired size: {desired_size}, option rect: {option.rect}")

			min_size.setWidth(max(min_size.width(), option.rect.width()))
			min_size.setHeight(max(min_size.height(), option.rect.height()))
			self._frameless_window.resize(min_size)

			if self._parent:
				global_pos = self._parent.mapToGlobal(option.rect.topLeft())
				self._frameless_window.move(global_pos)
				self._frameless_window.raise_()




	def createEditor(self, parent, option, index):
		field = index.data(QtCore.Qt.ItemDataRole.UserRole + 1) #TODO: maybe create a more descriptive role?

		editor = None
		entry_type = None
		metadata = None
		constraints = None
		if field:
			metadata = field.metadata
			entry_type = field.type
			constraints = metadata.get("constraints", None)
		self._parent = parent

		if constraints:
			constraints = [make_constraint(constraint) for constraint in constraints]
		elif constraints is None and entry_type is not None: #If no constraints, set constraints to current type
			#Get used types from field.type (e.g. typing.Literal, typing.Union, typing.List, typing.Dict, typing.Tuple,
			# typing.Callable, typing.Optional, typing.Any, typing.ClassVar, typing.Final, typing.TypeVar,
			# typing.Generic, typing.Protocol)
			try:
				constraints = DataclassEditorsDelegate.get_constraints_from_typehint(entry_type)
			except Exception as exception: #pylint: disable=broad-except
				log.warning(f"Could not get constraints from typehint {entry_type} - {exception}")
				constraints = None
		else:
			log.warning(f"Could not deduce constraints from neither field nor typehint of field {field}")


		try:
			if constraints:
				editor, getter, setter = self.get_editor_from_constraints(constraints, metadata, parent)

				#Put editor into a frame with a background
				editor_frame = QtWidgets.QFrame(parent)
				editor_frame.setFrameStyle(QtWidgets.QFrame.Shape.Panel | QtWidgets.QFrame.Shadow.Raised)
				editor_frame.setLayout(QtWidgets.QVBoxLayout())
				editor_frame.layout().addWidget(editor)
				editor_frame.layout().setContentsMargins(0, 0, 0, 0)
				palette = parent.palette()
				palette.setColor(editor_frame.backgroundRole(), self._background_color)
				editor_frame.setPalette(palette)

				#Set frameless window props
				self._frameless_window.setCentralWidget(editor_frame)
				self._frameless_window.resize(editor.sizeHint())
				#Get the global position of the currently clicked item
				# (e.g. if the item is in a scrollarea, the position is relative to the scrollarea)
				global_pos = parent.mapToGlobal(option.rect.topLeft()) #type:ignore
				# global_pos = option.mapToGlobal(option.rect.topLeft())
				# self._frameless_window.
				self._frameless_window.move(global_pos)
				self._frameless_window.show()
				self._frameless_window.raise_()

			else:
				raise ValueError(f"Could not create editor for field {field} - no constraints defined")

			return editor
		except Exception as exception: #pylint: disable=broad-except
			log.warning(f"Could not create editor from constraints {constraints} - {exception}")
			raise


	def setEditorData(self, editor, index):
		value = index.data(QtCore.Qt.ItemDataRole.EditRole)
		# entry_type = index.data(QtCore.Qt.ItemDataRole.UserRole) #TODO: maybe create a more descriptive role?

		if isinstance(editor, QtWidgets.QDateTimeEdit):
			editor.setDateTime(value)
		elif isinstance(editor, QtWidgets.QComboBox):
			index = editor.findData(value, QtCore.Qt.ItemDataRole.UserRole) #Get by data
			if index == -1:
				index = editor.findText(str(value))
			editor.setCurrentIndex(index)
		elif isinstance(editor, WidgetSwitcher):
			editor.set_value(value)
		elif isinstance(editor, WidgetList):
			editor.set_values(value)
		else:
			super().setEditorData(editor, index)

	# def sizeHint(self, option, index) -> QtCore.QSize:
		# return super().sizeHint(option, index)

	def setModelData(self, editor, model, index):
		if isinstance(editor, QtWidgets.QDateTimeEdit):
			value = editor.dateTime()
			model.setData(index, value, QtCore.Qt.ItemDataRole.EditRole)
		elif isinstance(editor, QtWidgets.QComboBox):
			value = editor.currentData(QtCore.Qt.ItemDataRole.UserRole)
			model.setData(index, value, QtCore.Qt.ItemDataRole.EditRole)
		elif isinstance(editor, WidgetSwitcher):
			value = editor.get_value()
			model.setData(index, value, QtCore.Qt.ItemDataRole.EditRole)
		elif isinstance(editor, WidgetList):
			value = editor.get_values()
			model.setData(index, value, QtCore.Qt.ItemDataRole.EditRole)
		else:
			super().setModelData(editor, model, index)

		if self._frameless_window:
			self._frameless_window.hide()
		# 	self._frameless_window = None
