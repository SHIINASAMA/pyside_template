import argparse
import os
import sys

# check working directory
# if 'app' is not in the current working directory, exit
if not os.path.exists('app'):
    print('Please run this script from the app directory.')
    exit(1)

# check using python virtual environment
if sys.prefix == sys.base_prefix:
    print(f'sys.prefix is {sys.prefix}.')
    print(f'sys.base_prefix is {sys.base_prefix}.')
    print('Please run this script from a python virtual environment.')
    exit(1)

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
builder_group = parser.add_mutually_exclusive_group()
builder_group.add_argument('--pyinstaller', action='store_true', help='Use pyinstaller to build the app')
builder_group.add_argument('--nuitka', action='store_true', help='Use nuitka to build the app')
# --onefile: create a single executable file
# --onedir: create a directory with the executable and all dependencies
package_format_group = parser.add_mutually_exclusive_group()
package_format_group.add_argument('--onefile', action='store_true', help='Create a single executable file')
package_format_group.add_argument('--onedir', action='store_true',
                                  help='Create a directory with the executable and all dependencies')
# do parse
args = parser.parse_args()

if args.ui or args.all:
    # foreach file in app/ui, and convert it to a .py file using pyside6-uic to app/ui_resources
    # if ui folder does not exist, skip it
    if not os.path.exists('app/ui'):
        print('No ui folder found, skipping ui conversion.')
    # if app/resources folder does not exist, create it
    if not os.path.exists('app/resources'):
        os.makedirs('app/resources')
    else:
        for root, dirs, files in os.walk('app/ui'):
            for file in files:
                if file.endswith('.ui'):
                    input_file = os.path.join(root, file)
                    output_file = os.path.join('app/resources', file.replace('.ui', '_ui.py'))
                    os.system(f'pyside6-uic {input_file} -o {output_file}')
                    print(f'Converted {input_file} to {output_file}.')

if args.build or args.all:
    print('Converting resource files to python files...')
    # if app/asserts.qrc does not exist, skip it
    if os.path.exists('app/asserts.qrc'):
        if not os.path.exists('app/resources'):
            os.makedirs('app/resources')
        os.system('pyside6-rcc app/asserts.qrc -o app/resources/resource.py')

    print('Building the app...')
    if args.pyinstaller:
        # call pyinstaller to build the app
        # include all files in app package and exclude the ui files
        os.system('pyinstaller '
                  '--noconfirm '
                  '--log-level=WARN '
                  '--windowed '
                  '--distpath "build" '
                  '--workpath "build/work" '
                  '--icon "app/asserts/logo.ico" '
                  'app/__main__.py '
                  '--name App '
                   + ('--onefile ' if args.onefile else '--onedir '))
        # remove *.spec file
        if os.path.exists('App.spec'):
            os.remove('App.spec')
    elif args.nuitka:
        # call nuitka to build the app
        # include all files in app package and exclude the ui files
        os.system('nuitka '
                  '--quiet '
                  '--standalone '
                  '--windows-console-mode=disable '
                  '--plugin-enable=pyside6 '
                  '--output-dir=build_nuitka '
                  '--follow-imports '
                  '--windows-icon-from-ico="app/asserts/logo.ico" '
                  '--output-filename="App" '
                  'app/__main__.py '
                  + ('--onefile ' if args.onefile else ' '))
    else:
        print('No builder specified. Use --pyinstaller or --nuitka.')
        exit(1)
    print('Build complete.')