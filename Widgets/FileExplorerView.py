

import PySide6.QtWidgets as QtWidgets
from PySide6.QtCore import Qt
import PySide6.QtCore
import PySide6.QtGui
import typing
from PySide6.QtGui import QKeySequence, QShortcut
from Models.FileExplorerModel import FileExplorerModel
import pandas as pd
import os
import winshell
# from Models.FileExplorerModel import FileExplorerModel
	
class DeleteAction(PySide6.QtGui.QUndoCommand):
	def __init__(self, file_system_model : QtWidgets.QFileSystemModel, index, parent: typing.Optional[PySide6.QtGui.QUndoCommand] = None) -> None:
		super().__init__()
		self._original_file_path = file_system_model.filePath(index)
		self._deleted_file_path = None

	def text(self) -> str:
		return "Delete"
	
	def undo(self):
		if self._deleted_file_path: #TODO: check if this works on linux-based systems
			os.rename(self._deleted_file_path, self._original_file_path) #Restore file
		else: #TODO: This only support windows or OS'es that return deleted-file-paths when using QFile.moveToTrash
			recycled_files = list(winshell.recycle_bin())
			winshell.undelete(self._original_file_path.replace("/", os.sep)) #Path returned by QFileSystemModel is in unix format, so we need to convert it to windows format

	def redo(self):
		succesful = PySide6.QtCore.QFile.moveToTrash(self._original_file_path, self._deleted_file_path)
		print(f"Deleted file: {self._deleted_file_path} - {self._original_file_path}")


class HighlightAction(PySide6.QtGui.QUndoCommand):
	def __init__(self, file_system_view : QtWidgets.QTreeView, current_selection, new_selection_index, parent: typing.Optional[PySide6.QtGui.QUndoCommand] = None) -> None:
		super().__init__()

		# self._original_selection = current_selection
		# self._new_selection_index = new_selection_index
		self._file_system_model = file_system_view
		self._original_file_path = file_system_view.model().filePath(current_selection)
		self._new_file_path = file_system_view.model().filePath(new_selection_index)

	def redo(self):
		self._file_system_model.setCurrentIndex(self._new_file_path)


	def undo(self):
		self._file_system_model.setCurrentIndex(self._original_file_path)



class FileExplorerView(QtWidgets.QTreeView):
	DESCRIPTION = "Simple file explorer view that lets the user select files"


	def __init__(self, parent: typing.Optional[PySide6.QtWidgets.QWidget] = None) -> None:
		super().__init__(parent)



		self._undo_stack = PySide6.QtGui.QUndoStack(self)

		#Create context menu
		self._context_menu = QtWidgets.QMenu(self)
		self._copy_action = self._context_menu.addAction("Copy")
		self._paste_action = self._context_menu.addAction("Paste")
		self._delete_action = self._context_menu.addAction("Delete")
		self._rename_action = self._context_menu.addAction("Rename")
		self._highlight_action = self._context_menu.addAction("Select")

		self._redo_action = self._context_menu.addAction("Redo")
		self._undo_action = self._context_menu.addAction("Undo")

		#Make sortable
		self.setSortingEnabled(True)
		
		#Add actions to list
		self.setContextMenuPolicy(PySide6.QtCore.Qt.ActionsContextMenu)
		# self.addAction(self._copy_action)
		# self.addAction(self._paste_action)
		self.addAction(self._delete_action)
		self.addAction(self._highlight_action)
		# self.addAction(self._rename_action)
		

		#Also create shortcuts and link them to actions
		self._copy_shortcut = QShortcut(QKeySequence("Ctrl+C"), self)
		self._pase_shortcut = QShortcut(QKeySequence("Ctrl+V"), self)
		self._delete_shortcut = QShortcut(QKeySequence("Del"), self)
		self._redo_shortcut = QShortcut(QKeySequence("Ctrl+Y"), self)
		self._undo_shortcut = QShortcut(QKeySequence("Ctrl+Z"), self)
		#on enter press, select file
		self._highlight_shortcut = QShortcut(QKeySequence("Return"), self)

		self._copy_shortcut.activated.connect(self._copy_action.trigger)
		self._pase_shortcut.activated.connect(self._paste_action.trigger)
		self._delete_shortcut.activated.connect(self._delete_action.trigger)
		self._redo_shortcut.activated.connect(self._redo_action.trigger)
		self._undo_shortcut.activated.connect(self._undo_action.trigger)
		self._highlight_shortcut.activated.connect(self._highlight_action.trigger)
		


		#Link actions to function
		# self._copy_action.triggered.connect(self.copySelection)
		# self._paste_action.triggered.connect(self.pasteSelection)
		self._delete_action.triggered.connect(self.deleteSelection)
		self._rename_action.triggered.connect(self.renameSelection)
		self._redo_action.triggered.connect(self.redoAction)
		self._undo_action.triggered.connect(self.undoAction)
		self._highlight_action.triggered.connect(self.highlightSelection)

		self._highlight = None

		#Catch double-click event on file
		# self.doubleClicked.connect(self.onDoubleClick)
		self.doubleClicked.connect(self.highlightSelection)

	def setModel(self, model: PySide6.QtCore.QAbstractItemModel) -> None:
		# assert(isinstance(model, FileExplorerModel)) #TODO: is this neccesary? 
		return super().setModel(model)

	def highlightSelection(self):
		print("Setting hightlight selection in view")
		model = self.model()
		if model and isinstance(model, FileExplorerModel):
			self._highlight = self.model().filePath(self.currentIndex())
			print("Is instance of FileExplorerModel, now trying to set")
			model.setHightLightKaas(self.currentIndex())
			print("Done setting in model")


	# def paintEvent(self, event: PySide6.QtGui.QPaintEvent) -> None:

	# 	#If path is equal to self._highlight, then highlight it
	# 	if self._highlight:
	# 		painter = PySide6.QtGui.QPainter(self.viewport())
	# 		painter.setPen(PySide6.QtGui.QPen(PySide6.QtGui.QColor(0, 0, 255), 2))
	# 		painter.drawRect(self.visualRect(self._highlight))
	# 		painter.end()

	# 	return super().paintEvent(event)


	# def onDoubleClick(self, index):
	# 	print(f"Double clicked {self.model().filePath(index)}")
	# 	# self.hightlightSelection(self.model().filePath(index))


	def redoAction(self):
		self._undo_stack.redo()

	def undoAction(self):
		self._undo_stack.undo()


	def deleteSelection(self):
		#Move selected file to trash using the MoveToTrash function
		#Get the current index
		index = self.currentIndex()
		# print(f"Now trying to delete {self.model().filePath(index)}")

		self._undo_stack.push(DeleteAction(self.model(), index))

		# index = self.currentIndex()
		# #Get the file path
		# file_path = self.model().filePath(index)
		# removed_path = PySide6.QtCore.QFile.moveToTrash(file_path)
		

		

	def renameSelection(self):
		print("renaming")
		#Get the current index
		index = self.currentIndex()
		
		#Start rename operation
		self.edit(index)
	
	


if __name__ == "__main__":
	import sys


	app = QtWidgets.QApplication(sys.argv)
	view = FileExplorerView()
	model = FileExplorerModel()

	model.setReadOnly(False)
	#Make view editable
	model.setRootPath(PySide6.QtCore.QDir.rootPath()) #Only update to changes in MachineLearningSettingsPath

	view.setModel(model)
	view.show()
	#Set path to C:\Users\user\Documents\radial_drilling\PySide6-Widgets\Examples\Temp
	view.setRootIndex(model.index("C:\\Users\\user\\Documents\\Temp"))
	sys.exit(app.exec())