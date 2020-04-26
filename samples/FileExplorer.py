# coding: utf-8
import subprocess

from PySide2.QtCore import (
    Qt,
)

from PySide2.QtWidgets import (
    QApplication,
    QMainWindow,
    QAbstractItemView,
    QMenu,
    QSplitter,
    QFileIconProvider,
)

from PySideLib.QCdtWidgets import (
    QDirectoryTreeItem,
    QDirectoryTreeModel,
    QDirectoryTreeView,
    QDirectoryTreeWidget,
    QFileListModel,
    QFileListView,
    QFileListWidget,
    QFileListViewMode,
    QFileListItem,
)

from PySideLib.QCdtUtils import (
    QFileIconLoader,
)


class DirTreeModel(QDirectoryTreeModel):

    def __init__(self, parent):
        super().__init__(parent)
        iconProvider = QFileIconProvider()
        self.__defaultIcon = iconProvider.icon(QFileIconProvider.Folder)
        self.__driveIcon = iconProvider.icon(QFileIconProvider.Drive)

    def createItem(self, path):
        item = QDirectoryTreeItem(path)

        if path == path.parent:
            icon = self.__driveIcon
        else:
            icon = self.__defaultIcon
        item.setIcon(icon)

        return item

    def data(self, index, role=Qt.DisplayRole):
        if role == Qt.DecorationRole:
            item = self.itemFromIndex(index)
            return item.icon()
        return super(DirTreeModel, self).data(index, role)


class DirTreeWidget(QDirectoryTreeWidget):

    def modelType(self):
        return DirTreeModel


class FileListModel(QFileListModel):

    icons = {}

    def data(self, index, role=Qt.DisplayRole):
        if role == Qt.DecorationRole:
            item = self.itemFromIndex(index)
            path = item.path()
            return FileListModel.icons.get(path)
        return super(FileListModel, self).data(index, role)


class FileListWidget(QFileListWidget):

    def modelType(self):
        return FileListModel


def main():
    app = QApplication()
    window = QMainWindow()
    window.setMinimumSize(600, 600)

    tree = DirTreeWidget(window)
    tree.setRootDirectoryPaths(['C:\\', 'D:\\'])
    tree.setSelectionMode(QAbstractItemView.ExtendedSelection)
    tree.itemSelectionChanged.connect(lambda x, y: print(tree.selectedItems()))
    tree.itemClicked.connect(lambda idx: print(f'click: {idx}'))
    tree.itemDoubleClicked.connect(lambda idx: print(f'doubleclick: {idx}'))
    tree.setContextMenuPolicy(Qt.CustomContextMenu)

    def _ctx_menu(point):
        def _open_directory(path):
            subprocess.call(f'explorer "{path()}"', shell=True)

        menu_items = {
            u'フォルダを開く': lambda path: _open_directory(path),
        }

        menu = QMenu()
        for label in menu_items.keys():
            menu.addAction(label)

        executed_action = menu.exec_(tree.mapToGlobal(point))
        action = menu_items[executed_action.text()]

        item = tree.currentItem()
        action(item.path)

    tree.customContextMenuRequested.connect(_ctx_menu)

    files = FileListWidget(window)
    files.setViewMode(QFileListViewMode.ListMode)
    files.setSelectionMode(QAbstractItemView.ExtendedSelection)
    # files.itemSelectionChanged.connect(lambda x, y: print(tree.selectedItems()))
    # files.itemClicked.connect(lambda idx: print(f'click: {idx}'))
    # files.itemDoubleClicked.connect(lambda idx: print(f'doubleclick: {idx}'))

    iconLoader = QFileIconLoader(None)

    def _updateFiles(index):
        item = tree.itemFromIndex(index)

        filePaths = list(item.path().glob('*'))
        iconLoader.reset(filePaths)

        def _set_icon(result):
            FileListModel.icons[result.filePath] = result.icon
            files.model().refresh()

        iconLoader.loaded.connect(_set_icon)
        # iconLoader.completed.connect(print)
        iconLoader.load_async(filePaths)

        files.setDirectoryPath(tree.itemFromIndex(index).path())

    tree.itemSelectionChanged.connect(lambda x, y: _updateFiles(tree.selectedIndexes()[0]))
    tree.itemClicked.connect(_updateFiles)

    def _changeDir(index):
        item = files.itemFromIndex(index)
        print(item.path())

    files.itemDoubleClicked.connect(_changeDir)

    splitter = QSplitter()
    splitter.addWidget(tree)
    splitter.addWidget(files)

    window.setCentralWidget(splitter)
    window.show()
    app.exec_()


if __name__ == '__main__':
    main()
