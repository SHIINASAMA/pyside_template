import sys
from PySide6.QtWidgets import QApplication, QMainWindow
from app.main_window import MainWindow

# Importing qdarktheme for dark mode support if needed
import qdarktheme

if __name__ == '__main__':
    app = QApplication(sys.argv)
    # Set the themes for the application via qdarktheme
    qdarktheme.setup_theme("auto")
    window = QMainWindow()
    main_window = MainWindow(window)
    window.show()
    sys.exit(app.exec())
