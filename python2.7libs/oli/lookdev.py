# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------------
# Created By: Gabriel O. Leite
# Created Date: 2022-05-26
# ----------------------------------------------------------------------------
import os
import shutil

import hou
import json
import toolutils

from . import utils


def copy_folder(src, dst, symlinks=False, ignore=None):
    """
    Copies folder tree even if it already exists in the destination.
    https://stackoverflow.com/a/12514470

    :param src: Source folder
    :param dst: Destination folder
    :param symlinks:
    :param ignore:
    :return:
    """

    for item in os.listdir(src):
        s = os.path.join(src, item)
        d = os.path.join(dst, item)
        if os.path.isdir(s):
            shutil.copytree(s, d, symlinks, ignore)
        else:
            shutil.copy2(s, d)


def demo_variant_instancer(node):
    explorevariants = node.createOutputNode("explorevariants")
    explorevariants.setParms({
        "mode": 1,
        "spacing": 0,
    })

    instancer = node.parent().createNode("instancer")
    instancer.setInput(1, explorevariants)
    instancer.moveToGoodPosition()

    instancer.setParms({
        "protopattern": "`lopinputprims('.', 1)`/*/*",
        "onlycopyprotoprims": False,
    })
    sop_grid = instancer.createNode("grid")

    sop_normal = sop_grid.createOutputNode("normal")

    sop_scatter = sop_normal.createOutputNode("scatter")

    sop_wrangle = sop_scatter.createOutputNode("attribwrangle", "randomize_orientation")
    sop_wrangle.parm("snippet").set("p@orient = quaternion(2*$PI*rand(@ptnum*.03), @N);")

    sop_output = sop_wrangle.createOutputNode("output")

    instancer.setGenericFlag(hou.nodeFlag.Display, True)

    return instancer


def get_usd_x_thumbnail(directory):
    asset_id = directory.split("_")[-1]

    with open(directory + "/" + asset_id + ".json") as f:
        data = json.load(f)

    asset_type = os.path.split(os.path.dirname(directory))[-1]
    asset_name = utils.makeSafe(data["name"])
    asset_name_full = asset_name + "_" + asset_id

    # TODO ------------------------------ delete above ------------------------------

    usd_directory = "U:/oleite/usd/" + asset_name_full
    usd_variants_directory = usd_directory + "/variants"

    usd_x_thumbnail = {}

    if not os.path.exists(usd_variants_directory):
        asset_path = usd_directory + "/" + asset_name_full + ".usd"
        thumbnail_path = usd_directory + "/" + asset_name_full + "_thumbnail.png"
        usd_x_thumbnail[asset_name_full] = {
            "asset_path": asset_path,
            "thumbnail_path": thumbnail_path
        }
    else:
        for var in os.listdir(usd_variants_directory):
            if not var.endswith(".usd"):
                continue
            asset_path = usd_variants_directory + "/" + var
            thumbnail_path = asset_path.replace(".usd", "_thumbnail.png")
            var_name_full = asset_name_full + " " + var.rstrip('.usd')

            usd_x_thumbnail[var_name_full] = {
                "asset_path": asset_path,
                "thumbnail_path": thumbnail_path,
            }

    return usd_x_thumbnail


def add_to_layout_asset_gallery(directory):
    asset_id = directory.split("_")[-1]

    with open(directory + "/" + asset_id + ".json") as f:
        data = json.load(f)

    asset_type = os.path.split(os.path.dirname(directory))[-1]
    asset_name = utils.makeSafe(data["name"])
    asset_name_full = asset_name + "_" + asset_id

    uuid_list = []

    usd_x_thumbnail_dict = get_usd_x_thumbnail(directory)
    for name in usd_x_thumbnail_dict:
        asset_path = usd_x_thumbnail_dict[name]["asset_path"]
        thumbnail_path = usd_x_thumbnail_dict[name]["thumbnail_path"]

        uuid = hou.qt.AssetGallery.addAsset(name, asset_path, thumbnail_path)
        uuid_list.append(uuid)

    if hou.isUIAvailable():
        hou.qt.AssetGallery().getLocalModel().updateFromSource()

    return uuid_list


def add_to_aws(uuid):
    import gc
    from layout.brushpanel import AssetWorkingSetPanel
    for obj in gc.get_objects():
        if isinstance(obj, AssetWorkingSetPanel):
            obj._aws.addAsset(uuid)


def add_to_ol_instancer(node, directory):
    asset_id = directory.split("_")[-1]
    with open(directory + "/" + asset_id + ".json") as f:
        data = json.load(f)
    asset_name = utils.makeSafe(data["name"])

    tag_count = node.evalParm("tag_count")

    idx1 = tag_count
    node.parm("tag_count").set(tag_count + 1)
    node.parm("tag_%i" % idx1).set(asset_name)

    usd_x_thumbnail_dict = get_usd_x_thumbnail(directory)
    node.parm("references_%i" % idx1).set(len(usd_x_thumbnail_dict))
    for idx2, name in enumerate(usd_x_thumbnail_dict):
        asset_path = usd_x_thumbnail_dict[name]["asset_path"]
        node.parm("filepath_%i_%i" % (idx1, idx2)).set(asset_path)

    return None


def createMatnet(parent, name=None, paneTab=None):
    category = parent.childTypeCategory().name()
    matnet = None

    if category == "Vop":
        matnet = parent

    elif category == "Lop":
        matnet = parent.createNode("materiallibrary", name)
        utils.moveNodeToCursor(matnet, paneTab)

    elif category == "Obj":
        matnet = parent.createNode("matnet", name)
        utils.moveNodeToCursor(matnet, paneTab)

    else:
        matnet = hou.node("/mat")

    return matnet


def buildMaterialOfRenderer(renderer, textures, name, matnet=None):
    if not matnet:           
        paneTab = hou.ui.paneTabUnderCursor()
        paneTabType = paneTab.type()

        if paneTabType == hou.paneTabType.NetworkEditor:
            pwd = paneTab.pwd()
            matnet = createMatnet(pwd, name, paneTab=paneTab)
        else:
            pwd = toolutils.networkEditor().pwd()
            matnet = createMatnet(pwd, name)

    if renderer == "VRay":
        try:
            import vray
        except ImportError:
            raise hou.Error("VRay is not installed")

        return buildVRayMaterial(textures, name, matnet)
    elif renderer == "MaterialX":
        if hou.applicationVersion() < (19, 0, 0):
            hou.ui.displayMessage('MaterialX is only supported in Houdini 19 or greater.')
            return

        return buildMaterialXMaterial(textures, name, matnet)
    else:
        hou.ui.displayMessage('"{}" materials not supported.'.format(renderer))
        return


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