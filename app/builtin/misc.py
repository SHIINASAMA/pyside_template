import sys
from pathlib import Path

def running_in_bundle() -> bool:
    if sys.platform != "darwin":
        return False

    exe_path = Path(sys.executable).resolve()
    return ".app/Contents/MacOS" in str(exe_path)
