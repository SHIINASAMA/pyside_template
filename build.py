import argparse
import os
import sys
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
# check working directory
# if 'app' is not in the current working directory, exit
if not os.path.exists('app'):
    logging.error('Please run this script from the app directory.')
    exit(1)

# check using python virtual environment
if sys.prefix == sys.base_prefix:
    logging.error(f'sys.prefix is {sys.prefix}.')
    logging.error(f'sys.base_prefix is {sys.base_prefix}.')
    logging.error('Please run this script from a python virtual environment.')
    exit(1)

# parse command line arguments
# --help: show this help message
parser = argparse.ArgumentParser(description='Build the app.')
# --ui: only convert ui files to python files
# --build: only build the app
# --all: convert ui files and build the app
mode_group = parser.add_mutually_exclusive_group(required=True)
mode_group.add_argument('--rc', action='store_true', help='Convert rc files to python files')
mode_group.add_argument('--build', action='store_true', help='Build the app')
mode_group.add_argument('--all', action='store_true', help='Convert rc files and build the app')
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

if args.rc or args.all:
    # foreach file in app/ui, and convert it to a .py file using pyside6-uic to app/ui_resources
    # if ui folder does not exist, skip it
    if not os.path.exists('app/ui'):
        logging.info('No ui folder found, skipping ui conversion.')
    # if app/resources folder does not exist, create it
    if not os.path.exists('app/resources'):
        os.makedirs('app/resources')

    logging.info('Converting ui files to python files...')
    for root, dirs, files in os.walk('app/ui'):
        for file in files:
            if file.endswith('.ui'):
                input_file = os.path.join(root, file)
                output_file = os.path.join('app/resources', file.replace('.ui', '_ui.py'))
                if 0 != os.system(f'pyside6-uic {input_file} -o {output_file}'):
                    logging.error('Failed to convert ui file.')
                    exit(1)
                logging.info(f'Converted {input_file} to {output_file}.')

    # if app/assets.qrc does not exist, skip it
    if os.path.exists('app/assets.qrc'):
        logging.info('Converting resource files to python files...')
        if not os.path.exists('app/resources'):
            os.makedirs('app/resources')
        if 0 != os.system('pyside6-rcc app/assets.qrc -o app/resources/resource.py'):
            logging.error('Failed to convert resource file.')
            exit(1)
        logging.info('Converted app/assets.qrc to app/resources/resource.py.')

if args.build or args.all:
    logging.info('Building the app...')
    if args.pyinstaller:
        # call pyinstaller to build the app
        # include all files in app package and exclude the ui files
        if 0 != os.system('pyinstaller '
                  '--noconfirm '
                  '--log-level=WARN '
                  '--windowed '
                  '--distpath "build" '
                  '--workpath "build/work" '
                  '--icon "app/assets/logo.ico" '
                  'app/__main__.py '
                  '--name App '
                  + ('--onefile ' if args.onefile else '--onedir ')):
            logging.error('Failed to build app via pyinstaller.')
            exit(1)
        # remove *.spec file
        if os.path.exists('App.spec'):
            os.remove('App.spec')
    elif args.nuitka:
        # call nuitka to build the app
        # include all files in app package and exclude the ui files
        if 0 != os.system('nuitka '
                  '--quiet '
                  '--standalone '
                  '--assume-yes-for-downloads '
                  '--windows-console-mode=disable '
                  '--plugin-enable=pyside6 '
                  '--output-dir=build_nuitka '
                  '--follow-imports '
                  '--windows-icon-from-ico="app/assets/logo.ico" '
                  '--output-filename="App" '
                  'app/__main__.py '
                  + ('--onefile ' if args.onefile else ' ')):
            logging.error('Failed to build app via nuitka.')
            exit(1)
    else:
        logging.error('No builder specified. Use --pyinstaller or --nuitka.')
        exit(1)
    logging.info('Build complete.')
