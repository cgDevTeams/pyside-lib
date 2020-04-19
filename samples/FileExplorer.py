# coding: utf-8
import sys
import os
import glob
import subprocess
import pathlib

from PySide2.QtCore import (
    Qt,
    QSize,
    QSortFilterProxyModel,
)

from PySide2.QtGui import (
    QIcon,
)

from PySide2.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QLineEdit,
    QVBoxLayout,
    QMessageBox,
    QSizePolicy,
    QHBoxLayout,
    QAbstractItemView,
    QMenu,
)

from PySideLib.QCdtWidgets import (
    QDirectoryTreeItem,
    QDirectoryTreeModel,
    QDirectoryTreeView,
    QDirectoryTreeWidget,
)

from PySideLib.QCdtUtils import (
    BatchImageLoader,
    ImageLoadingCallback,
)


class DirTreeModel(QDirectoryTreeModel):

    dirIcon = None

    def createItem(self, path):
        item = QDirectoryTreeItem(path)
        item.setIcon(DirTreeModel.dirIcon)
        return item

    def data(self, index, role=Qt.DisplayRole):
        if role == Qt.DecorationRole:
            item = self.itemFromIndex(index)
            return item.icon()
        return super(DirTreeModel, self).data(index, role)


class DirTreeWidget(QDirectoryTreeWidget):

    def modelType(self):
        return DirTreeModel


def main():
    app = QApplication()
    window = QMainWindow()
    window.setMinimumSize(600, 600)

    DirTreeModel.dirIcon = QIcon(os.path.join(os.path.dirname(__file__), 'resources', 'Folder_16x.png'))

    w = DirTreeWidget(window)
    w.setRootDirectoryPaths(['C:\\', 'D:\\'])
    w.setSelectionMode(QAbstractItemView.ExtendedSelection)
    # w.itemSelectionChanged.connect(lambda x, y: print(w.selectedItems()))
    w.setContextMenuPolicy(Qt.CustomContextMenu)

    def _ctx_menu(point):
        def _open_directory(path):
            subprocess.call(f'explorer "{path()}"', shell=True)

        menu_items = {
            u'フォルダを開く': lambda path: _open_directory(path),
        }

        menu = QMenu()
        for label in menu_items.keys():
            menu.addAction(label)

        executed_action = menu.exec_(w.mapToGlobal(point))
        action = menu_items[executed_action.text()]

        item = w.currentItem()
        action(item.path)

    w.customContextMenuRequested.connect(_ctx_menu)

    window.setCentralWidget(w)
    window.show()
    app.exec_()


if __name__ == '__main__':
    main()
