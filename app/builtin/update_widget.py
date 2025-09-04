import os

from PySide6.QtCore import Qt
from qasync import asyncSlot

from app.builtin.async_widget import AsyncWidget
from app.builtin.asyncio import to_thread
from app.builtin.update import Updater
from app.resources.builtin.update_widget_ui import Ui_UpdateWidget


class UpdateWidget(AsyncWidget):
    """
    If the update resource is downloaded and extracted successfully,
    the application can call `Updater.apply_update()` and close itself
    to restart with the new version.
    """
    need_restart: bool

    def __init__(self, parent, updater: Updater):
        super().__init__(parent)
        self.updater = updater
        self.need_restart = False
        flags = self.windowFlags()
        flags = flags | Qt.WindowType.Window
        flags = flags & ~Qt.WindowType.WindowMaximizeButtonHint
        flags = flags & ~Qt.WindowType.WindowMinimizeButtonHint
        flags = flags & ~Qt.WindowType.WindowCloseButtonHint
        self.setWindowFlags(flags)
        self.ui = Ui_UpdateWidget()
        self.ui.setupUi(self)

        self.ui.label.setText(self.tr("Found new version: {}").format(self.updater.remote_version))
        self.ui.textBrowser.setMarkdown(self.updater.description)

        self.ui.cancel_btn.clicked.connect(self.on_cancel)
        self.ui.update_btn.clicked.connect(self.on_update)

    def on_cancel(self):
        self.close()

    @asyncSlot()
    async def on_update(self):
        self.ui.cancel_btn.setEnabled(False)
        self.ui.update_btn.setEnabled(False)
        self.ui.label.setText(self.tr("Downloading new version..."))
        await self.download()
        self.ui.progressBar.setRange(0, 0)

        self.ui.label.setText(self.tr("Extracting new version..."))
        await to_thread(self.extract)
        self.need_restart = True
        self.close()

    async def download(self):
        async with self.updater.create_async_client() as client:
            async with client.stream("GET", self.updater.download_url, follow_redirects=True) as r:
                r.raise_for_status()
                total_size = int(r.headers.get("content-length", 0))
                downloaded = 0

                with open(self.updater.filename, "wb") as f:
                    async for chunk in r.aiter_bytes(8192):
                        f.write(chunk)
                        downloaded += len(chunk)

                        percent = int(downloaded * 100 / total_size)
                        self.ui.progressBar.setValue(percent)

    def extract(self):
        if self.updater.filename.endswith(".zip"):
            import zipfile
            with zipfile.ZipFile(self.updater.filename, 'r') as zip_ref:
                zip_ref.extractall(os.path.dirname(self.updater.filename))
        elif self.updater.filename.endswith(".tar.gz") or self.updater.filename.endswith(".tgz"):
            import tarfile
            with tarfile.open(self.updater.filename, 'r:gz') as tar_ref:
                tar_ref.extractall(os.path.dirname(self.updater.filename))
        else:
            raise RuntimeError(f"Unsupported file format: {self.updater.filename}")
        # remove the downloaded file
        os.remove(self.updater.filename)
