"""
Implements QFileSystemModel with the added ability to highlight a single file - which puts an icon next to the file
and sets it to bold.
"""
import logging
import os
import typing

from PySide6 import QtCore, QtGui, QtWidgets

log = logging.getLogger(__name__)

class FileExplorerModel(QtWidgets.QFileSystemModel):
	"""A QFileSystemModel that also allows for hightlighting of a single file, for example when selecting a file for
	 editing pruposes
	"""

	highlightPathChanged = QtCore.Signal(str)

	def __init__(self, parent: typing.Optional[QtCore.QObject] = None, allow_select_files_only=True) -> None:
		super().__init__(parent)
		self._selected_path = None

		self._selection_pixmap = QtWidgets.QStyle.StandardPixmap.SP_DialogApplyButton #Checkmark
		self._selection_icon = QtWidgets.QApplication.style().standardIcon(self._selection_pixmap)
		self._prev_selection = None

		if allow_select_files_only:
			self._allow_select_files_only = True

	def reset_hightlight(self) -> None:
		"""Reset the highlight"""
		self._selected_path = None
		if self._prev_selection:
			self.dataChanged.emit(self._prev_selection, self._prev_selection) #Update the icon of prev. highlighted item
			self._prev_selection = None
		self.highlightPathChanged.emit(None)

	def get_hightlight_path(self) -> str | None:
		"""Get the currently highlighted path"""
		return self._selected_path

	def set_hightlight_using_path(self, path: str | None) -> None:
		"""Set the current highlight to the given path
		
		Args:
			path (str | None): The path to highlight (or None to reset)
		"""
		self._selected_path = path
		self.highlightPathChanged.emit(self._selected_path)

	def set_highlight_using_index(self, selection: QtCore.QModelIndex) -> None:
		"""Set the current selection to the model"""
		log.info(f"Trying to set model selection to: {self.filePath(selection)}")

		if self._allow_select_files_only and not os.path.isfile(self.filePath(selection)): #Skip selection if only
				#files are allowed and the selection is not a file
			log.warning(f"Selection is not a file, skipping selection: {self.filePath(selection)}")
			return

		self._selected_path = self.filePath(selection)

		if self._prev_selection:
			self.dataChanged.emit(self._prev_selection, self._prev_selection)

		new_selection = self.index(selection.row(), 0, selection.parent()) #Get index of first column (icon)
		self._prev_selection = QtCore.QPersistentModelIndex(new_selection)
		self.dataChanged.emit(new_selection, new_selection)#, [QtCore.Qt.FileIconRole])
		self.highlightPathChanged.emit(self._selected_path)



	def data(self,
			index: QtCore.QModelIndex,
			role: int = QtCore.Qt.ItemDataRole.DisplayRole) -> typing.Any:

		#TODO: what if highlighted file changed? (e.g. file renamed/removed)

		#If first column and fileIconRole, return selection icon
		if role == QtWidgets.QFileSystemModel.Roles.FileIconRole \
				and index.column() == 0 \
				and self._selected_path \
				and (self.filePath(index) == self._selected_path):
			#Return arrow icon if selected
			return self._selection_icon

		return super().data(index, role)



if __name__ == "__main__":
	print("Testing FileExplorerModel")
	app = QtWidgets.QApplication([])
	# model = FileExplorerModel()
	model = QtWidgets.QFileSystemModel()

	#Get the current path
	current_path = os.path.dirname(os.path.realpath(__file__))

	#Set editable
	model.setReadOnly(False)
	print(current_path)
	model.setRootPath(current_path)


	view = QtWidgets.QTreeView()
	view.setModel(model)
	view.setRootIndex(model.index(current_path))
	view.show()

	app.exec()


	print("Done testing FileExplorerModel")
