import os
import sys
import inspect
import hou

tool_root = inspect.getfile(inspect.currentframe()).replace('\\', '/')
tool_root = tool_root.replace('/python2.7libs/pythonrc.pyc', '').replace('/python2.7libs/pythonrc.py', '')
tool_root = tool_root.replace('/python3.7libs/pythonrc.pyc', '').replace('/python3.7libs/pythonrc.py', '')

images_directory = tool_root + "/icons"
hou.putenv("OLI_ICONS", images_directory)
hou.putenv("OLI_ROOT", tool_root)


if hou.applicationVersion()[0] == 19:
    # =================================================================================
    # Workaround for Qt bug in Houdini 19.0.561 - Python 2
    # https://stackoverflow.com/questions/64737050/how-to-suppress-console-output-from-qwebengineview-errors
    os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] = "--enable-logging --log-level=3"
    # =================================================================================
