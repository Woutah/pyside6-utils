from PySide6 import QtCore, QtGui, QtWidgets
from datetime import datetime
import typing_inspect
import typing
from Models.DataClassModel import DataClassRoles


class DataClassEditorsDelegate(QtWidgets.QStyledItemDelegate):
	#Custom delegate that allows for editing of different data types of DataClassModel
	def createEditor(self, parent, option, index):
		# print(f"Field type: {index.internalPointer().field.type}")

		# print(f"index: {index}, row,column: {index.row()},{index.column()}")
		# try:
		# 	kaas = index.internalPointer()
		# except Exception as e:
		# 	print(f"EXCEPTIOJN: {e}")

		entry_type = index.data()

		#NOTE: using index.internalPointer goes wrong when using a proxy model, instead, it is probably best to define custom roles to get 
		index = index.model().mapToSource(index)

		if index.internalPointer().field.type == datetime:
			editor = QtWidgets.QDateTimeEdit(parent)
			editor.setCalendarPopup(True)
			return editor

		#If literal type
		elif typing_inspect.get_origin(index.internalPointer().field.type) == typing.Literal:
			# print("LITERAL!")
			editor = QtWidgets.QComboBox(parent)
			editor.addItems(index.internalPointer().field.type.__args__)
			return editor

		#If type float, create spinbox that's able to handle > 2 decimals
		elif index.internalPointer().field.type == float:
			editor = QtWidgets.QDoubleSpinBox(parent)
			# editor.setDecimals(5)
			editor.setDecimals(5)

			#Remove min/max values
			editor.setMinimum(-9999999)
			editor.setMaximum(9999999)

			return editor
		else:
			return super().createEditor(parent, option, index)

	def setEditorData(self, editor, index):
		value = index.data(QtCore.Qt.EditRole)

		mapped_index = index.model().mapToSource(index)
		if mapped_index.internalPointer().field.type == datetime:
			# value = QtCore.QDateTime(value)
			editor.setDateTime(value)
		else:
			super().setEditorData(editor, index)

	def setModelData(self, editor, model, index):
		
		mapped_index = index.model().mapToSource(index)
		if mapped_index.internalPointer().field.type == datetime:
			value = editor.dateTime()
			model.setData(index, value, QtCore.Qt.EditRole)
		else:
			super().setModelData(editor, model, index)

	def updateEditorGeometry(self, editor, option, index):
		editor.setGeometry(option.rect)



	def paint(self, painter: QtGui.QPainter, option: 'QStyleOptionViewItem', index: QtCore.QModelIndex) -> None:
		return super().paint(painter, option, index)
		if index.internalPointer().field and (index.column() == 1):
			if index.internalPointer().field.type == datetime:
				value = index.data(QtCore.Qt.DisplayRole)
				# if isinstance(value, datetime):
				try:
					#Format date according to local format settings
					locale = QtCore.QLocale()
					value = locale.toString(value, str(locale.dateTimeFormat(locale.ShortFormat)))
				except:
					value = ""

				painter.drawText(option.rect, QtCore.Qt.AlignLeft, value)
				return
			# elif index.internalPointer().field.type == bool:
			# 	value = index.data(QtCore.Qt.DisplayRole)
			# 	QStyleOptionButton = QtWidgets.QStyleOptionButton()
			# 	QStyleOptionButton.rect = option.rect
			# 	# QStyleOptionButton.state = QtWidgets.QStyle.State_Enabled
			# 	if value:
			# 		QStyleOptionButton.state |= QtWidgets.QStyle.State_On
			# 	else:
			# 		QStyleOptionButton.state |= QtWidgets.QStyle.State_Off
			# 	QStyleOptionButton.state |= QtWidgets.QStyle.State_Enabled
			# 	#Also make selectable
			# 	#Draw checkbox
			# 	QtWidgets.QApplication.style().drawControl(QtWidgets.QStyle.CE_CheckBox, QStyleOptionButton, painter)
			# 	return
				

						
		super().paint(painter, option, index)
