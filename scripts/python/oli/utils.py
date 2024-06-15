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


def centralizeNodes(selection, paneTab=None):
    """
    Repositions nodes to the center of the Houdini networkEditor.

    :param selection: List of 'hou.Node's.
    :return: hou.Vector2 of the target if operation successful.
    """
    if not selection:
        return None

    if not paneTab:
        paneTab = toolutils.networkEditor()
        if not paneTab:
            return None

    targetPos = paneTab.visibleBounds().center()

    first_pos = selection[0].position()
    for node in selection:
        if node.parentNetworkBox():
            continue
        node.move(targetPos - first_pos)

    wait(.1)
    paneTab.homeToSelection()
    return targetPos


def moveNodeToCursor(node, paneTab=None):
    if not paneTab:
        paneTab = toolutils.networkEditor()

    node.setPosition(paneTab.cursorPosition())
    node.move((-.5, -.2))
    
    
def moveNodesToCursor(nodes, paneTab=None):
    if not paneTab:
        paneTab = toolutils.networkEditor()

    offset = paneTab.cursorPosition() - nodes[0].position() + hou.Vector2((-.5, -.2))
    for node in nodes:
        node.move(offset)
        

def flashMessage(message, duration):
    """

    :param message:
    :param duration:
    :return:
    """
    toolutils.sceneViewer().flashMessage("", message, duration)
    toolutils.networkEditor().flashMessage("", message, duration)


def getGeometry(node):
    _type = type(node)
    if _type == hou.ObjNode and node.displayNode():
        geometry = node.displayNode().geometry()
    elif _type == hou.SopNode:
        geometry = node.geometry()
    elif _type == hou.Geometry:
        geometry = node
    else:
        return None
    return geometry
    

def getGeometryGlobal(node, mirror=True):
    _type = type(node)
    if _type == hou.ObjNode:
        sop = node.displayNode()
    elif _type == hou.SopNode:
        sop = node
    else:
        return None
    
    if not sop:
        return None

    temp = hou.node("/obj").createNode("geo", "temp")
    objMerge = temp.createNode("object_merge")
    objMerge.setParms({
        "objpath1": sop.path(),
        "xformtype": 1
    })
    out = objMerge
    if mirror:
        mirror = objMerge.createOutputNode("mirror")
        out = mirror

    geometry = hou.Geometry()
    geometry.copy(out.geometry())
    temp.destroy()
    return geometry


def cameraFrameGeometry(nodeOrGeometry, camera=None):
    """
    Frames the camera to the geometry.

    :param nodeOrGeometry: hou.Node (Sop or Obj) or hou.Geometry
    :param camera: Optional camera to be set as current.
    :return: hou.GeometryViewportCamera
    """
    geometry = getGeometryGlobal(nodeOrGeometry)
    if not geometry:
        geometry = getGeometry(nodeOrGeometry)
        if not geometry:
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


def selectAnyFromTree(path_list, picked=(), exclusive=True, message=None, title=None, clear_on_cancel=True, width=0, height=0):
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
    return hou.ui.selectFromTree(choices, picked, exclusive, message, title, clear_on_cancel, width, height)


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


def storeNodePos(node):
    pos = node.position()
    node.setUserData("posx", str(pos.x()))
    node.setUserData("posy", str(pos.y()))


def loadNodePos(node):
    posx = node.userData("posx")
    posy = node.userData("posy")
    if posx and posy:
        node.setPosition((float(posx), float(posy)))


def scaleWindow(windowSize, scaleFactor):
    """
    Scales a window to a given scale factor.
    
    :param windowSize: The size of the window to scale (width, height)
    :param scaleFactor: The scale factor to apply
    """

    width, height = windowSize
    scaledWidth = int(width * scaleFactor)
    scaledHeight = int(height * scaleFactor)
    position = ((width - scaledWidth) // 2, (height - scaledHeight) // 2)
    return position, (scaledWidth, scaledHeight)


def traverseUp(node, leafNodeTypes=[]):
    """
    Traverse up the network, returning a list of all connected nodes (including the start node)
    stopping at the first node that has no inputs or whose type is in leafNodeTypes.
    
    :param node: The node to start the traversal
    :param leafNodes: A list of node type names to stop at
    :return: Tuple of (nodes, leafNodes)
    """
    
    nodes = [node]
    leafNodes = []
    
    for inputNode in node.inputs():
        if not inputNode or inputNode.type().name() in leafNodeTypes:
            leafNodes.append(inputNode)
            continue
        
        n, l = traverseUp(inputNode, leafNodeTypes)
        nodes.extend(n)
        leafNodes.extend(l)
    
    return nodes, leafNodes


def alignConnectedUp(node):
    """
    Aligns all inputs in the node graph to the top of the node.
    """
    
    import nodegraphalign
    
    editor = toolutils.networkEditor()
    editor.setCurrentNode(node)
    nodegraphalign.alignConnected(editor, node, node.position(), "up")


def alignItemsUp(node, items):
    """
    Aligns selected items in the node graph to the top of the node.
    """
    
    import nodegraphalign
    
    if node not in items:
        items.append(node)
    
    editor = toolutils.networkEditor()
    editor.setCurrentNode(node)
    nodegraphalign.alignItems(editor, items, node, node.position(), "up")