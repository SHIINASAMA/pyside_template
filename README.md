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
| .cache/assets.json | Build Caches                                 |
| app/               | Source code directory                        |
| app/assets/**      | Qt resources files (images, icons, etc.)     |
| app/ui/**.ui       | Qt Designer UI files                         |
| app/resources/*.py | Generated Python files from UI and QRC files |
| pyproject.toml     | Project builds and settings                  |
| build.py           | Build script for the project                 |
| build/             | Build Destination Directory                  |

## Command

- Setup development environment and run the project.

    ```bash
    uv sync
    uv -m app
    ```

- Using QtDesigner to create UI files. The UI files are must have located in the `ui` folder.

    ```bash
    uv run pyside6-designer app/ui/main_window.ui
    ```

- How to build and package the project. Run the following command to get the help message:

    ```bash
    uv run ./build.py -h
    ```

- Run app via command line: (Will build the project)

    ```bash
    uv run ./build.py --all --onedir --run
    ```

  Or use your environment file to run the app: (Does not build the project)

    ```bash
    uv run ./build.py --rc --onedir
    uv run --env-file .env -- python -m app
    ```