"""Implements a wrapper that forces the inside widget to remain square"""
from PySide6 import QtCore, QtWidgets

class SquareFrame(QtWidgets.QFrame):
	"""Wrapper to QFrame which enforces a widget to remain square"""
	DESCRIPTION = "Simple wrapper to QFrame which enforces a widget to remain square"
	def __init__(self, parent=None):
		super().__init__(parent)

	def resizeEvent(self, event):
		"""On resize, force the widget to remain square"""
		new_size = QtCore.QSize(10, 10)
		new_size.scale(event.size(), QtCore.Qt.AspectRatioMode.KeepAspectRatio)
		self.resize(new_size)


if __name__ == "__main__":
	import sys
	app = QtWidgets.QApplication(sys.argv)
	widget = SquareFrame()
	widget.show()
	sys.exit(app.exec())
