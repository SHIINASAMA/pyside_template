# PySide6 Project Template

Easy to use template for PySide6 projects.
This template is designed to help you get started with PySide6 quickly and easily. 
It includes a basic project structure, a build script, and a requirements file.

## Main Dependencies

- PySide6
- Pyinstaller
- Nuitka

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
> python ./build.py -h
usage: build.py [-h] (--ui | --build | --all) [--pyinstaller | --nuitka] [--onefile | --onedir]

Build the app.

options:
  -h, --help     show this help message and exit
  --ui           Convert ui files to python files
  --build        Build the app
  --all          Convert ui files and build the app
  --pyinstaller  Use pyinstaller to build the app
  --nuitka       Use nuitka to build the app
  --onefile      Create a single executable file
  --onedir       Create a directory with the executable and all dependencies
```