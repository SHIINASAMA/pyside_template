import logging
import os


def gen_version_py(version):
    with open('app/resources/version.py', 'w', encoding='utf-8') as f:
        f.write(f'__version__ = "{version}"\n')


def gen_filelist(root_dir: str, filelist_name: str):
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
