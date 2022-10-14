# -*- coding: utf-8 -*-

import datetime
import io
import json
import os
import shutil

import hou
from imp import reload

import toolutils
from PySide2 import QtWidgets, QtCore

from oli import utils
from oli.GalleryModels import DefaultModel

reload(DefaultModel)


def screenshot(save_path):
    directory = os.path.split(save_path)[0]
    if not os.path.exists(directory):
        os.makedirs(directory)

    cur_desktop = hou.ui.curDesktop()
    scene_viewer = hou.paneTabType.SceneViewer
    scene = cur_desktop.paneTabOfType(scene_viewer)

    frame = hou.frame()

    settings = scene.flipbookSettings().stash()
    settings.frameRange((frame, frame))
    settings.resolution((512, 512))
    settings.outputToMPlay(False)
    settings.output(save_path)

    scene.flipbook(scene.curViewport(), settings)


class HoudiniNodeSetups(DefaultModel.DefaultModel):

    def __init__(self, ag):
        super(HoudiniNodeSetups, self).__init__(ag)

        self.datetime_format = '%Y-%m-%d %H:%M:%S'

        config_data = self.Gallery.getCurModelConfig()
        if "show_all" in config_data:
            self.show_all = config_data["show_all"]
        else:
            self.show_all = False
        self.toggleShowAll(self.show_all)

    def assetListContextMenuNoItems(self, event):
        menu = hou.qt.Menu()

        # Menu Item: Create Collection
        action_create_collection = QtWidgets.QAction("Create Collection", self.Gallery)
        action_create_collection.setProperty("action", "action_create_collection")
        font = action_create_collection.font()
        font.setBold(True)
        action_create_collection.setFont(font)
        menu.addAction(action_create_collection)

        # Separator
        menu.addSeparator()

        # Menu Item: Open in explorer
        action_open_in_explorer = QtWidgets.QAction("Open in Explorer", self.Gallery)
        action_open_in_explorer.setProperty("action", "action_open_in_explorer")
        menu.addAction(action_open_in_explorer)

        # Menu Item: Refresh
        action_refresh = QtWidgets.QAction("Refresh", self.Gallery)
        action_refresh.setProperty("action", "action_refresh")
        menu.addAction(action_refresh)

        # Separator
        menu.addSeparator()

        # Menu Item: Toggle Show All
        action_toggle_show_all = QtWidgets.QAction("Show All", self.Gallery)
        action_toggle_show_all.setProperty("action", "toggle_show_all")
        action_toggle_show_all.setCheckable(True)
        action_toggle_show_all.setChecked(self.show_all)
        menu.addAction(action_toggle_show_all)

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
                os.makedirs(hou.text.expandString(self.Gallery.ui.rootBox.currentText() + "/" + collection))
                self.Gallery.setMessage("")
                self.Gallery.loadState()

        elif action == "action_refresh":
            self.refresh()

        elif action == "toggle_show_all":
            self.toggleShowAll(action_toggle_show_all.isChecked())

        return True

    def createItem(self, asset_name):
        if asset_name == ".backup":
            return None

        itemData = {}

        thumbnail_path = self.Gallery.format_pattern(asset_name, "__ROOT__/__COLLECTION__/__ASSET__/thumbnail.jpg")
        if not os.path.isfile(hou.text.expandString(thumbnail_path)):
            thumbnail_path = None

        setup_file = self.Gallery.format_pattern(asset_name, "__ROOT__/__COLLECTION__/__ASSET__/__ASSET__.hns")
        if not os.path.isfile(hou.text.expandString(setup_file)):
            setup_file = None

        info_file = self.Gallery.format_pattern(asset_name, "__ROOT__/__COLLECTION__/__ASSET__/info.json")
        if os.path.isfile(hou.text.expandString(info_file)):
            itemData["info_file"] = info_file
            with io.open(hou.text.expandString(info_file), "r", encoding='utf8') as f:
                info = json.load(f)
                itemData.update(info)
        else:
            info_file = None

        category = asset_name.split("__")[-1]
        if "category" in itemData:
            category = itemData["category"]

        display_name = asset_name.replace("_", " ").rstrip(category)
        if "asset_display_name" in itemData:
            display_name = itemData["asset_display_name"]

        itemData.update({
            "asset_name": asset_name,
            "asset_display_name": display_name,
            "thumbnail_path": thumbnail_path,
            "setup_file": setup_file,
            "info_file": info_file,
            "category": category,
            "tags": self.Gallery.getTagsFromId(self.Gallery.ui.collectionsBox.currentText() + "/" + display_name),
        })

        item = QtWidgets.QListWidgetItem(self.Gallery.defaultThumbIcon, itemData["asset_display_name"])
        item.setData(QtCore.Qt.UserRole, itemData)

        self.Gallery.updateItemTooltip(item)
        self.Gallery.ui.assetList.addItem(item)
        return item

    def importAsset(self, item):
        network_editor = toolutils.networkEditor()
        parent = network_editor.pwd()

        itemData = item.data(QtCore.Qt.UserRole)

        setup_file = hou.text.expandString(itemData["setup_file"])
        category = itemData["category"]

        if parent.childTypeCategory().name() != category:
            hou.ui.displayMessage("Node is " + category, severity=hou.severityType.Error)
            return False

        # Clear selection
        for n in hou.selectedItems():
            n.setSelected(False)

        with hou.undos.group("Import"):
            parent.loadItemsFromFile(setup_file, ignore_load_warnings=True)
            nodes = hou.selectedItems()
            utils.centralizeNodes(nodes)

        return nodes

    def droppedIn(self, event):
        if not event.mimeData().hasText():
            return

        ag = self.Gallery

        text = event.mimeData().text()

        items = [hou.item(path) for path in text.split("\t") if hou.item(path)]
        if not items:
            return False

        # Avoid NetworkBoxes and any item that isn't a hou.Node to use as reference node
        node = None
        for item in items:
            if isinstance(item, hou.Node):
                node = item
                break
        if not node:
            return False

        parent = node.parent()
        creator = node.creator()

        if not parent or not creator:
            return False

        category = creator.childTypeCategory().name()

        asset_display_name = hou.ui.readInput("Setup Name")[1]
        if not asset_display_name:
            return False

        asset_name = utils.makeSafe(asset_display_name)
        directory = ag.collectionPath + "/" + asset_name

        if os.path.exists(directory):
            time_stamp = datetime.datetime.strftime(datetime.datetime.now(), '%Y-%m-%d_%H-%M-%S')
            backup_directory = ag.collectionPath + "/.backup/" + asset_name + ".bak" + time_stamp

            if not hou.ui.displayConfirmation("Overwrite \"{}\"?".format(asset_name),
                                              severity=hou.severityType.Warning,
                                              help="A backup will be saved at:\n{}".format(backup_directory),
                                              title="Asset Gallery",
                                              ):
                return False

            shutil.copytree(directory, backup_directory)
        else:
            os.makedirs(directory)

        thumbnail_file = directory + "/thumbnail.jpg"
        screenshot(thumbnail_file)

        setup_file = directory + "/" + asset_name + ".hns"
        parent.saveItemsToFile(items, setup_file, save_hda_fallbacks=True)

        info_file = directory + "/info.json"
        info = {
            "asset_display_name": asset_display_name,
            "category": category,
            "asset_name": asset_name,
            "user": hou.getenv("USER"),
            "date": datetime.datetime.strftime(datetime.datetime.now(), self.datetime_format),
            "houdini_version": hou.applicationVersionString()
        }
        with open(info_file, "w") as f:
            f.write(json.dumps(info, indent=4))

        self.refresh()

    def droppedOut(self, event):
        ag = self.Gallery
        pane = hou.ui.curDesktop().paneTabUnderCursor()
        if not pane:
            return False
        pane_type = pane.type()

        if pane_type == hou.paneTabType.NetworkEditor:
            pos = pane.cursorPosition()
            parent = pane.pwd()

            with hou.undos.group("Import"):
                node_groups = []
                for item in ag.ui.assetList.selectedItems():
                    itemData = item.data(QtCore.Qt.UserRole)

                    setup_file = hou.text.expandString(itemData["setup_file"])
                    category = itemData["category"]

                    if parent.childTypeCategory().name() != category:
                        hou.ui.displayMessage("Node is " + category, severity=hou.severityType.Error)
                        return False

                    # Clear selection
                    for n in hou.selectedItems():
                        n.setSelected(False)

                    parent.loadItemsFromFile(setup_file, ignore_load_warnings=True)
                    nodes = hou.selectedItems()

                    # Take all to 0 then move to cursor
                    first_pos = nodes[0].position()
                    for node in nodes:
                        if node.parentNetworkBox():
                            continue
                        node.move(-first_pos)
                        node.move(pos)

                    node_groups.append(nodes)

                for idx, group in enumerate(node_groups):
                    for node in group:
                        if not node or node.parentNetworkBox():
                            continue
                        node.move((-.5, -.2))
                        node.move((0, idx*-1))

        elif pane_type == hou.paneTabType.SceneViewer:
            parent = pane.pwd()

            with hou.undos.group("Import"):
                node_groups = []
                for item in ag.ui.assetList.selectedItems():
                    itemData = item.data(QtCore.Qt.UserRole)

                    setup_file = itemData["setup_file"]
                    category = itemData["category"]

                    if parent.childTypeCategory().name() != category:
                        hou.ui.displayMessage("Node is " + category, severity=hou.severityType.Error)
                        return False

                    # Clear selection
                    for n in hou.selectedItems():
                        n.setSelected(False)

                    parent.loadItemsFromFile(setup_file, ignore_load_warnings=True)
                    nodes = hou.selectedItems()

                    utils.centralizeNodes(nodes)

                    node_groups.append(nodes)

                for idx, group in enumerate(node_groups):
                    for node in group:
                        if not node:
                            continue
                        node.move((-.5, -.2))
                        node.move((0, idx*-1))

    def toggleShowAll(self, show_all):
        self.Gallery.paneTab.setShowNetworkControls(not show_all)
        if show_all != self.show_all:
            self.show_all = show_all
            self.Gallery.filterItems()

        # Update foldersTable Config
        self.Gallery.updateCurModelConfig({

        })
        data = self.Gallery.getCurModelConfig()
        data.update({
            "show_all": self.show_all
        })
        self.Gallery.setCurModelConfig(data)

    def filterItem(self, item, text=None):
        super(HoudiniNodeSetups, self).filterItem(item, text)

        if not self.show_all:
            current_category = self.Gallery.paneTab.pwd().childTypeCategory().name()
            itemData = item.data(QtCore.Qt.UserRole)
            if itemData["category"] != current_category:
                item.setHidden(True)

    def itemBadges(self, item, size=128):
        itemData = item.data(QtCore.Qt.UserRole)
        cat = itemData["category"]
        badgeList = []

        qtSize = QtCore.QSize(size, size)

        def addHIcon(name):
            badgeList.append(hou.qt.Icon(name, size, size).pixmap(qtSize))

        if cat == "Sop":
            addHIcon("OBJ_geo")
        elif cat == "Object":
            addHIcon("NETWORKS_scene")
        elif cat == "Vop":
            addHIcon("NETWORKS_vop")

        return badgeList