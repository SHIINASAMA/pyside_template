import asyncio

from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt, Signal


class AsyncWidget(QWidget):
    _closed = Signal()

    def __init__(self, parent):
        super().__init__(parent)
        self.setWindowModality(Qt.WindowModality.ApplicationModal)

    def closeEvent(self, event):
        self._closed.emit()
        super().closeEvent(event)

    async def show(self):
        future = asyncio.get_event_loop().create_future()
        self._closed.connect(lambda: future.set_result(None))
        super().show()
        await future
