"""Implements a QMdiArea with some extra functionality."""
from typing import List
from PySide6 import QtCore, QtGui, QtWidgets
import PySide6Widgets.Widgets.FramelessMdiWindow as FramelessMdiWindow


class ExtendedMdiArea(QtWidgets.QMdiArea):
	"""Implements a QMdiArea with some extra functionality.
	E.g.:
	-Zooming in/out on a single panel
	-Context menu for sorting, un-minimizing, and toggling tabbed view

	If the added windows are FramelessMdiWindows, some extra functionality is added:
	-Disable zoom/minimize/titlebar when tabbified

	TODO: save/load window layout? (e.g. when closing/opening the app)
	"""
	DESCRIPTION = "Implements a QMdiArea with some extra functionality."

	def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
		super().__init__(parent)
		self._subwindows : list[QtWidgets.QMdiSubWindow] = []
		self.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)
		self.customContextMenuRequested.connect(self.context_menu_requested)

	def addSubWindow(self,
		  		widget: QtWidgets.QWidget,
				flags: QtCore.Qt.WindowType = QtCore.Qt.WindowType() #type:ignore
			) -> QtWidgets.QMdiSubWindow:
		"""Adds a subwindow to the mdi area.
		"""
		subwindow = super().addSubWindow(widget, flags)
		self._subwindows.append(subwindow) #Keep track of window
		return subwindow

	def removeSubWindow(self, widget: QtWidgets.QWidget) -> None:
		self._subwindows.remove(widget) #Keep track of window #type:ignore
		return super().removeSubWindow(widget)

	def toggle_tabbified(self) -> None:
		"""Toggles the tabbed view of the mdi area.
		"""
		self.setViewMode(
			QtWidgets.QMdiArea.ViewMode.TabbedView
			if self.viewMode() == QtWidgets.QMdiArea.ViewMode.SubWindowView
			else QtWidgets.QMdiArea.ViewMode.SubWindowView
		)

		if self.viewMode() == QtWidgets.QMdiArea.ViewMode.TabbedView:
			for window in self._subwindows:
				if isinstance(window, FramelessMdiWindow.FramelessMdiWindow):
					window.set_tabbed_mode(True)
		else:
			for window in self._subwindows:
				if isinstance(window, FramelessMdiWindow.FramelessMdiWindow):
					window.set_tabbed_mode(False)



	def subWindowList(self,
				order: QtWidgets.QMdiArea.WindowOrder = QtWidgets.QMdiArea.WindowOrder.CreationOrder
			) -> List[QtWidgets.QMdiSubWindow]:
		"""Returns a list of subwindows in the mdi area. Used for sorting tiling/cascading."""
		if order == QtWidgets.QMdiArea.WindowOrder.CreationOrder:
			return self._subwindows

		return super().subWindowList(order)


	def context_menu_requested(self, pos: QtCore.QPoint) -> None:
		"""Shows a context menu with options to sort the subwindows.
		"""
		menu = QtWidgets.QMenu()

		tile_submenu = menu.addMenu("Tile")
		tile_submenu.addAction("Tile", self.tileSubWindows)
		tile_submenu.addAction("Cascade", self.cascadeSubWindows)

		show_hidden = menu.addMenu("Un-minimize")
		for subwindow in self._subwindows:
			if subwindow.isMinimized():
				show_hidden.addAction(subwindow.windowTitle(), subwindow.showNormal)
		if show_hidden.isEmpty():
			show_hidden.setEnabled(False)

		menu.addAction("Toggle Tabbed View", self.toggle_tabbified)

		menu.exec(self.mapToGlobal(pos))

if __name__ == "__main__":
	import sys
	app = QtWidgets.QApplication(sys.argv)
	area = ExtendedMdiArea()
	area.show()

	mdi_windows = []

	for i in range(6):
		mdi_window = FramelessMdiWindow.FramelessMdiWindow()
		mdi_window.setWindowTitle(f"Test Window {i+1}")
		label = QtWidgets.QLabel(f"Test Window {i+1}")
		label.setFont(QtGui.QFont("Arial", 20))
		mdi_window.setWidget(label)
		area.addSubWindow(mdi_window)
		area.removeSubWindow(mdi_window)
		mdi_window.show()
		mdi_windows.append(mdi_window)

	area.tileSubWindows()
	#Tile by order of creation
	# area.cascadeSubWindows()


	sys.exit(app.exec())

