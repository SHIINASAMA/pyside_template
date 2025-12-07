def detect_system_ui_language():
    import platform
    system = platform.system()

    if system == "Windows":
        import ctypes, locale
        lang_id = ctypes.windll.kernel32.GetUserDefaultUILanguage()
        return locale.windows_locale.get(lang_id)

    elif system == "Darwin":  # macOS
        from Foundation import NSUserDefaults
        langs = NSUserDefaults.standardUserDefaults().objectForKey_("AppleLanguages")
        return langs[0] if langs else None
    
    else:  # Linux
        import os
        return (os.environ.get("LANG") or
                os.environ.get("LC_ALL") or
                os.environ.get("LC_MESSAGES"))
