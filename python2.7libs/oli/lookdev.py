# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------------
# Created By: Gabriel O. Leite
# Created Date: 2022-05-26
# ----------------------------------------------------------------------------
import difflib
import os
import pickle
import shutil

import hou
import json
import re
import time
import cbFramework as cbFramework

# from __init__ import utils.makeSafe
# import utils.makeSafe
import toolutils


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