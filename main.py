from __future__ import annotations

import sys
from pathlib import Path

from PySide6 import QtCore, QtGui
from PySide6.QtWidgets import (QApplication, QMainWindow, QLabel, QDialog, QMenu, QSystemTrayIcon)
from PySide6.QtCore import Qt
from PySide6.QtCore import QAbstractNativeEventFilter, QAbstractEventDispatcher

import win32api
import win32gui

from loguru import logger
from qtkeybind import keybinder

from basemodels import SearchPathEntry, Catalog, QuerySet
from qtmodels import LaunchListModel
from widgets import CharLineEdit, CharListWidget


class WinEventFilter(QAbstractNativeEventFilter):
    def __init__(self, keybinder):
        self.keybinder = keybinder
        super().__init__()

    def nativeEventFilter(self, eventType, message):
        ret = self.keybinder.handler(eventType, message)
        return ret, 0


class CanaveralWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.dragging = False
        self.drag_start_point = None

        try:
            from paths import search_path_entries
            logger.debug('Loaded search path entries from paths.py.')
        except ImportError:
            logger.debug('No paths.py present, using default search path entries.')
            search_path_entries = [
                SearchPathEntry(path=Path(r'~').expanduser())
            ]

        self.search_path_entries = search_path_entries

        self.catalog = Catalog(self.search_path_entries, launch_data_file=Path('launch_data.txt'))
        logger.debug(f'Catalog has {len(self.catalog.items)} entries')
        self.query_set = QuerySet(catalog=self.catalog)
        # self.query_set.create_query('doc')

        self.model = LaunchListModel(catalog=self.catalog, query_set=self.query_set, max_launch_list_entries=10)

        self.setup()
        self.setup_sys_tray_icon()

        self.launch_list_view.setModel(self.model)
        self.update_launch_list_size()
        self.line_input.textEdited.connect(self.update_query)
        self.show_main_window_and_focus()

    def setup_sys_tray_icon(self):
        self.tray = QSystemTrayIcon()
        if self.tray.isSystemTrayAvailable():
            icon = QtGui.QIcon('resources/search_icon.png')
            menu = QMenu()
            setting_action = menu.addAction('Settings...')
            setting_action.triggered.connect(self.setting)
            exit_action = menu.addAction('Exit')
            exit_action.triggered.connect(sys.exit)

            self.tray.setIcon(icon)
            self.tray.setContextMenu(menu)
            self.tray.show()
            self.tray.setToolTip('Canaveral')
            self.setWindowFlag(QtCore.Qt.Tool)
            self.line_input.setFocusPolicy(QtCore.Qt.StrongFocus)
            self.setFocusPolicy(QtCore.Qt.StrongFocus)
        else:
            self.tray = None

    def setting(self):
        self.dialog = QDialog()
        self.dialog.setWindowTitle("Settings Dialog")
        self.dialog.show()

    def setup(self):
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_AlwaysShowToolTips)
        self.setAttribute(Qt.WA_InputMethodEnabled)
        # self.setFocusPolicy(Qt.ClickFocus)

        self.background = QLabel(parent=self)
        bg_pixmap = QtGui.QPixmap('resources/light_background_2x.png')
        bg_pixmap.setDevicePixelRatio(2)
        # bg_pixmap = QtGui.QPixmap(':/styles/frame')
        self.background_size_scaled = bg_pixmap.size() / bg_pixmap.devicePixelRatio()
        self.background.setPixmap(bg_pixmap)
        self.background.resize(self.background_size_scaled)
        self.background.move(0, 0)
        self.resize(self.background_size_scaled)

        self.search_icon = QLabel(parent=self)
        search_pixmap = QtGui.QPixmap('resources/search_icon.png')
        search_pixmap.setDevicePixelRatio(2)
        # bg_pixmap = QtGui.QPixmap(':/styles/frame')
        self.search_icon.setPixmap(search_pixmap)
        self.search_icon.resize(search_pixmap.size() / search_pixmap.devicePixelRatio())
        self.search_icon.move(550, 12)

        self.line_input = CharLineEdit(parent=self)
        self.line_input.setObjectName('input')
        self.line_input.resize(530, 30)
        self.line_input.move(12, 15)
        # self.line_input.setAutoFillBackground(True)
        self.line_input.setFont(QtGui.QFont('Franklin Gothic', 24))
        self.line_input.setStyleSheet('qproperty-frame: false;'
                                      'background-color: rgba(0, 0, 0, 0);')

        self.output_icon = QLabel(parent=self)
        self.output_icon.setObjectName('outputIcon')

        self.output = QLabel(parent=self)
        self.output.setObjectName('output')
        self.output.setAlignment(Qt.AlignHCenter)

        self.launch_list_view = CharListWidget(parent=self)
        self.launch_list_view.setAutoFillBackground(True)
        self.launch_list_view.setIconSize(QtCore.QSize(32, 32))
        self.launch_list_view.setObjectName('alternatives')

    def update_launch_list_size(self):
        x_margin = 40
        y_margin = 0
        width = self.width() - 2*x_margin
        x = x_margin
        y = self.background_size_scaled.height() - y_margin
        num_items_in_results = self.model.num_results()
        if num_items_in_results > 0:
            index = self.launch_list_view.model().index(0, 0)
            item_height = self.launch_list_view.model().data(index, Qt.SizeHintRole)
            num_display_items = min(self.model.max_launch_list_entries, num_items_in_results)

            # I guess we need 4px total for the top & bottom border?
            height = num_display_items * item_height.height() + \
                     (num_display_items-1)*self.launch_list_view.spacing() + 4
            self.launch_list_view.setGeometry(x, y, width, height)
            self.resize(self.width(), self.background_size_scaled.height()-y_margin+height)
            self.launch_list_view.show()
        else:
            self.hide_launch_list()
            self.resize(self.width(), self.background_size_scaled.height())

    def update_query(self, query_text):
        self.model.set_query(query_text)
        self.update_launch_list_size()

        # if self.model.query is None or len(self.model.query.sorted_score_results) == 0:
        #     self.output.setText('')
        #     self.output_icon.clear()
        # else:
        #     list_index = self.launch_list_view.model().index(0, 0)
        #     # top_result = self.model.query.sorted_score_results[0]
        #     self.output.setText(self.model.data(list_index, Qt.DisplayRole))
        #     self.output_icon.setPixmap(self.model.data(list_index, Qt.DecorationRole).pixmap(self.output_icon.size()))

    def hide_main_window(self):
        self.launch_list_view.hide()
        self.hide()

    def show_main_window_and_focus(self):
        frame_geometry = self.frameGeometry()
        monitor_center = self.screen().availableGeometry().center()
        frame_geometry.moveCenter(monitor_center)
        self.move(frame_geometry.topLeft())
        self.show()
        # self.setFocus()
        self.line_input.setFocus()
        win32gui.SetForegroundWindow(self.winId())

    def show_launch_list(self):
        self.launch_list_view.show()
        self.launch_list_view.setFocus()

    def hide_launch_list(self):
        self.launch_list_view.setCurrentIndex(self.launch_list_view.model().index(-1, 0))
        self.launch_list_view.repaint()
        self.launch_list_view.hide()
        self.line_input.setFocus()

    def mousePressEvent(self, event: QtGui.QMouseEvent) -> None:
        if event.buttons() == Qt.LeftButton:
            self.dragging = True
            self.drag_start_point = event.position()
            self.activateWindow()
            self.line_input.setFocus()

    def mouseMoveEvent(self, event: QtGui.QMouseEvent) -> None:
        if event.buttons() == Qt.LeftButton and self.dragging:
            p = event.globalPosition() - self.drag_start_point
            self.move(round(p.x()), round(p.y()))
            self.line_input.setFocus()
            self.launch_list_view.move(round(p.x()), round(p.y()))

    def mouseReleaseEvent(self, event: QtGui.QMouseEvent) -> None:
        self.dragging = False
        self.line_input.setFocus()

    def keyPressEvent(self, event: QtGui.QKeyEvent) -> None:
        key = event.key()
        if key == Qt.Key_Escape:
            if self.launch_list_view.isVisible():
                self.hide_launch_list()
            else:
                # QApplication.instance().quit()
                self.hide_main_window()

        elif key in (Qt.Key_Enter, Qt.Key_Return):
            logger.debug('Return/Enter key')
            item = self.model.data(self.launch_list_view.currentIndex(), role=Qt.UserRole)
            self.hide_main_window()

            # http://timgolden.me.uk/pywin32-docs/win32api__ShellExecute_meth.html
            # win32api.ShellExecute(hwnd, op, file, params, dir, bShow)
            win32api.ShellExecute(0, None, str(item.full_path), '', '', 1)

            self.catalog.update_launch_data(query_string=self.line_input.text(), launch_choice=item.full_path)

        elif key in (Qt.Key_Down, Qt.Key_Up, Qt.Key_PageDown, Qt.Key_PageUp):
            if self.launch_list_view.isVisible():
                logger.debug(f'spot 1: self.launch_list_view.isActiveWindow(): '
                             f'{self.launch_list_view.isActiveWindow()}')
                logger.debug(f'self.launch_list_view.hasFocus(): {self.launch_list_view.hasFocus()}')

                if not self.launch_list_view.hasFocus():
                    if self.launch_list_view.currentIndex().row() < 0 < self.model.num_results():
                        logger.debug('spot 2')
                        self.launch_list_view.setFocus()
                        self.launch_list_view.setCurrentIndex(self.launch_list_view.model().index(0, 0))
                    else:
                        logger.debug('spot 3')
                        self.launch_list_view.setFocus()
                        QApplication.sendEvent(self.launch_list_view, event)
                elif self.launch_list_view.currentIndex().row() == 0 and key == Qt.Key_Up:
                    logger.debug('spot 1.5')
                    self.line_input.setFocus()

            elif key in (Qt.Key_Down, Qt.Key_PageDown) and 0 < self.model.num_results():
                logger.debug('spot 4')
                self.launch_list_view.setCurrentIndex(self.launch_list_view.model().index(0, 0))
                self.show_launch_list()

    def closeEvent(self, event):
        logger.info('closeEvent')
        keybinder.unregister_hotkey(self.winId(), "Ctrl+Alt+Space")
        event.accept()
        sys.exit()


def run():
    logger.debug('Starting.')

    app = QApplication([])
    app.setFont(QtGui.QFont('Franklin Gothic'))
    app.setAttribute(Qt.AA_EnableHighDpiScaling)
    app.setQuitOnLastWindowClosed(False)

    main_window = CanaveralWindow()

    # Install a native event filter to receive events from the OS
    keybinder.init()
    keybinder.register_hotkey(main_window.winId(), "Ctrl+Alt+Space", main_window.show_main_window_and_focus)
    win_event_filter = WinEventFilter(keybinder)
    event_dispatcher = QAbstractEventDispatcher.instance()
    event_dispatcher.installNativeEventFilter(win_event_filter)

    app.exec()


if __name__ == '__main__':
    if Path(sys.executable).stem == 'pythonw':
        sys.stdout = open('stdout.txt', 'w')
        logger.remove()
        logger.add(sys.stdout)
    run()
    sys.stdout.close()
    sys.exit()
