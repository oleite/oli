import json

from PySide6.QtCore import QObject

from .models.DefaultModel import DefaultModel
from .GalleryView import GalleryView


class GalleryViewModel(QObject):
    def __init__(self, model: DefaultModel, parent=None):
        super().__init__(parent)
        self.model = model
        self.view = GalleryView()

        self.bindSignals()

        self.view.statusBar.showMessage("Loading data...")
        self.model.loadData()

    def bindSignals(self):
        self.model.dataLoadedSignal.connect(self.onDataLoaded)
        self.view.itemDoubleClickedSignal.connect(self.onItemDoubleClicked)

    def onDataLoaded(self, data: dict):
        self.view.assetList.clear()

        def thumbnailFunc(userData: dict):
            return userData.get("localThumbnail", None)

        if hasattr(self.model, "thumbnailFunc"):
            thumbnailFunc = getattr(self.model, "thumbnailFunc")

        for item in data.get("items", []):
            self.view.addItem(
                title=item.get("title", "Untitled"),
                tooltip=item.get("description", ""),
                userData=item,
                thumbnailFunc=thumbnailFunc,
            )

        self.view.statusBar.showMessage(
            f"Loaded {len(data.get('items', []))} items.", 2000
        )

    def onItemDoubleClicked(self, userData: dict):
        from . import openWindow
        from .models.ListModel import ListModel

        if "downloads" in userData:
            rootPaths = [d["path"] for d in userData["downloads"]]

            list = GalleryViewModel(model=ListModel(rootPaths=rootPaths), parent=self)
            list.view.setWindowTitle(userData["title"])
            list.view.resize(700, 400)
            list.view.show()

        elif userData.get("localThumbnail"):
            import os
            from PySide6.QtCore import QUrl
            from PySide6.QtGui import QDesktopServices

            QDesktopServices.openUrl(QUrl.fromLocalFile(userData["localThumbnail"]))
