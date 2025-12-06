from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *

class GalleryView(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)        
        self.setupUi()
        self.setupConnections()

    def setupUi(self):
        # Main Layout
        self.mainLayout = QVBoxLayout(self)
        self.mainLayout.setContentsMargins(0, 0, 0, 0)
        self.mainLayout.setObjectName("mainLayout")

        # Tab Widget
        self.tabWidget = QTabWidget(self)
        self.tabWidget.setObjectName("tabWidget")
        self.mainLayout.addWidget(self.tabWidget)

        # --------------------------------------------------------------------
        # Tab 1: Library
        # --------------------------------------------------------------------
        self.libraryTab = QWidget()
        self.libraryTab.setObjectName("libraryTab")
        self.libraryLayout = QVBoxLayout(self.libraryTab)
        self.libraryLayout.setContentsMargins(0, 3, 0, 0)
        self.libraryLayout.setSpacing(3)

        # Top Nav Container (Root & Collections)
        self.topNavContainer = QWidget(self.libraryTab)
        self.topNavLayout = QHBoxLayout(self.topNavContainer)
        self.topNavLayout.setContentsMargins(0, 0, 0, 0)
        self.topNavLayout.setSpacing(5)

        self.rootBox = QComboBox(self.topNavContainer)
        self.rootBox.setObjectName("rootBox")
        self.topNavLayout.addWidget(self.rootBox)

        self.collectionsBox = QComboBox(self.topNavContainer)
        self.collectionsBox.setObjectName("collectionsBox")
        self.topNavLayout.addWidget(self.collectionsBox)

        self.libraryLayout.addWidget(self.topNavContainer)

        # Toolbar Container (Search, Filters, Size)
        self.toolbarContainer = QWidget(self.libraryTab)
        self.toolbarLayout = QHBoxLayout(self.toolbarContainer)
        self.toolbarLayout.setContentsMargins(0, 0, 0, 0)

        self.searchBar = QLineEdit(self.toolbarContainer)
        self.searchBar.setObjectName("searchBar")
        self.searchBar.setPlaceholderText("Search string or Pattern (Eg.: tree*01)")
        self.toolbarLayout.addWidget(self.searchBar)

        self.toggleFavorites = QToolButton(self.toolbarContainer)
        self.toggleFavorites.setObjectName("toggleFavorites")
        self.toggleFavorites.setIconSize(QSize(16, 16))
        self.toggleFavorites.setCheckable(True)
        self.toggleFavorites.setToolTip("Isolate Favorites")
        self.toolbarLayout.addWidget(self.toggleFavorites)

        self.applyTag = QToolButton(self.toolbarContainer)
        self.applyTag.setObjectName("applyTag")
        self.applyTag.setText("TAG")
        self.applyTag.setCheckable(True)
        self.applyTag.setIconSize(QSize(16, 16))
        self.applyTag.setToolTip("Isolate items tagged as...")
        self.toolbarLayout.addWidget(self.applyTag)

        self.toolbarSpacer = QSpacerItem(50, 0, QSizePolicy.Preferred, QSizePolicy.Minimum)
        self.toolbarLayout.addItem(self.toolbarSpacer)

        self.thumbnailSizeSlider = QSlider(self.toolbarContainer)
        self.thumbnailSizeSlider.setObjectName("thumbnailSizeSlider")
        self.thumbnailSizeSlider.setOrientation(Qt.Horizontal)
        self.thumbnailSizeSlider.setMinimum(50)
        self.thumbnailSizeSlider.setMaximum(500)
        self.thumbnailSizeSlider.setValue(50)
        self.thumbnailSizeSlider.setToolTip("Changes the thumbnail sizes")
        self.toolbarLayout.addWidget(self.thumbnailSizeSlider)

        self.toggleListView = QToolButton(self.toolbarContainer)
        self.toggleListView.setObjectName("toggleListView")
        self.toggleListView.setEnabled(False)
        self.toggleListView.setCheckable(True)
        self.toggleListView.setIconSize(QSize(16, 16))
        self.toggleListView.setToolTip("Toggles between the List and Grid view modes")
        self.toolbarLayout.addWidget(self.toggleListView)

        self.libraryLayout.addWidget(self.toolbarContainer)

        # Splitter (Tree & Asset List)
        self.assetListSplitter = QSplitter(self.libraryTab)
        self.assetListSplitter.setOrientation(Qt.Horizontal)
        self.assetListSplitter.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # Left Nav (Tree)
        self.leftNavWidget = QWidget(self.assetListSplitter)
        self.leftNavLayout = QVBoxLayout(self.leftNavWidget)
        self.leftNavLayout.setContentsMargins(0, 0, 0, 0)
        self.leftNavLayout.setSpacing(0)

        self.treeNav = QTreeWidget(self.leftNavWidget)
        self.treeNav.setObjectName("treeNav")
        self.treeNav.setHeaderLabel("Category")
        self.treeNav.setHeaderHidden(True)
        self.treeNav.setRootIsDecorated(False)
        self.treeNav.setAnimated(True)
        self.leftNavLayout.addWidget(self.treeNav)
        
        self.assetListSplitter.addWidget(self.leftNavWidget)

        # Right Content (Asset List)
        self.assetList = QListWidget(self.assetListSplitter)
        self.assetList.setObjectName("assetList")
        self.assetList.setViewMode(QListView.IconMode)
        self.assetList.setResizeMode(QListView.Adjust)
        self.assetList.setMovement(QListView.Static)
        self.assetList.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.assetList.setDragEnabled(True)
        self.assetList.setAcceptDrops(True)
        self.assetList.setGridSize(QSize(100, 100))
        self.assetListSplitter.addWidget(self.assetList)

        self.libraryLayout.addWidget(self.assetListSplitter)

        # Message Browser
        self.messageBrowser = QTextBrowser(self.libraryTab)
        self.messageBrowser.setObjectName("messageBrowser")
        self.messageBrowser.setMaximumHeight(100) # Assuming intended height from "0" max size in original
        self.messageBrowser.setOpenExternalLinks(True)
        self.libraryLayout.addWidget(self.messageBrowser)

        self.tabWidget.addTab(self.libraryTab, "Library")

        # --------------------------------------------------------------------
        # Tab 2: Folder Management
        # --------------------------------------------------------------------
        self.folderManagementTab = QWidget()
        self.folderManagementTab.setObjectName("folderManagementTab")
        self.folderLayout = QVBoxLayout(self.folderManagementTab)
        self.folderLayout.setContentsMargins(0, 3, 0, 0)
        self.folderLayout.setSpacing(10)

        self.foldersTable = QTableWidget(self.folderManagementTab)
        self.foldersTable.setObjectName("foldersTable")
        self.foldersTable.setColumnCount(3)
        self.foldersTable.setHorizontalHeaderLabels(["root", "model", "config"])
        self.foldersTable.verticalHeader().setVisible(False)
        self.foldersTable.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.foldersTable.setContextMenuPolicy(Qt.CustomContextMenu)
        self.foldersTable.setCornerButtonEnabled(False)
        
        self.folderLayout.addWidget(self.foldersTable)

        self.tabWidget.addTab(self.folderManagementTab, "Folder Management")

    def setupConnections(self):
        # UI Element connections
        self.searchBar.textChanged.connect(self.filterItems)
        self.collectionsBox.currentTextChanged.connect(self.collectionChanged)
        self.thumbnailSizeSlider.valueChanged.connect(self.thumbnailResize)
        self.thumbnailSizeSlider.sliderReleased.connect(self.saveState)
        self.toggleListView.toggled.connect(self.toggleListViewMode)
        self.rootBox.currentTextChanged.connect(self.rootChanged)
        self.tabWidget.currentChanged.connect(self.tabChanged)
        self.toggleFavorites.toggled.connect(self.toggleFavoritesOnly)
        self.treeNav.currentItemChanged.connect(self.treeNavItemChanged)
        self.assetList.itemDoubleClicked.connect(self.import_asset)
        
        # Table connections
        self.foldersTable.customContextMenuRequested.connect(self.spawnFoldersTableContextMenu)
        self.foldersTable.itemChanged.connect(self.saveState)

    # ------------------------------------------------------------------------
    # Placeholder Slots (Logic to be implemented)
    # ------------------------------------------------------------------------

    def filterItems(self, text):
        pass

    def collectionChanged(self, text):
        pass

    def thumbnailResize(self, value):
        pass

    def saveState(self):
        pass

    def toggleListViewMode(self, checked):
        pass

    def rootChanged(self, text):
        pass

    def tabChanged(self, index):
        pass

    def toggleFavoritesOnly(self, checked):
        pass

    def treeNavItemChanged(self, current, previous):
        pass

    def import_asset(self, item):
        pass

    def spawnFoldersTableContextMenu(self, pos):
        pass