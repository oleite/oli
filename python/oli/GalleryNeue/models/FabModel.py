import os

from PySide6.QtCore import QObject, Signal, QRunnable, QThreadPool
from .DefaultModel import DefaultModel

import sqlite3


FAB_LIBRARY = r"M:\LIBRARY\VaultCache\FabLibrary"
FAB_LISTINGS = os.path.join(FAB_LIBRARY, "listings_v1.db")


class DataLoaderWorker(QRunnable):
    def __init__(self, signal):
        super().__init__()
        self.signal = signal

    def run(self):
        data = {"items": []}

        with sqlite3.connect(FAB_LISTINGS) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # Get all items from the catalog
            cursor.execute("SELECT * FROM catalog")
            rows = cursor.fetchall()
            data["items"] = [dict(row) for row in rows]

            # Get downloaded items
            cursor.execute("SELECT * FROM download_meta")
            for row in cursor.fetchall():
                uid = row["listing_uid"]

                for item in data["items"]:
                    if item["listing_uid"] == uid:
                        if not "downloads" in item:
                            item["downloads"] = []
                        item["downloads"].append(dict(row))

        self.signal.emit(data)


class FabModel(DefaultModel):
    def __init__(self):
        super().__init__()

    def loadData(self):
        self.dataLoader = DataLoaderWorker(self.dataLoadedSignal)
        self.threadPool.start(self.dataLoader)

    def thumbnailFunc(self, userData: dict):
        if not "downloads" in userData:
            return None

        for download in userData["downloads"]:
            return os.path.join(
                os.path.dirname(download["path"]), "thumbnail.jpeg"
            )