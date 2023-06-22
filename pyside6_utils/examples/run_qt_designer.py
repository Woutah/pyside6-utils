"""
2023
This example will run QT Designer, also setting the PYSIDE_DESIGNER_PLUGINS path to the appropriate location,
which should make all widgets in this package available in QT Designer.
"""
import os
import pathlib
import sys

from PySide6.QtCore import QProcess, QProcessEnvironment
from PySide6.QtWidgets import QApplication, QMessageBox


def run_qt_designer():
	"""Runs qt designer, first setting the path to all registrars such that all custom widgets are loaded"""
	#Get path 1 folder up from this file
	main_path = pathlib.Path(__file__).parent.parent.absolute()
	env = QProcessEnvironment.systemEnvironment()
	env.insert('PYSIDE_DESIGNER_PLUGINS', os.path.join(main_path, "registrars"))


	app = QApplication(sys.argv) #pylint: disable=unused-variable
	QMessageBox.information(
		None, #type: ignore
		"PySide6 Designer",
		f"""<p> This example will attempt to run Qt Designer, including the PySide6 widgets. </p>
		<p>After clicking <b>OK</b>, Qt Designer should be started.</p>
		<p>This example assumes that you are using the right python environment in which PySide6 is installed.
		This means that Qt Designer can be launched by running: <tt>pyside6-designer</tt> -
		if not, this example will not work.</p>
		<p>This script automatically sets the <tt>PYSIDE_DESIGNER_PLUGINS</tt> environment variable to <tt>./Registrars</tt>
		so that all of the widgets in this repository should appear in the widget box in the <b>PySide2 Widgets
		</b>group-box.</p>

		<p>Currently looking for Widgets/Registrars using path: <tt>{main_path}</tt></p>
		"""
	)

	designer_process = QProcess()
	designer_process.setProcessEnvironment(env)
	designer_process.setProcessChannelMode(QProcess.ProcessChannelMode.ForwardedChannels) #Show output in console
	designer_process.start("pyside6-designer", [os.path.join(main_path, "ui", "AllWidgets.ui")]) #Start Qt Designer,
		#opening the example UI file

	#Check if designer is running
	if not designer_process.waitForStarted():
		print("Designer process failed to start")
		#Create message box with reason why designer is not running
		QMessageBox.critical(
				None, #type: ignore
				"PySide6 Designer",
				f"<p>Qt Designer (pyside6-designer) could not be started.  Please check that it is "
				f"installed and that the <tt>designer</tt> executable is in your "
				f"path.</p>"
				f"<p>The error message returned was:</p>"
				f"<p><tt>{designer_process.errorString()}</tt></p>"
			)
		sys.exit(1)

	designer_process.waitForFinished(-1) #-1 otherwise we will quit after 30 seconds
	sys.exit(designer_process.exitCode())



if __name__ == "__main__":
	run_qt_designer()
	