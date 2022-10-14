# -*- coding: utf-8 -*-

import os
import hou
import toolutils
from PySide2 import QtWidgets, QtCore
import pyperclip

from oli import utils
from oli import gallery

class DefaultModel(object):
    def __init__(self, asset_gallery):
        self.Gallery = asset_gallery
        self.Gallery.paneTab.setShowNetworkControls(False)
        self.Gallery.setMessage("")
        self.valid = True

    def assetListContextMenuNoItems(self, event):
        menu = hou.qt.Menu()

        # Menu Item: Open in explorer
        action_open_in_explorer = QtWidgets.QAction("Open in Explorer", self.Gallery)
        action_open_in_explorer.setProperty("action", "action_open_in_explorer")
        menu.addAction(action_open_in_explorer)

        # Menu Item: Create Collection
        action_create_collection = QtWidgets.QAction("Create Collection", self.Gallery)
        action_create_collection.setProperty("action", "action_create_collection")
        menu.addAction(action_create_collection)

        # Menu Item: Refresh
        action_refresh = QtWidgets.QAction("Refresh", self.Gallery)
        action_refresh.setProperty("action", "action_refresh")
        menu.addAction(action_refresh)

        # Open Menu
        menu_exec = menu.exec_(event.globalPos())
        if not menu_exec:
            return False
        action = menu_exec.property("action")

        if action == "action_open_in_explorer":
            # TODO: Make more reliable "Open in Explorer" method
            directory = self.Gallery.collectionPath
            os.startfile(directory)

        elif action == "action_create_collection":
            collection = hou.ui.readInput("Collection Name")[1]
            if collection:
                os.makedirs(self.Gallery.ui.rootBox.currentText() + "/" + collection)
                self.Gallery.loadState()

        elif action == "action_refresh":
            self.refresh()

        return True

    def assetListContextMenu(self, event, itemList):
        if len(itemList) == 0:
            return self.assetListContextMenuNoItems(event)

        menu = hou.qt.Menu()

        # Menu Item: import_all
        action_import_all = QtWidgets.QAction("Import", self.Gallery)
        action_import_all.setProperty("action", "import_all")
        font = action_import_all.font()
        font.setBold(True)
        action_import_all.setFont(font)
        menu.addAction(action_import_all)

        # Separator
        menu.addSeparator()

        # Only show if single item selected
        if len(itemList) == 1:
            itemData = itemList[0].data(QtCore.Qt.UserRole)

            # Menu Item: "Copy" submenu
            submenu_copy = menu.addMenu("Copy")
            for key in itemData:
                if not itemData[key]:
                    continue
                keyname = key.replace("_", " ")
                keyname = keyname[0].upper() + keyname[1:]
                new_action = QtWidgets.QAction(keyname, self.Gallery)
                new_action.setProperty("action", "COPY_" + key)
                submenu_copy.addAction(new_action)

            # Menu Item: Open in explorer
            action_open_in_explorer = QtWidgets.QAction("Open Asset in Explorer", self.Gallery)
            action_open_in_explorer.setProperty("action", "action_open_in_explorer")
            menu.addAction(action_open_in_explorer)

        # Open Menu
        menu_exec = menu.exec_(event.globalPos())
        if not menu_exec:
            return False
        action = menu_exec.property("action")

        #
        # Run callbacks based on QActions "action" properties
        #

        if action == "import_all":
            for item in itemList:
                node = self.importAsset(item)

        for item in itemList:
            itemData = item.data(QtCore.Qt.UserRole)

            # if action == "import_all":
            #     self.Gallery.import_asset(item)

            if "COPY_" in action:
                action = action.lstrip("COPY_")
                pyperclip.copy(itemData[action])  # Copy to clipboard

            elif action == "action_open_in_explorer":
                # TODO: Make more reliable "Open in Explorer" method
                directory = self.Gallery.collectionPath + "/" + itemData["asset_name"]
                os.startfile(directory)

        return True

    def filterItem(self, item, text=None):
        itemData = item.data(QtCore.Qt.UserRole)

        item.setHidden(False)

        if text:
            if "*" in text:
                item.setHidden(not hou.text.patternMatch(text, item.data(0), ignore_case=True))
            else:
                item.setHidden(text.lower() not in item.data(0).lower())

        if self.Gallery.ui.toggleFavorites.isChecked() and "favorite" not in self.Gallery.getTags(item):
            item.setHidden(True)

        if self.Gallery.ui.treeNav.currentItem() and "category" in itemData:
            selectedPath = utils.treeItemToFullPath(self.Gallery.ui.treeNav.currentItem())

            if not itemData["category"].startswith(selectedPath):
                item.setHidden(True)

    def createItems(self):
        """
        Creates each item inside of the assetList from scratch.

        :return: List of QListWidgetItems
        """
        self.Gallery.ui.assetList.clear()

        if not os.path.exists(self.Gallery.collectionPath):
            return

        assets = next(os.walk(self.Gallery.collectionPath))[1]
        items = []

        for asset_name in sorted(assets):
            item = self.createItem(asset_name)
            if not item:
                continue
            items.append(item)
            self.Gallery.threadPool.start(self.Gallery.LoadItemThumbnail(item))

            item.setData(gallery.ITEM_BADGES_LIST_ROLE, self.itemBadges(item))

        self.Gallery.filterItems()
        return items

    def createItem(self, asset_name):
        itemData = {
            "asset_name": asset_name,
            "asset_display_name": asset_name.replace("_", " "),
            "thumbnail_path": None,
        }

        item = QtWidgets.QListWidgetItem(self.Gallery.defaultThumbIcon, itemData["asset_display_name"])
        item.setData(QtCore.Qt.UserRole, itemData)

        self.Gallery.updateItemTooltip(item)
        self.Gallery.ui.assetList.addItem(item)

        return item

    def itemBadges(self, item):
        badgeList = []
        return badgeList

    def importAsset(self, item):
        asset_name = item.data(0)
        selection = hou.selectedNodes()
        scene_viewer = hou.ui.paneTabOfType(hou.paneTabType.SceneViewer)

        itemData = item.data(QtCore.Qt.UserRole)
        collection = self.Gallery.ui.collectionsBox.currentText()

        n_sublayer = None

        if toolutils.activePane([]).isViewingSceneGraph():
            if "geometry_path" in itemData and itemData["geometry_path"]:
                # LOP Sublayer
                node = toolutils.activePane([]).pwd()
                n_sublayer = node.createNode("sublayer", utils.makeSafe(collection + "__" + asset_name))
                n_sublayer.parm("filepath1").set(itemData["geometry_path"])
                n_sublayer.setSelected(True, True)
                n_sublayer.setGenericFlag(hou.nodeFlag.Display, True)

                if selection:
                    n_sublayer.setInput(0, selection[-1])

        utils.flashMessage("Imported: " + asset_name, 3)
        return n_sublayer

    def droppedIn(self, event):
        return
    
    def droppedOut(self, event):
        ag = self.Gallery
        
        pane = hou.ui.curDesktop().paneTabUnderCursor()
        if not pane:
            return
        pane_type = pane.type()

        if pane_type == hou.paneTabType.NetworkEditor:
            pos = pane.cursorPosition()
            imported_nodes = ag.importSelectedAssets()

            for idx, node in enumerate(imported_nodes):
                if not node:
                    continue
                node.setPosition(pos)
                node.move((-.5, -.2))
                node.move((0, idx*-1))

        elif pane_type == hou.paneTabType.SceneViewer:
            if pane.currentState() == "sidefx_lop_layout":
                ag.import_selected_assets_to_lop_layout()
            else:
                imported_nodes = []
                for node in ag.importSelectedAssets():
                    node.moveToGoodPosition()
                    imported_nodes.append(node)
                utils.centralizeNodes(imported_nodes)

        elif pane_type == hou.paneTabType.Parm:
            node = pane.currentNode()
            node_type = node.type().name()

            if node_type == "ol::instancer":
                ag.import_selected_assets_to_ol_instancer(node)

            elif node_type == "layout":
                ag.import_selected_assets_to_lop_layout()

    def pwdChanged(self, old, new):
        self.Gallery.filterItems()

    def collectionsList(self):
        self.Gallery.ui.assetList.clear()
        root = hou.text.expandString(self.Gallery.ui.rootBox.currentText())
        if os.path.exists(root):
            collections_list = next(os.walk(root))[1]
            return collections_list
        return []

    def collectionChanged(self):
        collection = self.Gallery.ui.collectionsBox.currentText()

        self.Gallery.ui.treeNav.clear()

        # Update self.current_root_model
        for i in range(self.Gallery.ui.foldersTable.rowCount()):
            root_item = self.Gallery.ui.foldersTable.item(i, 0)
            model_item = self.Gallery.ui.foldersTable.item(i, 1)

            i_root = root_item.text() if root_item else ""
            i_model = model_item.text() if model_item else ""

            if i_root == self.Gallery.ui.rootBox.currentText():
                self.Gallery.currentRootModel = i_model
                break

        self.Gallery.collectionPath = self.Gallery.ui.rootBox.currentText() + "/" + collection
        self.Gallery.collectionPath = hou.text.expandString(self.Gallery.collectionPath)
        self.Gallery.createItems()

    def refresh(self):
        self.Gallery.loadState()

    def treeNavItemChanged(self, item, oldItem):
        self.Gallery.filterItems()

    def createNavHierarchy(self, category):
        tree = self.Gallery.ui.treeNav
        splitCategory = category.strip("/").split("/")

        topCat = splitCategory[0]
        childrenValues = [tree.topLevelItem(idx).text(0) for idx in range(tree.topLevelItemCount())]
        if topCat in childrenValues:
            item = tree.topLevelItem(childrenValues.index(topCat))
        else:
            item = QtWidgets.QTreeWidgetItem(tree, [topCat, ])

        item.setExpanded(True)

        for subCat in splitCategory[1:]:
            childrenValues = [item.child(idx).text(0) for idx in range(item.childCount())]

            if subCat in childrenValues:
                if item:
                    child = item.child(childrenValues.index(subCat))
            else:
                child = QtWidgets.QTreeWidgetItem(item, [subCat, ])
            item = child