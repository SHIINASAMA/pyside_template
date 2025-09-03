import asyncio
import os

import app.resources.resource  # type: ignore
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QMessageBox, QMainWindow
from app.resources.main_window_ui import Ui_MainWindow
from httpx import HTTPError
from qasync import asyncSlot

from app.builtin.theme_manager import ThemeManager
from app.builtin.update import UpdateWidget


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.ui.pushButton.clicked.connect(self.click_push_button)

        ThemeManager.instance().setup_theme("auto")
        self.ui.themeComboBox.addItem(self.tr("Auto"), "auto")
        self.ui.themeComboBox.addItem(self.tr("Dark"), "dark")
        self.ui.themeComboBox.addItem(self.tr("Light"), "light")
        self.ui.themeComboBox.currentIndexChanged.connect(self.change_theme)
        self.ui.themeComboBox.setCurrentIndex(0)

        self.setWindowTitle(self.tr("MainWindow"))
        self.setWindowIcon(QIcon(':/logo.png'))

    async def async_init(self):
        from app.builtin.github_updater import GithubUpdater
        updater = GithubUpdater.instance()
        if os.getenv("DEBUG", "0") == "1":
            # Debug mode
            pass
        else:
            # Production mode
            if not updater.is_updated:
                try:
                    await updater.fetch()
                    if updater.check_for_update():
                        update_widget = UpdateWidget(self, updater)
                        await update_widget.show()
                        if update_widget.need_restart:
                            updater.apply_update()
                            self.close()
                except HTTPError:
                    QMessageBox.warning(
                        self,
                        self.tr("Warning"),
                        self.tr("Failed to check for updates"),
                    )
            else:
                QMessageBox.information(
                    self,
                    self.tr("Info"),
                    self.tr("Update completed"),
                )

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

    def change_theme(self, index):
        theme = self.ui.themeComboBox.itemData(index)
        ThemeManager.instance().setup_theme(theme)