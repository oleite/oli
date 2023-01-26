# -*- coding: utf-8 -*-

import datetime
import importlib
import os
import sys
import time
import webbrowser
from imp import reload

import hou
import toolutils
import json

from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *

from . import galleryUi
from . import lookdev
from . import utils

reload(utils)

iconsPath = hou.getenv("OLI_ICONS")

ITEM_ID_ROLE = Qt.UserRole + 1
ITEM_THUMBNAIL_PIXMAP_ROLE = Qt.UserRole + 11
ITEM_BADGES_LIST_ROLE = Qt.UserRole + 12


def openGallery(attemptSplit=True, **kwargs):
    """
    Opens the oli Gallery

    :parm attemptSplit: Whether to attempt to split the SceneViewer instead of opening a new window.
    :return: Pane tab
    """
    desktop = hou.ui.curDesktop()

    hou.putenv("OLI_GALLERY_KWARGS", json.dumps(kwargs))

    galleryName = kwargs.get("galleryName", "oli Gallery")
    interface = "oli::gallery"

    if attemptSplit:
        sceneViewer = toolutils.sceneViewer()
        if sceneViewer:
            pane = sceneViewer.pane().splitVertically()
            tab = pane.currentTab().setType(hou.paneTabType.PythonPanel)
            tab.showToolbar(False)
            tab.setActiveInterface(hou.pypanel.interfaceByName(interface))
            tab.setName(galleryName)
            tab.setLabel(galleryName)
            return tab

    windowSize = hou.qt.mainWindow().size().toTuple()
    scaleFactor = 0.6
    position, scaledWindowSize = utils.scaleWindow(windowSize, scaleFactor)

    panel = desktop.createFloatingPanel(
        pane_tab_type=hou.paneTabType.PythonPanel,
        python_panel_interface=interface,
        position=position,
        size=scaledWindowSize
    )
    panel.setName(galleryName)

    for pane in panel.panes():
        pane.setShowPaneTabs(False)
        try:
            pane.showPaneTabsStow(False)
        except:
            pass

    return panel


def rectShrink(rect, x, y):
    shrink = QPoint(x, y)
    rect.setTopLeft(rect.topLeft() + shrink)
    rect.setBottomRight(rect.bottomRight() - shrink)
    return rect


def errHandler(msg_type, msg_log_context, msg_string):
    if "libpng" in msg_string:
        return
    print(msg_type, msg_log_context, msg_string)


# self.dialog.setWindowFlags(Qt.FramelessWindowHint)
# self.dialog.move(QCursor.pos())


class SignalEmitter(QObject):
    finished = Signal()
    error = Signal(str)
    progress = Signal(int)
    message = Signal(str)
    itemCreated = Signal(object)
    custom1 = Signal(object)
    custom2 = Signal(object)
    custom3 = Signal(object)
    custom4 = Signal(object)
    custom5 = Signal(object)


class Dialog(QDialog):
    def __init__(self, message, parent=None, title="Houdini", hold=0.1, pos=None, frameless=True, centralized=True):
        if parent:
            self.parent = parent
        else:
            self.parent = hou.qt.mainWindow()

        super(Dialog, self).__init__(self.parent)
        
        self.hold = hold
        if pos:
            self.pos = pos
        else:
            self.pos = QCursor.pos()
        
        self.setWindowTitle(title)
        self.setMinimumSize(250, 100)

        if frameless:
            self.setWindowFlags(Qt.FramelessWindowHint)

        self.centralized = centralized
        
        # add message to the dialog
        self.label = QLabel(message)
        self.label.setAlignment(Qt.AlignCenter)
        
        font = self.label.font()
        font.setBold(True)
        font.setPixelSize(font.pixelSize() * 1.5)
        
        self.label.setFont(font)

        layout = QVBoxLayout()
        layout.addWidget(self.label)
        self.setLayout(layout)

        self.setStyleSheet("""
            QDialog {
                border-left: 5px solid cyan;
                border-radius: 5px;
            }
        """)

        # Add a drop shadow to the dialog
        self.shadow = QGraphicsDropShadowEffect(self)
        self.shadow.setBlurRadius(100)
        self.shadow.setOffset(10, 30)
        self.shadow.setColor(QColor(0, 10, 10, 150))
        self.setGraphicsEffect(self.shadow)

        self.centralize()

    def centralize(self):
        self.adjustSize()

        if self.centralized:
            self.move(self.pos - QPoint(self.width() / 2, self.height() / 2))
        else:
            self.move(self.pos)

    def setMessage(self, message):
        self.label.setText(message)
        self.centralize()

    def addMessage(self, message):
        self.setMessage(self.label.text() + "\n\n" + message)

    def __enter__(self):
        # Show the dialog when entering the with block
        self.show()
        utils.wait(.01)
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        # Close the dialog when exiting the with block
        utils.wait(self.hold)
        self.close()



class MyDelegate(QStyledItemDelegate):
    def __init__(self, Gallery):
        super(MyDelegate, self).__init__()

        self.Gallery = Gallery

        size = 25
        self.iconSize = QSize(size, size)
        self.pad = QPoint(int(size / 2), int(size / 2))

        self.badgeSize = QSize(size, size)

    def favIconRect(self, rect):
        size = rect.size()
        rect.setSize(QSize(self.iconSize.width(), self.iconSize.height()))
        rect.translate(size.width()-self.iconSize.width()-self.pad.x(), self.pad.y())
        return rect

    def favIconBoundsRect(self, rect):
        size = rect.size()
        new = QRect(rect)
        padx = self.pad.x() * 2
        pady = self.pad.y() * 2
        new.setSize(QSize(self.iconSize.width() + padx, self.iconSize.height() + pady))
        new.translate(size.width() - self.iconSize.width() - padx, 0)
        return new

    def editorEvent(self, event, model, option, index):
        if event.type() == QEvent.MouseButtonRelease:
            if self.favIconBoundsRect(rectShrink(option.rect, 5, 5)).contains(event.pos()):
                self.Gallery.toggledFavorite(index.row())
                return True
        return False

    def startDrag(self):
        return

    def paint(self, painter, option, index):
        data = index.data(Qt.UserRole)
        tags = data.get("tags", [])
        item = self.Gallery.ui.assetList.item(index.row())

        mouseOver = option.state & QStyle.State_MouseOver
        selected = item.isSelected()

        # SHRINK RECT
        option.rect = rectShrink(option.rect, 5, 5)

        bgPath = QPainterPath()
        bgPath.addRoundedRect(option.rect, 5, 5)

        bgColor = QColor("#252525")
        bgColor2 = QColor("#091A2D")
        galColor = hou.qt.toQColor(self.Gallery.color)

        grad = QLinearGradient(option.rect.topLeft(), option.rect.bottomLeft())
        grad.setColorAt(0, QColor(0, 0, 0, 0))
        grad.setColorAt(1, QColor(0, 0, 0, 100))

        if selected:
            painter.fillPath(bgPath, bgColor2)
            painter.fillPath(bgPath, grad)
        else:
            painter.fillPath(bgPath, bgColor)

        pixmap = item.data(ITEM_THUMBNAIL_PIXMAP_ROLE)
        if pixmap:
            size = option.rect.size()
            size.setHeight(size.height() - 40)

            pixmap = pixmap.scaled(size, Qt.KeepAspectRatio)
            pos = option.rect.topLeft()
            pos += QPoint((pixmap.width() - size.width())/-2, (pixmap.width() - pixmap.height())/2.0)
            painter.drawPixmap(pos, pixmap)

        # ============================================================
        # Badges

        if mouseOver or selected:
            pass
        else:
            painter.setOpacity(0.5)

        badgeList = item.data(ITEM_BADGES_LIST_ROLE)
        if badgeList:
            for idx, pixmap in enumerate(badgeList):
                maxSizePercentage = .2
                sizey = (option.rect.size().height() - 40) * min(1.0/len(badgeList), maxSizePercentage)
                pad = sizey / 4
                badgeRect = QRect(option.rect)
                badgeRect.setSize(QSize(sizey, sizey))
                badgeRect.translate(self.pad.x(), pad)
                badgeRect.translate(pad, sizey * idx)
                painter.drawPixmap(badgeRect, pixmap)

        painter.setOpacity(1)

        # ============================================================
        # MouseOver Gradient

        if mouseOver or selected:
            painter.fillPath(bgPath, grad)

        # ============================================================
        # Text

        font = hou.qt.mainWindow().font()
        painter.setPen(QColor("#ddd"))
        if mouseOver or selected:
            font.setBold(True)
        painter.setFont(font)
        flags = Qt.AlignBottom | Qt.AlignHCenter | Qt.TextWordWrap
        painter.drawText(rectShrink(option.rect, 5, 5), flags, item.data(0))

        # ============================================================
        # Favorite

        if tags and "favorite" in tags:
            pixmap = hou.qt.Icon("BUTTONS_favorites", self.iconSize.width(), self.iconSize.height()).pixmap(self.iconSize)
            painter.drawPixmap(self.favIconRect(option.rect), pixmap)
        elif mouseOver:
            pixmap = hou.qt.Icon("BUTTONS_not_favorites", self.iconSize.width(), self.iconSize.height()).pixmap(self.iconSize)
            painter.drawPixmap(self.favIconRect(option.rect), pixmap)




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
        super(QListWidget, self.target).mouseMoveEvent(e)
        if self.target._drag:
            self.droppedOut(e)
            self.target._drag = False

    def startDrag(self, actions):
        super(QListWidget, self.target).startDrag(actions)
        self.target._drag = True

    def mimeTypes(self):
        return ['text/plain']

    def dropEvent(self, e):
        self.droppedIn(e)


class LoadItemThumbnail(QRunnable):
    def __init__(self, item):
        self.item = item
        super(LoadItemThumbnail, self).__init__()

    def run(self):
        time.sleep(0.01)  # For some reason QPixmap hangs houdini if this line isn't present (?????)
        
        if not self.item:
            return
        try:
            thumbnail_path = self.item.data(Qt.UserRole).get("thumbnail_path")
            if not thumbnail_path:
                return

            thumbnail_path = hou.text.expandString(thumbnail_path)

            if not thumbnail_path or not os.path.exists(thumbnail_path):
                return

            pixmap = QPixmap(thumbnail_path).scaled(QSize(512, 512), Qt.KeepAspectRatio)
            self.item.setData(ITEM_THUMBNAIL_PIXMAP_ROLE, pixmap)

        except Exception as e:
            import traceback
            traceback.print_exc()
            return

class Gallery(QWidget):
    def __init__(self, parent=None, paneTab=None, **kwargs):
        super(Gallery, self).__init__(parent)
        qInstallMessageHandler(errHandler)

        self.galleryName = kwargs.get("galleryName", "oli Gallery")

        self.paneTab = paneTab
        self.paneTabPwd = paneTab.pwd() if paneTab else None

        self.Model = None

        self.debug = hou.getenv("OLI_DEBUG", "0").lower() in ["true", "1", "t"]

        self.currentRootModel = None
        self.collectionPath = ""
        reload(galleryUi)
        self.ui = galleryUi.Ui_AssetGallery()

        self.ui.setupUi(self)

        self.ui.assetList.setDragEnabled(True)
        self.ui.assetList.setDragDropMode(QAbstractItemView.DragDrop)

        self.itemDelegate = MyDelegate(self)
        self.ui.assetList.setItemDelegate(self.itemDelegate)
        self.ui.assetList.setMouseTracking(True)

        self.customAssetListWidget = AssetListWidget(self.ui.assetList, self.droppedOut, self.droppedIn)

        self.LoadItemThumbnail = LoadItemThumbnail
        self.thumbnailLoadedCount = 0

        self.color = hou.Color()
        self.applyStyles()

        self.threadPool = QThreadPool()

        self.defaultThumbIcon = QIcon(iconsPath + "/default_thumbnail.png")
        self.ui.toggleListView.setIcon(QIcon(iconsPath + "/list_view.png"))
        self.ui.toggleListView.setIconSize(QSize(30, 30))

        self.ui.toggleFavorites.setIcon(hou.qt.Icon("BUTTONS_not_favorites", 30, 30))
        self.ui.toggleFavorites.setIconSize(QSize(30, 30))

        self.preferencesFile = kwargs.get("preferencesFile", hou.getenv("HOUDINI_USER_PREF_DIR") + "/oli_gallery_prefs.json")
        self.defaultPreferencesFile = kwargs.get("defaultPreferencesFile", str(hou.getenv("OLI_ROOT")) + "/oli_gallery_prefs.json")

        if not self.validatePreferences():
            return

        if kwargs.get("forceDefaultFolders"):
            self.loadDefaultFolders(append=False)
        elif kwargs.get("appendDefaultFolders"):
            self.loadStateFolders()
            self.loadDefaultFolders(append=True)

        self.loadMessage()

        if not self.debug:
            self.ui.toggleListView.hide()
            self.ui.applyTag.hide()

        return
        # Timer for periodic refresh
        self.periodicTimerDelay = 500
        self.periodicTimer = QTimer(self)
        self.periodicTimer.timeout.connect(self.periodicRefresh)
        self.toggleTimer(True)

    def toggleTimer(self, on):        
        if on:
            self.periodicTimer.start(self.periodicTimerDelay)
        else:
            self.periodicTimer.stop()

    def close(self):
        self.toggleTimer(False)

        return super().close()

    def periodicRefresh(self):
        self.getModel().periodicRefresh()
        self.filterItems()

    def validatePreferences(self):

        # ========================================
        # Ensure valid Default Preferences File

        def invalidDefaultMsg():
            hou.ui.displayMessage("Invalid Default Preferences file",
                        help=self.defaultPreferencesFile,
                        severity=hou.severityType.Error,
                        title="ol Gallery"
                        )
            self.setMessage('<span class="error"><b>Invalid Default Preferences File</b> <br><br>{}</span>'.format(self.defaultPreferencesFile))
            self.setDisabled(True)
            return False

        if not os.path.isfile(self.defaultPreferencesFile):
            invalidDefaultMsg()
            return False

        with open(self.defaultPreferencesFile, "r") as f:
            try:
                data = json.load(f)
            except ValueError:
                invalidDefaultMsg()
                return False

        # ========================================
        # Ensure valid Preferences File
        if os.path.isfile(self.preferencesFile):
            with open(self.preferencesFile, "r") as f:
                try:
                    data = json.load(f)
                except ValueError:
                    hou.ui.displayMessage("Invalid Preferences file",
                                          help=self.preferencesFile,
                                          severity=hou.severityType.Error,
                                          title="ol Gallery"
                                          )
                    if hou.ui.displayConfirmation("Reset preferences file to the defaults?", title="Gallery"):
                        data = {}
                        with open(self.preferencesFile, "w") as f2:
                            json.dump(data, f2, sort_keys=True)
                    else:
                        self.setMessage('<span class="error"><b>Invalid Preferences File</b> <br><br>{}</span>'.format(self.preferencesFile))
                        self.setDisabled(True)
                        return False

        return True

    def initialize(self):
        if not self.isEnabled():
            return

        self.ui.thumbnailSizeSlider.setValue(200)

        self.updateRootBox()

        self.ui.assetList.installEventFilter(self)

        # If still no folders, load the defaults
        if self.ui.foldersTable.rowCount() == 0:
            self.ui.tabWidget.setCurrentIndex(1)
            self.loadDefaultFolders()
            self.ui.tabWidget.setCurrentIndex(0)

        if self.debug:
            self.paneTab.showToolbar(True)

    def getModel(self, modelName=None):
        """
        Gets the current Asset Gallery Model according to the model_name.
        If not specified, uses the Model that was specified in the Folder Management tab matching the current root.

        :param modelName:
        :return:
        """
        warning = None

        # if self doesn't have an attribute Model, create it
        if not hasattr(self, "Model"):
            self.Model = None

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

        curModelName = type(self.Model).__name__
        if curModelName == modelName:
            Model = self.Model
            return Model

        del self.Model

        def getClassFromFile(parentModuleDir, className):
            if not os.path.exists(parentModuleDir):
                return

            with utils.add_path(parentModuleDir):
                availableModels = []
                for filename in os.listdir(parentModuleDir):
                    if "__" not in filename and os.path.isfile(parentModuleDir + "/" + filename):
                        availableModels.append(os.path.splitext(filename)[0])

                if className in availableModels:
                    module = importlib.import_module(className)
                    reload(module)
                    _class = getattr(module, className)
                    return _class

        galleryModelsPATHList = utils.envListValues("OLI_GALLERY_MODELS_PATH")
        for PATH in galleryModelsPATHList:
            modelClass = getClassFromFile(PATH, modelName)
            if not modelClass:
                continue

            self.Model = modelClass(self)
            return self.Model

        warning = '<span class="error">\"{}\" model not found</span>'.format(modelName)
        self.setMessage(warning)
        return self.getModel(defaultModelName)

    def getModelsData(self):
        modelFileList = []
        data = {}

        for PATH in utils.envListValues("OLI_GALLERY_MODELS_PATH"):

            for filename in os.listdir(PATH):
                filepath = utils.join(PATH, filename)
                # filename = filename.split(".")[0]
                if os.path.isfile(filepath) and not filename.startswith("__"):
                    name = os.path.splitext(os.path.basename(filepath))[0]
                    modelInfo = data.get(name, {})
                    modelInfo["file"] = filepath
                    data[name] = modelInfo

            iconsDir = utils.join(PATH, "icons")
            if os.path.isdir(iconsDir): 
                for filename in os.listdir(iconsDir):
                    filepath = utils.join(iconsDir, filename)
                    if os.path.isfile(filepath):
                        name = os.path.splitext(os.path.basename(filepath))[0]
                        if name in data:
                            data[name]["icon"] = filepath

        return data

    def getModelIconFromRoot(self, root):
        for row in range(self.ui.foldersTable.rowCount()):
            tableRoot = self.ui.foldersTable.item(row, 0).text()
            tableModel = self.ui.foldersTable.item(row, 1).text()

            if root == tableRoot:
                data = self.getModelsData()
                return data.get(tableModel, {}).get("icon", "")
        return ""

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
                if type(value) is str:
                    pass
                    # value = value.encode('utf-8')
                elif type(value) is list:
                    value = ", ".join(value)

                elif type(value) is dict:
                    value = json.dumps(value, indent=4).replace("}", "").replace("{", "")

                style = "font-weight:bold;"
            else:
                style += "color:red"

            msg += ":<br><span style=\"{}\">{}</span><br><br>".format(style, value)
        return msg.strip("<br>")

    def updateItemTooltip(self, item):
        itemData = item.data(Qt.UserRole)
        item.setToolTip(self.generateItemTooltip(itemData))

    def droppedOut(self, event):
        """
        Called when the user drags and drops an assetList item outside

        :param event: QEvent
        :return: None
        """
        Model = self.getModel()
        Model.droppedOut(event)

    def droppedIn(self, event):
        """
        Called when the user drops something into the assetList

        :param event: QEvent
        :return:
        """
        Model = self.getModel()
        Model.droppedIn(event)

    def eventFilter(self, source, event):
        """
        Monitors and handles incoming events
        """

        # ContextMenu
        if event.type() == QEvent.ContextMenu:
            if source is self.ui.assetList:
                itemList = self.ui.assetList.selectedItems()
                return self.getModel().assetListContextMenu(event, itemList)

        elif event.type() == QEvent.KeyPress:
            text = event.text().strip()
            # if text:
            #     self.ui.searchBar.setFocus(Qt.ShortcutFocusReason)
            #     self.ui.searchBar.setText(self.ui.searchBar.text() + text)

        # elif event.type() == QEvent.Paint:
        #     print(event)
        #     return True

        return False

    def onNodePathChanged(self, node):
        Model = self.getModel()
        Model.pwdChanged(self.paneTabPwd, self.paneTab.pwd())

        self.paneTabPwd = self.paneTab.pwd()

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
            for model in self.getModelsData():
                action_model = QAction(model, self)
                action_model.setProperty("action", "change_model")
                action_model.setProperty("model", model)
                menu_model.addAction(action_model)

            # Separator
            menu.addSeparator()

            # Menu Item: Remove
            action_remove = QAction("Remove", self)
            action_remove.setProperty("action", "remove")
            menu.addAction(action_remove)

        else:
            # Menu Item: Add Item
            action_add_item = QAction("Add Item", self)
            action_add_item.setProperty("action", "add_item")
            font = action_add_item.font()
            font.setBold(True)
            action_add_item.setFont(font)
            menu.addAction(action_add_item)

            # Menu Item: Open Preferences File
            action_open_prefs_file = QAction("Open Preferences File", self)
            action_open_prefs_file.setProperty("action", "open_prefs_file")
            menu.addAction(action_open_prefs_file)

            # Separator
            menu.addSeparator()

            # Menu Item: Reset to Defaults
            action_reset_to_defaults = QAction("Reset to Defaults", self)
            action_reset_to_defaults.setProperty("action", "reset_to_defaults")
            menu.addAction(action_reset_to_defaults)

        rows = []
        for i in itemList:
            row = i.row()
            if row not in rows:
                rows.append(row)

        # Open Menu
        menu_exec = menu.exec_(QCursor.pos())
        if not menu_exec:
            return False

        # Run callbacks based on QActions "action" properties
        action = menu_exec.property("action")
        if action == "add_item":
            self.addFolderDialog()

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
                    item = self.ui.foldersTable.setItem(row, 2, QTableWidgetItem(""))
                    self.ui.foldersTable.blockSignals(False)
                    item = self.ui.foldersTable.item(row, 1)

                item.setText(model_name)

        self.saveState()
        return

    def addFolderDialog(self):
        root = hou.ui.readInput("Root path/name")[1]

        modelChoices = sorted(self.getModelsData())
        defaultChoiceIdx = modelChoices.index("DefaultModel") if "DefaultModel" in modelChoices else 0
        modelChoiceIdx = hou.ui.selectFromList(modelChoices, default_choices=(defaultChoiceIdx, ), exclusive=True, title=self.galleryName)[0]

        model = modelChoices[modelChoiceIdx]

        self.ui.foldersTable.blockSignals(True)

        row = self.ui.foldersTable.rowCount()

        self.ui.foldersTable.insertRow(row)
        self.ui.foldersTable.setItem(row, 0, QTableWidgetItem(root))
        self.ui.foldersTable.setItem(row, 1, QTableWidgetItem(model))

        self.ui.foldersTable.blockSignals(False)

    def updateRootBox(self):
        """
        Updates the self.ui.rootBox content to match the folders specified in the Folder Management tab

        :return: None
        """
        self.loadStateFolders()

        self.ui.rootBox.clear()
        self.ui.rootBox.blockSignals(True)

        self.ui.rootBox.setIconSize(QSize(30, 30))

        for row in range(self.ui.foldersTable.rowCount()):
            root = self.ui.foldersTable.item(row, 0).text()
            root = root
            self.ui.rootBox.addItem(root)

            # Add Model Icon
            modelIconPath = self.getModelIconFromRoot(root)
            if os.path.exists(modelIconPath):
                self.ui.rootBox.setItemIcon(self.ui.rootBox.count()-1, QIcon(modelIconPath))

            # Add Colors to the rooBox
            with open(self.preferencesFile, "r") as f:
                try:
                    data = json.load(f)
                except ValueError:
                    pass
            try:
                rgb = data["folders"][root]["config"]["color"]
                self.ui.rootBox.setItemData(row, QColor(rgb[0], rgb[1], rgb[2]), Qt.ForegroundRole)
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
        self.ui.collectionsBox.setHidden(False)

        Model = self.getModel()
        collections_list = Model.collectionsList()
        if not collections_list:
            collections_list = [""]
            self.ui.collectionsBox.setDisabled(True)
            self.ui.collectionsBox.setHidden(True)

            # self.setMessage("No collection found")

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

        self.ui.assetList.sortItems()

    def createItems(self):
        """
        Creates each item inside of the assetList from scratch.

        :return: List of QListWidgetItems
        """
        if self.ui.rootBox.count() > 0:
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

        font_h = hou.qt.mainWindow().font().pixelSize()
        # if self.ui.assetList.count() > 0:
        #     font = self.ui.assetList.item(0).font()
        #     if ListMode:
        #         font.setPixelSize(20)
        #         font.setBold(True)
        #     font_h = QFontMetricsF(font).height()

        # # ========================
        # #        SNAP
        # listWidth = self.ui.assetList.width() - font_h
        # targetItemCount = listWidth / val
        # val = listWidth / targetItemCount

        if ListMode:
            self.ui.assetList.setIconSize(QSize(font_h, font_h))
            self.ui.assetList.setGridSize(QSize(0, font_h*2))
        else:
            self.ui.assetList.setIconSize(QSize(val, val))
            self.ui.assetList.setGridSize(QSize(val, val+font_h))

    def toggleListView(self, ListMode):
        """
        Toggles in or out of the ListMode view for the assetList

        :param ListMode: Whether to use ListMode
        :return: None
        """
        self.ui.toggleListView.blockSignals(True)

        if ListMode:
            self.ui.toggleListView.setChecked(True)
            self.ui.assetList.setViewMode(QListView.ListMode)
            self.thumbnailResize(0, ListMode=True)
            self.ui.thumbnailSizeSlider.setEnabled(False)
        else:
            self.ui.toggleListView.setChecked(False)
            self.ui.assetList.setProperty("viewMode", "IconMode")
            self.ui.assetList.setViewMode(QListView.IconMode)
            self.thumbnailResize(self.ui.thumbnailSizeSlider.value())
            self.ui.thumbnailSizeSlider.setEnabled(True)

        self.ui.toggleListView.blockSignals(False)
        self.saveState()

    def toggleFavoritesOnly(self, on):
        size = self.ui.toggleFavorites.iconSize()
        if on:
            self.ui.toggleFavorites.setIcon(hou.qt.Icon("BUTTONS_favorites", size.height(), size.width()))
        else:
            self.ui.toggleFavorites.setIcon(hou.qt.Icon("BUTTONS_not_favorites", size.height(), size.width()))

        self.filterItems()
        return

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
            itemData = item.data(Qt.UserRole)
            filepath = self.collectionPath + "/" + itemData["asset_name"]

            lookdev.add_to_ol_instancer(node, filepath)

    def import_selected_assets_to_lop_layout(self):
        for item in self.ui.assetList.selectedItems():
            itemData = item.data(Qt.UserRole)
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

        self.ui.assetListSplitter.setSizes([200, 1000])

        # self.ui.assetList.setUniformItemSizes(True)

        self.ui.foldersTable.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch);

        self.setStyleSheet("""
            Gallery {{
                background: #2e2e2e;
                border: 0;
            }}
                        
            libraryTab {{
                border: 0;
            }}
            
            QTabWidget::pane {{
            }}
            QTabWidget::tab-bar {{
                border: 0;
            }}
            
            QTabBar::tab {{
                border: 1px solid transparent;
                border-radius: 5px 5px 0 0;
                background: #2e2e2e;
                padding: 0px 30px;
            }}
            QTabBar::tab::selected {{
                background: #444;
                font-weight: bold;
            }}
            
            QLineEdit {{
                padding: 7px;
                border: 1px solid transparent;
                border-bottom: 3px;
                border-radius: 5px;
            }}
            QLineEdit::focus {{
                border-bottom: 3px solid rgba({r},{g},{b},.5);
            }}

            
            QComboBox {{
                border: 1px solid transparent;
                border-radius: 5px;
                background: #222;
            }}
            QComboBox::drop-down {{
                min-width: 50px;
            }}
            QComboBox::hover {{
                background: #2e2e2e;
            }}
            
            QToolButton {{
                border: 0;
                background: transparent;
                padding: 5px 10px;
                margin: 0;
                color: #999;
                font-weight: bold;
            }}
            QToolButton::hover {{
                background: #444;
            }}
            QToolButton:checked {{
                background: #2e2e2e;
            }}
            
            QLabel {{
                padding: 0;
                margin: 0;
            }}

            QTreeView {{
                background: #2e2e2e;
                font: 18px; 
            }}
            
            QTreeView::item {{
                padding: 3px;
            }}


        """.format(r=rgb[0], g=rgb[1], b=rgb[2]))

        self.ui.assetList.setStyleSheet("""
            QListWidget {{
                background-color: #222;
            }}
            
            QListWidget::item {{
                background-color: #252525;
                margin: 5px;
                border: 0px solid transparent;
                border-radius: 5px;
            }}
        
            QListWidget::item:selected {{
                background-color: rgba({r},{g},{b},.2);
                border: 1px;
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
                padding: 0;
                margin: 0;
            
                height: 20px;
                border: 1px solid transparent;
                border-radius: 5px;
                background: transparent;
            }}

            QSlider::handle {{
                padding: 0;
                margin: -1px 0;
                
                background: #4a4a4a;
                width: 50px;
                border: 1px solid transparent;
                border-radius: 5px;
            }}
            QSlider::handle:hover {{
                background: #666;
            }}

            QSlider::add-page {{
                padding: 0;
                margin: 1px 0;
            
                background: #222;
                border: 1px solid transparent;
                border-radius: 5px;
            }}

            QSlider::sub-page {{
                padding: 0;
                margin: 1px 0;
            
                background: #222;
                border: 1px solid transparent;
                border-radius: 5px;
            }}

            QSlider::handle:disabled {{
                background: #333;
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
        if root:
            data["last_root"] = root

        data["thumbnail_size"] = self.ui.thumbnailSizeSlider.value()
        data["list_mode"] = self.ui.assetList.viewMode() == QListView.ListMode

        data["folders"] = {}
        for i in range(self.ui.foldersTable.rowCount()):
            if self.ui.foldersTable.item(i, 0):
                i_root = self.ui.foldersTable.item(i, 0).text()
                i_root = utils.normpath(i_root)
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

        # self.ui.foldersTable.blockSignals(True)
        # self.loadStateFolders(preferencesFile)
        # self.ui.foldersTable.blockSignals(False)

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
                config = data["folders"][root]["config"]
                if "last_collection" in config:
                    self.ui.collectionsBox.setCurrentText(config["last_collection"])
                if "color" in config:
                    self.changeColor(utils.rgb255toHouColor(config["color"]))

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

    def loadStateFolders(self, preferencesFile=None, append=False):
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
                except ValueError as e:
                    return False
        else:
            self.updateParms()
            return False

        # ========================================
        # Gather roots to skip

        rootsToSkip = []

        if append:
            for i in range(self.ui.foldersTable.rowCount()):
                if self.ui.foldersTable.item(i, 0):
                    rootsToSkip.append(self.ui.foldersTable.item(i, 0).text())

        # ========================================
        # Load Folders
    
        self.ui.foldersTable.blockSignals(True)

        data.setdefault("folders", {})
        if len(data["folders"]) > 0:

            if not append:
                self.ui.foldersTable.setRowCount(0)

            for root in sorted(data["folders"]):
                if root in rootsToSkip:
                    continue

                row = self.ui.foldersTable.rowCount()
                self.ui.foldersTable.insertRow(row)
                self.ui.foldersTable.setItem(row, 0, QTableWidgetItem(root))

                if "model" in data["folders"][root]:
                    self.ui.foldersTable.setItem(row, 1, QTableWidgetItem(data["folders"][root]["model"]))
                if "config" in data["folders"][root]:
                    config = data["folders"][root]["config"]
                    if not isinstance(config, dict):
                        try:
                            config = json.loads(str(config))
                        except ValueError:
                            config = {}
                    self.ui.foldersTable.setItem(row, 2, QTableWidgetItem(json.dumps(config, indent=4, sort_keys=True)))

        self.ui.foldersTable.blockSignals(False)

    def loadDefaultFolders(self, append=False):
        """
        Loads the default folders in the Folder Management tab according to the self.default_preferencesFile path.
        Warns if the self.default_preferencesFile wasn't found.

        :return: None
        """
        if not os.path.isfile(self.defaultPreferencesFile):
            hou.ui.displayMessage("Default preferences file not found",
                                  help=self.defaultPreferencesFile, severity=hou.severityType.Error)

        self.loadStateFolders(preferencesFile=self.defaultPreferencesFile, append=append)
        self.loadStateRoot(preferencesFile=self.preferencesFile)
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

    def setErrorMessage(self, message):
        self.setMessage('<span class="error">' + message + '</span>')
        return True

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
                if config_item:
                    text = config_item.text()
                    if text:
                        return json.loads(text)                
                return {}

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

    def tagItem(self, tagName, item, on=True):
        """

        :return:
        """
        # =========================
        # Update current session's Item Data

        itemData = item.data(Qt.UserRole)
        tags = itemData.get("tags", [])

        if on:
            tags.append(tagName)
        elif tagName in tags:
            tags.remove(tagName)

        itemData["tags"] = tags
        item.setData(Qt.UserRole, itemData)
        self.updateItemTooltip(item)

        # =========================
        # Update Model Config State

        itemId = item.data(ITEM_ID_ROLE)

        data = self.getCurModelConfig()

        if on:
            if "tags" not in data:
                data["tags"] = {}
            if tagName not in data["tags"]:
                data["tags"][tagName] = []
            data["tags"][tagName].append(itemId)
            data["tags"][tagName] = list(dict.fromkeys(data["tags"][tagName]))
        else:
            if tagName in data.get("tags", {}):
                if itemId in data["tags"][tagName]:
                    data["tags"][tagName].remove(itemId)

        self.setCurModelConfig(data)

    def tagItemToggle(self, tagName, item, wholeSelection=True):
        on = True
        if tagName in self.getTags(item):
            on = False

        itemList = []
        if wholeSelection:
            itemList += self.ui.assetList.selectedItems()
        else:
            itemList.append(item)

        for _item in itemList:
            self.tagItem(tagName, _item, on)
            _item.setSelected(True)

    def getTags(self, item):
        return self.getTagsFromId(item.data(ITEM_ID_ROLE))

    def getTagsFromId(self, itemId):
        tags = []
        if itemId:
            data = self.getCurModelConfig()
            for tag, targets in data.get("tags", {}).items():
                if itemId in targets:
                    tags.append(tag)
        return tags

    def toggledFavorite(self, row):
        item = self.ui.assetList.item(row)
        self.tagItemToggle("favorite", item, wholeSelection=True)
        self.filterItems()

    def changeColor(self, color, alpha=1):
        self.color = color
        self.updateCurModelConfig({
            "color": utils.houColorTo255(color),
        })

        self.applyStyles()

    def treeNavItemChanged(self, item, oldItem):
        self.getModel().treeNavItemChanged(item, oldItem)

        # parent = item.parent()
        # if parent:
        #     for i in range(parent.childCount()):
        #         child = parent.child(i)
        #         child.setExpanded(False)
        #
        # item.setExpanded(True)
        #
        # item.setSelected(True)