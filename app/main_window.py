import asyncio
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QMainWindow, QMessageBox
from qasync import asyncSlot, QApplication
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

    @asyncSlot()
    async def click_push_button(self):
        async def async_task():
            await asyncio.sleep(1)
            QMessageBox.information(
                self,
                self.tr("Hello"),
                self.tr("Hello World!"))

        self.ui.pushButton.setEnabled(False)
        await asyncio.ensure_future(async_task())
        self.ui.pushButton.setEnabled(True)
