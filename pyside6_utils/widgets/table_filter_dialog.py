
from pyside6_utils.ui.TableFilterDialog_ui import Ui_TableFilterDialog
from PySide6 import QtWidgets
from PySide6 import QtCore, QtGui
from numbers import Number
import sys
from pyside6_utils.utility.view_filter import RegexFilter, ExpressionFilter, SelectionFilter, Filter, CombinationFilter
import traceback
import pyside6_utils.icons.app_resources_rc #To import fonts

import logging
log = logging.getLogger(__name__)


class TableFilterDialog(QtWidgets.QDialog):
	"""
	"""
	def __init__(self,
			column_entries : set, #For showing Filtering options
			old_filter : None | Filter = None, #For showing the old filter
			use_old_filter : bool = False, #If True, use the old filter by default, else use the new filter
			parent=None
		):
		super(TableFilterDialog, self).__init__()
		self.ui = Ui_TableFilterDialog()
		self.ui.setupUi(self)
		#Set padding to 0
		self.ui.resultsScrollArea.setContentsMargins(0, 0, 0, 0)


		self._old_filter = old_filter
		self._new_filter = None
		self._pressed_clear_filter = False

		self._search_results_item_list : list[tuple[QtWidgets.QWidget, QtWidgets.QCheckBox, QtWidgets.QLabel]] = []
		self._search_index_matches : list[int] = [] #The currently matched items in the list (by index)

		self.ui.buttonBox.accepted.connect(self.accept)
		self.ui.buttonBox.rejected.connect(self.reject)

		self.column_entries = list(column_entries)
		self.str_column_entries = [str(i) for i in column_entries]

		# ============ Using old filter ===============
		self.use_old_filter = use_old_filter
		self.ui.useOldFilterCheckBox.setChecked(use_old_filter)
		self.ui.useOldFilterCheckBox.stateChanged.connect(
			lambda *_: self.use_old_filter_checkbox_changed
		)
		
		#============ Find all old-filter-matches for the current column-entries ===========
		self._old_filter_column_entry_matches = []
		if old_filter: #If an old filter is specified
			for index, val in enumerate(self.column_entries):
				if old_filter(val):
					self._old_filter_column_entry_matches.append(index) #Add all indexes that match the old filter
		else:
			self._old_filter_column_entry_matches = [i for i in range(len(self.column_entries))] #Accepts all

		supports_operators = True #If the filter supports operators (like <, >, in addition to normal regex)
		for i in self.column_entries:
			if not isinstance(i, Number):
				supports_operators = False
				break

		if supports_operators:
			self.ui.expressionComboBox.setEnabled(True)
		else:
			self.ui.expressionComboBox.setEnabled(False)

		tooltip = ("Can only be used on columns that support operators (like <, >, etc.)\n"
			"Example: '>10 and <20' will filter all values between 10 and 20\n"
			"Example: '==2021-01-01 or >2022-01-01' will filter all dates that are equal to 2021-01-01 or greater than 2022-01-01\n"
			"Automatically parses dates/datetimes and relies on eval for all other types.")
		self.ui.expressionLabel.setToolTip(tooltip)
		self.ui.expressionComboBox.setToolTip(tooltip)


		#====== Old filter ===========

		#On filter-change, show new filtered results
		self.ui.filterRegexComboBox.addItem("")
		# if old_filter:
		# 	self.ui.filterRegexComboBox.setCurrentText(old_filter.pattern())
		self.ui.filterRegexComboBox.addItems([str(i) for i in column_entries])
		self.ui.filterRegexComboBox.currentTextChanged.connect(self.regex_filter_text_changed)
		self.ui.expressionComboBox.currentTextChanged.connect(self.expression_filter_text_changed)

		self.regex_filter_text_changed("")


		self._wrong_expression_hint_popup = QtWidgets.QMessageBox()

		#============= Some styles for when the filter is invalid ============
		self._default_palette = self.ui.expressionComboBox.palette()
		self._red_palette = self.ui.expressionComboBox.palette()
		#Background color red
		self._red_palette.setColor(QtGui.QPalette.ColorRole.Base, QtGui.QColor(255, 0, 0, 180))


		#========= Error-msg tooltipwindow

		self._err_tooltip_label = QtWidgets.QLabel()
		self._err_tooltip_label.setWindowFlags(QtCore.Qt.WindowType.ToolTip)
		self._err_tooltip_label.setFrameStyle(QtWidgets.QFrame.Shape.StyledPanel | QtWidgets.QFrame.Shadow.Raised)
		self._err_tooltip_label.setLineWidth(2)
		
		


		#Set background color to yellow
		self._err_tooltip_label.setAutoFillBackground(True)
		palette = self._err_tooltip_label.palette()
		palette.setColor(QtGui.QPalette.ColorRole.Window, QtGui.QColor(240, 240, 100, 255))
		self._err_tooltip_label.setPalette(palette)

		#On window move, also move the tooltip
		# self.moveEvent = lambda event: self._err_tooltip_label.move(self.ui.expressionComboBox.mapToGlobal(QtCore.QPoint(0, 0)) + QtCore.QPoint(0, 20))
	
		font = QtGui.QFont("Monospace")
		font.setStyleHint(QtGui.QFont.StyleHint.TypeWriter)
		self._err_tooltip_label.setFont(font)

		# #Add monospace font so error lines up
		# font = QtGui.QFontDatabase.addApplicationFont(u':/icons/fonts/Inconsolata-Regular.tff')
		# #set font
		# self._err_tooltip_label.setFont(QtGui.QFont("Inconsolata", 10))

	def pressed_clear_filter(self) -> bool:
		"""
		Whether the clear-filter button was pressed - thereby rejecting the dialog.
		"""
		return self._pressed_clear_filter

	def use_old_filter_checkbox_changed(self, state):
		if state == QtCore.Qt.CheckState.Checked:
			self.use_old_filter = True
		else:
			self.use_old_filter = False

		self.search_index_matches_changed()


	def get_resulting_filter(self) -> Filter | None:
		"""
		Returns the resulting filter from the dialog.

		Also takes into account the current state of use-old-filter. If this value is True, the old and new filter
		are combined into a CombinationFilter. If not, only the new filter is returned.
		"""
		if self.use_old_filter:
			if self._new_filter is None:
				return self._old_filter
			return CombinationFilter([self._old_filter, self._new_filter])

		return self._new_filter

	def search_index_matches_changed(self):
		"""
		When the search results change, this function updates the list of items and their checkboxes

		TODO: mark the old-filtered items as greyed-out checked items if "use old filter" is checked
		"""
		cur = 0
		for index in self._search_index_matches:
			item_text = self.str_column_entries[index]
			if cur >= len(self._search_results_item_list):
				checkbox = QtWidgets.QCheckBox()
				#Add some top-padding to the checkbox without stylesheet
				checkbox.setStyleSheet("QCheckBox::indicator { padding-top: 2px; }")
				label = QtWidgets.QLabel()
				hlayout = QtWidgets.QHBoxLayout()
				hlayout.addWidget(checkbox, 0, QtCore.Qt.AlignmentFlag.AlignLeft)
				hlayout.setSpacing(2)
				hlayout.addWidget(label, 1, QtCore.Qt.AlignmentFlag.AlignLeft)
				#Set padding to 0
				hlayout.setContentsMargins(0, 0, 0, 0)
				#left-align
				container = QtWidgets.QWidget()
				container.setLayout(hlayout)
				container.setContentsMargins(0, 0, 0, 0)
				self._search_results_item_list.append((container, checkbox, label))
				self.ui.resultsLayout.addWidget(container)	
			self._search_results_item_list[cur][0].show()
			self._search_results_item_list[cur][2].setText(f"<b>{item_text}</b>")
			try:
				self._search_results_item_list[cur][1].stateChanged.disconnect()
			except RuntimeError: #If no connection,
				pass
			if self._new_filter is None:
				self._search_results_item_list[cur][1].setChecked(
					index in self._old_filter_column_entry_matches and self.use_old_filter
				)
			if self.use_old_filter and index in self._old_filter_column_entry_matches:
				self._search_results_item_list[cur][1].setDisabled(True) #Disable the checkbox if always included
			self._search_results_item_list[cur][1].stateChanged.connect(
				lambda state, item_val=self.column_entries[index]: self.item_checkbox_changed(item_val, state)
			)
			#If regex contains all possibilities, 
			# self._search_results_item_list[cur][1].setChecked(i in self._filter_result or i in self._old_filter_results)
			cur += 1

		#Remove extra labels
		for item_text in range(cur, len(self._search_results_item_list)):
			self._search_results_item_list[item_text][0].hide()

	def regex_filter_text_changed(self, regex : str):
		"""
		If regex changed - update the search results and block ExpressionFilter
		If regex is empty, enable ExpressionFilter again
		"""
		#Filter the table based on the text
		reg = QtCore.QRegularExpression(regex)
		self._search_index_matches = [] #By default, accept all

		if regex is not None and regex != "": #If a valid regex is specified - filter the search
			self.ui.expressionComboBox.blockSignals(True)
			# self.ui.expressionComboBox.setDisabled(True)
			self.ui.expressionComboBox.setEditText("")
			self.ui.expressionComboBox.setToolTip("Can't be used when regex is active")
			self.ui.expressionComboBox.blockSignals(False)
			#Get all matching entries
			self._new_filter = RegexFilter(regex)
			for index, val in enumerate(self.str_column_entries):
				# if reg.matchView(val).hasMatch():
				if self._new_filter(val):
					self._search_index_matches.append(index)

		else: #If no regex is specified, show all items
			self._new_filter = None #Remove filter
			self.ui.expressionComboBox.setDisabled(False)
			self._search_index_matches = [i for i in range(len(self.column_entries))] #Accepts all


		self.search_index_matches_changed() #TODO: maybe check if results didn't change?
	

	def expression_filter_text_changed(self, expression : str):
		self.ui.expressionComboBox.setPalette(self._default_palette)
		self._search_index_matches = []
		self._err_tooltip_label.hide()

		if expression is not None and expression != "": #If the expression is empty, show all items
			
			#========= Clear regex when filtering by expression ==========
			#TODO: maybe allow for both?
			self.ui.filterRegexComboBox.blockSignals(True)
			self.ui.filterRegexComboBox.setEditText("")
			self.ui.filterRegexComboBox.setToolTip("Can't be used when expression is active")
			self.ui.filterRegexComboBox.blockSignals(False)


			try: #Try to create expressionfilter - show error if it fails
				self._new_filter = ExpressionFilter(expression)
				self._search_index_matches = []
				for index, val in enumerate(self.column_entries):
					if self._new_filter(val):
						self._search_index_matches.append(index)
			except SyntaxError as e: #If parsing the expression fails
				self.ui.expressionComboBox.setPalette(self._red_palette)
				trace = traceback.format_exc().splitlines()
				err_line = trace[-3] #The line that contains the error
				leading_spaces = len(err_line) - len(err_line.lstrip())

				

				err = f"{trace[-1]}\n{err_line[leading_spaces:]}\n{trace[-2][leading_spaces:]}"
				log.error(f"{e}: {err}")
				#Create a small popup window with the error
				self._err_tooltip_label.setText(err)
				self._err_tooltip_label.show()
				self._err_tooltip_label.move(self.ui.expressionComboBox.mapToGlobal(QtCore.QPoint(0, 0)) + QtCore.QPoint(0, 20))
				
				self._new_filter = None
				self.search_index_matches_changed()
				return
			except Exception as e:
				self.ui.expressionComboBox.setPalette(self._red_palette)
				self._new_filter = None
				log.error(f"Error parsing expression: {expression} : {e}")
				self.ui.expressionComboBox.setStatusTip(str(e))
				self.search_index_matches_changed()
				#Create a small popup window with the error
				self._err_tooltip_label.setText(str(e))
				self._err_tooltip_label.show()
				self._err_tooltip_label.move(self.ui.expressionComboBox.mapToGlobal(QtCore.QPoint(0, 0)) + QtCore.QPoint(0, 20))
				return
		else:
			self._new_filter = None
			self._search_index_matches = [i for i in range(len(self.column_entries))] #Show all results
		self.search_index_matches_changed()


	def item_checkbox_changed(self, item, state : bool):
		print(f"Filter result changed: {item} -> {state}")
		# if state:
		# 	self._filter_result.add(item)
		# else:
		# 	self._filter_result.remove(item)