import asyncio
import sys
from qasync import QApplication, run
from app.main_window import MainWindow

# Importing qdarktheme for dark mode support if needed
import qdarktheme

async def main():
    app_close_event = asyncio.Event()
    app.aboutToQuit.connect(app_close_event.set)

    qdarktheme.setup_theme("auto")
    main_window = MainWindow()
    main_window.show()

    await app_close_event.wait()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    run(main())

