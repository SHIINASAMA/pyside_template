import sys
from PySide6.QtWidgets import QApplication, QMainWindow

from app.main_window import MainWindow

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = QMainWindow()
    main_window = MainWindow(window)
    window.show()
    sys.exit(app.exec())
