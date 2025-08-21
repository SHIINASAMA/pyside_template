import asyncio
import sys

from qasync import QApplication, run
from PySide6.QtCore import QTranslator, QLocale, QLockFile
import qdarktheme

from app.main_window import MainWindow
from app.builtin.update import Updater, ReleaseType


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
    updater = Updater(release_type=ReleaseType.STABLE)

    # check if the app is already running
    lock_file = QLockFile("App.lock")
    if not lock_file.lock():
        sys.exit(0)

    # enable hdpi
    qdarktheme.enable_hi_dpi()

    # init QApplication
    app = QApplication(sys.argv)

    # i18n
    translator = QTranslator()
    lang_code = QLocale.system().name()
    translator.load(f":/assets/i18n/{lang_code}.qm")
    app.installTranslator(translator)

    # theme
    qdarktheme.setup_theme("auto")

    # start event loop
    run(main())
