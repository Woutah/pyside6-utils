"""Implements a collapsible QGroupBox (using checkmark to toggle)"""
import copy

from PySide6 import QtWidgets
from PySide6.QtCore import Property


class CollapsibleGroupBox(QtWidgets.QGroupBox):
	"""A collapsible QGroupBox (using checkmark to toggle)"""

	DESCRIPTION = "A collapsible QGroupBox (using checkmark to toggle)"

	#Use C++ style method names for functions to match Qt's naming convention
	def __init__(self, *args, title : str | None = None, **kwargs):
		super().__init__(title, *args, **kwargs)
		self.setCheckable(True)
		self._original_size_policy = self.sizePolicy()
		self._original_min_size = self.minimumSize()
		self._original_contents_margins = self.contentsMargins()
		self._original_flat_state = self.isFlat()
		self._original_size = self.size()
		self._collapses_horizontally = False
		self._collapses_vertically = True
		self._make_flat_when_collapsed = True
		self._collapsed = None

		if title is not None:
			self.setTitle(title)
		self.toggled.connect(self.toggle_active_collapse)

	def set_collapses_horizontally(self, collapse : bool):
		"""Set whether the widget collapses horizontally when collapsed"""
		self._collapses_horizontally = collapse
		self.toggle_active_collapse(self.isChecked())

	def get_collapses_horizontally(self):
		"""Returns whether the widget collapses horizontally when collapsed"""
		return self._collapses_horizontally

	def set_collapses_vertically(self, collapse : bool):
		"""Set whether the widget collapses vertically when collapsed"""
		self._collapses_vertically = collapse
		self.toggle_active_collapse(self.isChecked())

	def get_collapses_vertically(self):
		"""Returns whether the widget collapses vertically when collapsed"""
		return self._collapses_vertically

	def set_make_flat_when_collapsed(self, collapse : bool):
		"""Set whether the widget should be flat when collapsed"""
		self._make_flat_when_collapsed = collapse
		self.toggle_active_collapse(self.isChecked())

	def get_make_flat_when_collapsed(self):
		"""Returns whether the widget is flat when collapsed"""
		return self._make_flat_when_collapsed

	def toggle_active_collapse(self, checked : bool):
		"""Toggle the collapse-mode of the widget, based on the passed checked state"""
		if self._collapsed and checked != self._collapsed:
			return
		if self._collapsed is None or (self._collapsed != checked and not self._collapsed): #If initializing or
				# toggling to collapsed state, save the original values
			self._original_min_size = self.minimumSize()
			self._original_size_policy = self.sizePolicy()
			self._original_contents_margins = self.contentsMargins()
			self._original_flat_state = self.isFlat()
			self._original_size = self.size()

		new_size_policy = copy.copy(self._original_size_policy) #Make copies as not to modify originals
			# NOTE: we revert to original size, min_size and size_policy when toggling, even when these properties
			# are edited during runtime
		new_min_size = copy.copy(self._original_min_size)
		new_size = copy.copy(self._original_size)

		if self.makeFlatWhenCollapsed:
			if not checked:
				self.setFlat(True)
			else:
				self.setFlat(self._original_flat_state)

		for child in self.children(): #Hide/unhide all children
			if isinstance(child, QtWidgets.QWidget):
				child.setVisible(checked)

		if not checked: #No margins when collapsed
			self.setContentsMargins(0,0,0,0)
		else:
			self.setContentsMargins(self._original_contents_margins)

		if self.collapsesHorizontal:
			if not checked:
				new_size_policy.setHorizontalPolicy(QtWidgets.QSizePolicy.Policy.Fixed)
				new_min_size.setWidth(0)
				new_size.setWidth(30)

		if self.collapsesVertical:
			if not checked:
				new_size_policy.setVerticalPolicy(QtWidgets.QSizePolicy.Policy.Fixed)
				new_min_size.setHeight(20)
				new_size.setHeight(0)

		self.setMinimumSize(new_min_size)
		self.resize(new_size)
		self.setSizePolicy(new_size_policy)
		self.updateGeometry()

		self._collapsed = not checked #Update the collapsed state

	#Use C++ style properties for matching Qt-Designer style
	collapsesHorizontal = Property(bool, get_collapses_horizontally, set_collapses_horizontally)
	collapsesVertical = Property(bool, get_collapses_vertically, set_collapses_vertically)
	makeFlatWhenCollapsed = Property(bool, get_make_flat_when_collapsed, set_make_flat_when_collapsed)



if __name__ == "__main__":
	import logging
	log = logging.getLogger(__name__)

	formatter = logging.Formatter("[{pathname:>90s}:{lineno:<4}]  {levelname:<7s}   {message}", style='{')
	handler = logging.StreamHandler()
	handler.setFormatter(formatter)
	logging.basicConfig(
		handlers=[handler],
		level=logging.DEBUG) #Without time
	log.debug("Now running collapsible groupbox example...")

	app = QtWidgets.QApplication([])
	window = QtWidgets.QWidget()
	widget = CollapsibleGroupBox("Test")
	widget.setLayout(QtWidgets.QVBoxLayout())
	widget.layout().addWidget(QtWidgets.QLabel("Test label1"))
	widget.layout().addWidget(QtWidgets.QLabel("Test label2"))
	window.setLayout(QtWidgets.QVBoxLayout())
	window.layout().addWidget(widget)
	widget.show()
	window.show()
	app.exec()
	log.debug("Done!")
