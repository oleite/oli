import json
import os



from .GalleryViewModel import GalleryViewModel
from .models.FabModel import FabModel

window = None
vm = None

def openWindow(parent=None, model=None):
    global window
    global vm

    from PySide6.QtWidgets import QMainWindow

    if not model:
        model = FabModel()

    vm = GalleryViewModel(model=model, parent=parent)

    window = QMainWindow(parent=parent)
    window.setWindowTitle("oli Gallery")
    window.resize(800, 600)

    window.setCentralWidget(vm.view)

    return window