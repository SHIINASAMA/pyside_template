import argparse
import os
import sys
import logging
import json

class Build:
    args = None
    cache = {}

    def init(self):
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

        parser.add_argument('--msvc', action='store_true', help="Select the msvc as backend(nuitka)", required=False)
        parser.add_argument('--no-cache', action='store_true', help='Ignore existing caches', required=False)

        # do parse
        self.args = parser.parse_args()

    def load_cache(self):
        """load cache from .cache/assets.json"""
        if not os.path.exists('.cache'):
            os.makedirs('.cache')
        if os.path.exists('.cache/assets.json'):
            logging.info('Cache found.')
            with open('.cache/assets.json', 'r') as f:
                self.cache = json.load(f)
        if not self.cache:
            logging.info('No cache found.')

    def build_ui(self):
        """use pyside6-uic compile *.ui files"""
        # foreach file in app/ui, and convert it to a .py file using pyside6-uic to app/ui_resources
        # if ui folder does not exist, skip it
        if not os.path.exists('app/ui'):
            logging.info('No ui folder found, skipping ui conversion.')
        # if app/resources folder does not exist, create it
        if not os.path.exists('app/resources'):
            os.makedirs('app/resources')      

        logging.info('Converting ui files to python files...')
        if 'ui' in self.cache:
            ui_cache = self.cache['ui']
        else:
            ui_cache = {}
        for root, dirs, files in os.walk('app/ui'):
            for file in files:
                if not file.endswith('.ui'):
                    continue
                input_file = os.path.join(root, file)
                if input_file in ui_cache:
                    if ui_cache[input_file] == os.path.getmtime(input_file):
                        logging.info(f'{input_file} is up to date.')
                        continue
                ui_cache[input_file] = os.path.getmtime(input_file)
                logging.info(f'{input_file} is outdated. Need reconvert.')
                output_file = os.path.join('app/resources', file.replace('.ui', '_ui.py'))
                if 0 != os.system(f'pyside6-uic {input_file} -o {output_file}'):
                    logging.error('Failed to convert ui file.')
                    exit(1)
                logging.info(f'Converted {input_file} to {output_file}.')
        self.cache['ui'] = ui_cache

    def build_assets(self):
        # if app/assets.qrc does not exist, skip it
        if os.path.exists('app/assets.qrc'):
            logging.info('Converting resource files to python files...')
            if 'assets' in self.cache:
                assets_cache = self.cache['assets']
            else:
                assets_cache = {}

            if 'assets_json' in self.cache:
                assets_json = self.cache['assets_json']
            else:
                assets_json = ''

            if not os.path.exists('app/resources'):
                os.makedirs('app/resources')

            need_rebuild = False
            for root, dirs, files in os.walk('app/assets'):
                for file in files:
                    input_file = os.path.join(root, file)
                    if input_file in assets_cache:
                        if assets_cache[input_file] == os.path.getmtime(input_file):
                            logging.info(f'{input_file} is up to date.')
                            continue
                    assets_cache[input_file] = os.path.getmtime(input_file)
                    logging.info(f'{input_file} is outdated.')
                    need_rebuild = True
            if assets_json != os.path.getmtime('app/assets.qrc'):
                assets_json = os.path.getmtime('app/assets.qrc')
                logging.info(f'assets.json is outdated.')
                need_rebuild = True

            if self.args.no_cache:
                need_rebuild = True

            if need_rebuild:
                if 0 != os.system('pyside6-rcc app/assets.qrc -o app/resources/resource.py'):
                    logging.error('Failed to convert resource file.')
                    exit(1)
                logging.info('Converted app/assets.qrc to app/resources/resource.py.')
            else:
                logging.info('Assets is up to date.')

            self.cache['assets_json'] = assets_json
            self.cache['assets'] = assets_cache

    def save_cache(self):
        # save cache
        with open('.cache/assets.json', 'w') as f:
            json.dump(self.cache, f, indent=4)
        logging.info('Cache saved.')

    def build(self):
        logging.info('Building the app...')
        if self.args.pyinstaller:
            self.build_via_pyinstaller()
        elif self.args.nuitka:
            self.build_via_nuitka()
        else:
            logging.error('No builder specified. Use --pyinstaller or --nuitka.')
            exit(1)
        logging.info('Build complete.')

    def build_via_pyinstaller(self):
        # call pyinstaller to build the app
        # include all files in app package and exclude the ui files
        if self.args.msvc:
            logging.warning('Ignoring `--msvc` option for pyinstaller.')
        if 0 != os.system('pyinstaller '
                  '--noconfirm '
                  '--log-level=WARN '
                  '--windowed '
                  '--distpath "build" '
                  '--workpath "build/work" '
                  '--icon "app/assets/logo.ico" '
                  'app/__main__.py '
                  '--name App '
                  + ('--onefile ' if self.args.onefile else '--onedir ')):
            logging.error('Failed to build app via pyinstaller.')
            exit(1)
        # remove *.spec file
        if os.path.exists('App.spec'):
            os.remove('App.spec')

    def build_via_nuitka(self):
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
                  + ('--onefile ' if self.args.onefile else ' ')
                  + ('--msvc=latest') if self.args.msvc else ' '):
            logging.error('Failed to build app via nuitka.')
            exit(1)

    def run(self):
        self.init()
        if not self.args.no_cache:
            self.load_cache()
        if self.args.rc or self.args.all:
            self.build_ui()
            self.build_assets()
        self.save_cache()
        if self.args.build or self.args.all:
            self.build()

if __name__ == '__main__':
    builder = Build()
    builder.run()
