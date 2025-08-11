import argparse
import os
import sys
import logging
import json
import shutil
import time


class Build:
    def __init__(self):
        self.args = None
        self.cache = {}
        self.no_follow_import_to = []
        self.no_include_qt_plugins = []

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
        # --onefile: create a single executable file
        # --onedir: create a directory with the executable and all dependencies
        package_format_group = parser.add_mutually_exclusive_group()
        package_format_group.add_argument('--onefile', action='store_true', help='Create a single executable file')
        package_format_group.add_argument('--onedir', action='store_true',
                                          help='Create a directory with the executable and all dependencies')

        parser.add_argument('--msvc', action='store_true', help="Select the msvc as backend(nuitka)", required=False)
        parser.add_argument('--no-cache', action='store_true', help='Ignore existing caches', required=False)

        parser.add_argument('backend_args', nargs=argparse.REMAINDER, help='The backend\'s args.')

        # do parse
        self.args = parser.parse_args()
        if self.args.backend_args and self.args.backend_args[0] == "--":
            self.args.backend_args = self.args.backend_args[1:]

        if os.path.exists('build_options.json'):
            logging.info('Loading build_options.json.')
            json_data = json.load(open('build_options.json'))
            self.no_follow_import_to = json_data.get('no-follow-import-to', [])
            self.no_include_qt_plugins = json_data.get('no-include-qt-plugins', [])

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
                logging.info(f'{input_file} is outdated.')
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

    @staticmethod
    def filelist(root_dir: str, filelist_name: str):
        with open(filelist_name, "w", encoding="utf-8") as f:
            for current_path, dirs, files in os.walk(root_dir, topdown=False):
                for file in files:
                    relative_path = os.path.relpath(os.path.join(current_path, file), root_dir)
                    logging.info(relative_path)
                    f.write(relative_path + "\n")
                relative_path = os.path.relpath(os.path.join(current_path, ""), root_dir)
                if relative_path == ".":
                    continue
                logging.info(relative_path)
                f.write(relative_path + "\n")

    def build(self):
        # call nuitka to build the app
        # include all files in app package and exclude the ui files
        start = time.perf_counter()
        logging.info('Building the app...')
        rt = os.system(
            'nuitka '
            '--quiet '
            '--assume-yes-for-downloads '
            '--windows-console-mode=disable '
            '--plugin-enable=pyside6 '
            '--output-dir=build '
            '--windows-icon-from-ico="app/assets/logo.ico" '
            '--output-filename="App" '
            'app/__main__.py '
            + '--jobs={} '.format(os.cpu_count())
            + ('--onefile ' if self.args.onefile else '--standalone ')
            + ('--msvc=latest ' if self.args.msvc else ' ')
            + ('--nofollow-import-to=' + ",".join(self.no_follow_import_to) if self.no_follow_import_to else ' ')
            + ('--noinclude-qt-plugins=' + ",".join(self.no_include_qt_plugins) if self.no_include_qt_plugins else ' ')
            + (" ".join(self.args.backend_args)))
        end = time.perf_counter()
        if rt == 0:
            logging.info(f'Build complete in {end - start:.3f}s.')
            if not self.args.onefile:
                if os.path.exists('build/App'):
                    shutil.rmtree('build/App')
                shutil.move('build/__main__.dist', 'build/App')
                logging.info("Generate the filelist.")
                Build.filelist('build/App', 'build/App/filelist.txt')
        else:
            logging.error(f'Failed to build app in {end - start:.3f}s.')
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
