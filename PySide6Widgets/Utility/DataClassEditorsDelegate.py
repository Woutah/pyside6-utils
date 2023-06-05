from typing import Optional
from PySide6 import QtCore, QtGui, QtWidgets
from datetime import datetime
import PySide6.QtCore
import typing_inspect
import typing
from numbers import Number, Real, Integral
from enum import Enum
from PySide6Widgets.Utility.sklearn_param_validation import Interval, StrOptions
# from PySide6Widgets.Models.DataClassModel import DataClassRoles

# #Get pixmap of sp_DialogOkButton
# dialog_default_pixmap = QtWidgets.QApplication.style().standardPixmap(QtWidgets.QStyle.SP_DialogOkButton)
# dialog_default_icon = QtGui.QIcon(dialog_default_pixmap)

class DataClassEditorsDelegate(QtWidgets.QStyledItemDelegate):
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

	def createEditor(self, parent, option, index):
		#NOTE: we first used index.internalPointer==DateTime (or some other type) --> this goes wrong when using a proxy model, instead, it is probably best to define custom roles to get the field type
		# index = index.model().mapToSource(index)
		# kaas = DataClassRoles.dataclassFieldTypeRole
		# entry_type = index.data(DataClassRoles.dataclassFieldTypeRole)
		# entry_type = index.data(QtCore.Qt.UserRole) #TODO: maybe create a more descriptive role? 
		field = index.data(QtCore.Qt.UserRole + 1) #TODO: maybe create a more descriptive role?
		etry_type = field.metadata.get("type", None) if field else None

		self.editor_list = [] #List of the editor types that are created

		editor = None
		entry_type = None
		metadata = None
		constraints = None
		if field:
			metadata = field.metadata
			entry_type = field.type
			constraints = metadata.get("constraints", None)
		
		if constraints: #First try to get editor based off of constraints
			if len(constraints) == 0: #If no constraints are defined, use default editor
				pass
			elif "array-like" in constraints: #for now use text-editor for lists
				pass 
			elif len(constraints) <= 2:
				if len(constraints) == 1 and None in constraints: #If only none:
					pass
				else:					
					if None in constraints:
						the_constraint = constraints[0] if constraints[0] is not None else constraints[1]
					else:
						the_constraint = constraints[0]
				#The possible constraints are: 
					# "array-like":
					# "sparse matrix"
					# "random_state"
					# callable
					# None
					# isinstance(constraint, type) #Type-enforcing constraint
					# (Interval, StrOptions, Options, HasMethods)
					# "boolean"
					# "verbose"
					# "missing_values"
						# "cv_object"
					if the_constraint == bool or the_constraint == "boolean":
						editor = QtWidgets.QComboBox(parent)
						editor.addItems(["True", "False"])
						self.editor_list.append(editor)
						return editor
					elif isinstance(the_constraint, type) and issubclass(the_constraint, Integral): #If int or (other subclass of) integral
						editor = QtWidgets.QSpinBox(parent)
						editor.setMaximum(9999999)
						editor.setMinimum(-9999999)
						self.editor_list.append(editor)
						return editor
					elif isinstance(the_constraint, type) and issubclass(the_constraint, Real): #If float or (other subclass of) real
						editor = QtWidgets.QDoubleSpinBox(parent)
						self.editor_list.append(editor)
						editor.setDecimals(5) #TODO: make this user-selectable?
						editor.setMinimum(-9999999)
						editor.setMaximum(9999999)
						pass
					elif isinstance(the_constraint, Interval):
						if issubclass(the_constraint.type, Integral):
							editor = QtWidgets.QSpinBox(parent)
						else:
							editor = QtWidgets.QDoubleSpinBox(parent)
						if the_constraint.right:
							editor.setMaximum(the_constraint.right)
						if the_constraint.left:
							editor.setMinimum(the_constraint.left)
						
						self.editor_list.append(editor)
						return editor
					elif isinstance(the_constraint, StrOptions):
						editor = QtWidgets.QComboBox(parent)
						all_options = list(the_constraint.options)
						#Sort options alphabetically
						all_options.sort()
						editor.addItems(all_options)
						self.editor_list.append(editor)

						try:
							constraints_help_dict = metadata["constraints_help"]
							for i, option in enumerate(all_options):
								if option in constraints_help_dict: #If key-help is defined, add it as tooltip
									editor.setItemData(i, constraints_help_dict[option], QtCore.Qt.ToolTipRole)
						except KeyError:
							pass
						return editor
			elif len(constraints) >= 3:
				pass #For now too complex -> skip, TODO: but create a user-selectable editor for this? 
		
		
		elif entry_type: #if no constraints -> try to get editor based off of type-hint instead
			if entry_type == datetime: 
				editor = QtWidgets.QDateTimeEdit(parent)
				editor.setCalendarPopup(True)
				self.editor_list.append(editor)
				return editor
			elif typing_inspect.get_origin(entry_type) == typing.Literal:
				editor = QtWidgets.QComboBox(parent)
				editor.addItems(entry_type.__args__)
			# 	editor.setCurrentText(value)
				# editor.addItems(entry_type.__args__)
				self.editor_list.append(editor)
				return editor
			elif entry_type == float:
				editor = QtWidgets.QDoubleSpinBox(parent)
				# editor.setDecimals(5)
				editor.setDecimals(5)
				#Remove min/max values
				editor.setMinimum(-9999999)
				editor.setMaximum(9999999)
				self.editor_list.append(editor)
				return editor
			
		editor = super().createEditor(parent, option, index) #If no custom editor is created, use the default editor
		self.editor_list.append(editor)

		return editor
		

	def setEditorData(self, editor, index):
		value = index.data(QtCore.Qt.EditRole)
		entry_type = index.data(QtCore.Qt.UserRole) #TODO: maybe create a more descriptive role?
		# field = index.data(QtCore.Qt.UserRole + 1) #TODO: maybe create a more descriptive role?

		if entry_type == datetime:
			# value = QtCore.QDateTime(value)
			editor.setDateTime(value)
		# elif typing_inspect.get_origin(entry_type) == typing.Literal:
		# 	editor.addItems(entry_type.__args__)
		# 	editor.setCurrentText(value)

		# 	if field and field.metadata: #Key help is a dict of format { 'key': 'help text'} which is used to set the tooltip of the combobox
		# 		constraints_help_dict = field.metadata.get('constraints_help', {})
		# 		for i, entry in enumerate(entry_type.__args__):
		# 			if entry in constraints_help_dict:
		# 				editor.setItemData(i, constraints_help_dict[entry], QtCore.Qt.ToolTipRole)
		# 	editor.setToolTip(field.constraints_help)
		# else:
		super().setEditorData(editor, index)

	def setModelData(self, editor, model, index):
		
		entry_type = index.data(QtCore.Qt.UserRole) #TODO: maybe create a more descriptive role? 
		if entry_type == datetime:
			value = editor.dateTime()
			model.setData(index, value, QtCore.Qt.EditRole)
		else:
			super().setModelData(editor, model, index)

	def updateEditorGeometry(self, editor, option, index):
		editor.setGeometry(option.rect)



	def paint(self, painter: QtGui.QPainter, option: 'QStyleOptionViewItem', index: QtCore.QModelIndex) -> None:

		entry_type = index.data(QtCore.Qt.UserRole) #TODO: maybe create a more descriptive role? 
		if entry_type:
			if entry_type == datetime:
				value = index.data(QtCore.Qt.DisplayRole)
				try:
					#Format date according to local format settings
					locale = QtCore.QLocale()
					value = locale.toString(value, str(locale.dateTimeFormat(locale.ShortFormat)))
				except:
					value = ""

				painter.drawText(option.rect, QtCore.Qt.AlignLeft, value)
				return
		super().paint(painter, option, index)
