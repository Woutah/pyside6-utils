"""Implements a QMdiArea with some extra functionality."""
import enum
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
	TODO: autoscale subwindows when resizing the mdi area - even when not tiled
	"""
	DESCRIPTION = "Implements a QMdiArea with some extra functionality."

	class DisplayMode(enum.Enum):
		"""Enum for the display mode of the mdi area.
		"""
		TILED = enum.auto()
		CASCADED = enum.auto()
		#TODO: zoomed?

	def __init__(self,
	    	parent: QtWidgets.QWidget | None = None,
			re_tile_cascade_on_subwindow_changes : bool = True #Retile the subwindows when a subwindow is added/removed
		) -> None:
		super().__init__(parent)
		self._subwindows : list[QtWidgets.QMdiSubWindow] = []
		self.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)
		self.customContextMenuRequested.connect(self.context_menu_requested)

		self._cur_display_method = ExtendedMdiArea.DisplayMode.TILED #By default, tile the subwindows
		self._re_tile_cascade_on_subwindow_changes = re_tile_cascade_on_subwindow_changes

		self.setActivationOrder(QtWidgets.QMdiArea.WindowOrder.StackingOrder) #Set the activation order to creation order


	def order_windows_by_titles(self, titles : List[str]) -> None:
		"""Orders the subwindows by the given titles.

		Args:
			titles (List[str]): The titles to order the subwindows by
		"""
		#Sort the subwindows by the given titles
		self._subwindows.sort(key = lambda subwindow: titles.index(subwindow.windowTitle()))


	def order_windows_by_windowlist(self, windowlist : List[QtWidgets.QMdiSubWindow]) -> None:
		"""Orders the subwindows by the given windowlist. If a subwindow is not in the windowlist, it is moved to the end.

		Args:
			windowlist (List[QtWidgets.QMdiSubWindow]): The windowlist to order the subwindows by
		"""
		#Sort the subwindows by the given windowlist
		self._subwindows.sort(key = lambda subwindow: windowlist.index(subwindow) if subwindow in windowlist else len(windowlist))

	def addSubWindow(self,
		  		widget: QtWidgets.QWidget,
				flags: QtCore.Qt.WindowType = QtCore.Qt.WindowType() #type:ignore
			) -> QtWidgets.QMdiSubWindow:
		"""Adds a subwindow to the mdi area.
		"""
		subwindow = super().addSubWindow(widget, flags)
		self._subwindows.append(subwindow) #Keep track of window
		subwindow.show()
		if self._cur_display_method == ExtendedMdiArea.DisplayMode.TILED\
				and self._re_tile_cascade_on_subwindow_changes: #If tiled -> retile, nothing if tabed/cascaded.
			self.tileSubWindows()

		return subwindow

	def removeSubWindow(self, widget: QtWidgets.QWidget) -> None:
		self._subwindows.remove(widget) #Keep track of window #type:ignore
		if self._cur_display_method == ExtendedMdiArea.DisplayMode.TILED and self._re_tile_cascade_on_subwindow_changes:
			self.tileSubWindows()
		return super().removeSubWindow(widget)


	def set_tabbified(self, tabbified : bool) -> None:
		"""Set the tabbified state of the mdi area.
		Args:
			tabbified (bool): Whether the mdi area should be tabbified
		"""
		if self.viewMode() == QtWidgets.QMdiArea.ViewMode.TabbedView and tabbified or\
				self.viewMode() == QtWidgets.QMdiArea.ViewMode.SubWindowView and not tabbified:
			#If no change -> continue
			return

		if tabbified:
			self.setViewMode(QtWidgets.QMdiArea.ViewMode.TabbedView)
		else:
			self.setViewMode(QtWidgets.QMdiArea.ViewMode.SubWindowView)

		for window in self._subwindows:
			if isinstance(window, FramelessMdiWindow.FramelessMdiWindow):
				window.set_tabbed_mode(tabbified)

	def is_tabbified(self)-> bool:
		"""Returns whether the mdi area is currently tabbified"""
		return self.viewMode() == QtWidgets.QMdiArea.ViewMode.TabbedView

	def toggle_tabbified(self) -> None:
		"""Toggles the tabbed view of the mdi area.
		"""
		self.set_tabbified(not self.is_tabbified())

	def tileSubWindows(self) -> None:
		"""Tiles the subwindows, also untabs windows if current state is tabbed"""
		self.set_tabbified(False)
		self._cur_display_method = ExtendedMdiArea.DisplayMode.TILED
		for window in self._subwindows[::-1]:
			#To get the appropriate order, we activate the window, and then tile the subwindows
			self.setActiveSubWindow(window)

		return super().tileSubWindows()

	def cascadeSubWindows(self) -> None:
		"""Cascades the subwindows, also untabs windows if current state is tabbed"""
		self.set_tabbified(False)
		self._cur_display_method = ExtendedMdiArea.DisplayMode.CASCADED
		return super().cascadeSubWindows()

	def add_actions_to_menu(self, menu : QtWidgets.QMenu) -> None:
		"""Adds all available actions of this widget to the given menu.
		"""
		tile_submenu = menu.addMenu("Tile")
		tile_submenu.addAction("Tile", self.tileSubWindows)
		tile_submenu.addAction("Cascade", self.cascadeSubWindows)
		show_hidden = menu.addMenu("Un-minimize")
		for subwindow in self._subwindows:
			if subwindow.isMinimized():
				show_hidden.addAction(subwindow.windowTitle(), subwindow.showNormal)
		if show_hidden.isEmpty():
			show_hidden.setEnabled(False)

		bring_to_front = menu.addMenu("Bring to front")
		for subwindow in self._subwindows:
			bring_to_front.addAction(subwindow.windowTitle(), lambda subwindow=subwindow: self.setActiveSubWindow(subwindow))

		menu.addAction("Toggle Tabbed View", self.toggle_tabbified)


	def context_menu_requested(self, pos: QtCore.QPoint) -> None:
		"""Shows a context menu with options at the given position.
		"""
		menu = QtWidgets.QMenu()
		self.add_actions_to_menu(menu)
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
		mdi_window.show()
		mdi_windows.append(mdi_window)

	area.tileSubWindows()
	#Tile by order of creation
	# area.cascadeSubWindows()


	sys.exit(app.exec())
