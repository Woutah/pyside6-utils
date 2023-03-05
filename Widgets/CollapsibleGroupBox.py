from PySide6 import QtWidgets, QtCore
import copy
from PySide6.QtCore import Property

class CollapsibleGroupBox(QtWidgets.QGroupBox):
	DESCRIPTION = "A collapsible QGroupBox (using checkmark to toggle)"

	#Use C++ style method names for functions to match Qt's naming convention
	def __init__(self, title = None, *args, **kwargs):
		super().__init__(title, *args, **kwargs)
		self.setCheckable(True)
		self._original_size_policy = self.sizePolicy()
		self._original_min_size = self.minimumSize()
		self._original_contents_margins = self.contentsMargins()
		self._original_flat_state = self.isFlat()
		self._original_size = self.size()
		self._collapsesHorizontally = False
		self._collapsesVertically = True
		self._make_flat_when_collapsed = True
		self._collapsed = None

		self.title = self.__class__.__name__
		self.toggled.connect(self.toggleActiveCollapses)

	def setCollapsesHorizontally(self, collapse : bool):
		self._collapsesHorizontally = collapse
		self.toggleActiveCollapses(self.isChecked())
	
	def getCollapsesHorizontally(self):
		return self._collapsesHorizontally

	def setCollapsesVertically(self, collapse : bool):
		self._collapsesVertically = collapse
		self.toggleActiveCollapses(self.isChecked())
	
	def getCollapsesVertically(self):
		return self._collapsesVertically
	
	def setMakeFlatWhenCollapsed(self, collapse : bool):
		self._make_flat_when_collapsed = collapse
		self.toggleActiveCollapses(self.isChecked())
	
	def getMakeFlatWhenCollapsed(self):
		return self._make_flat_when_collapsed

	def toggleActiveCollapses(self, checked : bool):
		if self._collapsed and checked != self._collapsed:
			return
		if self._collapsed is None or (self._collapsed != checked and self._collapsed == False): #If initializing or toggling to collapsed state, save the original values
			self._original_min_size = self.minimumSize()
			self._original_size_policy = self.sizePolicy()
			self._original_contents_margins = self.contentsMargins()
			self._original_flat_state = self.isFlat()
			self._original_size = self.size()

		new_size_policy = copy.copy(self._original_size_policy) #Make copies as not to modify originals NOTE: we revert to original size, min_size and size_policy when toggling, even when these properties are edited during runtime
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
				new_size_policy.setHorizontalPolicy(QtWidgets.QSizePolicy.Fixed)
				new_min_size.setWidth(0)
				new_size.setWidth(30)

		if self.collapsesVertical:
			if not checked:
				new_size_policy.setVerticalPolicy(QtWidgets.QSizePolicy.Fixed)
				new_min_size.setHeight(20)
				new_size.setHeight(0)
				
		self.setMinimumSize(new_min_size)
		self.resize(new_size)
		self.setSizePolicy(new_size_policy)
		self.updateGeometry()
		
		self._collapsed = not checked #Update the collapsed state

	#Use C++ style properties for matching Qt-Designer style
	collapsesHorizontal = Property(bool, getCollapsesHorizontally, setCollapsesHorizontally)
	collapsesVertical = Property(bool, getCollapsesVertically, setCollapsesVertically)
	makeFlatWhenCollapsed = Property(bool, getMakeFlatWhenCollapsed, setMakeFlatWhenCollapsed)