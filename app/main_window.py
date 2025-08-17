import asyncio
import sys

from PySide6.QtCore import QTimer
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QMainWindow, QMessageBox
from qasync import asyncSlot
from app.resources.main_window_ui import Ui_MainWindow

# include the resource file
import app.resources.resource  # type: ignore


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowIcon(QIcon(':/assets/logo.png'))
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.ui.pushButton.clicked.connect(self.click_push_button)

        QTimer.singleShot(3, self.delay_task)

    def delay_task(self):
        if '--updated' in sys.argv:
            sys.argv.remove('--updated')
        else:
            # todo add a task to check for updates
            pass

    @asyncSlot()
    async def click_push_button(self):
        async def async_task():
            await asyncio.sleep(1)
            QMessageBox.information(
                self,
                self.tr("Hello"),
                self.tr("Hello World!"))

        self.ui.pushButton.setEnabled(False)
        await async_task()
        self.ui.pushButton.setEnabled(True)
