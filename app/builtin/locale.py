from PySide6.QtCore import QLocale


def bcp47_to_locale(tag: str) -> str:
    """
    Convert BCP-47 tag (e.g. zh-Hans-CN, en-US)
    to POSIX locale style (e.g. zh_CN, en_US).
    """
    if not tag:
        return ""

    parts = tag.replace("-", "_").split("_")

    language = parts[0]

    region = None
    for part in parts[1:]:
        if len(part) == 2 and part.isalpha():
            region = part.upper()
            break
        if len(part) == 3 and part.isdigit():
            region = part
            break

    if region:
        return f"{language.lower()}_{region}"
    else:
        return language.lower()


def detect_system_ui_language():
    locale = QLocale()
    lang = locale.language()
    script = locale.script()
    # country = locale.country()
    if lang == QLocale.Language.Chinese:
        if script == QLocale.Script.SimplifiedChineseScript:
            return "zh_CN"

    return lang.name()
