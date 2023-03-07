

import PySide6.QtCore, PySide6.QtGui, PySide6.QtWidgets
import typing


class FileExplorerModel(PySide6.QtWidgets.QFileSystemModel):

	def __init__(self, parent: typing.Optional[PySide6.QtCore.QObject] = None) -> None:
		super().__init__(parent)
		self._selected_path = None

		# self._selection_pixmap = PySide6.QtWidgets.QStyle.SP_ArrowRight #Right arrow
		self._selection_pixmap = PySide6.QtWidgets.QStyle.SP_DialogApplyButton #Checkmark
		self._selection_icon = PySide6.QtWidgets.QApplication.style().standardIcon(self._selection_pixmap)
		self._prev_selection = None

	def setHightLight(self, selection: PySide6.QtCore.QModelIndex) -> None:
		"""Set the current selection to the model"""
		print(f"Setting model selection to index {self.filePath(selection)}")
		self._selected_path = self.filePath(selection)
		
		if self._prev_selection:
			self.dataChanged.emit(self._prev_selection, self._prev_selection)

		self._prev_selection = PySide6.QtCore.QPersistentModelIndex(selection)
		self.dataChanged.emit(self._prev_selection, self._prev_selection)
		# self._prev_selection = selection


		#Inform view that data has changed
		self.dataChanged.emit(selection, selection)




# class test:
	def data(self, index: PySide6.QtCore.QModelIndex, role: int = PySide6.QtCore.Qt.DisplayRole) -> typing.Any:

		#If first column and fileIconRole, return selection icon
		if role == PySide6.QtWidgets.QFileSystemModel.FileIconRole and index.column() == 0 and self._selected_path and (self.filePath(index) == self._selected_path):
			#Return arrow icon if selected
			return self._selection_icon

		# if self._selected_path and (self.filePath(index) == self._selected_path):
		# 	# filepath = self.filePath(index)
		# 	# if self._selected_path == filepath:
		# 	print("Setting font to bold")
		# 	font = PySide6.QtGui.QFont()
		# 	font.setBold(True)
		# 	return font
		# 	return "->" + self.fileName(index)

		return super().data(index, role)
	

	# def setSelectedPath(self, path: str) -> None:
	# 	"""Set the current selection to the model"""
	# 	self._selected_path = path
	
	# selectedPath = PySide6.QtCore.Property(str, fget=lambda self: self._selected_path, fset = setSelectedPath)