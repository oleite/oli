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

sys.path.append(tool_root + "/python2.7libs")