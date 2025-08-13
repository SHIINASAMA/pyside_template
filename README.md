# PySide6 Project Template

Easy to use template for PySide6 projects.
This template is designed to help you get started with PySide6 quickly and easily.
It includes a basic project structure, a build script, and a pyproject file.

Even if some company computers are underpowered, they're still usable in most cases.
You just need to install uv and Python 3.8.

## Main Dependencies

- PySide6
- qasync
- Nuitka (Optional)
- PyQtDarkTheme (Optional)

## Project Structure

| File or Directory  | Description                                  |
|--------------------|----------------------------------------------|
| app/               | Source code directory                        |
| app/assets.qrc     | Qt resources mapping descript file           |
| app/assets/**      | Qt resources files (images, icons, etc.)     |
| app/ui/*.ui        | Qt Designer UI files                         |
| app/resources/*.py | Generated Python files from UI and QRC files |
| pyproject.toml     | Project builds and settings                  |
| build.py           | Build script for the project                 |
| .cache/assets.json | Build Caches                                 |
| build/             | Build Destination Directory                  |

## Command

Setup development environment and run the project.

```bash
uv sync
uv -m app
```

Using QtDesigner to create UI files. The UI files are must have located in the `ui` folder.

```bash
uv run pyside6-designer app/ui/main_window.ui
```

How to build and package the project. Run the following command to get the help message:

```bash
uv run ./build.py -h
```

Help message example:

```
> uv run build.py -h
usage: build.py [-h] (--rc | --build | --all) [--onefile | --onedir] [--msvc] [--no-cache]

Build the app.

options:
  -h, --help     show this help message and exit
  --rc           Convert rc files to python files
  --build        Build the app
  --all          Convert rc files and build the app
  --onefile      Create a single executable file
  --onedir       Create a directory with the executable and all dependencies
  --msvc         Select the msvc as backend(nuitka)
  --no-cache     Ignore existing caches
```