# macOS Build Guide

## Python Must Use a Framework Build

When running Qt-based GUI applications (such as Qt Designer) on macOS, you **must** use a **Framework build** of Python.

### Installation

It is recommended to install Python via Homebrew:

```bash
brew install python@3.13
```

Alternatively, download the official macOS installer from the Python website (the official installer provides a Framework build by default).

> [!NOTE]
> Adjust the Python version according to the actual version required by the project.


### Possible Error

If a non-Framework build of Python is used, running GUI applications may result in the following error:

> Unable to find Python library directory. Use a framework build of Python.

This is caused by macOS GUI runtime requirements and is unrelated to the project code.


### Virtual Environment Initialization

When creating a virtual environment, you must explicitly specify the Framework build interpreter.

> [!NOTE]
> `python3.13` is only an example version and is **not hardcoded**.  
You must select the Python version required by the project.

The required version can usually be found in the `.python-version` file located in the project root directory.

Example:

```bash
uv venv --python /opt/homebrew/bin/python3.13
```

Replace `3.13` with the version required by the project.

Do not use:

-   The system default Python
    
-   A non-Framework build of Python
    
-   Any minimal or embedded Python build
    

## Nuitka Limitations on macOS

On macOS:

-   Only `.app bundle` builds are supported
    
-   `onefile` is not supported
    
-   `onedir` is not supported
    

Therefore:

-   `pyside-cli build` uses bundle mode by default
    
-   No additional parameters are required
    

If you require:

-   Single-file distribution (`onefile`)
    
-   Directory-based distribution (`onedir`)
    

You must use **PyInstaller** as the build backend.

## Self-Update

In the current version:

-   Self-update is disabled by default
    
-   No alternative update mechanism is provided
    

To update the application, manually download a new version or integrate a third-party automatic update solution.