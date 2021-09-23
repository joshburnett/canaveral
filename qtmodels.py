from typing import List, Optional, Dict, Union

from PySide6 import QtCore, QtGui, QtWidgets, QtUiTools
from PySide6.QtCore import Qt

from loguru import logger

from basemodels import Catalog, QuerySet, Query


class LaunchListModel(QtCore.QAbstractListModel):
    catalog: Catalog
    # query_set: QuerySet
    query: Optional[Query]

    def __init__(self, *args, catalog: Catalog, query_set: QuerySet, max_launch_list_entries=10, **kwargs):
        super(LaunchListModel, self).__init__(*args, **kwargs)
        self.query_string = None
        self.query_set = query_set
        self.query = None
        self.catalog = catalog
        self.max_launch_list_entries = max_launch_list_entries

        # self.mime_database = QtCore.QMimeDatabase()
        self.file_icon_provider = QtWidgets.QFileIconProvider()

    def set_query(self, query_string: Optional[str]):
        if query_string in [None, '']:
            self.query_string = None
            self.query = None
        else:
            self.query_string = query_string
            self.query = self.catalog.query(query_string)
        self.layoutChanged.emit()

    def data(self, index: Union[QtCore.QModelIndex, QtCore.QPersistentModelIndex],
             role: int = QtCore.Qt.ItemDataRole.DisplayRole):
        score_result = self.query.sorted_score_results[index.row()]

        if role == Qt.DisplayRole:
            if score_result.item.full_path.suffix == '.lnk':
                return score_result.item.full_path.stem
            else:
                return score_result.item.name

        elif role == Qt.DecorationRole:
            info = QtCore.QFileInfo(str(score_result.item.full_path))

            return self.file_icon_provider.icon(info)

        elif role == Qt.ToolTipRole:
            return str(score_result.item.full_path)

        elif role == Qt.SizeHintRole:
            return QtCore.QSize(36, 36)

        elif role == Qt.UserRole:
            return score_result.item

        # mime_types = self.mime_database.mimeTypesForFileName(self._items[index.row()].name)
        #
        # icon = QtGui.QIcon()
        # for mime_type in mime_types:
        #     icon = QtGui.QIcon.fromTheme(mime_type.iconName())
        #     if icon.isNull():
        #         break
        #
        # if icon.isNull():
        #     return QtWidgets.QApplication.style().standardIcon(QtWidgets.QStyle.SP_FileIcon)
        # else:
        #     return icon

    def rowCount(self, parent: Union[QtCore.QModelIndex, QtCore.QPersistentModelIndex] = QtCore.QModelIndex) -> int:
        return min(self.num_results(), self.max_launch_list_entries)

    def num_results(self):
        if self.query is None:
            return 0
        else:
            return len(self.query.sorted_score_results)
