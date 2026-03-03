from PySide6.QtCore import QLocale


def detect_system_ui_language():
    locale = QLocale()
    lang = locale.language()
    script = locale.script()
    # country = locale.country()
    # if lang == QLocale.Language.Chinese:
    #     if script == QLocale.Script.SimplifiedChineseScript:
    #         return "zh-Hans"

    return f"{QLocale.languageToCode(lang)}-{QLocale.scriptToCode(script)}"
