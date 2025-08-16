import argparse
import os
import logging
import json
import shutil
import subprocess
import sys
import time
import toml
import glom


class Build:
    def __init__(self):
        self.args = None
        self.cache = {}
        self.opt_from_toml = ""
        self.lang_list = []

    def init(self):
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        # check working directory
        # if 'app' is not in the current working directory, exit
        if not os.path.exists('app'):
            logging.error('Please run this script from the project root directory.')
            exit(1)

        # parse command line arguments
        # --help: show this help message
        parser = argparse.ArgumentParser(description='Build the app.')
        # --ui: only convert ui files to python files
        # --build: only build the app
        # --all: convert ui files and build the app
        mode_group = parser.add_mutually_exclusive_group(required=True)
        mode_group.add_argument('--i18n', action='store_true',
                                help='Generate translation files (.ts) for all languages')
        mode_group.add_argument('--rc', action='store_true', help='Convert rc files to python files')
        mode_group.add_argument('--build', action='store_true', help='Build the app')
        mode_group.add_argument('--all', action='store_true', help='Convert rc files and build the app')
        # --onefile: create a single executable file
        # --onedir: create a directory with the executable and all dependencies
        package_format_group = parser.add_mutually_exclusive_group()
        package_format_group.add_argument('--onefile', action='store_true', help='Create a single executable file')
        package_format_group.add_argument('--onedir', action='store_true',
                                          help='Create a directory with the executable and all dependencies')

        parser.add_argument('--no-cache', action='store_true', help='Ignore existing caches', required=False)

        parser.add_argument('backend_args', nargs=argparse.REMAINDER,
                            help='Additional arguments for the build backend, e.g. -- --product-version=1.0.0')

        # do parse
        self.args = parser.parse_args()
        if self.args.backend_args and self.args.backend_args[0] == "--":
            self.args.backend_args = self.args.backend_args[1:]

        with open("pyproject.toml") as f:
            data = toml.load(f)
        config = glom.glom(data, "tool.build", default={})
        platform_config = glom.glom(data, f"tool.build.{sys.platform}", default={})
        config.update(platform_config)
        for k, v in config.items():
            if isinstance(v, list) and v:
                cmd = f"--{k}={','.join(v)} "
                self.opt_from_toml += cmd
            if isinstance(v, str) and v != "":
                cmd = f"--{k}={v} "
                self.opt_from_toml += cmd
            if type(v) is bool and v:
                cmd = f"--{k} "
                self.opt_from_toml += cmd
        self.lang_list = glom.glom(data, "tool.i18n.languages", default=[])

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
        """Compile *.ui files into Python files using pyside6-uic, preserving directory structure."""
        ui_dir = 'app/ui'
        res_dir = 'app/resources'

        # Skip if ui directory does not exist
        if not os.path.exists(ui_dir):
            logging.info('No ui folder found, skipping ui conversion.')
            return

        # Ensure the resources root directory exists
        os.makedirs(res_dir, exist_ok=True)

        logging.info('Converting ui files to Python files...')
        ui_cache = self.cache.get('ui', {})

        for root, dirs, files in os.walk(ui_dir):
            for file in files:
                if not file.endswith('.ui'):
                    continue

                input_file = os.path.join(root, file)
                rel_path = os.path.relpath(root, ui_dir)  # relative path under ui/
                output_dir = os.path.join(res_dir, rel_path)  # mirror the directory structure in resources/
                os.makedirs(output_dir, exist_ok=True)  # create the directory if not exists

                output_file = os.path.join(output_dir, file.replace('.ui', '_ui.py'))

                # Check cache to avoid unnecessary recompilation
                mtime = os.path.getmtime(input_file)
                if input_file in ui_cache and ui_cache[input_file] == mtime:
                    logging.info(f'{input_file} is up to date.')
                    continue

                ui_cache[input_file] = mtime

                # Run pyside6-uic (does not create directories automatically)
                if 0 != os.system(f'pyside6-uic "{input_file}" -o "{output_file}"'):
                    logging.error(f'Failed to convert {input_file}.')
                    exit(1)

                logging.info(f'Converted {input_file} → {output_file}')

        self.cache['ui'] = ui_cache

    def build_assets(self):
        """Generate assets.qrc from files in app/assets and compile it with pyside6-rcc."""
        assets_dir = 'app/assets'
        qrc_file = 'app/assets.qrc'
        res_dir = 'app/resources'
        py_res_file = os.path.join(res_dir, 'resource.py')

        # Skip if assets directory does not exist
        if not os.path.exists(assets_dir):
            logging.info('No assets folder found, skipping assets conversion.')
            return

        if not os.path.exists(res_dir):
            os.makedirs(res_dir)

        logging.info('Converting assets to Python resources...')

        assets_cache = self.cache.get('assets', {})
        need_rebuild = False

        # Traverse assets/ and update cache
        all_assets = []
        for root, dirs, files in os.walk(assets_dir):
            for file in files:
                input_file = os.path.join(root, file)
                rel_path = os.path.relpath(input_file, 'app')  # qrc requires path relative to app/
                all_assets.append(rel_path)

                mtime = os.path.getmtime(input_file)
                if input_file in assets_cache and assets_cache[input_file] == mtime:
                    logging.info(f'{input_file} is up to date.')
                    continue
                assets_cache[input_file] = mtime
                logging.info(f'{input_file} is outdated.')
                need_rebuild = True

        # Force rebuild if cache is disabled
        if self.args.no_cache:
            need_rebuild = True

        if need_rebuild:
            # Generate assets.qrc dynamically
            with open(qrc_file, 'w', encoding='utf-8') as f:
                f.write('<!DOCTYPE RCC>\n')
                f.write('<RCC version="1.0">\n')
                f.write('  <qresource>\n')
                for asset in all_assets:
                    f.write(f'    <file>{asset}</file>\n')
                f.write('  </qresource>\n')
                f.write('</RCC>\n')
            logging.info(f'Generated {qrc_file}.')

            # Compile qrc file to Python resource
            if 0 != os.system(f'pyside6-rcc {qrc_file} -o {py_res_file}'):
                logging.error('Failed to convert assets.qrc.')
                exit(1)
            logging.info(f'Converted {qrc_file} to {py_res_file}.')
        else:
            logging.info('Assets are up to date.')

        self.cache['assets'] = assets_cache

    def build_i18n_ts(self):
        """
        Generate translation (.ts) files for all languages in lang_list
        by scanning the app/ui directory using pyside6-lupdate recursively.
        """
        ui_dir = 'app/ui'
        i18n_dir = 'app/i18n'

        # Skip if ui directory does not exist
        if not os.path.exists(ui_dir):
            logging.info('No ui folder found, skipping i18n generation.')
            return

        # Ensure i18n output directory exists
        os.makedirs(i18n_dir, exist_ok=True)

        logging.info('Generating translation (.ts) files for languages: %s', ', '.join(self.lang_list))

        i18n_cache = self.cache.get('i18n', {})
        # Generate ts file for each language
        for lang in self.lang_list:
            ts_file = os.path.join(i18n_dir, f'{lang}.ts')
            logging.info('Generating %s ...', ts_file)

            # Use pyside6-lupdate to recursively scan ui_dir and generate ts
            cmd = f'pyside6-lupdate -recursive -extensions ui "{ui_dir}"  -ts "{ts_file}"'

            # Run the command
            if 0 != os.system(cmd):
                exit(1)
            i18n_cache[lang] = os.path.getmtime(ts_file)

            logging.info('Generated translation file: %s', ts_file)
        self.cache['i18n'] = i18n_cache

    def build_i18n(self):
        """
        Compile .ts translation files into .qm files under app/assets/i18n/.
        Only regenerate .qm if the corresponding .ts file has changed.
        """
        ts_dir = 'app/i18n'
        qm_dir = 'app/assets/i18n'

        # Skip if i18n directory does not exist
        if not os.path.exists(ts_dir):
            logging.info('No i18n folder found, skipping compilation.')
            return

        # Ensure output directory exists
        os.makedirs(qm_dir, exist_ok=True)

        logging.info('Compiling translation files...')

        # Get cache for i18n
        i18n_cache = self.cache.get('i18n', {})

        # Iterate all ts files
        for root, dirs, files in os.walk(ts_dir):
            for file in files:
                if not file.endswith('.ts'):
                    continue
                ts_file = os.path.join(root, file)
                qm_file = os.path.join(qm_dir, file.replace('.ts', '.qm'))

                # Check modification time cache
                ts_mtime = os.path.getmtime(ts_file)
                if ts_file in i18n_cache and i18n_cache[ts_file] == ts_mtime:
                    logging.info('%s is up to date.', ts_file)
                    continue

                logging.info('Compiling %s to %s', ts_file, qm_file)

                # Run pyside6-lrelease to compile ts -> qm
                cmd = f'pyside6-lrelease "{ts_file}" -qm "{qm_file}"'
                if 0 != os.system(cmd):
                    logging.error('Failed to compile translation file: %s', ts_file)
                    exit(1)

                logging.info('Compiled %s', qm_file)

                # Update cache
                i18n_cache[ts_file] = ts_mtime

    def save_cache(self):
        # save cache
        with open('.cache/assets.json', 'w') as f:
            json.dump(self.cache, f, indent=4)
        logging.info('Cache saved.')

    @staticmethod
    def filelist(root_dir: str, filelist_name: str):
        paths = []
        for current_path, dirs, files in os.walk(root_dir, topdown=False):
            for file in files:
                relative_path = os.path.relpath(os.path.join(current_path, file), root_dir)
                logging.info(relative_path)
                paths.append(relative_path)
            relative_path = os.path.relpath(os.path.join(current_path, ""), root_dir)
            if relative_path != ".":
                logging.info(relative_path)
                paths.append(relative_path)

        with open(filelist_name, "w", encoding="utf-8") as f:
            f.write("\n".join(paths))
            f.write("\n")

    @staticmethod
    def get_last_tag(default="0.0.0.0") -> str:
        """Get the last git tag as version, or return default if not found."""
        try:
            tag = subprocess.check_output(
                ["git", "describe", "--tags", "--abbrev=0"],
                stderr=subprocess.DEVNULL,
                text=True
            ).strip()
        except subprocess.CalledProcessError:
            return default

        return tag.split("-")[0] if tag else default

    def build(self):
        # call nuitka to build the app
        # include all files in app package and exclude the ui files
        start = time.perf_counter()
        logging.info('Building the app...')
        cmd = ('nuitka '
               '--output-dir=build '
               '--output-filename="App" '
               'app/__main__.py '
               + '--jobs={} '.format(os.cpu_count())
               + ('--onefile ' if self.args.onefile else '--standalone ')
               + self.opt_from_toml
               + (" ".join(self.args.backend_args)))
        logging.info(cmd)
        rt = os.system(cmd)
        end = time.perf_counter()
        if rt == 0:
            logging.info(f'Build complete in {end - start:.3f}s.')
            if not self.args.onefile:
                if os.path.exists('build/App'):
                    shutil.rmtree('build/App')
                shutil.move('build/__main__.dist', 'build/App')
                logging.info("Generate the filelist.")
                Build.filelist('build/App', 'build/App/filelist.txt')
                logging.info("Filelist has been generated.")
        else:
            logging.error(f'Failed to build app in {end - start:.3f}s.')
            exit(1)

    def run(self):
        self.init()
        if not self.args.no_cache:
            self.load_cache()
        if self.args.i18n:
            self.build_i18n_ts()
        if self.args.rc or self.args.all:
            self.build_ui()
            self.build_i18n()
            self.build_assets()
        self.save_cache()
        if self.args.build or self.args.all:
            if sys.platform == 'win32':
                self.opt_from_toml += f"--product-version={Build.get_last_tag()} "
            self.build()


if __name__ == '__main__':
    builder = Build()
    builder.run()
