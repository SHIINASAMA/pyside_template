import sys


def pop_arg_pair(name) -> str:
    argv = sys.argv

    try:
        idx = argv.index(name)
    except ValueError:
        raise RuntimeError(f"Missing required argument: {name}")

    if idx + 1 >= len(argv):
        raise RuntimeError(f"Argument {name} requires a value")

    value = argv[idx + 1]

    del argv[idx + 1]
    del argv[idx]

    return value


def pop_arg(name, default_value):
    if name in sys.argv:
        sys.argv.remove(name)
        return True
    else:
        return default_value