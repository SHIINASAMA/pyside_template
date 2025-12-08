import sys
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine
import qml_demo.resources.resource  # type: ignore


def main():
    app = QGuiApplication(sys.argv)
    engine = QQmlApplicationEngine()

    engine.load(":/qml/main.qml")
    if not engine.rootObjects():
        sys.exit(-1)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
