import os
import sys
import inspect
import hou
from oli import utils


tool_root = inspect.getfile(inspect.currentframe()).replace('\\', '/')
tool_root = tool_root.replace('/python2.7libs/pythonrc.pyc', '').replace('/python2.7libs/pythonrc.py', '')
tool_root = tool_root.replace('/python3.7libs/pythonrc.pyc', '').replace('/python3.7libs/pythonrc.py', '')

iconsDirectory = tool_root + "/icons"
galleryModelsDirectory = tool_root + "/python2.7libs/oli/GalleryModels"

hou.putenv("OLI_ROOT", tool_root)
hou.putenv("OLI_ICONS", iconsDirectory)
utils.envAddValue("OLI_GALLERY_MODELS_PATH", galleryModelsDirectory)


# ------------------------------ #


if hou.applicationVersion()[0] == 19:
    # =================================================================================
    # Workaround for Qt bug in Houdini 19.0.561 - Python 2
    # https://stackoverflow.com/questions/64737050/how-to-suppress-console-output-from-qwebengineview-errors
    os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] = "--enable-logging --log-level=3"
    # =================================================================================
