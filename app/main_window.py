from PySide6.QtWidgets import QMessageBox

from app.ui_resources.main_window_ui import Ui_MainWindow


class MainWindow:
    def __init__(self, window):
        self.window = window
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self.window)
        self.ui.pushButton.clicked.connect(self.click_push_button)

    def click_push_button(self):
        QMessageBox.information(self.window, "Hello", "Hello World!")
