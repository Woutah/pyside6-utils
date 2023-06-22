
# from PySide6.QtWidgets import
import typing

import PySide6
from PySide6 import QtCore, QtGui, QtWidgets
import logging
log = logging.getLogger(__name__)

class IntRangeSelector(QtWidgets.QSlider):
	"""A Qt-Style slider with 2 handles that can be used to select a range of (int) values"""

	DESCRIPTION = "A Qt-Style slider with 2 handles that can be used to select a range of values."

	valuesChanged = QtCore.Signal(int, int) #Min, max

	def __init__(self, parent=None, *args):
		super().__init__(parent, *args)
		self._span_thickness_percentage = 100 #Percentage of the slider height that the span should take up (0-100)
		self._values = [20, 80] # min/max
		self._hovering_on_control = [False, False] #Control = min/max handle
		self._dragging_control = [False, False]
		self._span_on_groove = False


		self._handle_rects = [QtCore.QRect(), QtCore.QRect()] #min/max handle
		self._span_rect = QtCore.QRect() #The span between the handles (used for dragging both handles at once)
		self._groove_rect = QtCore.QRect() #The groove rectangle (used for calculating the offset factor)

		self._drag_start_mouse_pos = None
		self._drag_start_values = self._values.copy()
		self._min_handle_difference = 0 #The minimum width the span can have (in value units), by default at least 1

		self._original_cursor = self.cursor() #Save the original cursor so we can restore it when not hovering over the handles
		#Track mouse position
		self.setMouseTracking(True)


	def _get_slider_style_options(self, handle_idx : bool, draw_groove : bool):
		#type: ignore
		style_options : QtWidgets.QStyleOptionSlider = QtWidgets.QStyleOptionSlider()
		self.initStyleOption(style_options) #Init style options according to QSlider
		style_options.subControls = QtWidgets.QStyle.SubControl.SC_SliderHandle #Draw sliderhandle
		if draw_groove:
			style_options.subControls |= QtWidgets.QStyle.SubControl.SC_SliderGroove #Also draw slidergroove
			if self.tickPosition() != QtWidgets.QSlider.TickPosition.NoTicks: #If draw ticks
				style_options.subControls |= QtWidgets.QStyle.SubControl.SC_SliderTickmarks

		style_options.activeSubControls = QtWidgets.QStyle.SubControl.SC_None #No active subcontrols
		if self._dragging_control[handle_idx]: #If hovering on handle
			style_options.activeSubControls = QtWidgets.QStyle.SubControl.SC_SliderHandle
			if self._dragging_control[1-handle_idx] and draw_groove:
				style_options.activeSubControls |= QtWidgets.QStyle.SubControl.SC_SliderGroove #Also mark groove as active if dragging both handles
		elif self._hovering_on_control[handle_idx]: #If hovering on handle
			style_options.activeSubControls = QtWidgets.QStyle.SubControl.SC_SliderHandle
			if self._hovering_on_control[1- handle_idx]: #If also hovering on other handle -> so hovering over middle
				style_options.activeSubControls |= QtWidgets.QStyle.SubControl.SC_SliderGroove #Also mark groove as active if hovering both handles (middle)
		style_options.sliderPosition = self._values[handle_idx]
		return style_options


	def paintEvent(self, event : QtGui.QPaintEvent) -> None: #pylint: disable=unused-argument
		painter = QtGui.QPainter(self)
		style = QtWidgets.QApplication.style()

		#Draw groove + ticks (if any) + first handle
		draw_options = self._get_slider_style_options(False, True)
		style.drawComplexControl(QtWidgets.QStyle.ComplexControl.CC_Slider, draw_options, painter, self)
		self._groove_rect = style.subControlRect(
			QtWidgets.QStyle.ComplexControl.CC_Slider,
			draw_options, #type: ignore
			QtWidgets.QStyle.SubControl.SC_SliderGroove,
			self
		) #Save the groove rectangle for later use
		self._handle_rects[0] = style.subControlRect(QtWidgets.QStyle.ComplexControl.CC_Slider,
			draw_options, #type: ignore
			QtWidgets.QStyle.SubControl.SC_SliderHandle,
			self
		) #Save the min-handle rectangle for later use

		#Draw max handle
		draw_options = self._get_slider_style_options(True, False)
		style.drawComplexControl(QtWidgets.QStyle.ComplexControl.CC_Slider, draw_options, painter, self)
		self._handle_rects[1] = style.subControlRect(QtWidgets.QStyle.ComplexControl.CC_Slider,
			draw_options, #type: ignore
			QtWidgets.QStyle.SubControl.SC_SliderHandle,
			self
		) #Save the max-handle rectangle for later use

		#Get painter style from draw_options we just used, as if we are coloring a slider
		# painter.setPen(draw_options.palette.color(QtGui.QPalette.Text))
		darker = 0
		if (self._dragging_control[0] and self._dragging_control[1]) or (self._hovering_on_control[0] and self._hovering_on_control[1]):
			darker = 200
		painter.setPen(draw_options.palette.color(QtGui.QPalette.ColorRole.Highlight).darker(darker))
		painter.setBrush(draw_options.palette.color(QtGui.QPalette.ColorRole.Highlight).darker(darker))
		painter.drawRect(self._span_rect)

		#Make sure no border is drawn when calling drawRect

		span_rect=None

		#Also manage ticks here #TODO: is this platform specific?
		tick_offset = 0
		if self.tickPosition() == QtWidgets.QSlider.TickPosition.TicksAbove or\
				self.tickPosition() == QtWidgets.QSlider.TickPosition.TicksLeft:
			tick_offset = 4
		elif self.tickPosition() == QtWidgets.QSlider.TickPosition.TicksBelow or\
				self.tickPosition() == QtWidgets.QSlider.TickPosition.TicksRight:
			tick_offset = -4

		span_rect = QtCore.QRect()
		if self.orientation() == QtCore.Qt.Orientation.Horizontal:
			if (self._handle_rects[1].left() - self._handle_rects[0].right()) <= 0: #If span is too small to draw
				pass #Continue without setting span_rect
			elif self._span_on_groove:
				span_rect = QtCore.QRect(
					self._handle_rects[0].right(),
					self._groove_rect.center().y()-2, #Make sure the span is not drawn over handles
					self._handle_rects[1].left() - self._handle_rects[0].right(),
					4
				)
			else:
				span_rect = QtCore.QRect(
					self._handle_rects[0].right(),
					(self._handle_rects[0].top() - self._groove_rect.center().y()) * (self._span_thickness_percentage * 0.01) + self._groove_rect.center().y() + tick_offset,
					self._handle_rects[1].left() - self._handle_rects[0].right(),
					self._handle_rects[0].height() * round(self._span_thickness_percentage * 0.01) - 2 - abs(tick_offset) #TODO: not sure why the -2 is needed -> maybe the rectangle has a border?
				)
		else: #Vertical
			if (self._handle_rects[0].top() - self._handle_rects[1].bottom()) <= 0:  #If span is too small to draw
				pass
			elif self._span_on_groove:
				span_rect = QtCore.QRect(
					self._groove_rect.center().x()-2,
					self._handle_rects[1].bottom(),
					4,
					self._handle_rects[0].top() - self._handle_rects[1].bottom()
				)
			else:
				span_rect = QtCore.QRect(
					(self._handle_rects[1].left() - self._groove_rect.center().x()) * (self._span_thickness_percentage * 0.01) + self._groove_rect.center().x() + tick_offset,
					self._handle_rects[1].bottom(),
					self._handle_rects[0].width() * round(self._span_thickness_percentage * 0.01) - 2 - abs(tick_offset),
					self._handle_rects[0].top() - self._handle_rects[1].bottom()
				)


		self._span_rect = span_rect
		painter.drawRect(span_rect)


	def mousePressEvent(self, ev: QtGui.QMouseEvent) -> None:

		self._dragging_control = [False, False] #Reset dragging flags
		pos = ev.position().toPoint()
		if self._handle_rects[0].contains(pos): #If clicking on min-handle
			self._dragging_control[0] = True
		elif self._handle_rects[1].contains(pos):
			self._dragging_control[1] = True
		elif self._span_rect.contains(pos):
			self._dragging_control = (True, True)
		self._drag_start_mouse_pos = pos
		self._drag_start_values = self._values.copy()

		self._hovering_on_control = [False, False] #Reset hovering flags

	def mouseReleaseEvent(self, ev: QtGui.QMouseEvent) -> None:
		self._dragging_control = [False, False]

	def _getMouseOffsetFactor(self, pos : QtCore.QPoint):
		if self.orientation() == QtCore.Qt.Orientation.Horizontal:
			return (pos.x() - self._drag_start_mouse_pos.x()) / self._groove_rect.width()
		else:
			return (self._drag_start_mouse_pos.y() - pos.y()) / self._groove_rect.height()



	def mouseMoveEvent(self, ev: QtGui.QMouseEvent) -> None:
		"""Handle mouse move events (e.g. marking box on-hover and moving box when dragging)"""
		ev.accept()
		if not(self._dragging_control[0] or self._dragging_control[1]): #If dragging neither, check for hover
			pos = ev.position().toPoint()
			self._hovering_on_control = [self._handle_rects[0].contains(pos), self._handle_rects[1].contains(pos)] #Check
				# if hovering on either handle
			if self._hovering_on_control[0] or self._hovering_on_control[1]:
				#If horizontal
				if self.orientation() == QtCore.Qt.Orientation.Horizontal:
					self.setCursor(QtCore.Qt.CursorShape.SizeHorCursor)
				else:
					self.setCursor(QtCore.Qt.CursorShape.SizeVerCursor)
			elif self._span_rect.contains(pos):
					self.setCursor(QtCore.Qt.CursorShape.OpenHandCursor)
					self._hovering_on_control = [True, True]
			else:
				self.setCursor(QtCore.Qt.CursorShape.ArrowCursor)
				self._hovering_on_control = [False, False]
			self.update()
			return

		pos = ev.position().toPoint()
		if not self._drag_start_mouse_pos or not self._drag_start_values: #This should not be possible as old mouse pos
				# is set at click but just in case
			self._drag_start_mouse_pos = pos
			self._drag_start_values = self._values.copy()
			return


		for i in range(2):
			offset_factor = self._getMouseOffsetFactor(pos)
			new_value = self._drag_start_values[i]
			if self._dragging_control[i]:
				new_value += round(offset_factor * (self.maximum() - self.minimum()))
				new_value = min(self.maximum(), max(self.minimum(), new_value))
			self._values[i] = new_value


		self._values = self._clamp(self._values, respect_min_handle_difference=True, prefer_change_idx=self._dragging_control[1])

		if self._values[0] > self._values[1]: #If the handles have overtaken each other during dragging, swap them
			self._values = [self._values[1], self._values[0]]
			self._dragging_control = [self._dragging_control[1], self._dragging_control[0]] #Swap the dragging flags
			self._drag_start_values = [self._drag_start_values[1], self._drag_start_values[0]] #Swap the start values
				#(otherwise calculations will fail)

		self.valuesChanged.emit(self._values[0], self._values[1])
		self.update() #Update the slider to show the new position of the handles

	def _clamp(self, values : list[int], respect_min_handle_difference : bool = True, prefer_change_idx : typing.Literal[0, 1] = 0):
		"""Clamp the values to the allowed range and make sure span width is respected if so desired
		NOTE: The values are not sorted

		Args:
			values (list[int]): The values to clamp - does not need to be sorted
			respect_min_handle_difference (bool, optional): If the values are too close together, should the values be
				changed to respect the min span width. Defaults to True.
			prefer_change_idx (typing.Union[0, 1], optional): Which value (min or max) should be changed if the values
				are too close together. Defaults to 0.

		Returns:
			list[int]: The clamped and min-distance-respected values NOTE: The values are not sorted
		"""
		slider_min, slider_max = self.minimum(), self.maximum()
		values = [min(slider_max, max(slider_min, value)) for value in values]


		span_diff = self._min_handle_difference - abs(values[0] - values[1])
		if respect_min_handle_difference and (span_diff > 0): #If values too close together
			if values[prefer_change_idx] >= values[1-prefer_change_idx]:
				if (values[prefer_change_idx] + span_diff) < slider_max: #Check that we don't go over the max value
						# when moving the value that should be changed
					values[prefer_change_idx] += span_diff
				else:
					values[1-prefer_change_idx] = slider_max
					values[prefer_change_idx] = slider_max - self._min_handle_difference
			elif values[prefer_change_idx] < values[1-prefer_change_idx]:
				if (values[prefer_change_idx] - span_diff) > slider_min:
					values[prefer_change_idx] -= span_diff
				else:
					values[1-prefer_change_idx] = slider_min
					values[prefer_change_idx] = slider_min + self._min_handle_difference


		return values

	def setSliderPositions(self, values : typing.List[int], respect_min_handle_difference : bool = True, change_max_when_too_close : bool = True):
		"""Set the position of the handles

		Args:
			values (typing.List[int]): The new desired positions of the handles
			respect_min_handle_difference(bool, optional): If the handles are too close together
				(if min_handle_difference has been set), decides which handle should be moved. Defaults to True.
				NOTE: if this is set to True, the set values might be altered to respect the min span width.
			change_max_when_too_close (bool, optional): If the handles are too close together (if min_handle_difference
				has been set and respect flag has been set to true), decides which handle should be moved.
				Defaults to True.
		"""
		new_vals = self._clamp(values, respect_min_handle_difference, int(change_max_when_too_close))
		new_vals = sorted(new_vals) #Make sure the values are sorted
		if new_vals == self._values:
			return
		self._values = new_vals
		self.valuesChanged.emit(self._values[0], self._values[1])
		self.update()

	def setSliderPositionMin(self, value): #TODO: make it so there is always 1 step space between handles (or not?)
		if value == self._values[0]:
			return
		new_vals = self._clamp([value, self._values[1]], prefer_change_idx = 1)
		self._values = sorted(new_vals)
		self.valuesChanged.emit(self._values[0], self._values[1])
		self.update()


	def setSliderPositionMax(self, value):
		if value == self._values[1]:
			return
		new_vals = self._clamp([self._values[0], value], prefer_change_idx = 0)
		self._values = sorted(new_vals)
		self.valuesChanged.emit(self._values[0], self._values[1])
		self.update()

	def setSpanHeightPercentage(self, value):
		self._span_thickness_percentage = min(100, max(0, value))
		self.update()

	def getSpanHeightPercentage(self):
		return self._span_thickness_percentage

	def setSpanOnGroove(self, value):
		self._span_on_groove = value
		self.update()

	def setminSpanWidth(self, value):
		self._min_handle_difference = value
		self.setSliderPositions(self._values)

	#Properties
	# value = None #Disabled these
	# sliderPosition = None #Disabled these

	spanOnGroove = QtCore.Property(bool, lambda self: self._span_on_groove, setSpanOnGroove)
	spanThicknessPercentage = QtCore.Property(int, getSpanHeightPercentage, setSpanHeightPercentage)
	sliderPositionMin = QtCore.Property(int, lambda self: self._values[0], setSliderPositionMin)
	sliderPositionMax = QtCore.Property(int, lambda self: self._values[1], setSliderPositionMax)
	minHandleDifference = QtCore.Property(int, lambda self: self._min_handle_difference, setminSpanWidth)


class RangeSelector(IntRangeSelector):
	"""Implements a range selector based on IntRangeSelector that can be used to select a range of values of any
	compatible type"""

	rangeChanged = QtCore.Signal(object) #Min/max of slider range changed (Of any type)
	valuesChanged = QtCore.Signal(object, object) #Min/max of selected range changed (Of any type)
	SUPPORTED_TYPES = typing.Union[int, float, QtCore.QDate, QtCore.QTime, QtCore.QDateTime, type(None)]

	def __init__(self, parent: typing.Optional[QtWidgets.QWidget] = None) -> None:
		super().__init__(parent)
		self._layout = QtWidgets.QHBoxLayout()
		self._layout.setContentsMargins(0, 0, 0, 0)
		# self._layout.setSpacing(0)
		self._has_value_boxes = True
		self._value_boxes = [QtWidgets.QSpinBox(), QtWidgets.QSpinBox()]

		# self._value_boxes[0].setParent(self)
		# self._value_boxes[1].setParent(self)
		# self._range_selector = IntRangeSelector()
		self._minimum = None
		self._maximum = None
		self._min_value = None
		self._max_value = None

		self._enforce_minimum = False
		self._enforce_maximum = False


	def minimum(self) -> any:
		return self._minimum

	def maximum(self) -> any:
		return self._maximum

	def setMinimum(self, value : SUPPORTED_TYPES):
		self._minimum = value
		# self._value_boxes[0].setMinimum(value)
		# self._value_boxes[1].setMinimum(value)
		self.update()

	def setMaximum(self, value : SUPPORTED_TYPES):
		self._maximum = value
		# self._value_boxes[0].setMaximum(value)
		# self._value_boxes[1].setMaximum(value)
		self.update()

	def setAll(self,
				minimum : SUPPORTED_TYPES,
				maximum : SUPPORTED_TYPES,
				min_value : SUPPORTED_TYPES,
				max_value : SUPPORTED_TYPES
			):
		self._minimum = minimum
		self._maximum = maximum
		self._min_value = min_value
		self._max_value = max_value
		# self._value_boxes[0].setMinimum(minimum)
		# self._value_boxes[0].setMaximum(maximum)
		# self._value_boxes[1].setMinimum(minimum)
		# self._value_boxes[1].setMaximum(maximum)
		self.update()

	def update(self):
		#Check if type of min/max is in SUPPORTED_TYPES
		supported_types = typing.get_args(self.SUPPORTED_TYPES)

		if self._minimum is None or self._maximum is None or self._min_value is None or self._max_value is None:
			self.setEnabled(False)
			super().update()
			return

		if type(self._minimum) not in supported_types\
				or type(self._maximum) not in supported_types\
				or type(self._min_value) not in supported_types\
				or type(self._max_value) not in supported_types:
			self.setEnabled(False)
			msg = (f"One of the values (min/max minval/maxval) of type {type(self._minimum)} is not a supported type for"
				f"RangeSelector. Supported types are: {self.SUPPORTED_TYPES}")
			log.warning(msg)
			raise TypeError(msg)

		#Check if all types are the same
		if type(self._minimum) != type(self._maximum) or\
				type(self._minimum) != type(self._min_value) or\
				type(self._minimum) != type(self._max_value):
			self.setEnabled(False)
			raise TypeError(f"Types of min/max minval/maxval are not the same. Types are: {type(self._minimum)}, {type(self._maximum)}, {type(self._min_value)}, {type(self._max_value)}")

		super().update()

	def setHasValueBoxes(self, value):
		self._has_value_boxes = value
		self._value_boxes[0].setVisible(value)
		self._value_boxes[1].setVisible(value)
		self.update()

	def enforceLimits(self):
		if self._enforce_minimum:
			self._min_value = min(self._minimum, self._min_value)
		if self._enforce_maximum:
			self._max_value = max(self._maximum, self._max_value)

	def setEnforceMinimum(self, value):
		self._enforce_minimum = value
		self.update()

	def setEnforceMaximum(self, value):
		self._enforce_maximum = value
		self.update()




	#QAbstractSlider properties
	value = None
	# sliderPosition = QtCore.Property(object, lambda self: (self._value_boxes[0].value(), self._value_boxes[1].value()), lambda self, value: self.setSliderPositions(value))
	# minimum = QtCore.Property(int, lambda self: self.minimum(), setMinimum)
	enforceMinimum = QtCore.Property(bool, lambda self: self._enforce_minimum, setEnforceMinimum) #Whether to enforce the minimum value when using setSliderPositions-methods
	enforceMaximum = QtCore.Property(bool, lambda self: self._enforce_maximum, setEnforceMaximum) #Whether to enforce the maximum value when using setSliderPositions-methods

	hasValueBoxes = QtCore.Property(bool, lambda self: self._has_value_boxes, setHasValueBoxes)


def run_example_app():
	"""Run the example app with this widget"""
	import sys
	app = QtWidgets.QApplication(sys.argv)
	window = QtWidgets.QMainWindow()

	range_selector1 = RangeSelector()
	range_selector1.setOrientation(QtCore.Qt.Orientation.Horizontal)
	range_selector1.setAll(0.0, 100.0, 20.0, 80.0)
	range_selector1.setTickInterval(5)
	range_selector1.setTickPosition(QtWidgets.QSlider.TickPosition.TicksAbove)

	range_selector2 = RangeSelector()
	range_selector2.setOrientation(QtCore.Qt.Orientation.Horizontal)
	range_selector2.setAll(0.0, 100.0, 20.0, 80.0)

	layout = QtWidgets.QVBoxLayout()
	layout.addWidget(range_selector1)
	layout.addWidget(range_selector2)
	widget = QtWidgets.QWidget()
	widget.setLayout(layout)
	window.setCentralWidget(widget)
	window.show()
	sys.exit(app.exec())



if __name__ == "__main__":
	formatter = logging.Formatter("[{pathname:>90s}:{lineno:<4}]  {levelname:<7s}   {message}", style='{')
	handler = logging.StreamHandler()
	handler.setFormatter(formatter)
	logging.basicConfig(
		handlers=[handler],
		level=logging.DEBUG) #Without time
	run_example_app()
