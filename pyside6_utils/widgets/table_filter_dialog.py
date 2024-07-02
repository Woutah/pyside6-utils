
from pyside6_utils.ui.TableFilterDialog_ui import Ui_TableFilterDialog
from PySide6 import QtWidgets
from PySide6 import QtCore
from numbers import Number





class TableFilterDialog(QtWidgets.QDialog):
	"""
	"""
	def __init__(self,
			column_entries : set, #For showing Filtering options
			# old_filter : QtCore.QRegularExpression | None = None, #For showing the old filter
			old_filter_results : set | None = set(), #For showing the old filter
			use_old_filter : bool = False, #If True, use the old filter, else use the new filter
			parent=None
		):
		super(TableFilterDialog, self).__init__()
		self.ui = Ui_TableFilterDialog()
		self.ui.setupUi(self)
		#Set padding to 0
		self.ui.resultsScrollArea.setContentsMargins(0, 0, 0, 0)

		if old_filter_results:
			self._old_filter_results : set = old_filter_results
		else:
			self._old_filter_results : set = set() #All the previously selected items

		self._filter_result : set = set() #All the actually selected items

		self.ui.resultsLayout = QtWidgets.QVBoxLayout()
		self._search_results_item_list : list[tuple[QtWidgets.QWidget, QtWidgets.QCheckBox, QtWidgets.QLabel]] = []
		self.ui.resultsScrollArea.setLayout(self.ui.resultsLayout)

		self.ui.buttonBox.accepted.connect(self.accept)
		self.ui.buttonBox.rejected.connect(self.reject)

		self.column_entries = list(column_entries)

		#====== Old filter ===========
		# if not old_filter: #If no old filter, hide option to use old filter
		# 	self.ui.useOldFilterCheckBox.hide()
		self.ui.useOldFilterCheckBox.setChecked(use_old_filter)

		#On filter-change, show new filtered results
		self.ui.filterRegexComboBox.addItem("")
		# if old_filter:
		# 	self.ui.filterRegexComboBox.setCurrentText(old_filter.pattern())
		self.ui.filterRegexComboBox.addItems([str(i) for i in column_entries])
		self.ui.filterRegexComboBox.currentTextChanged.connect(self.filter_text_changed)

		self.filter_text_changed("")


	def filter_text_changed(self, regex : str):
		#Filter the table based on the text
		reg = QtCore.QRegularExpression(regex)
		cur = 0

		#Get all matching entries
		for i in self.column_entries:
			if reg.matchView(i).hasMatch():
				if cur >= len(self._search_results_item_list):
					checkbox = QtWidgets.QCheckBox()
					label = QtWidgets.QLabel()
					hlayout = QtWidgets.QHBoxLayout()
					hlayout.addWidget(checkbox)
					hlayout.addWidget(label) 
					#left-align
					container = QtWidgets.QWidget()
					container.setLayout(hlayout)
					hlayout.setStretch(1, 0)
					self._search_results_item_list.append((container, checkbox, label))
					self.ui.resultsLayout.addWidget(container)	
				self._search_results_item_list[cur][0].show()
				self._search_results_item_list[cur][2].setText(f"<b>{i}</b>")
				try:
					self._search_results_item_list[cur][1].stateChanged.disconnect()
				except RuntimeError: #If no connection,
					pass
				self._search_results_item_list[cur][1].stateChanged.connect(
					lambda state, i=i: self.filter_result_changed(i, state)
				)
				#If regex contains all possibilities, 
				self._search_results_item_list[cur][1].setChecked(i in self._filter_result or i in self._old_filter_results)
				cur += 1

		#Remove extra labels
		for i in range(cur, len(self._search_results_item_list)):
			self._search_results_item_list[i][0].hide()

		# while len(self._results_item_list) > cur:
			# self.ui.resultsLayout.removeItem(self._results_item_list[-1][0])
			# self._results_item_list[-1][1].stateChanged.disconnect()
			# self._results_item_list[-1][0].deleteLater()
			# self._results_item_list.pop()

		# #Update vertical spacer
		self.ui.verticalSpacer.changeSize(0, 1000, QtWidgets.QSizePolicy.Policy.Minimum, QtWidgets.QSizePolicy.Policy.Expanding)

	
	def filter_result_changed(self, item, state : bool):
		print(f"Filter result changed: {item} -> {state}")
		if state:
			self._filter_result.add(item)
		else:
			self._filter_result.remove(item)