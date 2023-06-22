"""Implements a custom view for a file explorer that adds some shortcuts and the possibility to undo/redo certain
actions
"""

# from Models.FileExplorerModel import FileExplorerModel
import logging
import os
import shutil
import typing
from abc import abstractmethod

import winshell
from PySide6 import QtCore, QtGui, QtWidgets

from pyside6_utils.models.file_explorer_model import FileExplorerModel

log = logging.getLogger(__name__)


class UndoAbleAction(QtGui.QUndoCommand): #TODO: also inherit from ABC
	"""Abstract class for an undo-able action"""
	@abstractmethod
	def text(self) -> str:
		"""Returns the text that should be displayed in the undo/redo menu"""
		raise NotImplementedError

	@abstractmethod
	def undo(self):
		"""Undo the action"""
		raise NotImplementedError

	@abstractmethod
	def redo(self):
		"""Redo the action"""
		raise NotImplementedError


class DeleteAction(UndoAbleAction):
	"""A delete-file action that can be undone and redone"""
	def __init__(
				self,
				file_system_model : QtWidgets.QFileSystemModel,
				index,
				parent: typing.Optional[QtGui.QUndoCommand] = None #pylint: disable=unused-argument
			) -> None:
		super().__init__()
		self._original_file_path = file_system_model.filePath(index)
		self._deleted_file_path = None

	def text(self) -> str:
		return "Delete"

	def undo(self):
		if self._deleted_file_path: #TODO: check if this works on linux-based systems
			os.rename(self._deleted_file_path, self._original_file_path) #Restore file
		else: #TODO: This only support windows or OS'es that return deleted-file-paths when using QFile.moveToTrash
			# recycled_files = list(winshell.recycle_bin())
			winshell.undelete(self._original_file_path.replace("/", os.sep)) #Path returned by QFileSystemModel is in
				#unix format, so we need to convert it to windows format

	def redo(self):
		QtCore.QFile.moveToTrash(self._original_file_path, self._deleted_file_path) #type: ignore
		log.info(f"Deleted file: {self._deleted_file_path} - {self._original_file_path}")



class FileNameLineEdit(QtWidgets.QLineEdit):
	"""Normally, we would set the selection in the QStyledItemDelegate, but
	This does not work as QT internally calls selectAll() after the editor is created,
	so we need to change the selection to not include the file extension
	after the editor is created and after setEditorData is called.

	This simple wrapper around QLineEdit makes sure only the file name is selected on showEvent.
	"""
	def showEvent(self, event) -> None:
		super().showEvent(event)
		text = self.text()
		self.setSelection(0, len(os.path.splitext(text)[0]))



#Delegate class which enabled editing of the file name without also editing the extension
class FileNameDelegate(QtWidgets.QStyledItemDelegate):
	"""Delegate class which enabled editing of the file name without also editing the extension

	NOTE: We must implement a custom widget because otherwise QT will call selectAll() after the editor is created,
	rendering the selection of only the file name in this delegate useless
	"""
	def __init__(self, parent: typing.Optional[QtCore.QObject] = None) -> None:
		super().__init__(parent)

	def createEditor(self,
				parent : QtWidgets.QWidget,
				option : QtWidgets.QStyleOptionViewItem,
				index : QtCore.QModelIndex
			) -> QtWidgets.QWidget | None:
		#Check if the editor is a QLineEdit
		if not index.isValid():
			return None

		if isinstance(index.data(QtCore.Qt.ItemDataRole.EditRole), str): #To not-select the file extension when editing
			return FileNameLineEdit(parent)

		return super().createEditor(parent, option, index)


class FileExplorerView(QtWidgets.QTreeView):
	"""View meant for a custom file-explorer model built on top of QFileSystemModel with extra functionalities"""
	DESCRIPTION = "Simple file explorer view that lets the user select files"


	def __init__(self, parent: typing.Optional[QtWidgets.QWidget] = None) -> None:
		super().__init__(parent)



		self._undo_stack = QtGui.QUndoStack(self)

		#Create context menu
		self._context_menu = QtWidgets.QMenu(self)


		self.action_undo = self._context_menu.addAction("Undo")
		self.action_redo = self._context_menu.addAction("Redo")
		self.action_copy = self._context_menu.addAction("Copy")
		self.action_cut = self._context_menu.addAction("Cut")
		self.action_paste = self._context_menu.addAction("Paste")
		self.action_delete = self._context_menu.addAction("Delete")
		self.action_rename = self._context_menu.addAction("Rename")
		self.action_highlight = self._context_menu.addAction("Select")
		self.action_new_folder = self._context_menu.addAction("New Folder")


		self.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)
		self.customContextMenuRequested.connect(self.custom_menu_requested)

		self.setItemDelegateForColumn(0, FileNameDelegate(self)) #Set delegate for first column (filename)

		#Make sortable
		self.setSortingEnabled(True)

		#Add
		# self.setContextMenuPolicy(QtCore.Qt.ActionsContextMenu)
		self.addAction(self.action_copy)
		self.addAction(self.action_cut)
		self.addAction(self.action_paste)
		self.addAction(self.action_delete)
		self.addAction(self.action_highlight)
		self.addAction(self.action_undo)
		self.addAction(self.action_redo)
		self.addAction(self.action_new_folder)
		# self.addAction(self._rename_action)


		#Also create shortcuts and link them to actions
		self._undo_shortcut = QtCore.QCoreApplication.translate("ApplyMachineLearningWindow", "Ctrl+Z", None) #type: ignore
		self._redo_shortcut = QtCore.QCoreApplication.translate("FileExplorerView", "Ctrl+Y", None) #type: ignore
		self._copy_shortcut = QtCore.QCoreApplication.translate("FileExplorerView", "Ctrl+C", None) #type: ignore
		self._cut_shortcut = QtCore.QCoreApplication.translate("FileExplorerView", "Ctrl+X", None) #type: ignore
		self._paste_shortcut = QtCore.QCoreApplication.translate("FileExplorerView", "Ctrl+V", None) #type: ignore
		self._delete_shortcut = QtCore.QCoreApplication.translate("FileExplorerView", "Del", None) #type: ignore
		self._rename_shortcut = QtCore.QCoreApplication.translate("FileExplorerView", "F2", None) #type: ignore
		self._highlight_shortcut = QtCore.QCoreApplication.translate("FileExplorerView", "", None) #type: ignore
		self._new_folder_shortcut = QtCore.QCoreApplication.translate("FileExplorerView", "Ctrl+Shift+N", None) #type: ignore



		self.action_undo.setShortcut(self._undo_shortcut)
		self.action_redo.setShortcut(self._redo_shortcut)
		self.action_copy.setShortcut(self._copy_shortcut)
		self.action_cut.setShortcut(self._cut_shortcut)
		self.action_paste.setShortcut(self._paste_shortcut)
		self.action_delete.setShortcut(self._delete_shortcut)
		self.action_rename.setShortcut(self._rename_shortcut)
		self.action_highlight.setShortcut(self._highlight_shortcut)
		self.action_new_folder.setShortcut(self._new_folder_shortcut)


		#Link actions to function
		self.action_redo.triggered.connect(self.redo_action)
		self.action_undo.triggered.connect(self.undo_action)
		self.action_copy.triggered.connect(self.copy_action)
		self.action_cut.triggered.connect(self.cut_action)
		self.action_paste.triggered.connect(self.paste_action)
		self.action_delete.triggered.connect(self.delete_selection)
		self.action_rename.triggered.connect(self.rename_selection)
		self.action_highlight.triggered.connect(self.hightlight_selection)
		self.action_new_folder.triggered.connect(self.create_new_folder)

		self._highlight = None

		#Catch double-click event on file
		# self.doubleClicked.connect(self.onDoubleClick)
		self.doubleClicked.connect(self.hightlight_selection)

		self._copied_file_path = None #If copy is pressed, this will be set to the path of the selected file
		self._cut_mode = False


	def create_new_folder(self):
		"""Create a new folder at the current location and edit it"""
		index = self.currentIndex()
		if index.isValid():
			path = self.model().filePath(index)
			if not os.path.isdir(path):
				path = os.path.dirname(path)

			new_folder_name = "New Folder"
			new_folder_path = os.path.join(path, new_folder_name)
			if os.path.exists(new_folder_path):
				folder_index = 1
				while os.path.exists(new_folder_path):
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


	def custom_menu_requested(self, pos):
		"""Show the custom menu at the given position"""
		log.info("Custom menu requested")
		#Make alpha channel of font 0.5

		#If redo is not possible, disable it
		self.action_redo.setVisible(self._undo_stack.canRedo()) #Grey out redo if not possible
		self.action_undo.setVisible(self._undo_stack.canUndo()) #Grey out undo if not possible
		self.action_paste.setVisible(self._copied_file_path is not None)

		self._context_menu.popup(self.mapToGlobal(pos))

	def setModel(self, new_model: QtCore.QAbstractItemModel) -> None:
		assert isinstance(new_model, FileExplorerModel)
		return super().setModel(new_model)

	def hightlight_selection(self):
		"""Hightlight the current selection using the model"""
		log.info("Setting hightlight selection in view")
		cur_model = self.model()
		if cur_model and isinstance(cur_model, FileExplorerModel):
			self._highlight = self.model().filePath(self.currentIndex())
			log.info("Is instance of FileExplorerModel, now trying to set")
			cur_model.set_highlight_using_index(self.currentIndex())
			log.info("Done setting in model")


	def model(self) -> FileExplorerModel:  #FileExplorerModel type should be enforced by SetModel
		# assert(isinstance(model, FileExplorerModel))
		model = super().model()
		assert isinstance(model, FileExplorerModel)
		return model

	def copy_action(self):
		"""Copy the selected file (to be pasted later)"""
		#Get the current index
		index = self.currentIndex()
		#Get the file path
		self._copied_file_path = self.model().filePath(index)
		self._cut_mode = False
		log.info(f"Copied file path: {self._copied_file_path}")

	def cut_action(self):
		"""Cut the selected file"""
		#Get the current index
		index = self.currentIndex()
		#Get the file path
		self._copied_file_path = self.model().filePath(index)
		self._cut_mode = True

	def paste_action(self):
		"""Paste the copied file to the current folder"""
		if self._copied_file_path and os.path.exists(self._copied_file_path):
			#Get the current index
			index = self.currentIndex()
			if not index.isValid():
				log.info("Could not paste due to no destination folder being selected")
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




	def redo_action(self):
		"""Redo the last action"""
		self._undo_stack.redo()

	def undo_action(self):
		"""Undo the last action"""
		self._undo_stack.undo()


	def delete_selection(self):
		"""Delete the selected file"""
		index = self.currentIndex()
		self._undo_stack.push(DeleteAction(self.model(), index))


	def rename_selection(self):
		"""Rename the selected file"""
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

	test_app = QtWidgets.QApplication(sys.argv)
	test_view = FileExplorerView()
	test_model = FileExplorerModel()

	test_model.setReadOnly(False)
	#Make view editable
	test_model.setRootPath(QtCore.QDir.rootPath()) #Only update to changes in MachineLearningSettingsPath

	test_view.setModel(test_model)
	#Set size to 800x600
	test_view.resize(800, 600)
	#fit the columns to the content
	test_view.header().setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
	test_view.show()
	#Set path to C:\Users\user\Documents\radial_drilling\Widgets\Examples\Temp
	test_view.setRootIndex(test_model.index("C:\\Users\\user\\Documents\\Temp"))
	sys.exit(test_app.exec())
