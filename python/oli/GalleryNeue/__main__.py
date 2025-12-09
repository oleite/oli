import sys
from . import openWindow
import signal

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer


def debugWindow():
    app = QApplication(sys.argv)

    window = openWindow()
    window.show()

    if "loadStyleSheets" in dir(window):
        print("Stylesheet reloading enabled")
        timer = QTimer()
        timer.timeout.connect(window.loadStyleSheets)
        timer.start(1000)

    # Set the signal handler for SIGINT to the default handler to allow graceful termination with Ctrl+C
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    sys.exit(app.exec())

if __name__ == "__main__":
    debugWindow()