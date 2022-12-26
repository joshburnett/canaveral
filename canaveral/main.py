import sys
from pathlib import Path

from PySide6 import QtGui
from PySide6.QtWidgets import QApplication

from loguru import logger

# Try different ways of importing, so we can run this as an application installed via pip/pipx,
# and also just from the source directory.
# try:
if __name__ == '__main__':
    file = Path(__file__).resolve()
    sys.path.append(str(file.parent.parent))

from canaveral.mainwindow import CanaveralWindow, DIRS


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
    # app.setAttribute(Qt.AA_EnableHighDpiScaling)  # Not needed in PySide6
    app.setQuitOnLastWindowClosed(False)

    main_window = CanaveralWindow()

    app.exec()

    sys.stdout.close()
    sys.exit()


if __name__ == '__main__':
    run()
