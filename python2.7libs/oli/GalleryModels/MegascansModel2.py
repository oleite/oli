# -*- coding: utf-8 -*-

import json
import os

import hou
from imp import reload

import pyperclip
import toolutils
from PySide2 import QtWidgets, QtCore, QtGui
from oli.GalleryModels import DefaultModel
from oli import lookdev
from oli import utils
from oli import gallery

from olcb import AssetBuilder

reload(DefaultModel)

from timeit import default_timer as timer

class CBMegascansModel(DefaultModel.DefaultModel):
    def __init__(self, ag):
        super(CBMegascansModel, self).__init__(ag)

    def assetListContextMenu(self, event, itemList):
        if not self.valid:
            return False

        menu = hou.qt.Menu()

        if len(itemList) == 0:
            # Menu Item: Open in explorer
            action_open_in_explorer = QtWidgets.QAction("Open in Explorer", self.Gallery)
            action_open_in_explorer.setProperty("action", "action_open_in_explorer")
            menu.addAction(action_open_in_explorer)

            # Menu Item: Refresh
            action_refresh = QtWidgets.QAction("Refresh", self.Gallery)
            action_refresh.setProperty("action", "action_refresh")
            menu.addAction(action_refresh)

            # Menu Item: Change Color
            action_change_color = QtWidgets.QAction("Change Color", self.Gallery)
            action_change_color.setProperty("action", "action_change_color")
            menu.addAction(action_change_color)

            # Open Menu
            menu_exec = menu.exec_(event.globalPos())
            if not menu_exec:
                return False
            action = menu_exec.property("action")

            if action == "action_open_in_explorer":
                # TODO: Make more reliable "Open in Explorer" method
                directory = self.Gallery.collectionPath
                os.startfile(directory)

            elif action == "action_refresh":
                self.refresh()

            elif action == "action_change_color":
                hou.ui.openColorEditor(self.Gallery.changeColor, initial_color=self.Gallery.color)

            return True

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

        for item in itemList:
            itemData = item.data(QtCore.Qt.UserRole)

            if action == "import_all":
                node = self.importAsset(item)

            elif "COPY_" in action:
                action = action.replace("COPY_", "")
                pyperclip.copy(itemData[action])  # Copy to clipboard

            elif action == "action_open_in_explorer":
                # TODO: Make more reliable "Open in Explorer" method
                directory = self.Gallery.collectionPath + "/" + itemData["asset_name"]
                os.startfile(directory)

        return True

    def createItem(self, asset_name):
        itemData = {
            "asset_name": asset_name,
            "asset_display_name": asset_name.replace("_", " "),
            "thumbnail_path": None,
        }

        ms_json_path = self.Gallery.format_pattern(asset_name, "__ROOT__/__COLLECTION__/__ASSET__/*.json")
        if not os.path.isfile(ms_json_path):
            return

        with open(hou.text.expandString(ms_json_path), "r") as f:
            ms_dict = json.load(f)

        display_name = ms_dict["semanticTags"]["name"]

        d = ms_dict["assetCategories"]
        categoryList = []
        while len(d) > 0:
            if not type(d) == dict:
                break
            cat = sorted(d)[0]
            l = [w.strip().capitalize().replace("3d", "3D") for w in cat.split()]
            categoryList.append(utils.makeSafe("".join(l)))
            d = d[cat]
        category = "/".join(categoryList)

        self.createNavHierarchy(category)

        itemData.update({
            "ms_json_path": ms_json_path,
            "asset_display_name": display_name,
            "thumbnail_path": self.Gallery.format_pattern(asset_name,
                                                          "__ROOT__/__COLLECTION__/__ASSET__/*_Preview.png"),
            "ms_id": ms_dict["id"],
            "tags": self.Gallery.getTagsFromId(self.Gallery.ui.collectionsBox.currentText() + "/" + display_name),
            "category": category
        })

        item = QtWidgets.QListWidgetItem(self.Gallery.defaultThumbIcon, itemData["asset_display_name"])
        item.setData(QtCore.Qt.UserRole, itemData)

        self.Gallery.updateItemTooltip(item)
        self.Gallery.ui.assetList.addItem(item)

        return item

    def importAsset(self, item):
        if not self.valid:
            return
        itemData = item.data(QtCore.Qt.UserRole)
        assetDir = utils.join(self.Gallery.collectionPath, itemData["asset_name"])

        return AssetBuilder.buildMegascans(assetDir)
