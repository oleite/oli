import os
import sys
import inspect
import hou

tool_root = inspect.getfile(inspect.currentframe()).replace('\\', '/')
tool_root = tool_root.replace('/python2.7libs/pythonrc.pyc', '').replace('/python2.7libs/pythonrc.py', '')
tool_root = tool_root.replace('/python3.7libs/pythonrc.pyc', '').replace('/python3.7libs/pythonrc.py', '')
tool_root = tool_root.replace('/python3.9libs/pythonrc.pyc', '').replace('/python3.9libs/pythonrc.py', '')

iconsDirectory = tool_root + "/icons"
galleryModelsDirectory = tool_root + "/python2.7libs/oli/GalleryModels"

hou.putenv("OLI_ROOT", tool_root)
hou.putenv("OLI_ICONS", iconsDirectory)

# ------------------------------ #

sys.path.append(tool_root + "/python2.7libs")

from oli import utils

utils.envAddValue("OLI_GALLERY_MODELS_PATH", galleryModelsDirectory)


# ------------------------------ #
