import asyncio
import sys
from qasync import QApplication, run
from PySide6.QtCore import QTranslator, QLocale
from app.main_window import MainWindow

# Importing qdarktheme for dark mode support if needed
import qdarktheme

async def main():
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

