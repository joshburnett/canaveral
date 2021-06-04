from typing import List, Optional, Dict, Union, Sequence

from PySide6 import QtCore, QtGui, QtWidgets, QtUiTools
from PySide6.QtWidgets import (QApplication, QWidget, QPushButton, QMessageBox, QMainWindow, QLabel,
                               QLineEdit, QListView)

from PySide6.QtCore import Qt

from loguru import logger


class CharLineEdit(QLineEdit):
    def __init__(self, parent):
        super().__init__(parent)

    # def keyPressEvent(self, event: QtGui.QKeyEvent) -> None:
    #     key = event.key()
    #     logger.debug(key)
    #
    #     if key == Qt.Key_Escape:
    #         QApplication.instance().quit()
    #     else:
    #         super().keyPressEvent(event)


class CharListWidget(QListView):
    def __init__(self, parent):
        super().__init__(parent)
        self.setAttribute(Qt.WA_AlwaysShowToolTips)
        self.setAlternatingRowColors(True)
        self.setUniformItemSizes(True)

    # def dataChanged(self, topLeft: Union[QtCore.QModelIndex, QtCore.QPersistentModelIndex],
    #                 bottomRight: Union[QtCore.QModelIndex, QtCore.QPersistentModelIndex],
    #                 roles: Sequence[int] = list) -> None:
    #     logger.debug('data changed event called')
