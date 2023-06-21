"""Implements an overlay widget that acts as a container but allows displaying another widget on top of it."""

import PySide6.QtCore
import PySide6.QtGui
import PySide6.QtWidgets
import PySide6.QtWidgets as QtWidgets
from PySide6 import QtCore, QtGui
from PySide6.QtCore import Qt


class OverlayWidget(QtWidgets.QWidget):
	"""
	Container-like widget which allows the user to overlay another widget on top of it. Switching on/off the overlay
	widget is done by setting the overlayHidden property.
	"""

	DESCRIPTION = "Basic QtWidget that allows displaying another widget on top of it using setOverlayWidget."


	def __init__(self, parent: QtWidgets.QWidget | None) -> None:
		super().__init__(parent)

		self._display_overlay = False

		self._overlay_widget_container: QtWidgets.QWidget = QtWidgets.QWidget(self)
		self._overlay_widget_container.setParent(self)
		self._overlay_widget_container.setWindowFlags(Qt.WindowType.Widget | Qt.WindowType.FramelessWindowHint)
		self._overlay_widget_container.setAutoFillBackground(True)
		self._overlay_widget_container.setContentsMargins(0, 0, 0, 0)
		self._overlay_widget_container.raise_()

		self._cur_background_color = None
		self.set_overlay_mouse_block(True)
		self.set_background_color(QtGui.QColor(200, 200, 200, 150))


	def set_overlay_mouse_block(self, block: bool) -> None:
		"""Sets whether the overlay widget should block mouse events from reaching the underlying widget."""
		self._overlay_widget_container.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, not block)

	def get_overlay_mouse_block(self) -> bool:
		"""Returns whether the overlay widget blocks mouse events from reaching the underlying widget."""
		return self._overlay_widget_container.testAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

	def showEvent(self, event: QtGui.QShowEvent) -> None:
		"""On show, raise the overlay widget to make sure it is on top."""
		self._overlay_widget_container.raise_() #Make sure the overlay widget is on top
		return super().showEvent(event)


	def set_overlay_widget(self, widget: QtWidgets.QWidget) -> None:
		"""
		Sets the overlay widget to display on top of this widget.
		"""
		self._overlay_widget = widget
		self._overlay_widget_container.setLayout(QtWidgets.QVBoxLayout()) #Reset the layout to remove any previous
		self._overlay_widget_container.layout().addWidget(widget)
		self._overlay_widget_container.resize(self.size())
		self._overlay_widget_container.layout().setAlignment(Qt.AlignmentFlag.AlignCenter)
		self._overlay_widget_container.raise_()


	def resizeEvent(self, event: PySide6.QtGui.QResizeEvent) -> None:
		"""
		#On resize, update the overlay widget size
		"""
		super().resizeEvent(event)
		self._overlay_widget_container.resize(self.size())

	def set_overlay_hidden(self, hidden: bool) -> None:
		"""
		Sets the overlay widget to be hidden or visible.
		"""
		self._overlay_widget_container.setHidden(hidden)

	def get_overlay_hidden(self) -> bool:
		"""
		Returns whether the overlay widget is hidden or visible.
		"""
		return self._overlay_widget_container.isHidden()


	def set_background_color(self, color: QtGui.QColor) -> None:
		"""
		Sets the background color of the overlay widget.
		"""
		self._cur_background_color = color
		style = QtWidgets.QApplication.style()
		palette = style.standardPalette()
		palette.setColor(QtGui.QPalette.ColorRole.Window, color) #Background color
		self._overlay_widget_container.setPalette(palette)

	overlayHidden = QtCore.Property(bool, get_overlay_hidden, set_overlay_hidden)
	overlayBlocksMouse = QtCore.Property(bool, get_overlay_mouse_block, set_overlay_mouse_block)

	overlayBackgroundColor = QtCore.Property(QtGui.QColor, lambda self: self._cur_background_color, set_background_color)



if __name__ == "__main__":
	import logging
	log = logging.getLogger(__name__)

	formatter = logging.Formatter("[{pathname:>90s}:{lineno:<4}]  {levelname:<7s}   {message}", style='{')
	handler = logging.StreamHandler()
	handler.setFormatter(formatter)
	logging.basicConfig(
		handlers=[handler],
		level=logging.DEBUG) #Without time
	log.debug(f"Now running {OverlayWidget.__name__} example...")


	app = QtWidgets.QApplication([])
	widget = OverlayWidget(None)

	#Some buttons for behind the overlay
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

	#Create overlay and create button to hide it
	overlay = QtWidgets.QWidget(None)
	overlay.setFixedSize(300, 100)
	overlay.setLayout(QtWidgets.QVBoxLayout())
	overlay.layout().addWidget(QtWidgets.QLabel("Widget itself"))
	btn = QtWidgets.QPushButton("Hide overlay")
	btn.clicked.connect(lambda: widget.set_overlay_hidden(True))
	overlay.layout().addWidget(btn)
	widget.set_overlay_widget(overlay)
	widget.show()

	app.exec()
	log.debug("Done!")
