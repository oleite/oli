# -*- coding: utf-8 -*-

import json
import os
import re

import hou
from imp import reload

import pyperclip
import toolutils
from PySide2 import QtWidgets, QtCore, QtGui
from oli.GalleryModels import DefaultModel
from oli import lookdev
from oli import utils
from oli import gallery

reload(DefaultModel)

from timeit import default_timer as timer

class MegascansModel(DefaultModel.DefaultModel):
    def __init__(self, ag):
        super(MegascansModel, self).__init__(ag)

        self.rendererWidget = QtWidgets.QWidget()
        self.rendererWidgetLayout = QtWidgets.QHBoxLayout()
        self.rendererWidget.setLayout(self.rendererWidgetLayout)

        # label = QtWidgets.QLabel("Renderer:")
        # self.rendererWidgetLayout.addWidget(label)

        self.rendererComboBox = QtWidgets.QComboBox()
        self.rendererWidgetLayout.addWidget(self.rendererComboBox)

        self.rendererComboBox.currentTextChanged.connect(self.rendererChanged)
        self.rendererComboBox.setToolTip("Renderer")

        self.rendererComboBox.blockSignals(True)
        
        # Add available renderers to comboBox
        for val in ["VRay", "MaterialX"]:
            self.rendererComboBox.addItem(val)

        # Load from preferences
        renderer = self.Gallery.getCurModelConfig().get("renderer")
        if renderer:
            self.rendererComboBox.setCurrentText(renderer)
        
        self.rendererComboBox.blockSignals(False)

        self.rendererWidgetLayout.setSpacing(10)
        self.rendererWidgetLayout.setContentsMargins(10, 3, 10, 3)
        
        self.rendererWidget.setStyleSheet("""
            QComboBox {
                font: 18px;
            }
            QComboBox::drop-down {
                min-width: 0px;
            }
        """)

        self.Gallery.ui.leftNavWidget.layout().addWidget(self.rendererWidget)

    def rendererChanged(self, val):
        self.Gallery.updateCurModelConfig({
            "renderer": val,
        })

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
            "tags": self.Gallery.getTagsFromId(ms_dict["id"]),
            "category": category
        })

        item = QtWidgets.QListWidgetItem(self.Gallery.defaultThumbIcon, itemData["asset_display_name"])
        item.setData(QtCore.Qt.UserRole, itemData)
        item.setData(gallery.ITEM_ID_ROLE, ms_dict["id"])

        self.Gallery.updateItemTooltip(item)
        self.Gallery.ui.assetList.addItem(item)

        return item

    def importAsset(self, item):
        if not self.valid:
            return
        itemData = item.data(QtCore.Qt.UserRole)
        assetDir = utils.join(self.Gallery.collectionPath, itemData["asset_name"])

        msName = itemData["asset_display_name"]
        msId = itemData["ms_id"]
        msType = itemData["category"].split("/")[0]

        obj = self.getObjNet()

        # ================================================================================
        # Survey for files

        textures = {
            "displacement": None,
            "roughness": None,
            "albedo": None,
            # "ao": None,
            "normal": None,
            "translucency": None,
            "opacity": None,
        }
        alembicList = []

        def survey(_path):
            """
            Checks if the _path is a useful file, and if so adds it to its according list.
            """

            if not os.path.isfile(_path):
                return

            def getLOD(abcPath):
                splitted = abcPath.split("_LOD")
                
                root = splitted[0]
                
                if len(splitted) > 1:
                    lod = int(splitted[-1].replace(".abc", ""))
                else:
                    lod = -1
                
                return root, lod

            name = os.path.split(_path)[-1]
            if name.endswith(".abc"):

                # Checks if there is an Alembic at the same folder with a lower LOD number
                root, lod = getLOD(_path)
                for p in alembicList:
                    _root, _lod = getLOD(p)
                    if root == _root and lod > _lod:
                        return

                alembicList.append(_path)

            for texName in textures:
                if texName.lower() in [s.lower() for s in name.replace(".", "_").split("_")]:
                    textures[texName] = _path

        for name in os.listdir(assetDir):
            path = utils.join(assetDir, name)

            if os.path.isfile(path):
                survey(path)
                continue

            if name.startswith("Var") or name == "Textures":
                for name2 in os.listdir(path):
                    path2 = utils.join(path, name2)
                    if name2 == "Atlas":
                        for name3 in os.listdir(path2):
                            path3 = utils.join(path2, name3)
                            survey(path3)
                    else:
                        survey(path2)

        # ================================================================================
        # Build

        nodeName = utils.makeSafe("_".join([msName, msId]))

        if msType in ["3DAsset", "3DPlant", "Atlas"]:
            if not alembicList and msType in ["3DAsset", "3DPlant"]:
                hou.ui.displayMessage("No alembic found", title="Build Megascans", help=assetDir,
                                      severity=hou.severityType.Error)
                return

            objNode = obj.createNode("geo", nodeName)
            matnet = objNode.createNode("matnet", "materials")
            material = self.buildMaterial(textures, nodeName, matnet)


            if msType == "Atlas" and "opacity" in textures:
                opacityMap = textures["opacity"]

                try:
                    atlasSplitter = objNode.createNode("ODFX_AtlasSplitter")  # TODO
                    atlasSplitter.setParms({
                        "file": opacityMap,
                    })
                except hou.OperationFailed:
                    atlasSplitter = objNode.createNode("null", "ODFX_AtlasSplitter")
                    hou.ui.displayMessage("ODFX AtlasSplitter HDA wasn't found.", help="Available at: https://origamidigital.com")

                matSop = atlasSplitter.createOutputNode("material", "assign_material")
                matSop.parm("shop_materialpath1").set("../materials/{}".format(nodeName))

                outNullSop = matSop.createOutputNode("null", "OUT_MERGED")
                outNullSop.setGenericFlag(hou.nodeFlag.Display, True)
                outNullSop.setGenericFlag(hou.nodeFlag.Render, True)
                pass
            else:
                def cmToM(node):
                    xformSop = node.createOutputNode("xform", "cm_to_m")
                    xformSop.parm("scale").set(0.01)

                    switchIf = node.createOutputNode("switchif", "if_convert_to_meters")
                    switchIf.setInput(1, xformSop)
                    switchIf.parm("expr1").setExpression("ch('../convert_to_meters')")
                    return switchIf

                mergeSop = objNode.createNode("merge", "variation_merge")
                outNullMergedSop = cmToM(mergeSop).createOutputNode("null", "OUT_MERGED")

                switchSop = objNode.createNode("switch", "variation_switch")
                for abcPath in alembicList:
                    name = utils.makeSafe(os.path.split(abcPath)[-1].replace(".abc", ""))

                    abcSop = objNode.createNode("alembic", name)
                    abcSop.parm("fileName").set(abcPath)

                    nameSop = abcSop.createOutputNode("name", "name")
                    nameSop.parm("name1").set(name)

                    mergeSop.setNextInput(nameSop)
                    switchSop.setNextInput(nameSop)

                matSop = cmToM(switchSop).createOutputNode("material", "assign_material")
                matSop.parm("shop_materialpath1").set("../materials/{}".format(nodeName))

                outNullSop = matSop.createOutputNode("null", "OUT_SINGLE")
                outNullSop.setGenericFlag(hou.nodeFlag.Display, True)
                outNullSop.setGenericFlag(hou.nodeFlag.Render, True)

                # ================================================================================
                # Create "Variation" switch parm on top level objNode

                geoCount = len(switchSop.inputs())

                folderTemplateList = [
                    hou.ToggleParmTemplate("convert_to_meters", "Convert to Meters", True)
                ]
                if geoCount > 1:
                    folderTemplateList.append(
                        hou.IntParmTemplate("variation", "Variation", 1, (0,), min=0, max=geoCount - 1),
                    )
                    switchSop.parm("input").setExpression("ch('../variation')")
                else:
                    switchSop.destroy()

                folderTemplate = hou.FolderParmTemplate("tab_properties", "Properties", folderTemplateList,
                                                        hou.folderType.Simple)

                templateGroup = objNode.parmTemplateGroup()
                templateGroup.insertBefore((0,), hou.SeparatorParmTemplate("sep"))
                templateGroup.insertBefore((0,), folderTemplate)
                objNode.setParmTemplateGroup(templateGroup)

            matnet.layoutChildren()
            objNode.layoutChildren()
            objNode.setSelected(True, True)
            return objNode

        else:
            material = self.buildMaterial(textures, nodeName)
            if material:
                material.setSelected(True, True)
            return material

    @staticmethod
    def createMatnet(parent, name=None, paneTab=None):
        category = parent.childTypeCategory().name()
        matnet = None

        if category == "Vop":
            matnet = parent

        elif category == "Lop":
            matnet = parent.createNode("materiallibrary")
            
            if paneTab:
                matnet.setPosition(paneTab.cursorPosition())
                matnet.move((-.5, -.2))
        else:
            matnet = hou.node("/mat")

        if name:
            matnet.setName(name, True)
        return matnet

    def buildMaterial(self, textures, name, matnet=None):
        if not matnet:           

            paneTab = hou.ui.paneTabUnderCursor()
            paneTabType = paneTab.type()

            if paneTabType == hou.paneTabType.NetworkEditor:
                pwd = paneTab.pwd()
                matnet = self.createMatnet(pwd, name, paneTab=paneTab)
            else:
                pwd = toolutils.networkEditor().pwd()
                matnet = self.createMatnet(pwd, name)

        choice = self.rendererComboBox.currentText()

        if choice == "VRay":
            try:
                import vray
            except ImportError:
                raise hou.Error("VRay is not installed")
            
            self.buildVRayMaterial(textures, name, matnet)
        elif choice == "MaterialX":
            self.buildMaterialXMaterial(textures, name, matnet)
        else:
            hou.ui.displayMessage('"{}" materials not supported.'.format(choice))
            return

        matnet.layoutChildren()

    @staticmethod
    def buildMaterialXMaterial(textures, nodeName, matnet):
        subnet = matnet.createNode("subnet", nodeName)
        subnet.setGenericFlag(hou.nodeFlag.Material, True)

        for n in subnet.children():
            n.destroy()

        displacementOutput = subnet.createNode("subnetconnector", "displacement_output")
        displacementOutput.setParms({
            "connectorkind": "output",
            "parmname": "displacement",
            "parmlabel": "Displacement",
            "parmtype": "displacement",
        })

        surfaceOutput = subnet.createNode("subnetconnector", "surface_output")
        surfaceOutput.setParms({
            "connectorkind": "output",
            "parmname": "surface",
            "parmlabel": "Surface",
            "parmtype": "surface",
        })

        mtlxStdSurface = surfaceOutput.createInputNode(0, "mtlxstandard_surface") 

        albedoMap = textures.pop("albedo", None)
        opacityMap = textures.pop("opacity", None)
        roughnessMap = textures.pop("roughness", None)
        normalMap = textures.pop("normal", None)
        displacementMap = textures.pop("displacement", None)
        translucencyMap = textures.pop("translucency", None)

        if albedoMap:
            mtlxImage = subnet.createNode("mtlximage", "albedo_map")
            mtlxStdSurface.setNamedInput("base_color", mtlxImage, 0)
            mtlxImage.setParms({
                "signature": "color3",
                "file": albedoMap,
            })

        if opacityMap:
            mtlxImage = subnet.createNode("mtlximage", "opacity_map")
            mtlxStdSurface.setNamedInput("opacity", mtlxImage, 0)
            mtlxImage.setParms({
                "signature": "opacity",
                "file": opacityMap,
            })

        if roughnessMap:
            mtlxImage = subnet.createNode("mtlximage", "roughness_map")
            mtlxStdSurface.setNamedInput("specular_roughness", mtlxImage, 0)
            mtlxImage.setParms({
                "signature": "default",
                "file": roughnessMap,
            })

        if normalMap:
            mapNormal = subnet.createNode("mtlxnormalmap", "map_normals")
            mtlxStdSurface.setNamedInput("normal", mapNormal, 0)

            mtlxImage = mapNormal.createInputNode(0, "mtlximage", "normap_map")
            mtlxImage.setParms({
                "signature": "vector3",
                "file": normalMap,
            })

        if displacementMap:
            mtlxDisplacement = displacementOutput.createInputNode(0, "mtlxdisplacement")
            mtlxDisplacement.parm("scale").set(.01)

            mtlxImage = mtlxDisplacement.createInputNode(0, "mtlximage", "displacement_map")
            mtlxImage.setParms({
                "signature": "default",
                "file": displacementMap,
            })

        if translucencyMap:
            mtlxImage = subnet.createNode("mtlximage", "translucency_map")
            mtlxStdSurface.setNamedInput("subsurface_color", mtlxImage, 0)
            mtlxImage.setParms({
                "signature": "color3",
                "file": translucencyMap,
            })
            mtlxStdSurface.parm("subsurface").set(1)

        subnet.layoutChildren()
        return subnet


    @staticmethod
    def buildVRayMaterial(textures, nodeName, matnet):
        vraySubnet = matnet.createNode("vray_vop_material", nodeName)
        vrayMtl = vraySubnet.node("vrayMtl")
        vrayOutput = vraySubnet.node("vrayOutput")

        def imageFileNode(imgPath, name, colorSpace="lin_srgb"):
            node = vraySubnet.createNode("VRayNodeMetaImageFile", name)
            node.parm("BitmapBuffer_file").set(imgPath)
            node.parm("BitmapBuffer_rgb_color_space").set(colorSpace)
            if colorSpace == "raw":
                node.parm("BitmapBuffer_color_space").set("0")
            return node

        vrayMtl.parmTuple("reflect").set((1, 1, 1, 1))

        albedoMap = textures.get("albedo")
        opacityMap = textures.get("opacity")
        roughnessMap = textures.get("roughness")
        normalMap = textures.get("normal")
        displacementMap = textures.get("displacement")
        translucencyMap = textures.get("translucency")

        if albedoMap:
            fileNode = imageFileNode(albedoMap, "albedo_map", "lin_srgb")
            vrayMtl.setNamedInput("diffuse", fileNode, 0)
            vraySubnet.parm("ogl_tex1").set(albedoMap)

        if opacityMap:
            fileNode = imageFileNode(opacityMap, "opacity_map", "raw")
            vrayMtl.setNamedInput("opacity", fileNode, 0)
            vraySubnet.parm("ogl_opacitymap").set(opacityMap)

        if roughnessMap:
            fileNode = imageFileNode(roughnessMap, "roughness_map", "raw")
            invert = fileNode.createOutputNode("VRayNodeTexInvert", "invert_to_glossiness")
            vrayMtl.setNamedInput("reflect_glossiness", invert, 0)
            # vrayMtl.parm("option_use_roughness").set("1")   # Doesn't work with VRay RTX

        if normalMap:
            fileNode = imageFileNode(normalMap, "normal_map", "raw")
            vrayMtl.setNamedInput("bump_map", fileNode, 0)
            vrayMtl.parm("bump_type").set("1")  # Bump Type: Normal (Tangent)

        if displacementMap:
            fileNode = imageFileNode(displacementMap, "displacement_map", "raw")
            displacement = fileNode.createOutputNode("VRayNodeGeomDisplacedMesh")
            displacement.parm("displacement_amount").set(.01)
            displacement.parm("displacement_shift").setExpression("ch('displacement_amount')/-2")
            vrayOutput.setInput(1, displacement)

        if translucencyMap:
            fileNode = imageFileNode(translucencyMap, "translucency_map", "lin_srgb")
            twoSided = vrayMtl.createOutputNode("VRayNodeMtl2Sided", "twoSidedMtl")
            twoSided.setNamedInput("translucency_tex", fileNode, 0)
            vrayOutput.setInput(0, twoSided)

        vraySubnet.layoutChildren()
        return vraySubnet