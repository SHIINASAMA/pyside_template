from app.builtin.github_updater import GithubUpdater
from app.builtin.gitlab_updater import GitlabUpdater
import app.builtin.config as cfg

import sys
import platform
from pathlib import Path

from qdarktheme import enable_hi_dpi
from PySide6.QtWidgets import QApplication


def get_updater():
    match cfg.UPDATER_REMOTE_TYPE:
        case "GitHub":
            updater = GithubUpdater()
        case "GitLab":
            updater = GitlabUpdater()
        case _:
            raise ValueError(
                f"Unsupported updater remote type: {cfg.UPDATER_REMOTE_TYPE}"
            )
    updater.base_url = cfg.UPDATER_URL
    updater.project_name = cfg.UPDATER_PROJECT_NAME
    updater.app_name = cfg.UPDATER_APP_NAME
    return updater


def running_in_bundle() -> bool:
    if sys.platform != "darwin":
        return False

    exe_path = Path(sys.executable).resolve()
    return ".app/Contents/MacOS" in str(exe_path)


def get_sysname() -> str:
    sysname = platform.system().lower()
    if sysname == "windows":
        sysname = "windows"
    elif sysname == "darwin":
        sysname = "macos"
    elif sysname == "linux":
        sysname = "linux"
    else:
        raise RuntimeError(f"Unknown system: {sysname}")
    return sysname


def get_arch() -> str:
    arch = platform.machine().lower()
    if arch in ["x86_64", "amd64"]:
        arch = "x64"
    elif arch in ["aarch64", "arm64"]:
        arch = "arm64"
    else:
        raise RuntimeError(f"Unknown architecture: {arch}")
    return arch


def init_app():
    # enable hdpi
    enable_hi_dpi()

    # init QApplication
    app = QApplication(sys.argv)
    app.setApplicationName(cfg.APP_NAME)
    app.setApplicationDisplayName(cfg.APP_DISPLAY_NAME)
    app.setOrganizationName(cfg.ORG_NAME)

    return app
