from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QMessageBox
from app.resources.main_window_ui import Ui_MainWindow

# include the resource file
import app.resources.resource # type: ignore

class MainWindow:
    def __init__(self, window):
        self.window = window
        self.window.setWindowIcon(QIcon(':/assets/logo.png'))
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self.window)
        self.ui.pushButton.clicked.connect(self.click_push_button)


    def click_push_button(self):
        QMessageBox.information(self.window, "Hello", "Hello World!")
