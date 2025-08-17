import asyncio
import sys
from qasync import QApplication, run
from PySide6.QtCore import QTranslator, QLocale
from app.main_window import MainWindow

# Importing qdarktheme for dark mode support if needed
import qdarktheme


async def main():
    if '--copy-self' in sys.argv:
        # remove the argument to ensure the updater
        sys.argv.remove('--copy-self')
        from app.builtin.update import Updater, ReleaseType
        # will ignore release type and always use stable
        updater = Updater(release_type=ReleaseType.STABLE)
        # wait for last executable to exit
        await updater.copy_self()

    elif '--updated' in sys.argv:
        # remove the argument to ensure the updater
        # sys.argv.remove('--updated')
        # update completed, go a head
        # wait for last executable to exit
        pass

    app_close_event = asyncio.Event()
    app.aboutToQuit.connect(app_close_event.set)

    main_window = MainWindow()
    main_window.show()

    await app_close_event.wait()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    translator = QTranslator()
    lang_code = QLocale.system().name()
    translator.load(f":/assets/i18n/{lang_code}.qm")
    app.installTranslator(translator)
    qdarktheme.setup_theme("auto")
    run(main())
