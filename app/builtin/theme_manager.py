"""ThemeManager class to manage application theme settings
Built on top of pyqtdarktheme, this introduces additional QSS files for custom light or dark themes,
ensuring compatibility with systems that lack automatic theme switching.
"""

import atexit
import platform
from typing import Literal, Dict, Union, Optional

import darkdetect
import qdarktheme
from qdarktheme import load_stylesheet, load_palette
from qdarktheme.qtpy.QtCore import QCoreApplication
from qdarktheme._proxy_style import QDarkThemeStyle  # noqa: F401
from qdarktheme._os_appearance import listener  # noqa: F401


from singleton_decorator import singleton


@singleton
class ThemeManager:
    _listener = None
    _proxy_style = None
    additional_light_qss = ""
    additional_dark_qss = ""

    def setup_theme(
        self,
        theme: Literal["light", "dark", "auto"],
        corner_shape: Literal["rounded", "sharp"] = "rounded",
        custom_colors: Optional[Dict[str, Union[str, Dict[str, str]]]] = None,
        *,
        default_theme: Literal["light", "dark"] = "dark",
    ):
        app = QCoreApplication.instance()
        if theme != "auto":
            self._stop_sync()
        app.setProperty("_qdarktheme_use_setup_style", True)

        def callback():
            self._apply_style(
                theme=theme,
                corner_shape=corner_shape,
                custom_colors=custom_colors,
                default_theme=default_theme,
            )

        callback()
        if theme == "auto" and darkdetect.theme() is not None:
            self._sync_theme_with_system(callback)

    def _apply_style(self, **kargs):
        app = QCoreApplication.instance()
        stylesheet = load_stylesheet(**kargs)
        if kargs["theme"] == "auto":
            theme = "light" if darkdetect.isLight() else "dark"
        else:
            theme = kargs["theme"]
        if theme == "light":
            stylesheet += self.additional_light_qss
        else:
            stylesheet += self.additional_dark_qss
        app.setStyleSheet(stylesheet)
        app.setPalette(
            load_palette(
                kargs["theme"],
                kargs["custom_colors"],
                for_stylesheet=True,
                default_theme=kargs["default_theme"],
            )
        )
        if self._proxy_style is None:
            self._proxy_style = QDarkThemeStyle()
            app.setStyle(self._proxy_style)

    def _sync_theme_with_system(self, callback):
        if self._listener is not None:
            self._listener.sig_run.emit(True)
            return
        self._listener = listener.OSThemeSwitchListener(callback)
        if platform.system() == "Darwin":
            QCoreApplication.instance().installEventFilter(self._listener)
        else:
            atexit.register(self._listener.kill)
            self._listener.start()

    def _stop_sync(self):
        app = QCoreApplication.instance()
        if not app or not self._listener:
            return
        self._listener.sig_run.emit(False)

    def use_frameless_window(self):
        self.additional_dark_qss += """
            TitleBarButton{
                qproperty-normalColor: white;
                qproperty-hoverColor: white;
            }
            """
        self.additional_light_qss += """
            TitleBarButton{
                qproperty-normalColor: black;
                qproperty-hoverColor: black;
            }
            """


def enable_hi_dpi():
    qdarktheme.enable_hi_dpi()
