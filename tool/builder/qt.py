import logging
import os
from pathlib import Path


def build_ui(ui_list, cache):
    """Compile *.ui files into Python files using pyside6-uic, preserving directory structure."""
    ui_dir = Path("app/ui")
    res_dir = Path("app/resources")

    if not ui_list:
        logging.info("No ui files found, skipping ui conversion.")
        return

    res_dir.mkdir(parents=True, exist_ok=True)
    logging.info("Converting ui files to Python files...")
    ui_cache = cache.get("ui", {})

    for input_file in ui_list:
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

    cache["ui"] = ui_cache


def build_assets(asset_list, cache, no_cache=False):
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

    assets_cache = cache.get('assets', {})
    need_rebuild = False
    for asset in asset_list:
        mtime = asset.stat().st_mtime
        asset_key = str(asset)
        if asset_key in assets_cache and assets_cache[asset_key] == mtime:
            logging.info(f'{asset} is up to date.')
            continue
        assets_cache[asset_key] = mtime
        logging.info(f'{asset} is outdated.')
        need_rebuild = True

    # Force rebuild if cache is disabled
    if no_cache:
        need_rebuild = True

    if need_rebuild:
        # Generate assets.qrc dynamically
        with open(qrc_file, 'w', encoding='utf-8') as f:
            f.write('<!DOCTYPE RCC>\n')
            f.write('<RCC version="1.0">\n')
            f.write('  <qresource>\n')
            for asset in asset_list:
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

    cache['assets'] = assets_cache


def build_i18n_ts(lang_list, files_to_scan, cache):
    """
    Generate translation (.ts) files for all languages in lang_list
    by scanning self.ui_list and self.source_list using pyside6-lupdate.
    """
    i18n_dir = Path("app/i18n")
    i18n_dir.mkdir(parents=True, exist_ok=True)

    logging.info("Generating translation (.ts) files for languages: %s", ', '.join(lang_list))

    i18n_cache = cache.get("i18n", {})

    for lang in lang_list:
        ts_file = i18n_dir / f"{lang}.ts"
        logging.info("Generating %s ...", ts_file)

        files_str = " ".join(f'"{f}"' for f in files_to_scan)
        cmd = f'pyside6-lupdate -silent -locations absolute -extensions ui {files_str} -ts "{ts_file}"'

        if 0 != os.system(cmd):
            logging.error("Failed to generate translation file: %s", ts_file)
            exit(1)

        i18n_cache[lang] = ts_file.stat().st_mtime
        logging.info("Generated translation file: %s", ts_file)

    cache["i18n"] = i18n_cache


def build_i18n(i18n_list, cache):
    """
    Compile .ts translation files into .qm files under app/assets/i18n/.
    Only regenerate .qm if the corresponding .ts file has changed.
    """
    qm_root = Path("app/assets/i18n")
    qm_root.mkdir(parents=True, exist_ok=True)

    logging.info("Compiling translation files...")

    # Get cache for i18n
    i18n_cache = cache.get("i18n", {})

    for ts_file in i18n_list:
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

    cache["i18n"] = i18n_cache


def gen_init_py():
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
