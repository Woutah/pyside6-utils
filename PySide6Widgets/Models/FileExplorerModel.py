

import PySide6.QtCore, PySide6.QtGui, PySide6.QtWidgets
import typing
import os

import logging
log = logging.getLogger(__name__)

class FileExplorerModel(PySide6.QtWidgets.QFileSystemModel):
	"""A QFileSystemModel that also allows for hightlighting of a single file, for example when selecting a file for editing pruposes"""

	highlightPathChanged = PySide6.QtCore.Signal(str)

	def __init__(self, parent: typing.Optional[PySide6.QtCore.QObject] = None, allow_select_files_only=True) -> None:
		super().__init__(parent)
		self._selected_path = None

		self._selection_pixmap = PySide6.QtWidgets.QStyle.SP_DialogApplyButton #Checkmark
		self._selection_icon = PySide6.QtWidgets.QApplication.style().standardIcon(self._selection_pixmap)
		self._prev_selection = None

		if allow_select_files_only:
			self._allow_select_files_only = True
	
	def resetHighlight(self) -> None:
		"""Reset the highlight"""
		self._selected_path = None
		if self._prev_selection:
			self.dataChanged.emit(self._prev_selection, self._prev_selection) #Also update the icon of the previously highlighted item
			self._prev_selection = None
		self.highlightPathChanged.emit(None)

	def getHighlightPath(self) -> str:
		"""Get the currently highlighted path"""
		return self._selected_path

	def setHightLightPath(self, path: str) -> None:
		self._selected_path = path
		self.highlightPathChanged.emit(self._selected_path)

	def setHightLight(self, selection: PySide6.QtCore.QModelIndex) -> None:
		"""Set the current selection to the model"""
		log.info(f"Trying to set model selection to: {self.filePath(selection)}")

		if self._allow_select_files_only and not os.path.isfile(self.filePath(selection)): #Skip selection if only files are allowed and the selection is not a file
			log.warn(f"Selection is not a file, skipping selection: {self.filePath(selection)}")
			return

		self._selected_path = self.filePath(selection)
		
		if self._prev_selection:
			self.dataChanged.emit(self._prev_selection, self._prev_selection)#, [PySide6.QtCore.Qt.DisplayRole, PySide6.QtCore.Qt.FileIconRole])

		new_selection = self.index(selection.row(), 0, selection.parent()) #Get index of first column (this is where the icon resides)
		self._prev_selection = PySide6.QtCore.QPersistentModelIndex(new_selection)
		self.dataChanged.emit(new_selection, new_selection)#, [PySide6.QtCore.Qt.FileIconRole])
		self.highlightPathChanged.emit(self._selected_path)



	def data(self, index: PySide6.QtCore.QModelIndex, role: int = PySide6.QtCore.Qt.DisplayRole) -> typing.Any:

		#TODO: what if highlighted file changed? (e.g. file renamed/removed)

		#If first column and fileIconRole, return selection icon
		if role == PySide6.QtWidgets.QFileSystemModel.FileIconRole and index.column() == 0 and self._selected_path and (self.filePath(index) == self._selected_path):
			#Return arrow icon if selected
			return self._selection_icon

		return super().data(index, role)