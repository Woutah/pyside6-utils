"""Run a window with examples for the widgets in this package."""

import pandas as pd
from PySide6.QtWidgets import QApplication, QMainWindow

from PySide6Widgets.Models.PandasTableModel import PandasTableModel
from PySide6Widgets.UI.allWidgets_ui import Ui_MainWindow

if __name__ == "__main__":
	import sys
	app = QApplication(sys.argv)
	MainWindow = QMainWindow()
	ui = Ui_MainWindow()
	ui.setupUi(MainWindow)

	#====== Example df for PandasTableView ======
	example_df = pd.DataFrame({
		"Column 1": [1, 2, 3, 4, 5],
		"Column 2": [10, 20, 30, 40, 50],
		"Column 3": [100, 200, 300, 400, 500],
		"Column 4": [1000, 2000, 3000, 4000, 5000],
		"Column 5": [10000, 20000, 30000, 40000, 50000],
	})
	example_df_model = PandasTableModel(example_df)
	ui.pandasTableView.setModel(example_df_model)
	ui.pandasTableView.setStatusBar(MainWindow.statusBar())

	MainWindow.show()
	sys.exit(app.exec())
