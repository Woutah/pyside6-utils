from PySide6 import QtCore, QtGui, QtWidgets
from datetime import datetime
import typing_inspect
import typing
# from PySide6Widgets.Models.DataClassModel import DataClassRoles

# #Get pixmap of sp_DialogOkButton
# dialog_default_pixmap = QtWidgets.QApplication.style().standardPixmap(QtWidgets.QStyle.SP_DialogOkButton)
# dialog_default_icon = QtGui.QIcon(dialog_default_pixmap)

class DataClassEditorsDelegate(QtWidgets.QStyledItemDelegate):
	#Custom delegate that allows for editing of different data types of DataClassModel
	

	def createEditor(self, parent, option, index):
		#NOTE: we first used index.internalPointer==DateTime (or some other type) --> this goes wrong when using a proxy model, instead, it is probably best to define custom roles to get the field type
		# index = index.model().mapToSource(index)
		# kaas = DataClassRoles.dataclassFieldTypeRole
		# entry_type = index.data(DataClassRoles.dataclassFieldTypeRole)
		entry_type = index.data(QtCore.Qt.UserRole) #TODO: maybe create a more descriptive role? 
		default_value = index.data(QtCore.Qt.UserRole + 1) #TODO: maybe create a more descriptive role?

		# default_btn.setText("")
		editor = None
		if entry_type: #If entry_type is not None
			if entry_type == datetime: 
				editor = QtWidgets.QDateTimeEdit(parent)
				editor.setCalendarPopup(True)
			elif typing_inspect.get_origin(entry_type) == typing.Literal:
				editor = QtWidgets.QComboBox(parent)
				editor.addItems(entry_type.__args__)
			elif entry_type == float:
				editor = QtWidgets.QDoubleSpinBox(parent)
				# editor.setDecimals(5)
				editor.setDecimals(5)

				#Remove min/max values
				editor.setMinimum(-9999999)
				editor.setMaximum(9999999)
		else:
			editor = super().createEditor(parent, option, index) #If no custom editor is created, use the default editor

		# editor_layout = QtWidgets.QHBoxLayout(parent)
		# editor_layout.addWidget(editor)
		# #Add spacer to push btn to right
		# spacer = QtWidgets.QSpacerItem(0, 0, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
		# editor_layout.addItem(spacer)
		# default_btn = QtWidgets.QPushButton(parent)
		# default_btn.setIcon(dialog_default_icon)
		# editor_layout.addWidget(default_btn)
		# default_btn.setMaximumWidth(20)

		return editor
		

	def setEditorData(self, editor, index):
		value = index.data(QtCore.Qt.EditRole)

		entry_type = index.data(QtCore.Qt.UserRole) #TODO: maybe create a more descriptive role? 

		if entry_type == datetime:
			# value = QtCore.QDateTime(value)
			editor.setDateTime(value)
		else:
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
