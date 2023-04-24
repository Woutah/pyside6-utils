import pandas as pd
from PySide6.QtCore import QAbstractTableModel, Qt, QModelIndex


class PandasTableModel(QAbstractTableModel):

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

		if role == Qt.DisplayRole:
			data = self._dataframe.iloc[index.row(), index.column()]
			try:
				if data is None or pd.isnull(data):
					return ""
			except:
				pass			
			return str(data)
		elif role == Qt.EditRole:
			return self._dataframe.iloc[index.row(), index.column()]
		elif role == Qt.BackgroundRole:
			return None

		return None


	def headerData(
		self, section: int, orientation: Qt.Orientation, role: Qt.ItemDataRole
	):
		if role == Qt.DisplayRole:
			if orientation == Qt.Horizontal:
				return str(self._dataframe.columns[section])

			if orientation == Qt.Vertical:
				return str(self._dataframe.index[section])
		return None
	