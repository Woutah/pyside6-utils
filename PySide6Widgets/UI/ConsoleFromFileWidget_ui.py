# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'ConsoleFromFileWidget.ui'
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
from PySide6.QtWidgets import (QApplication, QHeaderView, QPlainTextEdit, QSizePolicy,
    QSplitter, QTableView, QVBoxLayout, QWidget)
import app_resources_rc

class Ui_ConsoleFromFileWidget(object):
    def setupUi(self, ConsoleFromFileWidget):
        if not ConsoleFromFileWidget.objectName():
            ConsoleFromFileWidget.setObjectName(u"ConsoleFromFileWidget")
        ConsoleFromFileWidget.resize(1466, 346)
        self.verticalLayout = QVBoxLayout(ConsoleFromFileWidget)
        self.verticalLayout.setSpacing(0)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.splitter = QSplitter(ConsoleFromFileWidget)
        self.splitter.setObjectName(u"splitter")
        self.splitter.setOrientation(Qt.Orientation.Horizontal)
        self.splitter.setHandleWidth(5)
        self.consoleTextEdit = QPlainTextEdit(self.splitter)
        self.consoleTextEdit.setObjectName(u"consoleTextEdit")
        sizePolicy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.consoleTextEdit.sizePolicy().hasHeightForWidth())
        self.consoleTextEdit.setSizePolicy(sizePolicy)
        self.consoleTextEdit.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.consoleTextEdit.setLineWrapMode(QPlainTextEdit.NoWrap)
        self.splitter.addWidget(self.consoleTextEdit)
        self.fileSelectionTableView = QTableView(self.splitter)
        self.fileSelectionTableView.setObjectName(u"fileSelectionTableView")
        self.splitter.addWidget(self.fileSelectionTableView)

        self.verticalLayout.addWidget(self.splitter)


        self.retranslateUi(ConsoleFromFileWidget)

        QMetaObject.connectSlotsByName(ConsoleFromFileWidget)
    # setupUi

    def retranslateUi(self, ConsoleFromFileWidget):
        ConsoleFromFileWidget.setWindowTitle(QCoreApplication.translate("ConsoleFromFileWidget", u"Form", None))
        self.consoleTextEdit.setPlainText("")
    # retranslateUi

