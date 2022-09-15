from imp import reload

import hou
import os
from oli import dragdrop


def dropAccept(files):
    reload(dragdrop)
    return dragdrop.dropAccept(files)