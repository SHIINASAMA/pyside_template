import enum
import json
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path
from time import sleep
from urllib.parse import urlparse

import packaging.version as Version0
from PySide6.QtCore import Qt
from glom import glom

from app.resources.builtin.update_widget_ui import Ui_UpdateWidget
from httpx import AsyncClient
from qasync import asyncSlot

from app.builtin.version import __version__
from app.builtin.async_widget import AsyncWidget
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


class UpdateWidget(AsyncWidget):
    """
    If the update resource is downloaded and extracted successfully,
    the application can call `Updater.apply_update()` and close itself
    to restart with the new version.
    """
    need_restart: bool

    def __init__(self, parent, updater):
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
        self.need_restart = True
        self.close()

    async def download(self):
        async with AsyncClient(proxy=Updater.instance().proxy) as client:
            async with client.stream("GET", self.updater.download_url) as r:
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
        # remove the downloaded file
        os.remove(self.filename)


class Updater:
    _copy_self_cmd = "--copy-self"
    _updated_cmd = "--updated"

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if not self._initialized:
            # Three attributes can be set by updater.json
            self.current_version = Updater._load_current_version()
            self.release_type = self.current_version.release_type
            self.proxy = None

            self.remote_version = None
            self.description = ""
            self.download_url = ""

            self.is_updated = False
            if Updater._copy_self_cmd in sys.argv:
                sys.argv.remove(Updater._copy_self_cmd)
                Updater.copy_self_and_exit()
            if Updater._updated_cmd in sys.argv:
                sys.argv.remove(Updater._updated_cmd)
                self.is_updated = True
                Updater.clean_old_package()

            self._initialized = True

    def load_from_file_and_override(self, filename: str):
        """Load updater configuration from a JSON file."""
        with open(filename, "r", encoding="utf-8") as f:
            data = json.load(f)

        version: str = data.get('version', None)
        if version is not None:
            self.current_version = Version(version)
        self.proxy = data.get('proxy', None)
        self.release_type = ReleaseType(data.get('channel', 'stable'))

    @staticmethod
    def instance():
        return Updater._instance

    async def fetch_latest_release_via_gitlab(self, base_url: str, project_name: str, timeout: int = 5):
        async with AsyncClient(proxy=self.proxy) as client:
            r = await client.get(
                url=f"{base_url}/api/v4/projects",
                params={"search": project_name,
                        "search_namespaces": "true"},
                timeout=timeout
            )
            r.raise_for_status()
            projects = r.json()
            if not projects:
                raise FileNotFoundError(f"Project {project_name} not found on GitLab: {base_url}")
            project = projects[0]
            project_id = project['id']
            r = await client.get(
                url=f"{base_url}/api/v4/projects/{project_id}/releases",
                headers={},
                params={"per_page": 1},
                timeout=timeout
            )
            r.raise_for_status()

            releases = []
            for release in r.json():
                version = Version(release['tag_name'])
                if version.release_type == self.release_type:
                    releases.append(release)
            latest_release = max(releases, key=lambda x: Version(x['tag_name']), default=None)
            if latest_release is None:
                # Does have any release for this channel
                self.remote_version = Version('0.0.0.0')
                return

            self.remote_version = Version(latest_release['tag_name'])
            self.description = latest_release['description']

            arch = platform.machine().lower()
            if arch in ['x86_64', 'amd64']:
                arch = 'amd64'
            elif arch in ['aarch64', 'arm64']:
                arch = 'arm64'
            else:
                raise RuntimeError(f"Unknown architecture: {arch}")

            sysname = platform.system().lower()
            if sysname == 'windows':
                sysname = 'windows'
                package_name = f"Package_{arch}_{sysname}"
            elif sysname == 'darwin':
                sysname = 'macos'
                package_name = f"Package_{arch}_{sysname}"
            elif sysname == 'linux':
                sysname = 'linux'
                package_name = f"Package_{arch}_{sysname}"
            else:
                raise RuntimeError(f"Unknown system: {sysname}")

            self.download_url = None
            for link in glom(release, 'assets.links', default={}):
                if link['name'] == package_name:
                    self.download_url = link['url']
            if self.download_url is None:
                raise FileNotFoundError(f"Package {package_name} not found in release assets.")

            r = await client.head(url=self.download_url)
            r.raise_for_status()

    @staticmethod
    def _load_current_version():
        """Get version from app"""
        return Version(__version__)

    def check_for_update(self):
        return (self.release_type == self.remote_version.release_type
                and self.remote_version > self.current_version)

    @staticmethod
    def apply_update():
        """
        Call Package/App.exe to copy itself to parent directory and run it.
        You must exit the current process after calling this.
        Because this function be called in GUI thread.
        """
        if sys.platform == "win32":
            subprocess.Popen(
                ['Package/App.exe', Updater._copy_self_cmd],
                creationflags=subprocess.DETACHED_PROCESS,
                env=os.environ.copy()
            )
        else:
            subprocess.Popen(
                ['Package/App', Updater._copy_self_cmd],
                preexec_fn=os.setpgrp,
                env=os.environ.copy()
            )

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
        if sys.platform == "win32":
            new_executable = Path(sys.executable).parent.parent / "App.exe"
            subprocess.Popen(
                [new_executable, "--updated"],
                creationflags=subprocess.DETACHED_PROCESS,
                env=os.environ.copy()
            )
        else:
            new_executable = Path(sys.executable).parent.parent / "App"
            subprocess.Popen(
                [new_executable, "--updated"],
                preexec_fn=os.setpgrp,
                env=os.environ.copy()
            )
        sys.exit(0)

    @staticmethod
    def clean_old_package():
        """Delete Package directory"""
        sleep(3)
        package_dir = Path(sys.executable).parent / "Package"
        if package_dir.exists() and package_dir.is_dir():
            shutil.rmtree(package_dir, ignore_errors=True)
