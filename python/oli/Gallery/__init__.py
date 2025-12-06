import json
import os



from .GalleryModel import GalleryModel
from .GalleryViewModel import GalleryViewModel

window = None

def openWindow(parent=None, settings={}):
    global window

    from PySide6.QtWidgets import QMainWindow

    vm = GalleryViewModel()

    window = QMainWindow(parent=parent)
    window.setWindowTitle("oli Gallery")
    window.resize(622, 402)

    window.setCentralWidget(vm.view)

    return window
