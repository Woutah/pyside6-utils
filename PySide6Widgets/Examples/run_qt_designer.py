"""
2023
This example will run QT Designer, also setting the PYSIDE_DESIGNER_PLUGINS path to the appropriate location, which should make all widgets in the PySide6 package available in QT Designer.
"""
import sys
import os
from PySide6.QtCore import QLibraryInfo, QProcess, QProcessEnvironment
from PySide6.QtWidgets import QApplication, QMessageBox
import pathlib

from ..Registrars.RegisterCollapsibleGroupbox import CollapsibleGroupBox


#Get path 1 folder up from this file
main_path = pathlib.Path(__file__).parent.parent.absolute()
env = QProcessEnvironment.systemEnvironment()
env.insert('PYSIDE_DESIGNER_PLUGINS', os.path.join(main_path, "Registrars"))


app = QApplication(sys.argv)
# QMessageBox.information(None, "PySide6 Designer", f"""<p> This example will attempt to run Qt Designer, including the PySide6 widgets. </p> 
#                         <p>After clicking <b>OK</b>, Qt Designer should be started.</p>
#                         <p>This example assumes that you are using the right python environment in which PySide6 is installed.
#                         This means that Qt Designer can be launched by running: <tt>pyside6-designer</tt> - if not, this example will not work.</p>
#                         <p>This script automatically sets the <tt>PYSIDE_DESIGNER_PLUGINS</tt> environment variable to <tt>./Registrars</tt> so that all of the widgets in this repository should appear in the widget box in the <b>PySide2 Widgets</b> group-box.</p>
                        
# 						<p>Currently looking for Widgets/Registrars using path: <tt>{main_path}</tt></p>
# 						""")

designer_process = QProcess()
designer_process.setProcessEnvironment(env)
designer_process.setProcessChannelMode(QProcess.ForwardedChannels) #Show output in console
#Start designer, opening allWidgets.ui from the current directory
designer_process.start("pyside6-designer", [os.path.join(main_path, "Examples", "allWidgets.ui")]) #Start Qt Designer, opening the example UI file

#Check if designer is running
if not designer_process.waitForStarted():
	print("Designer process failed to start")
	#Create message box with reason why designer is not running
	QMessageBox.critical(None, "PyQt Designer Plugins",
			"<p>Qt Designer could not be started.  Please check that it is "
			"installed and that the <tt>designer</tt> executable is in your "
			"path.</p>"
			"<p>The error message returned was:</p>"
			"<p><tt>{0}</tt></p>".format(designer_process.errorString()))
	sys.exit(1)

designer_process.waitForFinished(-1) #-1 otherwise we will quit after 30 seconds
sys.exit(designer_process.exitCode())