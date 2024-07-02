# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'TableFilterDialog.ui'
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
from PySide6.QtWidgets import (QAbstractButton, QApplication, QCheckBox, QComboBox,
    QDialog, QDialogButtonBox, QFormLayout, QHBoxLayout,
    QLabel, QLayout, QPushButton, QScrollArea,
    QSizePolicy, QSpacerItem, QVBoxLayout, QWidget)

class Ui_TableFilterDialog(object):
    def setupUi(self, TableFilterDialog):
        if not TableFilterDialog.objectName():
            TableFilterDialog.setObjectName(u"TableFilterDialog")
        TableFilterDialog.resize(353, 301)
        self.verticalLayout = QVBoxLayout(TableFilterDialog)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.StringFilterLayout = QFormLayout()
        self.StringFilterLayout.setObjectName(u"StringFilterLayout")
        self.label = QLabel(TableFilterDialog)
        self.label.setObjectName(u"label")

        self.StringFilterLayout.setWidget(0, QFormLayout.LabelRole, self.label)

        self.filterRegexComboBox = QComboBox(TableFilterDialog)
        self.filterRegexComboBox.setObjectName(u"filterRegexComboBox")
        self.filterRegexComboBox.setEditable(True)

        self.StringFilterLayout.setWidget(0, QFormLayout.FieldRole, self.filterRegexComboBox)


        self.verticalLayout.addLayout(self.StringFilterLayout)

        self.NumericFilter = QVBoxLayout()
        self.NumericFilter.setObjectName(u"NumericFilter")

        self.verticalLayout.addLayout(self.NumericFilter)

        self.useOldFilterCheckBox = QCheckBox(TableFilterDialog)
        self.useOldFilterCheckBox.setObjectName(u"useOldFilterCheckBox")

        self.verticalLayout.addWidget(self.useOldFilterCheckBox)

        self.horizontalLayout_4 = QHBoxLayout()
        self.horizontalLayout_4.setObjectName(u"horizontalLayout_4")
        self.pushButton_2 = QPushButton(TableFilterDialog)
        self.pushButton_2.setObjectName(u"pushButton_2")

        self.horizontalLayout_4.addWidget(self.pushButton_2)

        self.pushButton = QPushButton(TableFilterDialog)
        self.pushButton.setObjectName(u"pushButton")

        self.horizontalLayout_4.addWidget(self.pushButton)


        self.verticalLayout.addLayout(self.horizontalLayout_4)

        self.resultsScrollArea = QScrollArea(TableFilterDialog)
        self.resultsScrollArea.setObjectName(u"resultsScrollArea")
        self.resultsScrollArea.setWidgetResizable(True)
        self.scrollAreaWidgetContents = QWidget()
        self.scrollAreaWidgetContents.setObjectName(u"scrollAreaWidgetContents")
        self.scrollAreaWidgetContents.setGeometry(QRect(0, 0, 333, 149))
        self.verticalLayout_3 = QVBoxLayout(self.scrollAreaWidgetContents)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.resultsLayout = QVBoxLayout()
        self.resultsLayout.setSpacing(0)
        self.resultsLayout.setObjectName(u"resultsLayout")
        self.resultsLayout.setSizeConstraint(QLayout.SetMaximumSize)

        self.verticalLayout_3.addLayout(self.resultsLayout)

        self.verticalSpacer = QSpacerItem(20, 10000, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.verticalLayout_3.addItem(self.verticalSpacer)

        self.resultsScrollArea.setWidget(self.scrollAreaWidgetContents)

        self.verticalLayout.addWidget(self.resultsScrollArea)

        self.buttonBox = QDialogButtonBox(TableFilterDialog)
        self.buttonBox.setObjectName(u"buttonBox")
        self.buttonBox.setOrientation(Qt.Horizontal)
        self.buttonBox.setStandardButtons(QDialogButtonBox.Cancel|QDialogButtonBox.Ok)

        self.verticalLayout.addWidget(self.buttonBox)


        self.retranslateUi(TableFilterDialog)
        self.buttonBox.rejected.connect(TableFilterDialog.reject)
        self.buttonBox.accepted.connect(TableFilterDialog.accept)

        QMetaObject.connectSlotsByName(TableFilterDialog)
    # setupUi

    def retranslateUi(self, TableFilterDialog):
        TableFilterDialog.setWindowTitle(QCoreApplication.translate("TableFilterDialog", u"Dialog", None))
        self.label.setText(QCoreApplication.translate("TableFilterDialog", u"Filter:", None))
        self.useOldFilterCheckBox.setText(QCoreApplication.translate("TableFilterDialog", u"Add Filter To Current Filter", None))
        self.pushButton_2.setText(QCoreApplication.translate("TableFilterDialog", u"Select All", None))
        self.pushButton.setText(QCoreApplication.translate("TableFilterDialog", u"Deselect All", None))
    # retranslateUi

