from PySide6.QtCore import QLocale


def detect_system_ui_language():
    locale = QLocale()
    lang = locale.language()
    script = locale.script()
    # country = locale.country()

    return f"{QLocale.languageToCode(lang)}-{QLocale.scriptToCode(script)}"
