"""Run a window with examples for the widgets in this package."""

import sys

import pandas as pd
from PySide6.QtWidgets import QApplication, QMainWindow

from pyside6_utils.models.pandas_table_model import PandasTableModel
from pyside6_utils.ui.allWidgets_ui import Ui_MainWindow


def run_widgets_example_app():
	"""Creates a qt app and shows a window with all a couple of small widgets in this package.
	TODO: create buttons for the large widgets? 
	"""
	app = QApplication(sys.argv)
	example_window = QMainWindow()
	example_ui = Ui_MainWindow()
	example_ui.setupUi(example_window)

	#====== Example df for PandasTableView ======
	example_df = pd.DataFrame({
		"Column 1": [1, 2, 3, 4, 5],
		"Column 2": [10, 20, 30, 40, 50],
		"Column 3": [100, 200, 300, 400, 500],
		"Column 4": [1000, 2000, 3000, 4000, 5000],
		"Column 5": [10000, 20000, 30000, 40000, 50000],
	})
	example_df_model = PandasTableModel(example_df)
	example_ui.pandasTableView.setModel(example_df_model)
	example_ui.pandasTableView.set_status_bar(example_window.statusBar())

	example_window.show()
	sys.exit(app.exec())


if __name__ == "__main__":
	run_widgets_example_app()
