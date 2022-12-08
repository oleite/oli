import collections
import imp
import os
import re
import shutil
import sys
import time
from math import floor

import toolutils
import hou


def sgtkExists(verbose=True):
    """
    Checks if ShotGrid modules are available module exists.

    :return: Whether the sgtk module was found.
    """
    try:
        imp.find_module("sgtk")
        return True
    except Exception as e:
        if verbose:
            print(e)
        return False


def wait(amount):
    """
    Stops the code execution for the specified amount of time while keeping Houdini responsive.

    :param amount: Time in seconds
    :return: None
    """
    startTime = time.time()
    endTime = startTime + amount
    hou.ui.waitUntil(lambda: time.time() >= endTime)
    return None


def centralizeNodes(selection):
    """
    Repositions nodes to the center of the Houdini networkEditor.

    :param selection: List of 'hou.Node's.
    :return: hou.Vector2 of the target if operation successful.
    """
    if not selection:
        return None

    networkEditor = toolutils.networkEditor()
    if not networkEditor:
        return None

    targetPos = networkEditor.visibleBounds().center()

    first_pos = selection[0].position()
    for node in selection:
        if node.parentNetworkBox():
            continue
        node.move(targetPos - first_pos)

    wait(.1)
    networkEditor.homeToSelection()
    return targetPos


def moveNodeToCursor(node, paneTab=None):
    if not paneTab:
        paneTab = toolutils.networkEditor()

    node.setPosition(paneTab.cursorPosition())
    node.move((-.5, -.2))


def flashMessage(message, duration):
    """

    :param message:
    :param duration:
    :return:
    """
    toolutils.sceneViewer().flashMessage("", message, duration)
    toolutils.networkEditor().flashMessage("", message, duration)


def cameraFrameGeometry(nodeOrGeometry, camera=None):
    """
    Frames the camera to the geometry.

    :param nodeOrGeometry: hou.Node (Sop or Obj) or hou.Geometry
    :param camera: Optional camera to be set as current.
    :return: hou.GeometryViewportCamera
    """
    _type = type(nodeOrGeometry)
    if _type == hou.ObjNode:
        geometry = nodeOrGeometry.displayNode().geometry()
    elif _type == hou.SopNode:
        geometry = nodeOrGeometry.geometry()
    elif _type == hou.Geometry:
        geometry = nodeOrGeometry
    else:
        return None

    viewport = toolutils.sceneViewer().curViewport()
    if camera:
        viewport.setCamera(camera)

    viewportCam = viewport.defaultCamera()

    viewport.lockCameraToView(True)
    wait(.1)
    viewportCam.setTranslation((0, 1, 6))
    viewportCam.setRotation(hou.Matrix3(1))
    wait(.1)
    viewport.frameBoundingBox(geometry.boundingBox())
    wait(.1)
    viewport.lockCameraToView(False)

    return viewportCam


def patternMatchFile(path):
    path = normpath(path)
    if "*" in path:
        split = path.rsplit("/", 1)
        if not os.path.exists(split[0]):
            return path

        for filename in os.listdir(split[0]):
            if hou.text.patternMatch(split[1], filename):
                path = split[0] + "/" + filename
                return path
    return path


def fixRenderParms(node):
    """
    Workaround to fix the lack of parameters in the Render tab of a imported HDA that was saved by a script.
    WARNING: HDA already existing parameters might get deleted.

    :param node: hou.Node to be modified.
    :return: None
    """
    tempGeo = hou.node("/obj").createNode("geo")
    group = tempGeo.parmTemplateGroup()
    tempGeo.destroy()
    node.setParmTemplateGroup(group)
    return


def copytree(src, dst, symlinks=False, ignore=None):
    """
    Copy an entire directory of files into an existing (or not) directory
    https://stackoverflow.com/a/12514470

    :param src: Source file/folder
    :param dst: Destination file/folder
    :return:
    """
    for item in os.listdir(src):
        s = os.path.join(src, item)
        d = os.path.join(dst, item)
        if os.path.isdir(s):
            shutil.copytree(s, d, symlinks, ignore)
        else:
            shutil.copy2(s, d)


def normpath(path):
    if path:
        path = os.path.normpath(path).replace("\\", "/")
    else:
        path = ""
    return path


def join(path, *paths):
    return normpath(os.path.join(path, *paths))


def makeSafe(text):
    """
    Makes a text safe by replacing special characters and spaces by underscores, so that
    it can be used in things such as node names.

    :param text: The string to be processed
    :return: String
    """
    text = re.sub(r"[^a-zA-Z0-9]+", "_", text)
    return text


def selectAnyFromTree(path_list, exclusive=True):
    """
    Extends hou.ui.selectFromTree()
    Converts ["/character/pig/hat",] to ["/character","/character/pig","/character/pig/hat"]

    :param path_list: A sequence of strings containing the possible full paths.
    :param exclusive: Whether or not the user must choose exactly one of the possible choices.
    :return: Tuple of selected choice(s).
    """

    choices = []
    for path in path_list:
        plist = []
        for p in path.split("/"):
            plist.append(p)
            choices.append("/".join(plist))

    choices = list(dict.fromkeys(choices))  # Remove duplicates
    return hou.ui.selectFromTree(choices, exclusive=exclusive)


def clamp(val, val_min, val_max):
    """
    Clamps val between val_min and val_max

    :param val: Value to be clamped
    :param val_min: Target minimum value for val
    :param val_max: Target maximum value for val
    :return: Clamped value
    """

    return min(val_max, max(val_min, val))


def houColorTo255(color):
    """
    Converts floating 0-1 hou.Color RGB to 0-255 int tuple RGB

    :param color: hou.Color
    :return: tuple(int, int, int)
    """

    return tuple(int(floor(clamp(float(c), 0, 1) * 255.99)) for c in color.rgb())


def rgb255to01(color):
    return tuple(clamp(float(c), 0, 255) / 255.0 for c in color)


def rgb255toHouColor(color):
    color = rgb255to01(color)
    return hou.Color(color[0], color[1], color[2])


class add_path:
    def __init__(self, path):
        self.path = path

    def __enter__(self):
        sys.path.insert(0, self.path)

    def __exit__(self, exc_type, exc_value, traceback):
        try:
            sys.path.remove(self.path)
        except ValueError:
            pass


def envListValues(name):
    value = hou.getenv(name, "").strip().strip("&").strip(";")
    return [val for val in value.split(";") if val]


def envAddValue(name, value):
    valueList = envListValues(name)
    valueList.append(value)
    finalString = ";".join(valueList)
    hou.putenv(name, finalString)
    return finalString


def treeItemToFullPath(item, column=0):
    """
    (Qt) Gets the full path of an item in QTreeWidget

    :param item: QTreeWidgetItem
    """
    path = item.text(column)
    while item.parent():
        path = item.parent().text(column) + "/" + path
        item = item.parent()
    return path
