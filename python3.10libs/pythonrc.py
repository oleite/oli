import sys
import os
import inspect
import re
import hou

oliRoot = inspect.getfile(inspect.currentframe()).replace('\\', '/')
oliRoot = re.sub(r'/python\d+\.\d+libs/pythonrc\.(py|pyc)', '', oliRoot)

iconsDirectory = oliRoot + "/icons"
galleryModelsDirectory = oliRoot + "/python2.7libs/oli/GalleryModels"

hou.putenv("OLI_ROOT", oliRoot)
hou.putenv("OLI_ICONS", iconsDirectory)

# ------------------------------ #

sys.path.append(oliRoot + "/python3.10libs")

from oli import utils
utils.envAddValue("OLI_GALLERY_MODELS_PATH", galleryModelsDirectory)

# ------------------------------ #

if hou.applicationVersion()[0] == 19:
    # =================================================================================
    # Workaround for Qt bug in Houdini 19.0.561 - Python 2
    # https://stackoverflow.com/questions/64737050/how-to-suppress-console-output-from-qwebengineview-errors
    os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] = "--enable-logging --log-level=3"
    # =================================================================================
