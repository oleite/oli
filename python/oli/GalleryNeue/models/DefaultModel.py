from PySide6.QtCore import QObject, Signal, QThreadPool


class DefaultModel(QObject):
    dataLoadedSignal = Signal(dict)

    def __init__(self):
        super().__init__()
        self._data = {}

        self.threadPool = QThreadPool()
        self.dataLoadedSignal.connect(self.setData)

    def loadData(self):
        pass

    def getData(self):
        return self._data

    def setData(self, data: dict):
        self._data = data
