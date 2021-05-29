from __future__ import annotations
from typing import List, Optional, Dict

from pathlib import Path

from PySide6 import QtCore, QtGui, QtWidgets, QtUiTools
from PySide6.QtWidgets import (QApplication, QWidget, QPushButton, QMessageBox, QMainWindow, QLabel, QListWidget,
                               QLineEdit)

from PySide6.QtCore import Qt

from loguru import logger

import resources_rc
from basemodels import SearchPathEntry, Catalog, QuerySet
from qtmodels import LaunchListModel
from widgets import CharLineEdit, CharListWidget


class CanaveralWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.dragging = False
        self.drag_start_point = None
        self.max_launch_list_entries = 10

        self.search_path_entries = [
            SearchPathEntry(path=Path(r'~').expanduser())
        ]

        self.catalog = Catalog(self.search_path_entries)
        logger.debug(f'Catalog has {len(self.catalog.items)} entries')
        self.query_set = QuerySet(catalog=self.catalog)
        # self.query_set.create_query('doc')

        self.model = LaunchListModel(catalog=self.catalog, query_set=self.query_set)
        self.model.set_query('do')
        self.setup()

        self.launch_list_view.setModel(self.model)
        self.update_launch_list_size()
        self.line_input.textChanged.connect(self.update_query)
        
        # self.model.dataChanged.connect(self.launch_list_view.dataChanged())

    def setup(self):
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_AlwaysShowToolTips)
        self.setAttribute(Qt.WA_InputMethodEnabled)
        self.setFocusPolicy(Qt.ClickFocus)

        self.label = QLabel(parent=self)
        # bg_pixmap = QtGui.QPixmap('resources/Black_Glass/frame.png')
        bg_pixmap = QtGui.QPixmap(':/styles/frame')
        self.label.setPixmap(bg_pixmap)
        self.label.resize(bg_pixmap.size())
        self.label.move(0, 0)
        self.resize(self.label.size())

        self.line_input = CharLineEdit(parent=self)
        self.line_input.setObjectName('input')
        self.line_input.resize(200, 20)
        self.line_input.move(40, 20)
        self.line_input.setAutoFillBackground(True)

        self.launch_list_view = CharListWidget(parent=self)
        self.launch_list_view.setAutoFillBackground(True)
        self.launch_list_view.setIconSize(QtCore.QSize(32, 32))
        # self.launch_list_view.resize(500, 200)
        style_file = QtCore.QFile(':/styles/style')
        style_file.open(QtCore.QFile.ReadOnly | QtCore.QIODevice.Text)
        stream = QtCore.QTextStream(style_file)
        style_data = stream.readAll()
        self.setStyleSheet(style_data)
        style_file.close()

        self.show()

    def mousePressEvent(self, event: QtGui.QMouseEvent) -> None:
        if event.buttons() == Qt.LeftButton:
            self.dragging = True
            self.drag_start_point = event.pos()
            self.activateWindow()
            self.line_input.setFocus()

    def mouseMoveEvent(self, event: QtGui.QMouseEvent) -> None:
        if event.buttons() == Qt.LeftButton and self.dragging:
            p = event.globalPos() - self.drag_start_point
            self.move(p)
            self.line_input.setFocus()
            self.launch_list_view.move(p)

    def mouseReleaseEvent(self, event: QtGui.QMouseEvent) -> None:
        self.dragging = False
        self.line_input.setFocus()

    def update_launch_list_size(self):
        main_window_geometry = self.geometry()
        x_margin = 40
        y_margin = 20
        width = main_window_geometry.width() - 2*x_margin
        x = x_margin
        y = main_window_geometry.height() - y_margin
        index = self.launch_list_view.model().index(0, 0)
        item_height = self.launch_list_view.model().data(index, Qt.SizeHintRole)
        num_items = min(self.max_launch_list_entries, self.model.rowCount(index))
        height = self.max_launch_list_entries * item_height.height() + \
                 (self.max_launch_list_entries-1)*self.launch_list_view.spacing() + 4  # 4 is presumably for a border?
        self.launch_list_view.setGeometry(x, y, width, height)
        self.resize(self.width(), self.label.height()-y_margin+height)
        # self.setSi
        # self.launch_list_view.move(40, 60)

    def update_query(self, query_string):
        self.model.set_query(query_string)



def run():
    app = QApplication([])

    main_window = CanaveralWindow()
    app.exec()


if __name__ == '__main__':
    run()
