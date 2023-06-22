# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'allWidgets.ui'
##
## Created by: Qt User Interface Compiler version 6.5.0
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QApplication, QHeaderView, QLabel, QMainWindow,
    QMenuBar, QSizePolicy, QSlider, QSpacerItem,
    QStatusBar, QVBoxLayout, QWidget)

from pyside6_utils.widgets.collapsible_group_box import CollapsibleGroupBox
from pyside6_utils.widgets.pandas_table_view import PandasTableView
from pyside6_utils.widgets.range_selector import RangeSelector
import pyside6_utils.icons.app_resources_rc

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(1289, 960)
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.verticalLayout = QVBoxLayout(self.centralwidget)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.collapsibleGroupBox = CollapsibleGroupBox(self.centralwidget)
        self.collapsibleGroupBox.setObjectName(u"collapsibleGroupBox")
        self.collapsibleGroupBox.setProperty("collapsesHorizontal", False)
        self.collapsibleGroupBox.setProperty("makeFlatWhenCollapsed", True)
        self.verticalLayout_2 = QVBoxLayout(self.collapsibleGroupBox)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.label = QLabel(self.collapsibleGroupBox)
        self.label.setObjectName(u"label")

        self.verticalLayout_2.addWidget(self.label)

        self.label_2 = QLabel(self.collapsibleGroupBox)
        self.label_2.setObjectName(u"label_2")

        self.verticalLayout_2.addWidget(self.label_2)


        self.verticalLayout.addWidget(self.collapsibleGroupBox)

        self.label_3 = QLabel(self.centralwidget)
        self.label_3.setObjectName(u"label_3")
        font = QFont()
        font.setBold(True)
        self.label_3.setFont(font)

        self.verticalLayout.addWidget(self.label_3)

        self.pandasTableView = PandasTableView(self.centralwidget)
        self.pandasTableView.setObjectName(u"pandasTableView")

        self.verticalLayout.addWidget(self.pandasTableView)

        self.rangeSelector = RangeSelector(self.centralwidget)
        self.rangeSelector.setObjectName(u"rangeSelector")
        self.rangeSelector.setOrientation(Qt.Horizontal)
        self.rangeSelector.setInvertedAppearance(False)
        self.rangeSelector.setInvertedControls(False)
        self.rangeSelector.setTickPosition(QSlider.TicksAbove)
        self.rangeSelector.setProperty("spanOnGroove", False)
        self.rangeSelector.setProperty("hasValueBoxes", True)

        self.verticalLayout.addWidget(self.rangeSelector)

        self.verticalSpacer = QSpacerItem(20, 456, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.verticalLayout.addItem(self.verticalSpacer)

        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QMenuBar(MainWindow)
        self.menubar.setObjectName(u"menubar")
        self.menubar.setGeometry(QRect(0, 0, 1289, 22))
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QStatusBar(MainWindow)
        self.statusbar.setObjectName(u"statusbar")
        MainWindow.setStatusBar(self.statusbar)

        self.retranslateUi(MainWindow)

        QMetaObject.connectSlotsByName(MainWindow)
    # setupUi

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"MainWindow", None))
        self.collapsibleGroupBox.setTitle(QCoreApplication.translate("MainWindow", u"CollapsibleGroupBox", None))
        self.label.setText(QCoreApplication.translate("MainWindow", u"Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore", None))
        self.label_2.setText(QCoreApplication.translate("MainWindow", u"Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat.", None))
        self.label_3.setText(QCoreApplication.translate("MainWindow", u"Pandas Model/TableView:", None))
    # retranslateUi

