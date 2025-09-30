import logging
from os import system


def run_test(args):
    cmd = 'pytest app ' + (" ".join(args.backend_args))
    logging.debug(cmd)
    return system(cmd)
