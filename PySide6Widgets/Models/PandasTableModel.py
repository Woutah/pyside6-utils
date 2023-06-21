"""Implements the a Qt-Model for pandas dataframes, so we can display them as a table in Qt-Widgets"""
import logging
from numbers import Number

import pandas as pd
from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt

log = logging.getLogger(__name__)


class PandasTableModel(QAbstractTableModel):
	""" A model-wrapper around a pandas dataframe to use with a QTableView
	NOTE: editing is not supported (yet)
	"""

	def __init__(self, dataframe: pd.DataFrame, parent=None):
		QAbstractTableModel.__init__(self, parent)
		self._dataframe = dataframe

	def rowCount(self, parent=QModelIndex()) -> int:
		if parent == QModelIndex():
			return len(self._dataframe)
		return 0

	def columnCount(self, parent=QModelIndex()) -> int:
		if parent == QModelIndex():
			return len(self._dataframe.columns)
		return 0

	def data(self, index: QModelIndex, role=Qt.ItemDataRole):
		if not index.isValid():
			return None

		if role == Qt.ItemDataRole.DisplayRole:
			data = self._dataframe.iloc[index.row(), index.column()]
			if data is None or (isinstance(data, Number) and pd.isnull(data)):
				return ""
			#TODO: Convert item to qt-equivalent instead of string?
			return str(data)
		elif role == Qt.ItemDataRole.EditRole:
			return self._dataframe.iloc[index.row(), index.column()]
		elif role == Qt.ItemDataRole.BackgroundRole:
			return None

		return None


	def headerData(
		self, section: int, orientation: Qt.Orientation, role: Qt.ItemDataRole
	):
		if role == Qt.ItemDataRole.DisplayRole:
			if orientation == Qt.Orientation.Horizontal:
				return str(self._dataframe.columns[section])

			if orientation == Qt.Orientation.Vertical:
				return str(self._dataframe.index[section])
		return None
