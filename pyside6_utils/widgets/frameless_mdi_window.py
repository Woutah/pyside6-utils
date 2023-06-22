"""Implements a frameless Qt MDI window while retaining the move/resize controls.
A custom UI can be used, for more information, see the class documentation
"""
import enum
import logging

from PySide6 import QtCore, QtGui, QtWidgets

from pyside6_utils.ui.FramelessMdiWindow_ui import Ui_FramelessMidiWindow

log = logging.getLogger(__name__)

class SideGrip(QtWidgets.QWidget):
	""" Implements a grip for the sides of a window/mdi-window. Based on:
	https://stackoverflow.com/questions/62807295/how-to-resize-a-window-from-the-edges-after-adding-the-property-qtcore-qt-framel
	@musicamante

	Adapter for use with a QMdiSubWindow. The parent of this widget should be the QMdiSubWindow.

	TODO: also pass other window-rects to snap to edges?
	"""
	def __init__(self, parent, edge):
		QtWidgets.QWidget.__init__(self, parent)
		if edge == QtCore.Qt.Edge.LeftEdge:
			self.setCursor(QtCore.Qt.CursorShape.SizeHorCursor)
			self.resize_func = self.resize_left
		elif edge == QtCore.Qt.Edge.TopEdge:
			self.setCursor(QtCore.Qt.CursorShape.SizeVerCursor)
			self.resize_func = self.resize_top
		elif edge == QtCore.Qt.Edge.RightEdge:
			self.setCursor(QtCore.Qt.CursorShape.SizeHorCursor)
			self.resize_func = self.resize_right
		else:
			self.setCursor(QtCore.Qt.CursorShape.SizeVerCursor)
			self.resize_func = self.resize_bottom
		self.mouse_pos = None

	def resize_left(self, delta):
		"""Resize the window to the left"""
		window = self.parent()
		assert isinstance(window, QtWidgets.QMdiSubWindow)
		width = max(window.minimumWidth(), window.width() - delta.x()) #TODO: minimumsize does not seem to work?
		geo = window.geometry()
		geo.setLeft(geo.right() - width)
		window.setGeometry(geo)

	def resize_top(self, delta):
		"""Resize the window to the top"""
		window = self.parent()
		assert isinstance(window, QtWidgets.QMdiSubWindow)
		height = max(window.minimumHeight(), window.height() - delta.y())
		geo = window.geometry()
		geo.setTop(geo.bottom() - height)
		window.setGeometry(geo)

	def resize_right(self, delta):
		"""Resize the window to the right"""
		window = self.parent()
		assert isinstance(window, QtWidgets.QMdiSubWindow)
		width = max(window.minimumWidth(), window.width() + delta.x())
		window.resize(width, window.height())

	def resize_bottom(self, delta):
		"""Resize the window to the bottom"""
		window = self.parent()
		assert isinstance(window, QtWidgets.QMdiSubWindow)
		height = max(window.minimumHeight(), window.height() + delta.y())
		window.resize(window.width(), height)

	def mousePressEvent(self, event):
		if event.button() == QtCore.Qt.MouseButton.LeftButton:
			self.mouse_pos = event.position()

	def mouseMoveEvent(self, event):
		if self.mouse_pos is not None:
			delta = event.position() - self.mouse_pos
			self.resize_func(delta)

	def mouseReleaseEvent(self, event): #pylint: disable=unused-argument
		self.mouse_pos = None

class FramelessMdiWindow(QtWidgets.QMdiSubWindow):
	"""Implementation of a borderless Mdi-window using a custom UI.

	Note that the following items should be present in the passed ui, if using a custom ui:
		- contentLayout (QtWidgets.QLayout): The layout that will be used to add the content-widget
		- titleBar (QtWidgets.QWidget): The widget that will be used as the title bar, should contain the following:
			- titleLabel (QtWidgets.QLabel): The label that will be used to display the title
			- zoomButton (QtWidget.QButtton): If pressed, set window to fullscreen
			- minimizeButton (QtWidget.QButtton): If pressed, minimize the window


	If the parent of the window is ExtendedMdiArea, the following functionality will be added:
		- Right-clicking the titlebar will show the context menu for the mdi-area
		- When tabbified, the titlebar and grips will be hidden and window will be unmovable

	"""
	class DragType(enum.Enum):
		"""When a click-move is considered a Mdi-window-move"""
		TITLE_BAR = 0
		EVERYWHERE = enum.auto()

	def __init__(self,
	      		parent: QtWidgets.QWidget | None = None,
		  		flags: QtCore.Qt.WindowType = ..., #pylint: disable=unused-argument
		  		drag_type: DragType = DragType.TITLE_BAR,
				ui_class : type[Ui_FramelessMidiWindow | None] = Ui_FramelessMidiWindow,
				keep_inside_mdi_area : bool = True,
				resizeable_pix_size : int = 8, #The size of the resizeable area in pixels (around the edges), 0 for off
				moveable = True
			) -> None:
		super().__init__(parent)

		self.content = QtWidgets.QWidget()

		if ui_class is type(None):
			self.ui =  Ui_FramelessMidiWindow() #pylint: disable=invalid-name
		else:
			self.ui : Ui_FramelessMidiWindow = ui_class() #type: ignore

		assert self.ui is not None
		self.ui.setupUi(self.content)
		super().setWidget(self.content)
		self.setGeometry(self.content.geometry()) #Copy over initial geometry of the window

		self.setWindowFlags(QtCore.Qt.WindowType.FramelessWindowHint)
		self.start_mouse_pos = None
		self.start_window_pos = None
		self._drag_type = drag_type
		self._widget = None
		self._keep_inside_mdi_area = keep_inside_mdi_area
		self._resizable_pix_size = resizeable_pix_size
		self._moveable = moveable

		self.corner_grips : list[QtWidgets.QSizeGrip]= []
		for _ in range(4):
			grip = QtWidgets.QSizeGrip(self)
			grip.resize(self._resizable_pix_size, self._resizable_pix_size)
			grip.setStyleSheet("QSizeGrip { image: None;}") #Disable grip icon
			grip.setWindowFlag(QtCore.Qt.WindowType.WindowStaysOnTopHint)
			self.corner_grips.append(grip)

		self._edge_grips : dict[QtCore.Qt.Edge, SideGrip] = {}
		for edge in [QtCore.Qt.Edge.LeftEdge, QtCore.Qt.Edge.TopEdge, QtCore.Qt.Edge.RightEdge, QtCore.Qt.Edge.BottomEdge]:
			self._edge_grips[edge] = SideGrip(self, edge)
			self._edge_grips[edge].setWindowFlag(QtCore.Qt.WindowType.WindowStaysOnTopHint)

		self.ui.titleBar.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)
		self.ui.titleBar.customContextMenuRequested.connect(self.mdi_context_menu_requested)

		self.ui.zoomButton.clicked.connect(self.toggle_zoom)
		self.ui.MinimizeButton.clicked.connect(self.showMinimized)

	def set_moveable(self, moveable: bool) -> None:
		"""Sets whether the window can be moved"""
		self._moveable = moveable
		if not moveable: #Also rest the current start positions
			self.start_mouse_pos = None
			self.start_window_pos = None

	def setWindowTitle(self, arg__1: str) -> None:
		self.ui.titleLabel.setText(arg__1)
		return super().setWindowTitle(arg__1)

	def showNormal(self) -> None:
		"""When showing normal -> enable grips"""
		for grip in self.corner_grips:
			grip.show()
		for grip in self._edge_grips.values():
			grip.show()
		return super().showNormal()

	def showMaximized(self) -> None:
		"""When showing maximized -> disable grips"""
		for grip in self.corner_grips:
			grip.hide()
		for grip in self._edge_grips.values():
			grip.hide()
		return super().showMaximized()

	def toggle_zoom(self):
		"""Zooms in/out on the window"""
		if self.isMaximized():
			self.showNormal()
		else:
			self.showMaximized()

	def set_tabbed_mode(self, tabbed: bool) -> None:
		"""Sets the tabbed mode of this item, hiding the titlebar and grips/buttons"""
		self.ui.titleBar.setEnabled(not tabbed)
		self.ui.titleBar.setVisible(not tabbed)
		for grip in self.corner_grips:
			grip.setEnabled(not tabbed)
		for grip in self._edge_grips.values():
			grip.setEnabled(not tabbed)
		self.set_moveable(not tabbed)

	def mdi_context_menu_requested(self, pos: QtCore.QPoint) -> None:
		"""Pass on context menu to parent (QMdiArea) - tile/cascade etc. 
		"""
		parent = self.mdiArea()
		pos = self.ui.titleBar.mapToGlobal(pos)
		pos = parent.mapFromGlobal(pos)
		try:
			parent.context_menu_requested(pos)
		except AttributeError:
			log.debug("Parent of FramelessMdiWindow is not an ExtendedMdiArea, context menu not shown")

	def resizeEvent(self, resizeEvent: QtGui.QResizeEvent) -> None:
		"""Upon resize, make sure that all grips are at the right position"""
		super().resizeEvent(resizeEvent)
		rect = self.rect()
		self.corner_grips[0].move(rect.topLeft()) # + QtCore.QPoint(self., self._resizable_pix_size))
		self.corner_grips[1].move(rect.topRight() + QtCore.QPoint(-self._resizable_pix_size, 0))
		self.corner_grips[2].move(rect.bottomLeft() - QtCore.QPoint(0, self._resizable_pix_size))
		self.corner_grips[3].move(rect.bottomRight() - QtCore.QPoint(self._resizable_pix_size, self._resizable_pix_size))

		#Also resize/move the edge-grips
		self._edge_grips[QtCore.Qt.Edge.LeftEdge].setGeometry(
			0,
			self._resizable_pix_size,
			self._resizable_pix_size,
			self.height() - 2*self._resizable_pix_size
		)
		self._edge_grips[QtCore.Qt.Edge.TopEdge].setGeometry(
			self._resizable_pix_size,
			0,
			self.width() - 2*self._resizable_pix_size,
			self._resizable_pix_size
		)
		self._edge_grips[QtCore.Qt.Edge.RightEdge].setGeometry(
			self.width() - self._resizable_pix_size,
			self._resizable_pix_size,
			self._resizable_pix_size,
			self.height() - 2*self._resizable_pix_size
		)
		self._edge_grips[QtCore.Qt.Edge.BottomEdge].setGeometry(
			self._resizable_pix_size,
			self.height() - self._resizable_pix_size,
			self.width() - 2*self._resizable_pix_size,
			self._resizable_pix_size
		)



	def setWidget(self, widget: QtWidgets.QWidget) -> None:
		if self._widget is not None: #Set new content
			self.ui.contentLayout.removeWidget(self._widget)
		self.ui.contentLayout.insertWidget(0, widget) #Always insert at 0, so we can add a spacer to the bottom
		self._widget = widget
		self._widget.lower()
		# self._widget.setParent(self)
		self._widget.show()


	def mousePressEvent(self, event: QtGui.QMouseEvent) -> bool:
		global_mouse_pos = event.globalPosition() #mouse move results in movement so use global position to
			#avoid shaking motion
		if not self._moveable:
			return super().mousePressEvent(event) #type: ignore
		#If left-click, check if on titlebar
		if event.button() == QtCore.Qt.MouseButton.LeftButton:
			if self._drag_type == self.DragType.TITLE_BAR and\
					self.ui.titleBar.rect().contains(self.ui.titleBar.mapFromGlobal(global_mouse_pos).toPoint()):
				self.start_mouse_pos = event.globalPosition().toPoint()
				self.start_window_pos = self.pos()
			elif self._drag_type == self.DragType.EVERYWHERE:
				self.start_mouse_pos = event.globalPosition().toPoint()
				self.start_window_pos = self.pos()
		elif event.button() == QtCore.Qt.MouseButton.RightButton and\
				self.ui.titleBar.rect().contains(self.ui.titleBar.mapFromGlobal(global_mouse_pos).toPoint()):
			self.mdi_context_menu_requested(event.position().toPoint())
		return True

	def mouseReleaseEvent(self, mouseEvent: QtGui.QMouseEvent) -> bool: #pylint: disable=unused-argument
		self.start_mouse_pos = None
		self.start_window_pos = None
		return True

	def mouseMoveEvent(self, event: QtGui.QMouseEvent) -> None:
		if self.start_mouse_pos is None or self.start_window_pos is None: #If
			return
		delta = QtCore.QPoint(event.globalPosition().toPoint() - self.start_mouse_pos)
		new_window_pos = self.start_window_pos + delta
		#Check if outside of mdi-area, if so, move to edge
		if self._keep_inside_mdi_area:
			parent = self.mdiArea()
			if parent is not None and issubclass(type(parent), QtWidgets.QMdiArea):
				assert isinstance(parent, QtWidgets.QMdiArea)
				#Check if outside of parent
				new_bottom_right = new_window_pos + self.rect().bottomRight()
				if not parent.rect().contains(new_window_pos) or not parent.rect().contains(new_bottom_right):
					new_window_pos = QtCore.QPoint(
						min(max(parent.rect().left(), new_window_pos.x()), parent.rect().right() - self.width()),
						min(max(parent.rect().top(), new_window_pos.y()), parent.rect().bottom() - self.height())
					)
					self.move(new_window_pos)
					# self.start_mouse_pos = event.globalPosition().toPoint()
					return
		self.move(new_window_pos)

def run_example_app():
	"""Show example frameless window in a normal mdi area - for more functionality, see extended_mdi_area.py"""
	#pylint: disable=import-outside-toplevel
	import sys
	app = QtWidgets.QApplication(sys.argv)
	mdi_area = QtWidgets.QMdiArea()
	mdi_area.show()
	test_window = FramelessMdiWindow()
	# test_window = QtWidgets.QMdiSubWindow()
	label = QtWidgets.QLabel(" Test \n Test \n Test ")
	label.setFont(QtGui.QFont("Arial", 50))
	test_window.setWidget(label)
	mdi_area.addSubWindow(test_window)
	test_window.show()

	#center window to screen
	screen = app.primaryScreen()
	screen_size = screen.size()
	window_size = mdi_area.size()
	mdi_area.move((screen_size.width() - window_size.width()) // 2,
				(screen_size.height() - window_size.height()) // 2)
	sys.exit(app.exec())



if __name__ == "__main__":
	formatter = logging.Formatter("[{pathname:>90s}:{lineno:<4}]  {levelname:<7s}   {message}", style='{')
	handler = logging.StreamHandler()
	handler.setFormatter(formatter)
	logging.basicConfig(
		handlers=[handler],
		level=logging.DEBUG) #Without time
	run_example_app()