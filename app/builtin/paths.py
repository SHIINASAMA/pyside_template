from pathlib import Path
from singleton_decorator import singleton
from PySide6.QtCore import QStandardPaths, QCoreApplication

@singleton
class AppPaths:
    base_dir: Path
    update_dir: Path

    def __init__(self, *, base_dir=None):
        if base_dir is None:
            app = QCoreApplication.instance()
            if app is None:
                raise RuntimeError("QCoreApplication instance is not created yet.")
            self.base_dir = Path(QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppDataLocation))
        else:
            self.base_dir = base_dir

        self.update_dir = self.base_dir / "update_tmp"

        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.update_dir.mkdir(parents=True, exist_ok=True)
