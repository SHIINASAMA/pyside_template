import os

if __name__ == '__main__':
    # foreach file in app/ui, and convert it to a .py file using pyside6-uic to app/ui_resources
    for root, dirs, files in os.walk('app/ui'):
        for file in files:
            if file.endswith('.ui'):
                input_file = os.path.join(root, file)
                output_file = os.path.join('app/ui_resources', file.replace('.ui', '_ui.py'))
                os.system(f'pyside6-uic {input_file} -o {output_file}')
                print(f'Converted {input_file} to {output_file}')

    # call pyinstaller to build the app
    # include all files in app package and exclude the ui files
    # --onefile: create a single executable file
    # --onedir: create a directory with the executable and all dependencies
    os.system('pyinstaller --onefile --windowed --add-data "app:app" app/__main__.py --name App')