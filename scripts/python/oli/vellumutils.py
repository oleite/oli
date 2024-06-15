import itertools
import os
import hou

from .utils import makeSafe

def storeNodePos(node):
    pos = node.position()
    node.setUserData("posx", str(pos.x()))
    node.setUserData("posy", str(pos.y()))


def loadNodePos(node):
    posx = node.userData("posx")
    posy = node.userData("posy")
    if posx and posy:
        node.setPosition((float(posx), float(posy)))


def separate_alembic(directory=""):
    if not directory:
        directory = hou.ui.selectFile(file_type=hou.fileType.Directory)
    if not directory or not os.path.exists(directory):
        return False

    sopnet = hou.node("obj").createNode("geo", makeSafe(directory))
    sopnet.moveToGoodPosition()

    x = 0

    for filename in os.listdir(directory):
        if not filename.endswith(".abc"):
            continue

        filepath = directory + "/" + filename

        abc = sopnet.createNode("alembic", filename.rstrip(".abc"))
        abc.parm("fileName").set(filepath)
        abc.setPosition((x, 0))
        storeNodePos(abc)

        geo = abc.geometry()
        paths = geo.primStringAttribValues("path")

        geoname_list = []
        for path in paths:
            geoname_list.append(path.split("/")[1])
        geoname_list = list(dict.fromkeys(geoname_list))  # Remove duplicates

        previous = abc
        for geoname in geoname_list:
            pattern = "/" + geoname + "/*"

            split = sopnet.createNode("split", "split_" + makeSafe(geoname))
            split.setPosition((x, -1))
            storeNodePos(split)
            split.parm("group").set("@path=" + pattern)

            in_node = split.createOutputNode("null", "IN_" + makeSafe(geoname))
            in_node.setPosition((x, -3))
            storeNodePos(in_node)

            if previous.type().name() == "split":
                split.setInput(0, previous, 1)
            else:
                split.setInput(0, previous, 0)

            previous = split
            x += 10


def separate_into_materials(root=""):
    if not root:
        root = hou.ui.readInput("Path root", help="Without namespaces", initial_contents="/geo")[1]

    root = root.strip("/")

    merge = None

    for abc in hou.selectedNodes():
        parent = abc.parent()
        x = abc.position().x()
        y = abc.position().y()

        geo = abc.geometry()
        paths = geo.primStringAttribValues("path")

        geoname_list = []
        for path in paths:
            path = path.lstrip("/")

            # splitted = []
            # for val in path.split("/"):
            #     splitted.append(val.split(":")[-1])

            splitted = path.split("/")

            splitted = list(itertools.dropwhile(lambda val: val.split(":")[-1] == root, splitted))

            geoname_list.append(splitted[0] + "/" + splitted[1])
        geoname_list = list(dict.fromkeys(geoname_list))  # Remove duplicates

        previous = abc
        if not merge:
            merge = parent.createNode("merge")
            merge.setPosition((x, y - 7))
            merge.createOutputNode("null", "OUT")

        for geoname in geoname_list:
            pattern = "/" + geoname + "/*"
            if root:
                pattern = "*" + root + pattern

            _name = makeSafe(pattern.split("/")[-2].split(":")[-1])

            split = parent.createNode("split", "split_" + makeSafe(geoname))
            split.setPosition((x, y - 1))
            storeNodePos(split)
            split.parm("group").set("@path=" + pattern)

            null = split.createOutputNode("null", "IN_" + _name)
            null.setPosition((x, y - 3))
            storeNodePos(null)

            material = null.createOutputNode("material", _name)
            merge.setNextInput(material)

            if previous.type().name() == "split":
                split.setInput(0, previous, 1)
            else:
                split.setInput(0, previous, 0)

            previous = split
            x += 3

