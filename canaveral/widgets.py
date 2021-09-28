from PySide6 import QtGui
from PySide6.QtWidgets import QLineEdit, QListView

from PySide6.QtCore import Qt


class CharLineEdit(QLineEdit):
    def __init__(self, parent):
        super().__init__(parent)


class CharListWidget(QListView):
    def __init__(self, parent):
        super().__init__(parent)
        self.setAttribute(Qt.WA_AlwaysShowToolTips)
        self.setAlternatingRowColors(True)
        self.setUniformItemSizes(True)

    def keyPressEvent(self, event: QtGui.QKeyEvent) -> None:
        key = event.key()
        if key not in (Qt.Key_Down, Qt.Key_Up, Qt.Key_PageDown, Qt.Key_PageUp):
            self.parent().keyPressEvent(event)
        else:
            super().keyPressEvent(event)
