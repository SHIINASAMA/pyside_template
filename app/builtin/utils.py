from app.builtin.github_updater import GithubUpdater
from app.builtin.gitlab_updater import GitlabUpdater
import app.builtin.config as CFG

import sys
from pathlib import Path

from qdarktheme import enable_hi_dpi
from qasync import QApplication

def get_updater():
    match CFG.UPDATER_REMOTE_TYPE:
        case "GitHub":
            updater = GithubUpdater()
        case "GitLab":
            updater = GitlabUpdater()
        case _:
            raise ValueError(
                f"Unsupported updater remote type: {CFG.UPDATER_REMOTE_TYPE}"
            )
    updater.base_url = CFG.UPDATER_URL
    updater.project_name = CFG.UPDATER_PROJECT_NAME
    updater.app_name = CFG.UPDATER_APP_NAME
    return updater


def running_in_bundle() -> bool:
    if sys.platform != "darwin":
        return False

    exe_path = Path(sys.executable).resolve()
    return ".app/Contents/MacOS" in str(exe_path)


def init_app():
    # enable hdpi
    enable_hi_dpi()

    # init QApplication
    app = QApplication(sys.argv)
    app.setApplicationName(CFG.APP_NAME)
    app.setApplicationDisplayName(CFG.APP_DISPLAY_NAME)
    app.setOrganizationName(CFG.ORG_NAME)

    return app