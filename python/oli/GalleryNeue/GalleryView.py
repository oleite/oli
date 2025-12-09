import os

from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *


ICONS_PATH = os.path.join(os.getenv("OLI_ROOT", ""), "houdini/icons")
if not os.path.exists(ICONS_PATH):
    raise FileNotFoundError(f"Icons path not found: {ICONS_PATH}")


class ImageLoaderWorker(QRunnable):
    # Cant use Pixmaps in threads other than the main thread, so we use Images
    def __init__(self, thumbnailFunc, userData, signal, item: QListWidgetItem):
        super().__init__()
        self.thumbnailFunc = thumbnailFunc
        self.userData = userData
        self.signal = signal
        self.item = item

    def run(self):
        imagePath = self.thumbnailFunc(self.userData)

        if not imagePath:
            return
        if not os.path.exists(imagePath):
            print(f"Error: Thumbnail path does not exist: {imagePath}")
            return

        targetSize = QSize(500, 500)
        image = QImage(imagePath)
        if image.isNull():
            print(f"Failed to load image: {imagePath}")
            return

        # We want the equivalent of CSS's 'background-size: cover'
        imgSize = image.size()
        imgAspect = imgSize.width() / imgSize.height()
        targetAspect = targetSize.width() / targetSize.height()
        if imgAspect > targetAspect:
            # Image is wider than target, crop width
            newHeight = imgSize.height()
            newWidth = int(newHeight * targetAspect)
        else:
            # Image is taller than target, crop height
            newWidth = imgSize.width()
            newHeight = int(newWidth / targetAspect)
        xOffset = (imgSize.width() - newWidth) // 2
        yOffset = (imgSize.height() - newHeight) // 2
        cropped = image.copy(xOffset, yOffset, newWidth, newHeight)
        scaled = cropped.scaled(targetSize, Qt.KeepAspectRatio, Qt.SmoothTransformation)

        self.signal.emit(self.item, scaled, imagePath)


class GalleryView(QWidget):
    imageLoadedSignal = Signal(QListWidgetItem, QImage, str)
    itemDoubleClickedSignal = Signal(dict)

    def __init__(self):
        super().__init__()

        self.defaultThumbIcon = QIcon(os.path.join(ICONS_PATH, "default_thumbnail.png"))

        self.threadPool = QThreadPool()

        self.setupUi()
        self.bindSignals()
        self.setThumbnailSize(128)

    def setupUi(self):
        self.widgetLayout = QVBoxLayout(self)
        self.widgetLayout.setContentsMargins(0, 0, 0, 0)

        self.thumbnailSizeSlider = QSlider(Qt.Horizontal, self)
        self.thumbnailSizeSlider.setObjectName("thumbnailSizeSlider")
        self.thumbnailSizeSlider.setMinimum(50)
        self.thumbnailSizeSlider.setMaximum(500)
        self.thumbnailSizeSlider.setToolTip("Changes the thumbnail sizes")
        self.widgetLayout.addWidget(self.thumbnailSizeSlider)

        self.assetList = QListWidget(self)
        self.assetList.setObjectName("assetList")
        self.assetList.setViewMode(QListView.IconMode)
        self.assetList.setResizeMode(QListView.Adjust)
        self.assetList.setMovement(QListView.Static)
        self.assetList.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.assetList.setDragEnabled(True)
        self.assetList.setAcceptDrops(True)
        self.assetList.setGridSize(QSize(100, 100))
        self.widgetLayout.addWidget(self.assetList)

        self.statusBar = QStatusBar(self)
        self.widgetLayout.addWidget(self.statusBar)

    def bindSignals(self):
        self.imageLoadedSignal.connect(self.onImageLoaded)
        self.assetList.itemDoubleClicked.connect(self._onItemDoubleClicked)
        self.thumbnailSizeSlider.valueChanged.connect(self._setThumbnailSize)

    def _onItemDoubleClicked(self, item):
        data = item.data(Qt.UserRole)
        self.itemDoubleClickedSignal.emit(data)

    def addItem(
        self,
        title: str,
        tooltip: str = "",
        userData: dict = {},
        thumbnailFunc=None,
    ):
        listItem = QListWidgetItem(self.defaultThumbIcon, title)
        listItem.setData(Qt.UserRole, userData)

        if thumbnailFunc:
            imageLoader = ImageLoaderWorker(
                thumbnailFunc=thumbnailFunc, 
                userData=userData, 
                signal=self.imageLoadedSignal,
                item=listItem,
            )
            self.threadPool.start(imageLoader)

        if tooltip:
            listItem.setToolTip(tooltip)

        self.assetList.addItem(listItem)

    def onImageLoaded(self, item: QListWidgetItem, image: QImage, imagePath: str):
        pixmap = QPixmap.fromImage(image)
        icon = QIcon(pixmap)
        item.setIcon(icon)

        userData = item.data(Qt.UserRole)
        userData["localThumbnail"] = imagePath
        item.setData(Qt.UserRole, userData)

    def setThumbnailSize(self, size: int):
        self.thumbnailSizeSlider.setValue(size)

    def _setThumbnailSize(self, size: int):
        font_h = self.assetList.fontMetrics().height()

        self.assetList.setIconSize(QSize(size, size))
        self.assetList.setGridSize(QSize(size, size + font_h))
