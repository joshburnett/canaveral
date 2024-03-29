import sys
from pathlib import Path
import tomllib

from PySide6 import QtCore, QtGui
from PySide6.QtWidgets import QApplication, QMainWindow, QLabel, QDialog, QMenu, QSystemTrayIcon
from PySide6.QtCore import Qt, QAbstractNativeEventFilter, QAbstractEventDispatcher

import win32api
import win32gui

from loguru import logger
from appdirs import AppDirs

# Try different ways of importing, so we can run this as an application installed via pip/pipx,
# and also just from the source directory.
from canaveral.basemodels import SearchPathEntry, Catalog
from canaveral.qtmodels import LaunchListModel
from canaveral.widgets import CharLineEdit, CharListWidget
from canaveral.qtkeybind import keybinder


class WinEventFilter(QAbstractNativeEventFilter):
    """Used for intercepting keyboard events for global hotkeys"""
    def __init__(self, kb):
        self.keybinder = kb
        super().__init__()

    def nativeEventFilter(self, eventType, message):
        ret = self.keybinder.handler(eventType, message)
        return ret, 0


# Helper object for defining locations for config & log files
DIRS = AppDirs('Canaveral', appauthor='')


def load_search_paths(paths_file_path: Path | str) -> list[SearchPathEntry]:
    with open(paths_file_path, 'rb') as f:
        entries = tomllib.load(f)['search_path_entries']

    return [SearchPathEntry(**entry) for entry in entries]


class CanaveralWindow(QMainWindow):
    """Application's main window (the search window)"""

    def __init__(self):
        super().__init__()

        self.dragging = False
        self.drag_start_point = None

        try:
            self.search_path_entries = load_search_paths(Path(DIRS.user_data_dir) / 'paths.toml')
            logger.debug('Loaded search path entries from paths.toml.')
        except ImportError:
            logger.debug('No paths.toml present, creating from paths-example.toml.')
            import shutil
            shutil.copy(Path(__file__).parent / 'paths-example.toml', Path(DIRS.user_data_dir) / 'canaveralpaths.toml')
            self.search_path_entries = load_search_paths(Path(DIRS.user_data_dir) / 'paths.toml')
            logger.debug('Loaded search path entries from new paths.toml.')

        self.catalog = Catalog(self.search_path_entries, launch_data_file=Path(DIRS.user_data_dir) / 'launch_data.txt')

        self.model = LaunchListModel(catalog=self.catalog, max_launch_list_entries=10)

        self.setup()
        self.setup_sys_tray_icon()

        self.launch_list_view.setModel(self.model)
        self.update_launch_list_size()
        self.line_input.textEdited.connect(self.update_query)

        self.item_refresh_timer = QtCore.QTimer(self)
        self.item_refresh_timer.setInterval(5*60*1000)  # 5 minutes
        self.item_refresh_timer.timeout.connect(self.catalog.refresh_items_list)
        self.item_refresh_timer.start()

        # Install a native event filter to receive events from the OS
        keybinder.init()
        keybinder.register_hotkey(self.winId(), "Ctrl+Alt+Space", self.show_main_window_and_focus)
        self.win_event_filter = WinEventFilter(keybinder)
        self.event_dispatcher = QAbstractEventDispatcher.instance()
        self.event_dispatcher.installNativeEventFilter(self.win_event_filter)

    def setup_sys_tray_icon(self):
        self.tray = QSystemTrayIcon()
        if self.tray.isSystemTrayAvailable():
            icon = QtGui.QIcon(str(Path(__file__).parent / 'resources/rocket_with_shadow_blue.png'))
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
        bg_pixmap = QtGui.QPixmap(str(Path(__file__).parent / 'resources/light_background_2x.png'))
        bg_pixmap.setDevicePixelRatio(2)
        # bg_pixmap = QtGui.QPixmap(':/styles/frame')
        self.background_size_scaled = bg_pixmap.size() / bg_pixmap.devicePixelRatio()
        self.background.setPixmap(bg_pixmap)
        self.background.resize(self.background_size_scaled)
        self.background.move(0, 0)
        self.resize(self.background_size_scaled)

        self.search_icon = QLabel(parent=self)
        search_pixmap = QtGui.QPixmap(str(Path(__file__).parent / 'resources/search_icon.png'))
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
        self.line_input.selectAll()
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
        # logger.debug(f'Key pressed: {event.key()}')

        if key == Qt.Key_Escape:
            if self.launch_list_view.isVisible():
                self.hide_launch_list()
            else:
                # QApplication.instance().quit()
                self.hide_main_window()

        elif key in (Qt.Key_Enter, Qt.Key_Return):
            logger.debug('Return/Enter key')
            if self.launch_list_view.currentIndex().row() == -1:
                self.launch_list_view.setCurrentIndex(self.launch_list_view.model().index(0, 0))

            item = self.model.data(self.launch_list_view.currentIndex(), role=Qt.UserRole)
            self.hide_main_window()

            # http://timgolden.me.uk/pywin32-docs/win32api__ShellExecute_meth.html
            # win32api.ShellExecute(hwnd, op, file, params, dir, bShow)
            logger.debug(f'Executing: {item.full_path}')
            win32api.ShellExecute(0, None, str(item.full_path), '', '', 1)

            self.catalog.update_launch_data(query_string=self.line_input.text(), new_launch_choice=item.full_path)

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
        elif self.launch_list_view.hasFocus():
            self.launch_list_view.setCurrentIndex(self.launch_list_view.model().index(-1, 0))
            self.line_input.setFocus()
            self.line_input.keyPressEvent(event)

    def changeEvent(self, event):
        if event.type() == QtCore.QEvent.ActivationChange and not self.isActiveWindow():
            self.hide_main_window()
        super().changeEvent(event)

    def closeEvent(self, event):
        logger.info('closeEvent')
        keybinder.unregister_hotkey(self.winId(), "Ctrl+Alt+Space")
        event.accept()
        QApplication.instance().quit()
