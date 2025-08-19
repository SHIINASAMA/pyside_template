import enum
import os
import shutil
import subprocess
import sys
from pathlib import Path
from time import sleep
from urllib.parse import urlparse

import packaging.version as Version0
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialog
from httpx import AsyncClient
from qasync import asyncSlot

from app.resources.builtin.update_dialog_ui import Ui_UpdateDialog
from app.builtin.asyncio import to_thread


class ReleaseType(enum.Enum):
    STABLE = "stable"
    BETA = "beta"


class Version(Version0.Version):
    def __init__(self, version_string: str):
        version_part = version_string.split('-')
        super().__init__(version_part[0])
        if len(version_part) == 1:
            self.release_type = ReleaseType.STABLE
            return
        if version_part[1] == "beta":
            self.release_type = ReleaseType.BETA
        elif version_part[1] == "stable":
            self.release_type = ReleaseType.STABLE
        else:
            raise RuntimeError(f"Unknown release type: {version_part[1]}")

    def __str__(self):
        return f"{super().__str__()}-{self.release_type.value}"

    def get_number_version(self):
        """Get the version as a tuple of integers."""
        return super().__str__()


class UpdateWidget(QDialog):
    def __init__(self, parent, updater):
        super().__init__(parent)
        self.updater = updater
        flags = self.windowFlags()
        flags = flags | Qt.WindowType.Window
        flags = flags & ~Qt.WindowMaximizeButtonHint
        flags = flags & ~Qt.WindowMinimizeButtonHint
        flags = flags & ~Qt.WindowCloseButtonHint
        self.setWindowFlags(flags)
        self.setWindowModality(Qt.ApplicationModal)
        self.ui = Ui_UpdateDialog()
        self.ui.setupUi(self)

        self.ui.label.setText(self.tr("Found new version: {}").format(self.updater.remote_version))
        self.ui.textBrowser.setMarkdown(self.updater.description)

        path = urlparse(self.updater.download_url).path
        self.filename = os.path.basename(path)

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
        # Tell Package/App.exe to copy itself
        subprocess.run(
            ['Package/App.exe', "--copy-self"],
            creationflags=subprocess.DETACHED_PROCESS | subprocess.SW_HIDE
        )
        raise SystemExit(0)

    async def download(self):
        async with self.updater.client.stream("GET", self.updater.download_url) as r:
            r.raise_for_status()
            total_size = int(r.headers.get("content-length", 0))
            downloaded = 0

            with open(self.filename, "wb") as f:
                async for chunk in r.aiter_bytes(8192):
                    f.write(chunk)
                    downloaded += len(chunk)

                    percent = int(downloaded * 100 / total_size)
                    self.ui.progressBar.setValue(percent)

    def extract(self):
        if self.filename.endswith(".zip"):
            import zipfile
            with zipfile.ZipFile(self.filename, 'r') as zip_ref:
                zip_ref.extractall(os.path.dirname(self.filename))
        elif self.filename.endswith(".tar.gz") or self.filename.endswith(".tgz"):
            import tarfile
            with tarfile.open(self.filename, 'r:gz') as tar_ref:
                tar_ref.extractall(os.path.dirname(self.filename))
        else:
            raise RuntimeError(f"Unsupported file format: {self.filename}")


class Updater:
    _copy_self_cmd = "--copy-self"
    _updated_cmd = "--updated"

    _instance = None

    def __new__(cls, release_type: ReleaseType):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, release_type: ReleaseType):
        if not self._initialized:
            self.client = AsyncClient()
            self.release_type = release_type
            self.remote_version = None
            self.description = ""
            self.download_url = ""

            self.is_updated = False
            if Updater._copy_self_cmd in sys.argv:
                sys.argv.remove(Updater._copy_self_cmd)
                # wait for last executable to exit
                Updater.copy_self_and_exit()
            if Updater._updated_cmd in sys.argv:
                sys.argv.remove(Updater._updated_cmd)
                # only store that we have updated
                self.is_updated = True
                Updater.clean_old_package()

            self.get_current_version()

            self._initialized = True

    @staticmethod
    def instance():
        return Updater._instance

    async def get_latest_release_via_gitlab(self, base_url: str, project_name: str, timeout: int = 5):
        url = f"{base_url}/api/v4/projects/?search={project_name}"
        r = await self.client.get(url, timeout=timeout)
        r.raise_for_status()
        project = r.json()[0]
        project_id = project['id']

        url = f"{base_url}/api/v4/projects/{project_id}/releases"
        headers = {}
        params = {"per_page": 1}
        r = await self.client.get(url, headers=headers, params=params, timeout=timeout)
        r.raise_for_status()
        latest_release = r.json()[0]
        self.remote_version = Version(latest_release['tag_name'])
        self.description = latest_release['description']
        self.download_url = f"{base_url}/api/v4/projects/{project_id}/packages/generic/App/{self.remote_version}/Package.tar.gz"

    def get_current_version(self):
        # force set version from version.txt if it exists
        if os.path.exists("version.txt"):
            with open("version.txt", "r", encoding="utf-8") as f:
                version_string = f.read().strip()
            ver = Version(version_string)
            self.current_version = ver
            self.release_type = ver.release_type  # set release type from version
            return
        # get version from app
        if sys.platform == "win32":
            self.current_version = self.get_version_win32(sys.executable)
        else:
            raise RuntimeError(f"Unknown platform: {sys.platform}")

    @staticmethod
    def get_version_win32(filename: str) -> Version:
        import ctypes
        from ctypes import wintypes
        size = ctypes.windll.version.GetFileVersionInfoSizeW(filename, None)
        if not size:
            return None

        res = ctypes.create_string_buffer(size)
        ctypes.windll.version.GetFileVersionInfoW(filename, 0, size, res)

        lplpBuffer = ctypes.c_void_p()
        puLen = wintypes.UINT()
        ctypes.windll.version.VerQueryValueW(res, "\\", ctypes.byref(lplpBuffer), ctypes.byref(puLen))

        ffi = ctypes.cast(lplpBuffer, ctypes.POINTER(ctypes.c_uint16 * (puLen.value // 2))).contents
        ms = ffi[5], ffi[4]
        ls = ffi[7], ffi[6]
        return Version(f"{ms[0]}.{ms[1]}.{ls[0]}.{ls[1]}")

    def check_for_updates(self):
        return (self.release_type == self.remote_version.release_type
                and self.remote_version > self.current_version)

    @staticmethod
    def copy_self_and_exit():
        """Copy current executable to parent directory and run it with --updated argument."""
        # Wait for the last executable to exit
        sleep(3)

        parent_dir = Path(sys.executable).parent.parent
        current_dir = Path(sys.executable).parent
        filelist = parent_dir / "filelist.txt"
        # delete files by ../filelist.txt if it exists, workdir is parent directory
        if filelist.exists():
            with open(filelist, "r", encoding="utf-8") as f:
                for line in f:
                    path = line.strip()
                    if not path:
                        continue
                    abs_path = parent_dir / path
                    try:
                        if abs_path.is_file():
                            abs_path.unlink()
                        elif abs_path.is_dir():
                            shutil.rmtree(abs_path)
                    except Exception:
                        continue

        # Copy current directory to parent directory
        for item in current_dir.iterdir():
            target = parent_dir / item.name
            try:
                if item.is_file():
                    shutil.copy2(item, target)
                elif item.is_dir():
                    if target.exists():
                        shutil.rmtree(target)
                    shutil.copytree(item, target)
            except Exception:
                continue

        # Run copied executable with --updated argument
        new_executable = Path(sys.executable).parent.parent / "App.exe"
        subprocess.run(
            [new_executable, "--updated"],
            creationflags=subprocess.DETACHED_PROCESS
        )
        sys.exit(0)

    @staticmethod
    def clean_old_package():
        """delete "Package" directory"""
        sleep(3)
        package_dir = Path(sys.executable).parent / "Package"
        if package_dir.exists() and package_dir.is_dir():
            shutil.rmtree(package_dir, ignore_errors=True)
