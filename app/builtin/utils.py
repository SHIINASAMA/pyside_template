import app.builtin.config as cfg

import sys

from qdarktheme import enable_hi_dpi
from PySide6.QtWidgets import QApplication


def init_app():
    # enable hdpi
    enable_hi_dpi()

    # init QApplication
    app = QApplication(sys.argv)
    app.setApplicationName(cfg.APP_NAME)
    app.setApplicationDisplayName(cfg.APP_DISPLAY_NAME)

    return app
