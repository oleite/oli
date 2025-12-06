import os
import json
import time
import importlib
from imp import reload

from PySide6.QtCore import QObject, Signal, QThreadPool, QRunnable, Qt, QSize
from PySide6.QtGui import QPixmap


class LoadThumbnailRunnable(QRunnable):
    """
    Worker to load images in the background so the UI doesn't freeze.
    """
    def __init__(self, asset_data, callback):
        super(LoadThumbnailRunnable, self).__init__()
        self.asset_data = asset_data
        self.callback = callback

    def run(self):
        # Small sleep to prevent Houdini UI lockups during heavy IO
        time.sleep(0.01) 
        
        path = self.asset_data.get("thumbnail_path")
        if not path:
            return

        expanded_path = os.path.expandvars(os.path.expanduser(path))

        if os.path.exists(expanded_path):
            # Load pixmap
            pixmap = QPixmap(expanded_path).scaled(QSize(512, 512), Qt.KeepAspectRatio)
            # Return via callback (thread-safe communication handled by receiver usually)
            self.callback(self.asset_data["id"], pixmap)

class GalleryModel(QObject):
    """
    The Brains. Manages data, preferences, and Houdini interactions.
    Does NOT know about Buttons, Layouts, or Widgets.
    """

    # Signals to update the ViewModel/View
    rootsLoadedSignal = Signal(list)
    collectionsLoadedSignal = Signal(list)
    assetsLoadedSignal = Signal(list) # Sends list of data dicts
    categoriesLoadedSignal = Signal(dict) # Sends tree structure
    
    thumbnailLoadedSignal = Signal(str, object) # ID, QPixmap
    
    statusSignal = Signal(str)
    errorSignal = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)

        # State
        self.preferencesFile = os.getenv("HOUDINI_USER_PREF_DIR", "") + "/oli_gallery_prefs.json"
        self.defaultPreferencesFile = str(os.getenv("OLI_ROOT", "")) + "/oli_gallery_prefs.json"
        
        self.currentRoot = ""
        self.currentCollection = ""
        self.preferences = {}
        
        # The dynamic "Backend" (formerly called Model in your legacy code)
        self.backend = None 
        
        # Threading
        self.threadPool = QThreadPool()

        self.loadPreferences()

    # ----------------------------------------------------------------------
    # Preferences & State Management
    # ----------------------------------------------------------------------

    def loadPreferences(self):
        """Loads the JSON config into memory."""
        if not os.path.isfile(self.preferencesFile):
            if os.path.isfile(self.defaultPreferencesFile):
                self._copy_default_prefs()
            else:
                self.errorSignal.emit("No preferences file found.")
                return

        try:
            with open(self.preferencesFile, "r") as f:
                self.preferences = json.load(f)
        except ValueError:
            self.errorSignal.emit("Corrupt preferences file.")
            self.preferences = {}

    def savePreferences(self):
        """Persists current memory state to JSON."""
        try:
            with open(self.preferencesFile, "w") as f:
                json.dump(self.preferences, f, indent=4, sort_keys=True)
        except Exception as e:
            self.errorSignal.emit(f"Failed to save preferences: {str(e)}")

    def _copy_default_prefs(self):
        try:
            with open(self.defaultPreferencesFile, "r") as f:
                data = json.load(f)
            with open(self.preferencesFile, "w") as f:
                json.dump(data, f, indent=4)
        except Exception as e:
            self.errorSignal.emit(f"Failed to restore defaults: {str(e)}")

    def get_config_for_root(self, root):
        """Helper to get the 'config' dict for a specific root."""
        folders = self.preferences.get("folders", {})
        return folders.get(root, {}).get("config", {})

    def update_config_for_root(self, root, new_data):
        """Updates the config dict for a root and saves."""
        if "folders" not in self.preferences:
            self.preferences["folders"] = {}
        
        if root not in self.preferences["folders"]:
            self.preferences["folders"][root] = {}
            
        current_config = self.preferences["folders"][root].get("config", {})
        current_config.update(new_data)
        
        self.preferences["folders"][root]["config"] = current_config
        self.savePreferences()

    def updateFolderConfig(self, root, model_name, config_str):
        """Called by ViewModel when the Folder Management table changes."""
        try:
            config_data = json.loads(config_str) if config_str else {}
        except ValueError:
            config_data = {}

        if "folders" not in self.preferences:
            self.preferences["folders"] = {}

        self.preferences["folders"][root] = {
            "model": model_name,
            "config": config_data
        }
        self.savePreferences()
        self.refreshRoots() # Reload UI

    # ----------------------------------------------------------------------
    # Logic & Data Fetching
    # ----------------------------------------------------------------------

    def refreshRoots(self):
        """Parses preferences and emits available roots."""
        self.loadPreferences()
        folders = self.preferences.get("folders", {})
        
        # Convert dictionary keys to a list of roots
        roots = sorted(list(folders.keys()))
        self.rootsLoadedSignal.emit(roots)

    def setRoot(self, rootPath):
        """
        1. Sets the current root.
        2. Loads the appropriate Python Backend (legacy 'Model' class).
        3. Loads collections for this root.
        """
        if not rootPath:
            return

        self.currentRoot = rootPath
        self.statusSignal.emit(f"Switching to {rootPath}...")

        # 1. Determine which Backend class to load
        folders = self.preferences.get("folders", {})
        backend_name = folders.get(rootPath, {}).get("model", "DefaultModel")

        # 2. Load the Backend Strategy
        self._loadBackendStrategy(backend_name)

        # 3. Save state
        self.preferences["last_root"] = rootPath
        self.savePreferences()

        # 4. Fetch Collections via the Backend
        if self.backend:
             # Assuming backend has a method collectionsList() based on legacy code
            try:
                collections = self.backend.collectionsList()
                self.collectionsLoadedSignal.emit(sorted(collections))
            except Exception as e:
                self.errorSignal.emit(f"Backend error loading collections: {e}")
        else:
            self.collectionsLoadedSignal.emit([])

    def setCollection(self, collectionName):
        """
        Sets the collection and triggers asset loading.
        """
        self.currentCollection = collectionName
        
        # Save last used collection for this root
        self.update_config_for_root(self.currentRoot, {"last_collection": collectionName})

        # Ask Backend for data
        if self.backend:
            self.backend.collectionChanged() # Legacy hook
            # Assuming the backend has a createItems() that returned widgets. 
            # We need to adapt that logic to return DATA, not WIDGETS.
            # *Assumption*: You will refactor the Backends to return a list of dicts 
            # instead of creating QListWidgetItems directly. 
            assets = self.backend.getAssetsData() 
            self.assetsLoadedSignal.emit(assets)
            
            # Start thumbnail generation
            self._startThumbnailGeneration(assets)

    def setFilterText(self, text):
        """
        Filters the current assets. 
        Note: In a pure model, we might re-emit assetsLoadedSignal with a filtered list.
        Or, we keep it simple and let the View handle visual filtering if the dataset is small.
        """
        # For large datasets, filter here and emit new list.
        # For small datasets (under 500 items), View-side filtering is smoother.
        pass 

    def setFavoritesOnly(self, enabled):
        """Updates internal filter state."""
        # Logic to filter self.current_assets based on "tags" in config
        pass

    def setTagFilter(self, enabled):
        pass

    def setCategory(self, category_path):
        """Called when tree selection changes."""
        if self.backend:
            # Pass to backend logic if specific filtering is required
            pass

    # ----------------------------------------------------------------------
    # Import / Action Logic
    # ----------------------------------------------------------------------

    def importAsset(self, asset_data):
        """
        Delegates the import logic to the loaded backend.
        """
        if not self.backend:
            self.errorSignal.emit("No active backend loaded.")
            return

        try:
            self.statusSignal.emit(f"Importing {asset_data.get('name', 'asset')}...")
            
            # Legacy code called 'importAsset(item)'. 
            # We pass data now, so backends might need slight adjustment.
            result = self.backend.importAssetData(asset_data) 
            
            self.statusSignal.emit("Import complete.")
            return result
        except Exception as e:
            self.errorSignal.emit(f"Import failed: {str(e)}")
            import traceback
            traceback.print_exc()

    def toggleFavorite(self, asset_id, is_favorite):
        """Updates the 'tags' in the configuration."""
        config = self.get_config_for_root(self.currentRoot)
        
        tags = config.get("tags", {})
        favorites = tags.get("favorite", [])

        if is_favorite:
            if asset_id not in favorites:
                favorites.append(asset_id)
        else:
            if asset_id in favorites:
                favorites.remove(asset_id)
        
        tags["favorite"] = favorites
        config["tags"] = tags
        
        self.update_config_for_root(self.currentRoot, config)

    # ----------------------------------------------------------------------
    # Internal Mechanics (Backend/Thumbnail)
    # ----------------------------------------------------------------------

    def _startThumbnailGeneration(self, assets):
        """Queue up threads to load images."""
        self.threadPool.clear()
        for asset in assets:
            task = LoadThumbnailRunnable(asset, self._onThumbnailLoaded)
            self.threadPool.start(task)

    def _onThumbnailLoaded(self, asset_id, pixmap):
        """Callback from worker thread."""
        self.thumbnailLoadedSignal.emit(asset_id, pixmap)

    def _loadBackendStrategy(self, class_name):
        """
        Dynamic plugin loader. 
        Replaces 'getClassFromFile' from legacy code.
        """
        
        # Get paths from env
        paths = utils.envListValues("OLI_GALLERY_MODELS_PATH")
        
        found_class = None
        
        for path in paths:
            potential_file = os.path.join(path, class_name + ".py")
            if os.path.exists(potential_file):
                try:
                    # Logic to import module dynamically
                    # We add path to sys temporarily or use importlib.spec_from_file_location
                    with utils.add_path(path):
                        module = importlib.import_module(class_name)
                        reload(module)
                        found_class = getattr(module, class_name)
                        break
                except Exception as e:
                    print(f"Failed to load backend {class_name}: {e}")

        if found_class:
            # Initialize the backend, passing self (The Model) as parent/interface
            self.backend = found_class(self)
        else:
            self.errorSignal.emit(f"Backend '{class_name}' not found.")
            # Fallback to default if needed