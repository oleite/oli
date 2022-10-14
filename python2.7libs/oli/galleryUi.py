# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'galleryUi.ui'
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
        self.verticalLayout.setContentsMargins(0, 5, 0, 0)
        self.topNavContainer = QWidget(self.libraryTab)
        self.topNavContainer.setObjectName(u"topNavContainer")
        self.horizontalLayout_2 = QHBoxLayout(self.topNavContainer)
        self.horizontalLayout_2.setSpacing(5)
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.horizontalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.rootBox = QComboBox(self.topNavContainer)
        self.rootBox.addItem("")
        self.rootBox.setObjectName(u"rootBox")

        self.horizontalLayout_2.addWidget(self.rootBox)

        self.collectionsBox = QComboBox(self.topNavContainer)
        self.collectionsBox.addItem("")
        self.collectionsBox.setObjectName(u"collectionsBox")

        self.horizontalLayout_2.addWidget(self.collectionsBox)


        self.verticalLayout.addWidget(self.topNavContainer)

        self.libraryTopBarContainer = QWidget(self.libraryTab)
        self.libraryTopBarContainer.setObjectName(u"libraryTopBarContainer")
        self.horizontalLayout = QHBoxLayout(self.libraryTopBarContainer)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        self.searchBar = QLineEdit(self.libraryTopBarContainer)
        self.searchBar.setObjectName(u"searchBar")

        self.horizontalLayout.addWidget(self.searchBar)

        self.toggleFavorites = QToolButton(self.libraryTopBarContainer)
        self.toggleFavorites.setObjectName(u"toggleFavorites")
        self.toggleFavorites.setIconSize(QSize(16, 16))
        self.toggleFavorites.setCheckable(True)

        self.horizontalLayout.addWidget(self.toggleFavorites)

        self.applyTag = QToolButton(self.libraryTopBarContainer)
        self.applyTag.setObjectName(u"applyTag")
        self.applyTag.setMaximumSize(QSize(16777214, 16777215))
        self.applyTag.setIconSize(QSize(16, 16))
        self.applyTag.setCheckable(True)

        self.horizontalLayout.addWidget(self.applyTag)

        self.horizontalSpacer = QSpacerItem(50, 0, QSizePolicy.Preferred, QSizePolicy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer)

        self.thumbnailSizeSlider = QSlider(self.libraryTopBarContainer)
        self.thumbnailSizeSlider.setObjectName(u"thumbnailSizeSlider")
        self.thumbnailSizeSlider.setMinimum(50)
        self.thumbnailSizeSlider.setMaximum(500)
        self.thumbnailSizeSlider.setValue(50)
        self.thumbnailSizeSlider.setOrientation(Qt.Horizontal)

        self.horizontalLayout.addWidget(self.thumbnailSizeSlider)

        self.toggleListView = QToolButton(self.libraryTopBarContainer)
        self.toggleListView.setObjectName(u"toggleListView")
        self.toggleListView.setIconSize(QSize(16, 16))
        self.toggleListView.setCheckable(True)

        self.horizontalLayout.addWidget(self.toggleListView)


        self.verticalLayout.addWidget(self.libraryTopBarContainer)

        self.assetListSplitter = QSplitter(self.libraryTab)
        self.assetListSplitter.setObjectName(u"assetListSplitter")
        sizePolicy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.assetListSplitter.sizePolicy().hasHeightForWidth())
        self.assetListSplitter.setSizePolicy(sizePolicy)
        self.assetListSplitter.setOrientation(Qt.Horizontal)
        self.treeNav = QTreeWidget(self.assetListSplitter)
        self.treeNav.setObjectName(u"treeNav")
        self.treeNav.setHeaderHidden(True)
        self.assetListSplitter.addWidget(self.treeNav)
        self.treeNav.header().setVisible(False)
        self.assetList = QListWidget(self.assetListSplitter)
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
        self.assetListSplitter.addWidget(self.assetList)

        self.verticalLayout.addWidget(self.assetListSplitter)

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
        self.toggleFavorites.toggled.connect(AssetGallery.toggleFavoritesOnly)
        self.treeNav.currentItemChanged.connect(AssetGallery.treeNavItemChanged)

        self.tabWidget.setCurrentIndex(0)


        QMetaObject.connectSlotsByName(AssetGallery)
    # setupUi

    def retranslateUi(self, AssetGallery):
        AssetGallery.setWindowTitle(QCoreApplication.translate("AssetGallery", u"Form", None))
        self.rootBox.setItemText(0, QCoreApplication.translate("AssetGallery", u"Root \u2193", None))

        self.collectionsBox.setItemText(0, QCoreApplication.translate("AssetGallery", u"Collection \u2193 ", None))

        self.collectionsBox.setCurrentText(QCoreApplication.translate("AssetGallery", u"Collection \u2193 ", None))
        self.searchBar.setPlaceholderText(QCoreApplication.translate("AssetGallery", u"Search string or Pattern (Eg.: tree*01)", None))
#if QT_CONFIG(tooltip)
        self.toggleFavorites.setToolTip(QCoreApplication.translate("AssetGallery", u"Isolate Favorites", None))
#endif // QT_CONFIG(tooltip)
        self.toggleFavorites.setText("")
#if QT_CONFIG(tooltip)
        self.applyTag.setToolTip(QCoreApplication.translate("AssetGallery", u"Isolate items tagged as...", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(accessibility)
        self.applyTag.setAccessibleName("")
#endif // QT_CONFIG(accessibility)
        self.applyTag.setText(QCoreApplication.translate("AssetGallery", u"TAG", None))
#if QT_CONFIG(tooltip)
        self.thumbnailSizeSlider.setToolTip(QCoreApplication.translate("AssetGallery", u"Changes the thumbnail sizes", u"AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(statustip)
        self.thumbnailSizeSlider.setStatusTip("")
#endif // QT_CONFIG(statustip)
#if QT_CONFIG(whatsthis)
        self.thumbnailSizeSlider.setWhatsThis("")
#endif // QT_CONFIG(whatsthis)
#if QT_CONFIG(tooltip)
        self.toggleListView.setToolTip(QCoreApplication.translate("AssetGallery", u"Toggles between the List and Grid view modes", None))
#endif // QT_CONFIG(tooltip)
        self.toggleListView.setText("")
        ___qtreewidgetitem = self.treeNav.headerItem()
        ___qtreewidgetitem.setText(0, QCoreApplication.translate("AssetGallery", u"category", None));
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.libraryTab), QCoreApplication.translate("AssetGallery", u"Library", None))
        ___qtablewidgetitem = self.foldersTable.horizontalHeaderItem(0)
        ___qtablewidgetitem.setText(QCoreApplication.translate("AssetGallery", u"root", None));
        ___qtablewidgetitem1 = self.foldersTable.horizontalHeaderItem(1)
        ___qtablewidgetitem1.setText(QCoreApplication.translate("AssetGallery", u"model", None));
        ___qtablewidgetitem2 = self.foldersTable.horizontalHeaderItem(2)
        ___qtablewidgetitem2.setText(QCoreApplication.translate("AssetGallery", u"config", None));
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.folderManagementTab), QCoreApplication.translate("AssetGallery", u"Folder Management", None))
    # retranslateUi

