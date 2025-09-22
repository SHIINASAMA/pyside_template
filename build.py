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
from pathlib import Path


class Build:
    def __init__(self):
        self.args = None
        self.source_list = []
        self.ui_list = []
        self.asset_list = []
        self.i18n_list = []
        self.lang_list = []
        self.cache = {}
        self.opt_from_toml = ""

    def init(self):
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        # check working directory
        # if 'app' is not in the current working directory, exit
        if not os.path.exists('app'):
            logging.error('Please run this script from the project root directory.')
            exit(1)

        self.parse_args()
        if self.args.debug:
            logging.info('Debug mode enabled.')
            logging.getLogger().setLevel(logging.DEBUG)
        self.glob_files()
        self.load_pyproject()

    def load_pyproject(self):
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
        self.lang_list = glom.glom(data, "tool.build.i18n.languages", default=[])

    def glob_files(self):
        root = Path("app")
        assets_dir = root / "assets"
        i18n_dir = root / "i18n"
        exclude_dirs = [
            root / "resources",
        ]

        for path in root.rglob("*"):
            if any(ex in path.parents for ex in exclude_dirs):
                continue

            if assets_dir in path.parents and os.path.isfile(path):
                self.asset_list.append(path)
                continue

            if i18n_dir in path.parents and os.path.isfile(path):
                self.i18n_list.append(path)
                continue

            if path.suffix == ".py":
                self.source_list.append(path)
            elif path.suffix == ".ui":
                self.ui_list.append(path)

        logging.debug("Source list: %s", [str(x) for x in self.source_list])
        logging.debug("UI list: %s", [str(x) for x in self.ui_list])
        logging.debug("Asset list: %s", [str(x) for x in self.asset_list])
        logging.debug("I18n list: %s", [str(x) for x in self.i18n_list])

    def parse_args(self):
        """parse command line arguments"""
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

        parser.add_argument('--debug', action='store_true',
                            help='Enable debug mode, which will output more information during the build process')

        parser.add_argument('backend_args', nargs=argparse.REMAINDER,
                            help='Additional arguments for the build backend, e.g. -- --xxx=xxx')

        # do parse
        self.args = parser.parse_args()
        if self.args.backend_args and self.args.backend_args[0] == "--":
            self.args.backend_args = self.args.backend_args[1:]

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
        ui_dir = Path("app/ui")
        res_dir = Path("app/resources")

        if not self.ui_list:
            logging.info("No ui files found, skipping ui conversion.")
            return

        res_dir.mkdir(parents=True, exist_ok=True)
        logging.info("Converting ui files to Python files...")
        ui_cache = self.cache.get("ui", {})

        for input_file in self.ui_list:
            try:
                rel_path = input_file.parent.relative_to(ui_dir)
            except ValueError:
                # input_file is not under app/ui, skip it
                continue

            output_dir = res_dir / rel_path
            output_dir.mkdir(parents=True, exist_ok=True)

            output_file = output_dir / (input_file.stem + "_ui.py")

            # Check cache to avoid unnecessary recompilation
            mtime = input_file.stat().st_mtime
            if str(input_file) in ui_cache and ui_cache[str(input_file)] == mtime:
                logging.info(f"{input_file} is up to date.")
                continue

            ui_cache[str(input_file)] = mtime

            # Run pyside6-uic
            cmd = f'pyside6-uic "{input_file}" -o "{output_file}"'
            if 0 != os.system(cmd):
                logging.error(f"Failed to convert {input_file}.")
                exit(1)

            logging.info(f"Converted {input_file} to {output_file}")

        self.cache["ui"] = ui_cache

    @staticmethod
    def build_gen_version_py():
        with open('app/resources/version.py', 'w', encoding='utf-8') as f:
            f.write(f'__version__ = "{Build.get_last_tag()}"\n')

    def build_assets(self):
        """Generate assets.qrc from files in app/assets and compile it with pyside6-rcc."""
        assets_dir = Path('app/assets')
        res_dir = Path('app/resources')
        qrc_file = res_dir / 'assets.qrc'
        py_res_file = res_dir / 'resource.py'

        # Skip if assets directory does not exist
        if not os.path.exists(assets_dir):
            logging.info('No assets folder found, skipping assets conversion.')
            return

        if not os.path.exists(res_dir):
            os.makedirs(res_dir)

        logging.info('Converting assets to Python resources...')

        assets_cache = self.cache.get('assets', {})
        need_rebuild = False
        for asset in self.asset_list:
            mtime = asset.stat().st_mtime
            asset_key = str(asset)
            if asset_key in assets_cache and assets_cache[asset_key] == mtime:
                logging.info(f'{asset} is up to date.')
                continue
            assets_cache[asset_key] = mtime
            logging.info(f'{asset} is outdated.')
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
                for asset in self.asset_list:
                    posix_path = asset.as_posix()
                    # remove the leading "app/assets/" from the path
                    alias = posix_path[len('app/assets/'):]
                    # rel_path is the path relative to app/resources
                    rel_path = os.path.relpath(asset, res_dir)
                    f.write(f'    <file alias="{alias}">{rel_path}</file>\n')
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
        by scanning self.ui_list and self.source_list using pyside6-lupdate.
        """
        i18n_dir = Path("app/i18n")
        i18n_dir.mkdir(parents=True, exist_ok=True)

        logging.info("Generating translation (.ts) files for languages: %s", ', '.join(self.lang_list))

        i18n_cache = self.cache.get("i18n", {})

        files_to_scan = [str(f) for f in self.ui_list + self.source_list]

        for lang in self.lang_list:
            ts_file = i18n_dir / f"{lang}.ts"
            logging.info("Generating %s ...", ts_file)

            files_str = " ".join(f'"{f}"' for f in files_to_scan)
            cmd = f'pyside6-lupdate -silent -locations absolute -extensions ui {files_str} -ts "{ts_file}"'

            if 0 != os.system(cmd):
                logging.error("Failed to generate translation file: %s", ts_file)
                exit(1)

            i18n_cache[lang] = ts_file.stat().st_mtime
            logging.info("Generated translation file: %s", ts_file)

        self.cache["i18n"] = i18n_cache

    def build_i18n(self):
        """
        Compile .ts translation files into .qm files under app/assets/i18n/.
        Only regenerate .qm if the corresponding .ts file has changed.
        """
        qm_root = Path("app/assets/i18n")
        qm_root.mkdir(parents=True, exist_ok=True)

        logging.info("Compiling translation files...")

        # Get cache for i18n
        i18n_cache = self.cache.get("i18n", {})

        for ts_file in self.i18n_list:
            try:
                ts_file = Path(ts_file)
            except Exception:
                continue

            qm_file = qm_root / (ts_file.stem + ".qm")

            # Check modification time cache
            ts_mtime = ts_file.stat().st_mtime
            if str(ts_file) in i18n_cache and i18n_cache[str(ts_file)] == ts_mtime:
                logging.info("%s is up to date.", ts_file)
                continue

            logging.info("Compiling %s to %s", ts_file, qm_file)

            # Run pyside6-lrelease to compile ts -> qm
            cmd = f'pyside6-lrelease "{ts_file}" -qm "{qm_file}"'
            if 0 != os.system(cmd):
                logging.error("Failed to compile translation file: %s", ts_file)
                exit(1)

            logging.info("Compiled %s", qm_file)

            # Update cache
            i18n_cache[str(ts_file)] = ts_mtime

        self.cache["i18n"] = i18n_cache

    @staticmethod
    def build_gen_init_py():
        """Create __init__.py in every subdirectory if not exists"""
        root = Path("app/resources")
        init_file = root / "__init__.py"
        if not init_file.exists():
            init_file.touch()
        for path in root.rglob("*"):
            if path.is_dir():
                init_file = path / "__init__.py"
                if not init_file.exists():
                    init_file.touch()

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
                logging.debug(relative_path)
                paths.append(relative_path)
            relative_path = os.path.relpath(os.path.join(current_path, ""), root_dir)
            if relative_path != ".":
                logging.debug(relative_path)
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

        return tag if tag else default

    def build(self):
        # call nuitka to build the app
        # include all files in app package and exclude the ui files
        if sys.platform != 'win32':
            path = Path('build/App')
            if path.exists() and path.is_dir():
                shutil.rmtree(path)
            elif path.exists() and path.is_file():
                path.unlink()
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
        logging.debug(cmd)
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
            Build.build_gen_version_py()
            Build.build_gen_init_py()
        self.save_cache()
        if self.args.build or self.args.all:
            self.build()


if __name__ == '__main__':
    builder = Build()
    builder.run()
