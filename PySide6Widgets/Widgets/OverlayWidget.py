
from typing import Optional, Union

import PySide6.QtCore
import PySide6.QtGui
import PySide6.QtWidgets as QtWidgets
from PySide6 import QtCore, QtGui
from PySide6.QtCore import Qt
import PySide6.QtWidgets


class OverlayWidget(QtWidgets.QWidget):
	"""
	Container-like widget which allows the user to overlay another widget on top of it. Switching on/off the overlay
	widget is done by setting the overlayHidden property. 
	"""

	DESCRIPTION = "Basic QtWidget that allows displaying another widget on top of it using setOverlayWidget."


	def __init__(self, parent: QtWidgets.QWidget | None) -> None:
		super().__init__(parent)

		self._display_overlay = False

		self._overlay_widget_container: QtWidgets.QWidget | None = QtWidgets.QWidget(self)
		self._overlay_widget_container.setParent(self)
		self._overlay_widget_container.setWindowFlags(Qt.Widget | Qt.FramelessWindowHint)
		self._overlay_widget_container.setAutoFillBackground(True)
		self._overlay_widget_container.setContentsMargins(0, 0, 0, 0)
		self._overlay_widget_container.raise_()

		self._cur_background_color = None
		self.setOverlayMouseBlock(True)
		self.setBackgroundColor(QtGui.QColor(0, 0, 0, 100))


	def setOverlayMouseBlock(self, block: bool) -> None:
		self._overlay_widget_container.setAttribute(Qt.WA_TransparentForMouseEvents, not block)
	
	def getOverlayMouseBlock(self) -> bool:
		return self._overlay_widget_container.testAttribute(Qt.WA_TransparentForMouseEvents)

	def showEvent(self, event: QtGui.QShowEvent) -> None:
		self._overlay_widget_container.raise_() #Make sure the overlay widget is on top
		return super().showEvent(event)


	def setOverlayWidget(self, widget: QtWidgets.QWidget | None) -> None:
		"""
		Sets the overlay widget to display on top of this widget. 
		"""
		self._overlay_widget = widget
		self._overlay_widget_container.setLayout(QtWidgets.QVBoxLayout()) #Reset the layout to remove any previous
		self._overlay_widget_container.layout().addWidget(widget)
		self._overlay_widget_container.layout().addWidget(QtWidgets.QLabel("Overlayed"))
		self._overlay_widget_container.resize(self.size())
		# self._overlay_widget_container.move(0, 0)
		self._overlay_widget_container.layout().setAlignment(Qt.AlignCenter)

		self._overlay_widget_container.raise_()


	#On resize, update the overlay widget size
	def resizeEvent(self, event: PySide6.QtGui.QResizeEvent) -> None:
		super().resizeEvent(event)
		self._overlay_widget_container.resize(self.size())

	def setOverlayHidden(self, hidden: bool) -> None:
		"""
		Sets the overlay widget to be hidden or visible. 
		"""
		self._overlay_widget_container.setHidden(hidden)

	def getOverlayHidden(self) -> bool:
		"""
		Returns whether the overlay widget is hidden or visible. 
		"""
		return self._overlay_widget_container.isHidden()


	def setBackgroundColor(self, color: QtGui.QColor) -> None:
		"""
		Sets the background color of the overlay widget. 
		"""
		self._cur_background_color = color
		style = QtWidgets.QApplication.style()
		palette = style.standardPalette()
		palette.setColor(QtGui.QPalette.Window, color) #Background color
		# palette.setColor(QtGui.QPalette.WindowText, color)
		self._overlay_widget_container.setPalette(palette)
		# self.
	
	overlayHidden = QtCore.Property(bool, getOverlayHidden, setOverlayHidden)
	overlayBlocksMouse = QtCore.Property(bool, getOverlayMouseBlock, setOverlayMouseBlock)

	overlayBackgroundColor = QtCore.Property(QtGui.QColor, lambda self: self._cur_background_color, setBackgroundColor)



if __name__ == "__main__": 
	print("Starting")

	app = QtWidgets.QApplication([])
	widget = OverlayWidget(None)

	buttons = QtWidgets.QPushButton("Hello")
	buttons2 = QtWidgets.QPushButton("Hello2")
	buttons3 = QtWidgets.QPushButton("Hello3")
	
	buttons.setFixedSize(300, 100)
	buttons2.setFixedSize(300, 100)
	buttons3.setFixedSize(300, 100)
	widget.setLayout(QtWidgets.QVBoxLayout())
	widget.layout().addWidget(buttons)
	widget.layout().addWidget(buttons2)
	widget.layout().addWidget(buttons3)


	overlay = QtWidgets.QWidget(None)
	# overlay.setStyleSheet("background-color: rgba(255, 0, 0, 100);")
	# #Centering the overlay
	overlay.setFixedSize(300, 100)
	overlay.setLayout(QtWidgets.QVBoxLayout())
	overlay.layout().addWidget(QtWidgets.QLabel("Widget itself"))
	btn = QtWidgets.QPushButton("Hide overlay")
	btn.clicked.connect(lambda: widget.setOverlayHidden(True))
	overlay.layout().addWidget(btn)
	# overlay.layout().setAlignment(Qt.AlignCenter)
	# overlay.layout().addWidget(QtWidgets.QLabel("Overlayed"))

	widget.setOverlayWidget(overlay)
	# widget.setBackgroundColor(QtGui.QColor(255, 0, 0, 100))
	# widget.setOverlayHidden(False)

	widget.show()
	app.exec()


	print("All done.")



