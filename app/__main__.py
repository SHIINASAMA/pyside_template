import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QMessageBox
from app.ui_resources.main_window_ui import Ui_MainWindow

ui = Ui_MainWindow()

def click_push_button():
    QMessageBox.information(None, "Button Clicked", "You clicked the button!")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    MainWindow = QMainWindow()
    ui.setupUi(MainWindow)

    # Connect the button click signal to the slot
    ui.pushButton.clicked.connect(click_push_button)

    MainWindow.show()
    sys.exit(app.exec())