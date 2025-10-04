import enum
import json
import os
import shutil
import subprocess
import sys
from abc import abstractmethod, ABC
from pathlib import Path
from time import sleep

import packaging.version as Version0
from httpx import AsyncClient
from app.resources.version import __version__


class ReleaseType(enum.Enum):
    STABLE = "stable"
    BETA = "beta"
    ALPHA = "alpha"
    DEV = "dev"
    NIGHTLY = "nightly"


class Version(Version0.Version):
    def __init__(self, version_string: str):
        version_part = version_string.split('-')
        super().__init__(version_part[0])
        if len(version_part) == 1:
            self.release_type = ReleaseType.STABLE
            return
        if version_part[1] == "stable":
            self.release_type = ReleaseType.STABLE
        elif version_part[1] == "beta":
            self.release_type = ReleaseType.BETA
        elif version_part[1] == "alpha":
            self.release_type = ReleaseType.ALPHA
        elif version_part[1] == "dev":
            self.release_type = ReleaseType.DEV
        elif version_part[1] == "nightly":
            self.release_type = ReleaseType.NIGHTLY
        else:
            raise RuntimeError(f"Unknown release type: {version_part[1]}")

    def __str__(self):
        return f"{super().__str__()}-{self.release_type.value}"

    def get_number_version(self):
        """Get the version as a tuple of integers."""
        return super().__str__()


class Updater(ABC):
    _copy_self_cmd = "--updater-copy-self"
    _updated_cmd = "--updater-updated"
    _disable_cmd = "--updater-disable"

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

            # must set in self.fetch()
            self.remote_version = None
            self.description = ""
            self.download_url = ""
            self.filename = ""

            self.is_updated = False
            self.is_enable = True
            if Updater._copy_self_cmd in sys.argv:
                sys.argv.remove(Updater._copy_self_cmd)
                Updater.copy_self_and_exit()
            if Updater._updated_cmd in sys.argv:
                sys.argv.remove(Updater._updated_cmd)
                self.is_updated = True
                Updater.clean_old_package()
            if Updater._disable_cmd in sys.argv:
                sys.argv.remove(Updater._disable_cmd)
                self.is_enable = False

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

    @abstractmethod
    def create_async_client(self) -> AsyncClient:
        pass

    @abstractmethod
    async def fetch(self):
        pass

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
