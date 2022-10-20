# -*- coding: utf-8 -*-

import json
import os

import hou
from imp import reload

import pyperclip
from PySide2 import QtWidgets, QtCore
from oli.GalleryModels import DefaultModel
from oli import lookdev
from oli import utils

reload(DefaultModel)


class MegascansUSDModel(DefaultModel.DefaultModel):
    def __init__(self, ag):
        super(MegascansUSDModel, self).__init__(ag)

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

        # Menu Item: import_all_scatter
        action_import_all_scatter = QtWidgets.QAction("Import and Scatter", self.Gallery)
        action_import_all_scatter.setProperty("action", "import_all_scatter")
        menu.addAction(action_import_all_scatter)

        # Menu Item: add_to_layout_asset_gallery
        action_add_to_layout_asset_gallery = QtWidgets.QAction("Add to Layout Asset Gallery", self.Gallery)
        action_add_to_layout_asset_gallery.setProperty("action", "add_to_layout_asset_gallery")
        menu.addAction(action_add_to_layout_asset_gallery)

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

        elif action == "import_all_scatter":
            assetReferenceNodes = []

            # Deselect all
            for n in hou.selectedNodes():
                n.setSelected(False)

            for item in itemList:
                node = self.importAsset(item)
                if node.type().name() == "assetreference":
                    assetReferenceNodes.append(node)

            # Create demo Variant Instancer from imported assets
            if len(assetReferenceNodes) > 1 or action == "import_all_scatter":
                merge_node = assetReferenceNodes[0].parent().createNode("merge")
                y = 0
                total_x = 0
                for node in assetReferenceNodes:
                    merge_node.setNextInput(node)
                    y = min(y, node.position().y())
                    total_x += node.position().x()
                x = total_x / len(assetReferenceNodes)
                merge_node.setPosition((x, y - 1))
                reload(lookdev)
                lookdev.demo_variant_instancer(merge_node)

        elif action == "add_to_layout_asset_gallery":
            for item in itemList:
                itemData = item.data(QtCore.Qt.UserRole)
                directory = self.Gallery.collectionPath + "/" + itemData["asset_name"]
                reload(lookdev)
                uuid_list = lookdev.add_to_layout_asset_gallery(directory)
                for uuid in uuid_list:
                    lookdev.add_to_aws(uuid)

        for item in itemList:
            itemData = item.data(QtCore.Qt.UserRole)

            # if action == "import_all":
            #     self.Gallery.import_asset(item)

            if action == "import_mats_styles":
                self.importAsset(item, import_geo=False)

            elif "COPY_" in action:
                action = action.lstrip("COPY_")
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

        display_name = ms_dict["semanticTags"]["name"] + " " + ms_dict["id"]

        itemData.update({
            "ms_json_path": ms_json_path,
            "asset_name": display_name,
            "thumbnail_path": self.Gallery.format_pattern(asset_name, "__ROOT__/__COLLECTION__/__ASSET__/*_Preview.png"),
            "ms_id": ms_dict["id"],
            "tags": self.Gallery.getTagsFromId(self.Gallery.ui.collectionsBox.currentText() + "/" + display_name),
        })

        geometry_pattern = "__ROOT__/__COLLECTION__/__ASSET__/*.abc"
        geometry_path = self.Gallery.format_pattern(asset_name, geometry_pattern)

        item = QtWidgets.QListWidgetItem(self.Gallery.defaultThumbIcon, itemData["asset_name"])
        item.setData(QtCore.Qt.UserRole, itemData)

        self.Gallery.updateItemTooltip(item)
        self.Gallery.ui.assetList.addItem(item)

        return item

    def importAsset(self, item):
        if not self.valid:
            return False

        itemData = item.data(QtCore.Qt.UserRole)

        asset_directory = self.Gallery.collectionPath + "/" + itemData["asset_name"]

        # selection = hou.selectedNodes()
        # if selection:
        #     if selection[-1].type().name() == "ol::instancer":
        #         reload(lookdev)
        #         return lookdev.add_to_ol_instancer(selection[-1], directory)

        # TODO
        save_directory = "U:/Gabriel_Leite/usd"
        force_rebuild = False

        selection = hou.selectedNodes()
        asset_id = asset_directory.split("_")[-1]

        with open(hou.text.expandString(itemData["ms_json_path"])) as f:
            data = json.load(f)

        asset_type = os.path.split(os.path.dirname(asset_directory))[-1]
        asset_name = utils.makeSafe(data["name"])
        asset_name_full = asset_name + "_" + asset_id

        asset_save_directory = hou.text.expandString(save_directory + "/" + asset_name_full)
        if not os.path.exists(asset_save_directory):
            os.makedirs(asset_save_directory)

        # Copy preview
        import shutil
        preview_src = asset_directory + "/" + asset_id + "_Preview.png"
        preview_dst = asset_save_directory + "/" + asset_name_full + "_thumbnail.png"
        shutil.copyfile(preview_src, preview_dst)

        parent = hou.node("/stage")

        #
        # Asset Reference
        #
        usd_filepath = asset_save_directory + "/" + asset_name_full + ".usd"

        assetreference = parent.createNode("assetreference", asset_name)
        #assetreference.moveToGoodPosition()
        assetreference.setParms({
            "filepath": usd_filepath,
        })
        assetreference.setGenericFlag(hou.nodeFlag.Display, True)

        assetreference.setSelected(True, True)

        if selection:
            assetreference.setInput(0, selection[-1])

        if not force_rebuild and os.path.exists(usd_filepath):
            return assetreference

        #
        # TOPNET
        #

        topnet = parent.createNode("topnet", asset_name + "__BUILDING_ASSET")
        topnet.setPosition(assetreference.position())
        topnet.move((0, 1))

        hserver_begin = topnet.createNode("houdiniserver")

        sendcommand = hserver_begin.createOutputNode("sendcommand")

        sendcommand.parm("commandstring").set('''
import hou
from oli import build_asset

hou.hipFile.save("''' + asset_save_directory + '''/''' + asset_name_full + '''.hip", False)

componentoutput = build_asset.build_megascans_component("'''+asset_directory+'''")
componentoutput.parm("lopoutput").set("\$HIP/\`chs('filename')\`")
componentoutput.parm("execute").pressButton()

hou.hipFile.save()
        ''')

        hserver_end = sendcommand.createOutputNode("commandserverend")
        hserver_end.parm("pdg_feedbackbegin").set("../" + hserver_begin.name())
        hserver_end.setColor(hserver_begin.color())
        hserver_end.setGenericFlag(hou.nodeFlag.Display, True)

        topnet.layoutChildren()

        # Cook
        topnet.parm("cookbutton").pressButton()

        return assetreference

    def collectionChanged(self):
        super(MegascansUSDModel, self).collectionChanged()

        if hou.applicationVersion()[0] < 19:
            self.valid = False
            self.Gallery.setMessage('<span class="error">MegascansUSDModel só é suportado a partir do Houdini 19</span>')