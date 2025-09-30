import subprocess


def get_last_tag(default="0.0.0.0") -> str:
    """Get the last git tag as version, or return default if not found."""
    try:
        tag = subprocess.check_output(
            ["git", "describe", "--tags", "--abbrev=0", "--first-parent"],
            stderr=subprocess.DEVNULL,
            text=True
        ).strip()
    except subprocess.CalledProcessError:
        return default

    return tag if tag else default
