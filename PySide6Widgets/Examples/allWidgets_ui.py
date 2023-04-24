# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'allWidgets.ui'
##
## Created by: Qt User Interface Compiler version 6.4.2
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

from PySide6Widgets.Widgets.CollapsibleGroupBox import CollapsibleGroupBox
from PySide6Widgets.Widgets.PandasTableView import PandasTableView
from PySide6Widgets.Widgets.RangeSelector import RangeSelector

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(997, 869)
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

        self.verticalLayout.addWidget(self.rangeSelector)

        self.verticalSpacer = QSpacerItem(20, 456, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.verticalLayout.addItem(self.verticalSpacer)

        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QMenuBar(MainWindow)
        self.menubar.setObjectName(u"menubar")
        self.menubar.setGeometry(QRect(0, 0, 997, 22))
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
        self.label.setText(QCoreApplication.translate("MainWindow", u"Testlabel1", None))
        self.label_2.setText(QCoreApplication.translate("MainWindow", u"Testlabel2", None))
    # retranslateUi

