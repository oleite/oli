# -*- coding: utf-8 -*-

import importlib
import os
import time
import webbrowser
from imp import reload

import hou
import toolutils
from PySide2 import QtGui, QtWidgets, QtCore
import json

import GalleryModels
import galleryUi
import lookdev
import utils


iconsPath = hou.getenv("OLI_ICONS")


def openGallery(attemptSplit=True):
    """
    Opens the oli Gallery

    :parm attemptSplit: Whether to attempt to split the SceneViewer instead of opening a new window.
    :return: Pane tab
    """
    desktop = hou.ui.curDesktop()

    if attemptSplit:
        sceneViewer = toolutils.sceneViewer()
        if sceneViewer:
            pane = sceneViewer.pane().splitVertically()
            tab = pane.currentTab().setType(hou.paneTabType.PythonPanel)
            tab.showToolbar(False)
            tab.setActiveInterface(hou.pypanel.interfaceByName("oli::gallery"))
            return tab

    panel = desktop.createFloatingPanel(hou.paneTabType.PythonPanel, python_panel_interface="oli::gallery")
    panel.setName("oli Gallery")
    return panel


class LoadItemThumbnail(QtCore.QRunnable):
    def __init__(self, item, callback=None):
        self.item = item
        self.callback = callback
        super(LoadItemThumbnail, self).__init__()

    def run(self):
        time.sleep(0.01)  # For some reason QPixmap hangs houdini if this line isn't present (?????)
        if not self.item:
            return

        thumbnail_path = self.item.data(QtCore.Qt.UserRole)["thumbnail_path"]
        thumbnail_path = hou.text.expandString(thumbnail_path)

        if not thumbnail_path or not os.path.exists(thumbnail_path):
            return

        self.item.setIcon(QtGui.QIcon(thumbnail_path))

        if self.callback:
            self.callback()


class AssetListWidget(object):
    def __init__(self, target, droppedOut, droppedIn):
        self.target = target
        self.droppedOut = droppedOut
        self.droppedIn = droppedIn
        self.target._drag = False
        self.target.mouseMoveEvent = self.mouseMoveEvent
        self.target.startDrag = self.startDrag
        self.target.mimeTypes = self.mimeTypes
        self.target.dropEvent = self.dropEvent

    def mouseMoveEvent(self, e):        
        super(QtWidgets.QListWidget, self.target).mouseMoveEvent(e)
        if self.target._drag:
            self.droppedOut(e)
            self.target._drag = False

    def startDrag(self, actions):        
        super(QtWidgets.QListWidget, self.target).startDrag(actions)
        self.target._drag = True

    def mimeTypes(self):
        return ['text/plain']

    def dropEvent(self, e):        
        self.droppedIn(e)


class Gallery(QtWidgets.QWidget):

    def __init__(self, parent=None, pane_tab=None):
        super(Gallery, self).__init__(parent)

        self.paneTab = pane_tab
        self.paneTabPwd = pane_tab.pwd()

        self.Model = None

        self.currentRootModel = None
        self.collectionPath = ""
        reload(galleryUi)
        self.ui = galleryUi.Ui_AssetGallery()

        self.ui.setupUi(self)

        self.ui.assetList.setDragEnabled(True)
        self.ui.assetList.setDragDropMode(QtWidgets.QAbstractItemView.DragDrop)

        self.customAssetListWidget = AssetListWidget(self.ui.assetList, self.droppedOut, self.droppedIn)

        self.LoadItemThumbnail = LoadItemThumbnail
        self.thumbnailLoadedCount = 0

        self.color = hou.Color()
        self.applyStyles()

        self.threadPool = QtCore.QThreadPool()

        self.defaultThumbIcon = QtGui.QIcon(iconsPath + "/default_thumbnail.png")
        self.ui.toggleListView.setIcon(QtGui.QIcon(iconsPath + "/list_view.png"))
        self.ui.toggleListView.setIconSize(QtCore.QSize(30, 30))

        self.preferencesFile = hou.getenv("HOUDINI_USER_PREF_DIR") + "/oli_gallery_prefs.json"
        self.defaultPreferencesFile = str(hou.getenv("OLI_ROOT")) + "/oli_gallery_prefs.json"

        # Ensure valid Preferences File
        if os.path.isfile(self.preferencesFile):
            with open(self.preferencesFile, "r") as f:
                try:
                    json.load(f)
                except ValueError:
                    hou.ui.displayMessage("Invalid Preferences File",
                                          help=self.preferencesFile,
                                          severity=hou.severityType.Error,
                                          title="Asset Gallery"
                                          )
                    if hou.ui.displayConfirmation("Resetar arquivo de preferências?", title="Asset Gallery"):
                        with open(self.preferencesFile, "w") as f2:
                            json.dump({}, f2, sort_keys=True)
                    else:
                        self.setMessage('<span class="error"><b>Invalid Preferences File</b> <br><br>{}</span>'.format(self.preferencesFile))
                        self.setDisabled(True)
                        return

        self.loadMessage()

        self.ui.thumbnailSizeSlider.setValue(200)
        self.updateRootBox()

        self.ui.assetList.installEventFilter(self)

        # If still no folders, load the defaults
        if self.ui.foldersTable.rowCount() == 0:
            self.ui.tabWidget.setCurrentIndex(1)
            self.loadDefaultFolders()
            self.ui.tabWidget.setCurrentIndex(0)

    def getModel(self, modelName=None):
        """
        Gets the current Asset Gallery Model according to the model_name.
        If not specified, uses the Model that was specified in the Folder Management tab matching the current root.

        :param modelName:
        :return:
        """
        warning = None

        if not modelName:
            for i in range(self.ui.foldersTable.rowCount()):
                if self.ui.foldersTable.item(i, 0):
                    i_root = self.ui.foldersTable.item(i, 0).text()
                    if self.ui.foldersTable.item(i, 1):
                        i_model = self.ui.foldersTable.item(i, 1).text()
                        if i_root == self.ui.rootBox.currentText():
                            modelName = i_model
                            break

        defaultModelName = "DefaultModel"

        if not modelName:
            modelName = defaultModelName

        current_model_name = type(self.Model).__name__

        if current_model_name == modelName:
            Model = self.Model
            return Model

        try:
            modelModule = importlib.import_module(".GalleryModels." + modelName, package="oli")
        except ImportError:
            warning = '<span class="error">\"{}\" model not found</span>'.format(modelName)
            modelName = defaultModelName
            modelModule = importlib.import_module(".GalleryModels." + modelName, package="oli")

        reload(modelModule)
        Model = getattr(modelModule, modelName)(self)

        if warning:
            self.setMessage(warning)

        self.Model = Model
        return self.Model

    @staticmethod
    def generateItemTooltip(itemData):
        """
        Generates the tooltip XML string to be used for each item in the Asset Gallery.

        :param itemData: Dict of keys and respective values to be used.
        :return: String with XML tags.
        """

        msg = "<br>"
        itemDataKeys = sorted(itemData)
        for key in itemDataKeys:
            keyname = key.replace("_", " ")
            msg += keyname[0].upper() + keyname[1:]
            value = itemData[key]

            style = ""
            if value:
                value = value.encode('utf-8')
                style = "font-weight:bold;"
            else:
                style += "color:red"

            msg += ":<br><span style=\"{}\">{}</span><br><br>".format(style, value)
        return msg.strip("<br>")

    @staticmethod
    def getModelsNames():
        """
        Retrieves the available Gallery Models inside the GalleryModels package.

        :return: List of strings of the module names
        """
        models = []
        for name in os.listdir(GalleryModels.__path__[0]):
            name = name.split(".")[0]
            if name.startswith("__") or name in models:
                continue
            models.append(name)
        return sorted(models)

    def droppedOut(self, event):
        """
        Called when the user drags and drops an assetList item outside

        :param event: QtCore.QEvent
        :return: None
        """
        Model = self.getModel()
        Model.droppedOut(event)

    def droppedIn(self, event):
        """
        Called when the user drops something into the assetList

        :param event: QtCore.QEvent
        :return:
        """
        Model = self.getModel()
        Model.droppedIn(event)

    def eventFilter(self, source, event):
        """
        Monitors and handles incoming events
        """

        self.paneTabPwdUpdater()

        # ContextMenu
        if event.type() == QtCore.QEvent.ContextMenu:
            if source is self.ui.assetList:
                itemList = self.ui.assetList.selectedItems()
                return self.getModel().assetListContextMenu(event, itemList)

        return False

    def paneTabPwdUpdater(self):
        """
        Callback to be on every tick, checking if the Pane Tab pwd() has changed.
        If so, calls the Model.pwdChanged(old, new) method.

        :return: Whether to stop the callback
        """
        try:
            if self.paneTab.pwd() == self.paneTabPwd:
                return False

            Model = self.getModel()
            Model.pwdChanged(self.paneTabPwd, self.paneTab.pwd())

            self.paneTabPwd = self.paneTab.pwd()
            return False
        except:
            return True

    def spawnFoldersTableContextMenu(self):
        """
        Context menu for self.ui.foldersTable

        :return: None
        """

        itemList = self.ui.foldersTable.selectedItems()
        menu = hou.qt.Menu()

        #  If clicked without selecting any items
        if itemList:
            # Submenu: Change model to
            menu_model = menu.addMenu("Change model to")
            for model in self.getModelsNames():
                action_model = QtWidgets.QAction(model, self)
                action_model.setProperty("action", "change_model")
                action_model.setProperty("model", model)
                menu_model.addAction(action_model)

            # Separator
            menu.addSeparator()

            # Menu Item: Remove
            action_remove = QtWidgets.QAction("Remove", self)
            action_remove.setProperty("action", "remove")
            menu.addAction(action_remove)

        else:
            # Menu Item: Add Item
            action_add_item = QtWidgets.QAction("Add Item", self)
            action_add_item.setProperty("action", "add_item")
            menu.addAction(action_add_item)

            # Menu Item: Open Preferences File
            action_open_prefs_file = QtWidgets.QAction("Open Preferences File", self)
            action_open_prefs_file.setProperty("action", "open_prefs_file")
            menu.addAction(action_open_prefs_file)

            # Separator
            menu.addSeparator()

            # Menu Item: Reset to Defaults
            action_reset_to_defaults = QtWidgets.QAction("Reset to Defaults", self)
            action_reset_to_defaults.setProperty("action", "reset_to_defaults")
            menu.addAction(action_reset_to_defaults)

        rows = []
        for i in itemList:
            row = i.row()
            if row not in rows:
                rows.append(row)

        # Open Menu
        menu_exec = menu.exec_(QtGui.QCursor.pos())
        if not menu_exec:
            return False

        # Run callbacks based on QActions "action" properties
        action = menu_exec.property("action")
        if action == "add_item":
            self.ui.foldersTable.insertRow(self.ui.foldersTable.rowCount())

        elif action == "open_prefs_file":
            webbrowser.open(self.preferencesFile)

        elif action == "reset_to_defaults":
            if hou.ui.displayConfirmation("Reset to defaults?",
                                          help="Every custom config in the Folder Management tab will be lost."):
                self.loadDefaultFolders()

        elif action == "remove":
            # Reverse sort rows indexes
            rows = sorted(rows, reverse=True)

            # Delete rows
            for row in rows:
                self.ui.foldersTable.removeRow(row)

        elif action == "change_model":
            model_name = menu_exec.property("model")
            for row in rows:
                item = self.ui.foldersTable.item(row, 1)
                if not item:
                    self.ui.foldersTable.blockSignals(True)
                    item = self.ui.foldersTable.setItem(row, 2, QtWidgets.QTableWidgetItem(""))
                    self.ui.foldersTable.blockSignals(False)
                    item = self.ui.foldersTable.item(row, 1)

                item.setText(model_name)

        self.saveState()
        return

    def updateRootBox(self):
        """
        Updates the self.ui.rootBox content to match the folders specified in the Folder Management tab

        :return: None
        """
        self.loadStateFolders()

        self.ui.rootBox.clear()
        self.ui.rootBox.blockSignals(True)

        self.ui.rootBox.setIconSize(QtCore.QSize(30, 30))

        for row in range(self.ui.foldersTable.rowCount()):
            root = self.ui.foldersTable.item(row, 0).text()
            root = root
            self.ui.rootBox.addItem(root)

            # Add Model Icons
            modelIconPath = iconsPath + "/" + self.ui.foldersTable.item(row, 1).text() + "*"
            modelIconPath = utils.patternMatchFile(hou.text.expandString(modelIconPath))
            if os.path.exists(modelIconPath):
                self.ui.rootBox.setItemIcon(self.ui.rootBox.count()-1, QtGui.QIcon(modelIconPath))

            # Add Colors to the rooBox
            with open(self.preferencesFile, "r") as f:
                try:
                    data = json.load(f)
                except ValueError:
                    pass
            try:
                rgb = data["folders"][root]["config"]["color"]
                self.ui.rootBox.setItemData(row, QtGui.QColor(rgb[0], rgb[1], rgb[2]), QtCore.Qt.ForegroundRole)
            except KeyError:
                pass

        self.loadStateRoot()
        self.ui.rootBox.blockSignals(False)

    def rootChanged(self):
        """
        Called when the current self.ui.rootBox content has changed

        :return: None
        """
        self.setMessage("")
        self.loadState()
        self.saveState()

    def updateParms(self, block_signals=False):
        """
        Updates the collectionBox's contents.
        Called when a critical parameter changes (eg.: root)
        """
        self.ui.collectionsBox.blockSignals(True)  # Prevent .clear() from calling collectionChanged() slot
        self.ui.collectionsBox.clear()
        if not block_signals:
            self.ui.collectionsBox.blockSignals(False)

        self.ui.collectionsBox.setDisabled(False)

        Model = self.getModel()
        collections_list = Model.collectionsList()
        if not collections_list:
            collections_list = [""]
            self.ui.collectionsBox.setDisabled(True)
            self.setMessage("No collection found")
        self.ui.collectionsBox.addItems(sorted(collections_list))

    def collectionChanged(self, save_state=True):
        """
        Recreates the gallery's items based on the current collectionsBox value.
        Called when the collectionsBox value changes.
        """
        if save_state:
            config = self.getCurModelConfig()
            config["last_collection"] = self.ui.collectionsBox.currentText()
            self.setCurModelConfig(config)

        Model = self.getModel()
        Model.collectionChanged()

    def filterItems(self):
        """
        Handles filtering the assetList's items based on search strings and toggled filters.
        Called when a filter gets changed.

        :return: None
        """

        Model = self.getModel()

        text = self.ui.searchBar.text().strip()
        for row in range(self.ui.assetList.count()):
            item = self.ui.assetList.item(row)
            Model.filterItem(item, text)

    def createItems(self):
        """
        Creates each item inside of the assetList from scratch.

        :return: List of QListWidgetItems
        """

        Model = self.getModel()
        return Model.createItems()

    def format_pattern(self, asset_name, pattern, remappings=None):
        """
        Formats the patterns used for preferences' file paths, remapping special strings.
        Accepts wildcard pattern at the last folder level (Eg.: C:/assets/example/*.jpg), returning the
        first found item.

        :param asset_name: Name of the asset for which __ASSET__ will be replaced by
        :param pattern: Pattern to be remapped
        :param remappings: Optional custom remappings dict
        :return: Formatted path
        """

        path = os.path.normpath(pattern).replace("\\", "/")
        if remappings is None:
            remappings = {
                "__ROOT__": self.ui.rootBox.currentText(),
                "__COLLECTION__": self.ui.collectionsBox.currentText(),
                "__ASSET__": asset_name,
            }
        for key in remappings:
            key = hou.text.expandString(key)
            path = path.replace(key, remappings[key])

        path = utils.patternMatchFile(path)
        return path

    def thumbnailResize(self, val, ListMode=False):
        """
        Properly resizes the thumbnails by modifying the assetList Icon Size and Grid Size.

        :param val: Size in pixels
        :param ListMode: Whether the assetList's viewMode is in ListMode
        :return: None
        """

        font_h = 30
        # if self.ui.assetList.count() > 0:
        #     font = self.ui.assetList.item(0).font()
        #     if ListMode:
        #         font.setPixelSize(20)
        #         font.setBold(True)
        #     font_h = QtGui.QFontMetricsF(font).height()

        if ListMode:
            self.ui.assetList.setIconSize(QtCore.QSize(font_h, font_h))
            self.ui.assetList.setGridSize(QtCore.QSize(0, font_h))
        else:
            self.ui.assetList.setIconSize(QtCore.QSize(val - 3, val))
            self.ui.assetList.setGridSize(QtCore.QSize(val, val + (font_h * 2)))

    def toggleListView(self, ListMode):
        """
        Toggles in or out of the ListMode view for the assetList

        :param ListMode: Whether to use ListMode
        :return: None
        """
        self.ui.toggleListView.blockSignals(True)

        if ListMode:
            self.ui.toggleListView.setChecked(True)
            self.ui.assetList.setViewMode(QtWidgets.QListView.ListMode)
            self.thumbnailResize(0, ListMode=True)
            self.ui.thumbnailSizeSlider.setEnabled(False)
        else:
            self.ui.toggleListView.setChecked(False)
            self.ui.assetList.setProperty("viewMode", "IconMode")
            self.ui.assetList.setViewMode(QtWidgets.QListView.IconMode)
            self.thumbnailResize(self.ui.thumbnailSizeSlider.value())
            self.ui.thumbnailSizeSlider.setEnabled(True)

        self.ui.toggleListView.blockSignals(False)
        self.saveState()

    def import_asset(self, item):
        """
        Imports the asset according to the Model instructions.
        :param item: The assetList Item
        """

        return self.getModel().importAsset(item)

    def importSelectedAssets(self):
        nodes = []
        for item in self.ui.assetList.selectedItems():
            node = self.import_asset(item)
            if node:
                nodes.append(node)
        return nodes

    def import_selected_assets_to_ol_instancer(self, node):
        reload(lookdev)
        for item in self.ui.assetList.selectedItems():
            itemData = item.data(QtCore.Qt.UserRole)
            filepath = self.collectionPath + "/" + itemData["asset_name"]

            lookdev.add_to_ol_instancer(node, filepath)

    def import_selected_assets_to_lop_layout(self):
        for item in self.ui.assetList.selectedItems():
            itemData = item.data(QtCore.Qt.UserRole)
            filepath = self.collectionPath + "/" + itemData["asset_name"]

            reload(lookdev)
            uuid_list = lookdev.add_to_layout_asset_gallery(filepath)
            for uuid in uuid_list:
                lookdev.add_to_aws(uuid)

    def thumbnailLoaded(self):
        """
        Called when a thumbnail gets loaded.

        :return: None
        """

        self.thumbnailLoadedCount += 1
        if self.thumbnailLoadedCount >= self.ui.assetList.count():
            time.sleep(.1)
            self.ui.assetList.update()
            self.thumbnailLoadedCount = 0

    def applyStyles(self):
        """
        Applies custom stylesheets to the self.ui widgets.

        :return: None
        """
        rgb = utils.houColorTo255(self.color)

        self.ui.toggleListView.setStyleSheet("""
            QToolButton {
                border: 0;
                background: #333;
                padding: 5px 15px;
            }
            QToolButton::hover {
                background: #555
            }
            QToolButton:checked {
                background: #222;
            }
        """)

        self.ui.assetList.setStyleSheet("""
            QListWidget::item:selected {{
                background-color: rgba({r},{g},{b},.2);
                border: 0;
            }}
            QToolTip {{
                padding: 6px;
            }}
            QListWidget[ListMode="true"] {{
                color: red;
                background-color: red;
            }}
        """.format(r=rgb[0], g=rgb[1], b=rgb[2]))

        self.ui.thumbnailSizeSlider.setStyleSheet("""
            QSlider::groove {{
                padding: 2px 0 2px 0;
                margin: 2px 0;
            }}
            QSlider::handle {{
                width: 50px;
            }}
            QSlider::add-page {{
                /* */
            }}

            QSlider::sub-page {{
                background: rgba({r},{g},{b},.3);
            }}

            QSlider::handle:disabled {{
                background: #535454;
            }}
            QSlider::groove:disabled {{
                background: #222;
            }}
            QSlider::sub-page:disabled {{
                background: #535454;
            }}
        """.format(r=rgb[0], g=rgb[1], b=rgb[2]))

        self.ui.messageBrowser.document().setDefaultStyleSheet("""
            body {
                background: black;
            }
            a {
                color: #77f;
            }
            .error {
                color: red;
            }
        """)

        self.ui.rootBox.setStyleSheet("""
                    
        """)

    def saveState(self, e=None, preferencesFile=None):
        """
        Saves the current state to the preferencesFile.
        If not specified, uses self.preferencesFile.

        :return: None
        """
        if not preferencesFile:
            preferencesFile = self.preferencesFile

        if os.path.isfile(preferencesFile):
            with open(preferencesFile, "r") as f:
                try:
                    data = json.load(f)
                except:
                    return False
        else:
            data = {}

        root = self.ui.rootBox.currentText()
        data["last_root"] = root

        data["thumbnail_size"] = self.ui.thumbnailSizeSlider.value()
        data["list_mode"] = self.ui.assetList.viewMode() == QtWidgets.QListView.ListMode

        data["folders"] = {}
        for i in range(self.ui.foldersTable.rowCount()):
            if self.ui.foldersTable.item(i, 0):
                i_root = self.ui.foldersTable.item(i, 0).text()
                data["folders"].setdefault(i_root, {})

                if self.ui.foldersTable.item(i, 1):
                    data["folders"][i_root]["model"] = self.ui.foldersTable.item(i, 1).text()

                config = {}
                if self.ui.foldersTable.item(i, 2):
                    text = self.ui.foldersTable.item(i, 2).text()
                    try:
                        config = json.loads(text)
                    except ValueError:
                        config = {}
                data["folders"][i_root]["config"] = config

        with open(preferencesFile, "w") as f:
            json.dump(data, f, indent=4, sort_keys=True)

    def loadState(self, preferencesFile=None):
        """
        Loads the last state according to the preferencesFile, updating the current "collection", "thumbnail_size" and
        "list_mode".
        If not specified, uses self.preferencesFile.

        :param preferencesFile: The .json file path containing the preferences to be loaded
        :return: None
        """
        if not preferencesFile:
            preferencesFile = self.preferencesFile

        if os.path.isfile(preferencesFile):
            with open(preferencesFile, "r") as f:
                try:
                    data = json.load(f)
                except ValueError:
                    return False
        else:
            self.updateParms()
            return False

        self.ui.collectionsBox.blockSignals(True)
        self.updateParms(block_signals=True)

        if "folders" in data:
            root = self.ui.rootBox.currentText()
            if root in data["folders"] and "config" in data["folders"][root]:
                if "last_collection" in data["folders"][root]["config"]:
                    self.ui.collectionsBox.setCurrentText(data["folders"][root]["config"]["last_collection"])

        if "thumbnail_size" in data:
            self.ui.thumbnailSizeSlider.setValue(data["thumbnail_size"])
        else:
            self.ui.thumbnailSizeSlider.setValue(200)

        if "list_mode" in data:
            self.toggleListView(data["list_mode"])

        self.collectionChanged(save_state=False)
        self.ui.collectionsBox.blockSignals(False)

    def loadStateRoot(self, preferencesFile=None):
        """
        Loads the last_root in the self.ui.rootBox according to the preferencesFile.
        If not specified, uses self.preferencesFile.

        :param preferencesFile: The .json file path containing the preferences with ["last_root"] to be loaded
        :return: None
        """

        if not preferencesFile:
            preferencesFile = self.preferencesFile

        if os.path.isfile(preferencesFile):
            with open(preferencesFile, "r") as f:
                try:
                    data = json.load(f)
                except ValueError:
                    return False
        else:
            self.updateParms()
            return False

        self.ui.collectionsBox.blockSignals(True)

        if "last_root" in data:
            last_root = data["last_root"]
            if self.ui.rootBox.findText(last_root) != -1:
                self.ui.rootBox.setCurrentText(last_root)

        self.loadState()

    def loadStateFolders(self, preferencesFile=None):
        """
        Loads the folders in the Folder Management tab according to the preferencesFile.
        If not specified, uses self.preferencesFile.

        :param preferencesFile: The .json file path containing the preferences with ["folders"] to be loaded
        :return: None
        """

        if not preferencesFile:
            preferencesFile = self.preferencesFile

        if os.path.isfile(preferencesFile):
            with open(preferencesFile, "r") as f:
                try:
                    data = json.load(f)
                except ValueError:
                    return False
        else:
            self.updateParms()
            return False

        # ---------- Load Folders ----------

        self.ui.foldersTable.blockSignals(True)

        data.setdefault("folders", {})
        if len(data["folders"]) > 0:
            self.ui.foldersTable.setRowCount(0)
            for root in sorted(data["folders"]):
                row = self.ui.foldersTable.rowCount()
                self.ui.foldersTable.insertRow(row)
                self.ui.foldersTable.setItem(row, 0, QtWidgets.QTableWidgetItem(root))

                if "model" in data["folders"][root]:
                    self.ui.foldersTable.setItem(row, 1, QtWidgets.QTableWidgetItem(data["folders"][root]["model"]))
                if "config" in data["folders"][root]:
                    config = data["folders"][root]["config"]
                    if not isinstance(config, dict):
                        try:
                            config = json.loads(str(config))
                        except ValueError:
                            config = {}
                    self.ui.foldersTable.setItem(row, 2, QtWidgets.QTableWidgetItem(json.dumps(config, indent=4, sort_keys=True)))

        self.ui.foldersTable.blockSignals(False)

    def loadDefaultFolders(self):
        """
        Loads the default folders in the Folder Management tab according to the self.default_preferencesFile path.
        Warns if the self.default_preferencesFile wasn't found.

        :return: None
        """
        if not os.path.isfile(self.defaultPreferencesFile):
            hou.ui.displayMessage("Default preferences file not found",
                                  help=self.defaultPreferencesFile, severity=hou.severityType.Error)

        self.loadStateFolders(preferencesFile=self.defaultPreferencesFile)
        self.loadStateRoot(preferencesFile=self.defaultPreferencesFile)
        self.saveState()

    def tabChanged(self, tab_idx):
        """
        Gets called when the Asset Gallery Tab gets changed

        :param tab_idx: Index of the new tab
        :return: None
        """
        self.ui.rootBox.blockSignals(True)
        if tab_idx == 0:
            self.updateRootBox()
        self.ui.rootBox.blockSignals(False)

    def getMessage(self):
        """
        Retrieves the message currently displayed in the messageBrowser.

        :return: String
        """
        return self.ui.messageBrowser.text()

    def setMessage(self, message):
        """
        Sets a message to be displayed in the self.ui.messageBrowser.
        If empty, hides the messageBrowser.

        :param message: The message to be displayed
        :return: None
        """
        message = message.strip()
        if not message:
            self.ui.messageBrowser.hide()
            self.ui.messageBrowser.setText("")
            return False

        message = "<body>{}</body>".format(message)
        self.ui.messageBrowser.setText(message)

        lines = 1 + message.count("\n") + message.count("<br>")
        height = lines * 30
        self.ui.messageBrowser.setFixedHeight(height)
        self.ui.messageBrowser.show()

    def setTempMessage(self, message, duration=5):
        """

        :param message:
        :param duration:
        :return: None
        """
        def run():
            self.setMessage(message)
            utils.wait(duration)
            self.setMessage("")
        hou.ui.postEventCallback(run)

    def loadMessage(self, preferencesFile=None):
        """
        Loads the folders in the Folder Management tab according to the preferencesFile.
        If not specified, uses self.default_preferencesFile.

        :return: None
        """
        if not preferencesFile:
            preferencesFile = self.defaultPreferencesFile
        if not os.path.isfile(preferencesFile):
            return

        with open(preferencesFile, "r") as f:
            data = json.load(f)
        if "message" in data:
            self.setMessage(data["message"])

    def getCurModelConfig(self):
        """
        Gets the foldersTable config data for the Model relative to the current root
        :return: The config Dict
        """
        root = self.ui.rootBox.currentText()
        for row in range(self.ui.foldersTable.rowCount()):
            if self.ui.foldersTable.item(row, 0).text() == root:
                config_item = self.ui.foldersTable.item(row, 2)
                text = config_item.text()
                if text:
                    data = json.loads(text)
                else:
                    data = {}
                return data

    def setCurModelConfig(self, data):
        """
        Sets the foldersTable config data for the Model relative to the current root
        :param data: The config Dict
        :return: None
        """
        root = self.ui.rootBox.currentText()
        for row in range(self.ui.foldersTable.rowCount()):
            if self.ui.foldersTable.item(row, 0).text() == root:
                config_item = self.ui.foldersTable.item(row, 2)
                config_item.setText(json.dumps(data, indent=4, sort_keys=True))
                self.saveState()
                return

    def updateCurModelConfig(self, newData):
        """

        :param newData:
        :return:
        """
        data = self.getCurModelConfig()
        data.update(newData)
        self.setCurModelConfig(data)

    def changeColor(self, color, alpha):
        self.color = color
        self.updateCurModelConfig({
            "color": utils.houColorTo255(color),
        })

        self.applyStyles()
