"""
Implements a signal blocker which can be used to temporarily block qt signals
of a qt object using the with statement.
"""

from PySide6 import QtCore

class SignalBlocker(QtCore.QObject):
	"""Implements a signal blocker which can be used to temporarily block qt signals
	of a qt object using the with statement.
	"""
	def __init__(self, qt_object : QtCore.QObject) -> None:
		super().__init__()
		self._qt_object = qt_object

	def __enter__(self):
		self._qt_object.blockSignals(True)

	def __exit__(self, exc_type, exc_value, traceback):
		self._qt_object.blockSignals(False)
