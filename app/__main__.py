import asyncio
import sys
from qasync import QApplication, run
from app.main_window import MainWindow

# Importing qdarktheme for dark mode support if needed
import qdarktheme

if __name__ == '__main__':
    app = QApplication(sys.argv)
    app_close_event = asyncio.Event()
    app.aboutToQuit.connect(app_close_event.set)
    # Set the themes for the application via qdarktheme
    qdarktheme.setup_theme("auto")
    main_window = MainWindow()
    main_window.show()
    run(app_close_event.wait())

