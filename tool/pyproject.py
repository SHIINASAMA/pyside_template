import sys

import glom
import toml


def load_pyproject():
    """get and build vars from pyproject.toml
     1. nuitka command options
     2. enabled languages list"""
    with open("pyproject.toml") as f:
        data = toml.load(f)
    config = glom.glom(data, "tool.build", default={})
    platform_config = glom.glom(data, f"tool.build.{sys.platform}", default={})
    config.update(platform_config)

    nuitka_cmd = ""
    for k, v in config.items():
        if isinstance(v, list) and v:
            cmd = f"--{k}={','.join(v)} "
            nuitka_cmd += cmd
        if isinstance(v, str) and v != "":
            cmd = f"--{k}={v} "
            nuitka_cmd += cmd
        if type(v) is bool and v:
            cmd = f"--{k} "
            nuitka_cmd += cmd

    lang_list = glom.glom(data, "tool.build.i18n.languages", default=[])

    return nuitka_cmd, lang_list
