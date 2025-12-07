import asyncio
import os.path
import sys

from PySide6.QtCore import QTranslator, QLocale, QLockFile
from qasync import QApplication, run

from app.builtin.gitlab_updater import GitlabUpdater
from app.builtin.locale import detect_system_ui_language
from app.main_window import MainWindow
from qdarktheme import enable_hi_dpi


async def task():
    app_close_event = asyncio.Event()
    app = QApplication.instance()
    assert isinstance(app, QApplication)
    app.aboutToQuit.connect(app_close_event.set)

    main_window = MainWindow()
    main_window.show()
    await main_window.async_init()
    await app_close_event.wait()


def main(enable_updater: bool = True):
    # init updater, updater will remove some arguments
    # and do update logic
    # updater = GithubUpdater()
    # updater.project_name = "SHIINASAMA/pyside_template"
    updater = GitlabUpdater()
    updater.base_url = "https://gitlab.mikumikumi.xyz"
    updater.project_name = "kaoru/pyside_template"
    updater.is_enable = enable_updater

    # check if the app is already running
    lock_file = QLockFile("App.lock")
    if not lock_file.lock():
        sys.exit(0)

    if os.path.exists("updater.json"):
        updater.load_from_file_and_override("updater.json")

    # enable hdpi
    enable_hi_dpi()

    # init QApplication
    app = QApplication(sys.argv)

    # i18n
    translator = QTranslator()
    lang_code = detect_system_ui_language()
    translator.load(f":/i18n/{lang_code}.qm")
    app.installTranslator(translator)

    # start event loop
    run(task())


def main_no_updater():
    main(enable_updater=False)


def run_module():
    main()


if __name__ == "__main__":
    main()
