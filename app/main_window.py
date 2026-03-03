import asyncio
import os

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QMessageBox, QMainWindow
from qasync import asyncSlot
from qdarktheme import setup_theme

import app.resources.resource  # type: ignore
from app.resources.main_window_ui import Ui_MainWindow


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.ui.pushButton.clicked.connect(self.click_push_button)

        # ThemeManager.instance().setup_theme("auto")
        self.ui.themeComboBox.addItem(self.tr("Auto"), "auto")
        self.ui.themeComboBox.addItem(self.tr("Light"), "light")
        self.ui.themeComboBox.addItem(self.tr("Dark"), "dark")
        self.ui.themeComboBox.currentIndexChanged.connect(self.change_theme)
        self.ui.themeComboBox.setCurrentIndex(0)
        self.change_theme(0)

        self.setWindowTitle(self.tr("MainWindow"))
        self.setWindowIcon(QIcon(":/logo.png"))

    async def async_init(self):
        if os.getenv("DEBUG", "0") == "1":
            # Debug mode
            pass
        else:
            # Production mode
            await self.check_update()

    async def check_update(self):
        pass

    @asyncSlot()
    async def click_push_button(self):
        async def async_task():
            await asyncio.sleep(1)
            QMessageBox.information(self, self.tr("Hello"), self.tr("Hello World!"))

        self.ui.pushButton.setEnabled(False)
        await async_task()
        self.ui.pushButton.setEnabled(True)

    def change_theme(self, index):
        theme = self.ui.themeComboBox.itemData(index)
        setup_theme(theme)
