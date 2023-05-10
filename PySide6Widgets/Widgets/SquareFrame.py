
from PySide6 import QtCore, QtGui, QtWidgets

class SquareFrame(QtWidgets.QFrame):
	DESCRIPTION = "Small wrapper to QFrame which enforces a widget to remain square"
	def __init__(self, parent=None):
		super().__init__(parent)
		#Set the layout to a vertical layout
		# self.setLayout(QtWidgets.QVBoxLayout())

	def resizeEvent(self, event):
		new_size = QtCore.QSize(10, 10)
		new_size.scale(event.size(), QtCore.Qt.KeepAspectRatio)
		self.resize(new_size)


if __name__ == "__main__":
	import sys
	app = QtWidgets.QApplication(sys.argv)
	widget = SquareFrame()
	widget.show()
	sys.exit(app.exec_())