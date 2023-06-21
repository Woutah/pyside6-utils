"""Implements the delegate for a """
import logging
import math
import types
import typing
from datetime import datetime
from numbers import Integral, Real

import typing_inspect
from PySide6 import QtCore, QtWidgets

from PySide6Widgets.utility.constraints import Interval, Options, StrOptions

log = logging.getLogger(__name__)

class DataclassEditorsDelegate(QtWidgets.QStyledItemDelegate):
	"""
	Custom delegate made especially for the DataClassModel. This delegate allows for editing of various datatypes.
	TODO: maybe use a factory instead for the editors
	"""
	#Custom delegate that allows for editing of different data types of DataClassModel
	def __init__(self, *args, **kwargs) -> None: #pylint: disable=unused-argument
		super().__init__()
	def get_editor_from_constraint(self, constraint, metadata, parent):
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

		"""
		if constraint == bool or constraint == "boolean":
			editor = QtWidgets.QComboBox(parent)
			editor.addItem("True", True)
			editor.addItem("False", False)
			return editor
		elif constraint == datetime:
			editor = QtWidgets.QDateTimeEdit(parent)
			editor.setCalendarPopup(True)
			return editor 
		elif isinstance(constraint, type) and issubclass(constraint, Integral): #If int or (other subclass of) integral
			editor = QtWidgets.QSpinBox(parent)
			editor.setMaximum(9999999)
			editor.setMinimum(-9999999)
			return editor
		elif isinstance(constraint, type) and issubclass(constraint, Real): #If float or (other subclass of) real
			editor = QtWidgets.QDoubleSpinBox(parent)
			editor.setDecimals(4) #TODO: make this user-selectable?
			editor.setMinimum(-9999999)
			editor.setMaximum(9999999)
			return editor
		elif isinstance(constraint, Interval):
			if issubclass(constraint.type, Integral):
				editor = QtWidgets.QSpinBox(parent)
			else:
				editor = QtWidgets.QDoubleSpinBox(parent)
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

			return editor
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
			return editor
		else:
			log.debug(f"Could not create editor for constraint {constraint} - returning None-editor")
		return None


	@staticmethod
	def get_constraints_from_typehint(typehint) -> list | None:
		"""Retrieve the constraints from the passed typehint.
		E.g.: typing.Union[None, int] -> [None, int]

		"""
		constraints = None
		if isinstance(typehint, type):
			return [typehint]
		elif isinstance(typehint, types.UnionType) or \
				typing_inspect.get_origin(typehint) == typing.Union:
				# typing_inspect.get_origin(typehint) == typing.Union: #If optional -> same as Union[x | None],
			type_list = list(typing_inspect.get_args(typehint))
			constraints = []
			for cur_type in type_list:
				new_constraint = DataclassEditorsDelegate.get_constraints_from_typehint(cur_type)
				if new_constraint:
					constraints.extend(new_constraint)
		elif typing_inspect.get_origin(typehint) == typing.Literal: #pylint: disable=comparison-with-callable
			constraints = [Options(typing.Any, set(typehint.__args__))] #TODO: maybe check if all the same type instead
				# of typing.Any?
		return constraints


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


		if constraints is None and entry_type is not None: #If no constraints, set constraints to current type
			#Get used types from field.type (e.g. typing.Literal, typing.Union, typing.List, typing.Dict, typing.Tuple,
			# typing.Callable, typing.Optional, typing.Any, typing.ClassVar, typing.Final, typing.TypeVar,
			# typing.Generic, typing.Protocol)
			try:
				constraints = DataclassEditorsDelegate.get_constraints_from_typehint(entry_type)
			except Exception as exception: #pylint: disable=broad-except
				log.warning(f"Could not get constraints from typehint {entry_type} - {exception}")
				constraints = None
		try:
			if constraints: #First try to get editor based off of constraints
				if len(constraints) == 0: #If no constraints are defined, use default editor
					return
				elif "array-like" in constraints: #for now use text-editor for lists
					pass
				elif len(constraints) <= 2:
					if len(constraints) == 1 and None in constraints: #If only none:
						pass
					else: #TODO: implement more complex constraints
						if None in constraints or type(None) in constraints:
							the_constraint = constraints[0] \
								if constraints[0] is not None or isinstance(constraints[0], type(None)) else constraints[1]
						else:
							the_constraint = constraints[0] #For now, just use the first constaint
						editor = self.get_editor_from_constraint(the_constraint, metadata, parent)
						if editor is not None:
							return editor
				elif len(constraints) >= 3:
					pass #For now too complex -> skip, TODO: but create a user-selectable editor for this?
				# constraints = [entry_type]
		except Exception as exception: #pylint: disable=broad-except
			log.warning(f"Could not create editor from constraints {constraints} - {exception}")

		return super().createEditor(parent, option, index) #If no custom editor is created, use the default editor


	def setEditorData(self, editor, index):
		value = index.data(QtCore.Qt.ItemDataRole.EditRole)
		# entry_type = index.data(QtCore.Qt.ItemDataRole.UserRole) #TODO: maybe create a more descriptive role?

		if isinstance(editor, QtWidgets.QDateTimeEdit):
			editor.setDateTime(value)
		super().setEditorData(editor, index)

	def setModelData(self, editor, model, index):
		if isinstance(editor, QtWidgets.QDateTimeEdit):
			value = editor.dateTime()
			model.setData(index, value, QtCore.Qt.ItemDataRole.EditRole)
		elif isinstance(editor, QtWidgets.QComboBox):
			value = editor.currentData(QtCore.Qt.ItemDataRole.UserRole)
			model.setData(index, value, QtCore.Qt.ItemDataRole.EditRole)
		else:
			super().setModelData(editor, model, index)


	def updateEditorGeometry(self, editor, option, index): #pylint: disable=unused-argument
		editor.setGeometry(option.rect) #type: ignore
