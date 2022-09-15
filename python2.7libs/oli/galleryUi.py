# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'gallery.ui'
##
## Created by: Qt User Interface Compiler version 5.15.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *


class Ui_AssetGallery(object):
    def setupUi(self, AssetGallery):
        if not AssetGallery.objectName():
            AssetGallery.setObjectName(u"AssetGallery")
        AssetGallery.resize(622, 402)
        self.verticalLayout_2 = QVBoxLayout(AssetGallery)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.verticalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.tabWidget = QTabWidget(AssetGallery)
        self.tabWidget.setObjectName(u"tabWidget")
#if QT_CONFIG(whatsthis)
        self.tabWidget.setWhatsThis(u"")
#endif // QT_CONFIG(whatsthis)
        self.libraryTab = QWidget()
        self.libraryTab.setObjectName(u"libraryTab")
        self.verticalLayout = QVBoxLayout(self.libraryTab)
        self.verticalLayout.setSpacing(5)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(0, 3, 0, 0)
        self.widget = QWidget(self.libraryTab)
        self.widget.setObjectName(u"widget")
        self.horizontalLayout_2 = QHBoxLayout(self.widget)
        self.horizontalLayout_2.setSpacing(5)
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.horizontalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.rootBox = QComboBox(self.widget)
        self.rootBox.setObjectName(u"rootBox")

        self.horizontalLayout_2.addWidget(self.rootBox)

        self.collectionsBox = QComboBox(self.widget)
        self.collectionsBox.addItem("")
        self.collectionsBox.setObjectName(u"collectionsBox")

        self.horizontalLayout_2.addWidget(self.collectionsBox)


        self.verticalLayout.addWidget(self.widget)

        self.libraryTopBarContainer = QWidget(self.libraryTab)
        self.libraryTopBarContainer.setObjectName(u"libraryTopBarContainer")
        self.horizontalLayout = QHBoxLayout(self.libraryTopBarContainer)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        self.searchBar = QLineEdit(self.libraryTopBarContainer)
        self.searchBar.setObjectName(u"searchBar")

        self.horizontalLayout.addWidget(self.searchBar)

        self.thumbnailSizeSlider = QSlider(self.libraryTopBarContainer)
        self.thumbnailSizeSlider.setObjectName(u"thumbnailSizeSlider")
        self.thumbnailSizeSlider.setMinimum(50)
        self.thumbnailSizeSlider.setMaximum(500)
        self.thumbnailSizeSlider.setValue(50)
        self.thumbnailSizeSlider.setOrientation(Qt.Horizontal)

        self.horizontalLayout.addWidget(self.thumbnailSizeSlider)

        self.toggleListView = QToolButton(self.libraryTopBarContainer)
        self.toggleListView.setObjectName(u"toggleListView")
        icon = QIcon()
        icon.addFile(u"C:/Users/gabriel.leite/.designer/img/list_view.png", QSize(), QIcon.Normal, QIcon.On)
        self.toggleListView.setIcon(icon)
        self.toggleListView.setIconSize(QSize(16, 16))
        self.toggleListView.setCheckable(True)

        self.horizontalLayout.addWidget(self.toggleListView)


        self.verticalLayout.addWidget(self.libraryTopBarContainer)

        self.assetList = QListWidget(self.libraryTab)
        self.assetList.setObjectName(u"assetList")
        self.assetList.setAcceptDrops(True)
        self.assetList.setDragEnabled(True)
        self.assetList.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.assetList.setMovement(QListView.Static)
        self.assetList.setResizeMode(QListView.Adjust)
        self.assetList.setSpacing(0)
        self.assetList.setGridSize(QSize(100, 100))
        self.assetList.setViewMode(QListView.IconMode)
        self.assetList.setUniformItemSizes(False)

        self.verticalLayout.addWidget(self.assetList)

        self.messageBrowser = QTextBrowser(self.libraryTab)
        self.messageBrowser.setObjectName(u"messageBrowser")
        self.messageBrowser.setMaximumSize(QSize(16777215, 0))
        self.messageBrowser.setOpenExternalLinks(True)

        self.verticalLayout.addWidget(self.messageBrowser)

        self.tabWidget.addTab(self.libraryTab, "")
        self.folderManagementTab = QWidget()
        self.folderManagementTab.setObjectName(u"folderManagementTab")
        self.verticalLayout_3 = QVBoxLayout(self.folderManagementTab)
        self.verticalLayout_3.setSpacing(10)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.verticalLayout_3.setContentsMargins(0, 3, 0, 0)
        self.foldersTable = QTableWidget(self.folderManagementTab)
        if (self.foldersTable.columnCount() < 3):
            self.foldersTable.setColumnCount(3)
        __qtablewidgetitem = QTableWidgetItem()
        self.foldersTable.setHorizontalHeaderItem(0, __qtablewidgetitem)
        __qtablewidgetitem1 = QTableWidgetItem()
        self.foldersTable.setHorizontalHeaderItem(1, __qtablewidgetitem1)
        __qtablewidgetitem2 = QTableWidgetItem()
        self.foldersTable.setHorizontalHeaderItem(2, __qtablewidgetitem2)
        self.foldersTable.setObjectName(u"foldersTable")
        self.foldersTable.setContextMenuPolicy(Qt.CustomContextMenu)
        self.foldersTable.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.foldersTable.setCornerButtonEnabled(False)
        self.foldersTable.setColumnCount(3)
        self.foldersTable.verticalHeader().setVisible(False)

        self.verticalLayout_3.addWidget(self.foldersTable)

        self.tabWidget.addTab(self.folderManagementTab, "")

        self.verticalLayout_2.addWidget(self.tabWidget)


        self.retranslateUi(AssetGallery)
        self.searchBar.textChanged.connect(AssetGallery.filterItems)
        self.collectionsBox.currentTextChanged.connect(AssetGallery.collectionChanged)
        self.thumbnailSizeSlider.valueChanged.connect(AssetGallery.thumbnailResize)
        self.assetList.itemDoubleClicked.connect(AssetGallery.import_asset)
        self.toggleListView.toggled.connect(AssetGallery.toggleListView)
        self.foldersTable.customContextMenuRequested.connect(AssetGallery.spawnFoldersTableContextMenu)
        self.thumbnailSizeSlider.sliderReleased.connect(AssetGallery.saveState)
        self.rootBox.currentTextChanged.connect(AssetGallery.rootChanged)
        self.foldersTable.itemChanged.connect(AssetGallery.saveState)
        self.tabWidget.currentChanged.connect(AssetGallery.tabChanged)

        self.tabWidget.setCurrentIndex(0)


        QMetaObject.connectSlotsByName(AssetGallery)
    # setupUi

    def retranslateUi(self, AssetGallery):
        AssetGallery.setWindowTitle(QCoreApplication.translate("AssetGallery", u"Form", None))
        self.collectionsBox.setItemText(0, QCoreApplication.translate("AssetGallery", u"Collection \u2193 ", None))

        self.collectionsBox.setCurrentText(QCoreApplication.translate("AssetGallery", u"Collection \u2193 ", None))
        self.searchBar.setPlaceholderText(QCoreApplication.translate("AssetGallery", u"Search String or Pattern (Eg.: Soldado*A001)", None))
#if QT_CONFIG(tooltip)
        self.thumbnailSizeSlider.setToolTip(QCoreApplication.translate("AssetGallery", u"<html><head/><body><p>Changes the thumbnail sizes</p></body></html>", u"AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(statustip)
        self.thumbnailSizeSlider.setStatusTip("")
#endif // QT_CONFIG(statustip)
#if QT_CONFIG(whatsthis)
        self.thumbnailSizeSlider.setWhatsThis("")
#endif // QT_CONFIG(whatsthis)
#if QT_CONFIG(tooltip)
        self.toggleListView.setToolTip(QCoreApplication.translate("AssetGallery", u"<html><head/><body><p>Toggles between the List and Grid view modes</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.toggleListView.setText("")
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.libraryTab), QCoreApplication.translate("AssetGallery", u"Library", None))
        ___qtablewidgetitem = self.foldersTable.horizontalHeaderItem(0)
        ___qtablewidgetitem.setText(QCoreApplication.translate("AssetGallery", u"root", None));
        ___qtablewidgetitem1 = self.foldersTable.horizontalHeaderItem(1)
        ___qtablewidgetitem1.setText(QCoreApplication.translate("AssetGallery", u"model", None));
        ___qtablewidgetitem2 = self.foldersTable.horizontalHeaderItem(2)
        ___qtablewidgetitem2.setText(QCoreApplication.translate("AssetGallery", u"config", None));
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.folderManagementTab), QCoreApplication.translate("AssetGallery", u"Folder Management", None))
    # retranslateUi

