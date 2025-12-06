import os
import json

from PySide6.QtCore import QObject, Slot
from PySide6.QtWidgets import QTableWidgetItem

from .GalleryView import GalleryView
from .GalleryModel import GalleryModel


class GalleryViewModel(QObject):

    def __init__(self, parent=None):
        super().__init__(parent)

        # Initialize View and Model
        self.view = GalleryView(parent=parent)
        self.model = GalleryModel(parent=parent)

        # self.loadState()
        # self.bindSignals()

    def loadState(self):
        """Initial population of the View from Model/Settings."""
        
        # Load UI state settings (thumbnail size, last root, etc.)
        settings = {}
        
        if "thumbnail_size" in settings:
            self.view.thumbnailSizeSlider.setValue(settings["thumbnail_size"])
        
        # Trigger Model to load initial data
        self.model.refreshRoots()
        
        # Restore last used root if available
        last_root = settings.get("last_root_index", 0)
        if last_root < self.view.rootBox.count():
            self.view.rootBox.setCurrentIndex(last_root)

    def bindSignals(self):
        """Connects View signals to Model logic and vice-versa."""

        # --- View -> Model Connections ---

        # Navigation & Filtering
        self.view.rootBox.currentTextChanged.connect(self.model.setRoot)
        self.view.collectionsBox.currentTextChanged.connect(self.model.setCollection)
        self.view.searchBar.textChanged.connect(self.model.setFilterText)
        self.view.toggleFavorites.toggled.connect(self.model.setFavoritesOnly)
        self.view.applyTag.toggled.connect(self.model.setTagFilter)

        # Tree Navigation
        self.view.treeNav.currentItemChanged.connect(self._handleCategoryChange)

        # Asset Interactions
        self.view.assetList.itemDoubleClicked.connect(self._handleImport)
        
        # Folder Management
        self.view.foldersTable.itemChanged.connect(self._handleFolderConfigChange)

        # --- Model -> View Connections ---

        # Data Population
        self.model.rootsLoadedSignal.connect(self._populateRoots)
        self.model.collectionsLoadedSignal.connect(self._populateCollections)
        self.model.assetsLoadedSignal.connect(self.view.populateAssetList) # Assuming View has this helper
        self.model.categoriesLoadedSignal.connect(self.view.populateCategoryTree) 

        # Status & Feedback
        self.model.errorSignal.connect(lambda msg: mira.log.err(msg))
        self.model.statusSignal.connect(lambda msg: mira.log.info(msg))

        # --- View Internal Logic (State Saving) ---
        self.view.thumbnailSizeSlider.valueChanged.connect(self.view.refreshGridSize)
        self.view.thumbnailSizeSlider.sliderReleased.connect(self.saveState)
        self.view.rootBox.currentIndexChanged.connect(self.saveState)

    def saveState(self):
        """Persists simple UI state (slider positions, last selection) to settings."""
        state = {
            "thumbnail_size": self.view.thumbnailSizeSlider.value(),
            "last_root_index": self.view.rootBox.currentIndex()
        }
        mira.settings.set("gallery_prefs", state)

    @Slot(str)
    def _populateRoots(self, roots: list):
        """Updates the root combobox when the model loads roots."""
        self.view.rootBox.blockSignals(True)
        self.view.rootBox.clear()
        self.view.rootBox.addItems(roots)
        self.view.rootBox.blockSignals(False)
        
        # Trigger collection load for the current root
        if roots:
            self.model.setRoot(self.view.rootBox.currentText())

    @Slot(str)
    def _populateCollections(self, collections: list):
        """Updates the collections combobox."""
        self.view.collectionsBox.blockSignals(True)
        self.view.collectionsBox.clear()
        self.view.collectionsBox.addItems(collections)
        self.view.collectionsBox.blockSignals(False)

        # Select first available or restore previous if needed
        if collections:
            self.model.setCollection(collections[0])

    def _handleCategoryChange(self, current, previous):
        """Extracts category data from tree item and updates model."""
        if not current:
            return
        
        category_path = current.text(0) # Or current.data(0, Qt.UserRole)
        self.model.setCategory(category_path)

    def _handleImport(self, item):
        """Bridges the double-click event to the model's import logic."""
        asset_data = item.data(Qt.UserRole) # Assuming asset data is stored in UserRole
        if asset_data:
            mira.log.head(f"Importing {asset_data.get('name', 'Asset')}...")
            self.model.importAsset(asset_data)

    def _handleFolderConfigChange(self, item):
        """Updates folder configuration in the model when the table changes."""
        row = item.row()
        root = self.view.foldersTable.item(row, 0).text()
        model_path = self.view.foldersTable.item(row, 1).text()
        config_path = self.view.foldersTable.item(row, 2).text()
        
        self.model.updateFolderConfig(root, model_path, config_path)