"""ThemeManager class to manage application theme settings
Built on top of pyqtdarktheme, this introduces additional QSS files for custom light or dark themes,
ensuring compatibility with systems that lack automatic theme switching.
"""

import atexit
import platform
from typing import Literal, Dict, Union

from qdarktheme.qtpy.QtCore import QCoreApplication


def is_old_system() -> bool:
    """Check list of conditions, must meet one of them to be considered old system:
    1. The system is Windows 7 or older and python version is lower and equal to 3.8
    2. Cannot import darkdetect
    """
    try:
        import darkdetect  # noqa: F401
    except ImportError:
        return True

    if platform.system() == "Windows":
        ver = platform.version().split(".")
        try:
            major = int(ver[0])
            minor = int(ver[1])
        except (IndexError, ValueError):
            return False

        if major < 6 or (major == 6 and minor < 2):
            import sys
            if sys.version_info <= (3, 8):
                return True

    return False


if is_old_system():
    class ThemeManager:
        _instance = None

        def __new__(cls):
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
            return cls._instance

        def __init__(self):
            if not self._initialized:
                self._listener = None
                self._proxy_style = None
                self.additional_light_qss = ""
                self.additional_dark_qss = ""
                self._initialized = True

        @staticmethod
        def instance():
            if ThemeManager._instance is None:
                ThemeManager()
            return ThemeManager._instance

        def setup_theme(self,
                        theme: Literal["light", "dark"]):
            from qdarktheme import load_stylesheet
            app = QCoreApplication.instance()
            app.setStyleSheet(load_stylesheet(theme))


    def enable_hi_dpi():
        pass

else:
    import darkdetect
    from qdarktheme import load_stylesheet, load_palette


    class ThemeManager:
        _instance = None

        def __new__(cls):
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
            return cls._instance

        def __init__(self):
            if not self._initialized:
                self._listener = None
                self._proxy_style = None
                self.additional_light_qss = ""
                self.additional_dark_qss = ""
                self._initialized = True

        @staticmethod
        def instance():
            if ThemeManager._instance is None:
                ThemeManager()
            return ThemeManager._instance

        def setup_theme(self,
                        theme: Literal["light", "dark", "auto"],
                        corner_shape: Literal["rounded", "sharp"] = "rounded",
                        custom_colors: Dict[str, Union[str, Dict[str, str]]] = None,
                        *,
                        default_theme: Literal["light", "dark"] = "dark"):
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
            from qdarktheme._proxy_style import QDarkThemeStyle  # noqa: F401

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
            from qdarktheme._os_appearance import listener  # noqa: F401

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
        import qdarktheme
        qdarktheme.enable_hi_dpi()
