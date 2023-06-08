
from PySide6 import QtWidgets
import traceback
import logging
log = logging.getLogger(__name__)


def catchExceptionInMsgBoxDecorator(func : callable):
	"""Decorator that catches ALL exceptions and logs them. Also shows a message box if the app is running. 
	TODO: second argument with list of exceptions to catch?
	Args:
		func (callable): The function which should be called


	"""

	def catchExceptionInMsgBoxDecorator(*args, **kwargs):
		try:
			return func(*args, **kwargs)
		except Exception as e:
			log.exception(f"Exception in {func.__name__}: {e}")
			#Also create a message box
			#Check if app is running, if so -> show message box
			if QtWidgets.QApplication.instance() is not None:
				msg = QtWidgets.QMessageBox()
				msg.setWindowTitle("Error")
				msg.setIcon(QtWidgets.QMessageBox.Critical)
				msg.setText(f"An error occured in function call to: {func.__name__}")
				msg.setInformativeText(f"{type(e).__name__}: {e}")
				trace_msg = f"Traceback:\n{traceback.format_exc()}"
				msg.setDetailedText(trace_msg)
				msg.setStandardButtons(QtWidgets.QMessageBox.Ok)
				msg.exec()
			raise
	return catchExceptionInMsgBoxDecorator