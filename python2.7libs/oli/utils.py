import imp
import os
import re
import shutil
import time
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
    path = os.path.normpath(path).replace("\\", "/")
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
        path = path.replace("\\", "/").replace("//", "/")
    else:
        path = ""
    return path


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