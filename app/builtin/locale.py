import sys


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
    if sys.platform == "win32":
        import ctypes, locale

        lang_id = ctypes.windll.kernel32.GetUserDefaultUILanguage()
        return locale.windows_locale.get(lang_id)

    elif sys.platform == "darwin":  # macOS
        from Foundation import NSUserDefaults

        langs = NSUserDefaults.standardUserDefaults().objectForKey_("AppleLanguages")
        lang = langs[0] if langs else None
        assert lang is not None
        return bcp47_to_locale(lang)

    else:  # Linux
        import os

        return (
            os.environ.get("LANG")
            or os.environ.get("LC_ALL")
            or os.environ.get("LC_MESSAGES")
        )
