import os

from PySide6.QtCore import QObject, Signal, QRunnable, QThreadPool
from .DefaultModel import DefaultModel


class DataLoaderWorker(QRunnable):
    def __init__(self, signal, rootPath: str):
        super().__init__()
        self.signal = signal
        self.rootPath = rootPath

    def run(self):
        data = {"items": []}

        for fileName in os.listdir(self.rootPath):
            if not fileName.lower().endswith(".json"):
                filePath = os.path.join(self.rootPath, fileName)

                title = "_".join(fileName.split("_")[-2:])

                data["items"].append(
                    {
                        "title": title,
                        "localThumbnail": filePath,
                    }
                )

        self.signal.emit(data)


class ListModel(DefaultModel):

    def __init__(self, rootPaths: list[str]):
        super().__init__()
        self.rootPaths = rootPaths
        self.currentRootPath = rootPaths[0]

    def loadData(self):
        self.dataLoader = DataLoaderWorker(self.dataLoadedSignal, self.currentRootPath)
        self.threadPool.start(self.dataLoader)
