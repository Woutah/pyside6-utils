"""Implements a wrapper that forces the inside widget to remain square"""
import logging

from PySide6 import QtCore, QtWidgets

log = logging.getLogger(__name__)

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

def run_example_app():
	"""Creates a qt-app instance and runs the example, displaying a couple of square widgets"""
	#pylint: disable=import-outside-toplevel
	import sys
	app = QtWidgets.QApplication(sys.argv)

	example_window = QtWidgets.QMainWindow()
	central_widget = QtWidgets.QWidget()
	example_window.setCentralWidget(central_widget)
	layout = QtWidgets.QHBoxLayout()
	central_widget.setLayout(layout)

	for cur_int in range(4):
		widget = SquareFrame()
		new_btn = QtWidgets.QPushButton(f"Button {cur_int+1}")
		new_btn.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Expanding)
		widget.setLayout(QtWidgets.QVBoxLayout())
		widget.layout().addWidget(new_btn)
		layout.addWidget(widget)
		new_btn.show()
		# widget.show()
	example_window.show()
	sys.exit(app.exec())


if __name__ == "__main__":
	formatter = logging.Formatter("[{pathname:>90s}:{lineno:<4}]  {levelname:<7s}   {message}", style='{')
	handler = logging.StreamHandler()
	handler.setFormatter(formatter)
	logging.basicConfig(
		handlers=[handler],
		level=logging.DEBUG) #Without time
	#Run example
	run_example_app()