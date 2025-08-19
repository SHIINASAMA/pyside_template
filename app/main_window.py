import asyncio
import logging

from PySide6.QtCore import QTimer
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QMainWindow, QMessageBox
from httpx import HTTPError
from qasync import asyncSlot, asyncClose

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

        QTimer.singleShot(0, lambda: asyncio.create_task(self.delay_task()))

    @asyncClose
    async def closeEvent(self, event):
        pass

    async def delay_task(self):
        updater = Updater.instance()
        if not updater.is_updated:
            try:
                await updater.get_latest_release_via_gitlab(
                    base_url="https://gitlab.mikumikumi.xyz/",
                    project_name="pyside_template",
                )
                update_widget = UpdateWidget(self, updater)
                # todo when click cancel button to close the dialog and close parent window, program will crash with:
                # Exception ignored in: <function _ProactorBasePipeTransport.__del__ at 0x00000216F5C668B0>
                # Traceback (most recent call last):
                #   File "C:\Users\kaoru\AppData\Roaming\uv\python\cpython-3.8.20-windows-x86_64-none\lib\asyncio\proactor_events.py", line 116, in __del__
                #   File "C:\Users\kaoru\AppData\Roaming\uv\python\cpython-3.8.20-windows-x86_64-none\lib\asyncio\proactor_events.py", line 108, in close
                #   File "D:\workspaces\pyside_template\.venv\lib\site-packages\qasync\__init__.py", line 481, in call_soon
                #   File "D:\workspaces\pyside_template\.venv\lib\site-packages\qasync\__init__.py", line 471, in call_later
                #   File "D:\workspaces\pyside_template\.venv\lib\site-packages\qasync\__init__.py", line 477, in _add_callback
                #   File "D:\workspaces\pyside_template\.venv\lib\site-packages\qasync\__init__.py", line 255, in add_callback
                # RuntimeError: Internal C++ object (_SimpleTimer) already deleted.
                update_widget.exec()
            except HTTPError as e:
                QMessageBox.warning(
                    self,
                    self.tr("Warning"),
                    self.tr("Failed to check for updates"),
                )
            except SystemExit:
                self.close()

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
