import argparse
import os

# parse command line arguments
# --help: show this help message
parser = argparse.ArgumentParser(description='Build the app.')
# --ui: only convert ui files to python files
# --build: only build the app
# --all: convert ui files and build the app
mode_group = parser.add_mutually_exclusive_group(required=True)
mode_group.add_argument('--ui', action='store_true', help='Convert ui files to python files')
mode_group.add_argument('--build', action='store_true', help='Build the app')
mode_group.add_argument('--all', action='store_true', help='Convert ui files and build the app')
# --pyinstaller: use pyinstaller to build the app
# --nuitka: use nuitka to build the app
builder_group = parser.add_mutually_exclusive_group(required=True)
builder_group.add_argument('--pyinstaller', action='store_true', help='Use pyinstaller to build the app')
builder_group.add_argument('--nuitka', action='store_true', help='Use nuitka to build the app')
# --onefile: create a single executable file
# --onedir: create a directory with the executable and all dependencies
package_format_group = parser.add_mutually_exclusive_group(required=True)
package_format_group.add_argument('--onefile', action='store_true', help='Create a single executable file')
package_format_group.add_argument('--onedir', action='store_true',
                                  help='Create a directory with the executable and all dependencies')
# do parse
args = parser.parse_args()

if args.ui or args.all:
    # foreach file in app/ui, and convert it to a .py file using pyside6-uic to app/ui_resources
    for root, dirs, files in os.walk('app/ui'):
        for file in files:
            if file.endswith('.ui'):
                input_file = os.path.join(root, file)
                output_file = os.path.join('app/ui_resources', file.replace('.ui', '_ui.py'))
                os.system(f'pyside6-uic {input_file} -o {output_file}')
                print(f'Converted {input_file} to {output_file}')

if args.build or args.all:
    if args.pyinstaller:
        # call pyinstaller to build the app
        # include all files in app package and exclude the ui files
        os.system('pyinstaller '
                  '--quiet '
                  '--windowed '
                  '--distpath "build" '
                  '--workpath "build/work" '
                  '--add-data "app:app" '
                  'app/__main__.py '
                  '--name App'
                  '--onefile ' if args.onefile else '--onedir ')
    elif args.nuitka:
        # call nuitka to build the app
        # include all files in app package and exclude the ui files
        os.system('nuitka '
                  '--quiet '
                  '--standalone '
                  '--windows-console-mode=disable '
                  '--plugin-enable=pyside6 '
                  '--output-dir=build-nuitka '
                  '--follow-imports '
                  '--output-filename="App" '
                  'app/__main__.py '
                  '--onefile ' if args.onefile else '')