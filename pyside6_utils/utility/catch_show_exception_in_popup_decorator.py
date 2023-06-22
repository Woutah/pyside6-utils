"""Implements a decorator to be used in UI-classes to catch exceptions and show them in a message box"""
import logging
import traceback
import typing

from PySide6 import QtWidgets

log = logging.getLogger(__name__)


def catch_show_exception_in_popup_decorator(
		func : typing.Callable,
		re_raise : bool = True,
		add_traceback_to_details : bool = True,
		custom_error_msg : str | None = None
	):
	"""Decorator that catches ALL exceptions and logs them. Also shows a message box if the app is running.
	TODO: second argument with list of exceptions to catch?
	Args:
		func (callable): The function which should be called
		re_raise (bool, optional): If True, the exception will be re-raised after being logged. Defaults to True.

	"""

	def catch_show_exception_in_popup(*args, **kwargs):
		try:
			return func(*args, **kwargs)
		except Exception as exception: #pylint: disable=broad-except
			log.exception(f"Exception in {func.__name__}: {exception}")
			#Also create a message box
			#Check if app is running, if so -> show message box
			if QtWidgets.QApplication.instance() is not None:
				msg = QtWidgets.QMessageBox()
				msg.setWindowTitle("Error")
				msg.setIcon(QtWidgets.QMessageBox.Icon.Critical)
				if custom_error_msg is not None:
					msg.setText(custom_error_msg)
				else:
					msg.setText(f"An error occured in function call to: {func.__name__}")
				msg.setInformativeText(f"{type(exception).__name__}: {exception}")
				trace_msg = f"Traceback:\n{traceback.format_exc()}"
				if add_traceback_to_details:
					msg.setDetailedText(trace_msg)
				msg.setStandardButtons(QtWidgets.QMessageBox.StandardButton.Ok)
				msg.exec()
			if re_raise:
				raise
	return catch_show_exception_in_popup
