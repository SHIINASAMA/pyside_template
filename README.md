# PySide6 Project Template

Easy to use template for PySide6 projects.
This template is designed to help you get started with PySide6 quickly and easily.
It includes a basic project structure, a build script, and a requirements file.

Even if some company computers are underpowered, they're still usable in most cases. 
You just need to install Python 3.11 and do some simple virtual environment setup.

## Main Dependencies

- PySide6
- Pyinstaller (Optional)
- Nuitka (Optional)
- PyQtDarkTheme (Optional)

## Project Structure

| File or Directory   | Description                                        |
|---------------------|----------------------------------------------------|
| app/                | Source code directory                              |
| app/assets.qrc      | Qt resources mapping descript file                 |
| app/assets/**       | Qt resources files (images, icons, etc.)           |
| app/ui/*.ui         | Qt Designer UI files                               |
| app/resources/*.py  | Generated Python files from UI and QRC files       |
| build.py            | Build script for the project                       |
| requirements.txt    | List of dependencies for the project               |
| setup_via_mirror.py | Setup script for the project via mirror (optional) |
| .cache/assets.json  | Build Caches                                       |
| build/              | Build Destination Directory if use Pyinstaller     |
| build_nuitka/       | Build Destination Directory if use Nuitka          |

## Command

Setup development environment and run the project.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m app
```

Using QtDesigner to create UI files. The UI files are must have located in the `ui` folder.

```bash
pyside6-designer
```

How to build and package the project. Run the following command to get the help message:

```bash
python ./build.py -h
```

Help message example:

```
> python build.py -h
usage: build.py [-h] (--rc | --build | --all) [--pyinstaller | --nuitka] [--onefile | --onedir] [--msvc] [--no-cache]

Build the app.

options:
  -h, --help     show this help message and exit
  --rc           Convert rc files to python files
  --build        Build the app
  --all          Convert rc files and build the app
  --pyinstaller  Use pyinstaller to build the app
  --nuitka       Use nuitka to build the app
  --onefile      Create a single executable file
  --onedir       Create a directory with the executable and all dependencies
  --msvc         Select the msvc as backend(nuitka)
  --no-cache     Ignore existing caches
```