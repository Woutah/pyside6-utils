

from typing import Union
import PySide6.QtWidgets as QtWidgets
from PySide6.QtCore import Qt
from PySide6 import QtCore
import PySide6.QtCore
import PySide6.QtGui
import typing
from PySide6.QtGui import QKeySequence, QShortcut
import PySide6.QtWidgets
from PySide6Widgets.Models.FileExplorerModel import FileExplorerModel
import pandas as pd
import os
import winshell
import shutil
# from Models.FileExplorerModel import FileExplorerModel
import logging
log = logging.getLogger(__name__)
	
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
		log.info(f"Deleted file: {self._deleted_file_path} - {self._original_file_path}")


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


class FileNameLineEdit(QtWidgets.QLineEdit):
	"""Normally, we would set the selection in the QStyledItemDelegate, but 
	This does not work as QT calls selectAll() after the editor is created,
	so we need to change the selection to not include the file extension
	after the editor is created and after setEditorData is called.
	""" 
	def showEvent(self, event) -> None:
		super().showEvent(event)
		text = self.text()
		self.setSelection(0, len(os.path.splitext(text)[0]))
	


#Delegate class which enabled editing of the file name without also editing the extension
class FileNameDelegate(QtWidgets.QStyledItemDelegate):

	def __init__(self, parent: typing.Optional[PySide6.QtCore.QObject] = None) -> None:
		super().__init__(parent)
	
	def createEditor(self, parent : QtWidgets.QWidget, option : QtWidgets.QStyleOptionViewItem, index : QtCore.QModelIndex) -> QtWidgets.QWidget:
		#Check if the editor is a QLineEdit
		if not index.isValid():
			return 0
		
		if type(index.data(QtCore.Qt.EditRole)) == str: #To not-select the file extension when editing
			return FileNameLineEdit(parent)

		return super().createEditor(parent, option, index)


class FileExplorerView(QtWidgets.QTreeView):
	DESCRIPTION = "Simple file explorer view that lets the user select files"


	def __init__(self, parent: typing.Optional[PySide6.QtWidgets.QWidget] = None) -> None:
		super().__init__(parent)



		self._undo_stack = PySide6.QtGui.QUndoStack(self)

		#Create context menu
		self._context_menu = QtWidgets.QMenu(self)


		self.actionUndo = self._context_menu.addAction("Undo")
		self.actionRedo = self._context_menu.addAction("Redo")
		self.actionCopy = self._context_menu.addAction("Copy")
		self.actionCut = self._context_menu.addAction("Cut")
		self.actionPaste = self._context_menu.addAction("Paste")
		self.actionDelete = self._context_menu.addAction("Delete")
		self.actionRename = self._context_menu.addAction("Rename")
		self.actionHighlight = self._context_menu.addAction("Select")
		self.actionNewFolder = self._context_menu.addAction("New Folder")

		# self.actionUndo = PySide6.QtGui.QAction(self, "Undo")
		# self.actionRedo = PySide6.QtGui.QAction(self, "Redo")
		# self.actionCopy = PySide6.QtGui.QAction(self, "Copy")
		# self.actionPaste = PySide6.QtGui.QAction(self, "Paste")
		# self.actionDelete = PySide6.QtGui.QAction(self, "Delete")
		# self.actionRename = PySide6.QtGui.QAction(self, "Rename")
		# self.actionHighlight = PySide6.QtGui.QAction(self, "Select")


		self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
		self.customContextMenuRequested.connect(self.customMenuRequested)

		self.setItemDelegateForColumn(0, FileNameDelegate(self)) #Set delegate for first column (filename)

		#Make sortable
		self.setSortingEnabled(True)
		
		#Add 
		# self.setContextMenuPolicy(PySide6.QtCore.Qt.ActionsContextMenu)
		self.addAction(self.actionCopy)
		self.addAction(self.actionCut)
		self.addAction(self.actionPaste)
		self.addAction(self.actionDelete)
		self.addAction(self.actionHighlight)
		self.addAction(self.actionUndo)
		self.addAction(self.actionRedo)
		self.addAction(self.actionNewFolder)
		# self.addAction(self._rename_action)
		

		#Also create shortcuts and link them to actions
		self._undo_shortcut = PySide6.QtCore.QCoreApplication.translate("ApplyMachineLearningWindow", u"Ctrl+Z", None)
		self._redo_shortcut = PySide6.QtCore.QCoreApplication.translate("FileExplorerView", u"Ctrl+Y", None)
		self._copy_shortcut = PySide6.QtCore.QCoreApplication.translate("FileExplorerView", u"Ctrl+C", None)
		self._cut_shortcut = PySide6.QtCore.QCoreApplication.translate("FileExplorerView", u"Ctrl+X", None)
		self._paste_shortcut = PySide6.QtCore.QCoreApplication.translate("FileExplorerView", u"Ctrl+V", None)
		self._delete_shortcut = PySide6.QtCore.QCoreApplication.translate("FileExplorerView", u"Del", None)
		self._rename_shortcut = PySide6.QtCore.QCoreApplication.translate("FileExplorerView", u"F2", None)
		self._highlight_shortcut = PySide6.QtCore.QCoreApplication.translate("FileExplorerView", u"", None)
		self._new_folder_shortcut = PySide6.QtCore.QCoreApplication.translate("FileExplorerView", u"Ctrl+Shift+N", None)


		
		self.actionUndo.setShortcut(self._undo_shortcut)
		self.actionRedo.setShortcut(self._redo_shortcut)
		self.actionCopy.setShortcut(self._copy_shortcut)
		self.actionCut.setShortcut(self._cut_shortcut)
		self.actionPaste.setShortcut(self._paste_shortcut)
		self.actionDelete.setShortcut(self._delete_shortcut)
		self.actionRename.setShortcut(self._rename_shortcut)
		self.actionHighlight.setShortcut(self._highlight_shortcut)
		self.actionNewFolder.setShortcut(self._new_folder_shortcut)


		# self.actionUndo.setShortcutContext(PySide6.QtCore.Qt.WidgetShortcut)
		# self.actionRedo.setShortcutContext(PySide6.QtCore.Qt.WidgetShortcut)
		# self.actionCopy.setShortcutContext(PySide6.QtCore.Qt.WidgetShortcut)
		# self.actionPaste.setShortcutContext(PySide6.QtCore.Qt.WidgetShortcut)
		# self.actionDelete.setShortcutContext(PySide6.QtCore.Qt.WidgetShortcut)
		# self.actionRename.setShortcutContext(PySide6.QtCore.Qt.WidgetShortcut)
		# self.actionHighlight.setShortcutContext(PySide6.QtCore.Qt.WidgetShortcut)

		
		# self._undo_action.setShortcutContext(Qt.WidgetShortcut)
		# self._redo_action.setShortcutContext(Qt.WidgetShortcut)


		#Link actions to function
		# self._copy_action.triggered.connect(self.copySelection)
		# self._paste_action.triggered.connect(self.pasteSelection)
		self.actionRedo.triggered.connect(self.redoAction)
		self.actionUndo.triggered.connect(self.undoAction)
		self.actionCopy.triggered.connect(self.copyAction)
		self.actionCut.triggered.connect(self.cutAction)
		self.actionPaste.triggered.connect(self.pasteAction)
		self.actionDelete.triggered.connect(self.deleteSelection)
		self.actionRename.triggered.connect(self.renameSelection)
		self.actionHighlight.triggered.connect(self.highlightSelection)
		self.actionNewFolder.triggered.connect(self.createNewFolder)

		self._highlight = None

		#Catch double-click event on file
		# self.doubleClicked.connect(self.onDoubleClick)
		self.doubleClicked.connect(self.highlightSelection)

		self._copied_file_path = None #If copy is pressed, this will be set to the path of the selected file
		self._cut_mode = False


	def createNewFolder(self):
		index = self.currentIndex()
		if index.isValid():
			path = self.model().filePath(index)				
			if not os.path.isdir(path):
				path = os.path.dirname(path)

			new_folder_name = "New Folder"
			new_folder_path = os.path.join(path, new_folder_name)
			if os.path.exists(new_folder_path):
				folder_index = 1
				while(os.path.exists(new_folder_path)):
					new_folder_name = f"New Folder ({folder_index})"
					new_folder_path = os.path.join(path, new_folder_name)
					folder_index += 1
			os.mkdir(new_folder_path)
			# self.model().refresh(self.model().parent(index))
			# self.model().setHightLightPath(new_folder_path)
			# self.edit(index)
			new_index = self.model().index(new_folder_path)
			self.setCurrentIndex(new_index)
			self.edit(new_index)
		

	def customMenuRequested(self, pos):
		log.info("Custom menu requested")

		transparent_font = PySide6.QtGui.QFont()
		#Make alpha channel of font 0.5

		#If redo is not possible, disable it
		self.actionRedo.setVisible(self._undo_stack.canRedo()) #Grey out redo if not possible 
		self.actionUndo.setVisible(self._undo_stack.canUndo()) #Grey out undo if not possible
		self.actionPaste.setVisible(self._copied_file_path is not None)

		self._context_menu.popup(self.mapToGlobal(pos))

	def setModel(self, model: PySide6.QtCore.QAbstractItemModel) -> None:
		assert(isinstance(model, FileExplorerModel))
		return super().setModel(model)

	def highlightSelection(self):
		log.info("Setting hightlight selection in view")
		model = self.model()
		if model and isinstance(model, FileExplorerModel):
			self._highlight = self.model().filePath(self.currentIndex())
			log.info("Is instance of FileExplorerModel, now trying to set")
			model.setHightLight(self.currentIndex())
			log.info("Done setting in model")


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

	def model(self) -> FileExplorerModel:  #FileExplorerModel type should be enforced by SetModel
		# assert(isinstance(model, FileExplorerModel))
		return super().model()

	def copyAction(self):
		#Get the current index
		index = self.currentIndex()
		#Get the file path
		self._copied_file_path = self.model().filePath(index)
		self._cut_mode = False
		log.info(f"Copied file path: {self._copied_file_path}")
	
	def cutAction(self):
		#Get the current index
		index = self.currentIndex()
		#Get the file path
		self._copied_file_path = self.model().filePath(index)
		self._cut_mode = True

	def pasteAction(self):
		if self._copied_file_path and os.path.exists(self._copied_file_path):
			#Get the current index
			index = self.currentIndex()
			if not index.isValid():
				log.info(f"Could not paste due to no destination folder being selected")
				return
			#Get the file path
			file_path = self.model().filePath(index)

			#Get the folder path
			folder_path = file_path
			if not os.path.isdir(file_path):
				folder_path = os.path.dirname(file_path)

			#Get the current file name
			copied_file_name = os.path.basename(self._copied_file_path)
			new_file_name = copied_file_name
			if os.path.exists(os.path.join(folder_path, new_file_name)):
				copied_file_base_name, copied_file_extension = os.path.splitext(new_file_name)
				new_file_name = copied_file_base_name + " - Copy" + copied_file_extension
				file_index = 1
				while(os.path.exists(os.path.join(folder_path, new_file_name))):
					new_file_name =  f"{copied_file_base_name} - Copy ({file_index}){copied_file_extension}"
					file_index += 1

			#Copy the file
			if self._cut_mode:
				shutil.move(self._copied_file_path, os.path.join(folder_path, new_file_name))
			else:
				shutil.copy(self._copied_file_path, os.path.join(folder_path, new_file_name)) 
			log.info(f"Copied file: {self._copied_file_path} to {os.path.join(folder_path, new_file_name)}")
		else:
			log.warning(f"Could not paste copied file at path: {self._copied_file_path}")




	def redoAction(self):
		self._undo_stack.redo()

	def undoAction(self):
		self._undo_stack.undo()


	def deleteSelection(self):
		index = self.currentIndex()
		self._undo_stack.push(DeleteAction(self.model(), index))
		

	def renameSelection(self):
		print("renaming")
		#Get the current index
		index = self.currentIndex()
		
		#Start rename operation
		self.edit(index)
	
	


if __name__ == "__main__":
	import sys

	formatter = logging.Formatter("[{pathname:>90s}:{lineno:<4}]  {levelname:<7s}   {message}", style='{')
	handler = logging.StreamHandler()
	handler.setFormatter(formatter)
	logging.basicConfig(
		handlers=[handler],
		level=logging.DEBUG) #Without time

	app = QtWidgets.QApplication(sys.argv)
	view = FileExplorerView()
	model = FileExplorerModel()

	model.setReadOnly(False)
	#Make view editable
	model.setRootPath(PySide6.QtCore.QDir.rootPath()) #Only update to changes in MachineLearningSettingsPath

	view.setModel(model)
	#Set size to 800x600
	view.resize(800, 600)
	#fit the columns to the content
	view.header().setSectionResizeMode(QtWidgets.QHeaderView.ResizeToContents)
	view.show()
	#Set path to C:\Users\user\Documents\radial_drilling\PySide6-Widgets\Examples\Temp
	view.setRootIndex(model.index("C:\\Users\\user\\Documents\\Temp"))
	sys.exit(app.exec())