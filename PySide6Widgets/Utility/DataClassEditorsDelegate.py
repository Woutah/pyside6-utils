import logging
import math
import types
import typing
from datetime import datetime
from numbers import Integral, Number, Real

import typing_inspect
from PySide6 import QtCore, QtGui, QtWidgets

from PySide6Widgets.Utility.sklearn_param_validation import (Interval,
                                                             StrOptions)

log = logging.getLogger(__name__)

# from PySide6Widgets.Models.DataClassModel import DataClassRoles

# #Get pixmap of sp_DialogOkButton
# dialog_default_pixmap = QtWidgets.QApplication.style().standardPixmap(QtWidgets.QStyle.SP_DialogOkButton)
# dialog_default_icon = QtGui.QIcon(dialog_default_pixmap)

class DataClassEditorsDelegate(QtWidgets.QStyledItemDelegate):
	"""
	Custom delegate made especially for the DataClassModel. This delegate allows for editing of various datatypes.
	TODO: maybe use a factory instead for the editors
	"""
	#Custom delegate that allows for editing of different data types of DataClassModel
	# def __init__(self, parent: QtCore.QObject | None = ...) -> None:
	# 	super().__init__(parent)

	# 	self.restore_default_icon = QtWidgets.QApplication.style().standardIcon(QtWidgets.QStyle.SP_DockWidgetCloseButton)


	# def paint(self, painter : QtGui.QPainter, option : QtWidgets.QStyleOptionViewItem, index : QtCore.QModelIndex) -> None:
	# 	#First draw the default item
	# 	super().paint(painter, option, index)

	# 	if index.column() == 0: #If first column
	# 		return

	# 	if option.state & (QtWidgets.QStyle.State_MouseOver | (QtWidgets.QStyle.State_Selected)): #If mouse-over event is detected or part of selection #TODO: active?
	# 		painter.save()
	# 		#Get the rect of the first column
	# 		rect = option.rect
	# 		icon_rect = QtCore.QRect(rect.right() - self.icon_size, rect.top() + (rect.height()-self.icon_size)/2, self.icon_size, self.icon_size)

	# 		mouse_pos =  option.widget.mapFromGlobal(QtGui.QCursor.pos())
	# 		if icon_rect.contains(mouse_pos):
	# 			painter.fillRect(icon_rect, QtGui.QColor(0, 0, 0, 150))
	# 		# if self.hovering_del_btn: #If hovering over -> create grey background
	# 		# 	painter.fillRect(icon_rect, QtGui.QColor(0, 0, 0, 150))

	# 		#Get the icon rect
	# 		# icon_rect = QtCore.QRect(rect.right() - self.icon_size, rect.top(), self.icon_size, self.icon_size)
	# 		#Draw the icon
	# 		# painter.drawPixmap(icon_rect, self.trash_icon_pixmap)
	# 		# painter.paint
	# 		QtGui.QIcon.paint(self.trash_icon, painter, icon_rect, mode=QtGui.QIcon.Normal, state=QtGui.QIcon.On)


	# 		#Restore the painter state
	# 		painter.restore()

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
			parent (QtWidgets.QWidget): The parent widget to use for the editor
		"""
		if constraint == bool or constraint == "boolean":
			editor = QtWidgets.QComboBox(parent)
			editor.addItems(["True", "False"])
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
				else:
					editor.setDecimals(2)

			return editor
		elif isinstance(constraint, StrOptions):
			editor = QtWidgets.QComboBox(parent)
			all_options = list(constraint.options)
			#Sort options alphabetically
			all_options.sort()
			editor.addItems(all_options)

			try:
				constraints_help_dict = metadata["constraints_help"]
				for i, option in enumerate(all_options):
					if option in constraints_help_dict: #If key-help is defined, add it as tooltip
						editor.setItemData(i, constraints_help_dict[option], QtCore.Qt.ItemDataRole.ToolTipRole)
			except KeyError:
				pass
			return editor
		else:
			log.debug(f"Could not create editor for constraint {constraint} - returning None-editor")
		return None
	
	# def typehint_to_constraint(self, typehint):
	# 	typing_inspect.get_origin(entry_type) == typing.Literal

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
				new_constraint = DataClassEditorsDelegate.get_constraints_from_typehint(cur_type)
				if new_constraint:
					constraints.extend(new_constraint)
		elif typing_inspect.get_origin(typehint) == typing.Literal:
			constraints = [StrOptions(set(typehint.__args__))]
		return constraints


	def createEditor(self, parent, option, index):
		#NOTE: we first used index.internalPointer==DateTime (or some other type) --> this goes wrong when using a 
		# proxy model, instead, it is probably best to define custom roles to get the field type

		field = index.data(QtCore.Qt.ItemDataRole.UserRole + 1) #TODO: maybe create a more descriptive role?
		self.editor_list = [] #List of the editor types that are created

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
			constraints = DataClassEditorsDelegate.get_constraints_from_typehint(entry_type)


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
						the_constraint = constraints[0] if constraints[0] is not None or isinstance(constraints[0], type(None)) else constraints[1]
					else:
						the_constraint = constraints[0] #For now, just use the first constaint
					editor = self.get_editor_from_constraint(the_constraint, metadata, parent)
					if editor is not None:
						return editor
			elif len(constraints) >= 3:
				pass #For now too complex -> skip, TODO: but create a user-selectable editor for this?
			constraints = [entry_type]





		#Otherwise, use default editor
		editor = super().createEditor(parent, option, index) #If no custom editor is created, use the default editor
		# self.editor_list.append(editor)

		return editor


	def setEditorData(self, editor, index):
		value = index.data(QtCore.Qt.ItemDataRole.EditRole)
		entry_type = index.data(QtCore.Qt.ItemDataRole.UserRole) #TODO: maybe create a more descriptive role?
		# field = index.data(QtCore.Qt.ItemDataRole.UserRole + 1) #TODO: maybe create a more descriptive role?

		if isinstance(editor, QtWidgets.QDateTimeEdit): 
			editor.setDateTime(value)
		super().setEditorData(editor, index)

	def setModelData(self, editor, model, index):
		entry_type = index.data(QtCore.Qt.ItemDataRole.UserRole) #TODO: maybe create a more descriptive role?
		if isinstance(editor, QtWidgets.QDateTimeEdit):
			value = editor.dateTime()
			model.setData(index, value, QtCore.Qt.ItemDataRole.EditRole)
		else:
			super().setModelData(editor, model, index)

	def updateEditorGeometry(self, editor, option, index):
		editor.setGeometry(option.rect) #type: ignore



	def paint(self, painter : QtGui.QPainter, option : QtWidgets.QStyleOptionViewItem, index : QtCore.QModelIndex) -> None:
		
		if index.column() == 1: #If second (value) column -> some custom painting methods
			entry_type = index.data(QtCore.Qt.ItemDataRole.UserRole) #TODO: maybe create a more descriptive role?
			if entry_type:
				if entry_type == datetime:
					value = index.data(QtCore.Qt.ItemDataRole.DisplayRole)
					font = index.data(QtCore.Qt.ItemDataRole.FontRole)
					try:
						#Format date according to local format settings
						locale = QtCore.QLocale()
						value = locale.toString(value, str(locale.dateTimeFormat(locale.FormatType.ShortFormat)))
					except:
						value = ""

					#Use font from model
					if font:
						painter.setFont(font)
					painter.drawText(option.rect, QtCore.Qt.AlignmentFlag.AlignLeft, value) #type: ignore
					
					return
		super().paint(painter, option, index)
