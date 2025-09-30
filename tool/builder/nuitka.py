import logging
import os
import shutil
import sys
import time
from pathlib import Path

from tool.builder.build import gen_filelist


def build(args, opt_from_toml):
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
           + ('--onefile ' if args.onefile else '--standalone ')
           + opt_from_toml
           + (" ".join(args.backend_args)))
    logging.debug(cmd)
    rt = os.system(cmd)
    end = time.perf_counter()
    if rt == 0:
        logging.info(f'Build complete in {end - start:.3f}s.')
        if not args.onefile:
            if os.path.exists('build/App'):
                shutil.rmtree('build/App')
            shutil.move('build/__main__.dist', 'build/App')
            logging.info("Generate the filelist.")
            gen_filelist('build/App', 'build/App/filelist.txt')
            logging.info("Filelist has been generated.")
    else:
        logging.error(f'Failed to build app in {end - start:.3f}s.')
        exit(1)
