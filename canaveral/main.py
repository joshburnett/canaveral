import sys
from pathlib import Path

from PySide6 import QtGui
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from PySide6.QtCore import QAbstractEventDispatcher

from loguru import logger

# Try different ways of importing, so we can run this as an application installed via pip/pipx,
# and also just from the source directory.
try:
    from canaveral.mainwindow import CanaveralWindow, WinEventFilter, DIRS
    from canaveral.qtkeybind import keybinder
    from canaveral.basemodels import SearchPathEntry, Catalog, QuerySet
    from canaveral.qtmodels import LaunchListModel
    from canaveral.widgets import CharLineEdit, CharListWidget
except ImportError:
    from .mainwindow import CanaveralWindow, WinEventFilter, DIRS
    from .qtkeybind import keybinder
    from .basemodels import SearchPathEntry, Catalog, QuerySet
    from .qtmodels import LaunchListModel
    from .widgets import CharLineEdit, CharListWidget


def run():
    if Path(sys.executable).stem == 'pythonw':
        Path(DIRS.user_log_dir).mkdir(parents=True, exist_ok=True)
        sys.stdout = open(Path(DIRS.user_log_dir) / 'canaveral.log', 'w')
        sys.stderr = sys.stdout
        logger.remove()
        logger.add(sys.stdout)

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

    sys.stdout.close()
    sys.exit()


if __name__ == '__main__':
    run()
