"""Implements a delegate that adds a "delete" button ("x") to the console widget treeview"""
from PySide6 import QtCore, QtGui, QtWidgets

class ConsoleWidgetDelegate(QtWidgets.QStyledItemDelegate):
	"""Custom delegate that implements an "x" button
	"""

	deleteHoverItem = QtCore.Signal(QtCore.QModelIndex) #Emitted index when the "delete" button is clicked on an item

	#Custom delegate that puts an x-button at the end of the first column of the file-selection treeview
	#When this button is clicked, the file is deleted
	def __init__(self, parent : QtWidgets.QWidget | None = None) -> None:
		super().__init__(parent)
		# self._delete_button.setFixedSize(16, 16)

		#Get the icon size (normal)
		self.icon_size = QtWidgets.QApplication.style().pixelMetric(QtWidgets.QStyle.PixelMetric.PM_LargeIconSize)

		#Create pixmap from ":/Icons/places/user-trash.png"
		self.trash_icon = QtWidgets.QApplication.style().standardIcon(
			QtWidgets.QStyle.StandardPixmap.SP_TitleBarCloseButton)

		# self.trash_icon_pixmap = QtGui.QPixmap(":/Icons/places/user-trash.png")
		self.hovering_del_btn = False


	def paint(self,
	   		painter : QtGui.QPainter,
			option : QtWidgets.QStyleOptionViewItem, #TODO: typehinting not working? rect, state and widget not found
			index : QtCore.QModelIndex | QtCore.QPersistentModelIndex
		) -> None:
		#First draw the default item
		super().paint(painter, option, index)

		option_state : QtWidgets.QStyle.StateFlag = option.state #type: ignore
		option_rect : QtCore.QRect = option.rect #type: ignore

		#Set icon size based on the height of the item
		self.icon_size = option_rect.height() - 10 #10 is the padding on both top and bottom

		if option_state & \
				(QtWidgets.QStyle.StateFlag.State_MouseOver | (QtWidgets.QStyle.StateFlag.State_Selected)):
				#If mouse-over event is detected or part of selection #TODO: active?
			painter.save()
			#Get the rect of the first column
			icon_rect = QtCore.QRect(
				option_rect.right() - self.icon_size,
				option_rect.top() + (option_rect.height()-self.icon_size)//2,
			    self.icon_size,
				self.icon_size
			)
			option_widget : QtWidgets.QWidget = option.widget #type: ignore
			mouse_pos =  option_widget.mapFromGlobal(QtGui.QCursor.pos())
			if icon_rect.contains(mouse_pos):
				painter.fillRect(icon_rect, QtGui.QColor(0, 0, 0, 150))

			QtGui.QIcon.paint(self.trash_icon,
				painter,
				icon_rect,
				mode=QtGui.QIcon.Mode.Normal,
				state=QtGui.QIcon.State.On
			)


			#Restore the painter state
			painter.restore()


	def editorEvent(self,
			event : QtCore.QEvent,
			model : QtCore.QAbstractItemModel,
			option : QtWidgets.QStyleOptionViewItem, #TODO: typehinting not working? rect, state and widget not found
			index : QtCore.QModelIndex) -> bool:

		event_pos = event.position() #Local position #type: ignore
		global_pos = event_pos.toPoint()
		option_widget : QtWidgets.QTreeWidget = option.widget #type: ignore #TODO: option typehinting not working?
		option_rect : QtCore.QRect = option.rect #type: ignore



		#Check if the user clicked on the icon
		if event.type() == QtCore.QEvent.Type.MouseButtonPress:
			#Get the rect of the first column
			option_rect : QtCore.QRect = option.rect #type: ignore
			#Get the icon rect
			icon_rect = QtCore.QRect(option_rect.right() - self.icon_size, option_rect.top(), self.icon_size, self.icon_size)
			#Check if the mouse is inside the icon rect
			if icon_rect.contains(global_pos):
				#Emit the delete signal
				self.deleteHoverItem.emit(index)
				#Block event propagation
				event.setAccepted(True)
				return True

		elif event.type() == QtCore.QEvent.Type.MouseMove:
			#Get the rect of the first column
			#Get the icon rect
			icon_rect = QtCore.QRect(
				option_rect.right() - self.icon_size, option_rect.top() + (option_rect.height()-self.icon_size)//2,
				self.icon_size,
				self.icon_size
			)
			#Check if the mouse is inside the icon rect
			if icon_rect.contains(global_pos):
				if not self.hovering_del_btn: #Only update view if state changed
					self.hovering_del_btn = True
					option_widget.viewport().update()
				return True #Make sure that mousemove does not selet the underlying item
			elif self.hovering_del_btn:
				self.hovering_del_btn = False
				option_widget.viewport().update()

		return super().editorEvent(event, model, option, index)
