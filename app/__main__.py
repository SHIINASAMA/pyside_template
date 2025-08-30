import asyncio
import os.path
import sys

import qdarktheme
from PySide6.QtCore import QTranslator, QLocale, QLockFile
from qasync import QApplication, run

from app.builtin.theme_manager import ThemeManager
from app.builtin.update import Updater
from app.main_window import MainWindow


async def main():
    app_close_event = asyncio.Event()
    app.aboutToQuit.connect(app_close_event.set)

    main_window = MainWindow()
    main_window.show()
    await main_window.async_init()
    await app_close_event.wait()


if __name__ == '__main__':
    # init updater, updater will remove some arguments
    # and do update logic
    updater = Updater()

    # check if the app is already running
    lock_file = QLockFile("App.lock")
    if not lock_file.lock():
        sys.exit(0)

    if os.path.exists("updater.json"):
        updater.load_from_file_and_override("updater.json")

    # enable hdpi
    qdarktheme.enable_hi_dpi()

    # init QApplication
    app = QApplication(sys.argv)

    # i18n
    translator = QTranslator()
    lang_code = QLocale.system().name()
    translator.load(f":/i18n/{lang_code}.qm")
    app.installTranslator(translator)

    # theme
    theme = ThemeManager.instance()
    theme.use_frameless_window()

    # start event loop
    run(main())
