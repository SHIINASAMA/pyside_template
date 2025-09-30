import logging
import os
from pathlib import Path


def glob_files():
    root = Path("app")
    assets_dir = root / "assets"
    i18n_dir = root / "i18n"
    exclude_dirs = [
        root / "resources",
        root / "test"
    ]

    asset_list = []
    i18n_list = []
    source_list = []
    ui_list = []

    for path in root.rglob("*"):
        if any(ex in path.parents for ex in exclude_dirs):
            continue

        if assets_dir in path.parents and os.path.isfile(path):
            asset_list.append(path)
            continue

        if i18n_dir in path.parents and os.path.isfile(path):
            i18n_list.append(path)
            continue

        if path.suffix == ".py":
            source_list.append(path)
        elif path.suffix == ".ui":
            ui_list.append(path)

    logging.debug("Source list: %s", [str(x) for x in source_list])
    logging.debug("UI list: %s", [str(x) for x in ui_list])
    logging.debug("Asset list: %s", [str(x) for x in asset_list])
    logging.debug("I18n list: %s", [str(x) for x in i18n_list])

    return asset_list, i18n_list, source_list, ui_list
