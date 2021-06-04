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

        try:
            from paths import search_path_entries
            self.search_path_entries = search_path_entries
            logger.debug('Loaded search path entries from paths.py.')
        except ImportError:
            self.search_path_entries = [
                SearchPathEntry(path=Path(r'~').expanduser())
            ]
            logger.debug('No paths.py present, using default search path entries.')

        self.catalog = Catalog(self.search_path_entries)
        logger.debug(f'Catalog has {len(self.catalog.items)} entries')
        self.query_set = QuerySet(catalog=self.catalog)
        # self.query_set.create_query('doc')

        self.model = LaunchListModel(catalog=self.catalog, query_set=self.query_set)
        self.setup()

        self.launch_list_view.setModel(self.model)
        self.update_launch_list_size()
        self.line_input.textEdited.connect(self.update_query)

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

        self.output = QLabel(parent=self)
        self.output.setObjectName('output')
        self.output.setAlignment(Qt.AlignHCenter)

        self.line_input = CharLineEdit(parent=self)
        self.line_input.setObjectName('input')
        self.line_input.resize(200, 20)
        self.line_input.move(40, 20)
        self.line_input.setAutoFillBackground(True)

        self.output_icon = QLabel(parent=self)
        self.output_icon.setObjectName('outputIcon')

        self.transparent_pixmap = QtGui.QPixmap(16, 16)
        self.transparent_pixmap.fill(Qt.transparent)

        self.launch_list_view = CharListWidget(parent=self)
        self.launch_list_view.setAutoFillBackground(True)
        self.launch_list_view.setIconSize(QtCore.QSize(32, 32))
        self.launch_list_view.setObjectName('alternatives')

        self.alt_scroll = self.launch_list_view.verticalScrollBar()
        self.alt_scroll.setObjectName('altScroll')

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
        x_margin = 40
        y_margin = 20
        width = self.width() - 2*x_margin
        x = x_margin
        y = self.label.height() - y_margin
        num_items_in_results = self.model.rowCount(0)
        if num_items_in_results > 0:
            index = self.launch_list_view.model().index(0, 0)
            item_height = self.launch_list_view.model().data(index, Qt.SizeHintRole)
            num_items = min(self.max_launch_list_entries, num_items_in_results)

            # I guess we need 4px total for the top & bottom border?
            height = num_items * item_height.height() + (num_items-1)*self.launch_list_view.spacing() + 4
            self.launch_list_view.setGeometry(x, y, width, height)
            self.resize(self.width(), self.label.height()-y_margin+height)
            self.launch_list_view.show()
        else:
            self.hide_launch_list()
            self.resize(self.width(), self.label.height())

    def update_query(self, query_text):
        self.model.set_query(query_text)
        self.update_launch_list_size()
        if self.model.query is None or len(self.model.query.sorted_score_results) == 0:
            self.output.setText('')
            self.output_icon.clear()
        else:
            list_index = self.launch_list_view.model().index(0, 0)
            # top_result = self.model.query.sorted_score_results[0]
            self.output.setText(self.model.data(list_index, Qt.DisplayRole))
            self.output_icon.setPixmap(self.model.data(list_index, Qt.DecorationRole).pixmap(self.output_icon.size()))

    def keyPressEvent(self, event: QtGui.QKeyEvent) -> None:
        key = event.key()
        if key == Qt.Key_Escape:
            if self.launch_list_view.isVisible():
                self.hide_launch_list()
            else:
                QApplication.instance().quit()

        if key in (Qt.Key_Down, Qt.Key_Up, Qt.Key_PageDown, Qt.Key_PageUp):
            if self.launch_list_view.isVisible():
                if not self.launch_list_view.isActiveWindow():
                    if self.launch_list_view.currentIndex().row() < 0 < self.model.num_results():
                        self.launch_list_view.activateWindow()
                        self.launch_list_view.setCurrentIndex(self.launch_list_view.model().index(0, 0))
                    else:
                        self.launch_list_view.activateWindow()
                        QApplication.sendEvent(self.launch_list_view, event)
            elif key in (Qt.Key_Down, Qt.Key_PageDown) and 0 < self.model.num_results():
                self.launch_list_view.setCurrentIndex(self.launch_list_view.model().index(0, 0))
                self.show_launch_list()

    def show_launch_list(self):
        self.launch_list_view.show()
        self.launch_list_view.setFocus()

    def hide_launch_list(self):
        self.launch_list_view.setCurrentIndex(self.launch_list_view.model().index(-1, 0))
        self.launch_list_view.repaint()
        self.launch_list_view.hide()


def run():
    app = QApplication([])

    main_window = CanaveralWindow()
    app.exec()


if __name__ == '__main__':
    run()
