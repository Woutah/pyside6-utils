# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'FramelessMdiWindow.ui'
##
## Created by: Qt User Interface Compiler version 6.5.1
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
from PySide6.QtWidgets import (QApplication, QFrame, QHBoxLayout, QLabel,
    QPushButton, QSizePolicy, QVBoxLayout, QWidget)
import pyside6_utils.icons.app_resources_rc

class Ui_FramelessMidiWindow(object):
    def setupUi(self, FramelessMidiWindow):
        if not FramelessMidiWindow.objectName():
            FramelessMidiWindow.setObjectName(u"FramelessMidiWindow")
        FramelessMidiWindow.resize(424, 463)
        FramelessMidiWindow.setMinimumSize(QSize(60, 60))
        FramelessMidiWindow.setAutoFillBackground(False)
        self.verticalLayout_4 = QVBoxLayout(FramelessMidiWindow)
        self.verticalLayout_4.setSpacing(0)
        self.verticalLayout_4.setObjectName(u"verticalLayout_4")
        self.verticalLayout_4.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_3 = QVBoxLayout()
        self.verticalLayout_3.setSpacing(0)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.frame = QFrame(FramelessMidiWindow)
        self.frame.setObjectName(u"frame")
        self.frame.setAutoFillBackground(True)
        self.frame.setFrameShape(QFrame.StyledPanel)
        self.frame.setFrameShadow(QFrame.Plain)
        self.frame.setLineWidth(2)
        self.verticalLayout_2 = QVBoxLayout(self.frame)
        self.verticalLayout_2.setSpacing(0)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.verticalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.titleBar = QFrame(self.frame)
        self.titleBar.setObjectName(u"titleBar")
        sizePolicy = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.titleBar.sizePolicy().hasHeightForWidth())
        self.titleBar.setSizePolicy(sizePolicy)
        self.titleBar.setFrameShape(QFrame.StyledPanel)
        self.titleBar.setFrameShadow(QFrame.Plain)
        self.titleBar.setLineWidth(3)
        self.horizontalLayout = QHBoxLayout(self.titleBar)
        self.horizontalLayout.setSpacing(0)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        self.titleLabel = QLabel(self.titleBar)
        self.titleLabel.setObjectName(u"titleLabel")
        font = QFont()
        font.setBold(True)
        self.titleLabel.setFont(font)

        self.horizontalLayout.addWidget(self.titleLabel)

        self.MinimizeButton = QPushButton(self.titleBar)
        self.MinimizeButton.setObjectName(u"MinimizeButton")
        sizePolicy1 = QSizePolicy(QSizePolicy.Maximum, QSizePolicy.Fixed)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.MinimizeButton.sizePolicy().hasHeightForWidth())
        self.MinimizeButton.setSizePolicy(sizePolicy1)
        icon = QIcon()
        icon.addFile(u":/icons/actions/list-remove.png", QSize(), QIcon.Normal, QIcon.Off)
        self.MinimizeButton.setIcon(icon)
        self.MinimizeButton.setIconSize(QSize(15, 15))
        self.MinimizeButton.setFlat(False)

        self.horizontalLayout.addWidget(self.MinimizeButton)

        self.zoomButton = QPushButton(self.titleBar)
        self.zoomButton.setObjectName(u"zoomButton")
        sizePolicy1.setHeightForWidth(self.zoomButton.sizePolicy().hasHeightForWidth())
        self.zoomButton.setSizePolicy(sizePolicy1)
        icon1 = QIcon()
        icon1.addFile(u":/icons/actions/system-search.png", QSize(), QIcon.Normal, QIcon.Off)
        self.zoomButton.setIcon(icon1)
        self.zoomButton.setIconSize(QSize(15, 15))
        self.zoomButton.setFlat(False)

        self.horizontalLayout.addWidget(self.zoomButton)


        self.verticalLayout_2.addWidget(self.titleBar)

        self.contentLayout = QVBoxLayout()
        self.contentLayout.setObjectName(u"contentLayout")

        self.verticalLayout_2.addLayout(self.contentLayout)

        self.verticalLayout_2.setStretch(1, 1)

        self.verticalLayout_3.addWidget(self.frame)


        self.verticalLayout_4.addLayout(self.verticalLayout_3)


        self.retranslateUi(FramelessMidiWindow)

        QMetaObject.connectSlotsByName(FramelessMidiWindow)
    # setupUi

    def retranslateUi(self, FramelessMidiWindow):
        FramelessMidiWindow.setWindowTitle(QCoreApplication.translate("FramelessMidiWindow", u"Form", None))
        self.titleLabel.setText(QCoreApplication.translate("FramelessMidiWindow", u"WindowTitle", None))
        self.MinimizeButton.setText("")
        self.zoomButton.setText("")
    # retranslateUi

