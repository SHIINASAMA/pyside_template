# QML Demo

`QmlDemo` does **not fully adapt to the entire workflow template**.  
It only guarantees the most basic functionality: **build**.

The complete required configuration in `pyproject.toml` is as follows:

```toml
[tool.pyside-cli]
quiet = true
assume-yes-for-downloads = true
enable-plugins = ["pyside6"]
include-qt-plugins = ["qml", "platforms", "imageformats", "styles"]
include-module = ["PySide6.QtQml", "PySide6.QtQuick", "PySide6.QtQuickControls2"]
```

> [!WARNING]   
> The App(target's name) uses **httpx** as a replacement for **Qt6Network** by default.  
> Therefore, `PySide6.QtNetwork` is intentionally excluded.  
> However, using **QtQuick** implicitly depends on `PySide6.QtNetwork`.

Build the project using the following command:

```bash
uv run pyside-cli build -t QmlDemo
```
