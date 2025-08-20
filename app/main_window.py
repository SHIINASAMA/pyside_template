import asyncio

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QMainWindow, QMessageBox
from httpx import HTTPError
from qasync import asyncSlot

# include the resource file
import app.resources.resource  # type: ignore
from app.resources.main_window_ui import Ui_MainWindow
from app.builtin.update import Updater, UpdateWidget


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowIcon(QIcon(':/assets/logo.png'))
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.ui.pushButton.clicked.connect(self.click_push_button)

    async def async_init(self):
        updater = Updater.instance()
        if not updater.is_updated:
            try:
                await updater.get_latest_release_via_gitlab(
                    base_url="https://gitlab.mikumikumi.xyz/",
                    project_name="pyside_template",
                )
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
